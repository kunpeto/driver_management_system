"""
AssessmentStandard 考核標準模型
對應 tasks.md T159: 建立 AssessmentStandard 模型
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 考核標準主檔
"""

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .assessment_record import AssessmentRecord


class AssessmentCategory(str, enum.Enum):
    """考核類別（扣分類）"""
    D = "D"  # 服勤類（Daily Service）
    W = "W"  # 酒測類（Wine Test）
    O = "O"  # 其他類（Others）
    S = "S"  # 行車類（Safety）
    R = "R"  # 責任類（Responsibility）


class BonusCategory(str, enum.Enum):
    """考核類別（加分類）"""
    M = "+M"  # 月度獎勵（Monthly）
    A = "+A"  # 出勤類（Attendance）
    B = "+B"  # 表揚類（Bonus）
    C = "+C"  # 合理化建議類（Contribution）
    PR = "+R"  # 特殊貢獻類（Plus Recognition）


class CalculationCycle(str, enum.Enum):
    """計算週期"""
    YEARLY = "yearly"  # 年度累計
    MONTHLY = "monthly"  # 月度發放


class AssessmentStandard(Base, TimestampMixin):
    """
    考核標準主檔

    儲存所有考核項目的基本資料（61 項：41 扣分 + 20 加分標準）

    Attributes:
        id: 主鍵
        code: 代碼（唯一，如 D01, W02, +M01）
        category: 類別（D, W, O, S, R, +M, +A, +B, +C, +R）
        name: 項目名稱
        base_points: 基本分數（負數為扣分，正數為加分）
        has_cumulative: 是否適用累計加重
        calculation_cycle: 計算週期（yearly/monthly）
        description: 詳細說明
        is_active: 是否啟用

    Relationships:
        records: 考核記錄
    """

    __tablename__ = "assessment_standards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        comment="考核代碼（如 D01, W02, +M01）"
    )

    category: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="類別（D, W, O, S, R, +M, +A, +B, +C, +R）"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="項目名稱"
    )

    base_points: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="基本分數（負數扣分、正數加分）"
    )

    has_cumulative: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否適用累計加重"
    )

    calculation_cycle: Mapped[str] = mapped_column(
        Enum(CalculationCycle, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CalculationCycle.YEARLY.value,
        comment="計算週期（yearly: 年度累計, monthly: 月度發放）"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="詳細說明"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否啟用"
    )

    # Relationships
    records: Mapped[list["AssessmentRecord"]] = relationship(
        "AssessmentRecord",
        back_populates="standard",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_assessment_standards_category_active", "category", "is_active"),
        {"comment": "考核標準主檔（61 項）"}
    )

    def __repr__(self) -> str:
        return f"<AssessmentStandard(code={self.code!r}, name={self.name!r})>"

    @property
    def is_deduction(self) -> bool:
        """是否為扣分項目"""
        return self.base_points < 0

    @property
    def is_bonus(self) -> bool:
        """是否為加分項目"""
        return self.base_points > 0

    @property
    def is_r_type_human_fault(self) -> bool:
        """是否為 R02-R05 人為疏失項目（需責任判定）"""
        return self.code in {'R02', 'R03', 'R04', 'R05'}
