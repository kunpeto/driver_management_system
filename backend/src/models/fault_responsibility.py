"""
FaultResponsibilityAssessment 故障責任判定模型
對應 tasks.md T161: 建立 FaultResponsibilityAssessment 模型
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 故障責任判定（R02-R05 專用）
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .assessment_record import AssessmentRecord


class ResponsibilityLevel(str, enum.Enum):
    """責任程度"""
    FULL = "完全責任"  # 7-9 項疏失，係數 1.0
    MAJOR = "主要責任"  # 4-6 項疏失，係數 0.7
    MINOR = "次要責任"  # 1-3 項疏失，係數 0.3


# 9 項疏失查核項目的鍵值定義
CHECKLIST_KEYS = [
    "awareness_delay",      # 1. 察覺過晚或誤判
    "report_delay",         # 2. 通報延遲或不完整
    "unfamiliar_procedure", # 3. 不熟悉故障排除程序
    "wrong_operation",      # 4. 故障排除決策/操作錯誤
    "slow_action",          # 5. 動作遲緩
    "unconfirmed_result",   # 6. 未確認結果或誤認完成
    "no_progress_report",   # 7. 未主動回報處理進度
    "repeated_error",       # 8. 重複性錯誤
    "mental_state_issue",   # 9. 心理狀態影響表現
]

# 9 項疏失查核項目的中文名稱
CHECKLIST_LABELS = {
    "awareness_delay": "察覺過晚或誤判",
    "report_delay": "通報延遲或不完整",
    "unfamiliar_procedure": "不熟悉故障排除程序",
    "wrong_operation": "故障排除決策/操作錯誤",
    "slow_action": "動作遲緩",
    "unconfirmed_result": "未確認結果或誤認完成",
    "no_progress_report": "未主動回報處理進度",
    "repeated_error": "重複性錯誤",
    "mental_state_issue": "心理狀態影響表現",
}


def determine_responsibility(fault_count: int) -> tuple[str, float]:
    """
    根據疏失項數判定責任程度

    Args:
        fault_count: 疏失項數（0-9）

    Returns:
        (責任程度, 責任係數) 元組
    """
    if fault_count >= 7:
        return (ResponsibilityLevel.FULL.value, 1.0)
    elif 4 <= fault_count <= 6:
        return (ResponsibilityLevel.MAJOR.value, 0.7)
    elif 1 <= fault_count <= 3:
        return (ResponsibilityLevel.MINOR.value, 0.3)
    else:
        # 0 項疏失不應該建立此記錄，但以防萬一
        return (ResponsibilityLevel.MINOR.value, 0.0)


class FaultResponsibilityAssessment(Base, TimestampMixin):
    """
    故障責任判定模型（R02-R05 專用）

    儲存 R02-R05 責任判定的詳細資料，包含 9 項疏失查核表結果

    Attributes:
        id: 主鍵
        record_id: 考核記錄 ID (FK, unique, one-to-one)
        time_t0: T0 - 事件/故障發生時間
        time_t1: T1 - 司機員察覺異常時間
        time_t2: T2 - 開始通報/處理時間
        time_t3: T3 - 故障排除完成時間
        time_t4: T4 - 恢復正常運轉時間
        delay_seconds: 總延誤時間（秒）
        checklist_results: 9 項疏失查核結果（JSON）
        fault_count: 疏失項數（0-9）
        responsibility_level: 責任程度
        responsibility_coefficient: 責任係數
        notes: 備註

    Relationships:
        record: 關聯的考核記錄
    """

    __tablename__ = "fault_responsibility_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 一對一關聯到 AssessmentRecord
    record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessment_records.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="考核記錄 ID（一對一）"
    )

    # 時間節點（用於計算延誤時間）
    time_t0: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="T0: 事件/故障發生時間"
    )

    time_t1: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="T1: 司機員察覺異常時間"
    )

    time_t2: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="T2: 開始通報/處理時間"
    )

    time_t3: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="T3: 故障排除完成時間"
    )

    time_t4: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="T4: 恢復正常運轉時間"
    )

    # 延誤時間
    delay_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="總延誤時間（秒），依 OCC 計算或 T4-T0"
    )

    # 9 項疏失查核結果（JSON 格式）
    checklist_results: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="9 項疏失查核結果（JSON）"
    )

    # 責任判定結果
    fault_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="疏失項數（0-9）"
    )

    responsibility_level: Mapped[str] = mapped_column(
        Enum(ResponsibilityLevel, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="責任程度"
    )

    responsibility_coefficient: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="責任係數（1.0/0.7/0.3）"
    )

    # 備註
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="責任判定備註"
    )

    # Relationships
    record: Mapped["AssessmentRecord"] = relationship(
        "AssessmentRecord",
        back_populates="fault_responsibility"
    )

    __table_args__ = (
        Index("ix_fault_responsibility_level", "responsibility_level"),
        {"comment": "故障責任判定表（R02-R05 專用）"}
    )

    def __repr__(self) -> str:
        return (
            f"<FaultResponsibilityAssessment("
            f"record_id={self.record_id}, "
            f"level={self.responsibility_level}, "
            f"coefficient={self.responsibility_coefficient}"
            f")>"
        )

    @property
    def delay_minutes(self) -> float:
        """延誤時間（分鐘）"""
        return self.delay_seconds / 60

    @property
    def checked_items(self) -> list[str]:
        """已勾選的疏失項目"""
        return [
            key for key in CHECKLIST_KEYS
            if self.checklist_results.get(key, False)
        ]

    @property
    def checked_items_labels(self) -> list[str]:
        """已勾選的疏失項目（中文名稱）"""
        return [
            CHECKLIST_LABELS[key]
            for key in self.checked_items
        ]

    @classmethod
    def create_checklist_results(cls, **kwargs: bool) -> dict[str, bool]:
        """
        建立標準格式的查核結果 JSON

        Args:
            **kwargs: 各查核項目的布林值

        Returns:
            標準格式的查核結果字典
        """
        return {
            key: kwargs.get(key, False)
            for key in CHECKLIST_KEYS
        }

    def count_faults(self) -> int:
        """計算疏失項數"""
        return sum(
            1 for key in CHECKLIST_KEYS
            if self.checklist_results.get(key, False)
        )

    def update_responsibility(self) -> None:
        """根據查核結果更新責任判定"""
        self.fault_count = self.count_faults()
        level, coefficient = determine_responsibility(self.fault_count)
        self.responsibility_level = level
        self.responsibility_coefficient = coefficient
