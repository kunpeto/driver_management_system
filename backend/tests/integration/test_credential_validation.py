"""
憑證驗證整合測試
對應 tasks.md T037b: 實作憑證驗證整合測試

測試範圍：
- 有效/無效憑證格式驗證
- OAuth 2.0 格式驗證
- 模擬無權限情境
"""

import base64
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.credential_validator import (
    CredentialValidator,
    ValidationResult,
    get_credential_validator
)


# ============================================================
# 測試資料
# ============================================================

# 有效的 Service Account JSON 結構
VALID_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "test-project",
    "private_key_id": "key123",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n",
    "client_email": "test@test-project.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
}


def encode_service_account(sa_dict: dict) -> str:
    """將 Service Account dict 編碼為 Base64"""
    json_str = json.dumps(sa_dict)
    return base64.b64encode(json_str.encode()).decode()


# ============================================================
# Service Account 格式驗證測試
# ============================================================

class TestServiceAccountFormatValidation:
    """Service Account 格式驗證測試"""

    def setup_method(self):
        """每個測試方法前執行"""
        self.validator = CredentialValidator()

    def test_valid_service_account(self):
        """測試有效的 Service Account 憑證"""
        base64_json = encode_service_account(VALID_SERVICE_ACCOUNT)

        result = self.validator.validate_service_account_format(base64_json)

        assert result.valid is True
        assert result.error is None
        assert result.details is not None
        assert result.details["project_id"] == "test-project"
        assert result.details["client_email"] == "test@test-project.iam.gserviceaccount.com"

    def test_invalid_base64(self):
        """測試無效的 Base64 編碼"""
        invalid_base64 = "not-valid-base64!!!"

        result = self.validator.validate_service_account_format(invalid_base64)

        assert result.valid is False
        assert "Base64 解碼失敗" in result.error

    def test_invalid_json(self):
        """測試無效的 JSON 格式"""
        invalid_json = base64.b64encode(b"not a json").decode()

        result = self.validator.validate_service_account_format(invalid_json)

        assert result.valid is False
        assert "JSON 格式無效" in result.error

    def test_missing_required_fields(self):
        """測試缺少必要欄位"""
        incomplete_sa = {
            "type": "service_account",
            "project_id": "test-project"
            # 缺少其他必要欄位
        }
        base64_json = encode_service_account(incomplete_sa)

        result = self.validator.validate_service_account_format(base64_json)

        assert result.valid is False
        assert "缺少必要欄位" in result.error

    def test_wrong_credential_type(self):
        """測試錯誤的憑證類型"""
        wrong_type_sa = VALID_SERVICE_ACCOUNT.copy()
        wrong_type_sa["type"] = "authorized_user"
        base64_json = encode_service_account(wrong_type_sa)

        result = self.validator.validate_service_account_format(base64_json)

        assert result.valid is False
        assert "憑證類型錯誤" in result.error

    def test_invalid_private_key_format(self):
        """測試無效的 private_key 格式"""
        invalid_key_sa = VALID_SERVICE_ACCOUNT.copy()
        invalid_key_sa["private_key"] = "invalid-key-format"
        base64_json = encode_service_account(invalid_key_sa)

        result = self.validator.validate_service_account_format(base64_json)

        assert result.valid is False
        assert "private_key 格式無效" in result.error


# ============================================================
# OAuth 2.0 格式驗證測試
# ============================================================

