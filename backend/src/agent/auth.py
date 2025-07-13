"""Authentication utilities and JWT token handling."""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from agent.database import get_db, get_user_by_username, User
from sqlalchemy.ext.asyncio import AsyncSession

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(hours=24)

security = HTTPBearer()


def create_access_token(data: Dict[str, Any]) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + JWT_EXPIRATION_DELTA
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_username(db, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def check_auth_header(request: Request) -> Optional[str]:
    """Extract and validate auth header from request."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if payload is None:
        return None
    
    return payload.get("sub")  # Return username if token is valid


# LangGraph API paths that require authentication
PROTECTED_PATHS = [
    "/threads/enhanced",  # 自定义增强版threads接口需要认证
    "/threads/create",    # 创建线程需要认证
    "/threads/delete",    # 删除线程需要认证
    "/runs", 
    "/assistants",
    "/crons",
    "/store"
]

# 不需要认证的特定路径
UNPROTECTED_PATHS = [
    "/threads/{thread_id}/history"  # 线程历史记录不需要认证
]

def requires_auth(path: str) -> bool:
    """Check if a path requires authentication."""
    # 首先检查是否在不需要认证的路径列表中
    for unprotected_path in UNPROTECTED_PATHS:
        # 将路径模板中的参数替换为通配符进行匹配
        pattern = unprotected_path.replace("{thread_id}", "[^/]+")
        if path.startswith(pattern.split("{")[0]) and path.endswith(pattern.split("}")[-1]):
            return False
    
    # 如果不在不需要认证的路径列表中，则检查是否需要认证
    return any(path.startswith(prefix) for prefix in PROTECTED_PATHS) 