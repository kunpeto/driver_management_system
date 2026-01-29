"""
PDF 切分服務
對應 tasks.md T091: 實作 PDF 切分服務

功能：
- 依條碼切分多頁 PDF
- 支援依頁碼範圍切分
- 保留 PDF 元數據

依賴：
- PyPDF2: PDF 操作
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader, PdfWriter

from .barcode_reader import BarcodeResult, get_barcode_reader

logger = logging.getLogger(__name__)


@dataclass
class SplitResult:
    """切分結果"""
    output_path: Path         # 輸出檔案路徑
    start_page: int           # 起始頁碼（從 1 開始）
    end_page: int             # 結束頁碼
    page_count: int           # 頁數
    barcode_data: Optional[str] = None  # 關聯的條碼內容
    department: Optional[str] = None    # 判斷出的部門


class PdfSplitter:
    """PDF 切分器"""

    def __init__(self, output_dir: Optional[str | Path] = None):
        """
        初始化 PDF 切分器

        Args:
            output_dir: 預設輸出目錄，None 則使用原檔案所在目錄
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir and not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)

    def split_by_pages(
        self,
        pdf_path: str | Path,
        page_ranges: list[tuple[int, int]],
        output_names: Optional[list[str]] = None
    ) -> list[SplitResult]:
        """
        依頁碼範圍切分 PDF

        Args:
            pdf_path: 原始 PDF 路徑
            page_ranges: 頁碼範圍列表，如 [(1, 3), (4, 6)] 表示 1-3 頁和 4-6 頁
            output_names: 輸出檔案名稱列表（不含副檔名），None 則自動命名

        Returns:
            SplitResult 列表
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 檔案不存在: {pdf_path}")

        output_dir = self.output_dir or pdf_path.parent
        results = []

        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)

        logger.info(f"開始切分 PDF: {pdf_path} (共 {total_pages} 頁)")

        for idx, (start, end) in enumerate(page_ranges):
            # 驗證頁碼範圍
            if start < 1 or end > total_pages or start > end:
                logger.warning(f"無效的頁碼範圍: {start}-{end}，跳過")
                continue

            # 決定輸出檔名
            if output_names and idx < len(output_names):
                output_name = output_names[idx]
            else:
                output_name = f"{pdf_path.stem}_p{start}-{end}"

            output_path = output_dir / f"{output_name}.pdf"

            # 建立新 PDF
            writer = PdfWriter()
            for page_num in range(start - 1, end):  # PyPDF2 使用 0-based 索引
                writer.add_page(reader.pages[page_num])

            # 寫入檔案
            with open(output_path, 'wb') as f:
                writer.write(f)

            result = SplitResult(
                output_path=output_path,
                start_page=start,
                end_page=end,
                page_count=end - start + 1
            )
            results.append(result)
            logger.info(f"已建立: {output_path} (第 {start}-{end} 頁)")

        return results

    def split_by_barcodes(
        self,
        pdf_path: str | Path,
        barcodes: Optional[list[BarcodeResult]] = None
    ) -> list[SplitResult]:
        """
        依條碼切分 PDF

        每個條碼開始一個新的區段，直到下一個條碼或檔案結束。

        Args:
            pdf_path: 原始 PDF 路徑
            barcodes: 條碼識別結果，None 則自動識別

        Returns:
            SplitResult 列表
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 檔案不存在: {pdf_path}")

        # 自動識別條碼
        if barcodes is None:
            reader = get_barcode_reader()
            barcodes = reader.read_from_pdf(pdf_path)

        if not barcodes:
            logger.warning(f"PDF 中未發現條碼: {pdf_path}")
            return []

        # 按頁碼排序條碼
        sorted_barcodes = sorted(barcodes, key=lambda x: x.page_number)

        # 取得 PDF 總頁數
        pdf_reader = PdfReader(str(pdf_path))
        total_pages = len(pdf_reader.pages)

        # 計算切分範圍
        page_ranges = []
        barcode_mapping = []  # 記錄每個範圍對應的條碼

        for i, barcode in enumerate(sorted_barcodes):
            start_page = barcode.page_number

            # 結束頁碼是下一個條碼的前一頁，或 PDF 結尾
            if i + 1 < len(sorted_barcodes):
                end_page = sorted_barcodes[i + 1].page_number - 1
            else:
                end_page = total_pages

            # 確保範圍有效
            if start_page <= end_page:
                page_ranges.append((start_page, end_page))
                barcode_mapping.append(barcode)

        output_dir = self.output_dir or pdf_path.parent

        # 執行切分
        results = []
        for (start, end), barcode in zip(page_ranges, barcode_mapping):
            # 使用條碼內容作為檔名（清理非法字元）
            safe_name = self._sanitize_filename(barcode.barcode_data)
            output_name = f"{safe_name}_p{start}-{end}"
            output_path = output_dir / f"{output_name}.pdf"

            # 建立新 PDF
            writer = PdfWriter()
            for page_num in range(start - 1, end):
                writer.add_page(pdf_reader.pages[page_num])

            with open(output_path, 'wb') as f:
                writer.write(f)

            result = SplitResult(
                output_path=output_path,
                start_page=start,
                end_page=end,
                page_count=end - start + 1,
                barcode_data=barcode.barcode_data
            )
            results.append(result)
            logger.info(f"已建立: {output_path} (條碼: {barcode.barcode_data})")

        return results

    def split_single_pages(
        self,
        pdf_path: str | Path
    ) -> list[SplitResult]:
        """
        將 PDF 切分為單頁檔案

        Args:
            pdf_path: 原始 PDF 路徑

        Returns:
            SplitResult 列表
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 檔案不存在: {pdf_path}")

        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)

        page_ranges = [(i, i) for i in range(1, total_pages + 1)]
        output_names = [f"{pdf_path.stem}_page{i:03d}" for i in range(1, total_pages + 1)]

        return self.split_by_pages(pdf_path, page_ranges, output_names)

    def extract_pages(
        self,
        pdf_path: str | Path,
        pages: list[int],
        output_path: Optional[str | Path] = None
    ) -> Path:
        """
        提取指定頁面到新 PDF

        Args:
            pdf_path: 原始 PDF 路徑
            pages: 要提取的頁碼列表
            output_path: 輸出路徑，None 則自動命名

        Returns:
            輸出檔案路徑
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 檔案不存在: {pdf_path}")

        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)

        # 驗證頁碼
        valid_pages = [p for p in pages if 1 <= p <= total_pages]
        if not valid_pages:
            raise ValueError("沒有有效的頁碼")

        # 決定輸出路徑
        if output_path is None:
            output_dir = self.output_dir or pdf_path.parent
            pages_str = "_".join(str(p) for p in valid_pages[:5])
            if len(valid_pages) > 5:
                pages_str += "_etc"
            output_path = output_dir / f"{pdf_path.stem}_extracted_{pages_str}.pdf"
        else:
            output_path = Path(output_path)

        # 提取頁面
        writer = PdfWriter()
        for page_num in valid_pages:
            writer.add_page(reader.pages[page_num - 1])

        with open(output_path, 'wb') as f:
            writer.write(f)

        logger.info(f"已提取 {len(valid_pages)} 頁到: {output_path}")
        return output_path

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """清理檔名中的非法字元"""
        # Windows 非法字元
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            name = name.replace(char, '_')

        # 移除控制字元
        name = ''.join(c for c in name if ord(c) >= 32)

        # 限制長度
        if len(name) > 100:
            name = name[:100]

        return name or "unnamed"


# 單例模式
_pdf_splitter: Optional[PdfSplitter] = None


def get_pdf_splitter(output_dir: Optional[str | Path] = None) -> PdfSplitter:
    """取得 PDF 切分器實例"""
    global _pdf_splitter
    if _pdf_splitter is None or output_dir:
        _pdf_splitter = PdfSplitter(output_dir=output_dir)
    return _pdf_splitter


# 便利函式
def split_pdf_by_barcodes(pdf_path: str | Path) -> list[SplitResult]:
    """依條碼切分 PDF 的便利函式"""
    splitter = get_pdf_splitter()
    return splitter.split_by_barcodes(pdf_path)
