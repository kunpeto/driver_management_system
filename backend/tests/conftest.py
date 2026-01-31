"""
pytest 配置文件

提供測試所需的 fixtures 和配置。
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# 確保 backend 目錄在 Python 路徑中（使 from src.xxx import 能正確運作）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """
    自動模擬環境變數設定

    避免測試時讀取真實的 .env 文件或環境變數。
    """
    # 設定測試用環境變數
    test_env = {
        "API_ENVIRONMENT": "development",
        "API_SECRET_KEY": "test-secret-key-for-testing-only-minimum-32-chars",
        "ENCRYPTION_KEY": "5dLk2n5Gp3fIUoZBDyirPRDoMzBvPkGD3jfPusFclEw=",
        "TIDB_HOST": "localhost",
        "TIDB_PORT": "4000",
        "TIDB_USER": "test",
        "TIDB_PASSWORD": "test",
        "TIDB_DATABASE": "test",
        "GOOGLE_OAUTH_CLIENT_ID": "test-client-id",
        "GOOGLE_OAUTH_CLIENT_SECRET": "test-client-secret",
        "GOOGLE_OAUTH_REDIRECT_URI": "http://localhost:8000/api/auth/google/callback",
        "API_BASE_URL": "http://localhost:8000",
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


@pytest.fixture
def db_session():
    """
    提供測試用的資料庫 session

    使用 SQLite 記憶體資料庫進行測試
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.models.base import Base

    # 使用 SQLite 記憶體資料庫
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # 建立所有表
    Base.metadata.create_all(engine)

    # 建立 session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()

    yield session

    # 清理
    session.close()


@pytest.fixture
def client(db_session):
    """
    提供測試用的 FastAPI TestClient
    """
    from fastapi.testclient import TestClient
    from src.main import app
    from src.config.database import get_db

    # 覆蓋資料庫依賴
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # 清理
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """
    建立測試用的 Admin 使用者
    """
    from src.models.user import User
    from src.utils.password import hash_password

    user = User(
        username="admin_test",
        password_hash=hash_password("admin123"),
        role="admin",
        department="淡海",
        is_active=True,
        display_name="測試管理員"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def staff_user(db_session):
    """
    建立測試用的 Staff 使用者
    """
    from src.models.user import User
    from src.utils.password import hash_password

    user = User(
        username="staff_test",
        password_hash=hash_password("staff123"),
        role="staff",
        department="淡海",
        is_active=True,
        display_name="測試值班員"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """
    取得 Admin 使用者的 JWT Token
    """
    response = client.post(
        "/api/auth/login",
        json={
            "username": "admin_test",
            "password": "admin123"
        }
    )

    if response.status_code == 200:
        return response.json()["access_token"]

    # 如果登入失敗，直接生成 token
    from src.utils.jwt import create_access_token

    return create_access_token({
        "sub": str(admin_user.id),
        "username": admin_user.username,
        "role": admin_user.role,
        "department": admin_user.department
    })


@pytest.fixture
def staff_token(client, staff_user):
    """
    取得 Staff 使用者的 JWT Token
    """
    response = client.post(
        "/api/auth/login",
        json={
            "username": "staff_test",
            "password": "staff123"
        }
    )

    if response.status_code == 200:
        return response.json()["access_token"]

    # 如果登入失敗，直接生成 token
    from src.utils.jwt import create_access_token

    return create_access_token({
        "sub": str(staff_user.id),
        "username": staff_user.username,
        "role": staff_user.role,
        "department": staff_user.department
    })


@pytest.fixture
def mock_google_oauth_credentials():
    """
    模擬 Google OAuth 憑證
    """
    with patch('src.api.google_oauth._get_oauth_credentials') as mock:
        mock.return_value = (
            'test-client-id',
            'test-client-secret',
            'http://localhost:8000/api/auth/google/callback'
        )
        yield mock
