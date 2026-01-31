"""
系統設定 API 端點
對應 tasks.md T038: 實作系統設定 API

修復 Gemini Review High Priority #2: 加入權限驗證
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import require_admin, require_role, Role
from src.models.system_setting import DepartmentScope
from src.services.system_setting_service import (
    DuplicateSettingError,
    SettingNotFoundError,
    SystemSettingService,
)

router = APIRouter()


# ============================================================
# Pydantic 模型
# ============================================================

class SettingCreate(BaseModel):
    """建立設定請求"""
    key: str = Field(..., min_length=1, max_length=100, description="設定鍵名")
    value: Optional[str] = Field(None, description="設定值")
    department: Optional[str] = Field(
        None,
        description="部門範圍：淡海、安坑、global"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="設定說明"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "key": "google_sheets_id",
                    "value": "1ABC123...",
                    "department": "淡海",
                    "description": "淡海班表 Google Sheets ID"
                }
            ]
        }
    }


class SettingUpdate(BaseModel):
    """更新設定請求"""
    value: Optional[str] = Field(None, description="設定值")
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="設定說明"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "value": "1XYZ456...",
                    "description": "更新後的說明"
                }
            ]
        }
    }


class SettingResponse(BaseModel):
    """設定回應"""
    id: int
    key: str
    value: Optional[str]
    department: Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


class SettingListResponse(BaseModel):
    """設定列表回應"""
    total: int
    items: list[SettingResponse]


class BulkUpsertRequest(BaseModel):
    """批次更新請求"""
    settings: list[SettingCreate]


class DepartmentConfigResponse(BaseModel):
    """部門配置回應"""
    department: str
    settings: dict


# ============================================================
# API 端點
# ============================================================

@router.get(
    "",
    response_model=SettingListResponse,
    summary="取得所有設定",
    description="取得所有系統設定，可選擇按部門篩選（需要登入）"
)
def get_settings(
    department: Optional[str] = None,
    include_global: bool = True,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    取得所有系統設定

    - **department**: 篩選指定部門（淡海、安坑）
    - **include_global**: 是否包含全域設定（預設 True）
    """
    service = SystemSettingService(db)

    if department:
        items = service.list_by_department(department, include_global)
    else:
        items = service.list_all()

    return SettingListResponse(
        total=len(items),
        items=[SettingResponse.model_validate(item) for item in items]
    )


@router.get(
    "/{setting_id}",
    response_model=SettingResponse,
    summary="取得單一設定",
    description="根據 ID 取得單一系統設定（需要登入）"
)
def get_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得單一系統設定"""
    service = SystemSettingService(db)
    setting = service.get_by_id(setting_id)

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"設定 ID {setting_id} 不存在"
        )

    return SettingResponse.model_validate(setting)


@router.get(
    "/key/{key}",
    response_model=SettingResponse,
    summary="根據鍵名取得設定",
    description="根據鍵名和部門取得系統設定（需要登入）"
)
def get_setting_by_key(
    key: str,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """根據鍵名取得系統設定"""
    service = SystemSettingService(db)
    setting = service.get_by_key(key, department)

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"設定 '{key}' 在部門 '{department}' 不存在"
        )

    return SettingResponse.model_validate(setting)


@router.get(
    "/value/{key}",
    summary="取得設定值",
    description="取得設定值，支援 fallback 到 global 設定（需要登入）"
)
def get_setting_value(
    key: str,
    department: Optional[str] = None,
    default: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    取得設定值

    API CONTRACT: CRITICAL
    CONSUMERS: desktop_app/src/utils/backend_api_client.py
    SINCE: 1.0.0

    ============================================================
    警告：此端點被桌面應用直接依賴
    桌面應用打包為 .exe 後無法輕易更新
    任何破壞性變更都會導致已部署的桌面應用失效
    ============================================================

    禁止的變更：
    - 移除回應欄位（key, department, value）
    - 變更欄位類型
    - 變更 URL 路徑 /value/{key}

    允許的變更：
    - 新增可選回應欄位
    - 新增可選請求參數（需有預設值）

    詳見 docs/API_CONTRACT.md
    ============================================================

    優先順序：
    1. 指定部門的設定
    2. global 設定
    3. 預設值
    """
    service = SystemSettingService(db)
    value = service.get_value(key, department, default)

    # 回應格式為 CRITICAL CONTRACT，不可修改
    return {"key": key, "department": department, "value": value}


@router.post(
    "",
    response_model=SettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="建立設定",
    description="建立新的系統設定（僅管理員可操作）"
)
def create_setting(
    data: SettingCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """建立新的系統設定"""
    service = SystemSettingService(db)

    try:
        setting = service.create(
            key=data.key,
            value=data.value,
            department=data.department,
            description=data.description
        )
        return SettingResponse.model_validate(setting)

    except DuplicateSettingError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put(
    "/{setting_id}",
    response_model=SettingResponse,
    summary="更新設定",
    description="更新現有系統設定（僅管理員可操作）"
)
def update_setting(
    setting_id: int,
    data: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """更新系統設定"""
    service = SystemSettingService(db)

    try:
        setting = service.update(
            setting_id=setting_id,
            value=data.value,
            description=data.description
        )
        return SettingResponse.model_validate(setting)

    except SettingNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/upsert/{key}",
    response_model=SettingResponse,
    summary="更新或建立設定",
    description="若設定存在則更新，否則建立新設定（僅管理員可操作）"
)
def upsert_setting(
    key: str,
    data: SettingUpdate,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """更新或建立系統設定"""
    service = SystemSettingService(db)

    setting = service.upsert(
        key=key,
        value=data.value,
        department=department,
        description=data.description
    )
    return SettingResponse.model_validate(setting)


@router.delete(
    "/{setting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除設定",
    description="刪除系統設定（僅管理員可操作）"
)
def delete_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """刪除系統設定"""
    service = SystemSettingService(db)

    try:
        service.delete(setting_id)

    except SettingNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============================================================
# 批次操作
# ============================================================

@router.post(
    "/bulk",
    response_model=SettingListResponse,
    summary="批次更新設定",
    description="批次更新或建立多個系統設定（僅管理員可操作）"
)
def bulk_upsert_settings(
    data: BulkUpsertRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """批次更新或建立系統設定"""
    service = SystemSettingService(db)

    items = service.bulk_upsert([s.model_dump() for s in data.settings])

    return SettingListResponse(
        total=len(items),
        items=[SettingResponse.model_validate(item) for item in items]
    )


# ============================================================
# 部門配置
# ============================================================

@router.get(
    "/department/{department}/config",
    response_model=DepartmentConfigResponse,
    summary="取得部門完整配置",
    description="取得指定部門的所有設定（包含 global 設定，需要登入）"
)
def get_department_config(
    department: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得部門完整配置"""
    # 驗證部門名稱
    valid_departments = [DepartmentScope.DANHAI.value, DepartmentScope.ANKENG.value]
    if department not in valid_departments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的部門名稱，有效值為：{valid_departments}"
        )

    service = SystemSettingService(db)
    config = service.get_department_config(department)

    return DepartmentConfigResponse(
        department=department,
        settings=config
    )
