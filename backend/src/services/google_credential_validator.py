"""
Google 憑證驗證服務
對應 tasks.md T037: 實作 Google 憑證驗證服務（Dry Run 測試連線）

此模組封裝 CredentialValidator，提供更便捷的憑證驗證介面。
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from src.constants import Department
from src.models.system_setting import SettingKeys
from src.services.credential_validator import (
    CredentialValidator,
    ValidationResult,
    get_credential_validator,
)
from src.services.system_setting_service import SystemSettingService
from src.utils.logger import logger


@dataclass
class DryRunResult:
    """Dry Run 測試結果"""
    success: bool
    sheets_valid: bool = False
    drive_valid: bool = False
    sheets_error: Optional[str] = None
    drive_error: Optional[str] = None
    sheets_details: Optional[dict] = None
    drive_details: Optional[dict] = None


class GoogleCredentialValidator:
    """
    Google 憑證驗證服務

    提供 Dry Run 測試連線功能，整合 SystemSetting 讀取部門配置。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self._validator = get_credential_validator()
        self._setting_service = SystemSettingService(db)

    def validate_service_account(self, base64_json: str) -> ValidationResult:
        """
        驗證 Service Account JSON 格式

        Args:
            base64_json: Base64 編碼的 JSON 字串

        Returns:
            ValidationResult: 驗證結果
        """
        return self._validator.validate_service_account_format(base64_json)

    def test_sheets_connection(
        self,
        base64_json: str,
        spreadsheet_id: str
    ) -> ValidationResult:
        """
        測試 Google Sheets 連線（Dry Run）

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            spreadsheet_id: Google Sheets ID

        Returns:
            ValidationResult: 驗證結果
        """
        logger.info(
            "執行 Sheets 連線測試",
            spreadsheet_id=spreadsheet_id[:20] + "..." if len(spreadsheet_id) > 20 else spreadsheet_id
        )
        return self._validator.test_sheets_access(base64_json, spreadsheet_id)

    def test_drive_connection(
        self,
        base64_json: str,
        folder_id: str
    ) -> ValidationResult:
        """
        測試 Google Drive 連線（Dry Run）

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            folder_id: Google Drive 資料夾 ID

        Returns:
            ValidationResult: 驗證結果
        """
        logger.info(
            "執行 Drive 連線測試",
            folder_id=folder_id[:20] + "..." if len(folder_id) > 20 else folder_id
        )
        return self._validator.test_drive_access(base64_json, folder_id)

    def dry_run_department(
        self,
        department: str,
        base64_json: str,
        sheets_id: Optional[str] = None,
        drive_folder_id: Optional[str] = None
    ) -> DryRunResult:
        """
        執行部門 Dry Run 測試

        測試指定部門的 Google 服務連線。

        Args:
            department: 部門名稱 ('淡海', '安坑')
            base64_json: Base64 編碼的 Service Account JSON
            sheets_id: Google Sheets ID（可選，若未提供則從設定讀取）
            drive_folder_id: Google Drive 資料夾 ID（可選，若未提供則從設定讀取）

        Returns:
            DryRunResult: Dry Run 測試結果
        """
        logger.info(f"開始 {department} 部門 Dry Run 測試")

        # 1. 驗證 Service Account 格式
        format_result = self._validator.validate_service_account_format(base64_json)
        if not format_result.valid:
            return DryRunResult(
                success=False,
                sheets_error=format_result.error,
                drive_error=format_result.error
            )

        result = DryRunResult(success=True)

        # 2. 從設定讀取 Sheets ID（如果未提供）
        if sheets_id is None:
            sheets_id = self._setting_service.get_google_sheets_id(department)

        # 3. 測試 Sheets 連線
        if sheets_id:
            sheets_result = self._validator.test_sheets_access(base64_json, sheets_id)
            result.sheets_valid = sheets_result.valid
            result.sheets_error = sheets_result.error
            result.sheets_details = sheets_result.details

            if not sheets_result.valid:
                result.success = False
        else:
            result.sheets_valid = False
            result.sheets_error = "未設定 Google Sheets ID"

        # 4. 從設定讀取 Drive Folder ID（如果未提供）
        if drive_folder_id is None:
            drive_folder_id = self._setting_service.get_google_drive_folder_id(department)

        # 5. 測試 Drive 連線
        if drive_folder_id:
            drive_result = self._validator.test_drive_access(base64_json, drive_folder_id)
            result.drive_valid = drive_result.valid
            result.drive_error = drive_result.error
            result.drive_details = drive_result.details

            if not drive_result.valid:
                result.success = False
        else:
            # Drive 是選用的，不設定不算失敗
            result.drive_valid = False
            result.drive_error = "未設定 Google Drive 資料夾 ID"

        logger.info(
            f"{department} 部門 Dry Run 測試完成",
            success=result.success,
            sheets_valid=result.sheets_valid,
            drive_valid=result.drive_valid
        )

        return result

    def validate_all_departments(
        self,
        base64_json: str
    ) -> dict[str, DryRunResult]:
        """
        驗證所有部門的憑證

        Args:
            base64_json: Base64 編碼的 Service Account JSON

        Returns:
            dict: 各部門的驗證結果
        """
        results = {}

        for dept in [Department.DANHAI.value, Department.ANKENG.value]:
            results[dept] = self.dry_run_department(dept, base64_json)

        return results

    def quick_validate(
        self,
        base64_json: str,
        spreadsheet_id: str
    ) -> dict:
        """
        快速驗證（僅驗證格式和 Sheets 連線）

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            spreadsheet_id: Google Sheets ID

        Returns:
            dict: 驗證結果摘要
        """
        # 格式驗證
        format_result = self.validate_service_account(base64_json)
        if not format_result.valid:
            return {
                "valid": False,
                "step": "format",
                "error": format_result.error
            }

        # Sheets 連線測試
        sheets_result = self.test_sheets_connection(base64_json, spreadsheet_id)
        if not sheets_result.valid:
            return {
                "valid": False,
                "step": "sheets",
                "error": sheets_result.error,
                "service_account": format_result.details
            }

        return {
            "valid": True,
            "service_account": format_result.details,
            "spreadsheet": sheets_result.details
        }
