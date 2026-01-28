"""
系統托盤程式
對應 tasks.md T033: 建立系統托盤程式

功能：
- 系統托盤圖示
- 啟動/停止 API 服務
- 狀態顯示
"""

import subprocess
import sys
import os
import threading
import time
from typing import Optional

# 嘗試匯入 pystray（可能未安裝）
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("[WARNING] pystray 或 PIL 未安裝，托盤功能不可用")
    print("請執行: pip install pystray pillow")


class DriverManagementTray:
    """
    司機員管理系統托盤應用程式

    提供系統托盤圖示，讓使用者可以：
    - 啟動/停止本機 API
    - 查看 API 狀態
    - 快速存取功能
    """

    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.icon: Optional['Icon'] = None
        self.api_running = False
        self._status_check_thread: Optional[threading.Thread] = None
        self._stop_status_check = threading.Event()

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

            # 啟動 uvicorn
            self.api_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m", "uvicorn",
                    "src.main:app",
                    "--host", "127.0.0.1",
                    "--port", "8001"
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
                print("[OK] API 服務已啟動 (http://127.0.0.1:8001)")
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
        self.stop_api()

        if self.icon:
            self.icon.stop()

    def get_status_text(self) -> str:
        """取得狀態文字"""
        if self.api_running:
            return "API 狀態: 運行中"
        else:
            return "API 狀態: 已停止"

    def run(self):
        """執行托盤應用程式"""
        if not PYSTRAY_AVAILABLE:
            print("[ERROR] pystray 未安裝，無法啟動托盤應用")
            print("請執行: pip install pystray pillow")
            return

        # 建立選單
        menu = Menu(
            MenuItem("司機員管理系統", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("啟動 API", self.start_api),
            MenuItem("停止 API", self.stop_api),
            MenuItem("重啟 API", self.restart_api),
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

        # 執行托盤應用
        self.icon.run()


def main():
    """主程式入口"""
    app = DriverManagementTray()
    app.run()


if __name__ == "__main__":
    main()
