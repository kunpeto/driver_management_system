"""
Google 服務帳戶憑證載入工具
對應 tasks.md T017: 實作服務帳戶憑證載入工具

功能：
- 從環境變數讀取 Base64 編碼的服務帳戶 JSON
- 解碼並驗證憑證格式
- 建立 Google API 認證物件
"""

import base64
import json
from typing import Optional, Literal

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config.settings import get_settings


# 部門類型
DepartmentType = Literal["淡海", "安坑"]

# Google API 範圍
SCOPES_SHEETS_READONLY = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SCOPES_DRIVE_FULL = ["https://www.googleapis.com/auth/drive"]


class GoogleCredentialLoader:
    """
    Google 服務帳戶憑證載入器

    支援從環境變數讀取 Base64 編碼的憑證 JSON。
    """

    def __init__(self):
        self._settings = get_settings()
        self._credentials_cache: dict[str, service_account.Credentials] = {}

    def _get_service_account_json(self, department: DepartmentType) -> Optional[str]:
        """
        取得指定部門的服務帳戶 JSON（Base64 編碼）

        Args:
            department: 部門名稱（淡海/安坑）

        Returns:
            Base64 編碼的 JSON 字串，如果未設定則返回 None
        """
        if department == "淡海":
            return self._settings.tanhae_google_service_account_json
        elif department == "安坑":
            return self._settings.anping_google_service_account_json
        else:
            raise ValueError(f"未知的部門: {department}")

    def decode_credentials(self, base64_json: str) -> dict:
        """
        解碼 Base64 編碼的憑證 JSON

        Args:
            base64_json: Base64 編碼的 JSON 字串

        Returns:
            dict: 解碼後的憑證字典

        Raises:
            ValueError: JSON 格式無效
        """
        try:
            # 解碼 Base64
            decoded_bytes = base64.b64decode(base64_json)
            decoded_str = decoded_bytes.decode("utf-8")

            # 解析 JSON
            credentials_dict = json.loads(decoded_str)

            # 驗證必要欄位
            required_fields = ["type", "project_id", "private_key", "client_email"]
            for field in required_fields:
                if field not in credentials_dict:
                    raise ValueError(f"憑證缺少必要欄位: {field}")

            if credentials_dict["type"] != "service_account":
                raise ValueError(f"憑證類型錯誤，預期 'service_account'，得到 '{credentials_dict['type']}'")

            return credentials_dict
        except base64.binascii.Error as e:
            raise ValueError(f"Base64 解碼失敗: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失敗: {e}")

    def get_credentials(
        self,
        department: DepartmentType,
        scopes: list[str] = None
    ) -> Optional[service_account.Credentials]:
        """
        取得指定部門的 Google 服務帳戶憑證

        Args:
            department: 部門名稱
            scopes: API 範圍（預設為 Sheets 唯讀）

        Returns:
            Google 服務帳戶憑證物件，如果未設定則返回 None
        """
        if scopes is None:
            scopes = SCOPES_SHEETS_READONLY

        # 檢查快取
        cache_key = f"{department}:{','.join(scopes)}"
        if cache_key in self._credentials_cache:
            return self._credentials_cache[cache_key]

        # 取得 Base64 編碼的 JSON
        base64_json = self._get_service_account_json(department)
        if not base64_json:
            return None

        # 解碼並建立憑證
        try:
            credentials_dict = self.decode_credentials(base64_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=scopes
            )

            # 快取
            self._credentials_cache[cache_key] = credentials
            return credentials
        except ValueError:
            return None

    def get_sheets_service(self, department: DepartmentType):
        """
        取得 Google Sheets API 服務物件

        Args:
            department: 部門名稱

        Returns:
            Google Sheets API 服務物件

        Raises:
            ValueError: 憑證未設定或無效
        """
        credentials = self.get_credentials(department, SCOPES_SHEETS_READONLY)
        if not credentials:
            raise ValueError(f"{department} 部門的 Google 服務帳戶憑證未設定")

        return build("sheets", "v4", credentials=credentials)

    def get_drive_service(self, department: DepartmentType):
        """
        取得 Google Drive API 服務物件

        Args:
            department: 部門名稱

        Returns:
            Google Drive API 服務物件

        Raises:
            ValueError: 憑證未設定或無效
        """
        credentials = self.get_credentials(department, SCOPES_DRIVE_FULL)
        if not credentials:
            raise ValueError(f"{department} 部門的 Google 服務帳戶憑證未設定")

        return build("drive", "v3", credentials=credentials)

    def validate_credentials(self, department: DepartmentType) -> dict:
        """
        驗證指定部門的憑證是否有效

        Args:
            department: 部門名稱

        Returns:
            dict: 驗證結果 {
                "valid": bool,
                "error": str | None,
                "project_id": str | None,
                "client_email": str | None
            }
        """
        result = {
            "valid": False,
            "error": None,
            "project_id": None,
            "client_email": None
        }

        base64_json = self._get_service_account_json(department)
        if not base64_json:
            result["error"] = f"{department} 部門的服務帳戶憑證未設定"
            return result

        try:
            credentials_dict = self.decode_credentials(base64_json)
            result["project_id"] = credentials_dict.get("project_id")
            result["client_email"] = credentials_dict.get("client_email")

            # 嘗試建立憑證物件
            credentials = self.get_credentials(department)
            if credentials:
                result["valid"] = True
            else:
                result["error"] = "無法建立憑證物件"

        except ValueError as e:
            result["error"] = str(e)

        return result


# 便捷函數
_loader_instance: Optional[GoogleCredentialLoader] = None


def get_credential_loader() -> GoogleCredentialLoader:
    """取得憑證載入器實例（單例）"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = GoogleCredentialLoader()
    return _loader_instance


def get_sheets_service(department: DepartmentType):
    """取得 Google Sheets 服務"""
    return get_credential_loader().get_sheets_service(department)


def get_drive_service(department: DepartmentType):
    """取得 Google Drive 服務"""
    return get_credential_loader().get_drive_service(department)
