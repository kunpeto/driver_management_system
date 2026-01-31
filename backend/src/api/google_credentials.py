"""
Google 憑證驗證 API 端點
對應 tasks.md T039: 實作憑證驗證 API

修復 Gemini Review:
- High Priority #1: 新增儲存憑證 API
- High Priority #2: 加入權限驗證
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import require_admin, Role
from src.services.credential_validator import ValidationResult
from src.services.google_credential_validator import (
    DryRunResult,
    GoogleCredentialValidator,
)
from src.services.google_oauth_token_service import (
    GoogleOAuthTokenService,
    GoogleOAuthTokenServiceError,
)

router = APIRouter()


# ============================================================
# Pydantic 模型
# ============================================================

class ValidateServiceAccountRequest(BaseModel):
    """驗證 Service Account 請求"""
    base64_json: str = Field(
        ...,
        min_length=100,
        description="Base64 編碼的 Service Account JSON"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "base64_json": "eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6..."
                }
            ]
        }
    }


class ValidateSheetsRequest(BaseModel):
    """驗證 Sheets 存取請求"""
    base64_json: str = Field(
        ...,
        min_length=100,
        description="Base64 編碼的 Service Account JSON"
    )
    spreadsheet_id: str = Field(
        ...,
        min_length=20,
        description="Google Sheets ID"
    )


class ValidateDriveRequest(BaseModel):
    """驗證 Drive 存取請求"""
    base64_json: str = Field(
        ...,
        min_length=100,
        description="Base64 編碼的 Service Account JSON"
    )
    folder_id: str = Field(
        ...,
        min_length=10,
        description="Google Drive 資料夾 ID"
    )


class DryRunRequest(BaseModel):
    """Dry Run 測試請求"""
    department: str = Field(
        ...,
        description="部門名稱：淡海、安坑"
    )
    base64_json: str = Field(
        ...,
        min_length=100,
        description="Base64 編碼的 Service Account JSON"
    )
    sheets_id: Optional[str] = Field(
        None,
        description="Google Sheets ID（可選，若未提供則從設定讀取）"
    )
    drive_folder_id: Optional[str] = Field(
        None,
        description="Google Drive 資料夾 ID（可選，若未提供則從設定讀取）"
    )


class QuickValidateRequest(BaseModel):
    """快速驗證請求"""
    base64_json: str = Field(
        ...,
        min_length=100,
        description="Base64 編碼的 Service Account JSON"
    )
    spreadsheet_id: str = Field(
        ...,
        min_length=20,
        description="Google Sheets ID"
    )


class SaveCredentialRequest(BaseModel):
    """儲存憑證請求"""
    base64_json: str = Field(
        ...,
        min_length=100,
        description="Base64 編碼的 Service Account JSON"
    )
    authorized_email: Optional[str] = Field(
        None,
        description="授權者/管理者 Email"
    )


class ValidationResponse(BaseModel):
    """驗證回應"""
    valid: bool
    error: Optional[str] = None
    details: Optional[dict] = None


class DryRunResponse(BaseModel):
    """Dry Run 回應"""
    success: bool
    sheets_valid: bool
    drive_valid: bool
    sheets_error: Optional[str] = None
    drive_error: Optional[str] = None
    sheets_details: Optional[dict] = None
    drive_details: Optional[dict] = None


class QuickValidateResponse(BaseModel):
    """快速驗證回應"""
    valid: bool
    step: Optional[str] = None
    error: Optional[str] = None
    service_account: Optional[dict] = None
    spreadsheet: Optional[dict] = None


class CredentialStatusResponse(BaseModel):
    """憑證狀態回應"""
    department: str
    has_credential: bool
    authorized_email: Optional[str] = None
    updated_at: Optional[str] = None


class SaveCredentialResponse(BaseModel):
    """儲存憑證回應"""
    success: bool
    department: str
    message: str


# ============================================================
# 輔助函數
# ============================================================

def _validation_result_to_response(result: ValidationResult) -> ValidationResponse:
    """將 ValidationResult 轉換為 API 回應"""
    return ValidationResponse(
        valid=result.valid,
        error=result.error,
        details=result.details
    )


def _dry_run_result_to_response(result: DryRunResult) -> DryRunResponse:
    """將 DryRunResult 轉換為 API 回應"""
    return DryRunResponse(
        success=result.success,
        sheets_valid=result.sheets_valid,
        drive_valid=result.drive_valid,
        sheets_error=result.sheets_error,
        drive_error=result.drive_error,
        sheets_details=result.sheets_details,
        drive_details=result.drive_details
    )


def _validate_department(department: str) -> None:
    """驗證部門名稱"""
    valid_departments = ["淡海", "安坑"]
    if department not in valid_departments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的部門名稱，有效值為：{valid_departments}"
        )


# ============================================================
# 憑證儲存 API（需要管理員權限）
# ============================================================

@router.post(
    "/credentials/{department}",
    response_model=SaveCredentialResponse,
    summary="儲存部門憑證",
    description="儲存指定部門的 Service Account 憑證（僅管理員可操作）"
)
def save_credential(
    department: str,
    data: SaveCredentialRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    儲存部門的 Service Account 憑證

    憑證會經過 Fernet 加密後儲存到資料庫。

    - **department**: 部門名稱（淡海、安坑）
    - **base64_json**: Base64 編碼的 Service Account JSON
    - **authorized_email**: 授權者/管理者 Email（選填）
    """
    _validate_department(department)

    service = GoogleOAuthTokenService(db)

    try:
        service.save_service_account_json(
            department=department,
            base64_json=data.base64_json,
            authorized_email=data.authorized_email or current_user.username
        )

        return SaveCredentialResponse(
            success=True,
            department=department,
            message=f"{department} 部門的憑證已儲存"
        )

    except GoogleOAuthTokenServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/credentials/{department}",
    response_model=CredentialStatusResponse,
    summary="取得部門憑證狀態",
    description="取得指定部門的憑證狀態（僅管理員可操作）"
)
def get_credential_status(
    department: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    取得部門憑證狀態

    不會返回實際的憑證內容，只返回狀態資訊。
    """
    _validate_department(department)

    service = GoogleOAuthTokenService(db)
    token = service.get_by_department(department)

    if token:
        return CredentialStatusResponse(
            department=department,
            has_credential=token.has_valid_refresh_token,
            authorized_email=token.authorized_user_email,
            updated_at=token.updated_at.isoformat() if token.updated_at else None
        )
    else:
        return CredentialStatusResponse(
            department=department,
            has_credential=False
        )


@router.delete(
    "/credentials/{department}",
    summary="刪除部門憑證",
    description="刪除指定部門的憑證（僅管理員可操作）"
)
def delete_credential(
    department: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """刪除部門憑證"""
    _validate_department(department)

    service = GoogleOAuthTokenService(db)
    deleted = service.delete(department)

    if deleted:
        return {"success": True, "message": f"{department} 部門的憑證已刪除"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{department} 部門沒有設定憑證"
        )


@router.get(
    "/credentials",
    summary="取得所有部門憑證狀態",
    description="取得所有部門的憑證狀態（僅管理員可操作）"
)
def get_all_credential_status(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """取得所有部門的憑證狀態"""
    service = GoogleOAuthTokenService(db)
    return service.get_credential_status()


# ============================================================
# 驗證 API（需要管理員權限）
# ============================================================

@router.post(
    "/validate-credentials",
    response_model=ValidationResponse,
    summary="驗證 Service Account 格式",
    description="驗證 Service Account JSON 的格式是否正確（僅管理員可操作）"
)
def validate_credentials(
    data: ValidateServiceAccountRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    驗證 Service Account 格式

    檢查：
    - Base64 解碼是否成功
    - JSON 格式是否正確
    - 必要欄位是否存在
    - type 是否為 'service_account'
    - private_key 格式是否正確
    """
    validator = GoogleCredentialValidator(db)
    result = validator.validate_service_account(data.base64_json)
    return _validation_result_to_response(result)


@router.post(
    "/test-sheets",
    response_model=ValidationResponse,
    summary="測試 Sheets 連線",
    description="測試是否可以存取指定的 Google Sheets（僅管理員可操作）"
)
def test_sheets_connection(
    data: ValidateSheetsRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    測試 Google Sheets 連線

    執行實際的 API 呼叫，驗證憑證是否有效且有權限存取指定的試算表。
    """
    validator = GoogleCredentialValidator(db)
    result = validator.test_sheets_connection(data.base64_json, data.spreadsheet_id)
    return _validation_result_to_response(result)


@router.post(
    "/test-drive",
    response_model=ValidationResponse,
    summary="測試 Drive 連線",
    description="測試是否可以存取指定的 Google Drive 資料夾（僅管理員可操作）"
)
def test_drive_connection(
    data: ValidateDriveRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    測試 Google Drive 連線

    執行實際的 API 呼叫，驗證憑證是否有效且有權限存取指定的資料夾。
    """
    validator = GoogleCredentialValidator(db)
    result = validator.test_drive_connection(data.base64_json, data.folder_id)
    return _validation_result_to_response(result)


@router.post(
    "/dry-run",
    response_model=DryRunResponse,
    summary="執行 Dry Run 測試",
    description="執行完整的 Dry Run 測試（僅管理員可操作）"
)
def dry_run(
    data: DryRunRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    執行 Dry Run 測試

    測試指定部門的所有 Google 服務連線。
    """
    _validate_department(data.department)

    validator = GoogleCredentialValidator(db)
    result = validator.dry_run_department(
        department=data.department,
        base64_json=data.base64_json,
        sheets_id=data.sheets_id,
        drive_folder_id=data.drive_folder_id
    )
    return _dry_run_result_to_response(result)


@router.post(
    "/quick-validate",
    response_model=QuickValidateResponse,
    summary="快速驗證",
    description="快速驗證憑證格式和 Sheets 連線（僅管理員可操作）"
)
def quick_validate(
    data: QuickValidateRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    快速驗證

    執行格式驗證和 Sheets 連線測試，適合用於表單即時驗證。
    """
    validator = GoogleCredentialValidator(db)
    result = validator.quick_validate(data.base64_json, data.spreadsheet_id)
    return QuickValidateResponse(**result)


@router.post(
    "/validate-all-departments",
    summary="驗證所有部門",
    description="驗證所有部門的憑證（僅管理員可操作）"
)
def validate_all_departments(
    data: ValidateServiceAccountRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    驗證所有部門

    使用同一組憑證驗證淡海和安坑兩個部門的 Google 服務連線。
    """
    validator = GoogleCredentialValidator(db)
    results = validator.validate_all_departments(data.base64_json)

    response = {}
    for dept, result in results.items():
        response[dept] = {
            "success": result.success,
            "sheets_valid": result.sheets_valid,
            "drive_valid": result.drive_valid,
            "sheets_error": result.sheets_error,
            "drive_error": result.drive_error
        }

    return {
        "departments": response,
        "all_valid": all(r.success for r in results.values())
    }