class TestOAuthFormatValidation:
    """OAuth 2.0 格式驗證測試"""

    def setup_method(self):
        """每個測試方法前執行"""
        self.validator = CredentialValidator()

    def test_valid_oauth_credentials(self):
        """測試有效的 OAuth 憑證"""
        client_id = "123456789.apps.googleusercontent.com"
        client_secret = "GOCSPX-abcdefghijklmnop"

        result = self.validator.validate_oauth_format(client_id, client_secret)

        assert result.valid is True
        assert result.error is None

    def test_empty_client_id(self):
        """測試空的 Client ID"""
        result = self.validator.validate_oauth_format("", "valid-secret")

        assert result.valid is False
        assert "Client ID 不能為空" in result.error

    def test_invalid_client_id_format(self):
        """測試無效的 Client ID 格式"""
        result = self.validator.validate_oauth_format(
            "invalid-client-id",
            "valid-secret"
        )

        assert result.valid is False
        assert "Client ID 格式無效" in result.error

    def test_empty_client_secret(self):
        """測試空的 Client Secret"""
        result = self.validator.validate_oauth_format(
            "123.apps.googleusercontent.com",
            ""
        )

        assert result.valid is False
        assert "Client Secret 不能為空" in result.error

    def test_short_client_secret(self):
        """測試過短的 Client Secret"""
        result = self.validator.validate_oauth_format(
            "123.apps.googleusercontent.com",
            "short"
        )

        assert result.valid is False
        assert "Client Secret 長度過短" in result.error

    def test_multiple_errors(self):
        """測試多個錯誤同時發生"""
        result = self.validator.validate_oauth_format("", "")

        assert result.valid is False
        assert "Client ID 不能為空" in result.error
        assert "Client Secret 不能為空" in result.error


# ============================================================
# Sheets 存取權限測試（模擬）
# ============================================================

class TestSheetsAccessValidation:
    """Google Sheets 存取權限測試"""

    def setup_method(self):
        """每個測試方法前執行"""
        self.validator = CredentialValidator()
        self.valid_base64 = encode_service_account(VALID_SERVICE_ACCOUNT)

    @patch("src.services.credential_validator.build")
    @patch("src.services.credential_validator.service_account.Credentials.from_service_account_info")
    def test_successful_sheets_access(self, mock_creds, mock_build):
        """測試成功存取 Sheets"""
        # 設定 mock
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().get().execute.return_value = {
            "properties": {"title": "測試試算表"},
            "sheets": [
                {"properties": {"title": "Sheet1"}},
                {"properties": {"title": "Sheet2"}}
            ]
        }

        result = self.validator.test_sheets_access(
            self.valid_base64,
            "test-spreadsheet-id"
        )

        assert result.valid is True
        assert result.details["spreadsheet_title"] == "測試試算表"
        assert result.details["sheet_count"] == 2
        assert "Sheet1" in result.details["sheet_names"]

    @patch("src.services.credential_validator.build")
    @patch("src.services.credential_validator.service_account.Credentials.from_service_account_info")
    def test_permission_denied(self, mock_creds, mock_build):
        """測試權限不足（403 錯誤）"""
        from googleapiclient.errors import HttpError

        # 設定 mock 拋出 403 錯誤
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # 建立 HttpError mock
        mock_resp = Mock()
        mock_resp.status = 403
        http_error = HttpError(mock_resp, b'{"error": "forbidden"}')
        http_error.error_details = []

        mock_service.spreadsheets().get().execute.side_effect = http_error

        result = self.validator.test_sheets_access(
            self.valid_base64,
            "test-spreadsheet-id"
        )

        assert result.valid is False
        assert "權限不足" in result.error

    @patch("src.services.credential_validator.build")
    @patch("src.services.credential_validator.service_account.Credentials.from_service_account_info")
    def test_spreadsheet_not_found(self, mock_creds, mock_build):
        """測試試算表不存在（404 錯誤）"""
        from googleapiclient.errors import HttpError

        # 設定 mock 拋出 404 錯誤
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_resp = Mock()
        mock_resp.status = 404
        http_error = HttpError(mock_resp, b'{"error": "not found"}')
        http_error.error_details = []

        mock_service.spreadsheets().get().execute.side_effect = http_error

        result = self.validator.test_sheets_access(
            self.valid_base64,
            "non-existent-id"
        )

        assert result.valid is False
        assert "不存在" in result.error

    def test_invalid_credentials_format(self):
        """測試憑證格式無效時的 Sheets 存取"""
        result = self.validator.test_sheets_access(
            "invalid-base64",
            "test-spreadsheet-id"
        )

        assert result.valid is False
        assert "Base64 解碼失敗" in result.error


