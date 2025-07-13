# 🚀 LangGraph + FastAPI 全栈开发教程

> 本教程专为有编程基础但对 Python 高阶语法、FastAPI、LangGraph 不熟悉的开发者设计

## 📋 目录

1. [Python 高阶语法速成](#1-python-高阶语法速成)
2. [FastAPI 核心概念](#2-fastapi-核心概念)
3. [LangGraph 框架理解](#3-langgraph-框架理解)
4. [项目架构解析](#4-项目架构解析)
5. [认证系统深度解析](#5-认证系统深度解析)
6. [实战技巧与最佳实践](#6-实战技巧与最佳实践)

---

## 1. Python 高阶语法速成

### 1.1 异步编程 (async/await)

```python
# 同步代码 - 阻塞执行
def sync_function():
    time.sleep(1)  # 阻塞 1 秒
    return "完成"

# 异步代码 - 非阻塞执行
async def async_function():
    await asyncio.sleep(1)  # 非阻塞等待 1 秒
    return "完成"

# 调用异步函数
async def main():
    result = await async_function()  # 必须用 await
    print(result)

# 运行异步代码
asyncio.run(main())
```

**为什么需要异步？**
- 处理 I/O 操作（数据库、网络请求）时不阻塞
- 提高并发性能
- FastAPI 和 LangGraph 都是异步框架

### 1.2 装饰器 (Decorators)

```python
# 基础装饰器
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("函数执行前")
        result = func(*args, **kwargs)
        print("函数执行后")
        return result
    return wrapper

@my_decorator
def say_hello(name):
    print(f"Hello, {name}!")

# 等价于: say_hello = my_decorator(say_hello)

# FastAPI 中的装饰器示例
@app.get("/users")  # 路由装饰器
async def get_users():
    return {"users": []}

@auth.authenticate  # LangGraph 认证装饰器
async def authenticate(request):
    return "user_id"
```

### 1.3 类型注解 (Type Hints)

```python
from typing import Optional, List, Dict, Any

# 基础类型注解
def greet(name: str, age: int) -> str:
    return f"Hello {name}, you are {age} years old"

# 复杂类型注解
def process_users(users: List[Dict[str, Any]]) -> Optional[str]:
    if not users:
        return None
    return users[0].get("name")

# Pydantic 模型（FastAPI 常用）
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    age: Optional[int] = None

# 自动验证和序列化
user = User(username="john", email="john@example.com")
```

### 1.4 上下文管理器 (Context Managers)

```python
# 自动资源管理
async with AsyncSession() as db:
    user = await get_user(db, user_id=1)
    # db 会自动关闭

# 等价于:
db = AsyncSession()
try:
    user = await get_user(db, user_id=1)
finally:
    await db.close()
```

### 1.5 生成器和迭代器

```python
# 生成器 - 内存高效的迭代
def number_generator(n):
    for i in range(n):
        yield i * 2  # 惰性计算

# 异步生成器 - FastAPI 流式响应
async def stream_data():
    for i in range(100):
        await asyncio.sleep(0.1)
        yield f"data chunk {i}\n"

@app.get("/stream")
async def stream_endpoint():
    return StreamingResponse(stream_data(), media_type="text/plain")
```

---

## 2. FastAPI 核心概念

### 2.1 FastAPI 基础架构

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

# 创建应用实例
app = FastAPI(
    title="我的 API",
    description="API 文档描述",
    version="1.0.0"
)

# 中间件 - 在请求/响应之间执行
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2.2 路由和请求处理

```python
# GET 请求
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}

# POST 请求 - 接收 JSON 数据
@app.post("/users")
async def create_user(user: User):  # 自动验证和解析
    return {"message": "用户创建成功", "user": user}

# 查询参数
@app.get("/items")
async def get_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

# 请求头
@app.get("/protected")
async def protected_route(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="需要认证")
    return {"message": "受保护的资源"}
```

### 2.3 依赖注入系统

```python
# 依赖函数
async def get_db():
    db = AsyncSession()
    try:
        yield db
    finally:
        await db.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    # 验证 token 并返回用户
    user = await verify_token_and_get_user(token, db)
    return user

# 在路由中使用依赖
@app.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### 2.4 错误处理

```python
# 自定义异常
class UserNotFoundError(Exception):
    pass

# 异常处理器
@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"message": "用户未找到"}
    )

# 在路由中抛出异常
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await find_user(user_id)
    if not user:
        raise UserNotFoundError()
    return user
```

---

## 3. LangGraph 框架理解

### 3.1 LangGraph 核心概念

```python
# LangGraph 是一个用于构建有状态、多参与者应用的框架
from langgraph import StateGraph
from typing import TypedDict

# 1. 定义状态
class State(TypedDict):
    messages: List[str]
    user_input: str
    response: str

# 2. 定义节点函数
async def process_input(state: State) -> State:
    user_input = state["user_input"]
    # 处理用户输入
    processed = f"处理后的输入: {user_input}"
    return {
        **state,
        "messages": state["messages"] + [processed]
    }

async def generate_response(state: State) -> State:
    # 生成响应
    response = "这是 AI 的回复"
    return {
        **state,
        "response": response
    }

# 3. 构建图
graph = StateGraph(State)
graph.add_node("process", process_input)
graph.add_node("generate", generate_response)
graph.add_edge("process", "generate")
graph.set_entry_point("process")
graph.set_finish_point("generate")

# 4. 编译图
app = graph.compile()
```

### 3.2 LangGraph 认证机制

```python
from langgraph_sdk import Auth

# 创建认证实例
auth = Auth()

@auth.authenticate
async def authenticate(authorization: str) -> str:
    """
    LangGraph 官方认证函数
    
    Args:
        authorization: "Bearer <token>" 格式的认证头
        
    Returns:
        用户ID字符串
        
    Raises:
        Auth.exceptions.HTTPException: 认证失败时抛出
    """
    if not authorization.startswith("Bearer "):
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="无效的认证头"
        )
    
    token = authorization.split(" ")[1]
    user_id = verify_jwt_token(token)
    
    if not user_id:
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Token 无效"
        )
    
    return user_id
```

### 3.3 LangGraph 配置文件

```json
// langgraph.json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent/graph.py:graph"
  },
  "http": {
    "app": "./src/agent/app.py:app"
  },
  "auth": {
    "path": "./src/agent/langgraph_auth.py:auth",
    "openapi": {
      "securitySchemes": {
        "bearerAuth": {
          "type": "http",
          "scheme": "bearer",
          "bearerFormat": "JWT"
        }
      },
      "security": [{ "bearerAuth": [] }]
    }
  }
}
```

---

## 4. 项目架构解析

### 4.1 后端架构

```
backend/
├── src/agent/
│   ├── __init__.py
│   ├── app.py              # FastAPI 应用入口
│   ├── auth.py             # JWT 认证逻辑
│   ├── database.py         # 数据库连接和模型
│   ├── routes.py           # API 路由定义
│   ├── schemas.py          # Pydantic 数据模型
│   ├── langgraph_auth.py   # LangGraph 认证集成
│   └── graph.py            # LangGraph 图定义
├── langgraph.json          # LangGraph 配置
└── pyproject.toml          # Python 依赖管理
```

### 4.2 前端架构

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/           # 认证相关组件
│   │   └── ui/             # UI 组件库
│   ├── contexts/
│   │   └── AuthContext.tsx # 全局认证状态
│   ├── hooks/
│   │   └── useAuthenticatedStream.ts # 认证流处理
│   └── App.tsx             # 主应用组件
```

