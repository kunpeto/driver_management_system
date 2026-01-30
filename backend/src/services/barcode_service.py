"""
BarcodeService 條碼生成服務
對應 tasks.md T146: 實作條碼生成服務
對應 spec.md: User Story 8 - 條碼生成（後端實作）

使用 python-barcode + Pillow 生成 Code128 條碼圖片。
完全雲端化，無需本機 API。
"""

import io
from typing import Optional

from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image

from src.utils.barcode_encoder import BarcodeEncoder


class BarcodeServiceError(Exception):
    """條碼服務錯誤"""
    pass


class BarcodeService:
    """
    條碼生成服務

    使用 python-barcode + Pillow 生成 Code128 條碼圖片。
    """

    # 預設條碼設定
    DEFAULT_WIDTH = 0.4  # 條碼模組寬度（mm）
    DEFAULT_HEIGHT = 15.0  # 條碼高度（mm）
    DEFAULT_FONT_SIZE = 10  # 字體大小
    DEFAULT_TEXT_DISTANCE = 5.0  # 文字與條碼距離（mm）

    def __init__(self):
        """初始化服務"""
        pass

    def generate(
        self,
        barcode_data: str,
        width: Optional[float] = None,
        height: Optional[float] = None,
        include_text: bool = True
    ) -> bytes:
        """
        生成條碼圖片

        Args:
            barcode_data: 條碼資料字串
            width: 條碼模組寬度（mm）
            height: 條碼高度（mm）
            include_text: 是否包含文字

        Returns:
            PNG 圖片的 bytes

        Raises:
            BarcodeServiceError: 生成失敗
        """
        try:
            # 設定 ImageWriter 選項
            writer_options = {
                "module_width": width or self.DEFAULT_WIDTH,
                "module_height": height or self.DEFAULT_HEIGHT,
                "font_size": self.DEFAULT_FONT_SIZE if include_text else 0,
                "text_distance": self.DEFAULT_TEXT_DISTANCE if include_text else 0,
                "quiet_zone": 6.5,  # 靜區寬度
                "write_text": include_text,
            }

            # 建立 Code128 條碼
            barcode = Code128(barcode_data, writer=ImageWriter())

            # 生成到記憶體
            buffer = io.BytesIO()
            barcode.write(buffer, options=writer_options)
            buffer.seek(0)

            return buffer.getvalue()

        except Exception as e:
            raise BarcodeServiceError(f"條碼生成失敗: {e}") from e

    def generate_for_profile(
        self,
        profile_id: int,
        profile_type: str,
        version: int = 1,
        assessment_type: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        為履歷生成條碼

        使用 BarcodeEncoder 編碼履歷資訊，然後生成條碼圖片。

        Args:
            profile_id: 履歷 ID
            profile_type: 履歷類型
            version: 版本號
            assessment_type: 考核類型（加分/扣分）
            **kwargs: 傳遞給 generate 的其他參數

        Returns:
            PNG 圖片的 bytes
        """
        # 使用 BarcodeEncoder 生成編碼
        barcode_data = BarcodeEncoder.encode(
            profile_id=profile_id,
            profile_type=profile_type,
            version=version,
            assessment_type=assessment_type
        )

        return self.generate(barcode_data, **kwargs)

    def generate_image(
        self,
        barcode_data: str,
        width: Optional[float] = None,
        height: Optional[float] = None,
        include_text: bool = True
    ) -> Image.Image:
        """
        生成條碼 PIL Image 物件

        Args:
            barcode_data: 條碼資料字串
            width: 條碼模組寬度（mm）
            height: 條碼高度（mm）
            include_text: 是否包含文字

        Returns:
            PIL Image 物件
        """
        png_bytes = self.generate(
            barcode_data=barcode_data,
            width=width,
            height=height,
            include_text=include_text
        )

        return Image.open(io.BytesIO(png_bytes))

    def generate_base64(
        self,
        barcode_data: str,
        **kwargs
    ) -> str:
        """
        生成 Base64 編碼的條碼圖片

        Args:
            barcode_data: 條碼資料字串
            **kwargs: 傳遞給 generate 的其他參數

        Returns:
            Base64 編碼字串（不含 data URI 前綴）
        """
        import base64

        png_bytes = self.generate(barcode_data, **kwargs)
        return base64.b64encode(png_bytes).decode("utf-8")

    def generate_data_uri(
        self,
        barcode_data: str,
        **kwargs
    ) -> str:
        """
        生成 Data URI 格式的條碼圖片

        Args:
            barcode_data: 條碼資料字串
            **kwargs: 傳遞給 generate 的其他參數

        Returns:
            Data URI 字串（可直接用於 HTML img src）
        """
        base64_str = self.generate_base64(barcode_data, **kwargs)
        return f"data:image/png;base64,{base64_str}"


# 便捷函數
def generate_barcode(barcode_data: str, **kwargs) -> bytes:
    """
    生成條碼的便捷函數

    Args:
        barcode_data: 條碼資料字串
        **kwargs: 傳遞給 BarcodeService.generate 的其他參數

    Returns:
        PNG 圖片的 bytes
    """
    service = BarcodeService()
    return service.generate(barcode_data, **kwargs)


def generate_profile_barcode(
    profile_id: int,
    profile_type: str,
    version: int = 1,
    assessment_type: Optional[str] = None,
    **kwargs
) -> bytes:
    """
    為履歷生成條碼的便捷函數

    Args:
        profile_id: 履歷 ID
        profile_type: 履歷類型
        version: 版本號
        assessment_type: 考核類型
        **kwargs: 傳遞給 BarcodeService.generate 的其他參數

    Returns:
        PNG 圖片的 bytes
    """
    service = BarcodeService()
    return service.generate_for_profile(
        profile_id=profile_id,
        profile_type=profile_type,
        version=version,
        assessment_type=assessment_type,
        **kwargs
    )
