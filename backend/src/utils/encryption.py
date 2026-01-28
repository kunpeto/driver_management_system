"""
加密工具
對應 tasks.md T016: 實作 TokenEncryption 類別

使用 Fernet 對稱加密演算法加密/解密敏感資料，
主要用於加密 OAuth refresh_token 等敏感憑證。
"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from src.config.settings import get_settings


class TokenEncryption:
    """
    Token 加密/解密工具類別

    使用 Fernet 對稱加密，金鑰從環境變數讀取。
    如果未設定金鑰，會自動生成一個（僅適用於開發環境）。
    """

    _instance: Optional["TokenEncryption"] = None
    _fernet: Optional[Fernet] = None

    def __new__(cls) -> "TokenEncryption":
        """單例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """
        初始化加密器

        重要（Gemini Review 2026-01-28）：
        開發環境也必須設定固定的 ENCRYPTION_KEY，否則會拋出錯誤。
        這是為了避免重啟後已加密的資料（如 DB 中的 Token）無法解密。
        """
        settings = get_settings()
        encryption_key = settings.encryption_key

        if not encryption_key:
            # 無論開發或生產環境，都必須設定 ENCRYPTION_KEY
            error_msg = (
                "ENCRYPTION_KEY 環境變數未設定。\n\n"
                "解決方法：\n"
                "1. 執行以下命令生成新金鑰：\n"
                "   python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"\n\n"
                "2. 將生成的金鑰加入 .env 檔案：\n"
                "   ENCRYPTION_KEY=your-generated-key-here\n\n"
                "注意：開發環境也必須使用固定金鑰，否則重啟後已加密的資料將無法解密。"
            )
            raise ValueError(error_msg)

        # 確保金鑰格式正確（32 bytes base64 encoded）
        try:
            # 嘗試將金鑰轉換為 bytes
            if isinstance(encryption_key, str):
                key_bytes = encryption_key.encode()
            else:
                key_bytes = encryption_key

            self._fernet = Fernet(key_bytes)
        except Exception as e:
            raise ValueError(
                f"ENCRYPTION_KEY 格式無效: {e}。"
                "請使用 TokenEncryption.generate_key() 生成有效的金鑰。"
            )

    @staticmethod
    def generate_key() -> str:
        """
        生成新的加密金鑰

        Returns:
            str: Base64 編碼的 Fernet 金鑰（32 bytes）
        """
        return Fernet.generate_key().decode()

    def encrypt(self, plaintext: str) -> str:
        """
        加密字串

        Args:
            plaintext: 要加密的明文字串

        Returns:
            str: Base64 編碼的加密資料
        """
        if not plaintext:
            return ""

        encrypted_bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """
        解密字串

        Args:
            ciphertext: Base64 編碼的加密資料

        Returns:
            str: 解密後的明文字串

        Raises:
            InvalidToken: 金鑰不正確或資料已損壞
        """
        if not ciphertext:
            return ""

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            raise ValueError("解密失敗：金鑰不正確或資料已損壞")

    def encrypt_dict(self, data: dict) -> dict:
        """
        加密字典中的所有字串值

        Args:
            data: 要加密的字典

        Returns:
            dict: 加密後的字典（鍵不變，值被加密）
        """
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            elif isinstance(value, dict):
                encrypted[key] = self.encrypt_dict(value)
            else:
                encrypted[key] = value
        return encrypted

    def decrypt_dict(self, data: dict) -> dict:
        """
        解密字典中的所有加密值

        Args:
            data: 加密的字典

        Returns:
            dict: 解密後的字典
        """
        decrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    decrypted[key] = self.decrypt(value)
                except ValueError:
                    # 如果解密失敗，保留原值（可能不是加密的）
                    decrypted[key] = value
            elif isinstance(value, dict):
                decrypted[key] = self.decrypt_dict(value)
            else:
                decrypted[key] = value
        return decrypted


# 便捷函數
def get_encryption() -> TokenEncryption:
    """取得加密器實例"""
    return TokenEncryption()


def encrypt_token(token: str) -> str:
    """加密 Token"""
    return get_encryption().encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """解密 Token"""
    return get_encryption().decrypt(encrypted_token)
