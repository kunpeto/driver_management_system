"""
MonthlyReward 月度獎勵記錄模型
對應 tasks.md T163: 建立 MonthlyReward 模型
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 月度獎勵記錄
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .employee import Employee


class MonthlyReward(Base):
    """
    月度獎勵記錄模型

    記錄每位員工每月的月度獎勵發放情況

    Attributes:
        id: 主鍵
        employee_id: 員工 ID (FK)
        year_month: 獎勵月份（格式：YYYY-MM）
        full_attendance: +M01 月度全勤（+3 分）
        driving_zero_violation: +M02 月度行車零違規（+1 分）
        all_zero_violation: +M03 月度全項目零違規（+2 分）
        total_points: 當月獎勵合計分數
        calculated_at: 計算時間

    Relationships:
        employee: 關聯的員工

    Note:
        - +M02: 當月 R 類、S 類無任何扣分
        - +M03: 當月所有類別（D/W/O/S/R）皆無扣分
        - +M02 和 +M03 可疊加
    """

    __tablename__ = "monthly_rewards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 關聯
    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        comment="員工 ID"
    )

    # 獎勵月份
    year_month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="獎勵月份（格式：YYYY-MM）"
    )

    # 獎勵項目
    full_attendance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="+M01 月度全勤（+3 分）"
    )

    driving_zero_violation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="+M02 月度行車零違規（+1 分），條件：當月 R、S 類無任何扣分"
    )

    all_zero_violation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="+M03 月度全項目零違規（+2 分），條件：當月所有類別皆無扣分"
    )

    # 分數統計
    total_points: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="當月獎勵合計分數"
    )

    # 計算時間
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="計算時間（通常為下個月 1 日凌晨）"
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="monthly_rewards"
    )

    __table_args__ = (
        # 複合唯一約束：同一員工同一月份只能有一筆
        UniqueConstraint(
            'employee_id', 'year_month',
            name='uq_monthly_reward_employee_year_month'
        ),
        # 索引：月份查詢
        Index('ix_monthly_rewards_year_month', 'year_month'),
        {"comment": "月度獎勵記錄表"}
    )

    def __repr__(self) -> str:
        return (
            f"<MonthlyReward("
            f"employee_id={self.employee_id}, "
            f"year_month={self.year_month!r}, "
            f"total_points={self.total_points}"
            f")>"
        )

    @property
    def year(self) -> int:
        """年度"""
        return int(self.year_month.split('-')[0])

    @property
    def month(self) -> int:
        """月份"""
        return int(self.year_month.split('-')[1])

    def calculate_total_points(self) -> float:
        """
        計算總獎勵分數

        Returns:
            總獎勵分數
        """
        total = 0.0
        if self.full_attendance:
            total += 3.0  # +M01
        if self.driving_zero_violation:
            total += 1.0  # +M02
        if self.all_zero_violation:
            total += 2.0  # +M03
        self.total_points = total
        return total

    @property
    def reward_items(self) -> list[str]:
        """獲得的獎勵項目列表"""
        items = []
        if self.full_attendance:
            items.append("+M01 月度全勤")
        if self.driving_zero_violation:
            items.append("+M02 月度行車零違規")
        if self.all_zero_violation:
            items.append("+M03 月度全項目零違規")
        return items

    @property
    def has_any_reward(self) -> bool:
        """是否有任何獎勵"""
        return self.full_attendance or self.driving_zero_violation or self.all_zero_violation
