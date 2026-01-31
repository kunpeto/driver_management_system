"""
Google API 憑證測試服務
對應 tasks.md T072: 實作 Google API 憑證測試服務

功能：
- 測試 Service Account 憑證
- 測試 OAuth 2.0 憑證
- 驗證 API 權限範圍
- 提供詳細的測試結果

Gemini Review Fix: 新增逾時與重試設定
"""

import base64
import json
import socket
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Literal

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2

from src.config.settings import get_settings
from src.utils.logger import logger


# Gemini Review Fix: API 逾時與重試設定
API_TIMEOUT_SECONDS = 30  # 單次請求逾時時間
API_NUM_RETRIES = 2       # 失敗時重試次數


CredentialType = Literal["service_account", "oauth"]
TestResult = Literal["success", "failure", "skipped"]


@dataclass
class ApiTestResult:
    """單一 API 測試結果"""
    api_name: str
    result: TestResult
    message: str
    scope: Optional[str] = None
    details: Optional[dict] = None


@dataclass
class CredentialTestReport:
    """憑證測試報告"""
    credential_type: CredentialType
    department: Optional[str] = None
    format_valid: bool = False
    format_error: Optional[str] = None
    api_tests: List[ApiTestResult] = field(default_factory=list)
    overall_success: bool = False
    tested_at: datetime = field(default_factory=datetime.now)


