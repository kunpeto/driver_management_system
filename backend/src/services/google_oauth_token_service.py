"""
GoogleOAuthTokenService - Google OAuth 令牌服務
修復 Gemini Review High Priority #1: Credential 儲存機制

提供 Google OAuth 令牌的加密儲存與讀取功能。
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.models.google_oauth_token import Department, GoogleOAuthToken
from src.utils.encryption import TokenEncryption


class GoogleOAuthTokenServiceError(Exception):
    """Google OAuth Token 服務錯誤"""
    pass


class TokenNotFoundError(GoogleOAuthTokenServiceError):
    """令牌不存在錯誤"""
    pass


class EncryptionError(GoogleOAuthTokenServiceError):
    """加密/解密錯誤"""
    pass


class GoogleOAuthTokenService:
    """
    Google OAuth 令牌服務

    提供令牌的加密儲存、讀取、更新功能。
    所有敏感資料使用 Fernet 加密後儲存。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self._encryption = TokenEncryption()

    # ============================================================
    # 儲存與更新
    # ============================================================

    def save_refresh_token(
        self,
        department: str,
        refresh_token: str,
        authorized_email: Optional[str] = None
    ) -> GoogleOAuthToken:
        """
        儲存 Refresh Token（加密後）

        Args:
            department: 部門名稱 ('淡海', '安坑')
            refresh_token: 原始 refresh_token
            authorized_email: 授權者 Email

        Returns:
            GoogleOAuthToken: 儲存的令牌記錄

        Raises:
            EncryptionError: 加密失敗
        """
        # 驗證部門
        self._validate_department(department)

        # 加密 refresh_token
        try:
            encrypted_token = self._encryption.encrypt(refresh_token)
        except Exception as e:
            raise EncryptionError(f"加密 refresh_token 失敗: {str(e)}")

        # 查詢是否已存在
        existing = self.get_by_department(department)

        if existing:
            # 更新現有記錄
            existing.encrypted_refresh_token = encrypted_token
            existing.encrypted_access_token = None  # 清除舊的 access_token
            existing.access_token_expires_at = None
            if authorized_email:
                existing.authorized_user_email = authorized_email
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # 建立新記錄
            token = GoogleOAuthToken(
                department=department,
                encrypted_refresh_token=encrypted_token,
                authorized_user_email=authorized_email
            )
            self.db.add(token)
            self.db.commit()
            self.db.refresh(token)
            return token

    def save_access_token(
        self,
        department: str,
        access_token: str,
        expires_at: datetime
    ) -> GoogleOAuthToken:
        """
        儲存 Access Token（快取用）

        Args:
            department: 部門名稱
            access_token: 原始 access_token
            expires_at: 到期時間

        Returns:
            GoogleOAuthToken: 更新後的令牌記錄

        Raises:
            TokenNotFoundError: 部門的 refresh_token 不存在
            EncryptionError: 加密失敗
        """
        token = self.get_by_department(department)
        if not token:
            raise TokenNotFoundError(f"部門 '{department}' 的憑證不存在，請先儲存 refresh_token")

        # 加密 access_token
        try:
            encrypted_token = self._encryption.encrypt(access_token)
        except Exception as e:
            raise EncryptionError(f"加密 access_token 失敗: {str(e)}")

        token.encrypted_access_token = encrypted_token
        token.access_token_expires_at = expires_at

        self.db.commit()
        self.db.refresh(token)
        return token

    def save_service_account_json(
        self,
        department: str,
        base64_json: str,
        authorized_email: Optional[str] = None
    ) -> GoogleOAuthToken:
        """
        儲存 Service Account JSON（Base64 編碼後加密）

        這是用於儲存完整的 Service Account 憑證 JSON。

        Args:
            department: 部門名稱
            base64_json: Base64 編碼的 Service Account JSON
            authorized_email: 授權者/管理者 Email

        Returns:
            GoogleOAuthToken: 儲存的令牌記錄
        """
        # Service Account JSON 直接當作 refresh_token 儲存
        # 因為 Service Account 不需要 refresh，這裡借用欄位儲存完整 JSON
        return self.save_refresh_token(department, base64_json, authorized_email)

    # ============================================================
    # 讀取
    # ============================================================

    def get_by_department(self, department: str) -> Optional[GoogleOAuthToken]:
        """
        根據部門取得令牌記錄

        Args:
            department: 部門名稱

        Returns:
            GoogleOAuthToken 或 None
        """
        return self.db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.department == department
        ).first()

    def get_refresh_token(self, department: str) -> Optional[str]:
        """
        取得解密後的 Refresh Token

        Args:
            department: 部門名稱

        Returns:
            解密後的 refresh_token 或 None
        """
        token = self.get_by_department(department)
        if not token or not token.encrypted_refresh_token:
            return None

        try:
            return self._encryption.decrypt(token.encrypted_refresh_token)
        except Exception:
            return None

    def get_access_token(self, department: str) -> Optional[str]:
        """
        取得解密後的 Access Token（若未過期）

        Args:
            department: 部門名稱

        Returns:
            解密後的 access_token 或 None（若過期或不存在）
        """
        token = self.get_by_department(department)
        if not token or not token.encrypted_access_token:
            return None

        # 檢查是否過期
        if token.is_access_token_expired:
            return None

        try:
            return self._encryption.decrypt(token.encrypted_access_token)
        except Exception:
            return None

    def get_service_account_json(self, department: str) -> Optional[str]:
        """
        取得解密後的 Service Account JSON

        Args:
            department: 部門名稱

        Returns:
            Base64 編碼的 Service Account JSON 或 None
        """
        return self.get_refresh_token(department)

    # ============================================================
    # 刪除
    # ============================================================

    def delete(self, department: str) -> bool:
        """
        刪除部門的憑證

        Args:
            department: 部門名稱

        Returns:
            bool: 是否成功刪除
        """
        token = self.get_by_department(department)
        if not token:
            return False

        self.db.delete(token)
        self.db.commit()
        return True

    def clear_access_token(self, department: str) -> bool:
        """
        清除部門的 access_token 快取

        Args:
            department: 部門名稱

        Returns:
            bool: 是否成功清除
        """
        token = self.get_by_department(department)
        if not token:
            return False

        token.encrypted_access_token = None
        token.access_token_expires_at = None
        self.db.commit()
        return True

    # ============================================================
    # 查詢
    # ============================================================

    def list_all(self) -> list[GoogleOAuthToken]:
        """
        列出所有部門的憑證記錄

        Returns:
            list[GoogleOAuthToken]: 所有憑證記錄（不含解密資料）
        """
        return self.db.query(GoogleOAuthToken).all()

    def has_credential(self, department: str) -> bool:
        """
        檢查部門是否已設定憑證

        Args:
            department: 部門名稱

        Returns:
            bool: 是否已設定
        """
        token = self.get_by_department(department)
        return token is not None and token.has_valid_refresh_token

    def get_credential_status(self) -> dict:
        """
        取得所有部門的憑證狀態

        Returns:
            dict: 各部門的憑證狀態
        """
        result = {}
        for dept in [Department.DANHAI.value, Department.ANKENG.value]:
            token = self.get_by_department(dept)
            if token:
                result[dept] = {
                    "has_credential": token.has_valid_refresh_token,
                    "authorized_email": token.authorized_user_email,
                    "updated_at": token.updated_at.isoformat() if token.updated_at else None
                }
            else:
                result[dept] = {
                    "has_credential": False,
                    "authorized_email": None,
                    "updated_at": None
                }
        return result

    # ============================================================
    # 輔助方法
    # ============================================================

    def _validate_department(self, department: str) -> None:
        """驗證部門名稱"""
        valid_departments = [Department.DANHAI.value, Department.ANKENG.value]
        if department not in valid_departments:
            raise GoogleOAuthTokenServiceError(
                f"無效的部門名稱 '{department}'，有效值為：{valid_departments}"
            )
