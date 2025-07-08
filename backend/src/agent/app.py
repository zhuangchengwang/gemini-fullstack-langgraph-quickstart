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

# 注意：LangGraph API 现在通过 langgraph.json 中的 auth 配置进行保护
# 这些 API 包括: /threads, /runs, /assistants, /crons, /store
print("🔐 LangGraph API 现在通过官方认证机制保护")

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

# 注意：移除了代理路由以避免与 LangGraph 原生 API 冲突
# 如果需要拦截原生 API，应该在中间件中处理，而不是创建新路由

# 2. 完全自定义的新接口
@app.get("/analytics/threads")
async def get_thread_analytics():
    """全新的分析接口"""
    try:
        # 获取原始数据 - 注意：在生产环境中这里应该直接访问内部数据而不是HTTP调用
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
        "authentication": "enabled via LangGraph",
        "auth_method": "JWT Bearer Token",
        "protected_apis": ["/threads", "/runs", "/assistants", "/crons", "/store"]
    }

@app.get("/auth-info")
async def auth_info():
    """获取认证配置信息"""
    return {
        "authentication_method": "LangGraph Official Auth",
        "protected_endpoints": ["/threads", "/runs", "/assistants", "/crons", "/store"],
        "public_endpoints": ["/app", "/auth", "/static", "/health", "/auth-info"],
        "login_endpoint": "/auth/login",
        "register_endpoint": "/auth/register", 
        "user_info_endpoint": "/auth/me",
        "auth_header_format": "Authorization: Bearer <jwt_token>",
        "note": "LangGraph APIs are now protected by official LangGraph auth mechanism"
    }

@app.get("/test-auth")
async def test_auth_status(request: Request):
    """测试认证状态的接口"""
    auth_header = request.headers.get("Authorization")
    username = getattr(request.state, 'username', None)
    
    return {
        "path": "/test-auth",
        "is_protected": False,  # 这个接口本身不受保护
        "auth_header_present": bool(auth_header),
        "auth_header_preview": auth_header[:20] + "..." if auth_header else None,
        "username_from_state": username,
        "enforce_auth_setting": ENFORCE_AUTH,
        "test_protected_paths": {
            "threads_protected": "/threads" in [p for p in PROTECTED_LANGGRAPH_PATHS if ENFORCE_AUTH],
            "runs_protected": "/runs" in [p for p in PROTECTED_LANGGRAPH_PATHS if ENFORCE_AUTH]
        },
        "suggestion": "尝试访问 /threads 来测试认证是否工作"
    }


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
