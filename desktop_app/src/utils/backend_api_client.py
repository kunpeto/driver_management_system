"""
後端 API 客戶端
對應 Gemini Code Review 修復: 從後端同步系統設定

功能：
- 從後端 API 讀取系統設定
- 取得各部門的 Google Drive Folder ID
- 快取設定以減少 API 呼叫
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import httpx

logger = logging.getLogger(__name__)


class BackendApiClient:
    """後端 API 客戶端"""

    def __init__(self, base_url: Optional[str] = None):
        """
        初始化客戶端

        Args:
            base_url: 後端 API 基礎 URL，預設從環境變數讀取
        """
        self.base_url = base_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        self._cache: Dict[str, any] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)

    def _get_from_cache(self, key: str) -> Optional[any]:
        """從快取取得值"""
        if key in self._cache:
            if key in self._cache_expiry and datetime.now() < self._cache_expiry[key]:
                return self._cache[key]
            else:
                # 快取過期，清除
                self._cache.pop(key, None)
                self._cache_expiry.pop(key, None)
        return None

    def _set_to_cache(self, key: str, value: any):
        """設定快取值"""
        self._cache[key] = value
        self._cache_expiry[key] = datetime.now() + self._cache_ttl

    def get_system_setting(self, key: str, department: Optional[str] = None) -> Optional[str]:
        """
        從後端取得系統設定

        Args:
            key: 設定鍵值
            department: 部門名稱（淡海/安坑），None 表示全域設定

        Returns:
            Optional[str]: 設定值，失敗則返回 None
        """
        cache_key = f"setting_{key}_{department or 'global'}"

        # 檢查快取
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            params = {"key": key}
            if department:
                params["department"] = department

            response = httpx.get(
                f"{self.base_url}/api/system-settings",
                params=params,
                timeout=5.0
            )

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    value = data[0].get("value")
                    self._set_to_cache(cache_key, value)
                    return value

        except Exception as e:
            logger.warning(f"取得系統設定失敗: {key}, {e}")

        return None

    def get_drive_folder_id(self, department: str) -> Optional[str]:
        """
        取得指定部門的 Google Drive Folder ID

        Args:
            department: 部門名稱（淡海 或 安坑）

        Returns:
            Optional[str]: Folder ID，失敗則返回 None
        """
        return self.get_system_setting("google_drive_folder_id", department)

    def clear_cache(self):
        """清除所有快取"""
        self._cache.clear()
        self._cache_expiry.clear()


# 單例模式
_backend_client: Optional[BackendApiClient] = None


def get_backend_client(base_url: Optional[str] = None) -> BackendApiClient:
    """取得後端 API 客戶端（單例）"""
    global _backend_client
    if _backend_client is None:
        _backend_client = BackendApiClient(base_url)
    return _backend_client
