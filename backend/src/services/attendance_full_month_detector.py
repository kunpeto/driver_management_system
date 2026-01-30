"""
全勤判定服務
對應 tasks.md T196: 實作全勤判定服務

功能：
- 掃描班表所有儲存格，檢查是否包含「(假)」
- 正規化處理：移除多餘空白、全形符號轉半形
- 判定整月全勤狀態
"""

import re
from typing import List, Any, Optional
from dataclasses import dataclass

from src.utils.logger import logger


@dataclass
class FullMonthResult:
    """全勤判定結果"""
    employee_id: str
    employee_name: str
    is_full_attendance: bool
    leave_dates: List[str]  # 請假日期列表
    leave_count: int


class AttendanceFullMonthDetector:
    """
    全勤判定服務

    掃描員工整月班表，判定是否符合全勤條件。
    全勤定義：整月無任何請假（不含「(假)」、「(特)」、「(公)」等）
    """

    # 請假標記（含全形變體）
    LEAVE_PATTERNS = [
        r"\(假\)", r"（假）", r"\(特\)", r"（特）",
        r"\(公\)", r"（公）", r"\(婚\)", r"（婚）",
        r"\(喪\)", r"（喪）", r"\(病\)", r"（病）",
        r"\(事\)", r"（事）", r"\(育\)", r"（育）",
        r"\(產\)", r"（產）", r"\(傷\)", r"（傷）"
    ]

    def __init__(self):
        # 編譯合併的正則
        combined_pattern = "|".join(self.LEAVE_PATTERNS)
        self.leave_regex = re.compile(combined_pattern)

    def _normalize_text(self, text: str) -> str:
        """
        正規化文字

        - 移除多餘空白
        - 全形符號轉半形

        Args:
            text: 原始文字

        Returns:
            正規化後的文字
        """
        if not text:
            return ""

        # 移除多餘空白
        text = text.strip()
        text = re.sub(r"\s+", "", text)

        # 全形轉半形（僅處理括號）
        text = text.replace("（", "(").replace("）", ")")

        return text

    def check_cell_has_leave(self, cell_value: Any) -> bool:
        """
        檢查單一儲存格是否包含請假標記

        Args:
            cell_value: 儲存格值

        Returns:
            是否為請假
        """
        if cell_value is None:
            return False

        text = self._normalize_text(str(cell_value))

        # 使用正則匹配
        return bool(self.leave_regex.search(text))

    def detect_full_month(
        self,
        employee_id: str,
        employee_name: str,
        shift_cells: List[Any]
    ) -> FullMonthResult:
        """
        判定員工整月是否全勤

        Args:
            employee_id: 員工編號
            employee_name: 員工姓名
            shift_cells: 該員工整月的班別儲存格列表（索引=天數-1）

        Returns:
            FullMonthResult: 全勤判定結果
        """
        leave_dates = []

        for day_idx, cell in enumerate(shift_cells):
            day = day_idx + 1  # 日期從 1 開始

            if self.check_cell_has_leave(cell):
                leave_dates.append(str(day))

        is_full = len(leave_dates) == 0

        if not is_full:
            logger.debug(
                "員工有請假記錄",
                employee_id=employee_id,
                leave_dates=leave_dates
            )

        return FullMonthResult(
            employee_id=employee_id,
            employee_name=employee_name,
            is_full_attendance=is_full,
            leave_dates=leave_dates,
            leave_count=len(leave_dates)
        )

    def detect_batch(
        self,
        employees_data: List[dict]
    ) -> List[FullMonthResult]:
        """
        批次判定全勤

        Args:
            employees_data: 員工資料列表，格式：
                [{"employee_id": "xxx", "employee_name": "xxx", "shifts": [...]}]

        Returns:
            全勤判定結果列表
        """
        results = []

        for emp in employees_data:
            result = self.detect_full_month(
                employee_id=emp.get("employee_id", ""),
                employee_name=emp.get("employee_name", ""),
                shift_cells=emp.get("shifts", [])
            )
            results.append(result)

        # 統計
        full_count = sum(1 for r in results if r.is_full_attendance)
        logger.info(
            "全勤批次判定完成",
            total=len(results),
            full_attendance_count=full_count
        )

        return results


# 單例
_detector_instance: Optional[AttendanceFullMonthDetector] = None


def get_full_month_detector() -> AttendanceFullMonthDetector:
    """取得全勤判定器實例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = AttendanceFullMonthDetector()
    return _detector_instance
