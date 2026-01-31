"""
考核記錄 API
對應 tasks.md T178-T182: 考核記錄 CRUD、責任判定、年度摘要、月度獎勵、年度重置 API
對應 spec.md: User Story 9 - 考核系統
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..middleware.auth import get_current_user
from ..middleware.permission import require_admin
from ..models.fault_responsibility import CHECKLIST_KEYS, CHECKLIST_LABELS
from ..services.assessment_record_service import AssessmentRecordService
from ..services.annual_reset_service import AnnualResetService
from ..services.fault_responsibility_service import FaultResponsibilityService
from ..services.monthly_reward_calculator import MonthlyRewardCalculatorService

router = APIRouter(prefix="/api/assessment-records", tags=["考核記錄"])


# Pydantic Schemas
class ChecklistResults(BaseModel):
    """9 項疏失查核結果"""
    awareness_delay: bool = Field(False, description="1. 察覺過晚或誤判")
    report_delay: bool = Field(False, description="2. 通報延遲或不完整")
    unfamiliar_procedure: bool = Field(False, description="3. 不熟悉故障排除程序")
    wrong_operation: bool = Field(False, description="4. 故障排除決策/操作錯誤")
    slow_action: bool = Field(False, description="5. 動作遲緩")
    unconfirmed_result: bool = Field(False, description="6. 未確認結果或誤認完成")
    no_progress_report: bool = Field(False, description="7. 未主動回報處理進度")
    repeated_error: bool = Field(False, description="8. 重複性錯誤")
    mental_state_issue: bool = Field(False, description="9. 心理狀態影響表現")


class FaultResponsibilityData(BaseModel):
    """R02-R05 責任判定資料"""
    delay_seconds: int = Field(..., ge=0, description="延誤時間（秒）")
    checklist_results: ChecklistResults = Field(..., description="9 項疏失查核結果")
    time_t0: Optional[datetime] = Field(None, description="T0: 事件/故障發生時間")
    time_t1: Optional[datetime] = Field(None, description="T1: 司機員察覺異常時間")
    time_t2: Optional[datetime] = Field(None, description="T2: 開始通報/處理時間")
    time_t3: Optional[datetime] = Field(None, description="T3: 故障排除完成時間")
    time_t4: Optional[datetime] = Field(None, description="T4: 恢復正常運轉時間")
    notes: Optional[str] = Field(None, description="備註")


class AssessmentRecordCreate(BaseModel):
    """建立考核記錄請求"""
    employee_id: int = Field(..., description="員工 ID")
    standard_code: str = Field(..., max_length=10, description="考核標準代碼")
    record_date: date = Field(..., description="事件日期")
    description: Optional[str] = Field(None, description="事件描述")
    profile_id: Optional[int] = Field(None, description="關聯履歷 ID")
    fault_responsibility_data: Optional[FaultResponsibilityData] = Field(
        None, description="R02-R05 責任判定資料"
    )


class AssessmentRecordUpdate(BaseModel):
    """更新考核記錄請求"""
    description: Optional[str] = Field(None, description="事件描述")
    fault_responsibility_data: Optional[FaultResponsibilityData] = Field(
        None, description="R02-R05 責任判定資料"
    )


class AssessmentRecordResponse(BaseModel):
    """考核記錄回應"""
    id: int
    employee_id: int
    standard_code: str
    standard_name: str
    profile_id: Optional[int]
    record_date: str
    description: Optional[str]
    base_points: float
    responsibility_coefficient: Optional[float]
    actual_points: float
    cumulative_count: Optional[int]
    cumulative_multiplier: float
    final_points: float
    is_deleted: bool
    fault_responsibility: Optional[dict] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MonthlyRewardCalculateRequest(BaseModel):
    """月度獎勵計算請求"""
    year: int = Field(..., ge=2020, le=2100, description="年度")
    month: int = Field(..., ge=1, le=12, description="月份")


class AnnualResetRequest(BaseModel):
    """年度重置請求"""
    year: Optional[int] = Field(None, description="年度（預設為當前年度）")
    confirm: bool = Field(False, description="確認執行")


# API Endpoints
@router.get("", response_model=list[AssessmentRecordResponse])
async def list_records(
    employee_id: Optional[int] = Query(None, description="員工 ID"),
    year: Optional[int] = Query(None, description="年度"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月份"),
    category: Optional[str] = Query(None, description="類別"),
    include_deleted: bool = Query(False, description="是否包含已刪除記錄"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    取得考核記錄列表
    """
    if not employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請提供 employee_id 參數"
        )

    service = AssessmentRecordService(db)
    records = service.get_by_employee(
        employee_id=employee_id,
        year=year,
        month=month,
        category=category,
        include_deleted=include_deleted
    )

    return [_to_response(r) for r in records]


