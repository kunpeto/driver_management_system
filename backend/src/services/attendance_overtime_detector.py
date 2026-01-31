"""
延長工時判定服務
對應 tasks.md T198: 實作延長工時判定服務

功能：
- 正則匹配 (+1)~(+4) 提取加班時數
- 支援全形括號
- 返回加班時數與日期
"""

import re
from typing import List, Any, Optional
from datetime import date
from dataclasses import dataclass

from src.constants.attendance import (
    OVERTIME_PATTERN,
    OVERTIME_CODE_MAP,
    OVERTIME_POINTS_MAP
)
from src.utils.logger import logger


@dataclass
class OvertimeRecord:
    """延長工時記錄"""
    employee_id: str
    employee_name: str
    record_date: date
    shift_code: str
    overtime_hours: int  # 1~4


@dataclass
class OvertimeResult:
    """延長工時判定結果"""
    employee_id: str
    employee_name: str
    records: List[OvertimeRecord]
    total_overtime_hours: int
    overtime_days: int


class AttendanceOvertimeDetector:
    """
    延長工時判定服務

    從班表判定員工的延長工時情況。
    格式：(+1), (+2), (+3), (+4) 或全形版本
    對應考核項目：+A03~+A06
    """

    def __init__(self):
        # 從常量模組載入模式並編譯
        self._overtime_pattern = re.compile(OVERTIME_PATTERN)

    def _normalize_text(self, text: str) -> str:
        """正規化文字"""
        if not text:
            return ""
        text = text.strip()
        # 全形轉半形
        text = text.replace("（", "(").replace("）", ")")
        text = text.replace("＋", "+")
        return text

    def extract_overtime_hours(self, cell_value: Any) -> Optional[int]:
        """
        從儲存格提取延長工時時數

        Args:
            cell_value: 儲存格值

        Returns:
            延長工時小時數（1-4），無則返回 None
        """
        if cell_value is None:
            return None

        text = self._normalize_text(str(cell_value))
        match = self._overtime_pattern.search(text)

        if match:
            return int(match.group(1))
        return None

    def detect_single(
        self,
        cell_value: Any,
        employee_id: str,
        employee_name: str,
        record_date: date
    ) -> Optional[OvertimeRecord]:
        """
        判定單一儲存格的延長工時

        Args:
            cell_value: 儲存格值
            employee_id: 員工編號
            employee_name: 員工姓名
            record_date: 日期

        Returns:
            延長工時記錄或 None
        """
        hours = self.extract_overtime_hours(cell_value)

        if hours is None:
            return None

        text = self._normalize_text(str(cell_value))

        return OvertimeRecord(
            employee_id=employee_id,
            employee_name=employee_name,
            record_date=record_date,
            shift_code=text,
            overtime_hours=hours
        )

    def detect_employee_month(
        self,
        employee_id: str,
        employee_name: str,
        shift_cells: List[Any],
        year: int,
        month: int
    ) -> OvertimeResult:
        """
        判定員工整月的延長工時

        Args:
            employee_id: 員工編號
            employee_name: 員工姓名
            shift_cells: 班別儲存格列表
            year: 年份
            month: 月份

        Returns:
            OvertimeResult: 延長工時判定結果
        """
        records = []

        for day_idx, cell in enumerate(shift_cells):
            day = day_idx + 1

            try:
                record_date = date(year, month, day)
                record = self.detect_single(
                    cell_value=cell,
                    employee_id=employee_id,
                    employee_name=employee_name,
                    record_date=record_date
                )
                if record:
                    records.append(record)
            except ValueError:
                continue

        total_hours = sum(r.overtime_hours for r in records)
        overtime_days = len(records)

        if records:
            logger.debug(
                "員工有延長工時",
                employee_id=employee_id,
                overtime_days=overtime_days,
                total_hours=total_hours
            )

        return OvertimeResult(
            employee_id=employee_id,
            employee_name=employee_name,
            records=records,
            total_overtime_hours=total_hours,
            overtime_days=overtime_days
        )

    def detect_batch(
        self,
        employees_data: List[dict],
        year: int,
        month: int
    ) -> List[OvertimeResult]:
        """
        批次判定延長工時

        Args:
            employees_data: 員工資料列表
            year: 年份
            month: 月份

        Returns:
            延長工時判定結果列表
        """
        results = []

        for emp in employees_data:
            result = self.detect_employee_month(
                employee_id=emp.get("employee_id", ""),
                employee_name=emp.get("employee_name", ""),
                shift_cells=emp.get("shifts", []),
                year=year,
                month=month
            )
            results.append(result)

        # 統計
        total_days = sum(r.overtime_days for r in results)
        total_hours = sum(r.total_overtime_hours for r in results)
        logger.info(
            "延長工時批次判定完成",
            total_employees=len(results),
            total_overtime_days=total_days,
            total_overtime_hours=total_hours
        )

        return results

    @staticmethod
    def get_assessment_code(hours: int) -> str:
        """
        根據延長工時小時數取得考核代碼

        Args:
            hours: 延長工時小時數 (1-4)

        Returns:
            考核代碼（+A03~+A06）
        """
        return OVERTIME_CODE_MAP.get(hours, "+A03")

    @staticmethod
    def get_assessment_points(hours: int) -> float:
        """
        根據延長工時小時數取得加分分數

        Args:
            hours: 延長工時小時數 (1-4)

        Returns:
            加分分數
        """
        return OVERTIME_POINTS_MAP.get(hours, 0.5)


# 單例
_detector_instance: Optional[AttendanceOvertimeDetector] = None


def get_overtime_detector() -> AttendanceOvertimeDetector:
    """取得延長工時判定器實例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = AttendanceOvertimeDetector()
    return _detector_instance
