"""
Profile 履歷主表模型
對應 tasks.md T130: 建立 Profile 模型
對應 spec.md: User Story 8 - 司機員事件履歷管理系統

Gemini Review 2026-01-30 優化：
- 新增 event_time, event_title, data_source 欄位
- 新增 assessment_item, assessment_score 欄位（所有類型共用）
"""

import enum
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .google_oauth_token import Department

if TYPE_CHECKING:
    from .assessment_notice import AssessmentNotice
    from .assessment_record import AssessmentRecord
    from .corrective_measures import CorrectiveMeasures
    from .employee import Employee
    from .event_investigation import EventInvestigation
    from .personnel_interview import PersonnelInterview


class ProfileType(str, enum.Enum):
    """履歷類型"""

    BASIC = "basic"  # 基本履歷
    EVENT_INVESTIGATION = "event_investigation"  # 事件調查
    PERSONNEL_INTERVIEW = "personnel_interview"  # 人員訪談
    CORRECTIVE_MEASURES = "corrective_measures"  # 矯正措施
    ASSESSMENT_NOTICE = "assessment_notice"  # 考核通知


class ConversionStatus(str, enum.Enum):
    """轉換狀態"""

    PENDING = "pending"  # 待處理
    CONVERTED = "converted"  # 已轉換（已產生文件）
    COMPLETED = "completed"  # 已完成（已上傳 PDF）


class Profile(Base, TimestampMixin):
    """
    履歷主表模型

    儲存司機員事件履歷的基本資訊，作為所有履歷類型的主表。

    Attributes:
        id: 主鍵
        employee_id: 員工 ID (FK)
        profile_type: 履歷類型
        event_date: 事件日期
        event_time: 事件時間（Gemini Review 新增）
        event_location: 事件地點
        train_number: 列車車號
        event_title: 事件標題（Gemini Review 新增）
        event_description: 事件描述
        data_source: 資料來源/查核來源（Gemini Review 新增）
        assessment_item: 考核項目（Gemini Review 新增，所有類型共用）
        assessment_score: 考核分數（Gemini Review 新增，所有類型共用）
        conversion_status: 轉換狀態
        file_path: 檔案路徑
        gdrive_link: Google Drive 連結
        department: 部門
        document_version: 文件版本號（用於條碼）
        created_at: 建立時間
        updated_at: 更新時間

    Relationships:
        employee: 關聯的員工
        event_investigation: 事件調查子表
        personnel_interview: 人員訪談子表
        corrective_measures: 矯正措施子表
        assessment_notice: 考核通知子表
    """

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 員工關聯
    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="員工 ID"
    )

    # 履歷類型
    profile_type: Mapped[str] = mapped_column(
        Enum(ProfileType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProfileType.BASIC.value,
        index=True,
        comment="履歷類型"
    )

    # 事件基本資訊
    event_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="事件日期"
    )

    event_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="事件時間（Gemini Review 新增）"
    )

    event_location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="事件地點"
    )

    train_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="列車車號"
    )

    event_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="事件標題（Gemini Review 新增）"
    )

    event_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="事件描述"
    )

    # 查核/考核資訊（Gemini Review 新增，所有類型共用）
    data_source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="資料來源/查核來源（Gemini Review 新增）"
    )

    assessment_item: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="考核項目（Gemini Review 新增，所有類型共用）"
    )

    assessment_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="考核分數（Gemini Review 新增，所有類型共用）"
    )

    # 狀態與檔案
    conversion_status: Mapped[str] = mapped_column(
        Enum(ConversionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ConversionStatus.PENDING.value,
        index=True,
        comment="轉換狀態"
    )

    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="檔案路徑"
    )

    gdrive_link: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Google Drive 連結"
    )

    # 部門
    department: Mapped[str] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="部門"
    )

    # 文件版本號（用於條碼生成）
    document_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="文件版本號（每次生成文件時遞增）"
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="profiles",
        lazy="selectin"
    )

    event_investigation: Mapped[Optional["EventInvestigation"]] = relationship(
        "EventInvestigation",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )

    personnel_interview: Mapped[Optional["PersonnelInterview"]] = relationship(
        "PersonnelInterview",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )

    corrective_measures: Mapped[Optional["CorrectiveMeasures"]] = relationship(
        "CorrectiveMeasures",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )

    assessment_notice: Mapped[Optional["AssessmentNotice"]] = relationship(
        "AssessmentNotice",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Phase 12: 考核記錄關聯（一對一）
    assessment_record: Mapped[Optional["AssessmentRecord"]] = relationship(
        "AssessmentRecord",
        back_populates="profile",
        uselist=False
    )

    __table_args__ = (
        # 複合索引：未結案查詢優化（Gemini Review 建議）
        Index("ix_profiles_pending", "conversion_status", "department"),
        # 複合索引：日期範圍查詢
        Index("ix_profiles_date_dept", "event_date", "department"),
        {"comment": "履歷主表"}
    )

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, type={self.profile_type}, status={self.conversion_status})>"

    @property
    def is_basic(self) -> bool:
        """是否為基本履歷"""
        return self.profile_type == ProfileType.BASIC.value

    @property
    def can_convert(self) -> bool:
        """是否可轉換類型（僅 basic 且非 completed 可轉換）"""
        return (
            self.profile_type == ProfileType.BASIC.value
            and self.conversion_status != ConversionStatus.COMPLETED.value
        )

    @property
    def is_pending(self) -> bool:
        """是否為未結案（已轉換但未上傳 PDF）"""
        return (
            self.conversion_status == ConversionStatus.CONVERTED.value
            and self.gdrive_link is None
        )

    def increment_version(self) -> int:
        """遞增文件版本號並返回新版本"""
        self.document_version += 1
        return self.document_version
