"""
pytest 配置文件

提供測試所需的 fixtures 和配置。
"""

import os
import sys
import pytest

# 確保 src 目錄在 Python 路徑中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """
    自動模擬環境變數設定

    避免測試時讀取真實的 .env 文件或環境變數。
    """
    # 設定測試用環境變數
    # 注意：api_environment 只接受 'development' 或 'production'
    test_env = {
        "API_ENVIRONMENT": "development",
        "API_SECRET_KEY": "test-secret-key-for-testing-only-minimum-32-chars",
        "ENCRYPTION_KEY": "5dLk2n5Gp3fIUoZBDyirPRDoMzBvPkGD3jfPusFclEw=",  # 測試用 Fernet 金鑰
        "TIDB_HOST": "localhost",
        "TIDB_PORT": "4000",
        "TIDB_USER": "test",
        "TIDB_PASSWORD": "test",
        "TIDB_DATABASE": "test",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def sample_service_account():
    """提供測試用的 Service Account 結構"""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key123",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
