"""
FileNaming 檔案命名工具
對應 tasks.md T139: 實作檔案命名工具
對應 spec.md: User Story 8 - Office 文件命名規則

命名規則：
- 事件調查/人員訪談/矯正措施：類型-YYYYMMDD_車號_地點_姓名.docx
- 考核加扣分：類型_YYYYMMDD_姓名.docx
"""

import re
from datetime import date
from typing import Optional


class FileNaming:
    """
    檔案命名工具

    根據履歷類型與資料生成規範的檔案名稱。
    """

    # 類型中文名稱對應
    TYPE_NAMES = {
        "basic": "基本履歷",
        "event_investigation": "事件調查紀錄表",
        "personnel_interview": "人員訪談紀錄表",
        "corrective_measures": "事件矯正措施紀錄表",
        "assessment_notice": "考核通知單",
    }

    # 考核通知細分名稱
    ASSESSMENT_TYPE_NAMES = {
        "加分": "考核加分通知單",
        "扣分": "考核扣分通知單",
    }

    @classmethod
    def generate(
        cls,
        profile_type: str,
        event_date: date,
        employee_name: str,
        train_number: Optional[str] = None,
        event_location: Optional[str] = None,
        assessment_type: Optional[str] = None,
        extension: str = "docx"
    ) -> str:
        """
        生成檔案名稱

        規則：
        - 事件調查/人員訪談/矯正措施：類型-YYYYMMDD_車號_地點_姓名.docx
        - 考核加扣分：類型_YYYYMMDD_姓名.docx

        Args:
            profile_type: 履歷類型
            event_date: 事件日期
            employee_name: 員工姓名
            train_number: 列車車號
            event_location: 事件地點
            assessment_type: 考核類型（加分/扣分）
            extension: 副檔名

        Returns:
            檔案名稱

        Examples:
            >>> FileNaming.generate("event_investigation", date(2026, 1, 15),
            ...     "張三", "1234", "淡水站")
            '事件調查紀錄表-20260115_1234_淡水站_張三.docx'

            >>> FileNaming.generate("assessment_notice", date(2026, 1, 15),
            ...     "張三", assessment_type="加分")
            '考核加分通知單_20260115_張三.docx'
        """
        # 格式化日期
        date_str = event_date.strftime("%Y%m%d")

        # 清理檔案名稱中的非法字元
        employee_name = cls._sanitize(employee_name)
        train_number = cls._sanitize(train_number) if train_number else None
        event_location = cls._sanitize(event_location) if event_location else None

        # 取得類型名稱
        if profile_type == "assessment_notice" and assessment_type:
            type_name = cls.ASSESSMENT_TYPE_NAMES.get(
                assessment_type,
                cls.TYPE_NAMES.get(profile_type)
            )
        else:
            type_name = cls.TYPE_NAMES.get(profile_type, "履歷")

        # 根據類型生成不同格式的檔名
        if profile_type == "assessment_notice":
            # 考核通知單：類型_YYYYMMDD_姓名.docx
            filename = f"{type_name}_{date_str}_{employee_name}.{extension}"
        else:
            # 其他類型：類型-YYYYMMDD_車號_地點_姓名.docx
            parts = [type_name, date_str]

            if train_number:
                parts.append(train_number)

            if event_location:
                parts.append(event_location)

            parts.append(employee_name)

            # 第一個分隔符用 "-"，其餘用 "_"
            filename = f"{parts[0]}-{'_'.join(parts[1:])}.{extension}"

        return filename

    @classmethod
    def _sanitize(cls, text: Optional[str]) -> str:
        """
        清理檔案名稱中的非法字元

        Args:
            text: 原始文字

        Returns:
            清理後的文字
        """
        if not text:
            return ""

        # 移除 Windows 檔案名稱非法字元
        illegal_chars = r'[<>:"/\\|?*]'
        text = re.sub(illegal_chars, "", text)

        # 移除前後空白
        text = text.strip()

        # 將連續空白替換為單一底線
        text = re.sub(r'\s+', "_", text)

        return text

    @classmethod
    def generate_with_version(
        cls,
        profile_type: str,
        event_date: date,
        employee_name: str,
        version: int,
        train_number: Optional[str] = None,
        event_location: Optional[str] = None,
        assessment_type: Optional[str] = None,
        extension: str = "docx"
    ) -> str:
        """
        生成帶版本號的檔案名稱

        Args:
            profile_type: 履歷類型
            event_date: 事件日期
            employee_name: 員工姓名
            version: 版本號
            train_number: 列車車號
            event_location: 事件地點
            assessment_type: 考核類型
            extension: 副檔名

        Returns:
            檔案名稱（含版本號）

        Examples:
            >>> FileNaming.generate_with_version("event_investigation",
            ...     date(2026, 1, 15), "張三", 2, "1234", "淡水站")
            '事件調查紀錄表-20260115_1234_淡水站_張三_v2.docx'
        """
        base_name = cls.generate(
            profile_type=profile_type,
            event_date=event_date,
            employee_name=employee_name,
            train_number=train_number,
            event_location=event_location,
            assessment_type=assessment_type,
            extension=""
        )

        # 移除原本的副檔名部分
        if base_name.endswith("."):
            base_name = base_name[:-1]

        return f"{base_name}_v{version}.{extension}"

    @classmethod
    def get_type_name(
        cls,
        profile_type: str,
        assessment_type: Optional[str] = None
    ) -> str:
        """
        取得類型中文名稱

        Args:
            profile_type: 履歷類型
            assessment_type: 考核類型

        Returns:
            中文名稱
        """
        if profile_type == "assessment_notice" and assessment_type:
            return cls.ASSESSMENT_TYPE_NAMES.get(
                assessment_type,
                cls.TYPE_NAMES.get(profile_type, "履歷")
            )
        return cls.TYPE_NAMES.get(profile_type, "履歷")
