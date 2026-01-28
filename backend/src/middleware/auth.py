"""
認證中間件
對應 tasks.md T021: 實作認證中間件

功能：
- 從 HTTP Header 提取 Bearer Token
- 驗證 JWT Token 有效性
- 將使用者資訊注入請求上下文
"""

from typing import Optional

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, ExpiredSignatureError

from src.utils.jwt import get_jwt_handler
from src.utils.logger import log_auth_event, log_security_event


# HTTP Bearer 認證方案
security = HTTPBearer(auto_error=False)


class TokenData:
    """
    Token 資料容器

    儲存從 JWT Token 解析出的使用者資訊。
    """

    def __init__(
        self,
        user_id: int,
        username: str,
        role: str,
        department: Optional[str] = None
    ):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.department = department

    def __repr__(self) -> str:
        return f"TokenData(user_id={self.user_id}, username={self.username}, role={self.role}, department={self.department})"


def extract_token(authorization: str) -> Optional[str]:
    """
    從 Authorization header 提取 Token

    支援格式：Bearer <token>

    Args:
        authorization: Authorization header 值

    Returns:
        Token 字串，如果格式不正確則返回 None
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenData:
    """
    依賴注入：取得當前已認證的使用者

    從 JWT Token 解析使用者資訊。
    如果 Token 無效或已過期，拋出 401 錯誤。

    Args:
        credentials: HTTP 認證憑證（由 FastAPI 自動注入）

    Returns:
        TokenData: 使用者資訊

    Raises:
        HTTPException: 401 未授權
    """
    # 檢查是否提供 Token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    jwt_handler = get_jwt_handler()

    try:
        # 驗證並解析 Token
        payload = jwt_handler.verify_token(token)

        # 檢查 Token 類型
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 類型錯誤",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 提取使用者資訊
        user_id = int(payload.get("sub"))
        username = payload.get("username")
        role = payload.get("role")
        department = payload.get("department")

        if not all([user_id, username, role]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 資料不完整",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            department=department
        )

    except ExpiredSignatureError:
        log_auth_event("token_expired", extra={"token_prefix": token[:20] + "..."})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已過期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        log_security_event(
            f"無效的 JWT Token: {str(e)}",
            severity="warning",
            token_prefix=token[:20] + "..."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (ValueError, TypeError) as e:
        log_security_event(
            f"Token 解析錯誤: {str(e)}",
            severity="warning"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 解析失敗",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenData]:
    """
    依賴注入：取得當前使用者（可選）

    與 get_current_user 類似，但如果未提供 Token 則返回 None，
    而不是拋出錯誤。適用於可公開存取但登入後有額外功能的端點。

    Args:
        credentials: HTTP 認證憑證

    Returns:
        TokenData | None: 使用者資訊，如果未認證則為 None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# 便捷別名
CurrentUser = Depends(get_current_user)
OptionalUser = Depends(get_current_user_optional)
