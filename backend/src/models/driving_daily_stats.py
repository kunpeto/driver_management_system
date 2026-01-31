"""
DrivingDailyStats 每日駕駛時數統計模型
對應 tasks.md T103: 建立 DrivingDailyStats 模型
對應 spec.md: DrivingDailyStats (每日駕駛統計)
"""

from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .google_oauth_token import Department


class DrivingDailyStats(Base, TimestampMixin):
    """
    每日駕駛時數統計模型

    儲存每位員工每日的駕駛時數，由系統從 Google Sheets 勤務表同步計算。

    Attributes:
        id: 主鍵
        employee_id: 員工 ID (FK -> employees.id)
        department: 部門 ('淡海', '安坑')
        record_date: 記錄日期
        total_minutes: 當日總駕駛分鐘數
        is_holiday_work: 是否為 R班出勤（休假日出勤，用於 × 2 計算）
        incident_count: 當日責任事件次數（S/R 類別）
        created_at: 建立時間
        updated_at: 更新時間

    Business Rules:
        - is_holiday_work = true 時，該日時數在季度競賽計算中 × 2
        - 責任事件來源為 profiles 表的 S/R 類別事件
        - 每位員工每天只有一筆記錄（唯一約束）
    """

    __tablename__ = "driving_daily_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="員工 ID"
    )

    department: Mapped[str] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="部門：淡海、安坑"
    )

    record_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="記錄日期"
    )

    total_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="當日總駕駛分鐘數"
    )

    is_holiday_work: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否為 R班出勤（休假日出勤，用於 × 2 計算）"
    )

    incident_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="當日責任事件次數（S/R 類別）"
    )

    # Relationships
    employee = relationship("Employee", backref="driving_daily_stats")

    __table_args__ = (
        UniqueConstraint(
            "employee_id", "record_date",
            name="uq_driving_daily_stats_employee_date"
        ),
        Index("idx_driving_daily_stats_date_dept", "record_date", "department"),
        Index("idx_driving_daily_stats_employee_date_range", "employee_id", "record_date"),
        {"comment": "每日駕駛時數統計表"}
    )

    def __repr__(self) -> str:
        return f"<DrivingDailyStats(employee_id={self.employee_id}, date={self.record_date}, minutes={self.total_minutes})>"

    @property
    def total_hours(self) -> float:
        """轉換為小時"""
        return self.total_minutes / 60.0

    @property
    def effective_minutes(self) -> int:
        """有效分鐘數（R班 × 2）"""
        if self.is_holiday_work:
            return self.total_minutes * 2
        return self.total_minutes

    @property
    def effective_hours(self) -> float:
        """有效小時數（R班 × 2）"""
        return self.effective_minutes / 60.0
