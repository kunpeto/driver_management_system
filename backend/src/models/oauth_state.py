"""
OAuth State Token 模型
對應 Gemini Code Review 修復: Critical - OAuth State 儲存機制

功能：
- 儲存 OAuth 授權流程的 state token
- 支援過期時間和自動清理
- 確保 state token 的一次性使用
- 解決多 worker 部署和伺服器重啟問題
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, Index
from src.models.base import Base


class OAuthState(Base):
    """OAuth State Token 模型"""

    __tablename__ = "oauth_states"

    # 欄位
    state = Column(String(255), primary_key=True, comment="State token（隨機產生）")
    department = Column(String(50), nullable=False, comment="部門（淡海/安坑）")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="建立時間")
    expires_at = Column(DateTime, nullable=False, comment="過期時間")
    used = Column(Boolean, nullable=False, default=False, comment="是否已使用")
    used_at = Column(DateTime, nullable=True, comment="使用時間")

    # 索引
    __table_args__ = (
        Index('idx_oauth_states_expires_at', 'expires_at'),
        Index('idx_oauth_states_department', 'department'),
    )

    def is_valid(self) -> bool:
        """
        檢查 state token 是否有效

        Returns:
            bool: True 表示有效，False 表示無效
        """
        now = datetime.now(timezone.utc)

        # 檢查是否已過期
        if now > self.expires_at:
            return False

        # 檢查是否已使用
        if self.used:
            return False

        return True

    def mark_as_used(self) -> None:
        """標記 state token 為已使用"""
        self.used = True
        self.used_at = datetime.now(timezone.utc)

    @classmethod
    def create_state(
        cls,
        state: str,
        department: str,
        expires_in_minutes: int = 10
    ) -> "OAuthState":
        """
        建立新的 OAuth state token

        Args:
            state: State token 字串
            department: 部門名稱
            expires_in_minutes: 過期時間（分鐘），預設 10 分鐘

        Returns:
            OAuthState 實例
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expires_in_minutes)

        return cls(
            state=state,
            department=department,
            created_at=now,
            expires_at=expires_at,
            used=False
        )

    @classmethod
    def cleanup_expired(cls, db_session) -> int:
        """
        清理已過期的 state tokens

        Args:
            db_session: 資料庫 session

        Returns:
            int: 清理的數量
        """
        now = datetime.now(timezone.utc)

        # 刪除過期的 tokens
        count = db_session.query(cls).filter(
            cls.expires_at < now
        ).delete(synchronize_session=False)

        db_session.commit()

        return count

    def __repr__(self):
        return f"<OAuthState(state='{self.state[:8]}...', department='{self.department}', valid={self.is_valid()})>"
