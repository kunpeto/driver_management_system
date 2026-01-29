"""
PDF 條碼識別服務
對應 tasks.md T090: 實作 PDF 條碼識別服務

功能：
- 從 PDF 頁面中識別條碼
- 支援 Code128、Code39、QR Code 等格式
- 返回條碼內容與頁面位置

依賴：
- PyPDF2: PDF 讀取
- pdf2image: PDF 轉圖片
- pyzbar: 條碼識別
- Pillow: 圖片處理
"""

import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class BarcodeResult:
    """條碼識別結果"""
    page_number: int      # 頁碼（從 1 開始）
    barcode_type: str     # 條碼類型（CODE128, CODE39, QRCODE 等）
    barcode_data: str     # 條碼內容
    confidence: float     # 信心度（0-1）
    position: Optional[tuple] = None  # 條碼在頁面中的位置 (x, y, width, height)


class BarcodeReader:
    """PDF 條碼識別器"""

    # 支援的條碼類型
    SUPPORTED_TYPES = [
        'CODE128',
        'CODE39',
        'EAN13',
        'EAN8',
        'UPCA',
        'UPCE',
        'QRCODE',
        'PDF417',
        'DATAMATRIX',
    ]

    def __init__(self, dpi: int = 200):
        """
        初始化條碼識別器

        Args:
            dpi: PDF 轉圖片的解析度（預設 200 DPI，越高越清晰但越慢）
        """
        self.dpi = dpi
        self._check_dependencies()

    def _check_dependencies(self):
        """檢查必要依賴"""
        try:
            import pyzbar.pyzbar
            import pdf2image
        except ImportError as e:
            logger.error(f"缺少必要依賴: {e}")
            raise ImportError(
                "請安裝必要套件: pip install pyzbar pdf2image PyPDF2 Pillow\n"
                "Windows 用戶還需要安裝 poppler 並加入 PATH"
            )

    def read_from_pdf(
        self,
        pdf_path: str | Path,
        pages: Optional[list[int]] = None
    ) -> list[BarcodeResult]:
        """
        從 PDF 檔案中識別條碼

        Args:
            pdf_path: PDF 檔案路徑
            pages: 要處理的頁碼列表（從 1 開始），None 表示處理所有頁面

        Returns:
            BarcodeResult 列表
        """
        from pdf2image import convert_from_path
        from pyzbar import pyzbar

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 檔案不存在: {pdf_path}")

        results = []

        try:
            # 將 PDF 轉換為圖片
            logger.info(f"正在處理 PDF: {pdf_path}")

            # 如果指定頁碼，只處理指定頁面
            if pages:
                images = convert_from_path(
                    pdf_path,
                    dpi=self.dpi,
                    first_page=min(pages),
                    last_page=max(pages)
                )
                page_numbers = pages
            else:
                images = convert_from_path(pdf_path, dpi=self.dpi)
                page_numbers = list(range(1, len(images) + 1))

            # 逐頁識別條碼
            for idx, (image, page_num) in enumerate(zip(images, page_numbers)):
                logger.debug(f"處理第 {page_num} 頁...")

                # 轉為灰階提高識別率
                gray_image = image.convert('L')

                # 識別條碼
                barcodes = pyzbar.decode(gray_image)

                for barcode in barcodes:
                    barcode_type = barcode.type
                    barcode_data = barcode.data.decode('utf-8', errors='replace')

                    # 取得位置
                    rect = barcode.rect
                    position = (rect.left, rect.top, rect.width, rect.height)

                    result = BarcodeResult(
                        page_number=page_num,
                        barcode_type=barcode_type,
                        barcode_data=barcode_data,
                        confidence=1.0,  # pyzbar 沒有信心度，成功識別即為 1.0
                        position=position
                    )
                    results.append(result)
                    logger.info(f"第 {page_num} 頁發現條碼: {barcode_type} - {barcode_data}")

        except Exception as e:
            logger.error(f"PDF 條碼識別失敗: {e}")
            raise

        logger.info(f"共識別到 {len(results)} 個條碼")
        return results

    def read_from_image(self, image_path: str | Path) -> list[BarcodeResult]:
        """
        從圖片檔案中識別條碼

        Args:
            image_path: 圖片檔案路徑

        Returns:
            BarcodeResult 列表
        """
        from pyzbar import pyzbar

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"圖片檔案不存在: {image_path}")

        results = []

        try:
            image = Image.open(image_path)
            gray_image = image.convert('L')

            barcodes = pyzbar.decode(gray_image)

            for barcode in barcodes:
                barcode_type = barcode.type
                barcode_data = barcode.data.decode('utf-8', errors='replace')

                rect = barcode.rect
                position = (rect.left, rect.top, rect.width, rect.height)

                result = BarcodeResult(
                    page_number=1,
                    barcode_type=barcode_type,
                    barcode_data=barcode_data,
                    confidence=1.0,
                    position=position
                )
                results.append(result)

        except Exception as e:
            logger.error(f"圖片條碼識別失敗: {e}")
            raise

        return results

    def read_from_bytes(self, pdf_bytes: bytes) -> list[BarcodeResult]:
        """
        從 PDF bytes 中識別條碼

        Args:
            pdf_bytes: PDF 檔案的 bytes 資料

        Returns:
            BarcodeResult 列表
        """
        from pdf2image import convert_from_bytes
        from pyzbar import pyzbar

        results = []

        try:
            images = convert_from_bytes(pdf_bytes, dpi=self.dpi)

            for page_num, image in enumerate(images, start=1):
                gray_image = image.convert('L')
                barcodes = pyzbar.decode(gray_image)

                for barcode in barcodes:
                    barcode_type = barcode.type
                    barcode_data = barcode.data.decode('utf-8', errors='replace')

                    rect = barcode.rect
                    position = (rect.left, rect.top, rect.width, rect.height)

                    result = BarcodeResult(
                        page_number=page_num,
                        barcode_type=barcode_type,
                        barcode_data=barcode_data,
                        confidence=1.0,
                        position=position
                    )
                    results.append(result)

        except Exception as e:
            logger.error(f"PDF bytes 條碼識別失敗: {e}")
            raise

        return results


# 單例模式
_barcode_reader: Optional[BarcodeReader] = None


def get_barcode_reader(dpi: int = 200) -> BarcodeReader:
    """取得條碼識別器實例（單例）"""
    global _barcode_reader
    if _barcode_reader is None:
        _barcode_reader = BarcodeReader(dpi=dpi)
    return _barcode_reader


# 便利函式
def read_barcodes_from_pdf(
    pdf_path: str | Path,
    pages: Optional[list[int]] = None
) -> list[BarcodeResult]:
    """從 PDF 檔案識別條碼的便利函式"""
    reader = get_barcode_reader()
    return reader.read_from_pdf(pdf_path, pages)
