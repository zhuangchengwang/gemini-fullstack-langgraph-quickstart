"""
用户上下文处理工具 - 增强版
展示如何在 LangGraph 中获取和使用用户信息以及HTTP请求参数
"""

from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableConfig


def get_user_context(config: RunnableConfig) -> Dict[str, Any]:
    """
    从 RunnableConfig 中提取用户上下文信息和请求参数
    
    Args:
        config: LangGraph 运行配置
        
    Returns:
        包含用户信息和请求上下文的字典
    """
    configurable = config.get("configurable", {})
    
    # 方式1：获取 LangGraph 自动注入的认证用户信息
    auth_user = configurable.get("langgraph_auth_user", {})
    
    # 方式2：获取自定义配置参数
    user_preference = configurable.get("user_preference", "english")
    search_region = configurable.get("search_region", "en-US")
    personalization_enabled = configurable.get("personalization_enabled", False)
    
    # 方式3：从认证用户信息中获取请求上下文
    request_context = auth_user.get("request_context", {})
    custom_config = auth_user.get("custom_config", {})
    
    return {
        # 认证信息
        "user_id": auth_user.get("identity", "anonymous"),
        "username": auth_user.get("username", "anonymous"),
        "email": auth_user.get("email"),
        "is_authenticated": auth_user.get("is_authenticated", False),
        "roles": auth_user.get("roles", []),
        "permissions": auth_user.get("permissions", []),
        
        # 用户偏好
        "language_preference": auth_user.get("language", user_preference),
        "search_region": auth_user.get("region", search_region),
        "timezone": auth_user.get("timezone", "UTC"),
        "client_version": auth_user.get("client_version", "unknown"),
        "personalization_enabled": personalization_enabled,
        
        # HTTP请求上下文
        "request_method": request_context.get("method", "unknown"),
        "request_path": request_context.get("path", "unknown"),
        "query_params": request_context.get("query_params", {}),
        "path_params": request_context.get("path_params", {}),
        "headers": request_context.get("headers", {}),
        "body_params": request_context.get("body_params", {}),
        "user_agent": request_context.get("user_agent", "unknown"),
        "client_ip": request_context.get("client_ip", "unknown"),
        "content_type": request_context.get("content_type", ""),
        
        # 自定义配置（从URL参数或请求体提取）
        "custom_config": custom_config,
        
        # 调试信息
        "debug_info": auth_user.get("debug_info", {}),
        
        # 原始数据
        "raw_auth_user": auth_user,
        "raw_configurable": configurable
    }


