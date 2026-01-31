"""
憑證驗證服務
對應 tasks.md T037a: 實作憑證驗證服務

功能：
- 驗證 Service Account 格式
- 測試 Google Sheets 存取權限
- 驗證 OAuth 2.0 格式
"""

import base64
import json
from typing import Optional, Literal
from dataclasses import dataclass

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config.settings import get_settings
from src.utils.logger import logger


DepartmentType = Literal["淡海", "安坑"]


@dataclass
class ValidationResult:
    """驗證結果"""
    valid: bool
    error: Optional[str] = None
    details: Optional[dict] = None


class CredentialValidator:
    """
    憑證驗證服務

    用於驗證 Google API 憑證的格式和權限。
    """

    SCOPES_SHEETS = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    SCOPES_DRIVE = ["https://www.googleapis.com/auth/drive.readonly"]

    def __init__(self):
        self._settings = get_settings()

    def validate_service_account_format(self, base64_json: str) -> ValidationResult:
        """
        驗證 Service Account JSON 格式

        Args:
            base64_json: Base64 編碼的 JSON 字串

        Returns:
            ValidationResult: 驗證結果
        """
        try:
            # 1. Base64 解碼
            try:
                decoded_bytes = base64.b64decode(base64_json)
                decoded_str = decoded_bytes.decode("utf-8")
            except Exception as e:
                return ValidationResult(
                    valid=False,
                    error=f"Base64 解碼失敗: {str(e)}"
                )

            # 2. JSON 解析
            try:
                credentials_dict = json.loads(decoded_str)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    valid=False,
                    error=f"JSON 格式無效: {str(e)}"
                )

            # 3. 驗證必要欄位
            required_fields = [
                "type",
                "project_id",
                "private_key_id",
                "private_key",
                "client_email",
                "client_id",
                "auth_uri",
                "token_uri"
            ]

            missing_fields = [f for f in required_fields if f not in credentials_dict]
            if missing_fields:
                return ValidationResult(
                    valid=False,
                    error=f"缺少必要欄位: {', '.join(missing_fields)}"
                )

            # 4. 驗證類型
            if credentials_dict["type"] != "service_account":
                return ValidationResult(
                    valid=False,
                    error=f"憑證類型錯誤，預期 'service_account'，得到 '{credentials_dict['type']}'"
                )

            # 5. 驗證 private_key 格式
            private_key = credentials_dict["private_key"]
            if not private_key.startswith("-----BEGIN"):
                return ValidationResult(
                    valid=False,
                    error="private_key 格式無效"
                )

            return ValidationResult(
                valid=True,
                details={
                    "project_id": credentials_dict["project_id"],
                    "client_email": credentials_dict["client_email"]
                }
            )

        except Exception as e:
            return ValidationResult(
                valid=False,
                error=f"驗證過程發生錯誤: {str(e)}"
            )

    def validate_oauth_format(self, client_id: str, client_secret: str) -> ValidationResult:
        """
        驗證 OAuth 2.0 Client 格式

        Args:
            client_id: OAuth Client ID
            client_secret: OAuth Client Secret

        Returns:
            ValidationResult: 驗證結果
        """
        errors = []

        # 驗證 Client ID 格式
        if not client_id:
            errors.append("Client ID 不能為空")
        elif not client_id.endswith(".apps.googleusercontent.com"):
            errors.append("Client ID 格式無效（應以 .apps.googleusercontent.com 結尾）")

        # 驗證 Client Secret 格式
        if not client_secret:
            errors.append("Client Secret 不能為空")
        elif len(client_secret) < 10:
            errors.append("Client Secret 長度過短")

        if errors:
            return ValidationResult(
                valid=False,
                error="; ".join(errors)
            )

        return ValidationResult(valid=True)

    def test_sheets_access(
        self,
        base64_json: str,
        spreadsheet_id: str
    ) -> ValidationResult:
        """
        測試 Google Sheets 存取權限

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            spreadsheet_id: Google Sheets ID

        Returns:
            ValidationResult: 驗證結果（包含 sheet 名稱列表）
        """
        # 1. 先驗證格式
        format_result = self.validate_service_account_format(base64_json)
        if not format_result.valid:
            return format_result

        try:
            # 2. 建立憑證
            decoded_bytes = base64.b64decode(base64_json)
            credentials_dict = json.loads(decoded_bytes.decode("utf-8"))

            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=self.SCOPES_SHEETS
            )

            # 3. 建立服務
            service = build("sheets", "v4", credentials=credentials)

            # 4. 嘗試取得試算表資訊
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields="properties.title,sheets.properties.title"
            ).execute()

            # 5. 提取 sheet 名稱
            title = spreadsheet["properties"]["title"]
            sheets = [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]

            logger.info(
                f"Sheets 存取測試成功",
                spreadsheet_id=spreadsheet_id,
                title=title,
                sheet_count=len(sheets)
            )

            return ValidationResult(
                valid=True,
                details={
                    "spreadsheet_title": title,
                    "sheet_names": sheets,
                    "sheet_count": len(sheets)
                }
            )

        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            status_code = e.resp.status

            if status_code == 403:
                return ValidationResult(
                    valid=False,
                    error=f"權限不足：服務帳戶沒有存取此試算表的權限。請將 {format_result.details['client_email']} 加入試算表的共用名單。"
                )
            elif status_code == 404:
                return ValidationResult(
                    valid=False,
                    error="試算表不存在或 ID 錯誤"
                )
            else:
                return ValidationResult(
                    valid=False,
                    error=f"Google API 錯誤: {str(e)}"
                )

        except Exception as e:
            return ValidationResult(
                valid=False,
                error=f"存取測試失敗: {str(e)}"
            )

    def test_drive_access(
        self,
        base64_json: str,
        folder_id: str
    ) -> ValidationResult:
        """
        測試 Google Drive 資料夾存取權限

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            folder_id: Google Drive 資料夾 ID

        Returns:
            ValidationResult: 驗證結果
        """
        # 1. 先驗證格式
        format_result = self.validate_service_account_format(base64_json)
        if not format_result.valid:
            return format_result

        try:
            # 2. 建立憑證
            decoded_bytes = base64.b64decode(base64_json)
            credentials_dict = json.loads(decoded_bytes.decode("utf-8"))

            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=self.SCOPES_DRIVE
            )

            # 3. 建立服務
            service = build("drive", "v3", credentials=credentials)

            # 4. 嘗試取得資料夾資訊
            folder = service.files().get(
                fileId=folder_id,
                fields="id,name,mimeType"
            ).execute()

            # 5. 驗證是資料夾
            if folder["mimeType"] != "application/vnd.google-apps.folder":
                return ValidationResult(
                    valid=False,
                    error="指定的 ID 不是資料夾"
                )

            logger.info(
                f"Drive 存取測試成功",
                folder_id=folder_id,
                folder_name=folder["name"]
            )

            return ValidationResult(
                valid=True,
                details={
                    "folder_name": folder["name"],
                    "folder_id": folder["id"]
                }
            )

        except HttpError as e:
            status_code = e.resp.status

            if status_code == 403:
                return ValidationResult(
                    valid=False,
                    error=f"權限不足：服務帳戶沒有存取此資料夾的權限"
                )
            elif status_code == 404:
                return ValidationResult(
                    valid=False,
                    error="資料夾不存在或 ID 錯誤"
                )
            else:
                return ValidationResult(
                    valid=False,
                    error=f"Google API 錯誤: {str(e)}"
                )

        except Exception as e:
            return ValidationResult(
                valid=False,
                error=f"存取測試失敗: {str(e)}"
            )

    def validate_department_credentials(
        self,
        department: DepartmentType
    ) -> ValidationResult:
        """
        驗證指定部門的所有憑證

        從環境變數讀取憑證並驗證格式。

        Args:
            department: 部門名稱

        Returns:
            ValidationResult: 驗證結果
        """
        results = {}

        # 取得憑證
        if department == "淡海":
            base64_json = self._settings.tanhae_google_service_account_json
            sheets_id_schedule = self._settings.tanhae_google_sheets_id_schedule
            sheets_id_duty = self._settings.tanhae_google_sheets_id_duty
        else:
            base64_json = self._settings.anping_google_service_account_json
            sheets_id_schedule = self._settings.anping_google_sheets_id_schedule
            sheets_id_duty = self._settings.anping_google_sheets_id_duty

        # 1. 驗證 Service Account 格式
        if base64_json:
            format_result = self.validate_service_account_format(base64_json)
            results["service_account_format"] = {
                "valid": format_result.valid,
                "error": format_result.error,
                "details": format_result.details
            }
        else:
            results["service_account_format"] = {
                "valid": False,
                "error": "Service Account 憑證未設定"
            }

        # 2. 驗證 Sheets 存取（如果格式正確）
        if results["service_account_format"]["valid"] and sheets_id_schedule:
            sheets_result = self.test_sheets_access(base64_json, sheets_id_schedule)
            results["sheets_access_schedule"] = {
                "valid": sheets_result.valid,
                "error": sheets_result.error,
                "details": sheets_result.details
            }

        if results["service_account_format"]["valid"] and sheets_id_duty:
            sheets_result = self.test_sheets_access(base64_json, sheets_id_duty)
            results["sheets_access_duty"] = {
                "valid": sheets_result.valid,
                "error": sheets_result.error,
                "details": sheets_result.details
            }

        # 判斷整體結果
        all_valid = all(
            r.get("valid", False)
            for r in results.values()
        )

        return ValidationResult(
            valid=all_valid,
            details=results
        )


# 單例實例
_validator_instance: Optional[CredentialValidator] = None


def get_credential_validator() -> CredentialValidator:
    """取得憑證驗證器實例（單例）"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CredentialValidator()
    return _validator_instance
