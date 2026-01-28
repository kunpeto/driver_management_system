"""
錯誤處理中間件
對應 tasks.md T024: 建立錯誤處理中間件

功能：
- 統一錯誤回應格式
- 捕捉未處理的例外
- 記錄錯誤日誌
"""

import traceback
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.utils.logger import logger, log_security_event
from src.config.settings import get_settings


class APIError(Exception):
    """
    自訂 API 錯誤

    用於拋出具有特定狀態碼和訊息的錯誤。
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = None,
        details: dict = None
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code or f"ERR_{status_code}"
        self.details = details or {}
        super().__init__(message)


class NotFoundError(APIError):
    """資源不存在錯誤"""

    def __init__(self, resource: str, resource_id: Union[int, str] = None):
        message = f"{resource} 不存在"
        if resource_id:
            message = f"{resource} (ID: {resource_id}) 不存在"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="NOT_FOUND"
        )


class ValidationError(APIError):
    """資料驗證錯誤"""

    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else {}
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationError(APIError):
    """認證錯誤"""

    def __init__(self, message: str = "認證失敗"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTHENTICATION_ERROR"
        )


class PermissionError(APIError):
    """權限錯誤"""

    def __init__(self, message: str = "權限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="PERMISSION_DENIED"
        )


class DatabaseError(APIError):
    """資料庫錯誤"""

    def __init__(self, message: str = "資料庫操作失敗"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="DATABASE_ERROR"
        )


def create_error_response(
    status_code: int,
    message: str,
    error_code: str = None,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    """
    建立統一格式的錯誤回應

    Args:
        status_code: HTTP 狀態碼
        message: 錯誤訊息
        error_code: 錯誤代碼
        details: 詳細資訊
        request_id: 請求 ID

    Returns:
        JSONResponse: 格式化的錯誤回應
    """
    content = {
        "success": False,
        "error": {
            "code": error_code or f"ERR_{status_code}",
            "message": message,
        }
    }

    if details:
        content["error"]["details"] = details

    if request_id:
        content["error"]["request_id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=content
    )


def setup_exception_handlers(app: FastAPI):
    """
    設定例外處理器

    Args:
        app: FastAPI 應用實例
    """
    settings = get_settings()

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """處理自訂 API 錯誤"""
        logger.warning(
            f"API Error: {exc.error_code} - {exc.message}",
            path=str(request.url.path),
            method=request.method
        )
        return create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """處理 HTTP 例外"""
        # 401/403 視為安全事件
        if exc.status_code in [401, 403]:
            log_security_event(
                f"HTTP {exc.status_code}: {exc.detail}",
                severity="warning",
                path=str(request.url.path),
                method=request.method
            )

        return create_error_response(
            status_code=exc.status_code,
            message=str(exc.detail)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """處理請求驗證錯誤"""
        # 提取驗證錯誤細節
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })

        logger.debug(f"Validation Error: {errors}", path=str(request.url.path))

        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="請求資料驗證失敗",
            error_code="VALIDATION_ERROR",
            details={"errors": errors}
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """處理 SQLAlchemy 錯誤"""
        logger.error(
            f"Database Error: {str(exc)}",
            path=str(request.url.path),
            method=request.method,
            exc_info=True
        )

        # 生產環境不暴露詳細錯誤訊息
        if settings.is_production:
            message = "資料庫操作失敗，請稍後再試"
        else:
            message = f"資料庫錯誤: {str(exc)}"

        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="DATABASE_ERROR"
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """處理未預期的例外"""
        # 記錄完整的錯誤堆疊
        logger.error(
            f"Unhandled Exception: {str(exc)}",
            path=str(request.url.path),
            method=request.method,
            traceback=traceback.format_exc()
        )

        # 生產環境不暴露詳細錯誤訊息
        if settings.is_production:
            message = "伺服器發生錯誤，請稍後再試"
            details = None
        else:
            message = f"未預期的錯誤: {str(exc)}"
            details = {"traceback": traceback.format_exc().split("\n")}

        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="INTERNAL_ERROR",
            details=details
        )


# 匯出
__all__ = [
    "APIError",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    "PermissionError",
    "DatabaseError",
    "create_error_response",
    "setup_exception_handlers",
]
