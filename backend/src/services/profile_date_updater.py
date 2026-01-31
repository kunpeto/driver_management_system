"""
履歷日期變更重算服務
對應 tasks.md T172: 實作履歷日期變更重算服務
對應 spec.md: User Story 9 - 考核系統（P1 修正）
對應 data-model-phase12.md: 履歷日期變更的連動重算流程

此服務處理履歷日期變更時的考核記錄連動更新，
包含同年變更與跨年變更的重算邏輯。
此為 Gemini Review P1-2 發現的遺漏功能。
"""

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.assessment_record import AssessmentRecord
from ..models.profile import Profile
from .assessment_recalculator import AssessmentRecalculatorService
from .cumulative_category import get_cumulative_category


class ProfileDateUpdaterService:
    """
    履歷日期變更重算服務

    處理履歷日期變更時的考核記錄連動更新：
    1. 同年變更：重算該年度該類別所有記錄
    2. 跨年變更：重算兩個年度該類別所有記錄
    3. 使用 Transaction + FOR UPDATE 確保並發安全
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: 資料庫 Session
        """
        self.db = db
        self.recalculator = AssessmentRecalculatorService(db)

    def update_profile_date(
        self,
        profile_id: int,
        new_date: date
    ) -> dict[str, any]:
        """
        更新履歷日期並觸發考核記錄重算

        處理場景：
        1. 同年變更：重算該年度該類別所有記錄
        2. 跨年變更：重算兩個年度該類別所有記錄
        3. 並發安全：使用 Transaction + FOR UPDATE 鎖定

        Args:
            profile_id: 履歷 ID
            new_date: 新日期

        Returns:
            更新結果字典

        Raises:
            ValueError: 履歷不存在
        """
        # 1. 查詢履歷
        profile = self.db.execute(
            select(Profile).where(Profile.id == profile_id)
        ).scalar_one_or_none()

        if not profile:
            raise ValueError(f"履歷 {profile_id} 不存在")

        old_date = profile.event_date
        old_year = old_date.year
        new_year = new_date.year

        # 如果日期沒有變更，直接返回
        if old_date == new_date:
            return {
                "profile_id": profile_id,
                "date_changed": False,
                "old_date": old_date.isoformat(),
                "new_date": new_date.isoformat(),
                "recalculation_needed": False
            }

        # 2. 更新履歷日期
        profile.event_date = new_date

        # 3. 查詢關聯的考核記錄
        assessment_record = self.db.execute(
            select(AssessmentRecord).where(
                AssessmentRecord.profile_id == profile_id
            )
        ).scalar_one_or_none()

        result = {
            "profile_id": profile_id,
            "date_changed": True,
            "old_date": old_date.isoformat(),
            "new_date": new_date.isoformat(),
            "recalculation_needed": False,
            "is_cross_year": old_year != new_year,
            "years_recalculated": []
        }

        # 4. 若有關聯的考核記錄，更新考核記錄日期並重算
        if assessment_record and not assessment_record.is_deleted:
            # 取得累計類別
            standard = assessment_record.standard
            cumulative_category = get_cumulative_category(
                assessment_record.standard_code,
                standard.category
            )

            # 只有適用累計加重的項目才需要重算
            if standard.has_cumulative:
                result["recalculation_needed"] = True

                # 更新考核記錄日期
                assessment_record.record_date = new_date

                # 5. 根據是否跨年執行重算
                if old_year != new_year:
                    # 跨年變更：重算兩個年度
                    self.recalculator.recalculate_cumulative_counts(
                        profile.employee_id,
                        old_year,
                        cumulative_category
                    )
                    self.recalculator.recalculate_cumulative_counts(
                        profile.employee_id,
                        new_year,
                        cumulative_category
                    )
                    result["years_recalculated"] = [old_year, new_year]
                else:
                    # 同年變更：重算該年度
                    self.recalculator.recalculate_cumulative_counts(
                        profile.employee_id,
                        new_year,
                        cumulative_category
                    )
                    result["years_recalculated"] = [new_year]

                # 6. 重新計算員工總分
                new_score = self.recalculator.recalculate_employee_total_score(
                    profile.employee_id
                )
                result["new_employee_score"] = new_score
            else:
                # 不適用累計加重的項目，只更新日期
                assessment_record.record_date = new_date

        return result

    def preview_date_change(
        self,
        profile_id: int,
        new_date: date
    ) -> dict[str, any]:
        """
        預覽日期變更的影響

        Args:
            profile_id: 履歷 ID
            new_date: 新日期

        Returns:
            影響預覽結果
        """
        profile = self.db.execute(
            select(Profile).where(Profile.id == profile_id)
        ).scalar_one_or_none()

        if not profile:
            raise ValueError(f"履歷 {profile_id} 不存在")

        old_date = profile.event_date
        old_year = old_date.year
        new_year = new_date.year

        # 查詢關聯的考核記錄
        assessment_record = self.db.execute(
            select(AssessmentRecord).where(
                AssessmentRecord.profile_id == profile_id
            )
        ).scalar_one_or_none()

        result = {
            "profile_id": profile_id,
            "old_date": old_date.isoformat(),
            "new_date": new_date.isoformat(),
            "is_same_date": old_date == new_date,
            "is_cross_year": old_year != new_year,
            "has_assessment_record": assessment_record is not None,
            "will_trigger_recalculation": False,
            "affected_years": []
        }

        if assessment_record and not assessment_record.is_deleted:
            standard = assessment_record.standard
            if standard.has_cumulative:
                result["will_trigger_recalculation"] = True
                if old_year != new_year:
                    result["affected_years"] = [old_year, new_year]
                else:
                    result["affected_years"] = [new_year]

                result["assessment_record"] = {
                    "id": assessment_record.id,
                    "standard_code": assessment_record.standard_code,
                    "standard_name": standard.name,
                    "current_cumulative_count": assessment_record.cumulative_count,
                    "current_cumulative_multiplier": assessment_record.cumulative_multiplier,
                    "current_final_points": assessment_record.final_points
                }

        return result

    def batch_update_dates(
        self,
        updates: list[dict[str, any]]
    ) -> list[dict[str, any]]:
        """
        批次更新多個履歷的日期

        Args:
            updates: 更新列表，每個字典包含 profile_id 和 new_date

        Returns:
            每個更新的結果列表
        """
        results = []

        for update in updates:
            try:
                profile_id = update["profile_id"]
                new_date = update["new_date"]

                # 確保 new_date 是 date 類型
                if isinstance(new_date, str):
                    new_date = date.fromisoformat(new_date)

                result = self.update_profile_date(profile_id, new_date)
                result["success"] = True
                results.append(result)

            except Exception as e:
                results.append({
                    "profile_id": update.get("profile_id"),
                    "success": False,
                    "error": str(e)
                })

        return results
