"""
桌面應用 API 模組

提供 PDF 處理和條碼生成的 API 端點
"""

from .pdf_processor import router as pdf_router
from .barcode_generator import router as barcode_router

__all__ = [
    "pdf_router",
    "barcode_router",
]