### 4.3 数据流向

```
用户操作 → 前端组件 → AuthContext → useAuthenticatedStream 
    ↓
JWT Token → LangGraph API → LangGraph Auth → FastAPI → 数据库
    ↓
响应数据 ← 前端更新 ← 流式响应 ← 图执行结果
```

---

## 5. 认证系统深度解析

### 5.1 JWT (JSON Web Token) 原理

```python
# JWT 结构: header.payload.signature
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

import jwt
from datetime import datetime, timedelta

# 创建 JWT
def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,  # subject (用户ID)
        "exp": datetime.utcnow() + timedelta(hours=24),  # 过期时间
        "iat": datetime.utcnow()  # 签发时间
    }
    token = jwt.encode(payload, "secret_key", algorithm="HS256")
    return token

# 验证 JWT
def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token 过期
    except jwt.InvalidTokenError:
        return None  # Token 无效
```

### 5.2 密码安全处理

```python
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 加密密码
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 用户注册示例
async def register_user(username: str, password: str):
    hashed_password = hash_password(password)
    user = User(username=username, password_hash=hashed_password)
    await save_user(user)
```

### 5.3 数据库异步操作

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 创建异步引擎
engine = create_async_engine("sqlite+aiosqlite:///./users.db")

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 依赖注入：获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# 数据库操作示例
async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()
```

---

## 6. 实战技巧与最佳实践

### 6.1 错误处理最佳实践

```python
# 1. 使用自定义异常类
class AuthenticationError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code

