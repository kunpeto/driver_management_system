"""
年度重置服務
對應 tasks.md T174: 實作年度重置服務
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 年度重置流程

此服務負責每年 1/1 的年度重置操作，
包含重置員工分數與累計次數。
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from ..models.cumulative_counter import CumulativeCounter
from ..models.employee import Employee


class AnnualResetService:
    """
    年度重置服務

    執行每年 1/1 的年度重置：
    1. 重置所有員工的 current_score 為 80 分
    2. 重置所有累計次數計數器為 0
    3. 保留歷史考核記錄（不刪除）
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: 資料庫 Session
        """
        self.db = db

    def execute_annual_reset(
        self,
        year: Optional[int] = None,
        dry_run: bool = False
    ) -> dict[str, Any]:
        """
        執行年度重置

        Args:
            year: 要重置的年度（預設為當前年度）
            dry_run: 是否為模擬執行（不實際寫入）

        Returns:
            重置結果統計
        """
        if year is None:
            year = datetime.now().year

        result = {
            "year": year,
            "dry_run": dry_run,
            "executed_at": datetime.now().isoformat(),
            "employees_reset": 0,
            "counters_reset": 0
        }

        # 查詢將受影響的記錄數
        employee_count = self.db.execute(
            select(Employee).where(Employee.is_resigned == False)
        ).all()
        result["employees_reset"] = len(employee_count)

        counter_count = self.db.execute(
            select(CumulativeCounter).where(CumulativeCounter.year == year)
        ).all()
        result["counters_reset"] = len(counter_count)

        if not dry_run:
            # 1. 重置所有在職員工的分數為 80 分
            self.db.execute(
                update(Employee)
                .where(Employee.is_resigned == False)
                .values(current_score=80.0)
            )

            # 2. 重置指定年度的累計次數為 0
            self.db.execute(
                update(CumulativeCounter)
                .where(CumulativeCounter.year == year)
                .values(count=0)
            )

            result["status"] = "completed"
        else:
            result["status"] = "dry_run"

        return result

    def preview_reset(self, year: Optional[int] = None) -> dict[str, Any]:
        """
        預覽年度重置的影響

        Args:
            year: 年度

        Returns:
            預覽結果
        """
        if year is None:
            year = datetime.now().year

        # 查詢將受影響的員工
        employees = self.db.execute(
            select(Employee).where(Employee.is_resigned == False)
        ).scalars().all()

        # 查詢將受影響的累計次數
        counters = self.db.execute(
            select(CumulativeCounter).where(CumulativeCounter.year == year)
        ).scalars().all()

        # 統計各類別的累計次數
        category_totals = {}
        for counter in counters:
            if counter.category not in category_totals:
                category_totals[counter.category] = 0
            category_totals[counter.category] += counter.count

        # 統計員工分數分布
        score_distribution = {
            "above_80": 0,
            "at_80": 0,
            "below_80": 0,
            "min_score": None,
            "max_score": None,
            "avg_score": 0
        }

        total_score = 0
        for emp in employees:
            total_score += emp.current_score
            if emp.current_score > 80:
                score_distribution["above_80"] += 1
            elif emp.current_score < 80:
                score_distribution["below_80"] += 1
            else:
                score_distribution["at_80"] += 1

            if score_distribution["min_score"] is None or emp.current_score < score_distribution["min_score"]:
                score_distribution["min_score"] = emp.current_score
            if score_distribution["max_score"] is None or emp.current_score > score_distribution["max_score"]:
                score_distribution["max_score"] = emp.current_score

        if employees:
            score_distribution["avg_score"] = total_score / len(employees)

        return {
            "year": year,
            "employees_affected": len(employees),
            "counters_affected": len(counters),
            "category_totals": category_totals,
            "score_distribution": score_distribution,
            "employees_preview": [
                {
                    "id": emp.id,
                    "name": emp.employee_name,
                    "current_score": emp.current_score,
                    "score_change": 80.0 - emp.current_score
                }
                for emp in employees[:10]  # 只顯示前 10 筆
            ]
        }

    def initialize_new_year_counters(
        self,
        year: int,
        employee_ids: Optional[list[int]] = None
    ) -> int:
        """
        初始化新年度的累計次數計數器

        為所有在職員工建立 D, W, O, S, R 五個類別的計數器

        Args:
            year: 年度
            employee_ids: 要初始化的員工 ID 列表（若為 None 則處理所有在職員工）

        Returns:
            建立的計數器數量
        """
        categories = ['D', 'W', 'O', 'S', 'R']

        if employee_ids is None:
            employees = self.db.execute(
                select(Employee).where(Employee.is_resigned == False)
            ).scalars().all()
            employee_ids = [emp.id for emp in employees]

        created_count = 0

        for emp_id in employee_ids:
            for category in categories:
                # 檢查是否已存在
                existing = self.db.execute(
                    select(CumulativeCounter).where(
                        and_(
                            CumulativeCounter.employee_id == emp_id,
                            CumulativeCounter.year == year,
                            CumulativeCounter.category == category
                        )
                    )
                ).scalar_one_or_none()

                if not existing:
                    counter = CumulativeCounter(
                        employee_id=emp_id,
                        year=year,
                        category=category,
                        count=0
                    )
                    self.db.add(counter)
                    created_count += 1

        return created_count

    def check_reset_eligibility(self) -> dict[str, Any]:
        """
        檢查是否可執行年度重置

        Returns:
            檢查結果
        """
        now = datetime.now()
        current_year = now.year

        # 檢查是否為 1 月 1 日
        is_jan_first = now.month == 1 and now.day == 1

        # 檢查是否已執行過今年的重置（透過檢查是否有新年度的計數器）
        new_year_counters = self.db.execute(
            select(CumulativeCounter).where(
                CumulativeCounter.year == current_year
            ).limit(1)
        ).scalar_one_or_none()

        has_executed = new_year_counters is not None

        return {
            "current_year": current_year,
            "is_jan_first": is_jan_first,
            "has_executed_this_year": has_executed,
            "can_execute": not has_executed,
            "recommendation": (
                "建議執行年度重置" if is_jan_first and not has_executed
                else "無需執行" if has_executed
                else "非 1/1，若需強制執行請確認"
            )
        }
