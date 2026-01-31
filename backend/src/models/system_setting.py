"""
SystemSetting 系統設定模型
對應 tasks.md T034: 建立 SystemSetting 模型
對應 spec.md: SystemSetting (系統設定)
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class DepartmentScope(str, PyEnum):
    """部門範圍列舉"""
    DANHAI = "淡海"
    ANKENG = "安坑"
    GLOBAL = "global"


class SystemSetting(Base, TimestampMixin):
    """
    系統設定模型

    用於儲存系統配置參數，支援部門級別設定。

    Attributes:
        id: 主鍵
        key: 設定鍵名 (最長 100 字元)
        value: 設定值 (Text 類型，支援長字串)
        department: 部門範圍 ('淡海', '安坑', 'global')
        description: 設定說明 (最長 255 字元)
        created_at: 建立時間
        updated_at: 更新時間

    Constraints:
        - UniqueConstraint(key, department): 同一部門下 key 不可重複
    """

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="設定鍵名"
    )

    value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="設定值"
    )

    department: Mapped[Optional[str]] = mapped_column(
        Enum(DepartmentScope, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        index=True,
        comment="部門範圍：淡海、安坑、global"
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="設定說明"
    )

    __table_args__ = (
        UniqueConstraint("key", "department", name="uq_system_setting_key_department"),
        {"comment": "系統設定表"}
    )

    def __repr__(self) -> str:
        return f"<SystemSetting(key={self.key!r}, department={self.department!r})>"


# 預設系統設定鍵名常數
class SettingKeys:
    """系統設定鍵名常數"""

    # Google Sheets 相關
    GOOGLE_SHEETS_ID = "google_sheets_id"
    GOOGLE_SHEETS_SCHEDULE_TAB = "google_sheets_schedule_tab"

    # Google Drive 相關
    GOOGLE_DRIVE_FOLDER_ID = "google_drive_folder_id"
    GOOGLE_DRIVE_EVENT_FOLDER = "google_drive_event_folder"
    GOOGLE_DRIVE_INTERVIEW_FOLDER = "google_drive_interview_folder"

    # 考核系統相關
    ASSESSMENT_ACCUMULATION_COEFFICIENT = "assessment_accumulation_coefficient"
    ASSESSMENT_VERSION = "assessment_version"

    # 同步相關
    LAST_SYNC_TIME = "last_sync_time"
    SYNC_INTERVAL_MINUTES = "sync_interval_minutes"
