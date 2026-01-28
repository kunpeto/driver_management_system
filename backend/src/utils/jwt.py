"""
JWT 工具類別
對應 tasks.md T019: 建立 JWT 工具類別

功能：
- 生成 JWT Access Token
- 驗證 Token 有效性
- 解析 Token Payload
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import jwt, JWTError, ExpiredSignatureError

from src.config.settings import get_settings


class JWTHandler:
    """
    JWT Token 處理器

    用於生成、驗證、解析 JWT Token。
    Token payload 包含 user_id, username, role, department。
    """

    def __init__(self):
        self._settings = get_settings()

    @property
    def secret_key(self) -> str:
        """取得 JWT 簽署金鑰"""
        return self._settings.api_secret_key

    @property
    def algorithm(self) -> str:
        """取得 JWT 演算法"""
        return self._settings.jwt_algorithm

    @property
    def expire_minutes(self) -> int:
        """取得 Token 過期時間（分鐘）"""
        return self._settings.jwt_expire_minutes

    def create_access_token(
        self,
        user_id: int,
        username: str,
        role: str,
        department: Optional[str] = None,
        extra_data: Optional[dict] = None
    ) -> str:
        """
        建立 JWT Access Token

        Args:
            user_id: 使用者 ID
            username: 使用者名稱
            role: 角色（admin/staff/manager）
            department: 部門（淡海/安坑/None 表示全部）
            extra_data: 額外資料

        Returns:
            str: JWT Token 字串
        """
        # 計算過期時間
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)

        # 建立 payload
        payload = {
            "sub": str(user_id),  # Subject (用戶 ID)
            "username": username,
            "role": role,
            "department": department,
            "exp": expire,
            "iat": datetime.now(timezone.utc),  # Issued at
            "type": "access"
        }

        # 添加額外資料
        if extra_data:
            payload.update(extra_data)

        # 編碼並返回
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: int,
        expire_days: int = 7
    ) -> str:
        """
        建立 JWT Refresh Token

        Args:
            user_id: 使用者 ID
            expire_days: 過期天數（預設 7 天）

        Returns:
            str: JWT Refresh Token 字串
        """
        expire = datetime.now(timezone.utc) + timedelta(days=expire_days)

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        """
        驗證並解析 JWT Token

        Args:
            token: JWT Token 字串

        Returns:
            dict: Token payload

        Raises:
            JWTError: Token 無效
            ExpiredSignatureError: Token 已過期
        """
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm]
        )

    def decode_token(self, token: str) -> Optional[dict]:
        """
        解析 JWT Token（不驗證簽名）

        用於檢查 Token 內容，例如檢查是否過期。

        Args:
            token: JWT Token 字串

        Returns:
            dict | None: Token payload，如果解析失敗則返回 None
        """
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": False}
            )
        except JWTError:
            return None

    def get_user_id(self, token: str) -> Optional[int]:
        """
        從 Token 取得使用者 ID

        Args:
            token: JWT Token 字串

        Returns:
            int | None: 使用者 ID，如果解析失敗則返回 None
        """
        try:
            payload = self.verify_token(token)
            return int(payload.get("sub"))
        except (JWTError, TypeError, ValueError):
            return None

    def get_user_role(self, token: str) -> Optional[str]:
        """
        從 Token 取得使用者角色

        Args:
            token: JWT Token 字串

        Returns:
            str | None: 使用者角色，如果解析失敗則返回 None
        """
        try:
            payload = self.verify_token(token)
            return payload.get("role")
        except JWTError:
            return None

    def get_user_department(self, token: str) -> Optional[str]:
        """
        從 Token 取得使用者部門

        Args:
            token: JWT Token 字串

        Returns:
            str | None: 使用者部門，如果解析失敗則返回 None
        """
        try:
            payload = self.verify_token(token)
            return payload.get("department")
        except JWTError:
            return None

    def is_token_expired(self, token: str) -> bool:
        """
        檢查 Token 是否已過期

        Args:
            token: JWT Token 字串

        Returns:
            bool: True 表示已過期或無效
        """
        try:
            self.verify_token(token)
            return False
        except ExpiredSignatureError:
            return True
        except JWTError:
            return True

    def is_access_token(self, token: str) -> bool:
        """
        檢查是否為 Access Token

        Args:
            token: JWT Token 字串

        Returns:
            bool: True 表示是 Access Token
        """
        payload = self.decode_token(token)
        return payload is not None and payload.get("type") == "access"

    def is_refresh_token(self, token: str) -> bool:
        """
        檢查是否為 Refresh Token

        Args:
            token: JWT Token 字串

        Returns:
            bool: True 表示是 Refresh Token
        """
        payload = self.decode_token(token)
        return payload is not None and payload.get("type") == "refresh"


# 單例實例
_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """取得 JWT 處理器實例（單例）"""
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
    return _jwt_handler


# 便捷函數
def create_access_token(
    user_id: int,
    username: str,
    role: str,
    department: Optional[str] = None
) -> str:
    """建立 Access Token"""
    return get_jwt_handler().create_access_token(user_id, username, role, department)


def verify_token(token: str) -> dict:
    """驗證並解析 Token"""
    return get_jwt_handler().verify_token(token)


def get_user_id_from_token(token: str) -> Optional[int]:
    """從 Token 取得使用者 ID"""
    return get_jwt_handler().get_user_id(token)
