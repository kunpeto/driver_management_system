"""
班表解析服務
對應 tasks.md T081: 實作班表解析服務

功能：
- 解析 Google Sheets 班表資料格式
- 識別員工編號、姓名、班別
- 解析班別代碼（早班、中班、晚班、R班、休假等）
- 處理延長工時標記
"""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Any
from calendar import monthrange

from src.utils.logger import logger


@dataclass
class ParsedShift:
    """解析後的單一班別"""
    employee_id: str
    employee_name: str
    schedule_date: date
    shift_code: str
    shift_type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    overtime_hours: Optional[int] = None
    is_r_shift: bool = False
    is_leave: bool = False
    notes: Optional[str] = None


@dataclass
class ParseResult:
    """解析結果"""
    success: bool
    shifts: List[ParsedShift] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    total_rows: int = 0
    parsed_rows: int = 0
    skipped_rows: int = 0


class ScheduleParser:
    """
    班表解析服務

    解析從 Google Sheets 讀取的班表資料，
    將其轉換為結構化的班別記錄。
    """

    # 班別時間對照表（班別代碼 -> (開始時間, 結束時間)）
    SHIFT_TIME_MAP = {
        # 早班系列
        "0500G": ("05:00", "13:30"),
        "0530G": ("05:30", "14:00"),
        "0600G": ("06:00", "14:30"),
        "0630G": ("06:30", "15:00"),
        "0700G": ("07:00", "15:30"),
        "0730G": ("07:30", "16:00"),
        "0800G": ("08:00", "16:30"),
        # 中班系列
        "0900G": ("09:00", "17:30"),
        "0930G": ("09:30", "18:00"),
        "1000G": ("10:00", "18:30"),
        "1100G": ("11:00", "19:30"),
        "1200G": ("12:00", "20:30"),
        "1300G": ("13:00", "21:30"),
        # 晚班系列
        "1400G": ("14:00", "22:30"),
        "1500G": ("15:00", "23:30"),
        "1600G": ("16:00", "00:30"),
        "1700G": ("17:00", "01:30"),
        "1800G": ("18:00", "02:30"),
    }

    # 休假類型
    LEAVE_PATTERNS = ["(假)", "(特)", "(公)", "(婚)", "(喪)", "(病)", "(事)"]

    # Gemini Review Fix: 員工編號正則更彈性
    # 支援格式：1011M0095, 0912F0001, A123, 員工001 等
    EMPLOYEE_ID_PATTERN = re.compile(r"^[A-Za-z0-9\u4e00-\u9fff]+$")

    # 班別代碼正則
    SHIFT_CODE_PATTERN = re.compile(r"^(\d{4})([GDAR]?)$")

    # R班正則（R/0905G, R(國)/0905G）
    R_SHIFT_PATTERN = re.compile(r"^R(\(國\))?/(.+)$")

    # 延長工時正則（+1, +2, +3, +4）
    OVERTIME_PATTERN = re.compile(r"\(\+(\d)\)")

    def __init__(self):
        pass

    def _classify_shift_type(self, shift_code: str) -> str:
        """
        分類班別類型

        Args:
            shift_code: 班別代碼

        Returns:
            str: 班別類型（早班/中班/晚班/R班/休假/其他）
        """
        # 檢查休假
        for leave in self.LEAVE_PATTERNS:
            if leave in shift_code:
                return "休假"

        # 檢查 R班
        if shift_code.startswith("R/") or shift_code.startswith("R("):
            return "R班"

        # 解析時間判斷早中晚班
        match = self.SHIFT_CODE_PATTERN.match(shift_code.replace("R/", "").replace("R(國)/", ""))
        if match:
            time_str = match.group(1)
            hour = int(time_str[:2])

            if 5 <= hour < 9:
                return "早班"
            elif 9 <= hour < 14:
                return "中班"
            elif 14 <= hour < 24:
                return "晚班"

        # 其他特殊班別
        special_codes = ["站", "訓", "借", "支", "測"]
        for code in special_codes:
            if code in shift_code:
                return "其他"

        return "其他"

    def _parse_shift_time(self, shift_code: str) -> tuple[Optional[str], Optional[str]]:
        """
        解析班別的開始和結束時間

        Args:
            shift_code: 班別代碼

        Returns:
            tuple: (開始時間, 結束時間)
        """
        # 移除 R/ 前綴
        clean_code = shift_code
        if clean_code.startswith("R/"):
            clean_code = clean_code[2:]
        elif clean_code.startswith("R(國)/"):
            clean_code = clean_code[5:]

        # 移除延長工時標記
        clean_code = self.OVERTIME_PATTERN.sub("", clean_code)

        # 查詢時間對照表
        if clean_code in self.SHIFT_TIME_MAP:
            return self.SHIFT_TIME_MAP[clean_code]

        # 嘗試從代碼解析
        match = self.SHIFT_CODE_PATTERN.match(clean_code)
        if match:
            time_str = match.group(1)
            try:
                hour = int(time_str[:2])
                minute = int(time_str[2:])
                start_time = f"{hour:02d}:{minute:02d}"
                # 預設工時 8.5 小時
                end_hour = (hour + 8) % 24
                end_minute = (minute + 30) % 60
                if minute + 30 >= 60:
                    end_hour = (end_hour + 1) % 24
                end_time = f"{end_hour:02d}:{end_minute:02d}"
                return (start_time, end_time)
            except (ValueError, IndexError):
                pass

        return (None, None)

    def _parse_overtime(self, shift_code: str) -> Optional[int]:
        """
        解析延長工時

        Args:
            shift_code: 班別代碼

        Returns:
            int: 延長工時小時數，無則返回 None
        """
        match = self.OVERTIME_PATTERN.search(shift_code)
        if match:
            return int(match.group(1))
        return None

    def _find_header_row(self, data: List[List[Any]]) -> int:
        """
        找到表頭列

        Args:
            data: 原始資料

        Returns:
            int: 表頭列索引，找不到返回 -1
        """
        for i, row in enumerate(data):
            if not row:
                continue
            row_str = str(row).lower()
            # 尋找包含「編號」或「姓名」的列
            if "編號" in row_str or "員工" in row_str or "姓名" in row_str:
                return i
        return -1

    def _find_column_indices(
        self,
        header_row: List[Any],
        warnings: List[str]
    ) -> tuple[int, int, int]:
        """
        找到關鍵欄位的索引

        Gemini Review Fix: 增加 warnings 參數，記錄 header 驗證問題

        Args:
            header_row: 表頭列
            warnings: 警告列表（會被修改）

        Returns:
            tuple: (員工編號欄位, 姓名欄位, 日期起始欄位)
        """
        employee_id_col = -1
        name_col = -1
        date_start_col = -1

        # Gemini Review Fix: 驗證 header_row 是否足夠長
        if len(header_row) < 3:
            warnings.append(f"表頭列欄位數不足（只有 {len(header_row)} 欄），可能格式錯誤")

        for i, cell in enumerate(header_row):
            cell_str = str(cell).strip()

            if "編號" in cell_str or cell_str == "員編":
                employee_id_col = i
            elif "姓名" in cell_str or cell_str == "姓名":
                name_col = i
            elif cell_str.isdigit() and 1 <= int(cell_str) <= 31:
                # 找到第一個日期欄位（1, 2, 3...）
                if date_start_col == -1:
                    date_start_col = i

        # Gemini Review Fix: 記錄缺少的欄位警告
        if name_col == -1:
            warnings.append("找不到姓名欄位，員工姓名將為空")

        return (employee_id_col, name_col, date_start_col)

    def parse(
        self,
        data: List[List[Any]],
        department: str,
        year: int,
        month: int
    ) -> ParseResult:
        """
        解析班表資料

        Args:
            data: Google Sheets 讀取的原始資料
            department: 部門
            year: 年份
            month: 月份

        Returns:
            ParseResult: 解析結果
        """
        result = ParseResult(success=False, total_rows=len(data))

        if not data:
            result.errors.append("班表資料為空")
            return result

        # 找到表頭列
        header_row_idx = self._find_header_row(data)
        if header_row_idx == -1:
            result.errors.append("找不到表頭列（需包含「編號」或「姓名」）")
            return result

        header_row = data[header_row_idx]

        # Gemini Review Fix: 驗證 header 並收集警告
        # 找到關鍵欄位（同時記錄警告）
        emp_id_col, name_col, date_start_col = self._find_column_indices(
            header_row, result.warnings
        )

        if emp_id_col == -1:
            result.errors.append("找不到員工編號欄位")
            return result

        if date_start_col == -1:
            result.errors.append("找不到日期欄位")
            return result

        # 取得該月天數
        _, days_in_month = monthrange(year, month)

        logger.info(
            "開始解析班表",
            department=department,
            year=year,
            month=month,
            header_row=header_row_idx,
            emp_id_col=emp_id_col,
            date_start_col=date_start_col,
            days_in_month=days_in_month
        )

        # 解析每一列資料
        for row_idx in range(header_row_idx + 1, len(data)):
            row = data[row_idx]

            if not row or len(row) <= emp_id_col:
                result.skipped_rows += 1
                continue

            # 取得員工編號
            employee_id = str(row[emp_id_col]).strip()
            if not employee_id or employee_id == "":
                result.skipped_rows += 1
                continue

            # 取得員工姓名
            employee_name = ""
            if name_col != -1 and len(row) > name_col:
                employee_name = str(row[name_col]).strip()

            # 解析每天的班別
            for day in range(1, days_in_month + 1):
                col_idx = date_start_col + day - 1

                if col_idx >= len(row):
                    continue

                shift_code = str(row[col_idx]).strip()
                if not shift_code or shift_code == "":
                    continue

                try:
                    schedule_date = date(year, month, day)

                    # 解析班別資訊
                    shift_type = self._classify_shift_type(shift_code)
                    start_time, end_time = self._parse_shift_time(shift_code)
                    overtime_hours = self._parse_overtime(shift_code)
                    is_r_shift = shift_code.startswith("R/") or shift_code.startswith("R(")
                    is_leave = any(leave in shift_code for leave in self.LEAVE_PATTERNS)

                    parsed_shift = ParsedShift(
                        employee_id=employee_id,
                        employee_name=employee_name,
                        schedule_date=schedule_date,
                        shift_code=shift_code,
                        shift_type=shift_type,
                        start_time=start_time,
                        end_time=end_time,
                        overtime_hours=overtime_hours,
                        is_r_shift=is_r_shift,
                        is_leave=is_leave
                    )

                    result.shifts.append(parsed_shift)

                except Exception as e:
                    result.warnings.append(
                        f"第 {row_idx + 1} 列第 {day} 日解析失敗: {str(e)}"
                    )

            result.parsed_rows += 1

        result.success = len(result.shifts) > 0

        logger.info(
            "班表解析完成",
            department=department,
            year=year,
            month=month,
            total_shifts=len(result.shifts),
            parsed_rows=result.parsed_rows,
            skipped_rows=result.skipped_rows,
            warnings=len(result.warnings)
        )

        return result

    def parse_single_cell(self, shift_code: str) -> dict:
        """
        解析單一班別儲存格

        Args:
            shift_code: 班別代碼

        Returns:
            dict: 解析結果
        """
        shift_type = self._classify_shift_type(shift_code)
        start_time, end_time = self._parse_shift_time(shift_code)
        overtime_hours = self._parse_overtime(shift_code)

        return {
            "shift_code": shift_code,
            "shift_type": shift_type,
            "start_time": start_time,
            "end_time": end_time,
            "overtime_hours": overtime_hours,
            "is_r_shift": shift_code.startswith("R/") or shift_code.startswith("R("),
            "is_leave": any(leave in shift_code for leave in self.LEAVE_PATTERNS)
        }


# 單例實例
_parser_instance: Optional[ScheduleParser] = None


def get_schedule_parser() -> ScheduleParser:
    """取得班表解析器實例（單例）"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ScheduleParser()
    return _parser_instance
