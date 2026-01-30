"""
差勤加分 API
對應 tasks.md T201-T202: 實作差勤加分處理 API 與結果查詢 API
對應 spec.md: User Story 10 - 差勤加分自動處理
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, extract, func, select
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..middleware.permission import require_admin, require_auth
from ..models.assessment_record import AssessmentRecord
from ..models.employee import Employee
from ..services.attendance_bonus_processor import (
    AttendanceBonusProcessor,
    AttendanceBonusResult,
)
from ..services.schedule_sync_service import ScheduleSyncService, get_schedule_sync_service

router = APIRouter(prefix="/api/attendance-bonus", tags=["差勤加分"])


# Pydantic Schemas
class AttendanceBonusProcessRequest(BaseModel):
    """差勤加分處理請求"""
    year: int = Field(..., ge=2020, le=2100, description="年度")
    month: int = Field(..., ge=1, le=12, description="月份")
    department: str = Field(..., description="部門（淡海/安坑）")


class AttendanceBonusPreviewRequest(BaseModel):
    """差勤加分預覽請求"""
    year: int = Field(..., ge=2020, le=2100, description="年度")
    month: int = Field(..., ge=1, le=12, description="月份")
    department: str = Field(..., description="部門（淡海/安坑）")


class BonusRecordItem(BaseModel):
    """加分記錄項目"""
    standard_code: str
    employee_id: int
    employee_code: str
    employee_name: str
    record_date: str
    points: float
    description: str
    created: bool
    skipped_reason: Optional[str] = None


class AttendanceBonusResultResponse(BaseModel):
    """差勤加分處理結果回應"""
    success: bool
    year: int
    month: int
    department: str
    total_employees: int

    # +M 系列統計
    m01_count: int  # 全勤
    m02_count: int  # 行車零違規
    m03_count: int  # 全項目零違規

    # +A 系列統計
    a01_count: int  # R班出勤
    a02_count: int  # 國定假日出勤
    a03_count: int  # 延長工時 1 小時
    a04_count: int  # 延長工時 2 小時
    a05_count: int  # 延長工時 3 小時
    a06_count: int  # 延長工時 4 小時

    skipped_count: int  # 跳過（已存在）

    records: List[BonusRecordItem] = []
    errors: List[str] = []
    warnings: List[str] = []


class MonthlyBonusStats(BaseModel):
    """月度加分統計"""
    year: int
    month: int
    department: str
    m01_count: int = 0
    m02_count: int = 0
    m03_count: int = 0
    a01_count: int = 0
    a02_count: int = 0
    a03_count: int = 0
    a04_count: int = 0
    a05_count: int = 0
    a06_count: int = 0
    total_bonus_records: int = 0
    total_bonus_points: float = 0.0


class ProcessHistoryItem(BaseModel):
    """處理歷史項目"""
    year: int
    month: int
    department: str
    processed_at: str
    total_records: int


def _convert_result_to_response(
    result: AttendanceBonusResult
) -> AttendanceBonusResultResponse:
    """
    將處理結果轉換為 API 回應

    Args:
        result: 差勤加分處理結果

    Returns:
        API 回應物件
    """
    records = []
    for r in result.records:
        records.append(BonusRecordItem(
            standard_code=r.standard_code,
            employee_id=r.employee_id,
            employee_code=r.employee_code,
            employee_name=r.employee_name,
            record_date=r.record_date.isoformat(),
            points=r.points,
            description=r.description,
            created=r.created,
            skipped_reason=r.skipped_reason
        ))

    return AttendanceBonusResultResponse(
        success=result.success,
        year=result.year,
        month=result.month,
        department=result.department,
        total_employees=result.total_employees,
        m01_count=result.m01_count,
        m02_count=result.m02_count,
        m03_count=result.m03_count,
        a01_count=result.a01_count,
        a02_count=result.a02_count,
        a03_count=result.a03_count,
        a04_count=result.a04_count,
        a05_count=result.a05_count,
        a06_count=result.a06_count,
        skipped_count=result.skipped_count,
        records=records,
        errors=result.errors,
        warnings=result.warnings
    )


@router.post(
    "/process",
    response_model=AttendanceBonusResultResponse,
    summary="執行差勤加分處理",
    description="從 Google Sheets 班表讀取資料，自動建立差勤加分記錄"
)
async def process_attendance_bonus(
    request: AttendanceBonusProcessRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    執行差勤加分處理

    - 讀取指定月份的 Google Sheets 班表
    - 判定全勤、R班出勤、國定假日出勤、延長工時
    - 批次建立 AssessmentRecord
    - 觸發月度獎勵計算（+M01/+M02/+M03）
    """
    try:
        # 取得班表資料
        sync_service = get_schedule_sync_service()
        sheet_data = sync_service.fetch_schedule_data(
            department=request.department,
            year=request.year,
            month=request.month
        )

        if not sheet_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無法取得 {request.department} {request.year}年{request.month}月 班表資料"
            )

        # 執行處理
        processor = AttendanceBonusProcessor(db)
        result = processor.process(
            sheet_data=sheet_data,
            department=request.department,
            year=request.year,
            month=request.month,
            dry_run=False
        )

        return _convert_result_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"差勤加分處理失敗：{str(e)}"
        )


