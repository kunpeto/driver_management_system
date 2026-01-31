"""
累計次數計算服務
對應 tasks.md T168: 實作累計次數計算服務
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 累計次數計數器操作

此服務負責管理 CumulativeCounter 表，
提供查詢、更新、重算累計次數的功能。
"""

from datetime import date
from typing import Optional

from sqlalchemy import and_, extract, select
from sqlalchemy.orm import Session

from ..models.assessment_record import AssessmentRecord
from ..models.assessment_standard import AssessmentStandard
from ..models.cumulative_counter import CumulativeCounter
from .cumulative_category import (
    R_CUMULATIVE_GROUP,
    calculate_cumulative_multiplier,
    get_cumulative_category,
)


class CumulativeCalculatorService:
    """
    累計次數計算服務

    提供累計次數的查詢、更新、重算功能，
    支援 R 類合併計算規則。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: 資料庫 Session
        """
        self.db = db

    def get_current_count(
        self,
        employee_id: int,
        year: int,
        category: str
    ) -> int:
        """
        查詢員工指定年度類別的累計次數

        Args:
            employee_id: 員工 ID
            year: 年度
            category: 累計類別（應經過 get_cumulative_category 處理）

        Returns:
            累計次數（若無記錄則返回 0）
        """
        counter = self.db.execute(
            select(CumulativeCounter).where(
                and_(
                    CumulativeCounter.employee_id == employee_id,
                    CumulativeCounter.year == year,
                    CumulativeCounter.category == category
                )
            )
        ).scalar_one_or_none()

        return counter.count if counter else 0

    def get_next_count(
        self,
        employee_id: int,
        year: int,
        standard_code: str,
        category: str
    ) -> tuple[int, float]:
        """
        取得下一次違規的累計次數與倍率

        Args:
            employee_id: 員工 ID
            year: 年度
            standard_code: 考核標準代碼
            category: 原始類別

        Returns:
            (下一次累計次數, 累計倍率) 元組
        """
        cumulative_category = get_cumulative_category(standard_code, category)
        current_count = self.get_current_count(employee_id, year, cumulative_category)
        next_count = current_count + 1
        multiplier = calculate_cumulative_multiplier(next_count)
        return (next_count, multiplier)

    def increment_count(
        self,
        employee_id: int,
        year: int,
        standard_code: str,
        category: str
    ) -> CumulativeCounter:
        """
        遞增累計次數

        Args:
            employee_id: 員工 ID
            year: 年度
            standard_code: 考核標準代碼
            category: 原始類別

        Returns:
            更新後的 CumulativeCounter
        """
        cumulative_category = get_cumulative_category(standard_code, category)

        counter = self.db.execute(
            select(CumulativeCounter).where(
                and_(
                    CumulativeCounter.employee_id == employee_id,
                    CumulativeCounter.year == year,
                    CumulativeCounter.category == cumulative_category
                )
            )
        ).scalar_one_or_none()

        if counter:
            counter.count += 1
        else:
            counter = CumulativeCounter(
                employee_id=employee_id,
                year=year,
                category=cumulative_category,
                count=1
            )
            self.db.add(counter)

        return counter

    def recalculate_counts(
        self,
        employee_id: int,
        year: int,
        category: str
    ) -> list[AssessmentRecord]:
        """
        重算員工該年度該類別的累計次數

        此函數會：
        1. 查詢該員工該年度該類別所有未刪除的考核記錄
        2. 依 record_date 排序
        3. 重新計算每筆記錄的累計次數與倍率
        4. 更新累計次數計數器

        Args:
            employee_id: 員工 ID
            year: 年度
            category: 累計類別（應經過 get_cumulative_category 處理）

        Returns:
            更新後的考核記錄列表

        Note:
            category 應該是經過 get_cumulative_category() 處理後的值
            例如：R02/R03/R04/R05 應傳入 'R'，而非原始 category
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

    def get_employee_year_summary(
        self,
        employee_id: int,
        year: int
    ) -> dict[str, int]:
        """
        取得員工該年度各類別的累計次數摘要

        Args:
            employee_id: 員工 ID
            year: 年度

        Returns:
            類別到累計次數的字典
        """
        stmt = select(CumulativeCounter).where(
            and_(
                CumulativeCounter.employee_id == employee_id,
                CumulativeCounter.year == year
            )
        )

        counters = self.db.execute(stmt).scalars().all()
        return {c.category: c.count for c in counters}

    def reset_year(
        self,
        year: int,
        employee_id: Optional[int] = None
    ) -> int:
        """
        重置年度累計次數

        Args:
            year: 年度
            employee_id: 員工 ID（若為 None 則重置所有員工）

        Returns:
            重置的記錄數
        """
        stmt = select(CumulativeCounter).where(
            CumulativeCounter.year == year
        )

        if employee_id:
            stmt = stmt.where(CumulativeCounter.employee_id == employee_id)

        counters = list(self.db.execute(stmt).scalars().all())

        for counter in counters:
            counter.count = 0

        return len(counters)

    def initialize_employee_counters(
        self,
        employee_id: int,
        year: int
    ) -> list[CumulativeCounter]:
        """
        初始化員工年度累計次數計數器

        為員工建立 D, W, O, S, R 五個類別的計數器（初始 count=0）

        Args:
            employee_id: 員工 ID
            year: 年度

        Returns:
            建立的計數器列表
        """
        categories = ['D', 'W', 'O', 'S', 'R']
        counters = []

        for category in categories:
            # 檢查是否已存在
            existing = self.db.execute(
                select(CumulativeCounter).where(
                    and_(
                        CumulativeCounter.employee_id == employee_id,
                        CumulativeCounter.year == year,
                        CumulativeCounter.category == category
                    )
                )
            ).scalar_one_or_none()

            if not existing:
                counter = CumulativeCounter(
                    employee_id=employee_id,
                    year=year,
                    category=category,
                    count=0
                )
                self.db.add(counter)
                counters.append(counter)

        return counters
