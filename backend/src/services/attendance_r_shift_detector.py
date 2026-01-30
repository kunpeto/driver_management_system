"""
R班出勤判定服務
對應 tasks.md T197: 實作 R班出勤判定服務

功能：
- 正則匹配 R/... 判定一般 R班
- 正則匹配 R(國)/... 判定國定假日 R班
- 返回出勤類型與日期
"""

import re
from typing import List, Any, Optional
from datetime import date
from dataclasses import dataclass

from src.utils.logger import logger


@dataclass
class RShiftRecord:
    """R班出勤記錄"""
    employee_id: str
    employee_name: str
    record_date: date
    shift_code: str
    is_national_holiday: bool  # 是否為國定假日 R班


@dataclass
class RShiftResult:
    """R班判定結果"""
    employee_id: str
    employee_name: str
    records: List[RShiftRecord]
    r_shift_count: int
    national_holiday_count: int


class AttendanceRShiftDetector:
    """
    R班出勤判定服務

    判定員工班表中的 R班出勤情況。
    - R/0905G：一般 R班（+A01 +3分）
    - R(國)/0905G：國定假日 R班（+A01 +3分 + +A02 +1分）
    """

    # R班正則
    # 匹配：R/0905G, R(國)/1425G, R(國)/0905G(+2) 等
    R_SHIFT_PATTERN = re.compile(
        r"^R(?:\((國|国)\))?/(.+)$",
        re.IGNORECASE
    )

    # 國定假日標記
    NATIONAL_HOLIDAY_PATTERN = re.compile(
        r"^R\((國|国)\)/",
        re.IGNORECASE
    )

    def __init__(self):
        pass

    def _normalize_text(self, text: str) -> str:
        """正規化文字"""
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r"\s+", "", text)
        return text

    def check_is_r_shift(self, cell_value: Any) -> bool:
        """
        檢查儲存格是否為 R班

        Args:
            cell_value: 儲存格值

        Returns:
            是否為 R班
        """
        if cell_value is None:
            return False

        text = self._normalize_text(str(cell_value))

        # R班必須以 R/ 或 R(國)/ 開頭
        return bool(self.R_SHIFT_PATTERN.match(text))

    def check_is_national_holiday(self, cell_value: Any) -> bool:
        """
        檢查是否為國定假日 R班

        Args:
            cell_value: 儲存格值

        Returns:
            是否為國定假日 R班
        """
        if cell_value is None:
            return False

        text = self._normalize_text(str(cell_value))

        return bool(self.NATIONAL_HOLIDAY_PATTERN.match(text))

    def detect_single(
        self,
        cell_value: Any,
        employee_id: str,
        employee_name: str,
        record_date: date
    ) -> Optional[RShiftRecord]:
        """
        判定單一儲存格的 R班狀態

        Args:
            cell_value: 儲存格值
            employee_id: 員工編號
            employee_name: 員工姓名
            record_date: 日期

        Returns:
            R班記錄或 None
        """
        if not self.check_is_r_shift(cell_value):
            return None

        text = self._normalize_text(str(cell_value))
        is_national = self.check_is_national_holiday(cell_value)

        return RShiftRecord(
            employee_id=employee_id,
            employee_name=employee_name,
            record_date=record_date,
            shift_code=text,
            is_national_holiday=is_national
        )

    def detect_employee_month(
        self,
        employee_id: str,
        employee_name: str,
        shift_cells: List[Any],
        year: int,
        month: int
    ) -> RShiftResult:
        """
        判定員工整月的 R班出勤

        Args:
            employee_id: 員工編號
            employee_name: 員工姓名
            shift_cells: 班別儲存格列表（索引=天數-1）
            year: 年份
            month: 月份

        Returns:
            RShiftResult: R班判定結果
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
                # 無效日期（如 2 月 30 日）
                continue

        r_shift_count = len(records)
        national_holiday_count = sum(1 for r in records if r.is_national_holiday)

        if records:
            logger.debug(
                "員工有 R班出勤",
                employee_id=employee_id,
                r_shift_count=r_shift_count,
                national_holiday_count=national_holiday_count
            )

        return RShiftResult(
            employee_id=employee_id,
            employee_name=employee_name,
            records=records,
            r_shift_count=r_shift_count,
            national_holiday_count=national_holiday_count
        )

    def detect_batch(
        self,
        employees_data: List[dict],
        year: int,
        month: int
    ) -> List[RShiftResult]:
        """
        批次判定 R班

        Args:
            employees_data: 員工資料列表
            year: 年份
            month: 月份

        Returns:
            R班判定結果列表
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
        total_r_shifts = sum(r.r_shift_count for r in results)
        total_national = sum(r.national_holiday_count for r in results)
        logger.info(
            "R班批次判定完成",
            total_employees=len(results),
            total_r_shifts=total_r_shifts,
            total_national_holidays=total_national
        )

        return results


# 單例
_detector_instance: Optional[AttendanceRShiftDetector] = None


def get_r_shift_detector() -> AttendanceRShiftDetector:
    """取得 R班判定器實例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = AttendanceRShiftDetector()
    return _detector_instance
