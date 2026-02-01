"""
班表查詢 API
對應 tasks.md T084: 實作班表查詢 API

功能：
- 查詢班表資料（支援日期與部門篩選）
- 查詢特定員工班表
- 查詢特定日期班表
"""

from datetime import date
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.models.schedule import Schedule
from src.constants import Department
from src.middleware.auth import get_current_user
from src.utils.logger import logger


router = APIRouter(prefix="/api/schedules", tags=["班表管理"])


# ===== Pydantic Models =====

class ScheduleResponse(BaseModel):
    """班表回應格式"""
    id: int
    employee_id: str
    employee_name: Optional[str]
    department: str
    schedule_date: date
    shift_code: str
    shift_type: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    overtime_hours: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    """班表列表回應"""
    total: int
    items: List[ScheduleResponse]
    page: int
    page_size: int


class EmployeeScheduleResponse(BaseModel):
    """員工班表回應（按日期組織）"""
    employee_id: str
    employee_name: Optional[str]
    department: str
    year: int
    month: int
    schedules: dict  # 日期 -> 班別資訊


class DailyScheduleResponse(BaseModel):
    """每日班表回應（按員工組織）"""
    date: date
    department: str
    schedules: List[ScheduleResponse]


class ScheduleStatisticsResponse(BaseModel):
    """班表統計回應"""
    department: str
    year: int
    month: int
    total_records: int
    employee_count: int
    shift_type_distribution: dict  # 班別類型 -> 數量
    r_shift_count: int
    leave_count: int
    overtime_count: int


# ===== API Endpoints =====

