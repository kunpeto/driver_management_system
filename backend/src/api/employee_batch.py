"""
員工批次匯入/匯出 API 端點
對應 tasks.md T052: 實作批次匯入/匯出 API

提供 Excel 批次匯入員工資料、匯出員工資料、下載匯入範本功能。
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import (
    PermissionChecker,
    require_admin,
    require_role,
    Role,
)
from src.services.employee_import_service import EmployeeImportService
from src.services.employee_export_service import EmployeeExportService

router = APIRouter()


# ============================================================
# Pydantic 模型
# ============================================================

class ImportErrorDetail(BaseModel):
    """匯入錯誤詳情"""
    row: int
    error: str


class ImportResponse(BaseModel):
    """匯入結果回應"""
    success: bool
    total_rows: int
    imported_count: int
    skipped_count: int
    error_count: int
    errors: list[ImportErrorDetail]
    imported_ids: list[str]


class ValidateResponse(BaseModel):
    """驗證結果回應"""
    success: bool
    total_rows: int
    error_count: int
    errors: list[ImportErrorDetail]


class ExportCountResponse(BaseModel):
    """匯出筆數回應"""
    count: int


class TemplateColumnInfo(BaseModel):
    """範本欄位資訊"""
    name: str
    key: str
    required: bool
    description: str


class TemplateColumnsResponse(BaseModel):
    """範本欄位列表回應"""
    columns: list[TemplateColumnInfo]


# ============================================================
# API 端點
# ============================================================

@router.post(
    "/import",
    response_model=ImportResponse,
    summary="批次匯入員工",
    description="從 Excel 檔案批次匯入員工資料（需要管理員或主管權限）"
)
async def import_employees(
    file: UploadFile = File(..., description="Excel 檔案（.xlsx）"),
    skip_duplicates: bool = Query(True, description="是否跳過重複的員工編號"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role(Role.ADMIN, Role.MANAGER))
):
    """
    批次匯入員工

    - 支援 .xlsx 格式
    - 第一行為標題行
    - 必要欄位：員工編號、姓名、部門
    - 選填欄位：電話、電子郵件、緊急聯絡人、緊急聯絡電話

    若 skip_duplicates=True，重複的員工編號會被跳過而不報錯。
    """
    # 驗證檔案類型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="僅支援 Excel 檔案格式（.xlsx, .xls）"
        )

    # 讀取檔案內容
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"讀取檔案失敗：{str(e)}"
        )

    # 建立 BytesIO 物件
    import io
    file_stream = io.BytesIO(contents)

    # 執行匯入
    service = EmployeeImportService(db)
    result = service.import_from_excel(
        file=file_stream,
        skip_duplicates=skip_duplicates,
        created_by=current_user.username
    )

    return ImportResponse(
        success=result.success,
        total_rows=result.total_rows,
        imported_count=result.imported_count,
        skipped_count=result.skipped_count,
        error_count=result.error_count,
        errors=[ImportErrorDetail(**e) for e in result.errors],
        imported_ids=result.imported_ids
    )


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="驗證匯入檔案",
    description="驗證 Excel 檔案格式（不實際匯入）"
)
async def validate_import_file(
    file: UploadFile = File(..., description="Excel 檔案（.xlsx）"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    驗證匯入檔案

    檢查 Excel 檔案格式是否正確，回報格式錯誤但不實際匯入資料。
    """
    # 驗證檔案類型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="僅支援 Excel 檔案格式（.xlsx, .xls）"
        )

    # 讀取檔案內容
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"讀取檔案失敗：{str(e)}"
        )

    # 建立 BytesIO 物件
    import io
    file_stream = io.BytesIO(contents)

    # 執行驗證
    service = EmployeeImportService(db)
    result = service.validate_excel(file_stream)

    return ValidateResponse(
        success=result.success,
        total_rows=result.total_rows,
        error_count=result.error_count,
        errors=[ImportErrorDetail(**e) for e in result.errors]
    )


@router.get(
    "/export",
    summary="匯出員工資料",
    description="匯出員工資料為 Excel 檔案"
)
def export_employees(
    department: Optional[str] = Query(None, description="篩選部門"),
    include_resigned: bool = Query(False, description="是否包含離職員工"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    format: str = Query("xlsx", description="匯出格式（xlsx 或 csv）"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    匯出員工資料

    支援 Excel (.xlsx) 和 CSV 格式。
    """
    service = EmployeeExportService(db)

    if format.lower() == "csv":
        # 匯出 CSV
        csv_content = service.export_to_csv(
            department=department,
            include_resigned=include_resigned,
            search=search
        )

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=employees.csv"
            }
        )
    else:
        # 匯出 Excel
        excel_stream = service.export_to_excel(
            department=department,
            include_resigned=include_resigned,
            search=search
        )

        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=employees.xlsx"
            }
        )


@router.get(
    "/export/count",
    response_model=ExportCountResponse,
    summary="取得匯出筆數",
    description="取得符合篩選條件的員工筆數"
)
def get_export_count(
    department: Optional[str] = Query(None, description="篩選部門"),
    include_resigned: bool = Query(False, description="是否包含離職員工"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得匯出筆數"""
    service = EmployeeExportService(db)
    count = service.get_export_count(
        department=department,
        include_resigned=include_resigned,
        search=search
    )

    return ExportCountResponse(count=count)


@router.get(
    "/template",
    summary="下載匯入範本",
    description="下載員工匯入的 Excel 範本"
)
def download_template(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    下載匯入範本

    範本包含：
    - 標題行（必填欄位以黃色標示）
    - 範例資料
    - 部門下拉選單
    - 說明工作表
    """
    service = EmployeeExportService(db)
    template_stream = service.export_template()

    return StreamingResponse(
        template_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=employee_import_template.xlsx"
        }
    )


@router.get(
    "/template/columns",
    response_model=TemplateColumnsResponse,
    summary="取得範本欄位資訊",
    description="取得匯入範本的欄位定義資訊"
)
def get_template_columns(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得範本欄位資訊"""
    service = EmployeeImportService(db)
    columns = service.get_template_columns()

    return TemplateColumnsResponse(
        columns=[TemplateColumnInfo(**col) for col in columns]
    )
