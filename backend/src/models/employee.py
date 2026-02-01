"""
Employee 員工資料模型
對應 tasks.md T043: 建立 Employee 模型
對應 tasks.md T164: 擴充 Employee 模型（Phase 12 考核系統）
對應 spec.md: Employee (員工資料)
對應 data-model-phase12.md: Employee 擴充欄位
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from src.constants import Department

if TYPE_CHECKING:
    from .assessment_record import AssessmentRecord
    from .cumulative_counter import CumulativeCounter
    from .monthly_reward import MonthlyReward


class Employee(Base, TimestampMixin):
    """
    員工資料模型

    儲存司機員的基本資料，包含編號、姓名、部門、聯絡資訊等。

    Attributes:
        id: 主鍵
        employee_id: 員工編號（唯一索引，如 1011M0095）
        employee_name: 員工姓名
        current_department: 現職部門 ('淡海', '安坑')
        hire_year_month: 入職年月 (格式: YYYY-MM，如 2021-11)
        phone: 電話號碼
        email: 電子郵件
        emergency_contact: 緊急聯絡人
        emergency_phone: 緊急聯絡電話
        is_resigned: 是否離職
        created_at: 建立時間
        updated_at: 更新時間

    Relationships:
        transfers: 調動歷史記錄
    """

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    employee_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="員工編號（如 1011M0095）"
    )

    employee_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="員工姓名"
    )

    current_department: Mapped[str] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="現職部門：淡海、安坑"
    )

    hire_year_month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="入職年月（格式：YYYY-MM）"
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="電話號碼"
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="電子郵件"
    )

    emergency_contact: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="緊急聯絡人"
    )

    emergency_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="緊急聯絡電話"
    )

    is_resigned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="是否離職"
    )

    # Phase 12: 考核分數
    current_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=80.0,
        comment="當前考核分數（起始分數 80 分）"
    )

    # Relationships
    transfers = relationship(
        "EmployeeTransfer",
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="desc(EmployeeTransfer.transfer_date)"
    )

    # Phase 11: 履歷關係
    profiles = relationship(
        "Profile",
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="desc(Profile.event_date)"
    )

    # Phase 12: 考核系統關聯
    assessment_records: Mapped[list["AssessmentRecord"]] = relationship(
        "AssessmentRecord",
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="desc(AssessmentRecord.record_date)"
    )

    cumulative_counters: Mapped[list["CumulativeCounter"]] = relationship(
        "CumulativeCounter",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    monthly_rewards: Mapped[list["MonthlyReward"]] = relationship(
        "MonthlyReward",
        back_populates="employee",
        cascade="all, delete-orphan",
        order_by="desc(MonthlyReward.year_month)"
    )

    __table_args__ = (
        {"comment": "員工資料表"}
    )

    def __repr__(self) -> str:
        return f"<Employee(employee_id={self.employee_id!r}, name={self.employee_name!r})>"

    @property
    def display_name(self) -> str:
        """顯示名稱（編號 + 姓名）"""
        return f"{self.employee_id} {self.employee_name}"

    @property
    def is_active(self) -> bool:
        """是否在職"""
        return not self.is_resigned
