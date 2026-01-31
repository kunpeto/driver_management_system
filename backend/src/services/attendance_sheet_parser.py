"""
差勤班表解析服務
對應 tasks.md T195: 實作班表解析服務

功能：
- 解析 Google Sheets 班表
- 返回標準化的每日出勤物件
- 整合全勤、R班、延長工時判定
"""

from typing import List, Any, Optional, Dict
from datetime import date
from dataclasses import dataclass, field
from calendar import monthrange

from src.constants.attendance import (
    EMPLOYEE_ID_COLUMN_ALIASES,
    EMPLOYEE_NAME_COLUMN_ALIASES
)
from src.utils.logger import logger
from src.services.schedule_parser import ScheduleParser
from src.services.attendance_full_month_detector import (
    AttendanceFullMonthDetector,
    FullMonthResult,
    get_full_month_detector
)
from src.services.attendance_r_shift_detector import (
    AttendanceRShiftDetector,
    RShiftResult,
    RShiftRecord,
    get_r_shift_detector
)
from src.services.attendance_overtime_detector import (
    AttendanceOvertimeDetector,
    OvertimeResult,
    OvertimeRecord,
    get_overtime_detector
)


@dataclass
class DailyAttendance:
    """每日出勤物件"""
    employee_id: str
    employee_name: str
    record_date: date
    shift_code: str
    is_r_shift: bool = False
    is_national_holiday: bool = False
    overtime_hours: Optional[int] = None
    is_leave: bool = False


@dataclass
class EmployeeAttendanceSummary:
    """員工月度出勤摘要"""
    employee_id: str
    employee_name: str
    year: int
    month: int
    is_full_attendance: bool
    leave_dates: List[str]
    r_shift_records: List[RShiftRecord]
    overtime_records: List[OvertimeRecord]
    daily_records: List[DailyAttendance] = field(default_factory=list)


@dataclass
class AttendanceParseResult:
    """差勤解析結果"""
    success: bool
    year: int
    month: int
    department: str
    employees: List[EmployeeAttendanceSummary] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    total_employees: int = 0
    full_attendance_count: int = 0
    total_r_shifts: int = 0
    total_national_holidays: int = 0
    total_overtime_days: int = 0


