"""
連線狀態檢查服務
對應 tasks.md T071: 實作連線狀態檢查服務

功能：
- 檢查 TiDB 資料庫連線
- 檢查 Google Sheets API 連線
- 檢查 Google Drive API 連線
- 提供統一的連線狀態報告

Gemini Review Fix: 使用 ThreadPoolExecutor 並行處理 Google API 檢查
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

from src.config.database import check_database_connection
from src.services.credential_validator import (
    CredentialValidator,
    get_credential_validator,
    ValidationResult,
)
from src.config.settings import get_settings
from src.utils.logger import logger


# 並行執行的最大執行緒數
MAX_WORKERS = 4


ConnectionStatus = Literal["connected", "disconnected", "error", "not_configured"]


@dataclass
class ServiceStatus:
    """單一服務的連線狀態"""
    name: str
    status: ConnectionStatus
    message: Optional[str] = None
    details: Optional[dict] = None
    checked_at: Optional[datetime] = None


@dataclass
class CloudConnectionStatus:
    """雲端服務連線狀態"""
    database: ServiceStatus
    overall_status: ConnectionStatus
    checked_at: datetime


@dataclass
class GoogleConnectionStatus:
    """Google API 連線狀態"""
    danhai_sheets: ServiceStatus
    danhai_drive: ServiceStatus
    ankeng_sheets: ServiceStatus
    ankeng_drive: ServiceStatus
    overall_status: ConnectionStatus
    checked_at: datetime


class ConnectionMonitor:
    """
    連線狀態監控服務

    用於檢查系統各項服務的連線狀態，包括：
    - TiDB 資料庫
    - Google Sheets API（淡海、安坑）
    - Google Drive API（淡海、安坑）
    """

    def __init__(self):
        self._settings = get_settings()
        self._validator: Optional[CredentialValidator] = None

    @property
    def validator(self) -> CredentialValidator:
        """延遲載入憑證驗證器"""
        if self._validator is None:
            self._validator = get_credential_validator()
        return self._validator

    def check_database(self) -> ServiceStatus:
        """
        檢查資料庫連線狀態

        Returns:
            ServiceStatus: 資料庫連線狀態
        """
        try:
            result = check_database_connection()

            if result["status"] == "connected":
                logger.debug(
                    "資料庫連線檢查成功",
                    database=result.get("database"),
                    table_count=result.get("table_count")
                )
                return ServiceStatus(
                    name="TiDB Database",
                    status="connected",
                    message=f"連線正常 (版本: {result.get('version', 'unknown')})",
                    details={
                        "version": result.get("version"),
                        "database": result.get("database"),
                        "table_count": result.get("table_count"),
                    },
                    checked_at=datetime.now()
                )
            else:
                logger.warning(
                    "資料庫連線檢查失敗",
                    error=result.get("error")
                )
                return ServiceStatus(
                    name="TiDB Database",
                    status="error",
                    message=result.get("error", "連線失敗"),
                    checked_at=datetime.now()
                )

        except Exception as e:
            logger.error("資料庫連線檢查例外", error=str(e))
            return ServiceStatus(
                name="TiDB Database",
                status="error",
                message=str(e),
                checked_at=datetime.now()
            )

    def check_cloud_status(self) -> CloudConnectionStatus:
        """
        檢查雲端服務連線狀態

        包括：
        - TiDB 資料庫

        Returns:
            CloudConnectionStatus: 雲端連線狀態
        """
        database_status = self.check_database()

        # 決定整體狀態
        overall = "connected" if database_status.status == "connected" else "error"

        return CloudConnectionStatus(
            database=database_status,
            overall_status=overall,
            checked_at=datetime.now()
        )

    def _check_sheets_status(
        self,
        department: str,
        base64_json: Optional[str],
        spreadsheet_id: Optional[str]
    ) -> ServiceStatus:
        """
        檢查 Google Sheets 連線狀態

        Args:
            department: 部門名稱
            base64_json: Base64 編碼的 Service Account JSON
            spreadsheet_id: Google Sheets ID

        Returns:
            ServiceStatus: Sheets 連線狀態
        """
        service_name = f"{department} Google Sheets"

        # 檢查是否已配置
        if not base64_json:
            return ServiceStatus(
                name=service_name,
                status="not_configured",
                message="Service Account 憑證未設定",
                checked_at=datetime.now()
            )

        if not spreadsheet_id:
            return ServiceStatus(
                name=service_name,
                status="not_configured",
                message="Sheets ID 未設定",
                checked_at=datetime.now()
            )

        # 測試連線
        try:
            result = self.validator.test_sheets_access(base64_json, spreadsheet_id)

            if result.valid:
                return ServiceStatus(
                    name=service_name,
                    status="connected",
                    message=f"連線正常 ({result.details.get('spreadsheet_title', '')})",
                    details=result.details,
                    checked_at=datetime.now()
                )
            else:
                return ServiceStatus(
                    name=service_name,
                    status="error",
                    message=result.error,
                    checked_at=datetime.now()
                )

        except Exception as e:
            logger.error(f"{department} Sheets 連線檢查例外", error=str(e))
            return ServiceStatus(
                name=service_name,
                status="error",
                message=str(e),
                checked_at=datetime.now()
            )

    def _check_drive_status(
        self,
        department: str,
        base64_json: Optional[str],
        folder_id: Optional[str]
    ) -> ServiceStatus:
        """
        檢查 Google Drive 連線狀態

        Args:
            department: 部門名稱
            base64_json: Base64 編碼的 Service Account JSON
            folder_id: Google Drive 資料夾 ID

        Returns:
            ServiceStatus: Drive 連線狀態
        """
        service_name = f"{department} Google Drive"

        # 檢查是否已配置
        if not base64_json:
            return ServiceStatus(
                name=service_name,
                status="not_configured",
                message="Service Account 憑證未設定",
                checked_at=datetime.now()
            )

        if not folder_id:
            return ServiceStatus(
                name=service_name,
                status="not_configured",
                message="Drive 資料夾 ID 未設定",
                checked_at=datetime.now()
            )

        # 測試連線
        try:
            result = self.validator.test_drive_access(base64_json, folder_id)

            if result.valid:
                return ServiceStatus(
                    name=service_name,
                    status="connected",
                    message=f"連線正常 ({result.details.get('folder_name', '')})",
                    details=result.details,
                    checked_at=datetime.now()
                )
            else:
                return ServiceStatus(
                    name=service_name,
                    status="error",
                    message=result.error,
                    checked_at=datetime.now()
                )

        except Exception as e:
            logger.error(f"{department} Drive 連線檢查例外", error=str(e))
            return ServiceStatus(
                name=service_name,
                status="error",
                message=str(e),
                checked_at=datetime.now()
            )

    def check_google_status(self) -> GoogleConnectionStatus:
        """
        檢查 Google API 連線狀態（並行處理）

        包括：
        - 淡海 Google Sheets
        - 淡海 Google Drive
        - 安坑 Google Sheets
        - 安坑 Google Drive

        **Gemini Review Fix**: 使用 ThreadPoolExecutor 並行處理，
        避免依序呼叫導致請求逾時。

        Returns:
            GoogleConnectionStatus: Google API 連線狀態
        """
        # 淡海設定
        danhai_credential = self._settings.tanhae_google_service_account_json
        danhai_sheets_id = self._settings.tanhae_google_sheets_id_schedule
        danhai_drive_id = getattr(self._settings, 'tanhae_google_drive_folder_id', None)

        # 安坑設定
        ankeng_credential = self._settings.anping_google_service_account_json
        ankeng_sheets_id = self._settings.anping_google_sheets_id_schedule
        ankeng_drive_id = getattr(self._settings, 'anping_google_drive_folder_id', None)

        # 使用 ThreadPoolExecutor 並行檢查各項服務
        results = {}

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有檢查任務
            futures = {
                executor.submit(
                    self._check_sheets_status, "淡海", danhai_credential, danhai_sheets_id
                ): "danhai_sheets",
                executor.submit(
                    self._check_drive_status, "淡海", danhai_credential, danhai_drive_id
                ): "danhai_drive",
                executor.submit(
                    self._check_sheets_status, "安坑", ankeng_credential, ankeng_sheets_id
                ): "ankeng_sheets",
                executor.submit(
                    self._check_drive_status, "安坑", ankeng_credential, ankeng_drive_id
                ): "ankeng_drive",
            }

            # 收集結果
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    logger.error(f"並行檢查 {key} 發生例外", error=str(e))
                    results[key] = ServiceStatus(
                        name=key,
                        status="error",
                        message=f"檢查失敗: {str(e)}",
                        checked_at=datetime.now()
                    )

        # 取得結果
        danhai_sheets = results.get("danhai_sheets")
        danhai_drive = results.get("danhai_drive")
        ankeng_sheets = results.get("ankeng_sheets")
        ankeng_drive = results.get("ankeng_drive")

        # 決定整體狀態
        all_statuses = [
            danhai_sheets.status,
            danhai_drive.status,
            ankeng_sheets.status,
            ankeng_drive.status
        ]

        if all(s == "connected" for s in all_statuses):
            overall = "connected"
        elif all(s == "not_configured" for s in all_statuses):
            overall = "not_configured"
        elif any(s == "error" for s in all_statuses):
            overall = "error"
        elif any(s == "connected" for s in all_statuses):
            overall = "connected"  # 部分連線正常
        else:
            overall = "not_configured"

        return GoogleConnectionStatus(
            danhai_sheets=danhai_sheets,
            danhai_drive=danhai_drive,
            ankeng_sheets=ankeng_sheets,
            ankeng_drive=ankeng_drive,
            overall_status=overall,
            checked_at=datetime.now()
        )

    def check_all(self) -> dict:
        """
        檢查所有服務連線狀態

        Returns:
            dict: 包含所有服務狀態的字典
        """
        cloud_status = self.check_cloud_status()
        google_status = self.check_google_status()

        # 決定整體狀態
        if (cloud_status.overall_status == "connected" and
            google_status.overall_status in ("connected", "not_configured")):
            overall = "healthy"
        elif cloud_status.overall_status == "error":
            overall = "unhealthy"
        else:
            overall = "degraded"

        return {
            "overall_status": overall,
            "cloud": {
                "overall_status": cloud_status.overall_status,
                "database": {
                    "status": cloud_status.database.status,
                    "message": cloud_status.database.message,
                    "details": cloud_status.database.details
                }
            },
            "google": {
                "overall_status": google_status.overall_status,
                "danhai_sheets": {
                    "status": google_status.danhai_sheets.status,
                    "message": google_status.danhai_sheets.message
                },
                "danhai_drive": {
                    "status": google_status.danhai_drive.status,
                    "message": google_status.danhai_drive.message
                },
                "ankeng_sheets": {
                    "status": google_status.ankeng_sheets.status,
                    "message": google_status.ankeng_sheets.message
                },
                "ankeng_drive": {
                    "status": google_status.ankeng_drive.status,
                    "message": google_status.ankeng_drive.message
                }
            },
            "checked_at": datetime.now().isoformat()
        }


# 單例實例
_monitor_instance: Optional[ConnectionMonitor] = None


def get_connection_monitor() -> ConnectionMonitor:
    """取得連線監控器實例（單例）"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ConnectionMonitor()
    return _monitor_instance
