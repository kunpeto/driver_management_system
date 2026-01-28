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
    api_environment: Literal["development", "production"] = Field(default="development")

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

    # 加密金鑰（Fernet）
    encryption_key: str = Field(default="")

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


@lru_cache
def get_settings() -> Settings:
    """取得設定（快取）"""
    return Settings()
