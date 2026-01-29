"""
PDF 處理 API
對應 tasks.md T094: 實作 PDF 處理 API

功能：
- POST /api/pdf/process: 處理 PDF（識別條碼、切分、上傳到 Drive）
- POST /api/pdf/scan: 僅識別 PDF 中的條碼
- POST /api/pdf/split: 依條碼切分 PDF
"""

import logging
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pdf", tags=["PDF Processing"])


# ============================================================
# Pydantic Models
# ============================================================

class BarcodeInfo(BaseModel):
    """條碼資訊"""
    page_number: int
    barcode_type: str
    barcode_data: str
    department: Optional[str] = None


class ScanResult(BaseModel):
    """掃描結果"""
    success: bool
    file_name: str
    total_pages: int
    barcodes: list[BarcodeInfo]
    error_message: Optional[str] = None


class SplitFileInfo(BaseModel):
    """切分檔案資訊"""
    file_name: str
    start_page: int
    end_page: int
    page_count: int
    barcode_data: Optional[str] = None
    department: Optional[str] = None
    drive_link: Optional[str] = None
    drive_file_id: Optional[str] = None


class ProcessResult(BaseModel):
    """處理結果"""
    success: bool
    task_id: str
    file_name: str
    total_pages: int
    barcodes_found: int
    files_created: int
    files_uploaded: int
    split_files: list[SplitFileInfo]
    error_message: Optional[str] = None
    processing_time_ms: int


# ============================================================
# API Endpoints
# ============================================================

@router.post("/scan", response_model=ScanResult)
async def scan_pdf(
    file: UploadFile = File(..., description="PDF 檔案")
):
    """
    掃描 PDF 中的條碼

    僅識別條碼，不進行切分或上傳。
    """
    from desktop_app.src.services.barcode_reader import get_barcode_reader
    from desktop_app.src.services.department_detector import detect_department
    from PyPDF2 import PdfReader
    import io

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="僅支援 PDF 檔案")

    try:
        # 讀取檔案內容
        content = await file.read()

        # 取得頁數
        pdf_reader = PdfReader(io.BytesIO(content))
        total_pages = len(pdf_reader.pages)

        # 識別條碼
        reader = get_barcode_reader()
        barcodes = reader.read_from_bytes(content)

        # 判斷部門
        barcode_infos = []
        for bc in barcodes:
            dept_result = detect_department(bc.barcode_data)
            barcode_infos.append(BarcodeInfo(
                page_number=bc.page_number,
                barcode_type=bc.barcode_type,
                barcode_data=bc.barcode_data,
                department=dept_result.department.value if dept_result.department else None
            ))

        return ScanResult(
            success=True,
            file_name=file.filename,
            total_pages=total_pages,
            barcodes=barcode_infos
        )

    except Exception as e:
        logger.error(f"PDF 掃描失敗: {e}")
        return ScanResult(
            success=False,
            file_name=file.filename or "unknown",
            total_pages=0,
            barcodes=[],
            error_message=str(e)
        )


