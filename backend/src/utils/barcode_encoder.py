"""
BarcodeEncoder 條碼編碼工具
對應 tasks.md T138: 實作條碼編碼工具
對應 spec.md: User Story 8 - 條碼編碼格式

條碼編碼格式（Gemini Review 建議加入版本號）：
{profile_id}|{type_code}|{YYYYMM}|V{version:02d}

範例：12345|EI|202601|V01
"""

from datetime import date
from typing import Optional


class BarcodeEncoder:
    """
    條碼編碼工具

    生成符合規範的條碼編碼字串。
    """

    # 類型代碼對應
    TYPE_CODES = {
        "basic": "BA",
        "event_investigation": "EI",
        "personnel_interview": "PI",
        "corrective_measures": "CM",
        "assessment_notice": "AN",  # 通用，下面有加分/扣分細分
    }

    # 考核通知細分代碼
    ASSESSMENT_TYPE_CODES = {
        "加分": "AA",  # Assessment Add
        "扣分": "AD",  # Assessment Deduct
    }

    @classmethod
    def encode(
        cls,
        profile_id: int,
        profile_type: str,
        generate_date: Optional[date] = None,
        version: int = 1,
        assessment_type: Optional[str] = None
    ) -> str:
        """
        生成條碼編碼

        格式：{profile_id}|{type_code}|{YYYYMM}|V{version:02d}

        Args:
            profile_id: 履歷 ID
            profile_type: 履歷類型
            generate_date: 生成日期（預設為今天）
            version: 版本號
            assessment_type: 考核類型（加分/扣分，僅 assessment_notice 使用）

        Returns:
            條碼編碼字串

        Examples:
            >>> BarcodeEncoder.encode(12345, "event_investigation", date(2026, 1, 15), 1)
            '12345|EI|202601|V01'
            >>> BarcodeEncoder.encode(12345, "assessment_notice", date(2026, 1, 15), 1, "加分")
            '12345|AA|202601|V01'
        """
        if generate_date is None:
            generate_date = date.today()

        # 決定類型代碼
        if profile_type == "assessment_notice" and assessment_type:
            type_code = cls.ASSESSMENT_TYPE_CODES.get(assessment_type, "AN")
        else:
            type_code = cls.TYPE_CODES.get(profile_type, "XX")

        # 格式化年月
        year_month = generate_date.strftime("%Y%m")

        # 格式化版本號
        version_str = f"V{version:02d}"

        return f"{profile_id}|{type_code}|{year_month}|{version_str}"

    @classmethod
    def decode(cls, barcode: str) -> dict:
        """
        解析條碼編碼

        Args:
            barcode: 條碼編碼字串

        Returns:
            解析結果字典

        Raises:
            ValueError: 無效的條碼格式
        """
        parts = barcode.split("|")

        if len(parts) != 4:
            raise ValueError(f"無效的條碼格式: {barcode}")

        try:
            profile_id = int(parts[0])
            type_code = parts[1]
            year_month = parts[2]
            version_str = parts[3]

            # 解析年月
            year = int(year_month[:4])
            month = int(year_month[4:])

            # 解析版本號
            if not version_str.startswith("V"):
                raise ValueError(f"無效的版本號格式: {version_str}")
            version = int(version_str[1:])

            # 反向查詢類型
            profile_type = None
            assessment_type = None

            # 先檢查考核通知類型
            for a_type, code in cls.ASSESSMENT_TYPE_CODES.items():
                if code == type_code:
                    profile_type = "assessment_notice"
                    assessment_type = a_type
                    break

            # 再檢查一般類型
            if profile_type is None:
                for p_type, code in cls.TYPE_CODES.items():
                    if code == type_code:
                        profile_type = p_type
                        break

            return {
                "profile_id": profile_id,
                "type_code": type_code,
                "profile_type": profile_type,
                "assessment_type": assessment_type,
                "year": year,
                "month": month,
                "version": version,
            }

        except (ValueError, IndexError) as e:
            raise ValueError(f"無效的條碼格式: {barcode}") from e

    @classmethod
    def get_type_code(
        cls,
        profile_type: str,
        assessment_type: Optional[str] = None
    ) -> str:
        """
        取得類型代碼

        Args:
            profile_type: 履歷類型
            assessment_type: 考核類型

        Returns:
            類型代碼
        """
        if profile_type == "assessment_notice" and assessment_type:
            return cls.ASSESSMENT_TYPE_CODES.get(assessment_type, "AN")
        return cls.TYPE_CODES.get(profile_type, "XX")

    @classmethod
    def get_type_name(cls, type_code: str) -> str:
        """
        取得類型名稱

        Args:
            type_code: 類型代碼

        Returns:
            類型名稱
        """
        type_names = {
            "BA": "基本履歷",
            "EI": "事件調查",
            "PI": "人員訪談",
            "CM": "矯正措施",
            "AN": "考核通知",
            "AA": "考核加分",
            "AD": "考核扣分",
        }
        return type_names.get(type_code, "未知類型")
