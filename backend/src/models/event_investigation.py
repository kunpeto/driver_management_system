"""
EventInvestigation 事件調查模型
對應 tasks.md T131: 建立 EventInvestigation 模型
對應 spec.md: User Story 8 - 事件調查記錄

Gemini Review 2026-01-30 優化：
- 新增 has_responsibility, responsibility_ratio, category 欄位
- 支援 Phase 9 駕駛競賽責任事件統計
"""

import enum
from datetime import date, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .profile import Profile


class EventCategory(str, enum.Enum):
    """
    事件類別（支援 Phase 9 駕駛競賽統計）

    S: 安全類 (Safety)
    R: 服務類 (Service/Reliability)
    W: 工作類 (Work)
    O: 營運類 (Operation)
    D: 紀律類 (Discipline)
    """

    S = "S"  # 安全類
    R = "R"  # 服務類
    W = "W"  # 工作類
    O = "O"  # 營運類
    D = "D"  # 紀律類


class EventInvestigation(Base, TimestampMixin):
    """
    事件調查模型

    儲存事件調查的詳細資訊，作為 Profile 的子表。

    Attributes:
        id: 主鍵
        profile_id: 履歷 ID (FK)
        incident_time: 事件時間
        incident_location: 事件地點（詳細位置）
        witnesses: 目擊者
        cause_analysis: 原因分析
        process_description: 過程描述（事件人員自述）
        improvement_suggestions: 改善建議
        investigator: 調查人員
        investigation_date: 調查日期
        has_responsibility: 是否歸責（Phase 9 統計）
        responsibility_ratio: 責任比例 0-100（Phase 9 統計）
        category: 事件類別 S/R/W/O/D（Phase 9 統計）
        created_at: 建立時間
        updated_at: 更新時間

    Relationships:
        profile: 關聯的履歷主表
    """

    __tablename__ = "event_investigations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 履歷關聯
    profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="履歷 ID"
    )

    # 事件詳情
    incident_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="事件時間"
    )

    incident_location: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="事件地點（詳細位置）"
    )

    witnesses: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="目擊者"
    )

    cause_analysis: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="原因分析"
    )

    process_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="過程描述（事件人員自述）"
    )

    improvement_suggestions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="改善建議"
    )

    # 調查資訊
    investigator: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="調查人員"
    )

    investigation_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="調查日期"
    )

    # Phase 9 駕駛競賽統計欄位（Gemini Review 新增）
    has_responsibility: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        default=None,
        index=True,
        comment="是否歸責（Phase 9 統計）"
    )

    responsibility_ratio: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="責任比例 0-100%（Phase 9 統計）"
    )

    category: Mapped[Optional[str]] = mapped_column(
        Enum(EventCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        index=True,
        comment="事件類別 S/R/W/O/D（Phase 9 統計）"
    )

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="event_investigation"
    )

    __table_args__ = (
        {"comment": "事件調查表"}
    )

    def __repr__(self) -> str:
        return f"<EventInvestigation(id={self.id}, profile_id={self.profile_id})>"

    @property
    def has_full_responsibility(self) -> bool:
        """是否全責"""
        return self.responsibility_ratio == 100 if self.responsibility_ratio else False

    @property
    def responsibility_display(self) -> str:
        """責任顯示文字"""
        if self.has_responsibility is None:
            return "未判定"
        if not self.has_responsibility:
            return "無責任"
        ratio = self.responsibility_ratio or 0
        return f"有責任 ({ratio}%)"
