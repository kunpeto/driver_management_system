"""
日誌配置
對應 tasks.md T025: 建立日誌配置

使用 loguru 進行結構化日誌記錄。
不記錄敏感資訊（密碼、Token 等）。
"""

import sys
from typing import Any

from loguru import logger

from src.config.settings import get_settings


# 敏感欄位名稱（這些欄位的值會被遮蔽）
SENSITIVE_FIELDS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "private_key",
    "encryption_key",
    "authorization",
}


def _mask_sensitive_data(data: Any, depth: int = 0) -> Any:
    """
    遮蔽敏感資料

    Args:
        data: 要處理的資料
        depth: 遞迴深度（防止無限遞迴）

    Returns:
        處理後的資料，敏感欄位被替換為 "***"
    """
    if depth > 10:
        return data

    if isinstance(data, dict):
        return {
            k: "***" if k.lower() in SENSITIVE_FIELDS else _mask_sensitive_data(v, depth + 1)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [_mask_sensitive_data(item, depth + 1) for item in data]
    elif isinstance(data, str):
        # 檢查是否看起來像 JWT Token
        if data.startswith("eyJ") and data.count(".") == 2:
            return "***JWT_TOKEN***"
        return data
    else:
        return data


def setup_logger():
    """
    設定日誌配置

    根據環境變數設定日誌等級和格式。
    """
    settings = get_settings()

    # 移除預設的 handler
    logger.remove()

    # 日誌格式
    if settings.is_production:
        # 生產環境：JSON 格式，方便日誌分析工具解析
        log_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        log_level = "INFO"
    else:
        # 開發環境：彩色格式，方便閱讀
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        log_level = "DEBUG"

    # 添加 stdout handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=not settings.is_production,
        backtrace=not settings.is_production,
        diagnose=not settings.is_production,
    )

    # 生產環境：添加檔案 handler
    if settings.is_production:
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="INFO",
            rotation="00:00",  # 每天輪換
            retention="30 days",  # 保留 30 天
            compression="gz",  # 壓縮舊檔案
        )

        # 錯誤日誌單獨記錄
        logger.add(
            "logs/error_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="ERROR",
            rotation="00:00",
            retention="90 days",
            compression="gz",
        )

    logger.info(f"日誌系統初始化完成，等級: {log_level}")


def log_request(method: str, path: str, status_code: int, duration_ms: float, **extra):
    """
    記錄 HTTP 請求

    Args:
        method: HTTP 方法
        path: 請求路徑
        status_code: 回應狀態碼
        duration_ms: 處理時間（毫秒）
        **extra: 額外資訊
    """
    # 遮蔽敏感資料
    safe_extra = _mask_sensitive_data(extra)

    if status_code >= 500:
        logger.error(
            f"HTTP {method} {path} -> {status_code} ({duration_ms:.2f}ms)",
            **safe_extra
        )
    elif status_code >= 400:
        logger.warning(
            f"HTTP {method} {path} -> {status_code} ({duration_ms:.2f}ms)",
            **safe_extra
        )
    else:
        logger.info(
            f"HTTP {method} {path} -> {status_code} ({duration_ms:.2f}ms)",
            **safe_extra
        )


def log_db_query(query: str, duration_ms: float, **extra):
    """
    記錄資料庫查詢

    Args:
        query: SQL 查詢（會被截斷）
        duration_ms: 執行時間（毫秒）
        **extra: 額外資訊
    """
    # 截斷過長的查詢
    truncated_query = query[:200] + "..." if len(query) > 200 else query

    if duration_ms > 1000:  # 超過 1 秒的慢查詢
        logger.warning(f"慢查詢 ({duration_ms:.2f}ms): {truncated_query}", **extra)
    else:
        logger.debug(f"DB ({duration_ms:.2f}ms): {truncated_query}", **extra)


def log_auth_event(event: str, user_id: int = None, username: str = None, **extra):
    """
    記錄認證事件

    Args:
        event: 事件類型（login, logout, token_refresh, login_failed）
        user_id: 使用者 ID
        username: 使用者名稱
        **extra: 額外資訊
    """
    safe_extra = _mask_sensitive_data(extra)

    if event == "login_failed":
        logger.warning(f"AUTH {event}: user={username}", **safe_extra)
    else:
        logger.info(f"AUTH {event}: user_id={user_id}, user={username}", **safe_extra)


def log_security_event(event: str, severity: str = "info", **extra):
    """
    記錄安全事件

    Args:
        event: 事件描述
        severity: 嚴重程度（info, warning, error, critical）
        **extra: 額外資訊
    """
    safe_extra = _mask_sensitive_data(extra)

    if severity == "critical":
        logger.critical(f"SECURITY: {event}", **safe_extra)
    elif severity == "error":
        logger.error(f"SECURITY: {event}", **safe_extra)
    elif severity == "warning":
        logger.warning(f"SECURITY: {event}", **safe_extra)
    else:
        logger.info(f"SECURITY: {event}", **safe_extra)


# 匯出 logger 實例
__all__ = [
    "logger",
    "setup_logger",
    "log_request",
    "log_db_query",
    "log_auth_event",
    "log_security_event",
]
