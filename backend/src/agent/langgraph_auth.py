"""LangGraph 官方认证集成 - 增强版，支持透传请求参数"""

from langgraph_sdk import Auth
from agent.auth import verify_token
from typing import Dict, Any, Optional
import json

# 创建认证实例
my_auth = Auth()

@my_auth.authenticate
async def authenticate(
    authorization: str,
    headers: Dict[bytes, bytes],
    query_params: Dict[str, str],
    path_params: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
    path: str = "",
    method: str = ""
) -> Dict[str, Any]:
    """
    LangGraph 官方认证函数 - 增强版
    
    Args:
        authorization: Authorization header 的值（例如："Bearer <token>"）
        headers: 所有请求头
        query_params: URL查询参数
        path_params: 路径参数（如 /threads/{thread_id} 中的 thread_id）
        body: 请求体数据
        path: 请求路径
        method: HTTP方法
        
    Returns:
        包含用户信息和请求上下文的字典
        
    Raises:
        Auth.exceptions.HTTPException: 认证失败时抛出401错误
    """
    print(f"🔍 LangGraph Auth: 收到认证请求")
    print(f"📍 路径: {method} {path}")
    print(f"🔗 查询参数: {query_params}")
    print(f"📋 路径参数: {path_params}")
    
    # 解析 Bearer token
    if not authorization or not authorization.startswith("Bearer "):
        print(f"❌ LangGraph Auth: 无效的 Authorization 格式")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    # 提取 token
    token = authorization.split(" ", 1)[-1]
    print(f"🔍 提取的 token: {token[:20]}...")
    
    try:
        # 验证 JWT token
        payload = verify_token(token)
        if payload is None:
            print(f"❌ LangGraph Auth: JWT token 验证失败")
            raise Auth.exceptions.HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        
        username = payload.get("sub")
        if not username:
            print(f"❌ LangGraph Auth: token 中缺少用户信息")
            raise Auth.exceptions.HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )
        
        print(f"✅ LangGraph Auth: 用户 {username} 认证成功")
        
        # 解析headers为字符串格式
        str_headers = {}
        for key, value in headers.items():
            try:
                str_headers[key.decode('utf-8')] = value.decode('utf-8')
            except:
                str_headers[key.decode('utf-8', errors='ignore')] = str(value)
        
        # 提取有用的请求信息
        request_context = {
            # 基础请求信息
            "method": method,
            "path": path,
            "query_params": query_params,
            "path_params": path_params,
            
            # 请求头信息（过滤敏感信息）
            "headers": {
                k: v for k, v in str_headers.items() 
                if k.lower() not in ['authorization', 'cookie', 'x-api-key']
            },
            
            # 客户端信息
            "user_agent": str_headers.get("user-agent", "unknown"),
            "client_ip": str_headers.get("x-forwarded-for", str_headers.get("x-real-ip", "unknown")),
            "content_type": str_headers.get("content-type", ""),
            
            # 自定义参数提取
            "custom_params": {},
        }
        
        # 从查询参数中提取自定义配置
        custom_config = {}
        for key, value in query_params.items():
            if key.startswith("config_"):
                # config_language=zh -> {"language": "zh"}
                config_key = key[7:]  # 移除 "config_" 前缀
                try:
                    # 尝试解析JSON值
                    if value.lower() in ['true', 'false']:
                        custom_config[config_key] = value.lower() == 'true'
                    elif value.isdigit():
                        custom_config[config_key] = int(value)
                    else:
                        custom_config[config_key] = value
                except:
                    custom_config[config_key] = value
        
        # 从请求体中提取配置（如果有）
        if body and isinstance(body, dict):
            # 提取 config.configurable 中的参数
            if "config" in body and "configurable" in body["config"]:
                body_config = body["config"]["configurable"]
                custom_config.update(body_config)
            
            # 提取其他有用的body参数
            request_context["body_params"] = {
                k: v for k, v in body.items() 
                if k not in ["config"] and not k.startswith("_")
            }
        
        print(f"🎯 提取的自定义配置: {custom_config}")
        print(f"📦 请求上下文: method={method}, path={path}")
        
        # 返回详细的用户信息和请求上下文，LangGraph会自动添加到 config["configurable"]["langgraph_auth_user"] 中
        return {
            # 标准用户认证信息
            "identity": username,
            "username": username,
            "user_id": payload.get("user_id", username),
            "email": payload.get("email"),
            "is_authenticated": True,
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            
            # 请求上下文信息
            "request_context": request_context,
            
            # 自定义配置参数
            "custom_config": custom_config,
            
            # 特殊处理的常用参数
            "language": query_params.get("lang", query_params.get("language", custom_config.get("language", "en"))),
            "region": query_params.get("region", custom_config.get("region", "us")),
            "timezone": str_headers.get("x-timezone", query_params.get("timezone", "UTC")),
            "client_version": str_headers.get("x-client-version", query_params.get("version", "unknown")),
            
            # 调试信息
            "debug_info": {
                "auth_time": payload.get("iat"),
                "token_exp": payload.get("exp"),
                "request_id": str_headers.get("x-request-id", f"{method}_{path}_{username}")
            }
        }
        
    except Auth.exceptions.HTTPException:
        # 重新抛出认证异常
        raise
    except Exception as e:
        print(f"❌ LangGraph Auth: 认证过程发生错误: {e}")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

# 导出认证实例
auth = my_auth 