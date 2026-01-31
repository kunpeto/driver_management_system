"""
RouteStandardTime 勤務標準時間模型
對應 tasks.md T102: 建立 RouteStandardTime 模型
對應 spec.md: RouteStandardTime (勤務標準時間)
"""

from typing import Optional

from sqlalchemy import Boolean, Enum, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin
from .google_oauth_token import Department


class RouteStandardTime(Base, TimestampMixin):
    """
    勤務標準時間模型

    儲存各部門勤務項目的標準分鐘數，用於計算駕駛時數。
    每個部門的勤務設定獨立，不互相影響。

    Attributes:
        id: 主鍵
        department: 部門 ('淡海', '安坑')
        route_code: 勤務代碼（如 '淡安-全', '0905G'）
        route_name: 勤務名稱（如 '淡水-安坑全程', '早班 09:05 出發'）
        standard_minutes: 標準分鐘數
        is_active: 是否啟用（軟刪除用）
        created_at: 建立時間
        updated_at: 更新時間

    Business Rules:
        - 變更僅影響「變更日期之後」的駕駛時數計算，歷史資料不重新計算
        - 有關聯記錄的勤務標準時間改為「軟刪除」（is_active = false），不允許實體刪除
        - 部門 + 勤務代碼需唯一
    """

    __tablename__ = "route_standard_times"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    department: Mapped[str] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="部門：淡海、安坑"
    )

    route_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="勤務代碼（如 '淡安-全', '0905G'）"
    )

    route_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="勤務名稱（如 '淡水-安坑全程'）"
    )

    standard_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="標準分鐘數"
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="說明備註"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否啟用（軟刪除用）"
    )

    __table_args__ = (
        UniqueConstraint(
            "department", "route_code",
            name="uq_route_standard_time_dept_code"
        ),
        Index("idx_route_standard_time_dept_active", "department", "is_active"),
        {"comment": "勤務標準時間表"}
    )

    def __repr__(self) -> str:
        return f"<RouteStandardTime(dept={self.department!r}, code={self.route_code!r}, minutes={self.standard_minutes})>"

    @property
    def hours(self) -> float:
        """轉換為小時"""
        return self.standard_minutes / 60.0

    @property
    def display_time(self) -> str:
        """顯示格式（如 '8:00' 表示 8 小時 0 分）"""
        hours = self.standard_minutes // 60
        minutes = self.standard_minutes % 60
        return f"{hours}:{minutes:02d}"