def get_request_params(user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    提取所有HTTP请求参数
    
    Args:
        user_context: 用户上下文信息
        
    Returns:
        包含所有请求参数的字典
    """
    return {
        # URL查询参数
        "query": user_context.get("query_params", {}),
        
        # 路径参数
        "path": user_context.get("path_params", {}),
        
        # 请求头参数
        "headers": user_context.get("headers", {}),
        
        # 请求体参数
        "body": user_context.get("body_params", {}),
        
        # 自定义配置参数
        "config": user_context.get("custom_config", {}),
        
        # 请求元信息
        "meta": {
            "method": user_context.get("request_method"),
            "path": user_context.get("request_path"),
            "user_agent": user_context.get("user_agent"),
            "client_ip": user_context.get("client_ip"),
            "content_type": user_context.get("content_type")
        }
    }


def get_param_value(user_context: Dict[str, Any], param_name: str, default: Any = None) -> Any:
    """
    从多个来源获取参数值，按优先级顺序：custom_config > query_params > body_params > headers
    
    Args:
        user_context: 用户上下文
        param_name: 参数名
        default: 默认值
        
    Returns:
        参数值
    """
    # 优先级1：自定义配置
    custom_config = user_context.get("custom_config", {})
    if param_name in custom_config:
        return custom_config[param_name]
    
    # 优先级2：URL查询参数
    query_params = user_context.get("query_params", {})
    if param_name in query_params:
        return query_params[param_name]
    
    # 优先级3：请求体参数
    body_params = user_context.get("body_params", {})
    if param_name in body_params:
        return body_params[param_name]
    
    # 优先级4：请求头参数
    headers = user_context.get("headers", {})
    header_key = f"x-{param_name.lower()}"
    if header_key in headers:
        return headers[header_key]
    
    return default


def check_user_permission(user_context: Dict[str, Any], required_permission: str) -> bool:
    """
    检查用户是否具有特定权限
    
    Args:
        user_context: 用户上下文信息
        required_permission: 所需权限
        
    Returns:
        是否具有权限
    """
    permissions = user_context.get("permissions", [])
    return required_permission in permissions


def personalize_search_query(query: str, user_context: Dict[str, Any]) -> str:
    """
    根据用户上下文和请求参数个性化搜索查询
    
    Args:
        query: 原始查询
        user_context: 用户上下文
        
    Returns:
        个性化后的查询
    """
    if not user_context.get("personalization_enabled", False):
        return query
    
    # 从请求参数获取个性化设置
    search_scope = get_param_value(user_context, "search_scope", "global")
    search_depth = get_param_value(user_context, "search_depth", "standard")
    include_recent = get_param_value(user_context, "include_recent", "true").lower() == "true"
    
    # 根据用户语言偏好调整查询
    language = user_context.get("language_preference", "english")
    region = user_context.get("search_region", "en-US")
    
    modified_query = query
    
    if language == "chinese":
        # 为中文用户添加地区限定
        if "中国" not in query and "China" not in query and search_scope == "local":
            modified_query = f"{query} 中国相关"
    
    # 根据搜索深度调整
    if search_depth == "detailed":
        modified_query = f"{modified_query} 详细分析"
    elif search_depth == "summary":
        modified_query = f"{modified_query} 概述总结"
    
    # 是否包含最新信息
    if include_recent:
        modified_query = f"{modified_query} 最新"
    
    return modified_query


def get_user_specific_prompt(base_prompt: str, user_context: Dict[str, Any]) -> str:
    """
    根据用户上下文和请求参数生成个性化提示
    
    Args:
        base_prompt: 基础提示模板
        user_context: 用户上下文
        
    Returns:
        个性化提示
    """
    language = user_context.get("language_preference", "english")
    username = user_context.get("username", "用户")
    
    # 从请求参数获取回答格式偏好
    response_format = get_param_value(user_context, "response_format", "standard")
    response_length = get_param_value(user_context, "response_length", "medium")
    include_sources = get_param_value(user_context, "include_sources", "true").lower() == "true"
    
    # 添加用户信息到提示中
    user_info_section = f"""
用户信息:
- 用户名: {username}
- 语言偏好: {language}
- 地区: {user_context.get("search_region", "未知")}
- 时区: {user_context.get("timezone", "UTC")}
- 客户端: {user_context.get("user_agent", "未知")}
"""
    
    # 根据请求参数调整回答要求
    format_instructions = []
    
    if language == "chinese":
        format_instructions.append("请用中文回答，并考虑中国用户的使用习惯。")
    else:
        format_instructions.append("Please respond in English.")
    
    if response_format == "structured":
        format_instructions.append("请用结构化格式回答，包含标题、要点和总结。")
    elif response_format == "bullet_points":
        format_instructions.append("请用要点列表格式回答。")
    
    if response_length == "brief":
        format_instructions.append("请提供简洁的回答。")
    elif response_length == "detailed":
        format_instructions.append("请提供详细深入的回答。")
    
    if include_sources:
        format_instructions.append("请在回答中包含相关来源和引用。")
    
    instruction = " ".join(format_instructions)
    
    return f"{base_prompt}\n\n{user_info_section}\n回答要求: {instruction}"


def log_request_context(user_context: Dict[str, Any]) -> None:
    """
    记录请求上下文信息，用于调试和分析
    
    Args:
        user_context: 用户上下文
    """
    print(f"🔍 请求上下文分析:")
    print(f"👤 用户: {user_context['username']} ({user_context['user_id']})")
    print(f"🌐 请求: {user_context['request_method']} {user_context['request_path']}")
    print(f"🔗 查询参数: {user_context['query_params']}")
    print(f"📋 路径参数: {user_context['path_params']}")
    print(f"🎯 自定义配置: {user_context['custom_config']}")
    print(f"🌍 地区语言: {user_context['search_region']} / {user_context['language_preference']}")
    print(f"🔐 权限: {user_context['permissions']}")


# 示例：在图节点中使用增强的用户上下文
def example_node_with_enhanced_context(state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
    """
    展示如何在图节点中使用增强的用户上下文和请求参数
    """
    # 获取完整的用户上下文
    user_context = get_user_context(config)
    
    # 记录请求上下文
    log_request_context(user_context)
    
    # 获取所有请求参数
    request_params = get_request_params(user_context)
    print(f"📦 所有请求参数: {request_params}")
    
    # 获取特定参数
    search_type = get_param_value(user_context, "search_type", "general")
    max_results = get_param_value(user_context, "max_results", 10)
    priority = get_param_value(user_context, "priority", "normal")
    
    print(f"🎯 提取的参数: search_type={search_type}, max_results={max_results}, priority={priority}")
    
    # 检查权限
    if not check_user_permission(user_context, "search"):
        raise Exception("用户没有搜索权限")
    
    # 根据请求参数调整处理逻辑
    if search_type == "academic":
        print("🎓 使用学术搜索模式")
    elif search_type == "news":
        print("📰 使用新闻搜索模式")
    else:
        print("🔍 使用通用搜索模式")
    
    # 更新状态，传递用户信息和请求参数给下游节点
    return {
        "user_id": user_context["user_id"],
        "user_metadata": {
            "username": user_context["username"],
            "language": user_context["language_preference"],
            "region": user_context["search_region"],
            "request_params": request_params,
            "processing_mode": search_type,
            "max_results": max_results
        }
    } 