"""
員工編號解析工具
對應 tasks.md T045: 實作員工編號解析工具

功能：
- 從員工編號解析入職年月（如 1011M0095 → 2021-11）
- 驗證員工編號格式
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmployeeIdInfo:
    """員工編號解析結果"""
    valid: bool
    employee_id: str
    hire_year: Optional[int] = None
    hire_month: Optional[int] = None
    hire_year_month: Optional[str] = None
    employee_type: Optional[str] = None
    sequence_number: Optional[str] = None
    error: Optional[str] = None


class EmployeeIdParser:
    """
    員工編號解析器

    員工編號格式：YYMM + 類型碼 + 序號
    例如：1011M0095
    - 10: 民國年 (民國 101 年 = 西元 2012 年)
    - 11: 月份 (11 月)
    - M: 類型碼 (M = 司機員)
    - 0095: 序號

    注意：民國年的判斷邏輯：
    - 00-30: 假設為民國 100-130 年 (西元 2011-2041 年)
    - 31-99: 假設為民國 31-99 年 (西元 1942-2010 年)
    """

    # 員工編號正則表達式
    # 格式: YYMM + 1個英文字母 + 4位數字
    PATTERN = re.compile(r"^(\d{2})(\d{2})([A-Za-z])(\d{4})$")

    # 類型碼對照
    TYPE_CODES = {
        "M": "司機員",
        "S": "站務員",
        "A": "行政人員",
        "T": "技術人員",
    }

    @classmethod
    def parse(cls, employee_id: str) -> EmployeeIdInfo:
        """
        解析員工編號

        Args:
            employee_id: 員工編號字串

        Returns:
            EmployeeIdInfo: 解析結果
        """
        if not employee_id:
            return EmployeeIdInfo(
                valid=False,
                employee_id=employee_id or "",
                error="員工編號不能為空"
            )

        # 移除空白並轉大寫
        employee_id = employee_id.strip().upper()

        # 正則匹配
        match = cls.PATTERN.match(employee_id)
        if not match:
            return EmployeeIdInfo(
                valid=False,
                employee_id=employee_id,
                error="員工編號格式錯誤，應為 YYMM + 類型碼 + 4位序號（如 1011M0095）"
            )

        year_part, month_part, type_code, sequence = match.groups()

        # 解析年份（民國轉西元）
        roc_year = int(year_part)
        if roc_year <= 30:
            # 00-30 假設為民國 100-130 年
            roc_year += 100
        # 民國年 + 1911 = 西元年
        western_year = roc_year + 1911

        # 解析月份
        month = int(month_part)
        if month < 1 or month > 12:
            return EmployeeIdInfo(
                valid=False,
                employee_id=employee_id,
                error=f"月份無效：{month_part}，應為 01-12"
            )

        # 格式化入職年月
        hire_year_month = f"{western_year}-{month:02d}"

        return EmployeeIdInfo(
            valid=True,
            employee_id=employee_id,
            hire_year=western_year,
            hire_month=month,
            hire_year_month=hire_year_month,
            employee_type=cls.TYPE_CODES.get(type_code, "未知"),
            sequence_number=sequence
        )

    @classmethod
    def validate(cls, employee_id: str) -> bool:
        """
        驗證員工編號格式

        Args:
            employee_id: 員工編號字串

        Returns:
            bool: 是否有效
        """
        result = cls.parse(employee_id)
        return result.valid

    @classmethod
    def get_hire_year_month(cls, employee_id: str) -> Optional[str]:
        """
        取得入職年月

        Args:
            employee_id: 員工編號字串

        Returns:
            str 或 None: 入職年月（格式：YYYY-MM）
        """
        result = cls.parse(employee_id)
        return result.hire_year_month if result.valid else None

    @classmethod
    def get_hire_date_display(cls, employee_id: str) -> Optional[str]:
        """
        取得入職日期顯示格式

        Args:
            employee_id: 員工編號字串

        Returns:
            str 或 None: 入職年月（格式：YYYY/MM）
        """
        result = cls.parse(employee_id)
        if result.valid and result.hire_year and result.hire_month:
            return f"{result.hire_year}/{result.hire_month:02d}"
        return None


# 便捷函數
def parse_employee_id(employee_id: str) -> EmployeeIdInfo:
    """解析員工編號"""
    return EmployeeIdParser.parse(employee_id)


def validate_employee_id(employee_id: str) -> bool:
    """驗證員工編號格式"""
    return EmployeeIdParser.validate(employee_id)


def get_hire_year_month(employee_id: str) -> Optional[str]:
    """從員工編號取得入職年月"""
    return EmployeeIdParser.get_hire_year_month(employee_id)
