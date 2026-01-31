"""
AssessmentRecord 考核記錄模型
對應 tasks.md T160: 建立 AssessmentRecord 模型
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 考核記錄
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .assessment_standard import AssessmentStandard
    from .employee import Employee
    from .fault_responsibility import FaultResponsibilityAssessment
    from .profile import Profile


class AssessmentRecord(Base, TimestampMixin):
    """
    考核記錄模型

    儲存每筆考核扣分/加分記錄，包含累計倍率與最終分數

    Attributes:
        id: 主鍵
        employee_id: 員工 ID (FK)
        standard_code: 考核標準代碼 (FK)
        profile_id: 履歷 ID (FK, nullable)
        record_date: 事件發生日期
        description: 事件描述
        base_points: 基本分數（從標準複製）
        responsibility_coefficient: 責任係數（R02-R05 專用）
        actual_points: 實際扣分 = base_points × responsibility_coefficient
        cumulative_count: 該類別年度累計次數
        cumulative_multiplier: 累計倍率 = 1 + 0.5 × (count - 1)
        final_points: 最終分數 = actual_points × cumulative_multiplier
        is_deleted: 軟刪除標記
        deleted_at: 刪除時間

    Relationships:
        employee: 關聯的員工
        standard: 關聯的考核標準
        profile: 關聯的履歷（若透過履歷建立）
        fault_responsibility: 責任判定詳情（R02-R05 專用）
    """

    __tablename__ = "assessment_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 關聯
    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="員工 ID"
    )

    standard_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("assessment_standards.code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="考核標準代碼"
    )

    profile_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="關聯履歷 ID（若透過履歷建立）"
    )

    # 事件資料
    record_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="事件發生日期"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="事件描述"
    )

    # 分數計算
    base_points: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="基本分數（從考核標準複製）"
    )

    responsibility_coefficient: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=1.0,
        comment="責任係數（R02-R05：1.0/0.7/0.3，其他為 1.0）"
    )

    actual_points: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="實際扣分 = base_points × responsibility_coefficient"
    )

    cumulative_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="該類別年度累計次數（第 N 次）"
    )

    cumulative_multiplier: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        comment="累計倍率 = 1 + 0.5 × (cumulative_count - 1)"
    )

    final_points: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="最終分數 = actual_points × cumulative_multiplier"
    )

    # 軟刪除
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="軟刪除標記"
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="刪除時間"
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="assessment_records"
    )

    standard: Mapped["AssessmentStandard"] = relationship(
        "AssessmentStandard",
        back_populates="records"
    )

    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        back_populates="assessment_record"
    )

    fault_responsibility: Mapped[Optional["FaultResponsibilityAssessment"]] = relationship(
        "FaultResponsibilityAssessment",
        back_populates="record",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        # 複合索引：員工年度查詢
        Index("ix_assessment_records_employee_year", "employee_id", "record_date"),
        # 複合索引：員工 + 軟刪除查詢
        Index("ix_assessment_records_employee_active", "employee_id", "is_deleted"),
        # 複合索引：標準代碼 + 日期查詢
        Index("ix_assessment_records_standard_date", "standard_code", "record_date"),
        {"comment": "考核記錄表"}
    )

    def __repr__(self) -> str:
        return (
            f"<AssessmentRecord("
            f"id={self.id}, "
            f"employee_id={self.employee_id}, "
            f"standard={self.standard_code}, "
            f"final_points={self.final_points}"
            f")>"
        )

    @property
    def year(self) -> int:
        """記錄年度"""
        return self.record_date.year

    @property
    def month(self) -> int:
        """記錄月份"""
        return self.record_date.month

    @property
    def is_r_type_with_responsibility(self) -> bool:
        """是否為 R02-R05 且有責任判定"""
        return (
            self.standard_code in {'R02', 'R03', 'R04', 'R05'}
            and self.fault_responsibility is not None
        )

    def soft_delete(self) -> None:
        """執行軟刪除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """還原軟刪除"""
        self.is_deleted = False
        self.deleted_at = None