@router.post("/split", response_model=ProcessResult)
async def split_pdf(
    file: UploadFile = File(..., description="PDF 檔案"),
    output_dir: Optional[str] = Form(None, description="輸出目錄（預設為暫存目錄）")
):
    """
    依條碼切分 PDF

    根據識別到的條碼，將 PDF 切分為多個檔案。
    """
    from desktop_app.src.services.barcode_reader import get_barcode_reader
    from desktop_app.src.services.pdf_splitter import PdfSplitter
    from desktop_app.src.services.department_detector import detect_department
    from PyPDF2 import PdfReader
    import io
    import time

    start_time = time.time()
    task_id = str(uuid.uuid4())[:8]

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="僅支援 PDF 檔案")

    try:
        # 讀取檔案內容
        content = await file.read()

        # 取得頁數
        pdf_reader = PdfReader(io.BytesIO(content))
        total_pages = len(pdf_reader.pages)

        # 識別條碼
        reader = get_barcode_reader()
        barcodes = reader.read_from_bytes(content)

        if not barcodes:
            return ProcessResult(
                success=False,
                task_id=task_id,
                file_name=file.filename,
                total_pages=total_pages,
                barcodes_found=0,
                files_created=0,
                files_uploaded=0,
                split_files=[],
                error_message="PDF 中未發現條碼",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # 建立暫存目錄
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
        else:
            out_path = Path(tempfile.mkdtemp(prefix="pdf_split_"))

        # 儲存原始 PDF
        temp_pdf = out_path / f"original_{task_id}.pdf"
        with open(temp_pdf, 'wb') as f:
            f.write(content)

        # 切分 PDF
        splitter = PdfSplitter(output_dir=out_path)
        split_results = splitter.split_by_barcodes(temp_pdf, barcodes)

        # 建立結果
        split_files = []
        for result in split_results:
            dept_result = detect_department(result.barcode_data) if result.barcode_data else None
            split_files.append(SplitFileInfo(
                file_name=result.output_path.name,
                start_page=result.start_page,
                end_page=result.end_page,
                page_count=result.page_count,
                barcode_data=result.barcode_data,
                department=dept_result.department.value if dept_result and dept_result.department else None
            ))

        # 清理原始檔案
        temp_pdf.unlink(missing_ok=True)

        return ProcessResult(
            success=True,
            task_id=task_id,
            file_name=file.filename,
            total_pages=total_pages,
            barcodes_found=len(barcodes),
            files_created=len(split_results),
            files_uploaded=0,
            split_files=split_files,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )

    except Exception as e:
        logger.error(f"PDF 切分失敗: {e}")
        return ProcessResult(
            success=False,
            task_id=task_id,
            file_name=file.filename or "unknown",
            total_pages=0,
            barcodes_found=0,
            files_created=0,
            files_uploaded=0,
            split_files=[],
            error_message=str(e),
            processing_time_ms=int((time.time() - start_time) * 1000)
        )


@router.post("/process", response_model=ProcessResult)
async def process_pdf(
    file: UploadFile = File(..., description="PDF 檔案"),
    upload_to_drive: bool = Form(True, description="是否上傳到 Google Drive"),
    output_dir: Optional[str] = Form(None, description="本機輸出目錄")
):
    """
    完整處理 PDF

    1. 識別條碼
    2. 判斷部門
    3. 依條碼切分
    4. 上傳到對應部門的 Google Drive 資料夾

    Returns:
        ProcessResult: 處理結果，包含切分檔案資訊和 Drive 連結
    """
    from desktop_app.src.services.barcode_reader import get_barcode_reader
    from desktop_app.src.services.pdf_splitter import PdfSplitter
    from desktop_app.src.services.department_detector import detect_department, Department
    from desktop_app.src.services.google_drive_uploader import create_uploader_from_credential_manager
    from PyPDF2 import PdfReader
    import io
    import time

    start_time = time.time()
    task_id = str(uuid.uuid4())[:8]

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="僅支援 PDF 檔案")

    try:
        # 讀取檔案內容
        content = await file.read()

        # 取得頁數
        pdf_reader = PdfReader(io.BytesIO(content))
        total_pages = len(pdf_reader.pages)

        # 識別條碼
        reader = get_barcode_reader()
        barcodes = reader.read_from_bytes(content)

        if not barcodes:
            return ProcessResult(
                success=False,
                task_id=task_id,
                file_name=file.filename,
                total_pages=total_pages,
                barcodes_found=0,
                files_created=0,
                files_uploaded=0,
                split_files=[],
                error_message="PDF 中未發現條碼",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # 建立輸出目錄
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
        else:
            out_path = Path(tempfile.mkdtemp(prefix="pdf_process_"))

        # 儲存原始 PDF
        temp_pdf = out_path / f"original_{task_id}.pdf"
        with open(temp_pdf, 'wb') as f:
            f.write(content)

        # 切分 PDF
        splitter = PdfSplitter(output_dir=out_path)
        split_results = splitter.split_by_barcodes(temp_pdf, barcodes)

        # 處理每個切分結果
        split_files = []
        files_uploaded = 0

        # 按部門分組的上傳器快取
        uploaders = {}

        for result in split_results:
            # 判斷部門
            dept_result = detect_department(result.barcode_data) if result.barcode_data else None
            department = dept_result.department if dept_result else None

            file_info = SplitFileInfo(
                file_name=result.output_path.name,
                start_page=result.start_page,
                end_page=result.end_page,
                page_count=result.page_count,
                barcode_data=result.barcode_data,
                department=department.value if department else None
            )

            # 上傳到 Drive
            if upload_to_drive and department:
                dept_name = department.value

                # 取得或建立上傳器
                if dept_name not in uploaders:
                    uploaders[dept_name] = create_uploader_from_credential_manager(dept_name)

                uploader = uploaders.get(dept_name)

                if uploader:
                    # TODO: 從系統設定取得資料夾 ID
                    folder_id = None  # 需要從設定取得

                    upload_result = uploader.upload_file(
                        file_path=result.output_path,
                        folder_id=folder_id,
                        description=f"來源: {file.filename}, 條碼: {result.barcode_data}"
                    )

                    if upload_result.success:
                        file_info.drive_link = upload_result.web_view_link
                        file_info.drive_file_id = upload_result.file_id
                        files_uploaded += 1
                    else:
                        logger.warning(f"上傳失敗: {upload_result.error_message}")

            split_files.append(file_info)

        # 清理原始檔案
        temp_pdf.unlink(missing_ok=True)

        return ProcessResult(
            success=True,
            task_id=task_id,
            file_name=file.filename,
            total_pages=total_pages,
            barcodes_found=len(barcodes),
            files_created=len(split_results),
            files_uploaded=files_uploaded,
            split_files=split_files,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )

    except Exception as e:
        logger.error(f"PDF 處理失敗: {e}")
        return ProcessResult(
            success=False,
            task_id=task_id,
            file_name=file.filename or "unknown",
            total_pages=0,
            barcodes_found=0,
            files_created=0,
            files_uploaded=0,
            split_files=[],
            error_message=str(e),
            processing_time_ms=int((time.time() - start_time) * 1000)
        )


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    取得處理任務狀態

    （目前為同步處理，此端點為未來擴充用）
    """
    return {
        "task_id": task_id,
        "status": "completed",
        "message": "目前為同步處理模式，任務已完成"
    }
