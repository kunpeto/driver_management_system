"""
Schedule 班表資料模型
對應 tasks.md T079: 建立 Schedule 模型
對應 spec.md: Schedule (班表資料)

功能：
- 儲存從 Google Sheets 同步的班表資料
- 支援多部門、多員工、多日期的班表記錄
- 紀錄班別類型、原始值、同步來源
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from src.constants import Department


class ShiftType(str):
    """
    班別類型常數

    常見班別：
    - 早班: 0500G, 0600G 等
    - 中班: 1200G, 1300G 等
    - 晚班: 1800G, 1900G 等
    - R班: R/..., R(國)/... (休息日支援出勤)
    - 休假: (假), (特), (公)
    - 其他: 站, 訓, 借 等
    """
    EARLY = "早班"
    MIDDLE = "中班"
    LATE = "晚班"
    R_SHIFT = "R班"
    LEAVE = "休假"
    OTHER = "其他"


class Schedule(Base, TimestampMixin):
    """
    班表資料模型

    儲存從 Google Sheets 同步的每日班表資料。

    Attributes:
        id: 主鍵
        employee_id: 員工編號 (關聯 employees.employee_id)
        department: 部門 ('淡海', '安坑')
        schedule_date: 班表日期
        shift_code: 原始班別代碼 (如 '0600G', 'R/0905G', '(假)')
        shift_type: 班別分類 (早班/中班/晚班/R班/休假/其他)
        start_time: 開始時間 (如 '06:00')
        end_time: 結束時間 (如 '14:30')
        notes: 備註
        sync_source: 同步來源 (Google Sheets ID)
        sync_batch_id: 同步批次 ID
        synced_at: 同步時間

    Indexes:
        - (department, schedule_date) 複合索引
        - (employee_id, schedule_date) 複合索引
    """

    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 關聯員工（使用 employee_id 字串，而非外鍵）
    # 因為班表可能包含尚未建立資料的員工
    employee_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="員工編號（如 1011M0095）"
    )

    employee_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="員工姓名（同步時記錄，避免每次查詢）"
    )

    department: Mapped[str] = mapped_column(
        SQLEnum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="部門：淡海、安坑"
    )

    schedule_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="班表日期"
    )

    # 班別資訊
    shift_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="原始班別代碼（如 0600G, R/0905G, (假)）"
    )

    shift_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="班別分類（早班/中班/晚班/R班/休假/其他）"
    )

    start_time: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="開始時間（格式 HH:MM）"
    )

    end_time: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="結束時間（格式 HH:MM）"
    )

    # 延長工時標記
    overtime_hours: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        default=None,
        comment="延長工時小時數（從 +1, +2 等解析）"
    )

    # 備註
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="備註"
    )

    # 同步資訊
    sync_source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="同步來源（Google Sheets ID）"
    )

    sync_batch_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="同步批次 ID"
    )

    synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="同步時間"
    )

    __table_args__ = (
        # 複合索引：部門 + 日期（常用查詢）
        Index("ix_schedules_dept_date", "department", "schedule_date"),
        # 複合索引：員工 + 日期（查詢特定員工班表）
        Index("ix_schedules_emp_date", "employee_id", "schedule_date"),
        # 唯一約束：同一員工同一日期只能有一筆記錄
        Index(
            "uq_schedules_emp_date",
            "employee_id", "schedule_date",
            unique=True
        ),
        {"comment": "班表資料表"}
    )

    def __repr__(self) -> str:
        return f"<Schedule(employee={self.employee_id!r}, date={self.schedule_date}, shift={self.shift_code!r})>"

    @property
    def is_r_shift(self) -> bool:
        """是否為 R班（休息日支援出勤）"""
        return self.shift_code.startswith("R/") or self.shift_code.startswith("R(")

    @property
    def is_leave(self) -> bool:
        """是否為休假"""
        return "(假)" in self.shift_code or "(特)" in self.shift_code or "(公)" in self.shift_code

    @property
    def has_overtime(self) -> bool:
        """是否有延長工時"""
        return self.overtime_hours is not None and self.overtime_hours > 0


class SyncTask(Base, TimestampMixin):
    """
    同步任務記錄

    追蹤每次 Google Sheets 同步的執行狀態與結果。

    Attributes:
        id: 主鍵
        batch_id: 批次 ID（UUID）
        task_type: 任務類型（schedule_sync, duty_sync 等）
        department: 部門
        target_year: 目標年份
        target_month: 目標月份
        status: 狀態（pending, running, completed, failed）
        total_rows: 總處理行數
        success_count: 成功數量
        error_count: 錯誤數量
        error_details: 錯誤詳情（JSON）
        started_at: 開始時間
        completed_at: 完成時間
        triggered_by: 觸發方式（auto, manual）
        triggered_by_user: 觸發使用者
    """

    __tablename__ = "sync_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    batch_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="批次 ID（UUID）"
    )

    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="任務類型（schedule_sync, duty_sync）"
    )

    department: Mapped[Optional[str]] = mapped_column(
        SQLEnum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="部門（可空表示全部門）"
    )

    target_year: Mapped[int] = mapped_column(
        nullable=False,
        comment="目標年份"
    )

    target_month: Mapped[int] = mapped_column(
        nullable=False,
        comment="目標月份"
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="狀態：pending, running, completed, failed"
    )

    total_rows: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        default=0,
        comment="總處理行數"
    )

    success_count: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        default=0,
        comment="成功數量"
    )

    error_count: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        default=0,
        comment="錯誤數量"
    )

    error_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="錯誤詳情（JSON 格式）"
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="開始時間"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成時間"
    )

    triggered_by: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
        comment="觸發方式：auto（自動）, manual（手動）"
    )

    triggered_by_user: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="觸發使用者"
    )

    __table_args__ = (
        Index("ix_sync_tasks_status_type", "status", "task_type"),
        {"comment": "同步任務記錄表"}
    )

    def __repr__(self) -> str:
        return f"<SyncTask(batch={self.batch_id!r}, type={self.task_type!r}, status={self.status!r})>"

    @property
    def is_running(self) -> bool:
        """任務是否正在執行"""
        return self.status == "running"

    @property
    def is_completed(self) -> bool:
        """任務是否已完成"""
        return self.status in ("completed", "failed")

    @property
    def progress_percentage(self) -> float:
        """執行進度百分比"""
        if not self.total_rows or self.total_rows == 0:
            return 0.0
        processed = (self.success_count or 0) + (self.error_count or 0)
        return min(100.0, (processed / self.total_rows) * 100)
