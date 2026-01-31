"""
EmployeeTransfer 員工調動歷史模型
對應 tasks.md T044: 建立 EmployeeTransfer 模型
對應 spec.md: EmployeeTransfer (員工調動歷史)
"""

from datetime import date
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .google_oauth_token import Department


class EmployeeTransfer(Base):
    """
    員工調動歷史模型

    記錄員工在部門之間的調動歷史。

    Attributes:
        id: 主鍵
        employee_id: 員工編號（外鍵）
        from_department: 原部門
        to_department: 新部門
        transfer_date: 調動日期
        reason: 調動原因
        created_by: 建立者（操作人員）
        created_at: 建立時間

    Relationships:
        employee: 關聯的員工
    """

    __tablename__ = "employee_transfers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    employee_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="員工編號"
    )

    from_department: Mapped[str] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="原部門：淡海、安坑"
    )

    to_department: Mapped[str] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="新部門：淡海、安坑"
    )

    transfer_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="調動日期"
    )

    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="調動原因"
    )

    created_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="建立者（操作人員）"
    )

    created_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        comment="建立日期"
    )

    # Relationships
    employee = relationship(
        "Employee",
        back_populates="transfers"
    )

    __table_args__ = (
        {"comment": "員工調動歷史表"}
    )

    def __repr__(self) -> str:
        return f"<EmployeeTransfer(employee_id={self.employee_id!r}, {self.from_department} → {self.to_department})>"

    @property
    def description(self) -> str:
        """調動描述"""
        return f"{self.transfer_date}: {self.from_department} → {self.to_department}"
