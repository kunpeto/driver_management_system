"""
考核標準 API
對應 tasks.md T175, T176, T177: 考核標準 CRUD、Excel 匯入、搜尋 API
對應 spec.md: User Story 9 - 考核系統
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..middleware.auth import get_current_user
from ..middleware.permission import require_admin
from ..services.assessment_standard_service import AssessmentStandardService

router = APIRouter(prefix="/api/assessment-standards", tags=["考核標準"])


# Pydantic Schemas
class AssessmentStandardBase(BaseModel):
    """考核標準基本欄位"""
    code: str = Field(..., max_length=10, description="考核代碼")
    category: str = Field(..., max_length=10, description="類別")
    name: str = Field(..., max_length=100, description="項目名稱")
    base_points: float = Field(..., description="基本分數")
    has_cumulative: bool = Field(True, description="是否適用累計加重")
    calculation_cycle: str = Field("yearly", description="計算週期")
    description: Optional[str] = Field(None, description="說明")
    is_active: bool = Field(True, description="是否啟用")


class AssessmentStandardCreate(AssessmentStandardBase):
    """建立考核標準請求"""
    pass


class AssessmentStandardUpdate(BaseModel):
    """更新考核標準請求"""
    code: Optional[str] = Field(None, max_length=10)
    category: Optional[str] = Field(None, max_length=10)
    name: Optional[str] = Field(None, max_length=100)
    base_points: Optional[float] = None
    has_cumulative: Optional[bool] = None
    calculation_cycle: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AssessmentStandardResponse(AssessmentStandardBase):
    """考核標準回應"""
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ImportResultResponse(BaseModel):
    """匯入結果回應"""
    created: int
    updated: int
    skipped: int
    errors: int


# API Endpoints
@router.get("", response_model=list[AssessmentStandardResponse])
async def list_standards(
    is_active: Optional[bool] = Query(True, description="是否僅查詢啟用的標準"),
    category: Optional[str] = Query(None, description="類別篩選"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    取得所有考核標準

    - **is_active**: 是否僅查詢啟用的標準（預設 True）
    - **category**: 類別篩選
    """
    service = AssessmentStandardService(db)
    standards = service.get_all(is_active=is_active, category=category)

    return [
        AssessmentStandardResponse(
            id=s.id,
            code=s.code,
            category=s.category,
            name=s.name,
            base_points=s.base_points,
            has_cumulative=s.has_cumulative,
            calculation_cycle=s.calculation_cycle,
            description=s.description,
            is_active=s.is_active,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat()
        )
        for s in standards
    ]