@router.get("/summary")
async def get_employee_summary(
    employee_id: int = Query(..., description="員工 ID"),
    year: int = Query(..., description="年度"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    取得員工年度考核摘要
    """
    service = AssessmentRecordService(db)

    try:
        summary = service.get_employee_year_summary(employee_id, year)
        return summary

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/checklist-template")
async def get_checklist_template(
    _: dict = Depends(get_current_user)
):
    """
    取得責任判定查核表模板
    """
    return {
        "keys": CHECKLIST_KEYS,
        "labels": CHECKLIST_LABELS,
        "template": {key: False for key in CHECKLIST_KEYS},
        "responsibility_rules": {
            "完全責任": {"min_faults": 7, "max_faults": 9, "coefficient": 1.0},
            "主要責任": {"min_faults": 4, "max_faults": 6, "coefficient": 0.7},
            "次要責任": {"min_faults": 1, "max_faults": 3, "coefficient": 0.3},
        }
    }


@router.get("/{record_id}", response_model=AssessmentRecordResponse)
async def get_record(
    record_id: int,
    include_deleted: bool = Query(False, description="是否包含已刪除記錄"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    取得單一考核記錄
    """
    service = AssessmentRecordService(db)
    record = service.get_by_id(record_id, include_deleted=include_deleted)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"找不到考核記錄 ID: {record_id}"
        )

    return _to_response(record)


@router.post("", response_model=AssessmentRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    data: AssessmentRecordCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    建立考核記錄
    """
    service = AssessmentRecordService(db)

    try:
        fault_data = None
        if data.fault_responsibility_data:
            fault_data = {
                "delay_seconds": data.fault_responsibility_data.delay_seconds,
                "checklist_results": data.fault_responsibility_data.checklist_results.model_dump(),
                "time_t0": data.fault_responsibility_data.time_t0,
                "time_t1": data.fault_responsibility_data.time_t1,
                "time_t2": data.fault_responsibility_data.time_t2,
                "time_t3": data.fault_responsibility_data.time_t3,
                "time_t4": data.fault_responsibility_data.time_t4,
                "notes": data.fault_responsibility_data.notes
            }

        record = service.create(
            employee_id=data.employee_id,
            standard_code=data.standard_code,
            record_date=data.record_date,
            description=data.description,
            profile_id=data.profile_id,
            fault_responsibility_data=fault_data
        )
        db.commit()
        db.refresh(record)

        return _to_response(record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{record_id}", response_model=AssessmentRecordResponse)
async def update_record(
    record_id: int,
    data: AssessmentRecordUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    更新考核記錄
    """
    service = AssessmentRecordService(db)

    try:
        fault_data = None
        if data.fault_responsibility_data:
            fault_data = {
                "delay_seconds": data.fault_responsibility_data.delay_seconds,
                "checklist_results": data.fault_responsibility_data.checklist_results.model_dump(),
                "time_t0": data.fault_responsibility_data.time_t0,
                "time_t1": data.fault_responsibility_data.time_t1,
                "time_t2": data.fault_responsibility_data.time_t2,
                "time_t3": data.fault_responsibility_data.time_t3,
                "time_t4": data.fault_responsibility_data.time_t4,
                "notes": data.fault_responsibility_data.notes
            }

        record = service.update(
            record_id=record_id,
            description=data.description,
            fault_responsibility_data=fault_data
        )
        db.commit()
        db.refresh(record)

        return _to_response(record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{record_id}", response_model=AssessmentRecordResponse)
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    軟刪除考核記錄

    刪除後會觸發重算該年度該類別的累計次數
    """
    service = AssessmentRecordService(db)

    try:
        record = service.soft_delete(record_id)
        db.commit()

        return _to_response(record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{record_id}/restore", response_model=AssessmentRecordResponse)
async def restore_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    還原軟刪除的考核記錄
    """
    service = AssessmentRecordService(db)

    try:
        record = service.restore(record_id)
        db.commit()

        return _to_response(record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{record_id}/fault-responsibility", response_model=AssessmentRecordResponse)
async def update_fault_responsibility(
    record_id: int,
    data: FaultResponsibilityData,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    更新 R02-R05 責任判定

    此 API 會：
    1. 更新/建立責任判定記錄
    2. 重新計算責任係數
    3. 重新計算考核記錄的分數
    4. 更新員工總分
    """
    service = AssessmentRecordService(db)

    try:
        fault_data = {
            "delay_seconds": data.delay_seconds,
            "checklist_results": data.checklist_results.model_dump(),
            "time_t0": data.time_t0,
            "time_t1": data.time_t1,
            "time_t2": data.time_t2,
            "time_t3": data.time_t3,
            "time_t4": data.time_t4,
            "notes": data.notes
        }

        record = service.update(
            record_id=record_id,
            fault_responsibility_data=fault_data
        )
        db.commit()
        db.refresh(record)

        return _to_response(record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/preview-calculation")
async def preview_calculation(
    base_points: float = Query(..., description="基本分數"),
    cumulative_count: int = Query(1, ge=1, description="累計次數"),
    checklist_results: Optional[str] = Query(None, description="查核結果 JSON"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    預覽考核分數計算結果
    """
    import json

    fault_service = FaultResponsibilityService(db)

    checklist = {key: False for key in CHECKLIST_KEYS}
    if checklist_results:
        try:
            checklist = json.loads(checklist_results)
        except json.JSONDecodeError:
            pass

    cumulative_multiplier = 1.0 + 0.5 * (cumulative_count - 1)

    return fault_service.calculate_assessment_preview(
        base_points=base_points,
        checklist_results=checklist,
        cumulative_multiplier=cumulative_multiplier
    )


@router.post("/monthly-rewards/calculate")
async def calculate_monthly_rewards(
    data: MonthlyRewardCalculateRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    計算月度獎勵

    **僅管理員可執行**

    批次計算所有員工的月度獎勵（+M02、+M03）
    """
    service = MonthlyRewardCalculatorService(db)

    try:
        result = service.calculate_month_batch(data.year, data.month)
        db.commit()
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"月度獎勵計算失敗：{str(e)}"
        )


@router.post("/monthly-rewards/preview")
async def preview_monthly_rewards(
    data: MonthlyRewardCalculateRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    預覽月度獎勵計算結果（不實際寫入）

    **僅管理員可執行**
    """
    service = MonthlyRewardCalculatorService(db)
    return service.preview_month_calculation(data.year, data.month)


@router.get("/monthly-rewards/list")
async def list_monthly_rewards(
    year: int = Query(..., description="年度"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """
    取得月度獎勵列表
    """
    service = MonthlyRewardCalculatorService(db)
    rewards = service.get_month_rewards(year, month)

    return [
        {
            "id": r.id,
            "employee_id": r.employee_id,
            "year_month": r.year_month,
            "full_attendance": r.full_attendance,
            "driving_zero_violation": r.driving_zero_violation,
            "all_zero_violation": r.all_zero_violation,
            "total_points": r.total_points,
            "calculated_at": r.calculated_at.isoformat()
        }
        for r in rewards
    ]


@router.post("/annual-reset")
async def execute_annual_reset(
    data: AnnualResetRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    執行年度重置

    **僅管理員可執行**

    此操作會：
    1. 重置所有在職員工的分數為 80 分
    2. 重置指定年度的累計次數為 0
    3. 保留歷史考核記錄
    """
    if not data.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請確認執行（confirm=true）"
        )

    service = AnnualResetService(db)

    try:
        result = service.execute_annual_reset(year=data.year, dry_run=False)
        db.commit()
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"年度重置失敗：{str(e)}"
        )


@router.post("/annual-reset/preview")
async def preview_annual_reset(
    year: Optional[int] = Query(None, description="年度"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    預覽年度重置的影響

    **僅管理員可執行**
    """
    service = AnnualResetService(db)
    return service.preview_reset(year=year)


@router.get("/annual-reset/eligibility")
async def check_reset_eligibility(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    檢查是否可執行年度重置

    **僅管理員可執行**
    """
    service = AnnualResetService(db)
    return service.check_reset_eligibility()


# Helper functions
def _to_response(record) -> AssessmentRecordResponse:
    """轉換考核記錄為回應格式"""
    fault_responsibility = None
    if record.fault_responsibility:
        fr = record.fault_responsibility
        fault_responsibility = {
            "id": fr.id,
            "delay_seconds": fr.delay_seconds,
            "delay_minutes": fr.delay_minutes,
            "checklist_results": fr.checklist_results,
            "fault_count": fr.fault_count,
            "responsibility_level": fr.responsibility_level,
            "responsibility_coefficient": fr.responsibility_coefficient,
            "checked_items": fr.checked_items_labels,
            "notes": fr.notes,
            "time_t0": fr.time_t0.isoformat() if fr.time_t0 else None,
            "time_t1": fr.time_t1.isoformat() if fr.time_t1 else None,
            "time_t2": fr.time_t2.isoformat() if fr.time_t2 else None,
            "time_t3": fr.time_t3.isoformat() if fr.time_t3 else None,
            "time_t4": fr.time_t4.isoformat() if fr.time_t4 else None,
        }

    return AssessmentRecordResponse(
        id=record.id,
        employee_id=record.employee_id,
        standard_code=record.standard_code,
        standard_name=record.standard.name if record.standard else "",
        profile_id=record.profile_id,
        record_date=record.record_date.isoformat(),
        description=record.description,
        base_points=record.base_points,
        responsibility_coefficient=record.responsibility_coefficient,
        actual_points=record.actual_points,
        cumulative_count=record.cumulative_count,
        cumulative_multiplier=record.cumulative_multiplier,
        final_points=record.final_points,
        is_deleted=record.is_deleted,
        fault_responsibility=fault_responsibility,
        created_at=record.created_at.isoformat(),
        updated_at=record.updated_at.isoformat()
    )
