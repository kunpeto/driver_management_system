"""
pytest 配置文件（Desktop App）
對應 Gemini Code Review 修復: 補充 Desktop API 測試

提供測試所需的 fixtures 和配置。
"""

import os
import sys
import pytest
from pathlib import Path

# 確保 src 目錄在 Python 路徑中
desktop_app_root = Path(__file__).parent.parent
sys.path.insert(0, str(desktop_app_root / "src"))


@pytest.fixture
def sample_pdf_bytes():
    """提供測試用的 PDF bytes（最小化 PDF）"""
    # 最小化的 PDF 內容（1 頁空白）
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
411
%%EOF
"""
    return pdf_content


@pytest.fixture
def mock_barcode_result():
    """提供測試用的條碼識別結果"""
    from dataclasses import dataclass

    @dataclass
    class MockBarcodeResult:
        page_number: int
        barcode_type: str
        barcode_data: str
        confidence: float
        position: tuple = (0, 0, 100, 100)

    return MockBarcodeResult(
        page_number=1,
        barcode_type="CODE128",
        barcode_data="TH-12345",
        confidence=1.0
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """提供臨時輸出目錄"""
    output_dir = tmp_path / "pdf_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir
