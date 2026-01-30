"""
PersonnelInterview 人員訪談模型
對應 tasks.md T132: 建立 PersonnelInterview 模型
對應 spec.md: User Story 8 - 人員訪談記錄

Gemini Review 2026-01-30 優化：
- 新增 interview_result_data (JSON) 儲存訪談結果勾選
- 新增 follow_up_action_data (JSON) 儲存後續行動勾選
- 新增 conclusion 欄位
"""

from datetime import date
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .profile import Profile


class PersonnelInterview(Base, TimestampMixin):
    """
    人員訪談模型

    儲存人員訪談的詳細資訊，作為 Profile 的子表。
    包含訪談內容、班表資訊、訪談結果勾選等。

    Attributes:
        id: 主鍵
        profile_id: 履歷 ID (FK)
        hire_date: 到職日期
        shift_before_2days: 前2天班別
        shift_before_1day: 前1天班別
        shift_event_day: 事件當天班別
        interview_content: 訪談內容
        interviewer: 訪談人員
        interview_date: 訪談日期
        interview_result_data: 訪談結果勾選 (JSON)
        follow_up_action_data: 後續行動勾選 (JSON)
        conclusion: 結論
        created_at: 建立時間
        updated_at: 更新時間

    JSON 欄位格式：
        interview_result_data: {
            "ir_1": bool,  # 駕駛執照規定班別符合
            "ir_2": bool,  # 人員工作規定
            "ir_3": bool,  # 操作程序正確
            "ir_4": bool,  # 人員注意或作
            "ir_5": bool,  # 設備檢測正常
            "ir_6": bool,  # 人員規範熟練
            "ir_7": bool,  # 其他
            "ir_other_text": str  # 其他說明文字
        }

        follow_up_action_data: {
            "fa_1": bool,  # 加強駕駛班前訓練
            "fa_2": bool,  # 列入駕駛缺點管
            "fa_3": bool,  # 培訓複訓
            "fa_4": bool,  # 追蹤作業執行
            "fa_5": bool,  # 設備維修
            "fa_6": bool,  # 人員改善教訓
            "fa_7": bool,  # 其他
            "fa_other_text": str  # 其他說明文字
        }

    Relationships:
        profile: 關聯的履歷主表
    """

    __tablename__ = "personnel_interviews"

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

    # 人事資訊
    hire_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="到職日期"
    )

    # 班表資訊（自動從 schedules 表查詢填入）
    shift_before_2days: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="前2天班別"
    )

    shift_before_1day: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="前1天班別"
    )

    shift_event_day: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="事件當天班別"
    )

    # 訪談資訊
    interview_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="訪談內容"
    )

    interviewer: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="訪談人員"
    )

    interview_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="訪談日期"
    )

    # 訪談結果勾選（Gemini Review 新增）
    interview_result_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="訪談結果勾選 (JSON): ir_1~ir_7, ir_other_text"
    )

    # 後續行動勾選（Gemini Review 新增）
    follow_up_action_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="後續行動勾選 (JSON): fa_1~fa_7, fa_other_text"
    )

    # 結論（Gemini Review 新增）
    conclusion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="結論"
    )

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="personnel_interview"
    )

    __table_args__ = (
        {"comment": "人員訪談表"}
    )

    def __repr__(self) -> str:
        return f"<PersonnelInterview(id={self.id}, profile_id={self.profile_id})>"

    def get_interview_result(self, key: str) -> bool:
        """獲取訪談結果勾選值"""
        if not self.interview_result_data:
            return False
        return self.interview_result_data.get(key, False)

    def get_follow_up_action(self, key: str) -> bool:
        """獲取後續行動勾選值"""
        if not self.follow_up_action_data:
            return False
        return self.follow_up_action_data.get(key, False)

    def set_interview_result(self, key: str, value: bool) -> None:
        """設定訪談結果勾選值"""
        if self.interview_result_data is None:
            self.interview_result_data = {}
        self.interview_result_data[key] = value

    def set_follow_up_action(self, key: str, value: bool) -> None:
        """設定後續行動勾選值"""
        if self.follow_up_action_data is None:
            self.follow_up_action_data = {}
        self.follow_up_action_data[key] = value

    @property
    def shifts_display(self) -> str:
        """班別顯示（前2天 / 前1天 / 當天）"""
        shifts = [
            self.shift_before_2days or "-",
            self.shift_before_1day or "-",
            self.shift_event_day or "-",
        ]
        return " / ".join(shifts)
