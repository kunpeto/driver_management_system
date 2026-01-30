"""
本機連線狀態監控服務
對應 tasks.md T074: 實作本機連線狀態監控

功能：
- 定期檢查雲端 API 連線狀態
- 定期檢查 Google API 連線狀態
- 提供狀態變更回調機制

Gemini Review Fix: 支援環境變數配置
"""

import asyncio
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Callable, List
import httpx


class ConnectionState(Enum):
    """連線狀態"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CHECKING = "checking"
    UNKNOWN = "unknown"


@dataclass
class ServiceStatus:
    """服務狀態"""
    name: str
    state: ConnectionState
    message: Optional[str] = None
    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None


@dataclass
class SystemStatus:
    """系統整體狀態"""
    cloud_api: ServiceStatus
    google_api: ServiceStatus
    local_api: ServiceStatus
    overall_healthy: bool


class ConnectionMonitor:
    """
    連線狀態監控服務

    定期檢查各項服務的連線狀態，並在狀態變更時通知回調函數。
    """

    # 預設配置（Gemini Review Fix: 從環境變數讀取）
    DEFAULT_CLOUD_API_URL = os.environ.get(
        "CLOUD_API_URL",
        "https://driver-management-api.onrender.com"
    )
    DEFAULT_LOCAL_API_URL = os.environ.get(
        "LOCAL_API_URL",
        f"http://{os.environ.get('LOCAL_API_HOST', '127.0.0.1')}:{os.environ.get('LOCAL_API_PORT', '8001')}"
    )
    DEFAULT_CHECK_INTERVAL = int(os.environ.get("CONNECTION_CHECK_INTERVAL", "30"))  # 秒

    def __init__(
        self,
        cloud_api_url: Optional[str] = None,
        local_api_url: Optional[str] = None,
        check_interval: int = DEFAULT_CHECK_INTERVAL
    ):
        """
        初始化連線監控器

        Args:
            cloud_api_url: 雲端 API 位址
            local_api_url: 本機 API 位址
            check_interval: 檢查間隔（秒）
        """
        self.cloud_api_url = cloud_api_url or self.DEFAULT_CLOUD_API_URL
        self.local_api_url = local_api_url or self.DEFAULT_LOCAL_API_URL
        self.check_interval = check_interval

        # 狀態
        self._cloud_status = ServiceStatus(
            name="雲端 API",
            state=ConnectionState.UNKNOWN
        )
        self._google_status = ServiceStatus(
            name="Google API",
            state=ConnectionState.UNKNOWN
        )
        self._local_status = ServiceStatus(
            name="本機 API",
            state=ConnectionState.UNKNOWN
        )

        # 回調函數
        self._status_callbacks: List[Callable[[SystemStatus], None]] = []

        # 監控執行緒
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

    @property
    def is_running(self) -> bool:
        """監控是否正在執行"""
        return self._running

    @property
    def current_status(self) -> SystemStatus:
        """取得當前系統狀態"""
        overall = (
            self._cloud_status.state == ConnectionState.CONNECTED and
            self._local_status.state == ConnectionState.CONNECTED
        )

        return SystemStatus(
            cloud_api=self._cloud_status,
            google_api=self._google_status,
            local_api=self._local_status,
            overall_healthy=overall
        )

    def add_status_callback(self, callback: Callable[[SystemStatus], None]):
        """
        新增狀態變更回調函數

        Args:
            callback: 回調函數，接收 SystemStatus 參數
        """
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: Callable[[SystemStatus], None]):
        """移除狀態變更回調函數"""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def _notify_callbacks(self):
        """通知所有回調函數"""
        status = self.current_status
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                print(f"[ERROR] 回調函數執行失敗: {e}")

    async def _check_cloud_api(self) -> ServiceStatus:
        """檢查雲端 API 連線"""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.cloud_api_url}/health")

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return ServiceStatus(
                    name="雲端 API",
                    state=ConnectionState.CONNECTED,
                    message="連線正常",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                return ServiceStatus(
                    name="雲端 API",
                    state=ConnectionState.ERROR,
                    message=f"HTTP {response.status_code}",
                    last_check=datetime.now()
                )

        except httpx.ConnectError:
            return ServiceStatus(
                name="雲端 API",
                state=ConnectionState.DISCONNECTED,
                message="無法連線到伺服器",
                last_check=datetime.now()
            )
        except httpx.TimeoutException:
            return ServiceStatus(
                name="雲端 API",
                state=ConnectionState.ERROR,
                message="連線逾時",
                last_check=datetime.now()
            )
        except Exception as e:
            return ServiceStatus(
                name="雲端 API",
                state=ConnectionState.ERROR,
                message=str(e),
                last_check=datetime.now()
            )

    async def _check_google_api(self, access_token: Optional[str] = None) -> ServiceStatus:
        """
        檢查 Google API 連線

        透過雲端 API 的狀態端點檢查 Google API 狀態。
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = {}
                if access_token:
                    headers["Authorization"] = f"Bearer {access_token}"

                # 透過雲端 API 檢查 Google 狀態
                # 注意：需要登入才能存取，這裡先檢查基本的健康狀態
                response = await client.get(
                    f"{self.cloud_api_url}/api/status/health"
                )

            if response.status_code == 200:
                data = response.json()
                return ServiceStatus(
                    name="Google API",
                    state=ConnectionState.CONNECTED if data.get("status") == "healthy" else ConnectionState.ERROR,
                    message=data.get("message", "狀態已取得"),
                    last_check=datetime.now()
                )
            else:
                return ServiceStatus(
                    name="Google API",
                    state=ConnectionState.UNKNOWN,
                    message="需要登入才能檢查 Google API 狀態",
                    last_check=datetime.now()
                )

        except Exception as e:
            return ServiceStatus(
                name="Google API",
                state=ConnectionState.ERROR,
                message=str(e),
                last_check=datetime.now()
            )

    async def _check_local_api(self) -> ServiceStatus:
        """檢查本機 API 連線"""
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.local_api_url}/health")

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return ServiceStatus(
                    name="本機 API",
                    state=ConnectionState.CONNECTED,
                    message="連線正常",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                return ServiceStatus(
                    name="本機 API",
                    state=ConnectionState.ERROR,
                    message=f"HTTP {response.status_code}",
                    last_check=datetime.now()
                )

        except httpx.ConnectError:
            return ServiceStatus(
                name="本機 API",
                state=ConnectionState.DISCONNECTED,
                message="本機 API 未啟動",
                last_check=datetime.now()
            )
        except Exception as e:
            return ServiceStatus(
                name="本機 API",
                state=ConnectionState.ERROR,
                message=str(e),
                last_check=datetime.now()
            )

    async def check_all(self) -> SystemStatus:
        """
        檢查所有服務狀態

        Returns:
            SystemStatus: 系統整體狀態
        """
        # 並行檢查所有服務
        cloud_task = self._check_cloud_api()
        google_task = self._check_google_api()
        local_task = self._check_local_api()

        self._cloud_status, self._google_status, self._local_status = await asyncio.gather(
            cloud_task, google_task, local_task
        )

        return self.current_status

    def check_all_sync(self) -> SystemStatus:
        """同步版本的檢查所有服務"""
        return asyncio.run(self.check_all())

    def _monitor_loop(self):
        """監控迴圈"""
        while not self._stop_event.is_set():
            try:
                # 檢查狀態
                old_status = self.current_status

                asyncio.run(self.check_all())

                new_status = self.current_status

                # 檢查狀態是否變更
                if (old_status.cloud_api.state != new_status.cloud_api.state or
                    old_status.google_api.state != new_status.google_api.state or
                    old_status.local_api.state != new_status.local_api.state):
                    self._notify_callbacks()

            except Exception as e:
                print(f"[ERROR] 連線監控發生錯誤: {e}")

            # 等待下次檢查
            self._stop_event.wait(self.check_interval)

    def start(self):
        """啟動監控"""
        if self._running:
            print("[*] 連線監控已在執行中")
            return

        self._stop_event.clear()
        self._running = True

        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ConnectionMonitor"
        )
        self._monitor_thread.start()

        print("[OK] 連線監控已啟動")

    def stop(self):
        """停止監控"""
        if not self._running:
            return

        self._stop_event.set()
        self._running = False

        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None

        print("[OK] 連線監控已停止")


# 單例實例
_monitor_instance: Optional[ConnectionMonitor] = None


def get_connection_monitor() -> ConnectionMonitor:
    """取得連線監控器實例（單例）"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ConnectionMonitor()
    return _monitor_instance
