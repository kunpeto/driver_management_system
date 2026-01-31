"""
條碼生成 API
對應 tasks.md T095: 實作條碼生成 API

功能：
- POST /api/barcode/generate: 生成條碼圖片（返回 Base64）
- GET /api/barcode/formats: 取得支援的條碼格式列表
"""

import base64
import io
import logging
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/barcode", tags=["Barcode Generator"])


# ============================================================
# Enums & Constants
# ============================================================

class BarcodeFormat(str, Enum):
    """支援的條碼格式"""
    CODE128 = "code128"
    CODE39 = "code39"
    EAN13 = "ean13"
    EAN8 = "ean8"
    UPCA = "upca"
    ISBN13 = "isbn13"
    ISBN10 = "isbn10"
    ISSN = "issn"
    PZN = "pzn"


class ImageFormat(str, Enum):
    """輸出圖片格式"""
    PNG = "png"
    SVG = "svg"


# ============================================================
# Pydantic Models
# ============================================================

class BarcodeGenerateRequest(BaseModel):
    """條碼生成請求"""
    data: str = Field(..., min_length=1, max_length=100, description="條碼內容")
    format: BarcodeFormat = Field(default=BarcodeFormat.CODE128, description="條碼格式")
    image_format: ImageFormat = Field(default=ImageFormat.PNG, description="圖片格式")
    width: Optional[int] = Field(default=None, ge=50, le=1000, description="圖片寬度（像素）")
    height: Optional[int] = Field(default=100, ge=20, le=500, description="條碼高度（像素）")
    include_text: bool = Field(default=True, description="是否包含文字")
    font_size: int = Field(default=10, ge=6, le=24, description="文字字體大小")
    quiet_zone: int = Field(default=6, ge=0, le=20, description="靜區大小（毫米）")


class BarcodeGenerateResponse(BaseModel):
    """條碼生成回應"""
    success: bool
    data: str  # 原始條碼內容
    format: str  # 條碼格式
    image_format: str  # 圖片格式
    base64_image: Optional[str] = None  # Base64 編碼的圖片
    data_uri: Optional[str] = None  # Data URI（可直接用於 img src）
    error_message: Optional[str] = None


class BarcodeFormatInfo(BaseModel):
    """條碼格式資訊"""
    format: str
    name: str
    description: str
    data_pattern: str
    example: str


# ============================================================
# API Endpoints
# ============================================================

@router.post("/generate", response_model=BarcodeGenerateResponse)
async def generate_barcode(request: BarcodeGenerateRequest):
    """
    生成條碼圖片

    支援多種條碼格式，返回 Base64 編碼的圖片。
    """
    try:
        import barcode
        from barcode.writer import ImageWriter, SVGWriter

        # 取得條碼類別
        barcode_class = barcode.get_barcode_class(request.format.value)

        # 準備 writer
        if request.image_format == ImageFormat.SVG:
            writer = SVGWriter()
            mime_type = "image/svg+xml"
        else:
            writer = ImageWriter()
            mime_type = "image/png"

        # 設定 writer 選項
        writer_options = {
            'module_height': request.height / 10 if request.height else 10,
            'quiet_zone': request.quiet_zone,
            'font_size': request.font_size,
            'text_distance': 5,
            'write_text': request.include_text,
        }

        if request.width:
            # 計算 module_width（每個條的寬度）
            # 這是近似計算，實際寬度可能略有不同
            writer_options['module_width'] = request.width / 100

        # 建立條碼
        bc = barcode_class(request.data, writer=writer)

        # 生成圖片到記憶體
        buffer = io.BytesIO()
        bc.write(buffer, options=writer_options)
        buffer.seek(0)

        # 轉換為 Base64
        image_bytes = buffer.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # 建立 Data URI
        data_uri = f"data:{mime_type};base64,{base64_image}"

        logger.info(f"已生成條碼: {request.format.value} - {request.data}")

        return BarcodeGenerateResponse(
            success=True,
            data=request.data,
            format=request.format.value,
            image_format=request.image_format.value,
            base64_image=base64_image,
            data_uri=data_uri
        )

    except Exception as e:
        logger.error(f"條碼生成失敗: {e}")
        return BarcodeGenerateResponse(
            success=False,
            data=request.data,
            format=request.format.value,
            image_format=request.image_format.value,
            error_message=str(e)
        )


