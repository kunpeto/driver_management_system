"""
SystemSettingService 系統設定服務
對應 tasks.md T036: 實作 SystemSettingService
"""

from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.system_setting import DepartmentScope, SettingKeys, SystemSetting


class SystemSettingServiceError(Exception):
    """系統設定服務錯誤"""
    pass


class DuplicateSettingError(SystemSettingServiceError):
    """設定鍵名重複錯誤"""
    pass


class SettingNotFoundError(SystemSettingServiceError):
    """設定不存在錯誤"""
    pass


class SystemSettingService:
    """
    系統設定服務

    提供系統設定的 CRUD 操作與部門篩選功能。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db

    # ============================================================
    # CRUD 操作
    # ============================================================

    def create(
        self,
        key: str,
        value: Optional[str] = None,
        department: Optional[str] = None,
        description: Optional[str] = None
    ) -> SystemSetting:
        """
        建立新設定

        Args:
            key: 設定鍵名
            value: 設定值
            department: 部門範圍 ('淡海', '安坑', 'global', None)
            description: 設定說明

        Returns:
            SystemSetting: 新建立的設定

        Raises:
            DuplicateSettingError: 當 (key, department) 組合已存在
        """
        setting = SystemSetting(
            key=key,
            value=value,
            department=department,
            description=description
        )

        try:
            self.db.add(setting)
            self.db.commit()
            self.db.refresh(setting)
            return setting
        except IntegrityError:
            self.db.rollback()
            raise DuplicateSettingError(
                f"設定 '{key}' 在部門 '{department}' 已存在"
            )

    def get_by_id(self, setting_id: int) -> Optional[SystemSetting]:
        """
        根據 ID 取得設定

        Args:
            setting_id: 設定 ID

        Returns:
            SystemSetting 或 None
        """
        return self.db.query(SystemSetting).filter(
            SystemSetting.id == setting_id
        ).first()

    def get_by_key(
        self,
        key: str,
        department: Optional[str] = None
    ) -> Optional[SystemSetting]:
        """
        根據鍵名與部門取得設定

        Args:
            key: 設定鍵名
            department: 部門範圍

        Returns:
            SystemSetting 或 None
        """
        query = self.db.query(SystemSetting).filter(SystemSetting.key == key)

        if department is None:
            query = query.filter(SystemSetting.department.is_(None))
        else:
            query = query.filter(SystemSetting.department == department)

        return query.first()

    def get_value(
        self,
        key: str,
        department: Optional[str] = None,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        取得設定值（便捷方法）

        優先順序：
        1. 指定部門的設定
        2. global 設定
        3. 預設值

        Args:
            key: 設定鍵名
            department: 部門範圍
            default: 預設值

        Returns:
            設定值或預設值
        """
        # 先查詢指定部門
        setting = self.get_by_key(key, department)
        if setting and setting.value is not None:
            return setting.value

        # 再查詢 global
        if department != DepartmentScope.GLOBAL.value:
            setting = self.get_by_key(key, DepartmentScope.GLOBAL.value)
            if setting and setting.value is not None:
                return setting.value

        return default

    def update(
        self,
        setting_id: int,
        value: Optional[str] = None,
        description: Optional[str] = None
    ) -> SystemSetting:
        """
        更新設定

        Args:
            setting_id: 設定 ID
            value: 新的設定值
            description: 新的設定說明

        Returns:
            SystemSetting: 更新後的設定

        Raises:
            SettingNotFoundError: 當設定不存在
        """
        setting = self.get_by_id(setting_id)
        if not setting:
            raise SettingNotFoundError(f"設定 ID {setting_id} 不存在")

        if value is not None:
            setting.value = value
        if description is not None:
            setting.description = description

        self.db.commit()
        self.db.refresh(setting)
        return setting

    def upsert(
        self,
        key: str,
        value: Optional[str] = None,
        department: Optional[str] = None,
        description: Optional[str] = None
    ) -> SystemSetting:
        """
        更新或建立設定

        Args:
            key: 設定鍵名
            value: 設定值
            department: 部門範圍
            description: 設定說明

        Returns:
            SystemSetting: 更新或新建的設定
        """
        setting = self.get_by_key(key, department)

        if setting:
            if value is not None:
                setting.value = value
            if description is not None:
                setting.description = description
            self.db.commit()
            self.db.refresh(setting)
            return setting
        else:
            return self.create(key, value, department, description)

    def delete(self, setting_id: int) -> bool:
        """
        刪除設定

        Args:
            setting_id: 設定 ID

        Returns:
            bool: 是否成功刪除

        Raises:
            SettingNotFoundError: 當設定不存在
        """
        setting = self.get_by_id(setting_id)
        if not setting:
            raise SettingNotFoundError(f"設定 ID {setting_id} 不存在")

        self.db.delete(setting)
        self.db.commit()
        return True

    # ============================================================
    # 查詢操作
    # ============================================================

    def list_all(self) -> list[SystemSetting]:
        """
        列出所有設定

        Returns:
            list[SystemSetting]: 所有設定列表
        """
        return self.db.query(SystemSetting).order_by(
            SystemSetting.department,
            SystemSetting.key
        ).all()

    def list_by_department(
        self,
        department: str,
        include_global: bool = True
    ) -> list[SystemSetting]:
        """
        列出指定部門的設定

        Args:
            department: 部門範圍 ('淡海', '安坑')
            include_global: 是否包含 global 設定

        Returns:
            list[SystemSetting]: 設定列表
        """
        if include_global:
            query = self.db.query(SystemSetting).filter(
                or_(
                    SystemSetting.department == department,
                    SystemSetting.department == DepartmentScope.GLOBAL.value
                )
            )
        else:
            query = self.db.query(SystemSetting).filter(
                SystemSetting.department == department
            )

        return query.order_by(SystemSetting.key).all()

    def list_by_key_prefix(self, prefix: str) -> list[SystemSetting]:
        """
        根據鍵名前綴列出設定

        Args:
            prefix: 鍵名前綴

        Returns:
            list[SystemSetting]: 設定列表
        """
        return self.db.query(SystemSetting).filter(
            SystemSetting.key.startswith(prefix)
        ).order_by(
            SystemSetting.department,
            SystemSetting.key
        ).all()

    # ============================================================
    # 便捷方法
    # ============================================================

    def get_google_sheets_id(self, department: str) -> Optional[str]:
        """取得指定部門的 Google Sheets ID"""
        return self.get_value(SettingKeys.GOOGLE_SHEETS_ID, department)

    def get_google_drive_folder_id(self, department: str) -> Optional[str]:
        """取得指定部門的 Google Drive 資料夾 ID"""
        return self.get_value(SettingKeys.GOOGLE_DRIVE_FOLDER_ID, department)

    def get_assessment_coefficient(self) -> float:
        """取得考核累計加重係數"""
        value = self.get_value(
            SettingKeys.ASSESSMENT_ACCUMULATION_COEFFICIENT,
            DepartmentScope.GLOBAL.value,
            default="0.5"
        )
        return float(value)

    def set_google_sheets_id(self, department: str, sheets_id: str) -> SystemSetting:
        """設定指定部門的 Google Sheets ID"""
        return self.upsert(
            key=SettingKeys.GOOGLE_SHEETS_ID,
            value=sheets_id,
            department=department,
            description=f"{department} 班表 Google Sheets ID"
        )

    def set_google_drive_folder_id(self, department: str, folder_id: str) -> SystemSetting:
        """設定指定部門的 Google Drive 資料夾 ID"""
        return self.upsert(
            key=SettingKeys.GOOGLE_DRIVE_FOLDER_ID,
            value=folder_id,
            department=department,
            description=f"{department} Google Drive 資料夾 ID"
        )

    # ============================================================
    # 批次操作
    # ============================================================

    def bulk_upsert(self, settings: list[dict]) -> list[SystemSetting]:
        """
        批次更新或建立設定

        Args:
            settings: 設定列表，每個元素包含 key, value, department, description

        Returns:
            list[SystemSetting]: 更新或新建的設定列表
        """
        results = []
        for s in settings:
            result = self.upsert(
                key=s.get("key"),
                value=s.get("value"),
                department=s.get("department"),
                description=s.get("description")
            )
            results.append(result)
        return results

    def get_department_config(self, department: str) -> dict:
        """
        取得部門完整配置

        Args:
            department: 部門名稱

        Returns:
            dict: 部門配置字典
        """
        settings = self.list_by_department(department, include_global=True)

        config = {}
        for setting in settings:
            config[setting.key] = {
                "value": setting.value,
                "department": setting.department,
                "description": setting.description
            }

        return config
