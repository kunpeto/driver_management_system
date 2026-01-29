"""
資料模型模組

匯出所有 SQLAlchemy 模型供外部使用。
"""

from .base import Base, TimestampMixin
from .employee import Employee
from .employee_transfer import EmployeeTransfer
from .google_oauth_token import Department, GoogleOAuthToken
from .oauth_state import OAuthState
from .system_setting import DepartmentScope, SettingKeys, SystemSetting
from .user import User

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # SystemSetting
    "SystemSetting",
    "DepartmentScope",
    "SettingKeys",
    # GoogleOAuthToken
    "GoogleOAuthToken",
    "Department",
    # OAuthState
    "OAuthState",
    # Employee
    "Employee",
    "EmployeeTransfer",
    # User
    "User",
]