@router.get("/search", response_model=list[AssessmentStandardResponse])
async def search_standards(
    keyword: str = Query(..., min_length=1, description="搜尋關鍵字"),
    is_active: Optional[bool] = Query(True, description="是否僅查詢啟用的標準"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    搜尋考核標準

    搜尋範圍：代碼、名稱、說明
    """
    service = AssessmentStandardService(db)
    standards = service.search(keyword=keyword, is_active=is_active)

    return [
        AssessmentStandardResponse(
            id=s.id,
            code=s.code,
            category=s.category,
            name=s.name,
            base_points=s.base_points,
            has_cumulative=s.has_cumulative,
            calculation_cycle=s.calculation_cycle,
            description=s.description,
            is_active=s.is_active,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat()
        )
        for s in standards
    ]


@router.get("/categories")
async def get_by_categories(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    取得按類別分組的考核標準
    """
    service = AssessmentStandardService(db)
    categories = service.get_categories()

    return {
        category: [
            {
                "id": s.id,
                "code": s.code,
                "name": s.name,
                "base_points": s.base_points
            }
            for s in standards
        ]
        for category, standards in categories.items()
    }


@router.get("/r-type")
async def get_r_type_standards(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    取得 R02-R05 人為疏失項目（需責任判定）
    """
    service = AssessmentStandardService(db)
    standards = service.get_r_type_standards()

    return [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "base_points": s.base_points,
            "requires_responsibility_assessment": True
        }
        for s in standards
    ]


@router.get("/{standard_id}", response_model=AssessmentStandardResponse)
async def get_standard(
    standard_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    取得單一考核標準
    """
    service = AssessmentStandardService(db)
    standard = service.get_by_id(standard_id)

    if not standard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到考核標準 ID: {standard_id}"
        )

    return AssessmentStandardResponse(
        id=standard.id,
        code=standard.code,
        category=standard.category,
        name=standard.name,
        base_points=standard.base_points,
        has_cumulative=standard.has_cumulative,
        calculation_cycle=standard.calculation_cycle,
        description=standard.description,
        is_active=standard.is_active,
        created_at=standard.created_at.isoformat(),
        updated_at=standard.updated_at.isoformat()
    )


@router.post("", response_model=AssessmentStandardResponse, status_code=status.HTTP_201_CREATED)
async def create_standard(
    data: AssessmentStandardCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    建立考核標準

    **僅管理員可執行**
    """
    service = AssessmentStandardService(db)

    try:
        standard = service.create(
            code=data.code,
            category=data.category,
            name=data.name,
            base_points=data.base_points,
            has_cumulative=data.has_cumulative,
            calculation_cycle=data.calculation_cycle,
            description=data.description,
            is_active=data.is_active
        )
        db.commit()
        db.refresh(standard)

        return AssessmentStandardResponse(
            id=standard.id,
            code=standard.code,
            category=standard.category,
            name=standard.name,
            base_points=standard.base_points,
            has_cumulative=standard.has_cumulative,
            calculation_cycle=standard.calculation_cycle,
            description=standard.description,
            is_active=standard.is_active,
            created_at=standard.created_at.isoformat(),
            updated_at=standard.updated_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{standard_id}", response_model=AssessmentStandardResponse)
async def update_standard(
    standard_id: int,
    data: AssessmentStandardUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    更新考核標準

    **僅管理員可執行**
    """
    service = AssessmentStandardService(db)

    try:
        # 只傳遞有值的欄位
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        standard = service.update(standard_id, **update_data)
        db.commit()
        db.refresh(standard)

        return AssessmentStandardResponse(
            id=standard.id,
            code=standard.code,
            category=standard.category,
            name=standard.name,
            base_points=standard.base_points,
            has_cumulative=standard.has_cumulative,
            calculation_cycle=standard.calculation_cycle,
            description=standard.description,
            is_active=standard.is_active,
            created_at=standard.created_at.isoformat(),
            updated_at=standard.updated_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{standard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_standard(
    standard_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    刪除考核標準

    **僅管理員可執行**

    注意：若該標準已有考核記錄，則無法刪除
    """
    service = AssessmentStandardService(db)

    try:
        service.delete(standard_id)
        db.commit()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{standard_id}/toggle-active", response_model=AssessmentStandardResponse)
async def toggle_standard_active(
    standard_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    切換考核標準的啟用狀態

    **僅管理員可執行**
    """
    service = AssessmentStandardService(db)

    try:
        standard = service.toggle_active(standard_id)
        db.commit()
        db.refresh(standard)

        return AssessmentStandardResponse(
            id=standard.id,
            code=standard.code,
            category=standard.category,
            name=standard.name,
            base_points=standard.base_points,
            has_cumulative=standard.has_cumulative,
            calculation_cycle=standard.calculation_cycle,
            description=standard.description,
            is_active=standard.is_active,
            created_at=standard.created_at.isoformat(),
            updated_at=standard.updated_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/import-excel", response_model=ImportResultResponse)
async def import_from_excel(
    file: UploadFile = File(..., description="Excel 檔案"),
    update_existing: bool = Query(False, description="是否更新已存在的標準"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    從 Excel 匯入考核標準

    **僅管理員可執行**

    Excel 檔案格式：
    - 必要欄位：code, category, name, base_points
    - 選填欄位：has_cumulative, calculation_cycle, description, is_active
    """
    import io

    import openpyxl

    # 驗證檔案類型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="僅支援 .xlsx 或 .xls 格式的 Excel 檔案"
        )

    try:
        # 讀取 Excel
        contents = await file.read()
        workbook = openpyxl.load_workbook(io.BytesIO(contents))
        sheet = workbook.active

        # 取得標題行
        headers = [cell.value for cell in sheet[1]]

        # 驗證必要欄位
        required_fields = {'code', 'category', 'name', 'base_points'}
        if not required_fields.issubset(set(headers)):
            missing = required_fields - set(headers)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Excel 缺少必要欄位：{missing}"
            )

        # 解析資料
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = {headers[i]: row[i] for i in range(len(headers)) if headers[i]}
            if row_dict.get('code'):  # 跳過空行
                data.append(row_dict)

        # 匯入
        service = AssessmentStandardService(db)
        result = service.import_from_excel_data(data, update_existing=update_existing)
        db.commit()

        return ImportResultResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excel 處理失敗：{str(e)}"
        )


@router.post("/initialize-defaults", response_model=dict)
async def initialize_default_standards(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    初始化預設的 61 項考核標準

    **僅管理員可執行**

    注意：若已有資料則不會重複初始化
    """
    service = AssessmentStandardService(db)
    count = service.initialize_default_standards()
    db.commit()

    return {
        "message": f"已初始化 {count} 項考核標準" if count > 0 else "考核標準已存在，無需初始化",
        "created_count": count
    }
