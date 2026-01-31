"""
AssessmentRecordService 考核記錄服務
對應 tasks.md T170: 實作 AssessmentRecordService
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 考核記錄業務邏輯

此服務負責考核記錄的建立、更新、查詢，
整合責任判定與累計倍率計算。
"""

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import and_, extract, func, select
from sqlalchemy.orm import Session, joinedload

from ..models.assessment_record import AssessmentRecord
from ..models.assessment_standard import AssessmentStandard
from ..models.employee import Employee
from ..models.fault_responsibility import FaultResponsibilityAssessment
from .assessment_standard_service import AssessmentStandardService
from .cumulative_calculator import CumulativeCalculatorService
from .cumulative_category import get_cumulative_category
from .fault_responsibility_service import FaultResponsibilityService


class AssessmentRecordService:
    """
    考核記錄服務

    提供考核記錄的建立、更新、查詢功能，
    整合責任判定與累計倍率計算。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: 資料庫 Session
        """
        self.db = db
        self.standard_service = AssessmentStandardService(db)
        self.cumulative_service = CumulativeCalculatorService(db)
        self.fault_service = FaultResponsibilityService(db)

    def get_by_id(
        self,
        record_id: int,
        include_deleted: bool = False
    ) -> Optional[AssessmentRecord]:
        """
        根據 ID 取得考核記錄

        Args:
            record_id: 考核記錄 ID
            include_deleted: 是否包含已刪除的記錄

        Returns:
            考核記錄或 None
        """
        stmt = select(AssessmentRecord).where(AssessmentRecord.id == record_id)

        if not include_deleted:
            stmt = stmt.where(AssessmentRecord.is_deleted == False)

        stmt = stmt.options(
            joinedload(AssessmentRecord.standard),
            joinedload(AssessmentRecord.fault_responsibility)
        )

        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_employee(
        self,
        employee_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
        category: Optional[str] = None,
        include_deleted: bool = False
    ) -> list[AssessmentRecord]:
        """
        取得員工的考核記錄

        Args:
            employee_id: 員工 ID
            year: 年度篩選
            month: 月份篩選
            category: 類別篩選
            include_deleted: 是否包含已刪除的記錄

        Returns:
            考核記錄列表
        """
        stmt = select(AssessmentRecord).where(
            AssessmentRecord.employee_id == employee_id
        )

        if not include_deleted:
            stmt = stmt.where(AssessmentRecord.is_deleted == False)

        if year:
            stmt = stmt.where(extract('year', AssessmentRecord.record_date) == year)

        if month:
            stmt = stmt.where(extract('month', AssessmentRecord.record_date) == month)

        if category:
            stmt = stmt.join(AssessmentStandard).where(
                AssessmentStandard.category == category
            )

        stmt = stmt.options(
            joinedload(AssessmentRecord.standard),
            joinedload(AssessmentRecord.fault_responsibility)
        ).order_by(AssessmentRecord.record_date.desc())

        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        employee_id: int,
        standard_code: str,
        record_date: date,
        description: Optional[str] = None,
        profile_id: Optional[int] = None,
        fault_responsibility_data: Optional[dict[str, Any]] = None
    ) -> AssessmentRecord:
        """
        建立考核記錄

        Args:
            employee_id: 員工 ID
            standard_code: 考核標準代碼
            record_date: 事件日期
            description: 事件描述
            profile_id: 關聯履歷 ID
            fault_responsibility_data: R02-R05 責任判定資料

        Returns:
            建立的考核記錄
        """
        # 1. 查詢考核標準
        standard = self.standard_service.get_by_code(standard_code)
        if not standard or not standard.is_active:
            raise ValueError(f"考核標準 '{standard_code}' 不存在或未啟用")

        # 2. 計算責任係數（R02-R05 專用）
        responsibility_coefficient = 1.0
        fault_count = 0

        if standard_code in {'R02', 'R03', 'R04', 'R05'} and fault_responsibility_data:
            checklist = fault_responsibility_data.get('checklist_results', {})
            fault_count = self.fault_service.calculate_fault_count(checklist)
            _, responsibility_coefficient = self.fault_service.determine_responsibility_level(fault_count)

        # 3. 計算實際扣分
        actual_points = standard.base_points * responsibility_coefficient

        # 4. 查詢累計次數
        year = record_date.year
        cumulative_count = None
        cumulative_multiplier = 1.0

        if standard.has_cumulative:
            next_count, cumulative_multiplier = self.cumulative_service.get_next_count(
                employee_id, year, standard_code, standard.category
            )
            cumulative_count = next_count

        # 5. 計算最終分數
        final_points = actual_points * cumulative_multiplier

        # 6. 建立考核記錄
        record = AssessmentRecord(
            employee_id=employee_id,
            standard_code=standard_code,
            profile_id=profile_id,
            record_date=record_date,
            description=description,
            base_points=standard.base_points,
            responsibility_coefficient=responsibility_coefficient,
            actual_points=actual_points,
            cumulative_count=cumulative_count,
            cumulative_multiplier=cumulative_multiplier,
            final_points=final_points
        )
        self.db.add(record)
        self.db.flush()  # 取得 ID

        # 7. 建立責任判定記錄（R02-R05 專用）
        if standard_code in {'R02', 'R03', 'R04', 'R05'} and fault_responsibility_data:
            self.fault_service.create_assessment(
                record_id=record.id,
                delay_seconds=fault_responsibility_data.get('delay_seconds', 0),
                checklist_results=fault_responsibility_data.get('checklist_results', {}),
                time_t0=fault_responsibility_data.get('time_t0'),
                time_t1=fault_responsibility_data.get('time_t1'),
                time_t2=fault_responsibility_data.get('time_t2'),
                time_t3=fault_responsibility_data.get('time_t3'),
                time_t4=fault_responsibility_data.get('time_t4'),
                notes=fault_responsibility_data.get('notes')
            )

        # 8. 更新累計次數
        if standard.has_cumulative:
            self.cumulative_service.increment_count(
                employee_id, year, standard_code, standard.category
            )

        # 9. 更新員工總分
        self._update_employee_score(employee_id, final_points)

        # 10. P1 修正：觸發月度獎勵重算（處理回溯建檔導致的獎勵溢發）
        if standard.base_points < 0:  # 僅扣分項目影響月度獎勵
            self._trigger_monthly_reward_check(employee_id, record_date.year, record_date.month)

        return record

    def update(
        self,
        record_id: int,
        description: Optional[str] = None,
        fault_responsibility_data: Optional[dict[str, Any]] = None
    ) -> AssessmentRecord:
        """
        更新考核記錄

        注意：不允許修改 standard_code 和 record_date，
        如需修改這些欄位，應刪除後重建。

        Args:
            record_id: 考核記錄 ID
            description: 事件描述
            fault_responsibility_data: R02-R05 責任判定資料

        Returns:
            更新後的考核記錄
        """
        record = self.get_by_id(record_id)
        if not record:
            raise ValueError(f"找不到考核記錄 ID: {record_id}")

        # 更新描述
        if description is not None:
            record.description = description

        # 更新責任判定（R02-R05 專用）
        if fault_responsibility_data and record.standard_code in {'R02', 'R03', 'R04', 'R05'}:
            old_final_points = record.final_points

            # 更新或建立責任判定
            if record.fault_responsibility:
                self.fault_service.update_assessment(
                    record.fault_responsibility.id,
                    checklist_results=fault_responsibility_data.get('checklist_results'),
                    delay_seconds=fault_responsibility_data.get('delay_seconds'),
                    time_t0=fault_responsibility_data.get('time_t0'),
                    time_t1=fault_responsibility_data.get('time_t1'),
                    time_t2=fault_responsibility_data.get('time_t2'),
                    time_t3=fault_responsibility_data.get('time_t3'),
                    time_t4=fault_responsibility_data.get('time_t4'),
                    notes=fault_responsibility_data.get('notes')
                )
            else:
                self.fault_service.create_assessment(
                    record_id=record.id,
                    delay_seconds=fault_responsibility_data.get('delay_seconds', 0),
                    checklist_results=fault_responsibility_data.get('checklist_results', {}),
                    time_t0=fault_responsibility_data.get('time_t0'),
                    time_t1=fault_responsibility_data.get('time_t1'),
                    time_t2=fault_responsibility_data.get('time_t2'),
                    time_t3=fault_responsibility_data.get('time_t3'),
                    time_t4=fault_responsibility_data.get('time_t4'),
                    notes=fault_responsibility_data.get('notes')
                )

            # 重新計算分數
            record.responsibility_coefficient = record.fault_responsibility.responsibility_coefficient
            record.actual_points = record.base_points * record.responsibility_coefficient
            record.final_points = record.actual_points * record.cumulative_multiplier

            # 更新員工總分（差額）
            score_diff = record.final_points - old_final_points
            if score_diff != 0:
                self._update_employee_score(record.employee_id, score_diff)

        return record

    def soft_delete(self, record_id: int) -> AssessmentRecord:
        """
        軟刪除考核記錄

        刪除後會觸發重算該年度該類別的累計次數

        Args:
            record_id: 考核記錄 ID

        Returns:
            已刪除的考核記錄
        """
        record = self.get_by_id(record_id)
        if not record:
            raise ValueError(f"找不到考核記錄 ID: {record_id}")

        # 保存重算所需資訊
        employee_id = record.employee_id
        year = record.record_date.year
        standard = record.standard
        cumulative_category = get_cumulative_category(record.standard_code, standard.category)

        # 軟刪除
        record.soft_delete()

        # 從員工總分中扣除
        self._update_employee_score(employee_id, -record.final_points)

        # 重算累計次數（若適用累計加重）
        if standard.has_cumulative:
            self.cumulative_service.recalculate_counts(employee_id, year, cumulative_category)
            # 重新計算員工總分
            self._recalculate_employee_total_score(employee_id)

        # P1 修正：觸發月度獎勵重算（刪除扣分記錄後可能需要補發獎勵）
        if standard.base_points < 0:
            self._trigger_monthly_reward_check(employee_id, year, record.record_date.month)

        return record

    def restore(self, record_id: int) -> AssessmentRecord:
        """
        還原軟刪除的考核記錄

        還原後會觸發重算該年度該類別的累計次數

        Args:
            record_id: 考核記錄 ID

        Returns:
            還原的考核記錄
        """
        record = self.get_by_id(record_id, include_deleted=True)
        if not record:
            raise ValueError(f"找不到考核記錄 ID: {record_id}")

        if not record.is_deleted:
            raise ValueError(f"考核記錄 ID: {record_id} 未被刪除")

        # 保存重算所需資訊
        employee_id = record.employee_id
        year = record.record_date.year
        standard = record.standard
        cumulative_category = get_cumulative_category(record.standard_code, standard.category)

        # 還原
        record.restore()

        # 重算累計次數（若適用累計加重）
        if standard.has_cumulative:
            self.cumulative_service.recalculate_counts(employee_id, year, cumulative_category)

        # 重新計算員工總分
        self._recalculate_employee_total_score(employee_id)

        # P1 修正：觸發月度獎勵重算（還原扣分記錄後可能需要撤銷獎勵）
        if standard.base_points < 0:
            self._trigger_monthly_reward_check(employee_id, year, record.record_date.month)

        return record

    def get_employee_year_summary(
        self,
        employee_id: int,
        year: int
    ) -> dict[str, Any]:
        """
        取得員工年度考核摘要

        Args:
            employee_id: 員工 ID
            year: 年度

        Returns:
            年度考核摘要
        """
        # 取得員工資訊
        employee = self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        ).scalar_one_or_none()

        if not employee:
            raise ValueError(f"找不到員工 ID: {employee_id}")

        # 取得該年度所有考核記錄
        records = self.get_by_employee(employee_id, year=year)

        # 統計各類別
        category_stats: dict[str, dict[str, Any]] = {}
        total_deduction = 0.0
        total_bonus = 0.0

        for record in records:
            category = record.standard.category
            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "total_points": 0.0,
                    "records": []
                }

            category_stats[category]["count"] += 1
            category_stats[category]["total_points"] += record.final_points
            category_stats[category]["records"].append({
                "id": record.id,
                "date": record.record_date.isoformat(),
                "standard_code": record.standard_code,
                "standard_name": record.standard.name,
                "final_points": record.final_points
            })

            if record.final_points < 0:
                total_deduction += record.final_points
            else:
                total_bonus += record.final_points

        # 取得累計次數
        cumulative_counts = self.cumulative_service.get_employee_year_summary(employee_id, year)

        return {
            "employee_id": employee_id,
            "employee_name": employee.employee_name,
            "year": year,
            "current_score": employee.current_score,
            "total_records": len(records),
            "total_deduction": total_deduction,
            "total_bonus": total_bonus,
            "net_change": total_deduction + total_bonus,
            "category_stats": category_stats,
            "cumulative_counts": cumulative_counts
        }

    def _trigger_monthly_reward_check(self, employee_id: int, year: int, month: int) -> None:
        """
        觸發月度獎勵重算

        P1 修正：處理回溯建檔與刪除/還原時的獎勵連動

        Args:
            employee_id: 員工 ID
            year: 年度
            month: 月份
        """
        # 延遲 import 避免 circular import
        from .monthly_reward_calculator import MonthlyRewardCalculatorService

        reward_service = MonthlyRewardCalculatorService(self.db)
        reward_service.calculate_employee_month(employee_id, year, month)

    def _update_employee_score(self, employee_id: int, points_change: float) -> None:
        """
        更新員工分數（增量更新）

        Args:
            employee_id: 員工 ID
            points_change: 分數變動
        """
        employee = self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        ).scalar_one_or_none()

        if employee:
            employee.current_score += points_change

    def _recalculate_employee_total_score(self, employee_id: int) -> float:
        """
        重新計算員工總分

        Args:
            employee_id: 員工 ID

        Returns:
            新的總分
        """
        employee = self.db.execute(
            select(Employee).where(Employee.id == employee_id)
        ).scalar_one_or_none()

        if not employee:
            raise ValueError(f"找不到員工 ID: {employee_id}")

        # 查詢所有未刪除的考核記錄
        total = self.db.execute(
            select(func.coalesce(func.sum(AssessmentRecord.final_points), 0)).where(
                and_(
                    AssessmentRecord.employee_id == employee_id,
                    AssessmentRecord.is_deleted == False
                )
            )
        ).scalar_one()

        # 總分 = 起始分數 80 + 所有 final_points 總和
        new_score = 80.0 + float(total)
        employee.current_score = new_score

        return new_score