@router.post(
    "/preview",
    response_model=AttendanceBonusResultResponse,
    summary="預覽差勤加分處理",
    description="預覽將建立的記錄但不實際寫入"
)
async def preview_attendance_bonus(
    request: AttendanceBonusPreviewRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_auth)
):
    """
    預覽差勤加分處理

    - 讀取班表並分析
    - 返回將建立的記錄
    - 不實際寫入資料庫
    """
    try:
        # 取得班表資料
        sync_service = get_schedule_sync_service()
        sheet_data = sync_service.fetch_schedule_data(
            department=request.department,
            year=request.year,
            month=request.month
        )

        if not sheet_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無法取得 {request.department} {request.year}年{request.month}月 班表資料"
            )

        # 執行預覽
        processor = AttendanceBonusProcessor(db)
        result = processor.preview(
            sheet_data=sheet_data,
            department=request.department,
            year=request.year,
            month=request.month
        )

        return _convert_result_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"差勤加分預覽失敗：{str(e)}"
        )


@router.get(
    "/results/{year}/{month}",
    response_model=MonthlyBonusStats,
    summary="查詢月度加分統計",
    description="查詢指定月份的加分記錄統計"
)
async def get_monthly_bonus_stats(
    year: int,
    month: int,
    department: Optional[str] = Query(None, description="部門篩選"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_auth)
):
    """
    查詢月度加分統計

    - 統計 +M01/+M02/+M03 數量
    - 統計 +A01~+A06 數量
    - 計算總加分分數
    """
    try:
        # 查詢 +M 和 +A 系列記錄
        stmt = (
            select(
                AssessmentRecord.standard_code,
                func.count(AssessmentRecord.id).label("count"),
                func.sum(AssessmentRecord.final_points).label("total_points")
            )
            .where(
                and_(
                    extract('year', AssessmentRecord.record_date) == year,
                    extract('month', AssessmentRecord.record_date) == month,
                    AssessmentRecord.is_deleted == False,
                    AssessmentRecord.standard_code.like('+%')
                )
            )
            .group_by(AssessmentRecord.standard_code)
        )

        # 如果指定部門，加入員工篩選
        if department:
            stmt = stmt.join(
                Employee,
                AssessmentRecord.employee_id == Employee.id
            ).where(Employee.current_department == department)

        results = db.execute(stmt).all()

        # 轉換為統計物件
        stats = MonthlyBonusStats(
            year=year,
            month=month,
            department=department or "全部"
        )

        total_records = 0
        total_points = 0.0

        for code, count, points in results:
            total_records += count
            total_points += points or 0

            if code == "+M01":
                stats.m01_count = count
            elif code == "+M02":
                stats.m02_count = count
            elif code == "+M03":
                stats.m03_count = count
            elif code == "+A01":
                stats.a01_count = count
            elif code == "+A02":
                stats.a02_count = count
            elif code == "+A03":
                stats.a03_count = count
            elif code == "+A04":
                stats.a04_count = count
            elif code == "+A05":
                stats.a05_count = count
            elif code == "+A06":
                stats.a06_count = count

        stats.total_bonus_records = total_records
        stats.total_bonus_points = total_points

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢月度加分統計失敗：{str(e)}"
        )


@router.get(
    "/history",
    response_model=List[ProcessHistoryItem],
    summary="查詢處理歷史",
    description="查詢差勤加分處理歷史記錄"
)
async def get_process_history(
    year: Optional[int] = Query(None, description="年度篩選"),
    department: Optional[str] = Query(None, description="部門篩選"),
    limit: int = Query(12, ge=1, le=100, description="回傳筆數上限"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_auth)
):
    """
    查詢處理歷史

    - 查詢過去已處理的月份
    - 顯示每月的記錄數量
    """
    try:
        # 查詢有加分記錄的月份
        stmt = (
            select(
                extract('year', AssessmentRecord.record_date).label("year"),
                extract('month', AssessmentRecord.record_date).label("month"),
                func.count(AssessmentRecord.id).label("total_records"),
                func.max(AssessmentRecord.created_at).label("processed_at")
            )
            .where(
                and_(
                    AssessmentRecord.is_deleted == False,
                    AssessmentRecord.standard_code.like('+%')
                )
            )
            .group_by(
                extract('year', AssessmentRecord.record_date),
                extract('month', AssessmentRecord.record_date)
            )
            .order_by(
                extract('year', AssessmentRecord.record_date).desc(),
                extract('month', AssessmentRecord.record_date).desc()
            )
            .limit(limit)
        )

        if year:
            stmt = stmt.where(
                extract('year', AssessmentRecord.record_date) == year
            )

        results = db.execute(stmt).all()

        history = []
        for row in results:
            history.append(ProcessHistoryItem(
                year=int(row.year),
                month=int(row.month),
                department=department or "全部",
                processed_at=row.processed_at.isoformat() if row.processed_at else "",
                total_records=row.total_records
            ))

        return history

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢處理歷史失敗：{str(e)}"
        )
