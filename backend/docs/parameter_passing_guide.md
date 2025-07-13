# LangGraph 参数透传完整指南

本指南详细说明如何在 LangGraph 中传递 HTTP 请求参数（GET参数、POST参数、Headers等）到 Agent 节点中。

## 🎯 核心概念

### 参数传递流程

```
HTTP请求 → LangGraph认证函数 → RunnableConfig → Agent节点
    ↓           ↓                    ↓            ↓
查询参数    提取&解析            configurable    get_user_context()
请求头      过滤&转换            auth_user       get_param_value()
请求体      结构化存储            custom_config   个性化处理
路径参数
```

## 🔧 实现方案

### 1. 增强认证函数 (`langgraph_auth.py`)

```python
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
    增强版认证函数，支持提取所有HTTP请求参数
    """
    # 验证JWT token
    payload = verify_token(token)
    username = payload.get("sub")
    
    # 提取请求上下文
    request_context = {
        "method": method,
        "path": path,
        "query_params": query_params,
        "path_params": path_params,
        "headers": {k.decode(): v.decode() for k, v in headers.items()},
        "user_agent": headers.get(b"user-agent", b"").decode(),
        "client_ip": headers.get(b"x-forwarded-for", b"").decode()
    }
    
    # 从查询参数中提取自定义配置
    custom_config = {}
    for key, value in query_params.items():
        if key.startswith("config_"):
            config_key = key[7:]  # 移除 "config_" 前缀
            custom_config[config_key] = value
    
    # 从请求体中提取配置
    if body and "config" in body:
        custom_config.update(body["config"].get("configurable", {}))
    
    return {
        "identity": username,
        "username": username,
        "is_authenticated": True,
        # 关键：请求上下文信息
        "request_context": request_context,
        "custom_config": custom_config,
        # 常用参数的快速访问
        "language": query_params.get("lang", "en"),
        "region": query_params.get("region", "us"),
        "timezone": headers.get(b"x-timezone", b"UTC").decode()
    }
```

### 2. 用户上下文处理 (`user_context.py`)

```python
def get_user_context(config: RunnableConfig) -> Dict[str, Any]:
    """从配置中提取完整的用户上下文和请求参数"""
    auth_user = config.get("configurable", {}).get("langgraph_auth_user", {})
    request_context = auth_user.get("request_context", {})
    
    return {
        # 用户信息
        "user_id": auth_user.get("identity"),
        "username": auth_user.get("username"),
        
        # HTTP请求参数
        "query_params": request_context.get("query_params", {}),
        "path_params": request_context.get("path_params", {}),
        "headers": request_context.get("headers", {}),
        "custom_config": auth_user.get("custom_config", {}),
        
        # 请求元信息
        "request_method": request_context.get("method"),
        "request_path": request_context.get("path"),
        "user_agent": request_context.get("user_agent"),
        "client_ip": request_context.get("client_ip")
    }

def get_param_value(user_context: Dict[str, Any], param_name: str, default: Any = None) -> Any:
    """
    从多个来源获取参数值，按优先级：
    custom_config > query_params > body_params > headers
    """
    # 优先级1：自定义配置 (config_xxx 参数)
    if param_name in user_context.get("custom_config", {}):
        return user_context["custom_config"][param_name]
    
    # 优先级2：URL查询参数
    if param_name in user_context.get("query_params", {}):
        return user_context["query_params"][param_name]
    
    # 优先级3：请求头参数
    headers = user_context.get("headers", {})
    if f"x-{param_name.lower()}" in headers:
        return headers[f"x-{param_name.lower()}"]
    
    return default
```

### 3. 在Agent节点中使用

```python
def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """Web搜索节点，支持参数个性化"""
    # 获取用户上下文
    user_context = get_user_context(config)
    
    # 从请求参数获取搜索配置
    search_timeout = get_param_value(user_context, "search_timeout", 30)
    result_limit = get_param_value(user_context, "result_limit", 10)
    search_language = get_param_value(user_context, "search_language", "en")
    search_type = get_param_value(user_context, "search_type", "general")
    
    print(f"🔍 搜索配置: timeout={search_timeout}, limit={result_limit}")
    print(f"🌍 用户: {user_context['username']}, 语言: {search_language}")
    
    # 根据参数调整搜索逻辑
    if search_type == "academic":
        # 使用学术搜索模式
        pass
    elif search_type == "news":
        # 使用新闻搜索模式
        pass
    
    # 个性化搜索查询
    original_query = state["search_query"]
    personalized_query = personalize_search_query(original_query, user_context)
    
    # 执行搜索...
```

