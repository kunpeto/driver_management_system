"""
PDF 處理 API 單元測試
對應 Gemini Code Review 修復: 補充 Desktop API 測試

測試項目：
- POST /api/pdf/scan: 掃描 PDF 條碼
- POST /api/pdf/split: 依條碼切分 PDF
- POST /api/pdf/process: 完整處理（掃描、切分、上傳）
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """建立測試用的 FastAPI app"""
    from fastapi import FastAPI
    from desktop_app.src.api.pdf_processor import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """建立測試用的 TestClient"""
    return TestClient(app)


class TestPdfScan:
    """測試 PDF 掃描端點"""

    def test_scan_pdf_success(self, client, sample_pdf_bytes, mock_barcode_result):
        """測試成功掃描 PDF"""
        with patch('desktop_app.src.services.barcode_reader.get_barcode_reader') as mock_reader:
            # Mock 條碼識別器
            mock_reader_instance = Mock()
            mock_reader_instance.read_from_bytes.return_value = [mock_barcode_result]
            mock_reader.return_value = mock_reader_instance

            with patch('desktop_app.src.services.department_detector.detect_department') as mock_dept:
                # Mock 部門偵測
                mock_dept_result = Mock()
                mock_dept_result.department = Mock()
                mock_dept_result.department.value = "淡海"
                mock_dept.return_value = mock_dept_result

                response = client.post(
                    "/api/pdf/scan",
                    files={"file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["file_name"] == "test.pdf"
                assert data["total_pages"] > 0
                assert len(data["barcodes"]) == 1
                assert data["barcodes"][0]["barcode_data"] == "TH-12345"
                assert data["barcodes"][0]["department"] == "淡海"

    def test_scan_pdf_invalid_file_type(self, client):
        """測試上傳非 PDF 檔案"""
        response = client.post(
            "/api/pdf/scan",
            files={"file": ("test.txt", BytesIO(b"not a pdf"), "text/plain")}
        )

        assert response.status_code == 400
        assert "僅支援 PDF 檔案" in response.json()["detail"]

    def test_scan_pdf_no_barcodes(self, client, sample_pdf_bytes):
        """測試 PDF 中無條碼"""
        with patch('desktop_app.src.services.barcode_reader.get_barcode_reader') as mock_reader:
            mock_reader_instance = Mock()
            mock_reader_instance.read_from_bytes.return_value = []
            mock_reader.return_value = mock_reader_instance

            response = client.post(
                "/api/pdf/scan",
                files={"file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["barcodes"]) == 0


class TestPdfSplit:
    """測試 PDF 切分端點"""

    def test_split_pdf_success(self, client, sample_pdf_bytes, mock_barcode_result, temp_output_dir):
        """測試成功切分 PDF"""
        with patch('desktop_app.src.services.barcode_reader.get_barcode_reader') as mock_reader:
            mock_reader_instance = Mock()
            mock_reader_instance.read_from_bytes.return_value = [mock_barcode_result]
            mock_reader.return_value = mock_reader_instance

            with patch('desktop_app.src.services.pdf_splitter.PdfSplitter') as mock_splitter_class:
                # Mock PDF 切分器
                mock_splitter = Mock()
                mock_split_result = Mock()
                mock_split_result.output_path = Mock()
                mock_split_result.output_path.name = "TH-12345.pdf"
                mock_split_result.start_page = 1
                mock_split_result.end_page = 1
                mock_split_result.page_count = 1
                mock_split_result.barcode_data = "TH-12345"

                mock_splitter.split_by_barcodes.return_value = [mock_split_result]
                mock_splitter_class.return_value = mock_splitter

                with patch('desktop_app.src.services.department_detector.detect_department') as mock_dept:
                    mock_dept_result = Mock()
                    mock_dept_result.department = Mock()
                    mock_dept_result.department.value = "淡海"
                    mock_dept.return_value = mock_dept_result

                    response = client.post(
                        "/api/pdf/split",
                        files={"file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["barcodes_found"] == 1
                    assert data["files_created"] == 1
                    assert len(data["split_files"]) == 1
                    assert data["split_files"][0]["file_name"] == "TH-12345.pdf"

    def test_split_pdf_no_barcodes(self, client, sample_pdf_bytes):
        """測試 PDF 無條碼時無法切分"""
        with patch('desktop_app.src.services.barcode_reader.get_barcode_reader') as mock_reader:
            mock_reader_instance = Mock()
            mock_reader_instance.read_from_bytes.return_value = []
            mock_reader.return_value = mock_reader_instance

            response = client.post(
                "/api/pdf/split",
                files={"file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "未發現條碼" in data["error_message"]


class TestPdfProcess:
    """測試 PDF 完整處理端點"""

    def test_process_pdf_without_upload(self, client, sample_pdf_bytes, mock_barcode_result):
        """測試處理 PDF 但不上傳"""
        with patch('desktop_app.src.services.barcode_reader.get_barcode_reader') as mock_reader:
            mock_reader_instance = Mock()
            mock_reader_instance.read_from_bytes.return_value = [mock_barcode_result]
            mock_reader.return_value = mock_reader_instance

            with patch('desktop_app.src.services.pdf_splitter.PdfSplitter') as mock_splitter_class:
                mock_splitter = Mock()
                mock_split_result = Mock()
                mock_split_result.output_path = Mock()
                mock_split_result.output_path.name = "TH-12345.pdf"
                mock_split_result.start_page = 1
                mock_split_result.end_page = 1
                mock_split_result.page_count = 1
                mock_split_result.barcode_data = "TH-12345"

                mock_splitter.split_by_barcodes.return_value = [mock_split_result]
                mock_splitter_class.return_value = mock_splitter

                with patch('desktop_app.src.services.department_detector.detect_department') as mock_dept:
                    mock_dept_result = Mock()
                    mock_dept_result.department = Mock()
                    mock_dept_result.department.value = "淡海"
                    mock_dept.return_value = mock_dept_result

                    response = client.post(
                        "/api/pdf/process",
                        files={"file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")},
                        data={"upload_to_drive": "false"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["files_uploaded"] == 0  # 未上傳

    def test_process_pdf_with_upload(self, client, sample_pdf_bytes, mock_barcode_result):
        """測試處理 PDF 並上傳到 Drive"""
        with patch('desktop_app.src.services.barcode_reader.get_barcode_reader') as mock_reader:
            mock_reader_instance = Mock()
            mock_reader_instance.read_from_bytes.return_value = [mock_barcode_result]
            mock_reader.return_value = mock_reader_instance

            with patch('desktop_app.src.services.pdf_splitter.PdfSplitter') as mock_splitter_class:
                mock_splitter = Mock()
                mock_split_result = Mock()
                mock_split_result.output_path = Mock()
                mock_split_result.output_path.name = "TH-12345.pdf"
                mock_split_result.start_page = 1
                mock_split_result.end_page = 1
                mock_split_result.page_count = 1
                mock_split_result.barcode_data = "TH-12345"

                mock_splitter.split_by_barcodes.return_value = [mock_split_result]
                mock_splitter_class.return_value = mock_splitter

                with patch('desktop_app.src.services.department_detector.detect_department') as mock_dept:
                    mock_dept_result = Mock()
                    mock_dept_result.department = Mock()
                    mock_dept_result.department.value = "淡海"
                    mock_dept.return_value = mock_dept_result

                    with patch('desktop_app.src.services.google_drive_uploader.create_uploader_from_credential_manager') as mock_uploader_factory:
                        # Mock Google Drive 上傳器
                        mock_uploader = Mock()
                        mock_upload_result = Mock()
                        mock_upload_result.success = True
                        mock_upload_result.web_view_link = "https://drive.google.com/file/d/test123"
                        mock_upload_result.file_id = "test123"
                        mock_uploader.upload_file.return_value = mock_upload_result
                        mock_uploader_factory.return_value = mock_uploader

                        with patch('desktop_app.src.utils.backend_api_client.get_backend_client') as mock_backend:
                            mock_backend_instance = Mock()
                            mock_backend_instance.get_drive_folder_id.return_value = "folder123"
                            mock_backend.return_value = mock_backend_instance

                            response = client.post(
                                "/api/pdf/process",
                                files={"file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")},
                                data={"upload_to_drive": "true"}
                            )

                            assert response.status_code == 200
                            data = response.json()
                            assert data["success"] is True
                            assert data["files_uploaded"] == 1
                            assert data["split_files"][0]["drive_link"] == "https://drive.google.com/file/d/test123"
