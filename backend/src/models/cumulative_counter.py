"""
CumulativeCounter 累計次數計數器模型
對應 tasks.md T162: 建立 CumulativeCounter 模型
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 累計次數計數器（依類別獨立累計）
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .employee import Employee


# R 類合併累計群組（P1 修正：明確定義，避免未來新增 R01/R06 時誤判）
R_CUMULATIVE_GROUP = {'R02', 'R03', 'R04', 'R05'}


def get_cumulative_category(standard_code: str, category: str) -> str:
    """
    取得累計計算的類別（處理 R 類特殊規則）

    規則：
    - R02/R03/R04/R05: 合併計算為 'R' 類別
    - 其他所有項目: 依原始類別獨立計算

    Args:
        standard_code: 考核標準代碼（如 D01, R03, +M01）
        category: 原始類別（如 D, R, +M）

    Returns:
        累計計算的類別
    """
    if standard_code in R_CUMULATIVE_GROUP:
        return 'R'  # R02-R05 合併計算
    else:
        return category  # D, W, O, S 及其他 R 類項目各自獨立


class CumulativeCounter(Base):
    """
    累計次數計數器模型

    記錄每位員工每年度各類別的累計次數

    Attributes:
        id: 主鍵
        employee_id: 員工 ID (FK)
        year: 年度
        category: 類別（D, W, O, S, R）
        count: 累計次數
        last_updated: 最後更新時間

    Relationships:
        employee: 關聯的員工

    Note:
        R 類特殊規則：R02/R03/R04/R05 合併計算，使用 get_cumulative_category() 函數判定
    """

    __tablename__ = "cumulative_counters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 關聯
    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        comment="員工 ID"
    )

    # 累計範圍
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="年度（如 2026）"
    )

    category: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="類別（D, W, O, S, R）"
    )

    # 累計數據
    count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="累計次數"
    )

    # 時間戳
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="最後更新時間"
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="cumulative_counters"
    )

    __table_args__ = (
        # 複合唯一約束：同一員工同一年度同一類別只能有一筆
        UniqueConstraint(
            'employee_id', 'year', 'category',
            name='uq_cumulative_employee_year_category'
        ),
        # 複合索引：員工年度查詢
        Index('ix_cumulative_employee_year', 'employee_id', 'year'),
        {"comment": "累計次數計數器表"}
    )

    def __repr__(self) -> str:
        return (
            f"<CumulativeCounter("
            f"employee_id={self.employee_id}, "
            f"year={self.year}, "
            f"category={self.category!r}, "
            f"count={self.count}"
            f")>"
        )

    def increment(self) -> int:
        """
        遞增累計次數

        Returns:
            遞增後的累計次數
        """
        self.count += 1
        return self.count

    def reset(self) -> None:
        """重置累計次數為 0"""
        self.count = 0

    @property
    def cumulative_multiplier(self) -> float:
        """
        計算累計倍率

        公式：累計倍率 = 1 + 0.5 × (count - 1)

        Returns:
            累計倍率（最小為 1.0）
        """
        if self.count <= 0:
            return 1.0
        return 1.0 + 0.5 * (self.count - 1)

    @classmethod
    def get_next_cumulative_multiplier(cls, current_count: int) -> float:
        """
        計算下一次違規的累計倍率

        Args:
            current_count: 當前累計次數

        Returns:
            下一次的累計倍率
        """
        next_count = current_count + 1
        return 1.0 + 0.5 * (next_count - 1)