## 📡 API调用示例

### 1. 通过URL查询参数传递

```bash
POST /threads/123/runs?config_language=chinese&search_type=academic&max_results=20&lang=zh
Authorization: Bearer jwt_token
Content-Type: application/json

{
  "assistant_id": "agent",
  "input": {
    "messages": [{"role": "user", "content": "人工智能发展"}]
  }
}
```

**参数提取结果：**
```python
# 在Agent节点中可以获取到：
user_context = {
    "custom_config": {"language": "chinese"},  # config_language
    "query_params": {
        "search_type": "academic",
        "max_results": "20", 
        "lang": "zh"
    },
    "language": "zh"  # 快速访问
}
```

### 2. 通过请求头传递

```bash
POST /threads/123/runs
Authorization: Bearer jwt_token
X-Language: chinese
X-Search-Type: news
X-Max-Results: 15
X-Timezone: Asia/Shanghai
Content-Type: application/json

{
  "assistant_id": "agent",
  "input": {
    "messages": [{"role": "user", "content": "最新科技动态"}]
  }
}
```

**参数提取结果：**
```python
user_context = {
    "headers": {
        "x-language": "chinese",
        "x-search-type": "news",
        "x-max-results": "15",
        "x-timezone": "Asia/Shanghai"
    },
    "timezone": "Asia/Shanghai"  # 快速访问
}
```

### 3. 通过POST请求体传递

```bash
POST /threads/123/runs
Authorization: Bearer jwt_token
Content-Type: application/json

{
  "assistant_id": "agent",
  "input": {
    "messages": [{"role": "user", "content": "区块链应用"}],
    "user_preferences": {
      "expertise_level": "expert",
      "focus_areas": ["finance", "technology"]
    }
  },
  "config": {
    "configurable": {
      "response_format": "detailed_analysis",
      "include_charts": true,
      "search_depth": "comprehensive"
    }
  }
}
```

**参数提取结果：**
```python
user_context = {
    "custom_config": {
        "response_format": "detailed_analysis",
        "include_charts": True,
        "search_depth": "comprehensive"
    },
    "body_params": {
        "user_preferences": {
            "expertise_level": "expert",
            "focus_areas": ["finance", "technology"]
        }
    }
}
```

### 4. 路径参数自动提取

```bash
POST /threads/abc-123/runs/def-456/stream
```

**参数提取结果：**
```python
user_context = {
    "path_params": {
        "thread_id": "abc-123",
        "run_id": "def-456"
    },
    "request_path": "/threads/abc-123/runs/def-456/stream"
}
```

## 🎨 前端集成

### React Hook 增强

```typescript
export function useAuthenticatedStream(options: any) {
  const authenticatedSubmit = (data: any, config?: any) => {
    const enhancedConfig = {
      ...config,
      configurable: {
        // 从URL获取参数
        response_format: new URLSearchParams(window.location.search).get('format') || 'standard',
        search_depth: new URLSearchParams(window.location.search).get('depth') || 'standard',
        
        // 客户端环境信息
        client_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        client_language: navigator.language,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        
        ...config?.configurable,
      },
      headers: {
        'X-Client-Version': '1.0.0',
        'X-Client-Platform': 'web',
        'X-Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
        ...options.headers,
      }
    };
    
    originalSubmit(data, enhancedConfig);
  };
  
  return { ...stream, submit: authenticatedSubmit };
}
```

### 动态URL参数

