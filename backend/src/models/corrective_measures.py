"""
CorrectiveMeasures 矯正措施模型
對應 tasks.md T133: 建立 CorrectiveMeasures 模型
對應 spec.md: User Story 8 - 矯正措施記錄
"""

import enum
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .profile import Profile


class CompletionStatus(str, enum.Enum):
    """完成狀態"""

    PENDING = "pending"  # 待處理
    IN_PROGRESS = "in_progress"  # 進行中
    COMPLETED = "completed"  # 已完成


class CorrectiveMeasures(Base, TimestampMixin):
    """
    矯正措施模型

    儲存矯正措施的詳細資訊，作為 Profile 的子表。

    Attributes:
        id: 主鍵
        profile_id: 履歷 ID (FK)
        event_summary: 事件概述
        corrective_actions: 矯正行動
        responsible_person: 負責人
        completion_deadline: 完成期限
        completion_status: 完成狀態
        completion_date: 實際完成日期
        completion_notes: 完成備註
        created_at: 建立時間
        updated_at: 更新時間

    Relationships:
        profile: 關聯的履歷主表
    """

    __tablename__ = "corrective_measures"

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

    # 事件與矯正資訊
    event_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="事件概述"
    )

    corrective_actions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="矯正行動"
    )

    responsible_person: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="負責人"
    )

    # 完成狀態
    completion_deadline: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="完成期限"
    )

    completion_status: Mapped[str] = mapped_column(
        Enum(CompletionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CompletionStatus.PENDING.value,
        index=True,
        comment="完成狀態"
    )

    completion_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="實際完成日期"
    )

    completion_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="完成備註"
    )

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="corrective_measures"
    )

    __table_args__ = (
        {"comment": "矯正措施表"}
    )

    def __repr__(self) -> str:
        return f"<CorrectiveMeasures(id={self.id}, profile_id={self.profile_id}, status={self.completion_status})>"

    @property
    def is_overdue(self) -> bool:
        """是否逾期"""
        if not self.completion_deadline:
            return False
        if self.completion_status == CompletionStatus.COMPLETED.value:
            return False
        return date.today() > self.completion_deadline

    @property
    def days_until_deadline(self) -> Optional[int]:
        """距離截止日期的天數（負數表示已逾期）"""
        if not self.completion_deadline:
            return None
        return (self.completion_deadline - date.today()).days

    def mark_completed(self, notes: Optional[str] = None) -> None:
        """標記為已完成"""
        self.completion_status = CompletionStatus.COMPLETED.value
        self.completion_date = date.today()
        if notes:
            self.completion_notes = notes
