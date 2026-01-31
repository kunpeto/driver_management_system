"""
系統托盤程式
對應 tasks.md T033: 建立系統托盤程式
對應 tasks.md T075: 更新系統托盤程式（狀態列圖示、連線狀態顯示）

功能：
- 系統托盤圖示
- 啟動/停止 API 服務
- 狀態顯示
- 連線狀態監控與顯示（T075）
"""

import subprocess
import sys
import os
import threading
import time
from typing import Optional

# Gemini Review Fix: 從環境變數讀取 API Port
LOCAL_API_HOST = os.environ.get("LOCAL_API_HOST", "127.0.0.1")
LOCAL_API_PORT = os.environ.get("LOCAL_API_PORT", "8001")

# 嘗試匯入 pystray（可能未安裝）
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("[WARNING] pystray 或 PIL 未安裝，托盤功能不可用")
    print("請執行: pip install pystray pillow")

# 匯入連線監控器
try:
    from src.services.connection_monitor import (
        ConnectionMonitor,
        ConnectionState,
        SystemStatus,
        get_connection_monitor
    )
    CONNECTION_MONITOR_AVAILABLE = True
except ImportError:
    CONNECTION_MONITOR_AVAILABLE = False
    print("[WARNING] 連線監控模組未找到")


class DriverManagementTray:
    """
    司機員管理系統托盤應用程式

    提供系統托盤圖示，讓使用者可以：
    - 啟動/停止本機 API
    - 查看 API 狀態
    - 快速存取功能
    - 檢視連線狀態（T075）
    """

    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.icon: Optional['Icon'] = None
        self.api_running = False
        self._status_check_thread: Optional[threading.Thread] = None
        self._stop_status_check = threading.Event()

        # 連線監控（T075）
        self._connection_monitor: Optional['ConnectionMonitor'] = None
        self._cloud_connected = False
        self._google_connected = False

    def create_icon_image(self, color: str = "green") -> 'Image':
        """
        建立托盤圖示

        Args:
            color: 圖示顏色（green=運行中, red=已停止, yellow=啟動中）

        Returns:
            PIL Image 物件
        """
        # 建立 64x64 圖示
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 顏色對應
        colors = {
            "green": "#4CAF50",
            "red": "#F44336",
            "yellow": "#FFC107"
        }
        fill_color = colors.get(color, colors["green"])

        # 繪製圓形
        margin = 4
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=fill_color,
            outline="#333333",
            width=2
        )

        # 繪製「D」字母
        try:
            from PIL import ImageFont
            # 嘗試使用系統字型
            font = ImageFont.truetype("arial.ttf", 32)
        except (IOError, OSError):
            font = ImageFont.load_default()

        text = "D"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - 4  # 微調垂直位置
        draw.text((x, y), text, fill="white", font=font)

        return image

    def start_api(self, icon=None, item=None):
        """啟動 FastAPI 服務"""
        if self.api_process is not None:
            print("[*] API 已在運行中")
            return

        print("[*] 啟動 API 服務...")

        # 更新圖示為黃色（啟動中）
        if self.icon:
            self.icon.icon = self.create_icon_image("yellow")

        try:
            # 取得腳本所在目錄
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Windows 特殊處理：隱藏 CMD 視窗
            startupinfo = None
            creationflags = 0
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW

            # 啟動 uvicorn（Gemini Review Fix: 使用環境變數配置）
            self.api_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m", "uvicorn",
                    "src.main:app",
                    "--host", LOCAL_API_HOST,
                    "--port", LOCAL_API_PORT
                ],
                cwd=os.path.dirname(script_dir),  # desktop_app 目錄
                startupinfo=startupinfo,
                creationflags=creationflags,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 等待啟動
            time.sleep(2)

            if self.api_process.poll() is None:
                self.api_running = True
                print(f"[OK] API 服務已啟動 (http://{LOCAL_API_HOST}:{LOCAL_API_PORT})")
                if self.icon:
                    self.icon.icon = self.create_icon_image("green")
            else:
                print("[ERROR] API 服務啟動失敗")
                if self.icon:
                    self.icon.icon = self.create_icon_image("red")
                self.api_process = None

        except Exception as e:
            print(f"[ERROR] 啟動 API 失敗: {e}")
            if self.icon:
                self.icon.icon = self.create_icon_image("red")
            self.api_process = None

    def stop_api(self, icon=None, item=None):
        """停止 FastAPI 服務"""
        if self.api_process is None:
            print("[*] API 未在運行")
            return

        print("[*] 停止 API 服務...")

        try:
            self.api_process.terminate()
            self.api_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.api_process.kill()

        self.api_process = None
        self.api_running = False
        print("[OK] API 服務已停止")

        if self.icon:
            self.icon.icon = self.create_icon_image("red")

    def restart_api(self, icon=None, item=None):
        """重啟 FastAPI 服務"""
        self.stop_api()
        time.sleep(1)
        self.start_api()

    def open_docs(self, icon=None, item=None):
        """開啟 API 文件"""
        import webbrowser
        webbrowser.open("http://127.0.0.1:8001/docs")

    def open_health(self, icon=None, item=None):
        """開啟健康檢查頁面"""
        import webbrowser
        webbrowser.open("http://127.0.0.1:8001/health")

    def quit_app(self, icon=None, item=None):
        """結束程式"""
        print("[*] 結束程式...")
        self._stop_status_check.set()
        self.stop_connection_monitor()  # T075: 停止連線監控
        self.stop_api()

        if self.icon:
            self.icon.stop()

    def get_status_text(self) -> str:
        """取得狀態文字"""
        if self.api_running:
            return "API 狀態: 運行中"
        else:
            return "API 狀態: 已停止"

    def get_connection_status_text(self) -> str:
        """取得連線狀態文字（T075）"""
        cloud = "正常" if self._cloud_connected else "離線"
        google = "正常" if self._google_connected else "未知"
        return f"雲端: {cloud} | Google: {google}"

    def _on_connection_status_change(self, status: 'SystemStatus'):
        """連線狀態變更回調（T075）"""
        self._cloud_connected = status.cloud_api.state == ConnectionState.CONNECTED
        self._google_connected = status.google_api.state == ConnectionState.CONNECTED

        # 更新托盤圖示
        if self.icon:
            if not self._cloud_connected:
                # 雲端離線時使用黃色警示
                self.icon.icon = self.create_icon_image("yellow")
            elif self.api_running:
                self.icon.icon = self.create_icon_image("green")
            else:
                self.icon.icon = self.create_icon_image("red")

        print(f"[*] 連線狀態更新 - {self.get_connection_status_text()}")

    def start_connection_monitor(self):
        """啟動連線監控（T075）"""
        if not CONNECTION_MONITOR_AVAILABLE:
            print("[*] 連線監控模組不可用")
            return

        self._connection_monitor = get_connection_monitor()
        self._connection_monitor.add_status_callback(self._on_connection_status_change)
        self._connection_monitor.start()
        print("[OK] 連線監控已啟動")

    def stop_connection_monitor(self):
        """停止連線監控（T075）"""
        if self._connection_monitor:
            self._connection_monitor.stop()
            self._connection_monitor = None

    def check_connection_now(self, icon=None, item=None):
        """立即檢查連線狀態（T075）"""
        if not CONNECTION_MONITOR_AVAILABLE:
            print("[*] 連線監控模組不可用")
            return

        print("[*] 正在檢查連線狀態...")
        monitor = get_connection_monitor()
        status = monitor.check_all_sync()

        self._cloud_connected = status.cloud_api.state == ConnectionState.CONNECTED
        self._google_connected = status.google_api.state == ConnectionState.CONNECTED

        # 顯示詳細狀態
        print(f"    雲端 API: {status.cloud_api.state.value} - {status.cloud_api.message}")
        print(f"    Google API: {status.google_api.state.value} - {status.google_api.message}")
        print(f"    本機 API: {status.local_api.state.value} - {status.local_api.message}")
        print(f"[OK] 連線檢查完成")

    def run(self):
        """執行托盤應用程式"""
        if not PYSTRAY_AVAILABLE:
            print("[ERROR] pystray 未安裝，無法啟動托盤應用")
            print("請執行: pip install pystray pillow")
            return

        # 建立選單（T075: 新增連線狀態相關選項）
        menu = Menu(
            MenuItem("司機員管理系統", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("啟動 API", self.start_api),
            MenuItem("停止 API", self.stop_api),
            MenuItem("重啟 API", self.restart_api),
            Menu.SEPARATOR,
            MenuItem("檢查連線狀態", self.check_connection_now),
            Menu.SEPARATOR,
            MenuItem("開啟 API 文件", self.open_docs),
            MenuItem("健康檢查", self.open_health),
            Menu.SEPARATOR,
            MenuItem("結束", self.quit_app)
        )

        # 建立托盤圖示
        self.icon = Icon(
            name="DriverManagementAPI",
            icon=self.create_icon_image("red"),
            title="司機員管理系統 API",
            menu=menu
        )

        print("[*] 托盤應用程式已啟動")
        print("[*] 右鍵點擊托盤圖示可開啟選單")

        # 自動啟動 API
        threading.Thread(target=self.start_api, daemon=True).start()

        # 啟動連線監控（T075）
        threading.Thread(target=self.start_connection_monitor, daemon=True).start()

        # 執行托盤應用
        self.icon.run()


def main():
    """主程式入口"""
    app = DriverManagementTray()
    app.run()


if __name__ == "__main__":
    main()
