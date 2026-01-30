"""
認證 API 端點
對應 tasks.md T063: 實作認證 API

提供登入、登出、Token 刷新功能。
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import get_current_user, TokenData
from src.services.auth_service import (
    AuthService,
    AuthenticationError,
    InvalidTokenError,
    UserInactiveError,
)

router = APIRouter(prefix="/api/auth", tags=["認證"])


# ==================== 請求/回應模型 ====================

class LoginRequest(BaseModel):
    """登入請求"""
    username: str = Field(..., min_length=1, max_length=50, description="使用者名稱")
    password: str = Field(..., min_length=1, description="密碼")


class LoginResponse(BaseModel):
    """登入回應"""
    access_token: str = Field(..., description="Access Token")
    refresh_token: str = Field(..., description="Refresh Token")
    token_type: str = Field(default="bearer", description="Token 類型")
    user: dict = Field(..., description="使用者資訊")


class RefreshRequest(BaseModel):
    """Token 刷新請求"""
    refresh_token: str = Field(..., description="Refresh Token")


class RefreshResponse(BaseModel):
    """Token 刷新回應"""
    access_token: str = Field(..., description="新的 Access Token")
    token_type: str = Field(default="bearer", description="Token 類型")


class LogoutResponse(BaseModel):
    """登出回應"""
    message: str = Field(default="登出成功", description="訊息")


class UserInfoResponse(BaseModel):
    """使用者資訊回應"""
    id: int
    username: str
    display_name: str
    email: Optional[str]
    role: str
    department: Optional[str]
    is_active: bool


# ==================== API 端點 ====================

@router.post("/login", response_model=LoginResponse, summary="使用者登入")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    使用者登入

    使用帳號密碼登入，成功後返回 Access Token 和 Refresh Token。

    - **username**: 使用者名稱
    - **password**: 密碼
    """
    auth_service = AuthService(db)

    try:
        result = auth_service.login(request.username, request.password)

        return LoginResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
            user={
                "id": result.user.id,
                "username": result.user.username,
                "display_name": result.user.display_name,
                "email": result.user.email,
                "role": result.user.role,
                "department": result.user.department,
            }
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except UserInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/refresh", response_model=RefreshResponse, summary="刷新 Token")
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    刷新 Access Token

    使用 Refresh Token 取得新的 Access Token。

    - **refresh_token**: Refresh Token
    """
    auth_service = AuthService(db)

    try:
        result = auth_service.refresh_token(request.refresh_token)

        return RefreshResponse(
            access_token=result.access_token,
            token_type=result.token_type
        )

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except UserInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/logout", response_model=LogoutResponse, summary="使用者登出")
async def logout(
    current_user: TokenData = Depends(get_current_user)
):
    """
    使用者登出

    由於 JWT 是無狀態的，實際的登出行為由前端清除 Token 完成。
    此端點僅作為確認登出的標準化接口。

    **安全性說明**:
    目前實作中，Token 在過期前仍然有效（無狀態設計）。
    若需要更高安全性（如即時失效已登出的 Token），建議：
    1. 實作 Token 黑名單（使用 Redis 存儲已登出的 Token jti）
    2. 黑名單 TTL 設定為 Token 剩餘有效時間
    3. 在認證中間件中檢查黑名單
    """
    return LogoutResponse(message="登出成功")


@router.get("/me", response_model=UserInfoResponse, summary="取得當前使用者資訊")
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得當前登入使用者的資訊

    需要在 Header 中提供有效的 Access Token。
    """
    from src.services.user_service import UserService

    user_service = UserService(db)
    user = user_service.get_by_id(current_user.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在"
        )

    return UserInfoResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        department=user.department,
        is_active=user.is_active
    )


@router.post("/change-password", summary="變更密碼")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    變更當前使用者的密碼

    - **old_password**: 舊密碼
    - **new_password**: 新密碼
    """
    from src.services.user_service import (
        UserService,
        InvalidPasswordError,
        WeakPasswordError,
    )

    user_service = UserService(db)

    try:
        user_service.change_password(
            user_id=current_user.user_id,
            old_password=old_password,
            new_password=new_password
        )

        return {"message": "密碼變更成功"}

    except InvalidPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="舊密碼錯誤"
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
