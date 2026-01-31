"""
駕駛時數查詢 API 端點
對應 tasks.md T112: 實作駕駛時數查詢 API

提供駕駛時數統計的查詢功能。
"""

from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.services.driving_stats_calculator import DrivingStatsCalculator

router = APIRouter()


# ============================================================
# Pydantic 模型
# ============================================================

class DailyStatsResponse(BaseModel):
    """每日統計回應"""
    id: int
    employee_id: int
    department: str
    record_date: date
    total_minutes: int
    total_hours: float
    is_holiday_work: bool
    effective_minutes: int
    effective_hours: float
    incident_count: int


class DailyStatsListResponse(BaseModel):
    """每日統計列表回應"""
    items: List[DailyStatsResponse]
    total: int


class QuarterStatsResponse(BaseModel):
    """季度統計回應"""
    employee_id: int
    employee_code: Optional[str]
    employee_name: Optional[str]
    department: str
    year: int
    quarter: int
    start_date: str
    end_date: str
    total_minutes: int
    total_hours: float
    holiday_work_minutes: int
    holiday_work_bonus_minutes: int
    effective_minutes: int
    effective_hours: float
    work_days: int
    incident_count: int


class DepartmentQuarterStatsResponse(BaseModel):
    """部門季度統計回應"""
    department: str
    year: int
    quarter: int
    employees: List[QuarterStatsResponse]
    total_employees: int


# ============================================================
# API 端點
# ============================================================

@router.get("/driving/stats", response_model=DailyStatsListResponse)
async def list_daily_stats(
    employee_id: Optional[int] = Query(None, description="篩選員工 ID"),
    department: Optional[str] = Query(None, description="篩選部門"),
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="結束日期"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="限制筆數"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    查詢每日駕駛時數統計

    - 支援員工篩選
    - 支援部門篩選
    - 支援日期範圍篩選
    - 支援分頁
    - 非管理員僅能查詢自己的資料
    """
    # 日期範圍驗證
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="起始日期不能晚於結束日期"
        )

    # 權限檢查：非管理員僅能查詢自己的資料
    if not current_user.is_admin:
        if employee_id is None:
            # 未指定員工 ID，預設查詢自己
            employee_id = current_user.employee_id
        elif employee_id != current_user.employee_id:
            # 試圖查詢他人資料，拒絕
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="權限不足，僅能查詢個人資料"
            )

    calculator = DrivingStatsCalculator(db)

    items = calculator.list_daily_stats(
        employee_id=employee_id,
        department=department,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

    return DailyStatsListResponse(
        items=[
            DailyStatsResponse(
                id=item.id,
                employee_id=item.employee_id,
                department=item.department,
                record_date=item.record_date,
                total_minutes=item.total_minutes,
                total_hours=item.total_hours,
                is_holiday_work=item.is_holiday_work,
                effective_minutes=item.effective_minutes,
                effective_hours=item.effective_hours,
                incident_count=item.incident_count
            )
            for item in items
        ],
        total=len(items)
    )


@router.get("/driving/stats/quarter", response_model=QuarterStatsResponse)
async def get_employee_quarter_stats(
    employee_id: int = Query(..., description="員工 ID"),
    year: int = Query(..., ge=2020, le=2100, description="年份"),
    quarter: int = Query(..., ge=1, le=4, description="季度 (1-4)"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    查詢員工季度統計

    返回指定員工在指定季度的累計統計資料。
    非管理員僅能查詢自己的資料。
    """
    # 權限檢查：非管理員僅能查詢自己的資料
    if not current_user.is_admin and employee_id != current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足，僅能查詢個人資料"
        )

    calculator = DrivingStatsCalculator(db)

    stats = calculator.get_quarter_stats(employee_id, year, quarter)

    return QuarterStatsResponse(**stats)


@router.get("/driving/stats/quarter/department", response_model=DepartmentQuarterStatsResponse)
async def get_department_quarter_stats(
    department: str = Query(..., description="部門"),
    year: int = Query(..., ge=2020, le=2100, description="年份"),
    quarter: int = Query(..., ge=1, le=4, description="季度 (1-4)"),
    include_resigned: bool = Query(False, description="是否包含離職員工"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    查詢部門季度統計

    返回指定部門所有員工在指定季度的累計統計資料，按有效時數降序排列。
    """
    calculator = DrivingStatsCalculator(db)

    employees = calculator.get_quarter_stats_by_department(
        department=department,
        year=year,
        quarter=quarter,
        include_resigned=include_resigned
    )

    return DepartmentQuarterStatsResponse(
        department=department,
        year=year,
        quarter=quarter,
        employees=[QuarterStatsResponse(**emp) for emp in employees],
        total_employees=len(employees)
    )
