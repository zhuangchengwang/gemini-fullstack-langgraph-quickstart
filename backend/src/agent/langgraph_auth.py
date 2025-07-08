"""LangGraph 官方认证集成"""

from langgraph_sdk import Auth
from agent.auth import verify_token

# 创建认证实例
my_auth = Auth()

@my_auth.authenticate
async def authenticate(authorization: str) -> str:
    """
    LangGraph 官方认证函数
    
    Args:
        authorization: Authorization header 的值（例如："Bearer <token>"）
        
    Returns:
        用户ID字符串
        
    Raises:
        Auth.exceptions.HTTPException: 认证失败时抛出401错误
    """
    print(f"🔍 LangGraph Auth: 收到认证请求，authorization: {authorization}")
    
    # 解析 Bearer token
    if not authorization or not authorization.startswith("Bearer "):
        print(f"❌ LangGraph Auth: 无效的 Authorization 格式")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    # 提取 token
    token = authorization.split(" ", 1)[-1]  # "Bearer <token>"
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
        return username
        
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