# ============================================================
# Drive 存取權限測試（模擬）
# ============================================================

class TestDriveAccessValidation:
    """Google Drive 存取權限測試"""

    def setup_method(self):
        """每個測試方法前執行"""
        self.validator = CredentialValidator()
        self.valid_base64 = encode_service_account(VALID_SERVICE_ACCOUNT)

    @patch("src.services.credential_validator.build")
    @patch("src.services.credential_validator.service_account.Credentials.from_service_account_info")
    def test_successful_drive_access(self, mock_creds, mock_build):
        """測試成功存取 Drive 資料夾"""
        # 設定 mock
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.files().get().execute.return_value = {
            "id": "folder-id",
            "name": "測試資料夾",
            "mimeType": "application/vnd.google-apps.folder"
        }

        result = self.validator.test_drive_access(
            self.valid_base64,
            "folder-id"
        )

        assert result.valid is True
        assert result.details["folder_name"] == "測試資料夾"

    @patch("src.services.credential_validator.build")
    @patch("src.services.credential_validator.service_account.Credentials.from_service_account_info")
    def test_not_a_folder(self, mock_creds, mock_build):
        """測試指定的 ID 不是資料夾"""
        # 設定 mock 返回文件而非資料夾
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.files().get().execute.return_value = {
            "id": "file-id",
            "name": "測試文件.docx",
            "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }

        result = self.validator.test_drive_access(
            self.valid_base64,
            "file-id"
        )

        assert result.valid is False
        assert "不是資料夾" in result.error

    @patch("src.services.credential_validator.build")
    @patch("src.services.credential_validator.service_account.Credentials.from_service_account_info")
    def test_drive_permission_denied(self, mock_creds, mock_build):
        """測試 Drive 權限不足"""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_resp = Mock()
        mock_resp.status = 403
        http_error = HttpError(mock_resp, b'{"error": "forbidden"}')

        mock_service.files().get().execute.side_effect = http_error

        result = self.validator.test_drive_access(
            self.valid_base64,
            "folder-id"
        )

        assert result.valid is False
        assert "權限不足" in result.error


# ============================================================
# 單例模式測試
# ============================================================

class TestSingletonPattern:
    """單例模式測試"""

    def test_get_credential_validator_returns_same_instance(self):
        """測試 get_credential_validator 返回相同實例"""
        validator1 = get_credential_validator()
        validator2 = get_credential_validator()

        assert validator1 is validator2


# ============================================================
# ValidationResult 測試
# ============================================================

class TestValidationResult:
    """ValidationResult 資料類別測試"""

    def test_valid_result(self):
        """測試有效結果"""
        result = ValidationResult(valid=True, details={"key": "value"})

        assert result.valid is True
        assert result.error is None
        assert result.details == {"key": "value"}

    def test_invalid_result(self):
        """測試無效結果"""
        result = ValidationResult(valid=False, error="錯誤訊息")

        assert result.valid is False
        assert result.error == "錯誤訊息"
        assert result.details is None

    def test_default_values(self):
        """測試預設值"""
        result = ValidationResult(valid=True)

        assert result.error is None
        assert result.details is None


# ============================================================
# 部門憑證驗證測試（模擬）
# ============================================================

class TestDepartmentCredentialValidation:
    """部門憑證驗證測試"""

    @patch("src.services.credential_validator.get_settings")
    def test_missing_service_account(self, mock_settings):
        """測試 Service Account 未設定"""
        # 設定 mock
        mock_settings.return_value = Mock(
            tanhae_google_service_account_json=None,
            tanhae_google_sheets_id_schedule=None,
            tanhae_google_sheets_id_duty=None
        )

        validator = CredentialValidator()
        result = validator.validate_department_credentials("淡海")

        assert result.valid is False
        assert "service_account_format" in result.details
        assert result.details["service_account_format"]["valid"] is False
        assert "未設定" in result.details["service_account_format"]["error"]
