"""
桌面應用服務模組

提供 PDF 處理、條碼識別、Google Drive 上傳等服務
"""

from .barcode_reader import (
    BarcodeReader,
    BarcodeResult,
    get_barcode_reader,
    read_barcodes_from_pdf,
)
from .pdf_splitter import (
    PdfSplitter,
    SplitResult,
    get_pdf_splitter,
    split_pdf_by_barcodes,
)
from .department_detector import (
    Department,
    DepartmentDetector,
    DepartmentDetectionResult,
    get_department_detector,
    detect_department,
    is_tanhai,
    is_ankeng,
)
from .google_drive_uploader import (
    GoogleDriveUploader,
    UploadResult,
    create_uploader_with_token,
    create_uploader_from_credential_manager,
)

__all__ = [
    # Barcode Reader
    "BarcodeReader",
    "BarcodeResult",
    "get_barcode_reader",
    "read_barcodes_from_pdf",
    # PDF Splitter
    "PdfSplitter",
    "SplitResult",
    "get_pdf_splitter",
    "split_pdf_by_barcodes",
    # Department Detector
    "Department",
    "DepartmentDetector",
    "DepartmentDetectionResult",
    "get_department_detector",
    "detect_department",
    "is_tanhai",
    "is_ankeng",
    # Google Drive Uploader
    "GoogleDriveUploader",
    "UploadResult",
    "create_uploader_with_token",
    "create_uploader_from_credential_manager",
]
