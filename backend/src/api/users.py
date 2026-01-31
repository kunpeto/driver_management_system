"""
使用者管理 API 端點
對應 tasks.md T064: 實作使用者管理 API

提供使用者 CRUD 功能，僅 Admin 可存取。
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import require_admin, Role
from src.services.user_service import (
    UserService,
    UserNotFoundError,
    DuplicateUsernameError,
    WeakPasswordError,
)

router = APIRouter(prefix="/api/users", tags=["使用者管理"])


# ==================== 請求/回應模型 ====================

class UserCreateRequest(BaseModel):
    """建立使用者請求"""
    username: str = Field(..., min_length=3, max_length=50, description="使用者名稱")
    password: str = Field(..., min_length=8, description="密碼")
    display_name: str = Field(..., min_length=1, max_length=100, description="顯示名稱")
    email: Optional[str] = Field(None, description="電子郵件")
    role: str = Field(default="staff", description="角色：admin, manager, staff")
    department: Optional[str] = Field(None, description="部門：淡海, 安坑")
    is_active: bool = Field(default=True, description="是否啟用")


class UserUpdateRequest(BaseModel):
    """更新使用者請求"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="顯示名稱")
    email: Optional[str] = Field(None, description="電子郵件")
    role: Optional[str] = Field(None, description="角色")
    department: Optional[str] = Field(None, description="部門")
    is_active: Optional[bool] = Field(None, description="是否啟用")


class ResetPasswordRequest(BaseModel):
    """重設密碼請求"""
    new_password: str = Field(..., min_length=8, description="新密碼")


class UserResponse(BaseModel):
    """使用者回應"""
    id: int
    username: str
    display_name: str
    email: Optional[str]
    role: str
    department: Optional[str]
    is_active: bool
    last_login_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """使用者列表回應"""
    items: list[UserResponse]
    total: int
    skip: int
    limit: int


# ==================== 輔助函數 ====================

def user_to_response(user) -> UserResponse:
    """將使用者物件轉換為回應模型"""
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )


# ==================== API 端點 ====================

@router.get("", response_model=UserListResponse, summary="取得使用者列表")
async def list_users(
    role: Optional[str] = Query(None, description="角色篩選"),
    department: Optional[str] = Query(None, description="部門篩選"),
    is_active: Optional[bool] = Query(None, description="是否啟用篩選"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(50, ge=1, le=100, description="回傳筆數"),
    current_user: TokenData = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    取得使用者列表

    僅 Admin 可存取。

    - **role**: 角色篩選（admin, manager, staff）
    - **department**: 部門篩選（淡海, 安坑）
    - **is_active**: 是否啟用篩選
    """
    user_service = UserService(db)

    users = user_service.list_users(
        role=role,
        department=department,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

    total = user_service.count_users(
        role=role,
        department=department,
        is_active=is_active
    )

    return UserListResponse(
        items=[user_to_response(u) for u in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{user_id}", response_model=UserResponse, summary="取得單一使用者")
async def get_user(
    user_id: int,
    current_user: TokenData = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    取得單一使用者詳情

    僅 Admin 可存取。
    """
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"使用者 ID {user_id} 不存在"
        )

    return user_to_response(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="建立使用者")
async def create_user(
    request: UserCreateRequest,
    current_user: TokenData = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    建立新使用者

    僅 Admin 可存取。

    - **username**: 使用者名稱（3-50 字元）
    - **password**: 密碼（至少 8 字元，包含大小寫字母和數字）
    - **display_name**: 顯示名稱
    - **role**: 角色（預設 staff）
    - **department**: 部門（非 admin 必須指定）
    """
    user_service = UserService(db)

    try:
        user = user_service.create(
            username=request.username,
            password=request.password,
            display_name=request.display_name,
            email=request.email,
            role=request.role,
            department=request.department,
            is_active=request.is_active
        )

        return user_to_response(user)

    except DuplicateUsernameError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserResponse, summary="更新使用者")
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: TokenData = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    更新使用者資訊

    僅 Admin 可存取。
    """
    user_service = UserService(db)

    try:
        user = user_service.update(
            user_id=user_id,
            display_name=request.display_name,
            email=request.email,
            role=request.role,
            department=request.department,
            is_active=request.is_active
        )

        return user_to_response(user)

    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{user_id}/reset-password", summary="重設密碼")
async def reset_password(
    user_id: int,
    request: ResetPasswordRequest,
    current_user: TokenData = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    重設使用者密碼

    僅 Admin 可存取。管理員可以直接重設任何使用者的密碼，不需要舊密碼。
    """
    user_service = UserService(db)

    try:
        user_service.reset_password(
            user_id=user_id,
            new_password=request.new_password
        )

        return {"message": "密碼重設成功"}

    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{user_id}/activate", summary="啟用使用者")
async def activate_user(
    user_id: int,
    current_user: TokenData = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    啟用使用者帳號

    僅 Admin 可存取。
    """
    user_service = UserService(db)

    try:
        user_service.activate(user_id)
        return {"message": "使用者已啟用"}

    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{user_id}/deactivate", summary="停用使用者")
async def deactivate_user(
    user_id: int,
    current_user: TokenData = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    停用使用者帳號

    僅 Admin 可存取。不允許停用自己的帳號。
    """
    # 檢查是否停用自己
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能停用自己的帳號"
        )

    user_service = UserService(db)

    try:
        user_service.deactivate(user_id)
        return {"message": "使用者已停用"}

    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除使用者")
async def delete_user(
    user_id: int,
    current_user: TokenData = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """
    刪除使用者

    僅 Admin 可存取。不允許刪除自己的帳號。
    建議使用停用而非刪除，以保留歷史紀錄。
    """
    # 檢查是否刪除自己
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能刪除自己的帳號"
        )

    user_service = UserService(db)

    try:
        user_service.delete(user_id)

    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== 系統初始化端點 ====================

@router.post("/init-admin", summary="初始化管理員帳號")
def init_admin(db: Session = Depends(get_db)):
    """
    初始化預設管理員帳號

    安全性：只有在系統中完全沒有使用者時才能執行。
    如果已有任何使用者存在，將返回錯誤。

    預設帳號：admin / admin123
    """
    from src.models.user import User
    from src.utils.password import hash_password

    # 檢查是否已有使用者
    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"系統中已有 {user_count} 個使用者，無法初始化管理員帳號。如需重設，請聯繫系統管理員。"
        )

    # 建立預設管理員
    admin_user = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        display_name="系統管理員",
        role="admin",
        department=None,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return {
        "message": "預設管理員帳號建立成功",
        "username": "admin",
        "password": "admin123",
        "warning": "請登入後立即修改預設密碼！"
    }