```typescript
// 使用URL参数控制Agent行为
const searchWithParams = (query: string) => {
  const urlParams = {
    format: 'structured',
    depth: 'detailed', 
    max_results: '20',
    search_type: 'academic'
  };
  
  // 更新URL
  const url = new URL(window.location.href);
  Object.entries(urlParams).forEach(([key, value]) => {
    url.searchParams.set(key, value);
  });
  window.history.replaceState({}, '', url.toString());
  
  // 提交查询
  thread.submit({
    messages: [{ role: "user", content: query }]
  });
};
```

## 🛠️ 实用工具函数

### 参数验证和转换

```python
def validate_and_convert_params(user_context: Dict[str, Any]) -> Dict[str, Any]:
    """验证和转换请求参数"""
    params = {}
    
    # 数值参数
    max_results = get_param_value(user_context, "max_results", "10")
    try:
        params["max_results"] = max(1, min(int(max_results), 100))
    except:
        params["max_results"] = 10
    
    # 枚举参数
    search_type = get_param_value(user_context, "search_type", "general")
    params["search_type"] = search_type if search_type in ["general", "academic", "news"] else "general"
    
    # 布尔参数
    include_sources = get_param_value(user_context, "include_sources", "true")
    params["include_sources"] = include_sources.lower() in ["true", "1", "yes"]
    
    return params
```

### 参数优先级处理

```python
def get_param_with_priority(user_context: Dict[str, Any], param_name: str, default: Any = None) -> Any:
    """
    按优先级获取参数：
    1. custom_config (config_xxx)
    2. query_params (URL参数)  
    3. headers (X-xxx)
    4. body_params (POST体)
    5. default
    """
    sources = [
        ("custom_config", user_context.get("custom_config", {})),
        ("query_params", user_context.get("query_params", {})),
        ("headers", {k.replace("x-", ""): v for k, v in user_context.get("headers", {}).items() if k.startswith("x-")}),
        ("body_params", user_context.get("body_params", {}))
    ]
    
    for source_name, source_data in sources:
        if param_name in source_data:
            print(f"📍 参数 {param_name} 来源: {source_name}")
            return source_data[param_name]
    
    return default
```

## 🔍 调试和监控

### 请求参数日志

```python
def log_request_context(user_context: Dict[str, Any]) -> None:
    """记录完整的请求上下文，用于调试"""
    print("🔍 请求上下文分析:")
    print(f"👤 用户: {user_context['username']} ({user_context['user_id']})")
    print(f"🌐 请求: {user_context['request_method']} {user_context['request_path']}")
    print(f"🔗 查询参数: {user_context['query_params']}")
    print(f"📋 路径参数: {user_context['path_params']}")
    print(f"📦 自定义配置: {user_context['custom_config']}")
    print(f"🌍 地区语言: {user_context.get('region')} / {user_context.get('language')}")
    print(f"🔐 权限: {user_context.get('permissions', [])}")
```

## 📊 参数映射总结

| 参数来源 | 格式示例 | 提取位置 | 优先级 | 用途 |
|---------|---------|---------|--------|------|
| URL查询参数 | `?config_lang=zh&type=news` | `query_params` | 2 | 用户偏好设置 |
| config_前缀参数 | `?config_language=chinese` | `custom_config` | 1 | 高优先级配置 |
| 请求头 | `X-Language: chinese` | `headers` | 3 | 客户端环境信息 |
| POST请求体 | `config.configurable.*` | `custom_config` | 1 | 复杂配置对象 |
| 路径参数 | `/threads/{id}/runs` | `path_params` | - | 资源标识符 |

## 🎯 最佳实践

1. **参数命名规范**：
   - URL参数：`config_xxx` 用于高优先级配置
   - 请求头：`X-xxx` 用于客户端信息
   - POST体：`config.configurable` 用于复杂配置

2. **参数验证**：
   - 始终提供默认值
   - 验证参数类型和范围
   - 记录参数来源用于调试

3. **性能考虑**：
   - 缓存频繁使用的参数
   - 避免在每个节点中重复解析
   - 使用懒加载获取复杂参数

4. **安全考虑**：
   - 过滤敏感请求头
   - 验证参数权限
   - 记录参数访问日志

通过这套完整的参数透传方案，你可以将任何HTTP请求参数传递到LangGraph的Agent节点中，实现高度个性化和可配置的AI应用！ 