@router.get("", response_model=ScheduleListResponse)
async def get_schedules(
    department: Optional[Literal["淡海", "安坑"]] = Query(None, description="部門篩選"),
    start_date: Optional[date] = Query(None, description="開始日期"),
    end_date: Optional[date] = Query(None, description="結束日期"),
    employee_id: Optional[str] = Query(None, description="員工編號"),
    shift_type: Optional[str] = Query(None, description="班別類型"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(50, ge=1, le=500, description="每頁筆數"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    查詢班表資料

    支援多種篩選條件，分頁返回結果。
    """
    query = db.query(Schedule)

    # 套用篩選條件
    if department:
        query = query.filter(Schedule.department == department)
    if start_date:
        query = query.filter(Schedule.schedule_date >= start_date)
    if end_date:
        query = query.filter(Schedule.schedule_date <= end_date)
    if employee_id:
        query = query.filter(Schedule.employee_id == employee_id)
    if shift_type:
        query = query.filter(Schedule.shift_type == shift_type)

    # 計算總數
    total = query.count()

    # 分頁與排序
    schedules = query.order_by(
        Schedule.schedule_date.desc(),
        Schedule.employee_id
    ).offset((page - 1) * page_size).limit(page_size).all()

    return ScheduleListResponse(
        total=total,
        items=[ScheduleResponse.model_validate(s) for s in schedules],
        page=page,
        page_size=page_size
    )


@router.get("/employee/{employee_id}", response_model=EmployeeScheduleResponse)
async def get_employee_schedule(
    employee_id: str,
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    查詢特定員工的月班表

    返回員工指定月份的所有班表資料。
    """
    # 計算日期範圍
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    schedules = db.query(Schedule).filter(
        and_(
            Schedule.employee_id == employee_id,
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date < end_date
        )
    ).order_by(Schedule.schedule_date).all()

    if not schedules:
        raise HTTPException(
            status_code=404,
            detail=f"找不到員工 {employee_id} 在 {year} 年 {month} 月的班表"
        )

    # 組織為日期 -> 班別的格式
    schedule_dict = {}
    employee_name = None
    department = None

    for s in schedules:
        day = s.schedule_date.day
        schedule_dict[day] = {
            "shift_code": s.shift_code,
            "shift_type": s.shift_type,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "overtime_hours": s.overtime_hours
        }
        if not employee_name:
            employee_name = s.employee_name
        if not department:
            department = s.department

    return EmployeeScheduleResponse(
        employee_id=employee_id,
        employee_name=employee_name,
        department=department,
        year=year,
        month=month,
        schedules=schedule_dict
    )


@router.get("/daily/{schedule_date}", response_model=DailyScheduleResponse)
async def get_daily_schedule(
    schedule_date: date,
    department: Optional[Literal["淡海", "安坑"]] = Query(None, description="部門篩選"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    查詢特定日期的班表

    返回指定日期所有員工的班表。
    """
    query = db.query(Schedule).filter(Schedule.schedule_date == schedule_date)

    if department:
        query = query.filter(Schedule.department == department)

    schedules = query.order_by(Schedule.employee_id).all()

    if not schedules:
        raise HTTPException(
            status_code=404,
            detail=f"找不到 {schedule_date} 的班表資料"
        )

    return DailyScheduleResponse(
        date=schedule_date,
        department=department or "全部",
        schedules=[ScheduleResponse.model_validate(s) for s in schedules]
    )


@router.get("/statistics", response_model=ScheduleStatisticsResponse)
async def get_schedule_statistics(
    department: Literal["淡海", "安坑"] = Query(..., description="部門"),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    查詢班表統計資訊

    返回指定部門月份的班表統計。
    """
    # 計算日期範圍
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # 基本查詢條件
    base_filter = and_(
        Schedule.department == department,
        Schedule.schedule_date >= start_date,
        Schedule.schedule_date < end_date
    )

    # 總記錄數
    total_records = db.query(Schedule).filter(base_filter).count()

    # 員工數量
    employee_count = db.query(func.count(func.distinct(Schedule.employee_id))).filter(
        base_filter
    ).scalar()

    # 班別類型分佈
    shift_type_query = db.query(
        Schedule.shift_type,
        func.count(Schedule.id)
    ).filter(base_filter).group_by(Schedule.shift_type).all()

    shift_type_distribution = {
        st or "未分類": count
        for st, count in shift_type_query
    }

    # R班數量
    r_shift_count = db.query(Schedule).filter(
        and_(
            base_filter,
            Schedule.shift_code.like("R/%")
        )
    ).count()

    # 休假數量
    leave_count = db.query(Schedule).filter(
        and_(
            base_filter,
            Schedule.shift_type == "休假"
        )
    ).count()

    # 延長工時數量
    overtime_count = db.query(Schedule).filter(
        and_(
            base_filter,
            Schedule.overtime_hours.isnot(None),
            Schedule.overtime_hours > 0
        )
    ).count()

    return ScheduleStatisticsResponse(
        department=department,
        year=year,
        month=month,
        total_records=total_records,
        employee_count=employee_count,
        shift_type_distribution=shift_type_distribution,
        r_shift_count=r_shift_count,
        leave_count=leave_count,
        overtime_count=overtime_count
    )


@router.get("/lookup")
async def lookup_schedule(
    employee_id: str = Query(..., description="員工編號"),
    target_date: date = Query(..., description="目標日期"),
    days_before: int = Query(2, ge=0, le=7, description="往前查詢天數"),
    days_after: int = Query(2, ge=0, le=7, description="往後查詢天數"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    查詢特定員工特定日期前後的班表

    用於履歷系統（US8）查詢事件前後班別。

    Args:
        employee_id: 員工編號
        target_date: 目標日期（通常是事件發生日期）
        days_before: 往前查詢天數
        days_after: 往後查詢天數

    Returns:
        dict: 日期範圍內的班表資料
    """
    from datetime import timedelta

    start_date = target_date - timedelta(days=days_before)
    end_date = target_date + timedelta(days=days_after)

    schedules = db.query(Schedule).filter(
        and_(
            Schedule.employee_id == employee_id,
            Schedule.schedule_date >= start_date,
            Schedule.schedule_date <= end_date
        )
    ).order_by(Schedule.schedule_date).all()

    result = {
        "employee_id": employee_id,
        "target_date": target_date.isoformat(),
        "range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "schedules": {}
    }

    for s in schedules:
        # 計算相對於目標日期的偏移
        delta = (s.schedule_date - target_date).days
        if delta < 0:
            key = f"before_{abs(delta)}_days"
        elif delta > 0:
            key = f"after_{delta}_days"
        else:
            key = "event_day"

        result["schedules"][key] = {
            "date": s.schedule_date.isoformat(),
            "shift_code": s.shift_code,
            "shift_type": s.shift_type,
            "start_time": s.start_time,
            "end_time": s.end_time
        }

    return result
