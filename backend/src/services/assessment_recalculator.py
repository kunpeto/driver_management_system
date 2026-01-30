"""
考核記錄重算服務
對應 tasks.md T171: 實作考核記錄重算服務
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 刪除/修改後重算流程

此服務負責考核記錄的重算邏輯，
包含累計次數重算、員工總分重算等功能。
使用 Transaction + FOR UPDATE 鎖定確保並發安全。
"""

from datetime import date
from typing import Any, Optional

from sqlalchemy import and_, extract, func, select
from sqlalchemy.orm import Session

from ..models.assessment_record import AssessmentRecord
from ..models.assessment_standard import AssessmentStandard
from ..models.cumulative_counter import CumulativeCounter
from ..models.employee import Employee
from .cumulative_category import (
    R_CUMULATIVE_GROUP,
    calculate_cumulative_multiplier,
    get_cumulative_category,
)


class AssessmentRecalculatorService:
    """
    考核記錄重算服務

    提供考核記錄的重算功能，
    確保累計次數與員工總分的一致性。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: 資料庫 Session
        """
        self.db = db

    def recalculate_cumulative_counts(
        self,
        employee_id: int,
        year: int,
        category: str
    ) -> list[AssessmentRecord]:
        """
        重算員工該年度該類別的累計次數（Transaction）

        此函數會：
        1. 鎖定該員工該年度該類別所有記錄
        2. 依 record_date 排序重新計算累計次數
        3. 更新每筆記錄的累計倍率與最終分數
        4. 更新累計次數計數器

        Args:
            employee_id: 員工 ID
            year: 年度
            category: 累計類別（應經過 get_cumulative_category 處理）

        Returns:
            更新後的考核記錄列表

        Note:
            category 應該是經過 get_cumulative_category() 處理後的值
            例如：R02/R03/R04/R05 應傳入 'R'
        """
        # 查詢記錄（依類別不同處理）
        if category == 'R':
            # R 類特殊處理：查詢所有 R02-R05 的記錄
            stmt = (
                select(AssessmentRecord)
                .join(AssessmentStandard)
                .where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.is_deleted == False,
                        extract('year', AssessmentRecord.record_date) == year,
                        AssessmentStandard.code.in_(R_CUMULATIVE_GROUP),
                        AssessmentStandard.has_cumulative == True
                    )
                )
                .order_by(AssessmentRecord.record_date)
                .with_for_update()  # 鎖定記錄
            )
        else:
            # 一般類別：依 category 查詢
            stmt = (
                select(AssessmentRecord)
                .join(AssessmentStandard)
                .where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.is_deleted == False,
                        extract('year', AssessmentRecord.record_date) == year,
                        AssessmentStandard.category == category,
                        AssessmentStandard.has_cumulative == True
                    )
                )
                .order_by(AssessmentRecord.record_date)
                .with_for_update()  # 鎖定記錄
            )

        records = list(self.db.execute(stmt).scalars().all())

        # 重新計算累計次數
        for idx, record in enumerate(records, start=1):
            cumulative_count = idx
            cumulative_multiplier = calculate_cumulative_multiplier(cumulative_count)

            # 重新計算實際扣分（考慮責任係數）
            coefficient = record.responsibility_coefficient or 1.0
            actual_points = record.base_points * coefficient
            final_points = actual_points * cumulative_multiplier

            # 更新記錄
            record.cumulative_count = cumulative_count
            record.cumulative_multiplier = cumulative_multiplier
            record.actual_points = actual_points
            record.final_points = final_points

        # 更新累計次數計數器
        counter = self.db.execute(
            select(CumulativeCounter).where(
                and_(
                    CumulativeCounter.employee_id == employee_id,
                    CumulativeCounter.year == year,
                    CumulativeCounter.category == category
                )
            )
        ).scalar_one_or_none()

        if counter:
            counter.count = len(records)
        elif len(records) > 0:
            counter = CumulativeCounter(
                employee_id=employee_id,
                year=year,
                category=category,
                count=len(records)
            )
            self.db.add(counter)

        return records

    def recalculate_employee_total_score(self, employee_id: int) -> float:
        """
        重新計算員工總分

        總分 = 起始分數 80 + 所有考核記錄的 final_points 總和

        Args:
            employee_id: 員工 ID

        Returns:
            新的總分
        """
        employee = self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        ).scalar_one_or_none()

        if not employee:
            raise ValueError(f"員工 {employee_id} 不存在")

        # 查詢所有未刪除的考核記錄
        total = self.db.execute(
            select(func.coalesce(func.sum(AssessmentRecord.final_points), 0)).where(
                and_(
                    AssessmentRecord.employee_id == employee_id,
                    AssessmentRecord.is_deleted == False
                )
            )
        ).scalar_one()

        # 計算總分
        total_score = 80.0 + float(total)
        employee.current_score = total_score

        return total_score

    def recalculate_all_for_employee(
        self,
        employee_id: int,
        year: Optional[int] = None
    ) -> dict[str, int]:
        """
        重算員工所有類別的累計次數

        Args:
            employee_id: 員工 ID
            year: 年度（若為 None 則重算所有年度）

        Returns:
            重算結果統計
        """
        result = {"categories_updated": 0, "records_updated": 0}

        # 取得需要重算的年度與類別
        stmt = (
            select(
                extract('year', AssessmentRecord.record_date).label('year'),
                AssessmentStandard.category
            )
            .distinct()
            .join(AssessmentStandard)
            .where(
                and_(
                    AssessmentRecord.employee_id == employee_id,
                    AssessmentRecord.is_deleted == False,
                    AssessmentStandard.has_cumulative == True
                )
            )
        )

        if year:
            stmt = stmt.where(extract('year', AssessmentRecord.record_date) == year)

        year_categories = self.db.execute(stmt).fetchall()

        # 處理 R 類合併
        processed = set()
        for row in year_categories:
            record_year = int(row.year)
            category = row.category

            # R 類特殊處理
            if category == 'R':
                key = (record_year, 'R')
            else:
                key = (record_year, category)

            if key not in processed:
                processed.add(key)
                cumulative_category = 'R' if category == 'R' else category
                records = self.recalculate_cumulative_counts(
                    employee_id, record_year, cumulative_category
                )
                result["categories_updated"] += 1
                result["records_updated"] += len(records)

        # 重算員工總分
        self.recalculate_employee_total_score(employee_id)

        return result

    def recalculate_year_for_all_employees(self, year: int) -> dict[str, int]:
        """
        重算指定年度所有員工的累計次數

        Args:
            year: 年度

        Returns:
            重算結果統計
        """
        result = {"employees_updated": 0, "categories_updated": 0, "records_updated": 0}

        # 取得該年度有考核記錄的員工
        employee_ids = self.db.execute(
            select(AssessmentRecord.employee_id)
            .distinct()
            .where(
                and_(
                    extract('year', AssessmentRecord.record_date) == year,
                    AssessmentRecord.is_deleted == False
                )
            )
        ).scalars().all()

        for employee_id in employee_ids:
            employee_result = self.recalculate_all_for_employee(employee_id, year)
            result["employees_updated"] += 1
            result["categories_updated"] += employee_result["categories_updated"]
            result["records_updated"] += employee_result["records_updated"]

        return result

    def verify_employee_score(self, employee_id: int) -> dict[str, Any]:
        """
        驗證員工分數是否正確

        Args:
            employee_id: 員工 ID

        Returns:
            驗證結果
        """
        employee = self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        ).scalar_one_or_none()

        if not employee:
            raise ValueError(f"員工 {employee_id} 不存在")

        # 計算應有的總分
        total = self.db.execute(
            select(func.coalesce(func.sum(AssessmentRecord.final_points), 0)).where(
                and_(
                    AssessmentRecord.employee_id == employee_id,
                    AssessmentRecord.is_deleted == False
                )
            )
        ).scalar_one()

        expected_score = 80.0 + float(total)
        actual_score = employee.current_score
        is_correct = abs(expected_score - actual_score) < 0.001

        return {
            "employee_id": employee_id,
            "actual_score": actual_score,
            "expected_score": expected_score,
            "is_correct": is_correct,
            "difference": actual_score - expected_score
        }
