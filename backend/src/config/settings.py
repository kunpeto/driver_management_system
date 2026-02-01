"""
環境變數配置
對應 tasks.md T013: 建立環境變數載入工具
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用程式設定"""

    model_config = SettingsConfigDict(
        # 嘗試多個 .env 位置：當前目錄、父目錄（本機開發時）
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # TiDB 資料庫連線
    tidb_host: str = Field(default="gateway01.ap-northeast-1.prod.aws.tidbcloud.com")
    tidb_port: int = Field(default=4000)
    tidb_user: str = Field(default="")
    tidb_password: str = Field(default="")
    tidb_database: str = Field(default="test")

    # FastAPI 設定
    api_secret_key: str = Field(default="development-secret-key-change-in-production")
    api_environment: Literal["development", "production", "test"] = Field(default="development")

    def validate_production_settings(self) -> list[str]:
        """
        驗證生產環境必要設定

        Returns:
            警告訊息列表（空列表表示驗證通過）
        """
        warnings = []

        # 生產環境必須更換預設 Secret Key
        if self.is_production and self.api_secret_key == "development-secret-key-change-in-production":
            warnings.append(
                "🔴 CRITICAL: API_SECRET_KEY 使用預設值！"
                "生產環境必須設定安全的隨機密鑰。"
            )

        # 生產環境必須設定資料庫帳密
        if self.is_production:
            if not self.tidb_user:
                warnings.append("🔴 CRITICAL: TIDB_USER 未設定！")
            if not self.tidb_password:
                warnings.append("🔴 CRITICAL: TIDB_PASSWORD 未設定！")

        # 生產環境建議設定加密金鑰
        if self.is_production and not self.encryption_key:
            warnings.append(
                "🟠 WARNING: ENCRYPTION_KEY 未設定，"
                "Google OAuth Token 加密功能將無法使用。"
            )

        return warnings

    # JWT 設定
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=1440)  # 24 小時

    # Google Sheets 服務帳戶憑證（Base64 編碼）
    tanhae_google_service_account_json: str = Field(default="")
    anping_google_service_account_json: str = Field(default="")

    # Google Sheets ID
    tanhae_google_sheets_id_schedule: str = Field(default="")
    tanhae_google_sheets_id_duty: str = Field(default="")
    anping_google_sheets_id_schedule: str = Field(default="")
    anping_google_sheets_id_duty: str = Field(default="")

    # Google Drive 資料夾 ID
    tanhae_google_drive_folder_id_type1: str = Field(default="")
    tanhae_google_drive_folder_id_type2: str = Field(default="")
    tanhae_google_drive_folder_id_type3: str = Field(default="")
    tanhae_google_drive_folder_id_type4: str = Field(default="")
    anping_google_drive_folder_id_type1: str = Field(default="")
    anping_google_drive_folder_id_type2: str = Field(default="")
    anping_google_drive_folder_id_type3: str = Field(default="")
    anping_google_drive_folder_id_type4: str = Field(default="")

    # Google OAuth 2.0
    google_oauth_client_id: str = Field(default="")
    google_oauth_client_secret: str = Field(default="")
    google_oauth_redirect_uri: str = Field(default="http://localhost:8000/api/auth/google/callback")

    # API 基礎 URL（用於 OAuth 回調等）
    api_base_url: str = Field(default="http://localhost:8000")

    # 加密金鑰（Fernet）
    encryption_key: str = Field(default="")

    # CORS 允許來源（生產環境可透過環境變數擴充，以逗號分隔）
    cors_allowed_origins: str = Field(default="")

    @property
    def database_url(self) -> str:
        """取得資料庫連線 URL（SQLAlchemy 格式）"""
        return (
            f"mysql+pymysql://{self.tidb_user}:{self.tidb_password}"
            f"@{self.tidb_host}:{self.tidb_port}/{self.tidb_database}"
            f"?ssl_verify_cert=true&ssl_verify_identity=true"
        )

    @property
    def is_production(self) -> bool:
        """是否為生產環境"""
        return self.api_environment == "production"

    def get_cors_origins(self) -> list[str]:
        """
        取得 CORS 允許來源清單

        Returns:
            CORS 允許的來源清單
        """
        if self.cors_allowed_origins:
            # 從環境變數讀取（以逗號分隔）
            return [origin.strip() for origin in self.cors_allowed_origins.split(",")]

        # 預設值
        if self.is_production:
            return ["https://kunpeto.github.io"]
        else:
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]


@lru_cache
def get_settings() -> Settings:
    """取得設定（快取）"""
    return Settings()
