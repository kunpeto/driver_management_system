"""
條碼生成 API 單元測試
對應 Gemini Code Review 修復: 補充 Desktop API 測試

測試項目：
- POST /api/barcode/generate: 生成條碼圖片
- GET /api/barcode/formats: 取得支援的條碼格式
- POST /api/barcode/generate-department-barcode: 快速生成部門條碼
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import base64


@pytest.fixture
def app():
    """建立測試用的 FastAPI app"""
    from fastapi import FastAPI
    from desktop_app.src.api.barcode_generator import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """建立測試用的 TestClient"""
    return TestClient(app)


class TestBarcodeGenerate:
    """測試條碼生成端點"""

    def test_generate_barcode_success(self, client):
        """測試成功生成條碼"""
        response = client.post(
            "/api/barcode/generate",
            json={
                "data": "TEST-12345",
                "barcode_type": "code128",
                "width": 300,
                "height": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "image_base64" in data
        assert data["barcode_type"] == "code128"
        assert data["data"] == "TEST-12345"

        # 驗證 base64 格式
        try:
            base64.b64decode(data["image_base64"])
        except Exception:
            pytest.fail("Invalid base64 image data")

    def test_generate_barcode_invalid_type(self, client):
        """測試使用無效的條碼類型"""
        response = client.post(
            "/api/barcode/generate",
            json={
                "data": "TEST-12345",
                "barcode_type": "invalid_type",
                "width": 300,
                "height": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error_message" in data

    def test_generate_barcode_missing_data(self, client):
        """測試缺少必要參數"""
        response = client.post(
            "/api/barcode/generate",
            json={
                "barcode_type": "code128",
                "width": 300,
                "height": 100
            }
        )

        assert response.status_code == 422  # Validation error

    def test_generate_barcode_default_size(self, client):
        """測試使用預設尺寸"""
        response = client.post(
            "/api/barcode/generate",
            json={
                "data": "TEST-12345",
                "barcode_type": "code128"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["width"] == 400  # 預設寬度
        assert data["height"] == 150  # 預設高度

    def test_generate_qr_code(self, client):
        """測試生成 QR Code"""
        response = client.post(
            "/api/barcode/generate",
            json={
                "data": "https://example.com",
                "barcode_type": "qr",
                "width": 200,
                "height": 200
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["barcode_type"] == "qr"


class TestBarcodeFormats:
    """測試取得支援的條碼格式"""

    def test_get_formats(self, client):
        """測試取得條碼格式列表"""
        response = client.get("/api/barcode/formats")

        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert isinstance(data["formats"], list)
        assert len(data["formats"]) > 0

        # 驗證必要的格式
        format_codes = [f["code"] for f in data["formats"]]
        assert "code128" in format_codes
        assert "code39" in format_codes
        assert "qr" in format_codes


class TestDepartmentBarcodeGenerate:
    """測試快速生成部門條碼"""

    def test_generate_department_barcode_tanhai(self, client):
        """測試生成淡海部門條碼"""
        response = client.post(
            "/api/barcode/generate-department-barcode",
            json={
                "department": "淡海",
                "identifier": "12345"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == "TH-12345"
        assert data["department"] == "淡海"
        assert "image_base64" in data

    def test_generate_department_barcode_ankeng(self, client):
        """測試生成安坑部門條碼"""
        response = client.post(
            "/api/barcode/generate-department-barcode",
            json={
                "department": "安坑",
                "identifier": "67890"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == "AK-67890"
        assert data["department"] == "安坑"

    def test_generate_department_barcode_invalid_department(self, client):
        """測試使用無效部門"""
        response = client.post(
            "/api/barcode/generate-department-barcode",
            json={
                "department": "無效部門",
                "identifier": "12345"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "無效的部門" in data["error_message"]

    def test_generate_department_barcode_custom_format(self, client):
        """測試使用自訂條碼格式"""
        response = client.post(
            "/api/barcode/generate-department-barcode",
            json={
                "department": "淡海",
                "identifier": "12345",
                "barcode_type": "code39",
                "width": 500,
                "height": 200
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["barcode_type"] == "code39"
        assert data["width"] == 500
        assert data["height"] == 200


class TestBarcodeValidation:
    """測試條碼資料驗證"""

    def test_generate_barcode_with_special_chars(self, client):
        """測試包含特殊字元的條碼資料"""
        response = client.post(
            "/api/barcode/generate",
            json={
                "data": "TEST-2024/01/29",
                "barcode_type": "code128"
            }
        )

        assert response.status_code == 200
        data = response.json()
        # CODE128 支援大部分 ASCII 字元
        assert data["success"] is True

    def test_generate_barcode_empty_data(self, client):
        """測試空白資料"""
        response = client.post(
            "/api/barcode/generate",
            json={
                "data": "",
                "barcode_type": "code128"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_generate_barcode_with_chinese(self, client):
        """測試包含中文的條碼（QR Code 支援）"""
        response = client.post(
            "/api/barcode/generate",
            json={
                "data": "測試中文",
                "barcode_type": "qr"
            }
        )

        assert response.status_code == 200
        data = response.json()
        # QR Code 支援 Unicode
        assert data["success"] is True