@router.get("/formats", response_model=list[BarcodeFormatInfo])
async def get_supported_formats():
    """
    取得支援的條碼格式列表
    """
    formats = [
        BarcodeFormatInfo(
            format="code128",
            name="Code 128",
            description="高密度條碼，支援全 ASCII 字元",
            data_pattern="任意 ASCII 字元",
            example="TH-12345"
        ),
        BarcodeFormatInfo(
            format="code39",
            name="Code 39",
            description="常用於工業和軍事應用",
            data_pattern="A-Z, 0-9, 空格, -.$/+%",
            example="ABC-123"
        ),
        BarcodeFormatInfo(
            format="ean13",
            name="EAN-13",
            description="歐洲商品條碼，用於零售商品",
            data_pattern="12 位數字（第 13 位為檢查碼）",
            example="590123412345"
        ),
        BarcodeFormatInfo(
            format="ean8",
            name="EAN-8",
            description="EAN-13 的縮短版本",
            data_pattern="7 位數字（第 8 位為檢查碼）",
            example="9638507"
        ),
        BarcodeFormatInfo(
            format="upca",
            name="UPC-A",
            description="美國通用商品條碼",
            data_pattern="11 位數字（第 12 位為檢查碼）",
            example="12345678901"
        ),
        BarcodeFormatInfo(
            format="isbn13",
            name="ISBN-13",
            description="國際標準書號（13位）",
            data_pattern="ISBN 格式，如 978-x-xxx-xxxxx-x",
            example="978-3-16-148410-0"
        ),
        BarcodeFormatInfo(
            format="isbn10",
            name="ISBN-10",
            description="國際標準書號（10位，舊版）",
            data_pattern="ISBN 格式，如 x-xxx-xxxxx-x",
            example="3-16-148410-X"
        ),
        BarcodeFormatInfo(
            format="issn",
            name="ISSN",
            description="國際標準期刊號",
            data_pattern="8 位數字",
            example="12345679"
        ),
        BarcodeFormatInfo(
            format="pzn",
            name="PZN",
            description="德國藥品識別碼",
            data_pattern="7 位數字",
            example="1234567"
        ),
    ]

    return formats


@router.post("/validate")
async def validate_barcode_data(
    data: str,
    format: BarcodeFormat = BarcodeFormat.CODE128
):
    """
    驗證條碼資料是否有效
    """
    try:
        import barcode

        barcode_class = barcode.get_barcode_class(format.value)

        # 嘗試建立條碼（不寫入檔案）
        bc = barcode_class(data)

        return {
            "valid": True,
            "data": data,
            "format": format.value,
            "message": "資料格式正確"
        }

    except Exception as e:
        return {
            "valid": False,
            "data": data,
            "format": format.value,
            "message": str(e)
        }


@router.post("/generate-department-barcode")
async def generate_department_barcode(
    department: str = "淡海",
    identifier: str = "12345",
    format: BarcodeFormat = BarcodeFormat.CODE128,
    image_format: ImageFormat = ImageFormat.PNG
):
    """
    生成部門條碼

    自動根據部門生成帶有前綴的條碼（TH/AK）
    """
    # 部門前綴映射
    prefix_map = {
        "淡海": "TH",
        "安坑": "AK",
    }

    prefix = prefix_map.get(department)
    if not prefix:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的部門: {department}，僅支援 淡海 或 安坑"
        )

    # 組合條碼資料
    barcode_data = f"{prefix}-{identifier}"

    # 呼叫通用生成函式
    request = BarcodeGenerateRequest(
        data=barcode_data,
        format=format,
        image_format=image_format,
        include_text=True
    )

    return await generate_barcode(request)
