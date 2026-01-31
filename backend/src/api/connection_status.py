"""
連線狀態 API 端點
對應 tasks.md T073: 實作連線狀態 API

提供系統連線狀態查詢功能。
"""

from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import get_current_user, TokenData
from src.services.connection_monitor import get_connection_monitor
from src.services.google_api_tester import get_google_api_tester


router = APIRouter(prefix="/api/status", tags=["連線狀態"])


# ==================== 回應模型 ====================

class ServiceStatusResponse(BaseModel):
    """單一服務狀態回應"""
    name: str = Field(..., description="服務名稱")
    status: str = Field(..., description="狀態: connected, disconnected, error, not_configured")
    message: Optional[str] = Field(None, description="狀態訊息")
    details: Optional[dict] = Field(None, description="詳細資訊")


class CloudStatusResponse(BaseModel):
    """雲端服務狀態回應"""
    overall_status: str = Field(..., description="整體狀態")
    database: ServiceStatusResponse = Field(..., description="資料庫狀態")


class GoogleStatusResponse(BaseModel):
    """Google API 狀態回應"""
    overall_status: str = Field(..., description="整體狀態")
    danhai_sheets: ServiceStatusResponse = Field(..., description="淡海 Sheets 狀態")
    danhai_drive: ServiceStatusResponse = Field(..., description="淡海 Drive 狀態")
    ankeng_sheets: ServiceStatusResponse = Field(..., description="安坑 Sheets 狀態")
    ankeng_drive: ServiceStatusResponse = Field(..., description="安坑 Drive 狀態")


class AllStatusResponse(BaseModel):
    """所有服務狀態回應"""
    overall_status: str = Field(..., description="整體狀態: healthy, degraded, unhealthy")
    cloud: CloudStatusResponse = Field(..., description="雲端服務狀態")
    google: GoogleStatusResponse = Field(..., description="Google API 狀態")
    checked_at: str = Field(..., description="檢查時間 (ISO 格式)")


class CredentialTestResponse(BaseModel):
    """憑證測試結果回應"""
    credential_type: str = Field(..., description="憑證類型: service_account, oauth")
    department: Optional[str] = Field(None, description="部門")
    format_valid: bool = Field(..., description="格式是否有效")
    format_error: Optional[str] = Field(None, description="格式錯誤訊息")
    api_tests: list = Field(default_factory=list, description="API 測試結果")
    overall_success: bool = Field(..., description="整體測試是否成功")


class CredentialTestRequest(BaseModel):
    """憑證測試請求 (Dry Run)"""
    department: Literal["淡海", "安坑"] = Field(..., description="部門名稱")
    base64_json: str = Field(..., description="Base64 編碼的 Service Account JSON")
    spreadsheet_id: Optional[str] = Field(None, description="Google Sheets ID（可選）")
    folder_id: Optional[str] = Field(None, description="Google Drive 資料夾 ID（可選）")


# ==================== API 端點 ====================

@router.get("/cloud", response_model=CloudStatusResponse, summary="查詢雲端服務狀態")
def get_cloud_status(
    current_user: TokenData = Depends(get_current_user)
):
    """
    查詢雲端服務連線狀態

    包括：
    - TiDB 資料庫連線狀態

    需要登入才能存取。
    """
    monitor = get_connection_monitor()
    cloud_status = monitor.check_cloud_status()

    return CloudStatusResponse(
        overall_status=cloud_status.overall_status,
        database=ServiceStatusResponse(
            name=cloud_status.database.name,
            status=cloud_status.database.status,
            message=cloud_status.database.message,
            details=cloud_status.database.details
        )
    )


@router.get("/google", response_model=GoogleStatusResponse, summary="查詢 Google API 狀態")
def get_google_status(
    current_user: TokenData = Depends(get_current_user)
):
    """
    查詢 Google API 連線狀態

    包括：
    - 淡海 Google Sheets
    - 淡海 Google Drive
    - 安坑 Google Sheets
    - 安坑 Google Drive

    需要登入才能存取。

    **注意**: 此端點會實際測試 Google API 連線，可能需要較長時間。
    """
    monitor = get_connection_monitor()
    google_status = monitor.check_google_status()

    return GoogleStatusResponse(
        overall_status=google_status.overall_status,
        danhai_sheets=ServiceStatusResponse(
            name=google_status.danhai_sheets.name,
            status=google_status.danhai_sheets.status,
            message=google_status.danhai_sheets.message,
            details=google_status.danhai_sheets.details
        ),
        danhai_drive=ServiceStatusResponse(
            name=google_status.danhai_drive.name,
            status=google_status.danhai_drive.status,
            message=google_status.danhai_drive.message,
            details=google_status.danhai_drive.details
        ),
        ankeng_sheets=ServiceStatusResponse(
            name=google_status.ankeng_sheets.name,
            status=google_status.ankeng_sheets.status,
            message=google_status.ankeng_sheets.message,
            details=google_status.ankeng_sheets.details
        ),
        ankeng_drive=ServiceStatusResponse(
            name=google_status.ankeng_drive.name,
            status=google_status.ankeng_drive.status,
            message=google_status.ankeng_drive.message,
            details=google_status.ankeng_drive.details
        )
    )


