"""
資料模型模組

匯出所有 SQLAlchemy 模型供外部使用。
"""

from .base import Base, TimestampMixin
from .driving_competition import DrivingCompetition
from .driving_daily_stats import DrivingDailyStats
from .employee import Employee
from .employee_transfer import EmployeeTransfer
from .google_oauth_token import Department, GoogleOAuthToken
from .oauth_state import OAuthState
from .route_standard_time import RouteStandardTime
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
    # Phase 9: 駕駛時數與競賽
    "RouteStandardTime",
    "DrivingDailyStats",
    "DrivingCompetition",
]