# 2. 统一错误处理中间件
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except AuthenticationError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.message}
        )
    except Exception as e:
        logger.error(f"未处理的错误: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "内部服务器错误"}
        )
```

### 6.2 环境配置管理

```python
# settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    jwt_secret_key: str = "your-secret-key"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()

# .env 文件
JWT_SECRET_KEY=your-super-secret-key
DATABASE_URL=sqlite+aiosqlite:///./production.db
DEBUG=false
```

### 6.3 日志记录

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 在代码中使用日志
@app.post("/login")
async def login(credentials: LoginRequest):
    logger.info(f"用户登录尝试: {credentials.username}")
    
    try:
        user = await authenticate_user(credentials)
        logger.info(f"用户登录成功: {user.username}")
        return {"token": create_token(user.id)}
    except AuthenticationError as e:
        logger.warning(f"登录失败: {e.message}")
        raise HTTPException(status_code=401, detail=e.message)
```

### 6.4 测试策略

```python
import pytest
from httpx import AsyncClient

# 测试 FastAPI 端点
@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={
            "username": "test@example.com",
            "password": "testpass"
        })
    assert response.status_code == 200
    assert "token" in response.json()

# 测试数据库操作
@pytest.mark.asyncio
async def test_create_user():
    async with AsyncSessionLocal() as db:
        user = await create_user(db, "test@example.com", "password")
        assert user.username == "test@example.com"
```

### 6.5 性能优化技巧

```python
# 1. 数据库连接池
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # 连接池大小
    max_overflow=0,  # 最大溢出连接
    pool_pre_ping=True  # 连接前检查
)

# 2. 缓存常用数据
from functools import lru_cache

@lru_cache(maxsize=128)
def get_user_permissions(user_id: str):
    # 缓存用户权限信息
    return fetch_permissions_from_db(user_id)

# 3. 异步并发处理
import asyncio

async def process_multiple_requests(requests):
    tasks = [process_single_request(req) for req in requests]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 🎯 总结

### 关键概念回顾

1. **异步编程**: 使用 `async/await` 处理 I/O 操作
2. **FastAPI**: 现代、快速的 Web 框架，自动文档生成
3. **LangGraph**: 有状态的 AI 应用框架，支持复杂工作流
4. **JWT 认证**: 无状态的令牌认证机制
5. **依赖注入**: 管理组件之间的依赖关系

### 学习路径建议

1. **先掌握 Python 异步编程基础**
2. **熟悉 FastAPI 的路由和依赖注入**
3. **理解 LangGraph 的状态管理和图构建**
4. **实践 JWT 认证和数据库操作**
5. **学习错误处理和测试最佳实践**

### 常用命令速查

```bash
# 启动开发服务器
make dev

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest

# 查看 API 文档
# 访问 http://localhost:8000/docs
```

这个教程涵盖了项目中用到的所有核心技术。建议按顺序学习，每个概念都配有实际代码示例。有问题随时可以参考这个文档！🚀 