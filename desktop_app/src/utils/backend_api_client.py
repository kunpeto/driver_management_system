"""
後端 API 客戶端
對應 Gemini Code Review 修復: 從後端同步系統設定

功能：
- 從後端 API 讀取系統設定
- 取得各部門的 Google Drive Folder ID
- 快取設定以減少 API 呼叫

API CONTRACT 依賴：
- GET /api/settings/value/{key} [CRITICAL]
  此端點被本客戶端直接依賴，詳見 docs/API_CONTRACT.md
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import httpx

logger = logging.getLogger(__name__)

# API 契約版本常數
API_CONTRACT_VERSION = "1.0.0"
MIN_BACKEND_VERSION = "1.0.0"


@dataclass
class VersionCheckResult:
    """版本檢查結果"""
    compatible: bool
    backend_version: Optional[str] = None
    backend_reachable: bool = False
    error_message: Optional[str] = None


def _parse_version(version_str: str) -> Tuple[int, int, int]:
    """
    解析版本字串為元組

    Args:
        version_str: 版本字串，如 "1.0.0" 或 "1.x.x"

    Returns:
        Tuple[int, int, int]: (major, minor, patch)
    """
    parts = version_str.replace("x", "0").split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return (major, minor, patch)


class BackendApiClient:
    """後端 API 客戶端"""

    def __init__(self, base_url: Optional[str] = None):
        """
        初始化客戶端

        Args:
            base_url: 後端 API 基礎 URL，預設從環境變數讀取
        """
        self.base_url = base_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        self.timeout = 15.0  # 從 5 秒調整為 15 秒，提高網路不穩定時的容錯能力
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

        API CONTRACT: CRITICAL
        ENDPOINT: GET /api/settings/value/{key}
        SINCE: 1.0.0

        警告：此方法依賴後端的 /api/settings/value/{key} 端點
        該端點為 CRITICAL 契約，不可修改其回應格式
        詳見 docs/API_CONTRACT.md

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
            # 使用 /api/settings/value/{key} 端點（CRITICAL CONTRACT）
            # 回應格式: {"key": "...", "department": "...", "value": "..."}
            url = f"{self.base_url}/api/settings/value/{key}"
            params = {}
            if department:
                params["department"] = department

            response = httpx.get(
                url,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                # 契約保證回應包含 "value" 欄位
                value = data.get("value")
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

    def get_domain_for_permission(self) -> Optional[str]:
        """
        取得用於 Google Drive 權限設定的網域

        Returns:
            Optional[str]: 網域名稱（例如 "metro.taipei"），未設定則返回 None
        """
        return self.get_system_setting("google_drive_domain")

    def clear_cache(self):
        """清除所有快取"""
        self._cache.clear()
        self._cache_expiry.clear()

    def check_backend_compatibility(self) -> VersionCheckResult:
        """
        檢查後端版本是否與桌面應用相容

        在應用啟動時呼叫此方法，確保後端版本符合最低要求。
        如果後端版本過舊，應用應顯示警告或拒絕啟動。

        Returns:
            VersionCheckResult: 包含相容性檢查結果
        """
        try:
            # 呼叫後端健康檢查端點取得版本
            response = httpx.get(
                f"{self.base_url}/health",
                timeout=5.0  # 版本檢查使用較短的超時
            )

            if response.status_code != 200:
                return VersionCheckResult(
                    compatible=False,
                    backend_reachable=True,
                    error_message=f"後端回應異常: HTTP {response.status_code}"
                )

            data = response.json()
            backend_version = data.get("version", "0.0.0")

            # 比較版本
            backend_ver = _parse_version(backend_version)
            min_ver = _parse_version(MIN_BACKEND_VERSION)

            if backend_ver < min_ver:
                logger.warning(
                    f"後端版本過舊: {backend_version} < {MIN_BACKEND_VERSION}"
                )
                return VersionCheckResult(
                    compatible=False,
                    backend_version=backend_version,
                    backend_reachable=True,
                    error_message=f"後端版本 {backend_version} 低於最低要求 {MIN_BACKEND_VERSION}"
                )

            logger.info(f"後端版本檢查通過: {backend_version}")
            return VersionCheckResult(
                compatible=True,
                backend_version=backend_version,
                backend_reachable=True
            )

        except httpx.ConnectError:
            logger.warning(f"無法連接後端: {self.base_url}")
            return VersionCheckResult(
                compatible=False,
                backend_reachable=False,
                error_message=f"無法連接後端服務: {self.base_url}"
            )
        except httpx.TimeoutException:
            logger.warning(f"連接後端超時: {self.base_url}")
            return VersionCheckResult(
                compatible=False,
                backend_reachable=False,
                error_message="連接後端服務超時"
            )
        except Exception as e:
            logger.error(f"版本檢查失敗: {e}")
            return VersionCheckResult(
                compatible=False,
                backend_reachable=False,
                error_message=f"版本檢查時發生錯誤: {str(e)}"
            )


# 單例模式
_backend_client: Optional[BackendApiClient] = None


def get_backend_client(base_url: Optional[str] = None) -> BackendApiClient:
    """取得後端 API 客戶端（單例）"""
    global _backend_client
    if _backend_client is None:
        _backend_client = BackendApiClient(base_url)
    return _backend_client
