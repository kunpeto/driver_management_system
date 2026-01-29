"""
勤務標準時間 API 端點
對應 tasks.md T110: 實作勤務標準時間 CRUD API
對應 tasks.md T111: 實作勤務標準時間 Excel 匯入 API

提供勤務標準時間的 CRUD 操作與 Excel 匯入功能。
"""

from typing import Optional, List
import io

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import require_admin
from src.services.route_standard_time_service import (
    DuplicateRouteError,
    RouteNotFoundError,
    RouteStandardTimeService,
    RouteStandardTimeServiceError,
)

router = APIRouter()


# ============================================================
# Pydantic 模型
# ============================================================

class RouteStandardTimeCreate(BaseModel):
    """建立勤務標準時間請求"""
    department: str = Field(..., description="部門（淡海 或 安坑）")
    route_code: str = Field(..., min_length=1, max_length=50, description="勤務代碼")
    route_name: str = Field(..., min_length=1, max_length=100, description="勤務名稱")
    standard_minutes: int = Field(..., ge=0, description="標準分鐘數")
    description: Optional[str] = Field(None, max_length=500, description="說明備註")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "department": "淡海",
                    "route_code": "0905G",
                    "route_name": "早班 09:05 出發",
                    "standard_minutes": 480,
                    "description": "全程駕駛"
                }
            ]
        }
    }


class RouteStandardTimeUpdate(BaseModel):
    """更新勤務標準時間請求"""
    route_name: Optional[str] = Field(None, min_length=1, max_length=100, description="勤務名稱")
    standard_minutes: Optional[int] = Field(None, ge=0, description="標準分鐘數")
    description: Optional[str] = Field(None, max_length=500, description="說明備註")


class RouteStandardTimeResponse(BaseModel):
    """勤務標準時間回應"""
    id: int
    department: str
    route_code: str
    route_name: str
    standard_minutes: int
    standard_hours: float
    description: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class RouteStandardTimeListResponse(BaseModel):
    """勤務標準時間列表回應"""
    items: List[RouteStandardTimeResponse]
    total: int
    skip: int
    limit: int


class ImportResult(BaseModel):
    """匯入結果"""
    created: int
    updated: int
    skipped: int
    errors: List[str]
    total: int


# ============================================================
# API 端點
# ============================================================

@router.get("/routes", response_model=RouteStandardTimeListResponse)
async def list_routes(
    department: Optional[str] = Query(None, description="篩選部門"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    include_inactive: bool = Query(False, description="是否包含已刪除的"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="限制筆數"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    列出勤務標準時間

    - 支援部門篩選
    - 支援關鍵字搜尋
    - 支援分頁
    """
    service = RouteStandardTimeService(db)

    items = service.list_all(
        department=department,
        include_inactive=include_inactive,
        search=search,
        skip=skip,
        limit=limit
    )

    total = service.count(department=department, include_inactive=include_inactive)

    return RouteStandardTimeListResponse(
        items=[
            RouteStandardTimeResponse(
                id=item.id,
                department=item.department,
                route_code=item.route_code,
                route_name=item.route_name,
                standard_minutes=item.standard_minutes,
                standard_hours=item.hours,
                description=item.description,
                is_active=item.is_active
            )
            for item in items
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/routes/{route_id}", response_model=RouteStandardTimeResponse)
async def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """取得單筆勤務標準時間"""
    service = RouteStandardTimeService(db)
    route = service.get_by_id(route_id)

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"勤務標準時間 ID {route_id} 不存在"
        )

    return RouteStandardTimeResponse(
        id=route.id,
        department=route.department,
        route_code=route.route_code,
        route_name=route.route_name,
        standard_minutes=route.standard_minutes,
        standard_hours=route.hours,
        description=route.description,
        is_active=route.is_active
    )


@router.post("/routes", response_model=RouteStandardTimeResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    data: RouteStandardTimeCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    """
    建立勤務標準時間

    僅管理員可執行
    """
    service = RouteStandardTimeService(db)

    try:
        route = service.create(
            department=data.department,
            route_code=data.route_code,
            route_name=data.route_name,
            standard_minutes=data.standard_minutes,
            description=data.description
        )

        return RouteStandardTimeResponse(
            id=route.id,
            department=route.department,
            route_code=route.route_code,
            route_name=route.route_name,
            standard_minutes=route.standard_minutes,
            standard_hours=route.hours,
            description=route.description,
            is_active=route.is_active
        )

    except DuplicateRouteError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except RouteStandardTimeServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/routes/{route_id}", response_model=RouteStandardTimeResponse)
async def update_route(
    route_id: int,
    data: RouteStandardTimeUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    """
    更新勤務標準時間

    僅管理員可執行
    """
    service = RouteStandardTimeService(db)

    try:
        route = service.update(
            id=route_id,
            route_name=data.route_name,
            standard_minutes=data.standard_minutes,
            description=data.description
        )

        return RouteStandardTimeResponse(
            id=route.id,
            department=route.department,
            route_code=route.route_code,
            route_name=route.route_name,
            standard_minutes=route.standard_minutes,
            standard_hours=route.hours,
            description=route.description,
            is_active=route.is_active
        )

    except RouteNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RouteStandardTimeServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    """
    刪除勤務標準時間（軟刪除）

    僅管理員可執行
    """
    service = RouteStandardTimeService(db)

    try:
        service.soft_delete(route_id)
    except RouteNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/routes/{route_id}/restore", response_model=RouteStandardTimeResponse)
async def restore_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    """
    恢復已刪除的勤務標準時間

    僅管理員可執行
    """
    service = RouteStandardTimeService(db)

    try:
        route = service.restore(route_id)

        return RouteStandardTimeResponse(
            id=route.id,
            department=route.department,
            route_code=route.route_code,
            route_name=route.route_name,
            standard_minutes=route.standard_minutes,
            standard_hours=route.hours,
            description=route.description,
            is_active=route.is_active
        )

    except RouteNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/routes/import-excel", response_model=ImportResult)
async def import_routes_from_excel(
    department: str = Query(..., description="目標部門"),
    update_existing: bool = Query(True, description="是否更新已存在的資料"),
    file: UploadFile = File(..., description="Excel 檔案"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    """
    從 Excel 匯入勤務標準時間

    僅管理員可執行

    Excel 格式要求：
    - 第一行為標題（route_code, route_name, standard_minutes, description）
    - route_code: 勤務代碼（必填）
    - route_name: 勤務名稱（必填）
    - standard_minutes: 標準分鐘數（必填，整數）
    - description: 說明備註（選填）
    """
    # 檢查檔案類型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="僅支援 Excel 檔案格式（.xlsx, .xls）"
        )

    try:
        import openpyxl

        # 讀取 Excel
        content = await file.read()
        workbook = openpyxl.load_workbook(io.BytesIO(content))
        sheet = workbook.active

        # 解析資料
        rows = []
        headers = [cell.value for cell in sheet[1]]

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if all(cell is None for cell in row):
                continue
            row_dict = dict(zip(headers, row))
            rows.append(row_dict)

        service = RouteStandardTimeService(db)

        # 驗證資料
        valid_rows, errors = service.validate_import_data(rows, department)

        if errors:
            return ImportResult(
                created=0,
                updated=0,
                skipped=0,
                errors=errors,
                total=len(rows)
            )

        # 批次匯入
        result = service.bulk_import(valid_rows, department, update_existing)

        return ImportResult(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excel 解析錯誤: {str(e)}"
        )
