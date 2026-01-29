"""
Google OAuth API 單元測試
對應 tasks.md T098a: 實作 OAuth 回調端點單元測試

測試項目：
- 正常授權流程
- 拒絕授權（error='access_denied'）
- 無效的 authorization code
- 遺失 code 參數
- 無效的 state token
- Refresh token 加密儲存
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestGoogleOAuthAuthUrl:
    """測試授權 URL 生成"""

    def test_get_auth_url_success(self, client, admin_token):
        """測試成功生成授權 URL"""
        with patch('src.api.google_oauth._get_oauth_credentials') as mock_creds:
            mock_creds.return_value = (
                'test-client-id',
                'test-client-secret',
                'http://localhost:8000/api/auth/google/callback'
            )

            response = client.get(
                "/api/google/auth-url?department=淡海",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert "state" in data
            assert data["department"] == "淡海"
            assert "accounts.google.com" in data["auth_url"]
            assert "test-client-id" in data["auth_url"]

    def test_get_auth_url_invalid_department(self, client, admin_token):
        """測試無效部門"""
        response = client.get(
            "/api/google/auth-url?department=無效部門",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400
        assert "無效的部門" in response.json()["detail"]

    def test_get_auth_url_unauthorized(self, client, staff_token):
        """測試非 Admin 無法取得授權 URL"""
        response = client.get(
            "/api/google/auth-url?department=淡海",
            headers={"Authorization": f"Bearer {staff_token}"}
        )

        assert response.status_code == 403

    def test_get_auth_url_no_oauth_config(self, client, admin_token):
        """測試未設定 OAuth 憑證"""
        with patch('src.api.google_oauth._get_oauth_credentials') as mock_creds:
            mock_creds.side_effect = HTTPException(
                status_code=500,
                detail="Google OAuth 未設定"
            )

            response = client.get(
                "/api/google/auth-url?department=淡海",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == 500


class TestGoogleOAuthCallback:
    """測試 OAuth 回調處理"""

    def test_callback_access_denied(self, client):
        """測試使用者拒絕授權"""
        response = client.get(
            "/api/auth/google/callback",
            params={
                "error": "access_denied",
                "error_description": "使用者拒絕了授權"
            }
        )

        assert response.status_code == 400
        assert "授權失敗" in response.text

    def test_callback_missing_code(self, client):
        """測試缺少 code 參數"""
        response = client.get(
            "/api/auth/google/callback",
            params={"state": "some-state"}
        )

        assert response.status_code == 400
        assert "缺少必要參數" in response.json()["detail"]

    def test_callback_missing_state(self, client):
        """測試缺少 state 參數"""
        response = client.get(
            "/api/auth/google/callback",
            params={"code": "some-code"}
        )

        assert response.status_code == 400
        assert "缺少必要參數" in response.json()["detail"]

    def test_callback_invalid_state(self, client):
        """測試無效的 state token"""
        response = client.get(
            "/api/auth/google/callback",
            params={
                "code": "some-auth-code",
                "state": "invalid-state-token"
            }
        )

        assert response.status_code == 400
        assert "無效或過期的 state token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_callback_success(self, client, admin_token, db_session):
        """測試成功的 OAuth 回調"""
        from src.api.google_oauth import _generate_state_token

        # 先生成 state
        with patch('src.api.google_oauth._get_oauth_credentials') as mock_creds:
            mock_creds.return_value = (
                'test-client-id',
                'test-client-secret',
                'http://localhost:8000/api/auth/google/callback'
            )

            # 生成授權 URL 以取得 state
            auth_response = client.get(
                "/api/google/auth-url?department=淡海",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            state = auth_response.json()["state"]

        # Mock token 交換
        mock_token_response = AsyncMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600
        }

        # Mock userinfo
        mock_userinfo_response = AsyncMock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = {
            "email": "test@example.com"
        }

        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_token_response
            mock_client.get.return_value = mock_userinfo_response
            mock_client.__aenter__.return_value = mock_client
            mock_httpx.return_value = mock_client

            with patch('src.api.google_oauth._get_oauth_credentials') as mock_creds:
                mock_creds.return_value = (
                    'test-client-id',
                    'test-client-secret',
                    'http://localhost:8000/api/auth/google/callback'
                )

                response = client.get(
                    "/api/auth/google/callback",
                    params={
                        "code": "valid-auth-code",
                        "state": state
                    }
                )

                # 應該返回成功頁面
                assert response.status_code == 200
                assert "授權成功" in response.text
                assert "淡海" in response.text

    def test_callback_invalid_code(self, client, admin_token):
        """測試無效的 authorization code"""
        from src.api.google_oauth import _generate_state_token

        with patch('src.api.google_oauth._get_oauth_credentials') as mock_creds:
            mock_creds.return_value = (
                'test-client-id',
                'test-client-secret',
                'http://localhost:8000/api/auth/google/callback'
            )

            # 生成授權 URL 以取得 state
            auth_response = client.get(
                "/api/google/auth-url?department=淡海",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            state = auth_response.json()["state"]

        # Mock 失敗的 token 交換
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code"
        }
        mock_response.text = "Invalid authorization code"

        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_httpx.return_value = mock_client

            with patch('src.api.google_oauth._get_oauth_credentials') as mock_creds:
                mock_creds.return_value = (
                    'test-client-id',
                    'test-client-secret',
                    'http://localhost:8000/api/auth/google/callback'
                )

                response = client.get(
                    "/api/auth/google/callback",
                    params={
                        "code": "invalid-auth-code",
                        "state": state
                    }
                )

                assert response.status_code == 400
                assert "Token 交換失敗" in response.json()["detail"]


class TestGoogleOAuthAccessToken:
    """測試 Access Token 取得"""

    def test_get_access_token_not_authorized(self, client, staff_token):
        """測試部門未授權"""
        response = client.post(
            "/api/google/get-access-token?department=淡海",
            headers={"Authorization": f"Bearer {staff_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "尚未完成 OAuth 授權" in data["error_message"]

    def test_get_access_token_invalid_department(self, client, staff_token):
        """測試無效部門"""
        response = client.post(
            "/api/google/get-access-token?department=無效部門",
            headers={"Authorization": f"Bearer {staff_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "無效的部門" in data["error_message"]


class TestGoogleOAuthStatus:
    """測試 OAuth 狀態檢查"""

    def test_get_oauth_status(self, client, staff_token):
        """測試取得 OAuth 狀態"""
        response = client.get(
            "/api/google/oauth-status",
            headers={"Authorization": f"Bearer {staff_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # 淡海 和 安坑

        departments = [item["department"] for item in data]
        assert "淡海" in departments
        assert "安坑" in departments


class TestGoogleOAuthRevoke:
    """測試撤銷授權"""

    def test_revoke_not_authorized(self, client, admin_token):
        """測試撤銷未授權的部門"""
        response = client.delete(
            "/api/google/revoke?department=淡海",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "沒有已授權" in data["message"]

    def test_revoke_invalid_department(self, client, admin_token):
        """測試撤銷無效部門"""
        response = client.delete(
            "/api/google/revoke?department=無效部門",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 400

    def test_revoke_unauthorized_user(self, client, staff_token):
        """測試非 Admin 無法撤銷"""
        response = client.delete(
            "/api/google/revoke?department=淡海",
            headers={"Authorization": f"Bearer {staff_token}"}
        )

        assert response.status_code == 403


class TestTokenEncryptionInOAuth:
    """測試 OAuth 中的 Token 加密"""

    def test_refresh_token_encrypted_storage(self, db_session):
        """測試 refresh_token 加密儲存"""
        from src.models.google_oauth_token import GoogleOAuthToken
        from src.utils.encryption import encrypt_token, decrypt_token

        # 準備測試資料
        test_refresh_token = "test-refresh-token-12345"
        encrypted = encrypt_token(test_refresh_token).encode('utf-8')

        # 建立記錄
        token_record = GoogleOAuthToken(
            department="淡海",
            encrypted_refresh_token=encrypted,
            authorized_user_email="test@example.com"
        )
        db_session.add(token_record)
        db_session.commit()

        # 讀取並解密
        saved_record = db_session.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.department == "淡海"
        ).first()

        decrypted = decrypt_token(saved_record.encrypted_refresh_token.decode('utf-8'))
        assert decrypted == test_refresh_token

        # 清理
        db_session.delete(saved_record)
        db_session.commit()

    def test_encrypted_token_not_plaintext(self, db_session):
        """測試加密的 token 不是明文"""
        from src.utils.encryption import encrypt_token

        test_token = "my-secret-token"
        encrypted = encrypt_token(test_token)

        # 加密後的值應該與原值不同
        assert encrypted != test_token
        # 加密後應該是 base64 格式
        assert len(encrypted) > len(test_token)


class TestStateTokenValidation:
    """測試 State Token 驗證"""

    def test_state_token_expiration(self, client, admin_token):
        """測試 state token 過期"""
        from src.api.google_oauth import _pending_states, _generate_state_token
        from datetime import timedelta

        with patch('src.api.google_oauth._get_oauth_credentials') as mock_creds:
            mock_creds.return_value = (
                'test-client-id',
                'test-client-secret',
                'http://localhost:8000/api/auth/google/callback'
            )

            # 生成授權 URL 以取得 state
            auth_response = client.get(
                "/api/google/auth-url?department=淡海",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            state = auth_response.json()["state"]

            # 修改 state 的建立時間為 15 分鐘前（超過 10 分鐘限制）
            if state in _pending_states:
                _pending_states[state]["created_at"] = (
                    datetime.now(timezone.utc) - timedelta(minutes=15)
                )

            # 嘗試使用過期的 state
            response = client.get(
                "/api/auth/google/callback",
                params={
                    "code": "some-code",
                    "state": state
                }
            )

            assert response.status_code == 400
            assert "無效或過期" in response.json()["detail"]

    def test_state_token_single_use(self, client, admin_token):
        """測試 state token 只能使用一次"""
        from src.api.google_oauth import _pending_states

        with patch('src.api.google_oauth._get_oauth_credentials') as mock_creds:
            mock_creds.return_value = (
                'test-client-id',
                'test-client-secret',
                'http://localhost:8000/api/auth/google/callback'
            )

            auth_response = client.get(
                "/api/google/auth-url?department=淡海",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            state = auth_response.json()["state"]

            # 第一次使用（會失敗因為沒有真正的 OAuth，但 state 會被消費）
            client.get(
                "/api/auth/google/callback",
                params={
                    "code": "some-code",
                    "state": state
                }
            )

            # 第二次使用同樣的 state 應該失敗
            response = client.get(
                "/api/auth/google/callback",
                params={
                    "code": "some-code",
                    "state": state
                }
            )

            assert response.status_code == 400
            assert "無效或過期" in response.json()["detail"]
