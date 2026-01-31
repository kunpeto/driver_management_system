"""
駕駛競賽排名 API 端點
對應 tasks.md T113: 實作駕駛競賽排名 API

提供季度競賽排名的查詢功能。
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import require_admin
from src.services.driving_competition_ranker import (
    DrivingCompetitionRanker,
    DrivingCompetitionRankerError,
)

router = APIRouter()


# ============================================================
# Pydantic 模型
# ============================================================

class RankingEntry(BaseModel):
    """排名項目"""
    id: int
    employee_id: int
    employee_code: Optional[str]
    employee_name: Optional[str]
    department: str
    total_driving_minutes: int
    total_hours: float
    holiday_work_bonus_minutes: int
    effective_minutes: int
    effective_hours: float
    incident_count: int
    final_score: float
    rank_in_department: int
    is_qualified: bool
    is_employed_on_last_day: bool
    bonus_amount: int


class RankingStats(BaseModel):
    """排名統計"""
    total_employees: int
    qualified_count: int
    bonus_recipients: int
    total_bonus: int


class CompetitionRankingResponse(BaseModel):
    """競賽排名回應"""
    year: int
    quarter: int
    quarter_label: str
    rankings: List[RankingEntry]
    stats: RankingStats


class EmployeeHistoryEntry(BaseModel):
    """員工歷史記錄項目"""
    year: int
    quarter: int
    quarter_label: str
    department: str
    total_hours: float
    effective_hours: float
    final_score: float
    rank: int
    is_qualified: bool
    bonus_amount: int


class EmployeeHistoryResponse(BaseModel):
    """員工歷史回應"""
    employee_id: int
    history: List[EmployeeHistoryEntry]


class CalculationResult(BaseModel):
    """計算結果"""
    year: int
    quarter: int
    start_date: str
    end_date: str
    departments: dict
    total_processed: int
    errors: List[str]


# ============================================================
# API 端點
# ============================================================

@router.get("/driving/competition", response_model=CompetitionRankingResponse)
async def get_competition_ranking(
    year: int = Query(..., ge=2020, le=2100, description="年份"),
    quarter: int = Query(..., ge=1, le=4, description="季度 (1-4)"),
    department: Optional[str] = Query(None, description="篩選部門"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    查詢季度競賽排名

    參數說明：
    - year: 年份
    - quarter: 季度（1=Q1/1-3月, 2=Q2/4-6月, 3=Q3/7-9月, 4=Q4/10-12月）
    - department: 篩選部門（可選，淡海 或 安坑）

    返回：
    - rankings: 排名列表，包含員工資訊、時數、積分、排名、資格狀態、獎金
    - stats: 統計資訊，包含總人數、符合資格人數、獲獎人數、獎金總額
    """
    ranker = DrivingCompetitionRanker(db)

    result = ranker.get_quarterly_ranking(
        year=year,
        quarter=quarter,
        department=department
    )

    return CompetitionRankingResponse(
        year=result["year"],
        quarter=result["quarter"],
        quarter_label=result["quarter_label"],
        rankings=[RankingEntry(**r) for r in result["rankings"]],
        stats=RankingStats(**result["stats"])
    )


@router.get("/driving/competition/employee/{employee_id}", response_model=EmployeeHistoryResponse)
async def get_employee_competition_history(
    employee_id: int,
    limit: int = Query(8, ge=1, le=20, description="限制筆數"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    查詢員工競賽歷史

    返回指定員工最近的競賽排名歷史記錄。
    """
    ranker = DrivingCompetitionRanker(db)

    history = ranker.get_employee_history(employee_id, limit)

    return EmployeeHistoryResponse(
        employee_id=employee_id,
        history=[EmployeeHistoryEntry(**h) for h in history]
    )


@router.post("/driving/competition/calculate", response_model=CalculationResult)
async def calculate_competition_ranking(
    year: int = Query(..., ge=2020, le=2100, description="年份"),
    quarter: int = Query(..., ge=1, le=4, description="季度 (1-4)"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin),
):
    """
    手動計算季度競賽排名

    僅管理員可執行。

    此 API 會立即執行指定季度的排名計算：
    1. 彙總該季度所有員工的駕駛時數
    2. 計算 R班加成與責任事件懲罰
    3. 檢查資格（≥300小時 且 季末在職）
    4. 依部門排名並分配獎金

    注意：此操作會覆蓋該季度已存在的排名資料。
    """
    ranker = DrivingCompetitionRanker(db)

    try:
        result = ranker.calculate_quarterly_ranking(year, quarter)

        # 簡化 departments 回傳格式
        simplified_departments = {}
        for dept, data in result["departments"].items():
            simplified_departments[dept] = {
                "processed": data["processed"],
                "qualified_count": data["qualified_count"],
                "bonus_recipients": data["bonus_recipients"],
                "total_bonus": data["total_bonus"]
            }

        return CalculationResult(
            year=result["year"],
            quarter=result["quarter"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            departments=simplified_departments,
            total_processed=result["total_processed"],
            errors=result["errors"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"計算失敗: {str(e)}"
        )


@router.get("/driving/competition/bonus-tiers")
async def get_bonus_tiers(
    current_user: TokenData = Depends(get_current_user),
):
    """
    取得獎金階層設定

    返回各部門的排名名額與獎金金額。
    """
    from src.models.driving_competition import DrivingCompetition

    return {
        "qualification_hours": DrivingCompetition.QUALIFICATION_MINUTES / 60,
        "qualification_minutes": DrivingCompetition.QUALIFICATION_MINUTES,
        "bonus_tiers": DrivingCompetition.BONUS_TIERS,
        "rules": {
            "淡海": {
                "max_rank": 5,
                "amounts": DrivingCompetition.BONUS_TIERS["淡海"]
            },
            "安坑": {
                "max_rank": 3,
                "amounts": DrivingCompetition.BONUS_TIERS["安坑"]
            }
        }
    }
