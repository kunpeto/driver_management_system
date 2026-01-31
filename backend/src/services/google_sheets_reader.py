"""
Google Sheets 讀取服務
對應 tasks.md T080: 實作 Google Sheets 讀取服務

功能：
- 使用服務帳戶憑證連接 Google Sheets
- 讀取指定試算表的資料
- 支援讀取特定分頁
- 唯讀權限操作
"""

import base64
import json
import socket
from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2

from src.config.settings import get_settings
from src.utils.logger import logger


# API 設定
API_TIMEOUT_SECONDS = 30
API_NUM_RETRIES = 2

# Google Sheets 權限範圍
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


@dataclass
class SheetInfo:
    """試算表分頁資訊"""
    sheet_id: int
    title: str
    row_count: int
    column_count: int


@dataclass
class SpreadsheetInfo:
    """試算表資訊"""
    spreadsheet_id: str
    title: str
    sheets: List[SheetInfo] = field(default_factory=list)


@dataclass
class ReadResult:
    """讀取結果"""
    success: bool
    data: List[List[Any]] = field(default_factory=list)
    error: Optional[str] = None
    row_count: int = 0
    column_count: int = 0


class GoogleSheetsReader:
    """
    Google Sheets 讀取服務

    使用服務帳戶憑證讀取 Google Sheets 資料。
    僅使用唯讀權限，確保資料安全。
    """

    def __init__(self):
        self._settings = get_settings()
        # Gemini Review Fix: 使用 Dict 確保 Python 3.8 相容性
        self._credentials_cache: Dict[str, service_account.Credentials] = {}

    def _decode_credentials(self, base64_json: str) -> dict:
        """
        解碼 Base64 編碼的憑證 JSON

        Args:
            base64_json: Base64 編碼的 Service Account JSON

        Returns:
            dict: 解碼後的憑證字典

        Raises:
            ValueError: 解碼失敗
        """
        try:
            decoded_bytes = base64.b64decode(base64_json)
            decoded_str = decoded_bytes.decode("utf-8")
            return json.loads(decoded_str)
        except Exception as e:
            raise ValueError(f"憑證解碼失敗: {str(e)}")

    def _get_credentials(self, base64_json: str) -> service_account.Credentials:
        """
        取得 Google 憑證物件

        Args:
            base64_json: Base64 編碼的 Service Account JSON

        Returns:
            service_account.Credentials: 憑證物件
        """
        # 使用憑證快取避免重複解碼
        cache_key = hash(base64_json)
        if cache_key in self._credentials_cache:
            return self._credentials_cache[cache_key]

        credentials_dict = self._decode_credentials(base64_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )

        self._credentials_cache[cache_key] = credentials
        return credentials

    def _build_service(self, credentials: service_account.Credentials) -> Any:
        """
        建立 Sheets API 服務

        Gemini Review Fix: 加入返回類型 hint

        Args:
            credentials: Google 憑證

        Returns:
            Any: Google Sheets API 服務物件（Resource 類型無公開定義）
        """
        http = httplib2.Http(timeout=API_TIMEOUT_SECONDS)
        return build("sheets", "v4", credentials=credentials, http=http)

    def get_spreadsheet_info(
        self,
        base64_json: str,
        spreadsheet_id: str
    ) -> SpreadsheetInfo:
        """
        取得試算表資訊

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            spreadsheet_id: 試算表 ID

        Returns:
            SpreadsheetInfo: 試算表資訊

        Raises:
            ValueError: 讀取失敗
        """
        try:
            credentials = self._get_credentials(base64_json)
            service = self._build_service(credentials)

            spreadsheet = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields="properties.title,sheets.properties"
            ).execute(num_retries=API_NUM_RETRIES)

            sheets = []
            for sheet in spreadsheet.get("sheets", []):
                props = sheet["properties"]
                sheets.append(SheetInfo(
                    sheet_id=props["sheetId"],
                    title=props["title"],
                    row_count=props.get("gridProperties", {}).get("rowCount", 0),
                    column_count=props.get("gridProperties", {}).get("columnCount", 0)
                ))

            return SpreadsheetInfo(
                spreadsheet_id=spreadsheet_id,
                title=spreadsheet["properties"]["title"],
                sheets=sheets
            )

        except HttpError as e:
            status = e.resp.status
            if status == 403:
                raise ValueError("權限不足：請確認憑證有存取此試算表的權限")
            elif status == 404:
                raise ValueError("試算表不存在或 ID 錯誤")
            else:
                raise ValueError(f"API 錯誤 ({status}): {str(e)}")
        except socket.timeout:
            raise ValueError(f"連線逾時（超過 {API_TIMEOUT_SECONDS} 秒）")
        except Exception as e:
            raise ValueError(f"讀取失敗: {str(e)}")

    def read_sheet(
        self,
        base64_json: str,
        spreadsheet_id: str,
        sheet_name: Optional[str] = None,
        range_notation: Optional[str] = None
    ) -> ReadResult:
        """
        讀取試算表資料

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            spreadsheet_id: 試算表 ID
            sheet_name: 分頁名稱（可選，預設讀取第一個分頁）
            range_notation: 範圍標記（如 A1:Z100，可選）

        Returns:
            ReadResult: 讀取結果
        """
        try:
            credentials = self._get_credentials(base64_json)
            service = self._build_service(credentials)

            # 建立範圍字串
            if sheet_name and range_notation:
                range_str = f"'{sheet_name}'!{range_notation}"
            elif sheet_name:
                range_str = f"'{sheet_name}'"
            elif range_notation:
                range_str = range_notation
            else:
                range_str = None

            # 讀取資料
            request = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_str if range_str else "A:ZZ"
            )
            response = request.execute(num_retries=API_NUM_RETRIES)

            values = response.get("values", [])

            logger.info(
                "Google Sheets 讀取成功",
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                row_count=len(values)
            )

            return ReadResult(
                success=True,
                data=values,
                row_count=len(values),
                column_count=max(len(row) for row in values) if values else 0
            )

        except HttpError as e:
            status = e.resp.status
            if status == 403:
                error_msg = "權限不足：請確認憑證有存取此試算表的權限"
            elif status == 404:
                error_msg = "試算表或分頁不存在"
            else:
                error_msg = f"API 錯誤 ({status}): {str(e)}"

            logger.error(
                "Google Sheets 讀取失敗",
                spreadsheet_id=spreadsheet_id,
                error=error_msg
            )
            return ReadResult(success=False, error=error_msg)

        except socket.timeout:
            error_msg = f"連線逾時（超過 {API_TIMEOUT_SECONDS} 秒）"
            logger.error("Google Sheets 連線逾時", spreadsheet_id=spreadsheet_id)
            return ReadResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"讀取失敗: {str(e)}"
            logger.error(
                "Google Sheets 讀取例外",
                spreadsheet_id=spreadsheet_id,
                error=str(e)
            )
            return ReadResult(success=False, error=error_msg)

    def read_multiple_sheets(
        self,
        base64_json: str,
        spreadsheet_id: str,
        sheet_names: List[str]
    ) -> Dict[str, ReadResult]:
        """
        批次讀取多個分頁

        Args:
            base64_json: Base64 編碼的 Service Account JSON
            spreadsheet_id: 試算表 ID
            sheet_names: 分頁名稱列表

        Returns:
            dict: 分頁名稱 -> 讀取結果
        """
        results = {}
        for sheet_name in sheet_names:
            results[sheet_name] = self.read_sheet(
                base64_json=base64_json,
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name
            )
        return results

    def read_schedule_sheet(
        self,
        department: str,
        year: int,
        month: int
    ) -> ReadResult:
        """
        讀取指定部門的班表分頁

        Args:
            department: 部門（'淡海' 或 '安坑'）
            year: 年份
            month: 月份

        Returns:
            ReadResult: 讀取結果
        """
        # 取得部門憑證與試算表 ID
        if department == "淡海":
            base64_json = self._settings.tanhae_google_service_account_json
            spreadsheet_id = self._settings.tanhae_google_sheets_id_schedule
        else:
            base64_json = self._settings.anping_google_service_account_json
            spreadsheet_id = self._settings.anping_google_sheets_id_schedule

        if not base64_json:
            return ReadResult(
                success=False,
                error=f"{department} 部門的 Service Account 憑證未設定"
            )

        if not spreadsheet_id:
            return ReadResult(
                success=False,
                error=f"{department} 部門的班表試算表 ID 未設定"
            )

        # 班表分頁名稱格式：YYYY-MM 或 YYYYMM
        # 嘗試多種可能的分頁名稱格式
        possible_sheet_names = [
            f"{year}-{month:02d}",
            f"{year}{month:02d}",
            f"{year}年{month}月",
            f"{month}月",
        ]

        # 先取得試算表資訊，確認分頁名稱
        try:
            spreadsheet_info = self.get_spreadsheet_info(base64_json, spreadsheet_id)
            available_sheets = [s.title for s in spreadsheet_info.sheets]

            logger.debug(
                "班表試算表分頁列表",
                department=department,
                sheets=available_sheets
            )

            # 找到匹配的分頁
            sheet_name = None
            for name in possible_sheet_names:
                if name in available_sheets:
                    sheet_name = name
                    break

            if not sheet_name:
                return ReadResult(
                    success=False,
                    error=f"找不到 {year} 年 {month} 月的班表分頁。可用分頁：{', '.join(available_sheets)}"
                )

            logger.info(
                "讀取班表分頁",
                department=department,
                year=year,
                month=month,
                sheet_name=sheet_name
            )

            return self.read_sheet(
                base64_json=base64_json,
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name
            )

        except ValueError as e:
            return ReadResult(success=False, error=str(e))


# 單例實例
_reader_instance: Optional[GoogleSheetsReader] = None


def get_google_sheets_reader() -> GoogleSheetsReader:
    """取得 Google Sheets 讀取器實例（單例）"""
    global _reader_instance
    if _reader_instance is None:
        _reader_instance = GoogleSheetsReader()
    return _reader_instance