class AttendanceSheetParser:
    """
    差勤班表解析服務

    整合班表解析、全勤判定、R班判定、延長工時判定，
    提供統一的差勤資料結構。
    """

    def __init__(self):
        self.schedule_parser = ScheduleParser()
        self.full_month_detector = get_full_month_detector()
        self.r_shift_detector = get_r_shift_detector()
        self.overtime_detector = get_overtime_detector()

    def _extract_employees_shifts(
        self,
        data: List[List[Any]],
        year: int,
        month: int,
        warnings: List[str]
    ) -> Dict[str, dict]:
        """
        從原始班表資料提取員工班別

        Args:
            data: Google Sheets 原始資料
            year: 年份
            month: 月份
            warnings: 警告列表

        Returns:
            員工編號到資料的字典
        """
        employees = {}
        _, days_in_month = monthrange(year, month)

        # 找表頭列（使用別名常量進行匹配）
        header_row_idx = -1
        all_aliases = EMPLOYEE_ID_COLUMN_ALIASES + EMPLOYEE_NAME_COLUMN_ALIASES
        for i, row in enumerate(data):
            if not row:
                continue
            row_str = str(row).lower()
            if any(alias.lower() in row_str for alias in all_aliases):
                header_row_idx = i
                break

        if header_row_idx == -1:
            warnings.append("找不到表頭列")
            return employees

        header_row = data[header_row_idx]

        # 找關鍵欄位（使用別名常量進行匹配）
        emp_id_col = -1
        name_col = -1
        date_start_col = -1

        for i, cell in enumerate(header_row):
            cell_str = str(cell).strip()
            # 員工編號欄位匹配
            if any(alias in cell_str or cell_str == alias for alias in EMPLOYEE_ID_COLUMN_ALIASES):
                emp_id_col = i
            # 員工姓名欄位匹配
            elif any(alias in cell_str or cell_str == alias for alias in EMPLOYEE_NAME_COLUMN_ALIASES):
                name_col = i
            # 日期欄位（數字 1-31）
            elif cell_str.isdigit() and 1 <= int(cell_str) <= 31:
                if date_start_col == -1:
                    date_start_col = i

        if emp_id_col == -1:
            warnings.append("找不到員工編號欄位")
            return employees

        if date_start_col == -1:
            warnings.append("找不到日期欄位")
            return employees

        # 解析每列
        for row_idx in range(header_row_idx + 1, len(data)):
            row = data[row_idx]

            if not row or len(row) <= emp_id_col:
                continue

            employee_id = str(row[emp_id_col]).strip()
            if not employee_id:
                continue

            employee_name = ""
            if name_col != -1 and len(row) > name_col:
                employee_name = str(row[name_col]).strip()

            # 提取班別列表
            shifts = []
            for day in range(1, days_in_month + 1):
                col_idx = date_start_col + day - 1
                if col_idx < len(row):
                    shifts.append(row[col_idx])
                else:
                    shifts.append(None)

            employees[employee_id] = {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "shifts": shifts
            }

        return employees

    def parse(
        self,
        data: List[List[Any]],
        department: str,
        year: int,
        month: int
    ) -> AttendanceParseResult:
        """
        解析差勤班表

        Args:
            data: Google Sheets 讀取的原始資料
            department: 部門
            year: 年份
            month: 月份

        Returns:
            AttendanceParseResult: 差勤解析結果
        """
        result = AttendanceParseResult(
            success=False,
            year=year,
            month=month,
            department=department
        )

        if not data:
            result.errors.append("班表資料為空")
            return result

        logger.info(
            "開始解析差勤班表",
            department=department,
            year=year,
            month=month,
            rows=len(data)
        )

        # 提取員工班別資料
        employees_data = self._extract_employees_shifts(
            data, year, month, result.warnings
        )

        if not employees_data:
            result.errors.append("無法解析任何員工資料")
            return result

        result.total_employees = len(employees_data)

        # 轉換為列表格式
        emp_list = list(employees_data.values())

        # 全勤判定
        full_month_results = self.full_month_detector.detect_batch(emp_list)
        full_month_map = {r.employee_id: r for r in full_month_results}

        # R班判定
        r_shift_results = self.r_shift_detector.detect_batch(
            emp_list, year, month
        )
        r_shift_map = {r.employee_id: r for r in r_shift_results}

        # 延長工時判定
        overtime_results = self.overtime_detector.detect_batch(
            emp_list, year, month
        )
        overtime_map = {r.employee_id: r for r in overtime_results}

        # 組合結果
        for emp_id, emp_data in employees_data.items():
            full_month = full_month_map.get(emp_id)
            r_shift = r_shift_map.get(emp_id)
            overtime = overtime_map.get(emp_id)

            summary = EmployeeAttendanceSummary(
                employee_id=emp_id,
                employee_name=emp_data["employee_name"],
                year=year,
                month=month,
                is_full_attendance=full_month.is_full_attendance if full_month else False,
                leave_dates=full_month.leave_dates if full_month else [],
                r_shift_records=r_shift.records if r_shift else [],
                overtime_records=overtime.records if overtime else []
            )

            result.employees.append(summary)

            # 累計統計
            if summary.is_full_attendance:
                result.full_attendance_count += 1
            result.total_r_shifts += len(summary.r_shift_records)
            result.total_national_holidays += sum(
                1 for r in summary.r_shift_records if r.is_national_holiday
            )
            result.total_overtime_days += len(summary.overtime_records)

        result.success = True

        logger.info(
            "差勤班表解析完成",
            department=department,
            year=year,
            month=month,
            total_employees=result.total_employees,
            full_attendance_count=result.full_attendance_count,
            total_r_shifts=result.total_r_shifts,
            total_national_holidays=result.total_national_holidays,
            total_overtime_days=result.total_overtime_days
        )

        return result


# 單例
_parser_instance: Optional[AttendanceSheetParser] = None


def get_attendance_sheet_parser() -> AttendanceSheetParser:
    """取得差勤班表解析器實例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = AttendanceSheetParser()
    return _parser_instance
