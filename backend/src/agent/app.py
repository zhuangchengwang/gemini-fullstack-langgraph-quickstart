# mypy: disable - error - code = "no-untyped-def,misc"
import os
import pathlib
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from agent.database import create_tables
from agent.routes import auth_router
from agent.auth import check_auth_header, requires_auth
import httpx
from typing import Any, Dict

# Define the FastAPI app
app = FastAPI(title="LangGraph Agent API", description="AI Agent with Authentication")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database tables will be created on first use
# Note: Tables will be auto-created when first database operation occurs

# Include authentication routes
app.include_router(auth_router)

# Check if authentication should be enforced (default: True to protect LangGraph APIs)
ENFORCE_AUTH = os.getenv("ENFORCE_AUTH", "true").lower() == "true"

# LangGraph API endpoints that should be protected by default
PROTECTED_LANGGRAPH_PATHS = [
    "/threads",
    "/runs", 
    "/assistants",
    "/crons",
    "/store"
]

# Public endpoints that don't require authentication
PUBLIC_PATHS = [
    "/app",          # Frontend routes
    "/auth",         # Authentication routes  
    "/static",       # Static files
    "/",             # Root
    "/docs",         # API documentation
    "/openapi.json", # OpenAPI spec
    "/redoc",        # ReDoc documentation
    "/health",       # Health check (if exists)
    "/ping"          # Ping endpoint (if exists)
]

# === 扩展 LangGraph API 的示例 ===

# 1. 自定义路由覆盖示例
@app.get("/threads/enhanced")
async def get_enhanced_threads(request: Request):
    """扩展版的 threads 接口，添加自定义逻辑"""
    try:
        # 调用原始 LangGraph API
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:2024/threads")
            threads_data = response.json() if response.status_code == 200 else []
        
        # 添加自定义信息
        enhanced_threads = []
        for thread in threads_data:
            enhanced_thread = {
                **thread,
                "custom_metadata": {
                    "enhanced": True,
                    "user_id": getattr(request.state, 'username', 'anonymous'),
                    "api_version": "v2"
                }
            }
            enhanced_threads.append(enhanced_thread)
        
        return {
            "threads": enhanced_threads,
            "total": len(enhanced_threads),
            "enhanced_features": ["user_tracking", "metadata", "analytics"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced API error: {str(e)}")

# 2. 代理模式示例 - 拦截并增强现有接口
@app.api_route("/threads/{thread_id}", methods=["GET", "PUT", "DELETE"])
async def enhanced_thread_operations(thread_id: str, request: Request):
    """代理并增强单个线程的操作"""
    method = request.method
    username = getattr(request.state, 'username', 'anonymous')
    
    # 记录操作日志（示例）
    print(f"用户 {username} 对线程 {thread_id} 执行 {method} 操作")
    
    # 转发到原始 LangGraph API
    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(f"http://localhost:2024/threads/{thread_id}")
            elif method == "PUT":
                body = await request.body()
                response = await client.put(f"http://localhost:2024/threads/{thread_id}", content=body)
            elif method == "DELETE":
                response = await client.delete(f"http://localhost:2024/threads/{thread_id}")
            
            # 返回增强的响应
            if response.status_code == 200:
                data = response.json()
                data["_metadata"] = {
                    "accessed_by": username,
                    "api_version": "enhanced",
                    "operation": method
                }
                return data
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Upstream service error: {str(e)}")

# 3. 完全自定义的新接口
@app.get("/analytics/threads")
async def get_thread_analytics():
    """全新的分析接口"""
    try:
        # 获取原始数据
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:2024/threads")
            threads = response.json() if response.status_code == 200 else []
        
        # 生成分析数据
        analytics = {
            "total_threads": len(threads),
            "active_threads": len([t for t in threads if t.get("status") == "active"]),
            "thread_creation_trend": "增长",  # 这里可以加入真实的分析逻辑
            "most_active_hour": "14:00-15:00",
            "custom_metrics": {
                "avg_messages_per_thread": 5.2,
                "user_engagement": "高"
            }
        }
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

# === 系统接口 ===

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "LangGraph Agent API",
        "authentication": "enabled" if ENFORCE_AUTH else "disabled",
        "protected_paths": PROTECTED_LANGGRAPH_PATHS if ENFORCE_AUTH else [],
        "public_paths": PUBLIC_PATHS
    }

@app.get("/auth-info")
async def auth_info():
    """获取认证配置信息"""
    return {
        "authentication_required": ENFORCE_AUTH,
        "protected_endpoints": PROTECTED_LANGGRAPH_PATHS,
        "public_endpoints": PUBLIC_PATHS,
        "login_endpoint": "/auth/login",
        "register_endpoint": "/auth/register",
        "user_info_endpoint": "/auth/me"
    }

# JWT Authentication middleware for LangGraph API routes
@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    """JWT Authentication middleware to protect LangGraph API routes.
    
    By default, all LangGraph APIs require authentication.
    Set ENFORCE_AUTH=false environment variable to disable authentication protection.
    """
    path = request.url.path
    
    # Check if path is in public routes (no auth required)
    is_public_path = any(path.startswith(public_path) for public_path in PUBLIC_PATHS)
    
    if is_public_path:
        response = await call_next(request)
        return response
    
    # Check if authentication is enforced and path needs protection
    needs_auth = False
    
    if ENFORCE_AUTH:
        # Check if this is a LangGraph API path that needs protection
        is_langgraph_api = any(path.startswith(protected_path) for protected_path in PROTECTED_LANGGRAPH_PATHS)
        
        if is_langgraph_api:
            needs_auth = True
    
    # Enforce authentication if required
    if needs_auth:
        username = check_auth_header(request)
        if not username:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Authentication required for LangGraph API access",
                    "error_code": "UNAUTHORIZED",
                    "required_header": "Authorization: Bearer <jwt_token>",
                    "login_endpoint": "/auth/login"
                }
            )
        
        # Add username to request state for potential use in enhanced endpoints
        request.state.username = username
        
        # Log API access for security auditing
        print(f"🔐 用户 '{username}' 访问 LangGraph API: {request.method} {path}")
    
    response = await call_next(request)
    return response


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    return StaticFiles(directory=build_path, html=True)


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)