class GoogleApiTester:
    """
    Google API 憑證測試服務

    用於全面測試 Google API 憑證的有效性和權限。
    """

    # Sheets API 權限範圍
    SCOPE_SHEETS_READONLY = "https://www.googleapis.com/auth/spreadsheets.readonly"
    SCOPE_SHEETS_FULL = "https://www.googleapis.com/auth/spreadsheets"

    # Drive API 權限範圍
    SCOPE_DRIVE_READONLY = "https://www.googleapis.com/auth/drive.readonly"
    SCOPE_DRIVE_FILE = "https://www.googleapis.com/auth/drive.file"
    SCOPE_DRIVE_FULL = "https://www.googleapis.com/auth/drive"

    def __init__(self):
        self._settings = get_settings()

    def _decode_service_account_json(self, base64_json: str) -> tuple[bool, dict | str]:
        """
        解碼 Base64 編碼的 Service Account JSON

        Args:
            base64_json: Base64 編碼的 JSON 字串

        Returns:
            tuple: (成功與否, 解碼後的字典或錯誤訊息)
        """
        try:
            decoded_bytes = base64.b64decode(base64_json)
            decoded_str = decoded_bytes.decode("utf-8")
            credentials_dict = json.loads(decoded_str)
            return True, credentials_dict
        except Exception as e:
            return False, str(e)

    def _validate_service_account_format(self, credentials_dict: dict) -> tuple[bool, str | None]:
        """
        驗證 Service Account 格式

        Args:
            credentials_dict: 憑證字典

        Returns:
            tuple: (有效與否, 錯誤訊息)
        """
        required_fields = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri"
        ]

        missing = [f for f in required_fields if f not in credentials_dict]
        if missing:
            return False, f"缺少必要欄位: {', '.join(missing)}"

        if credentials_dict["type"] != "service_account":
            return False, f"憑證類型錯誤，預期 'service_account'，得到 '{credentials_dict['type']}'"

        if not credentials_dict["private_key"].startswith("-----BEGIN"):
            return False, "private_key 格式無效"

        return True, None

    def test_sheets_api(
        self,
        credentials: service_account.Credentials | OAuthCredentials,
        spreadsheet_id: str
    ) -> ApiTestResult:
        """
        測試 Google Sheets API 存取

        Args:
            credentials: Google 憑證
            spreadsheet_id: 試算表 ID

        Returns:
            ApiTestResult: 測試結果
        """
        if not spreadsheet_id:
            return ApiTestResult(
                api_name="Google Sheets API",
                result="skipped",
                message="未提供 Spreadsheet ID",
                scope=self.SCOPE_SHEETS_READONLY
            )

        try:
            # Gemini Review Fix: 設定逾時與重試參數
            http = httplib2.Http(timeout=API_TIMEOUT_SECONDS)
            service = build("sheets", "v4", credentials=credentials, http=http)
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields="properties.title,sheets.properties.title"
            ).execute(num_retries=API_NUM_RETRIES)

            title = spreadsheet["properties"]["title"]
            sheet_count = len(spreadsheet.get("sheets", []))

            return ApiTestResult(
                api_name="Google Sheets API",
                result="success",
                message=f"成功存取試算表: {title}",
                scope=self.SCOPE_SHEETS_READONLY,
                details={
                    "spreadsheet_title": title,
                    "sheet_count": sheet_count
                }
            )

        except HttpError as e:
            status = e.resp.status
            if status == 403:
                message = "權限不足：請確認憑證有存取此試算表的權限"
            elif status == 404:
                message = "試算表不存在或 ID 錯誤"
            else:
                message = f"API 錯誤 ({status}): {str(e)}"

            return ApiTestResult(
                api_name="Google Sheets API",
                result="failure",
                message=message,
                scope=self.SCOPE_SHEETS_READONLY
            )

        except socket.timeout:
            # Gemini Review Fix: 明確處理逾時例外
            return ApiTestResult(
                api_name="Google Sheets API",
                result="failure",
                message=f"連線逾時（超過 {API_TIMEOUT_SECONDS} 秒）",
                scope=self.SCOPE_SHEETS_READONLY
            )

        except Exception as e:
            return ApiTestResult(
                api_name="Google Sheets API",
                result="failure",
                message=f"測試失敗: {str(e)}",
                scope=self.SCOPE_SHEETS_READONLY
            )

    def test_drive_api(
        self,
        credentials: service_account.Credentials | OAuthCredentials,
        folder_id: str
    ) -> ApiTestResult:
        """
        測試 Google Drive API 存取

        Args:
            credentials: Google 憑證
            folder_id: 資料夾 ID

        Returns:
            ApiTestResult: 測試結果
        """
        if not folder_id:
            return ApiTestResult(
                api_name="Google Drive API",
                result="skipped",
                message="未提供資料夾 ID",
                scope=self.SCOPE_DRIVE_READONLY
            )

        try:
            # Gemini Review Fix: 設定逾時與重試參數
            http = httplib2.Http(timeout=API_TIMEOUT_SECONDS)
            service = build("drive", "v3", credentials=credentials, http=http)
            folder = service.files().get(
                fileId=folder_id,
                fields="id,name,mimeType"
            ).execute(num_retries=API_NUM_RETRIES)

            if folder["mimeType"] != "application/vnd.google-apps.folder":
                return ApiTestResult(
                    api_name="Google Drive API",
                    result="failure",
                    message="指定的 ID 不是資料夾",
                    scope=self.SCOPE_DRIVE_READONLY
                )

            return ApiTestResult(
                api_name="Google Drive API",
                result="success",
                message=f"成功存取資料夾: {folder['name']}",
                scope=self.SCOPE_DRIVE_READONLY,
                details={
                    "folder_name": folder["name"],
                    "folder_id": folder["id"]
                }
            )

        except HttpError as e:
            status = e.resp.status
            if status == 403:
                message = "權限不足：請確認憑證有存取此資料夾的權限"
            elif status == 404:
                message = "資料夾不存在或 ID 錯誤"
            else:
                message = f"API 錯誤 ({status}): {str(e)}"

            return ApiTestResult(
                api_name="Google Drive API",
                result="failure",
                message=message,
                scope=self.SCOPE_DRIVE_READONLY
            )

        except socket.timeout:
            # Gemini Review Fix: 明確處理逾時例外
            return ApiTestResult(
                api_name="Google Drive API",
                result="failure",
                message=f"連線逾時（超過 {API_TIMEOUT_SECONDS} 秒）",
                scope=self.SCOPE_DRIVE_READONLY
            )

        except Exception as e:
            return ApiTestResult(
                api_name="Google Drive API",
                result="failure",
                message=f"測試失敗: {str(e)}",
                scope=self.SCOPE_DRIVE_READONLY
            )

    def test_service_account(
        self,
        base64_json: str,
        department: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ) -> CredentialTestReport:
        """
        測試 Service Account 憑證

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            department: 部門名稱（可選）
            spreadsheet_id: Google Sheets ID（可選）
            folder_id: Google Drive 資料夾 ID（可選）
            scopes: 權限範圍（可選，預設為 Sheets + Drive 唯讀）

        Returns:
            CredentialTestReport: 測試報告
        """
        report = CredentialTestReport(
            credential_type="service_account",
            department=department
        )

        # 1. 解碼 Base64
        success, result = self._decode_service_account_json(base64_json)
        if not success:
            report.format_error = f"Base64 解碼失敗: {result}"
            return report

        credentials_dict = result

        # 2. 驗證格式
        valid, error = self._validate_service_account_format(credentials_dict)
        if not valid:
            report.format_error = error
            return report

        report.format_valid = True

        # 3. 建立憑證
        if scopes is None:
            scopes = [self.SCOPE_SHEETS_READONLY, self.SCOPE_DRIVE_READONLY]

        try:
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=scopes
            )
        except Exception as e:
            report.format_error = f"建立憑證失敗: {str(e)}"
            return report

        # 4. 測試 API
        if spreadsheet_id:
            sheets_result = self.test_sheets_api(credentials, spreadsheet_id)
            report.api_tests.append(sheets_result)
        else:
            report.api_tests.append(ApiTestResult(
                api_name="Google Sheets API",
                result="skipped",
                message="未提供 Spreadsheet ID，跳過測試",
                scope=self.SCOPE_SHEETS_READONLY
            ))

        if folder_id:
            drive_result = self.test_drive_api(credentials, folder_id)
            report.api_tests.append(drive_result)
        else:
            report.api_tests.append(ApiTestResult(
                api_name="Google Drive API",
                result="skipped",
                message="未提供資料夾 ID，跳過測試",
                scope=self.SCOPE_DRIVE_READONLY
            ))

        # 5. 判斷整體結果
        non_skipped = [t for t in report.api_tests if t.result != "skipped"]
        if not non_skipped:
            # 只驗證格式，沒有實際測試 API
            report.overall_success = True
        else:
            report.overall_success = all(t.result == "success" for t in non_skipped)

        logger.info(
            "Service Account 憑證測試完成",
            department=department,
            format_valid=report.format_valid,
            overall_success=report.overall_success,
            api_tests=[t.api_name for t in report.api_tests if t.result == "success"]
        )

        return report

    def test_oauth_token(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        department: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> CredentialTestReport:
        """
        測試 OAuth 2.0 憑證

        Args:
            access_token: Access Token
            refresh_token: Refresh Token（可選）
            department: 部門名稱（可選）
            spreadsheet_id: Google Sheets ID（可選）
            folder_id: Google Drive 資料夾 ID（可選）

        Returns:
            CredentialTestReport: 測試報告
        """
        report = CredentialTestReport(
            credential_type="oauth",
            department=department
        )

        # 驗證 Token 存在
        if not access_token:
            report.format_error = "Access Token 不能為空"
            return report

        report.format_valid = True

        # 建立 OAuth 憑證
        try:
            credentials = OAuthCredentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self._settings.google_oauth_client_id,
                client_secret=self._settings.google_oauth_client_secret
            )
        except Exception as e:
            report.format_error = f"建立 OAuth 憑證失敗: {str(e)}"
            return report

        # 測試 API
        if spreadsheet_id:
            sheets_result = self.test_sheets_api(credentials, spreadsheet_id)
            report.api_tests.append(sheets_result)

        if folder_id:
            drive_result = self.test_drive_api(credentials, folder_id)
            report.api_tests.append(drive_result)

        # 判斷整體結果
        non_skipped = [t for t in report.api_tests if t.result != "skipped"]
        if not non_skipped:
            report.overall_success = True
        else:
            report.overall_success = all(t.result == "success" for t in non_skipped)

        logger.info(
            "OAuth 憑證測試完成",
            department=department,
            overall_success=report.overall_success
        )

        return report

    def test_department_credentials(
        self,
        department: Literal["淡海", "安坑"]
    ) -> CredentialTestReport:
        """
        測試指定部門的憑證

        從環境變數讀取憑證進行測試。

        Args:
            department: 部門名稱

        Returns:
            CredentialTestReport: 測試報告
        """
        if department == "淡海":
            base64_json = self._settings.tanhae_google_service_account_json
            sheets_id = self._settings.tanhae_google_sheets_id_schedule
            drive_id = getattr(self._settings, 'tanhae_google_drive_folder_id', None)
        else:
            base64_json = self._settings.anping_google_service_account_json
            sheets_id = self._settings.anping_google_sheets_id_schedule
            drive_id = getattr(self._settings, 'anping_google_drive_folder_id', None)

        if not base64_json:
            report = CredentialTestReport(
                credential_type="service_account",
                department=department
            )
            report.format_error = f"{department} Service Account 憑證未設定"
            return report

        return self.test_service_account(
            base64_json=base64_json,
            department=department,
            spreadsheet_id=sheets_id,
            folder_id=drive_id
        )


# 單例實例
_tester_instance: Optional[GoogleApiTester] = None


def get_google_api_tester() -> GoogleApiTester:
    """取得 Google API 測試器實例（單例）"""
    global _tester_instance
    if _tester_instance is None:
        _tester_instance = GoogleApiTester()
    return _tester_instance
