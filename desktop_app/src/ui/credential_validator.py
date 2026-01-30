"""
憑證驗證介面
對應 tasks.md T076: 實作憑證驗證介面

功能：
- 顯示憑證驗證結果
- 顯示錯誤訊息
- 提供詳細的驗證資訊
"""

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Callable

# 嘗試匯入 tkinter（可能未安裝）
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("[WARNING] tkinter 未安裝，GUI 功能不可用")


@dataclass
class ValidationItem:
    """驗證項目"""
    name: str
    passed: bool
    message: str
    details: Optional[dict] = None


@dataclass
class ValidationReport:
    """驗證報告"""
    department: str
    items: List[ValidationItem]
    overall_passed: bool
    validated_at: datetime


class CredentialValidatorUI:
    """
    憑證驗證介面

    提供圖形化介面讓使用者選擇憑證檔案並驗證。
    """

    def __init__(self, on_validate: Optional[Callable] = None):
        """
        初始化憑證驗證介面

        Args:
            on_validate: 驗證回調函數，接收 (department, base64_json) 參數
        """
        self._on_validate = on_validate
        self._window: Optional['tk.Tk'] = None
        self._result_text: Optional['tk.Text'] = None

    def _create_window(self):
        """建立視窗"""
        if not TKINTER_AVAILABLE:
            print("[ERROR] tkinter 未安裝，無法建立 GUI")
            return None

        self._window = tk.Tk()
        self._window.title("Google 憑證驗證")
        self._window.geometry("600x500")
        self._window.resizable(True, True)

        # 主框架
        main_frame = ttk.Frame(self._window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 標題
        title_label = ttk.Label(
            main_frame,
            text="Google Service Account 憑證驗證",
            font=("Microsoft JhengHei", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 說明
        desc_label = ttk.Label(
            main_frame,
            text="選擇部門和憑證檔案，驗證 Google API 連線是否正常",
            font=("Microsoft JhengHei", 10)
        )
        desc_label.pack(pady=(0, 20))

        # 部門選擇框架
        dept_frame = ttk.LabelFrame(main_frame, text="部門選擇", padding="10")
        dept_frame.pack(fill=tk.X, pady=(0, 10))

        self._department_var = tk.StringVar(value="淡海")

        ttk.Radiobutton(
            dept_frame,
            text="淡海",
            value="淡海",
            variable=self._department_var
        ).pack(side=tk.LEFT, padx=10)

        ttk.Radiobutton(
            dept_frame,
            text="安坑",
            value="安坑",
            variable=self._department_var
        ).pack(side=tk.LEFT, padx=10)

        # 檔案選擇框架
        file_frame = ttk.LabelFrame(main_frame, text="憑證檔案", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self._file_path_var = tk.StringVar()

        file_entry = ttk.Entry(
            file_frame,
            textvariable=self._file_path_var,
            state="readonly",
            width=50
        )
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = ttk.Button(
            file_frame,
            text="瀏覽...",
            command=self._browse_file
        )
        browse_btn.pack(side=tk.RIGHT)

        # 操作按鈕
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        validate_btn = ttk.Button(
            btn_frame,
            text="驗證憑證",
            command=self._validate
        )
        validate_btn.pack(side=tk.LEFT, padx=(0, 10))

        clear_btn = ttk.Button(
            btn_frame,
            text="清除結果",
            command=self._clear_result
        )
        clear_btn.pack(side=tk.LEFT)

        # 結果顯示
        result_frame = ttk.LabelFrame(main_frame, text="驗證結果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # 結果文字區域
        self._result_text = tk.Text(
            result_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            state="disabled"
        )
        self._result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # 捲動軸
        scrollbar = ttk.Scrollbar(
            result_frame,
            orient=tk.VERTICAL,
            command=self._result_text.yview
        )
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self._result_text.config(yscrollcommand=scrollbar.set)

        # 設定文字標籤顏色
        self._result_text.tag_configure("success", foreground="green")
        self._result_text.tag_configure("error", foreground="red")
        self._result_text.tag_configure("info", foreground="blue")
        self._result_text.tag_configure("warning", foreground="orange")

        return self._window

    def _browse_file(self):
        """瀏覽選擇檔案"""
        file_path = filedialog.askopenfilename(
            title="選擇 Service Account JSON 檔案",
            filetypes=[
                ("JSON 檔案", "*.json"),
                ("所有檔案", "*.*")
            ]
        )

        if file_path:
            self._file_path_var.set(file_path)

    def _append_result(self, text: str, tag: Optional[str] = None):
        """新增結果文字"""
        self._result_text.config(state="normal")
        if tag:
            self._result_text.insert(tk.END, text, tag)
        else:
            self._result_text.insert(tk.END, text)
        self._result_text.config(state="disabled")
        self._result_text.see(tk.END)

    def _clear_result(self):
        """清除結果"""
        self._result_text.config(state="normal")
        self._result_text.delete("1.0", tk.END)
        self._result_text.config(state="disabled")

    def _validate(self):
        """執行驗證"""
        file_path = self._file_path_var.get()
        department = self._department_var.get()

        if not file_path:
            messagebox.showwarning("警告", "請先選擇憑證檔案")
            return

        self._clear_result()
        self._append_result(f"=== {department} 憑證驗證 ===\n\n")
        self._append_result(f"檔案: {file_path}\n")
        self._append_result(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            # 讀取檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = f.read()

            # 驗證 JSON 格式
            self._append_result("[1] 驗證 JSON 格式...\n")
            try:
                credentials = json.loads(json_content)
                self._append_result("    ", None)
                self._append_result("✓ JSON 格式正確\n", "success")
            except json.JSONDecodeError as e:
                self._append_result("    ", None)
                self._append_result(f"✗ JSON 格式錯誤: {e}\n", "error")
                return

            # 驗證必要欄位
            self._append_result("\n[2] 驗證必要欄位...\n")
            required_fields = [
                "type", "project_id", "private_key_id", "private_key",
                "client_email", "client_id", "auth_uri", "token_uri"
            ]

            missing = [f for f in required_fields if f not in credentials]
            if missing:
                self._append_result("    ", None)
                self._append_result(f"✗ 缺少必要欄位: {', '.join(missing)}\n", "error")
                return
            else:
                self._append_result("    ", None)
                self._append_result("✓ 所有必要欄位都存在\n", "success")

            # 驗證憑證類型
            self._append_result("\n[3] 驗證憑證類型...\n")
            if credentials.get("type") != "service_account":
                self._append_result("    ", None)
                self._append_result(f"✗ 憑證類型錯誤: {credentials.get('type')}\n", "error")
                return
            else:
                self._append_result("    ", None)
                self._append_result("✓ 憑證類型正確 (service_account)\n", "success")

            # 顯示憑證資訊
            self._append_result("\n[4] 憑證資訊:\n")
            self._append_result(f"    專案 ID: {credentials.get('project_id')}\n", "info")
            self._append_result(f"    服務帳戶: {credentials.get('client_email')}\n", "info")

            # Base64 編碼
            self._append_result("\n[5] 產生 Base64 編碼...\n")
            base64_json = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
            self._append_result("    ", None)
            self._append_result("✓ Base64 編碼完成\n", "success")
            self._append_result(f"    長度: {len(base64_json)} 字元\n", "info")

            # 呼叫驗證回調
            if self._on_validate:
                self._append_result("\n[6] 執行 API 連線測試...\n")
                try:
                    result = self._on_validate(department, base64_json)
                    if result:
                        if result.get("success"):
                            self._append_result("    ", None)
                            self._append_result("✓ API 連線測試成功\n", "success")
                        else:
                            self._append_result("    ", None)
                            self._append_result(f"✗ API 連線測試失敗: {result.get('error')}\n", "error")
                except Exception as e:
                    self._append_result("    ", None)
                    self._append_result(f"✗ API 測試例外: {e}\n", "error")

            self._append_result("\n" + "=" * 40 + "\n")
            self._append_result("驗證完成\n", "success")

        except FileNotFoundError:
            self._append_result("✗ 找不到檔案\n", "error")
        except PermissionError:
            self._append_result("✗ 沒有讀取檔案的權限\n", "error")
        except Exception as e:
            self._append_result(f"✗ 發生錯誤: {e}\n", "error")

    def show_result(self, report: ValidationReport):
        """
        顯示驗證報告

        Args:
            report: 驗證報告
        """
        if not self._result_text:
            return

        self._clear_result()

        self._append_result(f"=== {report.department} 憑證驗證報告 ===\n\n")
        self._append_result(f"驗證時間: {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for i, item in enumerate(report.items, 1):
            status = "✓" if item.passed else "✗"
            tag = "success" if item.passed else "error"

            self._append_result(f"[{i}] {item.name}\n")
            self._append_result(f"    {status} ", None)
            self._append_result(f"{item.message}\n", tag)

            if item.details:
                for key, value in item.details.items():
                    self._append_result(f"    - {key}: {value}\n", "info")
            self._append_result("\n")

        self._append_result("=" * 40 + "\n")
        overall_text = "驗證成功" if report.overall_passed else "驗證失敗"
        overall_tag = "success" if report.overall_passed else "error"
        self._append_result(f"整體結果: {overall_text}\n", overall_tag)

    def run(self):
        """執行 GUI"""
        if not TKINTER_AVAILABLE:
            print("[ERROR] tkinter 未安裝，無法執行 GUI")
            return

        window = self._create_window()
        if window:
            window.mainloop()

    def show(self):
        """顯示視窗（非阻塞）"""
        if not TKINTER_AVAILABLE:
            print("[ERROR] tkinter 未安裝，無法顯示 GUI")
            return

        if not self._window:
            self._create_window()

        if self._window:
            self._window.deiconify()

    def hide(self):
        """隱藏視窗"""
        if self._window:
            self._window.withdraw()

    def close(self):
        """關閉視窗"""
        if self._window:
            self._window.destroy()
            self._window = None


def create_validator_ui(on_validate: Optional[Callable] = None) -> CredentialValidatorUI:
    """建立憑證驗證介面"""
    return CredentialValidatorUI(on_validate)
