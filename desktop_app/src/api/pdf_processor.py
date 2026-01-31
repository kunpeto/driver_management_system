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

    API CONTRACT: CRITICAL
    CONSUMERS: 前端 Web 應用
    SINCE: 1.0.0

    警告：此端點被前端直接依賴
    任何破壞性變更都會導致前端功能失效

    禁止的變更：
    - 移除回應欄位（success, file_name, total_pages, barcodes, error_message）
    - 變更 barcodes 陣列元素的欄位（page_number, barcode_type, barcode_data, department）
    - 變更欄位類型
    - 變更 URL 路徑

    詳見 docs/API_CONTRACT.md

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

    API CONTRACT: CRITICAL
    CONSUMERS: 前端 Web 應用
    SINCE: 1.0.0

    警告：此端點被前端直接依賴
    任何破壞性變更都會導致前端功能失效

    禁止的變更：
    - 移除 ProcessResult 回應欄位
    - 變更欄位類型
    - 變更 URL 路徑

    詳見 docs/API_CONTRACT.md

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

    API CONTRACT: CRITICAL
    CONSUMERS: 前端 Web 應用
    SINCE: 1.0.0

    警告：此端點被前端直接依賴
    任何破壞性變更都會導致前端功能失效

    禁止的變更：
    - 移除 ProcessResult 回應欄位
    - 變更 split_files 陣列元素的欄位
    - 變更欄位類型
    - 變更 URL 路徑

    詳見 docs/API_CONTRACT.md

    處理流程：
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
                    # 從後端 API 取得資料夾 ID
                    from desktop_app.src.utils.backend_api_client import get_backend_client

                    backend_client = get_backend_client()
                    folder_id = backend_client.get_drive_folder_id(dept_name)

                    if not folder_id:
                        logger.warning(f"未設定 {dept_name} 的 Google Drive Folder ID，檔案將上傳到根目錄")

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


# ============================================================
# Phase 14: 履歷 PDF 上傳（T191）
# ============================================================

class ProfileUploadRequest(BaseModel):
    """履歷上傳請求"""
    profile_type: str  # event_investigation, personnel_interview, etc.
    year_month: str    # YYYYMM 格式
    file_name: Optional[str] = None
    set_domain_permission: bool = True


class ProfileUploadResponse(BaseModel):
    """履歷上傳回應"""
    success: bool
    file_id: Optional[str] = None
    web_view_link: Optional[str] = None
    file_name: str
    folder_path: str
    error_message: Optional[str] = None


@router.post("/upload-profile", response_model=ProfileUploadResponse)
async def upload_profile_pdf(
    file: UploadFile = File(..., description="PDF 檔案"),
    profile_type: str = Form(..., description="履歷類型"),
    year_month: str = Form(..., description="年月 (YYYYMM)"),
    department: str = Form(..., description="部門 (淡海/安坑)"),
    file_name: Optional[str] = Form(None, description="自訂檔案名稱"),
    folder_path: Optional[str] = Form(None, description="資料夾路徑（由後端提供，優先使用）"),
    set_domain_permission: bool = Form(True, description="設定網域權限")
):
    """
    上傳履歷 PDF 到 Google Drive（Phase 14 T191）

    自動依履歷類型與日期建立資料夾結構：
    - {根資料夾}/{年月}/{類型}/檔案.pdf
    - 例如：履歷/202601/事件調查/事件調查_A12345_20260115.pdf

    權限設定：
    - 預設設定為「僅網域內可檢視」

    流程：
    1. 前端呼叫後端 GET /api/profiles/{id}/upload-params 取得參數
    2. 前端呼叫本 API 上傳 PDF
    3. 前端呼叫後端 POST /api/profiles/{id}/complete 更新 gdrive_link
    """
    from desktop_app.src.services.google_drive_uploader import (
        create_profile_uploader,
        ProfileUploadResult
    )
    from desktop_app.src.utils.backend_api_client import get_backend_client

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="僅支援 PDF 檔案")

    # 驗證年月格式
    if len(year_month) != 6 or not year_month.isdigit():
        raise HTTPException(status_code=400, detail="年月格式錯誤，應為 YYYYMM")

    try:
        # 從後端取得資料夾 ID
        backend_client = get_backend_client()
        folder_id = backend_client.get_drive_folder_id(department)

        if not folder_id:
            return ProfileUploadResponse(
                success=False,
                file_name=file_name or file.filename,
                folder_path=f"{year_month}/{profile_type}",
                error_message=f"未設定 {department} 的 Google Drive 資料夾 ID"
            )

        # 從組態取得網域（用於設定權限）
        domain = backend_client.get_domain_for_permission()

        # 建立上傳器
        uploader = create_profile_uploader(
            department=department,
            root_folder_id=folder_id,
            domain=domain if set_domain_permission else None
        )

        if not uploader:
            return ProfileUploadResponse(
                success=False,
                file_name=file_name or file.filename,
                folder_path=f"{year_month}/{profile_type}",
                error_message=f"無法建立 {department} 的上傳器，請檢查 OAuth 授權"
            )

        # 儲存檔案到暫存
        content = await file.read()
        temp_path = Path(tempfile.mktemp(suffix='.pdf'))
        with open(temp_path, 'wb') as f:
            f.write(content)

        try:
            # 上傳（優先使用後端提供的 folder_path，Gemini Review P1 修正）
            result = uploader.upload_profile_pdf(
                file_path=temp_path,
                profile_type=profile_type,
                year_month=year_month,
                file_name=file_name or file.filename,
                folder_path=folder_path,  # 後端提供的路徑優先
                set_domain_permission=set_domain_permission
            )

            return ProfileUploadResponse(
                success=result.success,
                file_id=result.file_id,
                web_view_link=result.web_view_link,
                file_name=result.file_name,
                folder_path=result.folder_path,
                error_message=result.error_message
            )
        finally:
            # 清理暫存檔案
            temp_path.unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"履歷 PDF 上傳失敗: {e}")
        return ProfileUploadResponse(
            success=False,
            file_name=file_name or file.filename or "unknown",
            folder_path=f"{year_month}/{profile_type}",
            error_message=str(e)
        )