@router.get("/all", response_model=AllStatusResponse, summary="查詢所有服務狀態")
def get_all_status(
    current_user: TokenData = Depends(get_current_user)
):
    """
    查詢所有服務連線狀態

    一次取得所有服務的狀態，包括：
    - 雲端服務（資料庫）
    - Google API（淡海、安坑的 Sheets 和 Drive）

    **注意**: 此端點會執行所有連線測試，可能需要較長時間。
    """
    monitor = get_connection_monitor()
    all_status = monitor.check_all()

    return AllStatusResponse(
        overall_status=all_status["overall_status"],
        cloud=CloudStatusResponse(
            overall_status=all_status["cloud"]["overall_status"],
            database=ServiceStatusResponse(
                name="TiDB Database",
                status=all_status["cloud"]["database"]["status"],
                message=all_status["cloud"]["database"]["message"],
                details=all_status["cloud"]["database"]["details"]
            )
        ),
        google=GoogleStatusResponse(
            overall_status=all_status["google"]["overall_status"],
            danhai_sheets=ServiceStatusResponse(
                name="淡海 Google Sheets",
                status=all_status["google"]["danhai_sheets"]["status"],
                message=all_status["google"]["danhai_sheets"]["message"]
            ),
            danhai_drive=ServiceStatusResponse(
                name="淡海 Google Drive",
                status=all_status["google"]["danhai_drive"]["status"],
                message=all_status["google"]["danhai_drive"]["message"]
            ),
            ankeng_sheets=ServiceStatusResponse(
                name="安坑 Google Sheets",
                status=all_status["google"]["ankeng_sheets"]["status"],
                message=all_status["google"]["ankeng_sheets"]["message"]
            ),
            ankeng_drive=ServiceStatusResponse(
                name="安坑 Google Drive",
                status=all_status["google"]["ankeng_drive"]["status"],
                message=all_status["google"]["ankeng_drive"]["message"]
            )
        ),
        checked_at=all_status["checked_at"]
    )


@router.get("/test-credential", response_model=CredentialTestResponse, summary="測試部門憑證")
def test_department_credential(
    department: Literal["淡海", "安坑"] = Query(..., description="部門名稱"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    測試指定部門的 Google API 憑證

    從系統設定中讀取憑證，測試：
    - 憑證格式是否正確
    - Google Sheets API 存取權限
    - Google Drive API 存取權限

    **注意**: 此端點會實際呼叫 Google API，需要較長時間。
    """
    # 僅 Admin 和 Manager 可以測試憑證
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="僅管理員和主管可以測試憑證"
        )

    tester = get_google_api_tester()
    report = tester.test_department_credentials(department)

    return CredentialTestResponse(
        credential_type=report.credential_type,
        department=report.department,
        format_valid=report.format_valid,
        format_error=report.format_error,
        api_tests=[
            {
                "api_name": t.api_name,
                "result": t.result,
                "message": t.message,
                "scope": t.scope,
                "details": t.details
            }
            for t in report.api_tests
        ],
        overall_success=report.overall_success
    )


@router.post("/test-credential-content", response_model=CredentialTestResponse, summary="測試憑證內容 (Dry Run)")
def test_credential_content(
    request: CredentialTestRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    測試尚未儲存的憑證內容 (Dry Run)

    用於在儲存前驗證憑證的有效性：
    - 驗證憑證格式是否正確
    - 測試 Google Sheets API 存取權限（如提供 spreadsheet_id）
    - 測試 Google Drive API 存取權限（如提供 folder_id）

    **注意**: 此端點會實際呼叫 Google API，需要較長時間。

    **Gemini Review Fix**: 新增此端點以支援前端 Dry Run 功能
    """
    # 僅 Admin 和 Manager 可以測試憑證
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="僅管理員和主管可以測試憑證"
        )

    tester = get_google_api_tester()
    report = tester.test_service_account(
        base64_json=request.base64_json,
        department=request.department,
        spreadsheet_id=request.spreadsheet_id,
        folder_id=request.folder_id
    )

    return CredentialTestResponse(
        credential_type=report.credential_type,
        department=report.department,
        format_valid=report.format_valid,
        format_error=report.format_error,
        api_tests=[
            {
                "api_name": t.api_name,
                "result": t.result,
                "message": t.message,
                "scope": t.scope,
                "details": t.details
            }
            for t in report.api_tests
        ],
        overall_success=report.overall_success
    )


# 公開的健康檢查端點（不需要認證）
@router.get("/health", summary="快速健康檢查")
def health_check():
    """
    快速健康檢查

    僅檢查資料庫連線，用於監控系統。
    此端點不需要認證。
    """
    monitor = get_connection_monitor()
    db_status = monitor.check_database()

    return {
        "status": "healthy" if db_status.status == "connected" else "unhealthy",
        "database": db_status.status,
        "message": db_status.message
    }
