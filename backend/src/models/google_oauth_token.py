"""
GoogleOAuthToken OAuth 令牌加密儲存模型
對應 tasks.md T035: 建立 GoogleOAuthToken 模型
對應 spec.md: GoogleOAuthToken (OAuth 令牌加密儲存)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from src.constants import Department
from .base import Base, TimestampMixin


class GoogleOAuthToken(Base, TimestampMixin):
    """
    Google OAuth 令牌加密儲存模型

    用於安全儲存各部門的 Google OAuth 憑證，
    所有敏感資料使用 Fernet 加密後儲存。

    Attributes:
        id: 主鍵
        department: 部門 ('淡海', '安坑')，唯一索引
        encrypted_refresh_token: 加密的 refresh_token (LargeBinary)
        encrypted_access_token: 加密的 access_token (快取用，可為空)
        access_token_expires_at: access_token 到期時間
        authorized_user_email: 授權者的 Google 帳號 Email
        created_at: 建立時間
        updated_at: 更新時間

    Security:
        - encrypted_refresh_token 和 encrypted_access_token 使用 Fernet 加密
        - 加密金鑰儲存於環境變數 ENCRYPTION_KEY
        - 請勿直接存取加密欄位，使用對應的 service 方法
    """

    __tablename__ = "google_oauth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    department: Mapped[str] = mapped_column(
        Enum(Department, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        unique=True,
        index=True,
        comment="部門：淡海、安坑"
    )

    encrypted_refresh_token: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="加密的 refresh_token（使用 Fernet 加密）"
    )

    encrypted_access_token: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
        comment="加密的 access_token（快取用）"
    )

    access_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="access_token 到期時間"
    )

    authorized_user_email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="授權者的 Google 帳號 Email"
    )

    __table_args__ = (
        {"comment": "Google OAuth 令牌加密儲存表"}
    )

    def __repr__(self) -> str:
        return f"<GoogleOAuthToken(department={self.department!r}, email={self.authorized_user_email!r})>"

    @property
    def is_access_token_expired(self) -> bool:
        """檢查 access_token 是否已過期"""
        if self.access_token_expires_at is None:
            return True
        return datetime.now(self.access_token_expires_at.tzinfo) >= self.access_token_expires_at

    @property
    def has_valid_refresh_token(self) -> bool:
        """檢查是否有有效的 refresh_token"""
        return self.encrypted_refresh_token is not None and len(self.encrypted_refresh_token) > 0
