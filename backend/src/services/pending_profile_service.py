"""
未結案查詢服務
對應 tasks.md T186: 實作未結案查詢服務

功能：
- 查詢 conversion_status = 'converted' AND gdrive_link IS NULL 的履歷
- 按類型分組統計
- 最舊未結案日期計算
- 本月完成率計算
"""

from typing import Optional
from datetime import date
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.profile import Profile, ConversionStatus
from src.utils.logger import logger


@dataclass
class PendingStatistics:
    """未結案統計資料"""
    total: int
    by_type: dict[str, int]
    oldest_pending_date: Optional[date]
    this_month_completed: int
    this_month_total: int
    completion_rate: float  # 0.0 ~ 1.0


class PendingProfileService:
    """
    未結案查詢服務

    提供未結案履歷的查詢、統計功能。
    未結案定義：conversion_status = 'converted' AND gdrive_link IS NULL
    """

    def __init__(self, db: Session):
        self.db = db

    def get_pending_count(self, department: Optional[str] = None) -> int:
        """
        取得未結案總數

        Args:
            department: 部門篩選

        Returns:
            未結案總數
        """
        query = self.db.query(func.count(Profile.id)).filter(
            Profile.conversion_status == ConversionStatus.CONVERTED.value,
            Profile.gdrive_link.is_(None)
        )

        if department:
            query = query.filter(Profile.department == department)

        return query.scalar() or 0

    def get_pending_by_type(
        self,
        department: Optional[str] = None
    ) -> dict[str, int]:
        """
        按類型統計未結案數量

        Args:
            department: 部門篩選

        Returns:
            各類型未結案數量
        """
        query = self.db.query(
            Profile.profile_type,
            func.count(Profile.id).label("count")
        ).filter(
            Profile.conversion_status == ConversionStatus.CONVERTED.value,
            Profile.gdrive_link.is_(None)
        )

        if department:
            query = query.filter(Profile.department == department)

        results = query.group_by(Profile.profile_type).all()
        return {r.profile_type: r.count for r in results}

    def get_oldest_pending_date(
        self,
        department: Optional[str] = None
    ) -> Optional[date]:
        """
        取得最舊未結案日期

        Args:
            department: 部門篩選

        Returns:
            最舊未結案的事件日期，無未結案則返回 None
        """
        query = self.db.query(func.min(Profile.event_date)).filter(
            Profile.conversion_status == ConversionStatus.CONVERTED.value,
            Profile.gdrive_link.is_(None)
        )

        if department:
            query = query.filter(Profile.department == department)

        result = query.scalar()
        return result

    def get_this_month_stats(
        self,
        department: Optional[str] = None
    ) -> tuple[int, int]:
        """
        取得本月完成數和總數（Gemini Review P3：合併查詢優化）

        Args:
            department: 部門篩選

        Returns:
            (本月已完成數量, 本月轉換總數)
        """
        from sqlalchemy import case

        today = date.today()
        first_day = date(today.year, today.month, 1)

        # 使用單次查詢同時計算已完成和未結案數量
        query = self.db.query(
            # 本月已完成數量
            func.count(case(
                (Profile.conversion_status == ConversionStatus.COMPLETED.value, Profile.id)
            )).label("completed"),
            # 本月未結案數量
            func.count(case(
                ((Profile.conversion_status == ConversionStatus.CONVERTED.value) &
                 (Profile.gdrive_link.is_(None)), Profile.id)
            )).label("pending")
        ).filter(
            Profile.updated_at >= first_day
        )

        if department:
            query = query.filter(Profile.department == department)

        result = query.first()
        completed = result.completed or 0
        pending = result.pending or 0

        return completed, completed + pending

    def get_full_statistics(
        self,
        department: Optional[str] = None
    ) -> PendingStatistics:
        """
        取得完整的未結案統計

        Args:
            department: 部門篩選

        Returns:
            PendingStatistics: 完整統計資料
        """
        try:
            by_type = self.get_pending_by_type(department)
            total = sum(by_type.values())
            oldest_date = self.get_oldest_pending_date(department)

            # Gemini Review P3：使用合併查詢優化
            this_month_completed, this_month_total = self.get_this_month_stats(department)

            # 計算完成率（避免除以零）
            completion_rate = 0.0
            if this_month_total > 0:
                completion_rate = this_month_completed / this_month_total

            logger.debug(
                "未結案統計",
                department=department,
                total=total,
                oldest_pending_date=oldest_date,
                this_month_completed=this_month_completed,
                this_month_total=this_month_total,
                completion_rate=completion_rate
            )

            return PendingStatistics(
                total=total,
                by_type=by_type,
                oldest_pending_date=oldest_date,
                this_month_completed=this_month_completed,
                this_month_total=this_month_total,
                completion_rate=round(completion_rate, 4)
            )
        except Exception as e:
            # 資料庫欄位不匹配或其他錯誤時，返回空統計
            logger.warning(f"取得未結案統計失敗: {e}")
            return PendingStatistics(
                total=0,
                by_type={},
                oldest_pending_date=None,
                this_month_completed=0,
                this_month_total=0,
                completion_rate=0.0
            )


# 單例
_service_instance: Optional[PendingProfileService] = None


def get_pending_profile_service(db: Session) -> PendingProfileService:
    """取得未結案查詢服務實例"""
    return PendingProfileService(db)
