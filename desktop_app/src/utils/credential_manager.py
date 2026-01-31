"""
本機憑證管理器
對應 tasks.md T018: 實作本機憑證管理器

功能：
- OAuth 令牌加密檔案存儲
- 憑證讀取與解密
- 憑證更新與刷新
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken


# 預設憑證儲存位置
DEFAULT_CREDENTIAL_DIR = Path.home() / ".driver_management_system"
TOKEN_FILE_NAME = "tokens.encrypted"
KEY_FILE_NAME = ".key"


class LocalCredentialManager:
    """
    本機憑證管理器

    將 OAuth 令牌以加密形式儲存在本機檔案系統。
    使用 Fernet 對稱加密保護敏感資料。
    """

    def __init__(self, credential_dir: Optional[Path] = None):
        """
        初始化憑證管理器

        Args:
            credential_dir: 憑證儲存目錄，預設為 ~/.driver_management_system
        """
        self._credential_dir = credential_dir or DEFAULT_CREDENTIAL_DIR
        self._token_file = self._credential_dir / TOKEN_FILE_NAME
        self._key_file = self._credential_dir / KEY_FILE_NAME
        self._fernet: Optional[Fernet] = None

        # 確保目錄存在
        self._ensure_directory()

    def _ensure_directory(self):
        """確保憑證目錄存在"""
        self._credential_dir.mkdir(parents=True, exist_ok=True)

        # 設定目錄權限（僅限擁有者）
        if os.name != 'nt':  # Unix 系統
            os.chmod(self._credential_dir, 0o700)

    def _get_or_create_key(self) -> bytes:
        """取得或建立加密金鑰"""
        if self._key_file.exists():
            return self._key_file.read_bytes()

        # 生成新金鑰
        key = Fernet.generate_key()
        self._key_file.write_bytes(key)

        # 設定檔案權限（僅限擁有者）
        if os.name != 'nt':
            os.chmod(self._key_file, 0o600)

        return key

    def _get_fernet(self) -> Fernet:
        """取得 Fernet 加密器"""
        if self._fernet is None:
            key = self._get_or_create_key()
            self._fernet = Fernet(key)
        return self._fernet

    def _load_all_tokens(self) -> Dict[str, Any]:
        """載入所有儲存的令牌"""
        if not self._token_file.exists():
            return {}

        try:
            encrypted_data = self._token_file.read_bytes()
            decrypted_data = self._get_fernet().decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))
        except (InvalidToken, json.JSONDecodeError):
            # 金鑰不匹配或資料損壞，返回空字典
            return {}

    def _save_all_tokens(self, tokens: Dict[str, Any]):
        """儲存所有令牌"""
        data = json.dumps(tokens, ensure_ascii=False, indent=2)
        encrypted_data = self._get_fernet().encrypt(data.encode("utf-8"))
        self._token_file.write_bytes(encrypted_data)

        # 設定檔案權限（僅限擁有者）
        if os.name != 'nt':
            os.chmod(self._token_file, 0o600)

    def save_oauth_token(
        self,
        department: str,
        access_token: str,
        refresh_token: str,
        expires_at: Optional[datetime] = None,
        token_type: str = "Bearer",
        scope: Optional[str] = None
    ):
        """
        儲存 OAuth 令牌

        Args:
            department: 部門（淡海/安坑）
            access_token: Access Token
            refresh_token: Refresh Token
            expires_at: 過期時間
            token_type: Token 類型
            scope: 授權範圍
        """
        tokens = self._load_all_tokens()

        tokens[department] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": token_type,
            "scope": scope,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "updated_at": datetime.now().isoformat()
        }

        self._save_all_tokens(tokens)

    def get_oauth_token(self, department: str) -> Optional[Dict[str, Any]]:
        """
        取得指定部門的 OAuth 令牌

        Args:
            department: 部門（淡海/安坑）

        Returns:
            dict | None: 令牌資料，包含 access_token, refresh_token, expires_at 等
        """
        tokens = self._load_all_tokens()
        token_data = tokens.get(department)

        if token_data and token_data.get("expires_at"):
            # 轉換過期時間為 datetime
            token_data["expires_at"] = datetime.fromisoformat(token_data["expires_at"])

        return token_data

    def get_access_token(self, department: str) -> Optional[str]:
        """
        取得指定部門的 Access Token

        Args:
            department: 部門（淡海/安坑）

        Returns:
            str | None: Access Token
        """
        token_data = self.get_oauth_token(department)
        return token_data.get("access_token") if token_data else None

    def get_refresh_token(self, department: str) -> Optional[str]:
        """
        取得指定部門的 Refresh Token

        Args:
            department: 部門（淡海/安坑）

        Returns:
            str | None: Refresh Token
        """
        token_data = self.get_oauth_token(department)
        return token_data.get("refresh_token") if token_data else None

    def is_token_expired(self, department: str) -> bool:
        """
        檢查指定部門的 Token 是否已過期

        Args:
            department: 部門（淡海/安坑）

        Returns:
            bool: True 表示已過期或不存在
        """
        token_data = self.get_oauth_token(department)
        if not token_data:
            return True

        expires_at = token_data.get("expires_at")
        if not expires_at:
            return False  # 沒有過期時間，假設未過期

        # 提前 5 分鐘視為過期（預留刷新時間）
        from datetime import timedelta
        buffer_time = timedelta(minutes=5)
        return datetime.now() >= (expires_at - buffer_time)

    def update_access_token(
        self,
        department: str,
        access_token: str,
        expires_at: Optional[datetime] = None
    ):
        """
        更新 Access Token（保留 Refresh Token）

        Args:
            department: 部門
            access_token: 新的 Access Token
            expires_at: 新的過期時間
        """
        tokens = self._load_all_tokens()

        if department not in tokens:
            raise ValueError(f"部門 {department} 的憑證不存在")

        tokens[department]["access_token"] = access_token
        tokens[department]["expires_at"] = expires_at.isoformat() if expires_at else None
        tokens[department]["updated_at"] = datetime.now().isoformat()

        self._save_all_tokens(tokens)

    def delete_token(self, department: str):
        """
        刪除指定部門的令牌

        Args:
            department: 部門（淡海/安坑）
        """
        tokens = self._load_all_tokens()

        if department in tokens:
            del tokens[department]
            self._save_all_tokens(tokens)

    def delete_all_tokens(self):
        """刪除所有令牌"""
        if self._token_file.exists():
            self._token_file.unlink()

    def list_departments(self) -> list:
        """
        列出所有已儲存憑證的部門

        Returns:
            list: 部門列表
        """
        tokens = self._load_all_tokens()
        return list(tokens.keys())

    def has_token(self, department: str) -> bool:
        """
        檢查指定部門是否有儲存的憑證

        Args:
            department: 部門

        Returns:
            bool: True 表示有儲存的憑證
        """
        return department in self._load_all_tokens()


# 單例實例
_manager_instance: Optional[LocalCredentialManager] = None


def get_credential_manager() -> LocalCredentialManager:
    """取得憑證管理器實例（單例）"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = LocalCredentialManager()
    return _manager_instance
