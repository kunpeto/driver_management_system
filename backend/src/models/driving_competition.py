"""
DrivingCompetition 駕駛競賽排名模型（季度制）
對應 tasks.md T104: 建立 DrivingCompetition 模型
對應 spec.md: DrivingCompetition (駕駛競賽排名)
對應 115年度當責駕駛時數激勵方案
"""

from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Enum, Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .google_oauth_token import Department


class DrivingCompetition(Base, TimestampMixin):
    """
    駕駛競賽排名模型（季度制）

    儲存每季每位員工的競賽排名結果，包含積分、排名、資格狀態、獎金等。

    Attributes:
        id: 主鍵
        employee_id: 員工 ID (FK -> employees.id)
        competition_year: 競賽年度
        competition_quarter: 競賽季度 (1-4, Q1=1-3月, Q2=4-6月, Q3=7-9月, Q4=10-12月)
        department: 部門 ('淡海', '安坑')
        total_driving_minutes: 季度累計駕駛分鐘數（一般出勤）
        holiday_work_bonus_minutes: R班加成分鐘數（R班額外時數）
        incident_count: 季度責任事件次數（S/R 類別）
        final_score: 最終積分 = (total + holiday_bonus) / (1 + incident_count)
        rank_in_department: 部門內排名
        is_qualified: 是否符合資格（累計≥300小時 且 季末在職）
        is_employed_on_last_day: 季度最後一日是否在職
        bonus_amount: 獎金金額（依排名：淡海5階/安坑3階）
        created_at: 建立時間
        updated_at: 更新時間

    Business Rules:
        - 評比週期：每季結算（Q1: 1-3月、Q2: 4-6月、Q3: 7-9月、Q4: 10-12月）
        - 計算時機：每季首日（1/1, 4/1, 7/1, 10/1）凌晨 3:00
        - 資格門檻：季度累計時數 ≥ 300小時（18000分鐘）且季末在職
        - 排名名額與獎金：
          - 淡海：前5名（3600/3000/2400/1800/1200 元）
          - 安坑：前3名（3600/3000/2400 元）
        - 積分公式：(total_driving_minutes + holiday_work_bonus_minutes) / (1 + incident_count)
        - 責任事件定義：S類別（行車運轉）+ R類別（故障排除）扣分項目
    """

    __tablename__ = "driving_competitions"

    # 淡海與安坑的獎金階層
    BONUS_TIERS = {
        "淡海": [3600, 3000, 2400, 1800, 1200],
        "安坑": [3600, 3000, 2400],
    }

    # 資格門檻（分鐘）= 300 小時
    QUALIFICATION_MINUTES = 300 * 60  # 18000 分鐘

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="員工 ID"
    )

    competition_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="競賽年度"
    )

    competition_quarter: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="競賽季度 (1-4)"
    )

    department: Mapped[str] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="部門：淡海、安坑"
    )

    total_driving_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="季度累計駕駛分鐘數（一般出勤）"
    )

    holiday_work_bonus_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="R班加成分鐘數（R班額外時數）"
    )

    incident_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="季度責任事件次數（S/R 類別）"
    )

    final_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="最終積分"
    )

    rank_in_department: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="部門內排名"
    )

    is_qualified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否符合資格（累計≥300小時 且 季末在職）"
    )

    is_employed_on_last_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="季度最後一日是否在職"
    )

    bonus_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="獎金金額"
    )

    # Relationships
    employee = relationship("Employee", backref="driving_competitions")

    __table_args__ = (
        UniqueConstraint(
            "employee_id", "competition_year", "competition_quarter",
            name="uq_driving_competition_employee_quarter"
        ),
        CheckConstraint(
            "competition_quarter >= 1 AND competition_quarter <= 4",
            name="ck_competition_quarter_range"
        ),
        Index(
            "idx_driving_competition_period",
            "competition_year", "competition_quarter", "department"
        ),
        Index(
            "idx_driving_competition_ranking",
            "competition_year", "competition_quarter", "department", "rank_in_department"
        ),
        {"comment": "駕駛競賽排名表（季度制）"}
    )

    def __repr__(self) -> str:
        return (
            f"<DrivingCompetition("
            f"employee_id={self.employee_id}, "
            f"year={self.competition_year}, "
            f"Q{self.competition_quarter}, "
            f"rank={self.rank_in_department}, "
            f"score={self.final_score:.2f})>"
        )

    @property
    def total_hours(self) -> float:
        """總駕駛小時數"""
        return self.total_driving_minutes / 60.0

    @property
    def effective_minutes(self) -> int:
        """有效分鐘數（含R班加成）"""
        return self.total_driving_minutes + self.holiday_work_bonus_minutes

    @property
    def effective_hours(self) -> float:
        """有效小時數（含R班加成）"""
        return self.effective_minutes / 60.0

    @property
    def quarter_label(self) -> str:
        """季度標籤（如 '2026 Q1'）"""
        return f"{self.competition_year} Q{self.competition_quarter}"

    @property
    def is_bonus_recipient(self) -> bool:
        """是否獲得獎金"""
        return self.bonus_amount > 0

    @classmethod
    def get_quarter_months(cls, quarter: int) -> tuple[int, int, int]:
        """取得季度包含的月份"""
        quarters = {
            1: (1, 2, 3),
            2: (4, 5, 6),
            3: (7, 8, 9),
            4: (10, 11, 12),
        }
        return quarters.get(quarter, (1, 2, 3))

    @classmethod
    def get_bonus_amount(cls, department: str, rank: int, is_qualified: bool) -> int:
        """
        根據部門和排名計算獎金金額

        Args:
            department: 部門名稱
            rank: 排名（從1開始）
            is_qualified: 是否符合資格

        Returns:
            獎金金額，不符合資格或超出名額返回0
        """
        if not is_qualified:
            return 0

        bonus_tiers = cls.BONUS_TIERS.get(department, [])
        if rank < 1 or rank > len(bonus_tiers):
            return 0

        return bonus_tiers[rank - 1]

    @classmethod
    def calculate_final_score(
        cls,
        total_minutes: int,
        holiday_bonus_minutes: int,
        incident_count: int
    ) -> float:
        """
        計算最終積分

        公式: (total_minutes + holiday_bonus_minutes) / (1 + incident_count)

        Args:
            total_minutes: 總駕駛分鐘數
            holiday_bonus_minutes: R班加成分鐘數
            incident_count: 責任事件次數

        Returns:
            最終積分
        """
        effective_minutes = total_minutes + holiday_bonus_minutes
        divisor = 1 + incident_count
        return effective_minutes / divisor

    @classmethod
    def check_qualification(cls, total_minutes: int, is_employed: bool) -> bool:
        """
        檢查是否符合資格

        Args:
            total_minutes: 季度累計分鐘數
            is_employed: 季末是否在職

        Returns:
            是否符合資格
        """
        return total_minutes >= cls.QUALIFICATION_MINUTES and is_employed
