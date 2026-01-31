"""
AssessmentNotice 考核通知模型
對應 tasks.md T134: 建立 AssessmentNotice 模型
對應 spec.md: User Story 8 - 考核加扣分通知單
"""

import enum
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .profile import Profile


class AssessmentType(str, enum.Enum):
    """考核類型"""

    PLUS = "加分"  # 加分
    MINUS = "扣分"  # 扣分


class AssessmentNotice(Base, TimestampMixin):
    """
    考核通知模型

    儲存考核加扣分通知單的詳細資訊，作為 Profile 的子表。

    注意：Profile 主表已有 assessment_item 和 assessment_score 欄位，
    本表的同名欄位用於儲存通知單特有的細節（可能與主表略有不同）。

    Attributes:
        id: 主鍵
        profile_id: 履歷 ID (FK)
        assessment_type: 考核類型（加分/扣分）
        assessment_item: 考核項目（通知單詳細項目）
        assessment_score: 考核分數（通知單記錄的分數）
        issue_date: 核發日期
        approver: 核准人
        remarks: 備註
        created_at: 建立時間
        updated_at: 更新時間

    Relationships:
        profile: 關聯的履歷主表
    """

    __tablename__ = "assessment_notices"

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

    # 考核資訊
    assessment_type: Mapped[str] = mapped_column(
        Enum(AssessmentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="考核類型：加分、扣分"
    )

    assessment_item: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="考核項目"
    )

    assessment_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="考核分數"
    )

    # 核發資訊
    issue_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="核發日期"
    )

    approver: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="核准人"
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="備註"
    )

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="assessment_notice"
    )

    __table_args__ = (
        {"comment": "考核通知表"}
    )

    def __repr__(self) -> str:
        return f"<AssessmentNotice(id={self.id}, type={self.assessment_type}, score={self.assessment_score})>"

    @property
    def is_plus(self) -> bool:
        """是否為加分"""
        return self.assessment_type == AssessmentType.PLUS.value

    @property
    def is_minus(self) -> bool:
        """是否為扣分"""
        return self.assessment_type == AssessmentType.MINUS.value

    @property
    def score_display(self) -> str:
        """分數顯示（帶正負號）"""
        if self.assessment_score is None:
            return "-"
        prefix = "+" if self.is_plus else ""
        return f"{prefix}{self.assessment_score}"

    @property
    def type_code(self) -> str:
        """類型代碼（用於條碼）"""
        return "AA" if self.is_plus else "AD"
