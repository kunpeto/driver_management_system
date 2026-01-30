"""
月度獎勵計算服務
對應 tasks.md T173: 實作月度獎勵計算服務
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 月度獎勵計算邏輯

此服務負責計算員工每月的月度獎勵，
包含 +M02（行車零違規）和 +M03（全項目零違規）的判定。
"""

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import and_, extract, func, select
from sqlalchemy.orm import Session

from ..models.assessment_record import AssessmentRecord
from ..models.assessment_standard import AssessmentStandard
from ..models.employee import Employee
from ..models.monthly_reward import MonthlyReward


class MonthlyRewardCalculatorService:
    """
    月度獎勵計算服務

    計算並發放月度獎勵：
    - +M01: 月度全勤（+3 分，由差勤系統處理）
    - +M02: 月度行車零違規（+1 分，R+S 類無扣分）
    - +M03: 月度全項目零違規（+2 分，D/W/O/S/R 類皆無扣分）

    +M02 和 +M03 可疊加。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: 資料庫 Session
        """
        self.db = db

    def calculate_employee_month(
        self,
        employee_id: int,
        year: int,
        month: int,
        include_full_attendance: bool = False
    ) -> Optional[MonthlyReward]:
        """
        計算單一員工單月的月度獎勵

        Args:
            employee_id: 員工 ID
            year: 年度
            month: 月份（1-12）
            include_full_attendance: 是否包含全勤獎勵（由外部判定）

        Returns:
            月度獎勵記錄或 None（若無任何獎勵）
        """
        year_month = f"{year:04d}-{month:02d}"

        # 查詢當月扣分記錄的類別
        deduction_categories = self._get_month_deduction_categories(
            employee_id, year, month
        )

        # 判定 +M02（R、S 類零違規）
        driving_zero = not any(cat in ['R', 'S'] for cat in deduction_categories)

        # 判定 +M03（全類別零違規）
        all_zero = len(deduction_categories) == 0

        # 計算總分
        total = 0.0
        if include_full_attendance:
            total += 3.0  # +M01
        if driving_zero:
            total += 1.0  # +M02
        if all_zero:
            total += 2.0  # +M03

        # 查詢現有月度獎勵記錄
        existing = self.db.execute(
            select(MonthlyReward).where(
                and_(
                    MonthlyReward.employee_id == employee_id,
                    MonthlyReward.year_month == year_month
                )
            )
        ).scalar_one_or_none()

        # P1 修正：處理「回溯建檔」導致的獎勵溢發
        # 若現在不符合獎勵資格，但之前已發放獎勵，需要撤銷
        if total == 0:
            if existing and existing.has_any_reward:
                # 撤銷已發放的獎勵
                self._revoke_reward_records(employee_id, year, month, existing)
                existing.full_attendance = False
                existing.driving_zero_violation = False
                existing.all_zero_violation = False
                existing.total_points = 0
            return None

        if existing:
            # 檢查是否需要撤銷部分獎勵（例如：原本有 +M03，現在只有 +M02）
            old_driving_zero = existing.driving_zero_violation
            old_all_zero = existing.all_zero_violation

            # 更新現有記錄
            existing.full_attendance = include_full_attendance
            existing.driving_zero_violation = driving_zero
            existing.all_zero_violation = all_zero
            existing.total_points = total
            reward = existing

            # P1 修正：撤銷不再符合的獎勵
            self._sync_reward_records(
                employee_id, year, month,
                old_driving_zero, old_all_zero,
                driving_zero, all_zero
            )
        else:
            # 建立新記錄
            reward = MonthlyReward(
                employee_id=employee_id,
                year_month=year_month,
                full_attendance=include_full_attendance,
                driving_zero_violation=driving_zero,
                all_zero_violation=all_zero,
                total_points=total
            )
            self.db.add(reward)
            # 建立對應的考核記錄
            self._create_reward_records(employee_id, year, month, driving_zero, all_zero)

        return reward

    def calculate_month_batch(
        self,
        year: int,
        month: int
    ) -> dict[str, Any]:
        """
        批次計算所有員工的月度獎勵

        Args:
            year: 年度
            month: 月份

        Returns:
            計算結果統計
        """
        # 取得所有在職員工
        employees = self.db.execute(
            select(Employee).where(Employee.is_resigned == False)
        ).scalars().all()

        result = {
            "year": year,
            "month": month,
            "total_employees": len(employees),
            "driving_zero_count": 0,  # +M02
            "all_zero_count": 0,  # +M03
            "no_reward_count": 0,
            "rewards": []
        }

        for employee in employees:
            reward = self.calculate_employee_month(employee.id, year, month)

            if reward:
                if reward.driving_zero_violation:
                    result["driving_zero_count"] += 1
                if reward.all_zero_violation:
                    result["all_zero_count"] += 1

                result["rewards"].append({
                    "employee_id": employee.id,
                    "employee_name": employee.employee_name,
                    "driving_zero_violation": reward.driving_zero_violation,
                    "all_zero_violation": reward.all_zero_violation,
                    "total_points": reward.total_points
                })
            else:
                result["no_reward_count"] += 1

        return result

    def get_month_rewards(
        self,
        year: int,
        month: int
    ) -> list[MonthlyReward]:
        """
        取得指定月份的所有月度獎勵記錄

        Args:
            year: 年度
            month: 月份

        Returns:
            月度獎勵記錄列表
        """
        year_month = f"{year:04d}-{month:02d}"

        return list(
            self.db.execute(
                select(MonthlyReward).where(
                    MonthlyReward.year_month == year_month
                )
            ).scalars().all()
        )

    def get_employee_rewards(
        self,
        employee_id: int,
        year: Optional[int] = None
    ) -> list[MonthlyReward]:
        """
        取得員工的月度獎勵記錄

        Args:
            employee_id: 員工 ID
            year: 年度（可選）

        Returns:
            月度獎勵記錄列表
        """
        stmt = select(MonthlyReward).where(
            MonthlyReward.employee_id == employee_id
        )

        if year:
            stmt = stmt.where(MonthlyReward.year_month.like(f"{year}-%"))

        stmt = stmt.order_by(MonthlyReward.year_month.desc())

        return list(self.db.execute(stmt).scalars().all())

    def _get_month_deduction_categories(
        self,
        employee_id: int,
        year: int,
        month: int
    ) -> set[str]:
        """
        取得員工當月有扣分的類別

        Args:
            employee_id: 員工 ID
            year: 年度
            month: 月份

        Returns:
            有扣分的類別集合
        """
        # 查詢當月扣分記錄（base_points < 0）
        stmt = (
            select(AssessmentStandard.category)
            .distinct()
            .join(AssessmentRecord)
            .where(
                and_(
                    AssessmentRecord.employee_id == employee_id,
                    AssessmentRecord.is_deleted == False,
                    extract('year', AssessmentRecord.record_date) == year,
                    extract('month', AssessmentRecord.record_date) == month,
                    AssessmentStandard.base_points < 0  # 僅查扣分項目
                )
            )
        )

        categories = self.db.execute(stmt).scalars().all()
        return set(categories)

    def _create_reward_records(
        self,
        employee_id: int,
        year: int,
        month: int,
        driving_zero: bool,
        all_zero: bool
    ) -> list[AssessmentRecord]:
        """
        建立月度獎勵的考核記錄

        Args:
            employee_id: 員工 ID
            year: 年度
            month: 月份
            driving_zero: 是否獲得 +M02
            all_zero: 是否獲得 +M03

        Returns:
            建立的考核記錄列表
        """
        records = []
        record_date = date(year, month, 1)

        # 檢查是否已有該月的 +M02 記錄
        if driving_zero:
            existing_m02 = self.db.execute(
                select(AssessmentRecord).where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.standard_code == '+M02',
                        extract('year', AssessmentRecord.record_date) == year,
                        extract('month', AssessmentRecord.record_date) == month,
                        AssessmentRecord.is_deleted == False
                    )
                )
            ).scalar_one_or_none()

            if not existing_m02:
                record = AssessmentRecord(
                    employee_id=employee_id,
                    standard_code='+M02',
                    record_date=record_date,
                    description=f"{year}年{month}月 行車零違規獎勵",
                    base_points=1.0,
                    responsibility_coefficient=1.0,
                    actual_points=1.0,
                    cumulative_multiplier=1.0,
                    final_points=1.0
                )
                self.db.add(record)
                records.append(record)

                # 更新員工分數
                employee = self.db.execute(
                    select(Employee).where(Employee.id == employee_id)
                ).scalar_one()
                employee.current_score += 1.0

        # 檢查是否已有該月的 +M03 記錄
        if all_zero:
            existing_m03 = self.db.execute(
                select(AssessmentRecord).where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.standard_code == '+M03',
                        extract('year', AssessmentRecord.record_date) == year,
                        extract('month', AssessmentRecord.record_date) == month,
                        AssessmentRecord.is_deleted == False
                    )
                )
            ).scalar_one_or_none()

            if not existing_m03:
                record = AssessmentRecord(
                    employee_id=employee_id,
                    standard_code='+M03',
                    record_date=record_date,
                    description=f"{year}年{month}月 全項目零違規獎勵",
                    base_points=2.0,
                    responsibility_coefficient=1.0,
                    actual_points=2.0,
                    cumulative_multiplier=1.0,
                    final_points=2.0
                )
                self.db.add(record)
                records.append(record)

                # 更新員工分數
                employee = self.db.execute(
                    select(Employee).where(Employee.id == employee_id)
                ).scalar_one()
                employee.current_score += 2.0

        return records

    def _revoke_reward_records(
        self,
        employee_id: int,
        year: int,
        month: int,
        existing_reward: MonthlyReward
    ) -> None:
        """
        撤銷已發放的月度獎勵考核記錄

        P1 修正：處理「回溯建檔」導致的獎勵溢發

        Args:
            employee_id: 員工 ID
            year: 年度
            month: 月份
            existing_reward: 現有的月度獎勵記錄
        """
        points_to_deduct = 0.0

        # 撤銷 +M02
        if existing_reward.driving_zero_violation:
            m02_record = self.db.execute(
                select(AssessmentRecord).where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.standard_code == '+M02',
                        extract('year', AssessmentRecord.record_date) == year,
                        extract('month', AssessmentRecord.record_date) == month,
                        AssessmentRecord.is_deleted == False
                    )
                )
            ).scalar_one_or_none()

            if m02_record:
                m02_record.is_deleted = True
                m02_record.deleted_at = datetime.now()
                points_to_deduct += 1.0

        # 撤銷 +M03
        if existing_reward.all_zero_violation:
            m03_record = self.db.execute(
                select(AssessmentRecord).where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.standard_code == '+M03',
                        extract('year', AssessmentRecord.record_date) == year,
                        extract('month', AssessmentRecord.record_date) == month,
                        AssessmentRecord.is_deleted == False
                    )
                )
            ).scalar_one_or_none()

            if m03_record:
                m03_record.is_deleted = True
                m03_record.deleted_at = datetime.now()
                points_to_deduct += 2.0

        # 更新員工分數
        if points_to_deduct > 0:
            employee = self.db.execute(
                select(Employee).where(Employee.id == employee_id)
            ).scalar_one()
            employee.current_score -= points_to_deduct

    def _sync_reward_records(
        self,
        employee_id: int,
        year: int,
        month: int,
        old_driving_zero: bool,
        old_all_zero: bool,
        new_driving_zero: bool,
        new_all_zero: bool
    ) -> None:
        """
        同步獎勵考核記錄（處理部分撤銷與補發）

        P1 修正：處理獎勵狀態變更時的考核記錄同步

        Args:
            employee_id: 員工 ID
            year: 年度
            month: 月份
            old_driving_zero: 原本是否有 +M02
            old_all_zero: 原本是否有 +M03
            new_driving_zero: 現在是否符合 +M02
            new_all_zero: 現在是否符合 +M03
        """
        record_date = date(year, month, 1)

        # 處理 +M02
        if old_driving_zero and not new_driving_zero:
            # 撤銷 +M02
            m02_record = self.db.execute(
                select(AssessmentRecord).where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.standard_code == '+M02',
                        extract('year', AssessmentRecord.record_date) == year,
                        extract('month', AssessmentRecord.record_date) == month,
                        AssessmentRecord.is_deleted == False
                    )
                )
            ).scalar_one_or_none()

            if m02_record:
                m02_record.is_deleted = True
                m02_record.deleted_at = datetime.now()
                employee = self.db.execute(
                    select(Employee).where(Employee.id == employee_id)
                ).scalar_one()
                employee.current_score -= 1.0

        elif not old_driving_zero and new_driving_zero:
            # 補發 +M02
            existing = self.db.execute(
                select(AssessmentRecord).where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.standard_code == '+M02',
                        extract('year', AssessmentRecord.record_date) == year,
                        extract('month', AssessmentRecord.record_date) == month,
                        AssessmentRecord.is_deleted == False
                    )
                )
            ).scalar_one_or_none()

            if not existing:
                record = AssessmentRecord(
                    employee_id=employee_id,
                    standard_code='+M02',
                    record_date=record_date,
                    description=f"{year}年{month}月 行車零違規獎勵",
                    base_points=1.0,
                    responsibility_coefficient=1.0,
                    actual_points=1.0,
                    cumulative_multiplier=1.0,
                    final_points=1.0
                )
                self.db.add(record)
                employee = self.db.execute(
                    select(Employee).where(Employee.id == employee_id)
                ).scalar_one()
                employee.current_score += 1.0

        # 處理 +M03
        if old_all_zero and not new_all_zero:
            # 撤銷 +M03
            m03_record = self.db.execute(
                select(AssessmentRecord).where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.standard_code == '+M03',
                        extract('year', AssessmentRecord.record_date) == year,
                        extract('month', AssessmentRecord.record_date) == month,
                        AssessmentRecord.is_deleted == False
                    )
                )
            ).scalar_one_or_none()

            if m03_record:
                m03_record.is_deleted = True
                m03_record.deleted_at = datetime.now()
                employee = self.db.execute(
                    select(Employee).where(Employee.id == employee_id)
                ).scalar_one()
                employee.current_score -= 2.0

        elif not old_all_zero and new_all_zero:
            # 補發 +M03
            existing = self.db.execute(
                select(AssessmentRecord).where(
                    and_(
                        AssessmentRecord.employee_id == employee_id,
                        AssessmentRecord.standard_code == '+M03',
                        extract('year', AssessmentRecord.record_date) == year,
                        extract('month', AssessmentRecord.record_date) == month,
                        AssessmentRecord.is_deleted == False
                    )
                )
            ).scalar_one_or_none()

            if not existing:
                record = AssessmentRecord(
                    employee_id=employee_id,
                    standard_code='+M03',
                    record_date=record_date,
                    description=f"{year}年{month}月 全項目零違規獎勵",
                    base_points=2.0,
                    responsibility_coefficient=1.0,
                    actual_points=2.0,
                    cumulative_multiplier=1.0,
                    final_points=2.0
                )
                self.db.add(record)
                employee = self.db.execute(
                    select(Employee).where(Employee.id == employee_id)
                ).scalar_one()
                employee.current_score += 2.0

    def preview_month_calculation(
        self,
        year: int,
        month: int
    ) -> dict[str, Any]:
        """
        預覽月度獎勵計算結果（不實際寫入）

        Args:
            year: 年度
            month: 月份

        Returns:
            預覽結果
        """
        employees = self.db.execute(
            select(Employee).where(Employee.is_resigned == False)
        ).scalars().all()

        result = {
            "year": year,
            "month": month,
            "total_employees": len(employees),
            "preview": []
        }

        for employee in employees:
            deduction_categories = self._get_month_deduction_categories(
                employee.id, year, month
            )

            driving_zero = not any(cat in ['R', 'S'] for cat in deduction_categories)
            all_zero = len(deduction_categories) == 0

            total = 0.0
            if driving_zero:
                total += 1.0
            if all_zero:
                total += 2.0

            result["preview"].append({
                "employee_id": employee.id,
                "employee_name": employee.employee_name,
                "deduction_categories": list(deduction_categories),
                "driving_zero_violation": driving_zero,
                "all_zero_violation": all_zero,
                "expected_points": total
            })

        return result
