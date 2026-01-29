"""
API 路由模組

匯出所有 API 路由供 main.py 註冊使用。
"""

from .google_credentials import router as google_credentials_router
from .system_settings import router as system_settings_router
from .employees import router as employees_router
from .employee_transfers import router as employee_transfers_router
from .employee_batch import router as employee_batch_router
from .auth import router as auth_router
from .users import router as users_router
from .connection_status import router as connection_status_router
from .schedules import router as schedules_router
from .sync_tasks import router as sync_tasks_router
from .google_oauth import router as google_oauth_router

__all__ = [
    "system_settings_router",
    "google_credentials_router",
    "employees_router",
    "employee_transfers_router",
    "employee_batch_router",
    "auth_router",
    "users_router",
    "connection_status_router",
    "schedules_router",
    "sync_tasks_router",
    "google_oauth_router",
]
