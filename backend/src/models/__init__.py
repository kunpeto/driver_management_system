"""
資料模型模組

匯出所有 SQLAlchemy 模型供外部使用。
"""

from .base import Base, TimestampMixin
from .driving_competition import DrivingCompetition
from .driving_daily_stats import DrivingDailyStats
from .employee import Employee
from .employee_transfer import EmployeeTransfer
from src.constants import Department
from .google_oauth_token import GoogleOAuthToken
from .oauth_state import OAuthState
from .route_standard_time import RouteStandardTime
from .system_setting import DepartmentScope, SettingKeys, SystemSetting
from .user import User

# Phase 11: 履歷管理模型
from .profile import ConversionStatus, Profile, ProfileType
from .event_investigation import EventCategory, EventInvestigation
from .personnel_interview import PersonnelInterview
from .corrective_measures import CompletionStatus, CorrectiveMeasures
from .assessment_notice import AssessmentNotice, AssessmentType

# Phase 12: 考核系統模型
from .assessment_standard import (
    AssessmentCategory,
    AssessmentStandard,
    BonusCategory,
    CalculationCycle,
)
from .assessment_record import AssessmentRecord
from .fault_responsibility import (
    CHECKLIST_KEYS,
    CHECKLIST_LABELS,
    FaultResponsibilityAssessment,
    ResponsibilityLevel,
    determine_responsibility,
)
from .cumulative_counter import (
    CumulativeCounter,
    R_CUMULATIVE_GROUP,
    get_cumulative_category,
)
from .monthly_reward import MonthlyReward

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
    # Phase 11: 履歷管理
    "Profile",
    "ProfileType",
    "ConversionStatus",
    "EventInvestigation",
    "EventCategory",
    "PersonnelInterview",
    "CorrectiveMeasures",
    "CompletionStatus",
    "AssessmentNotice",
    "AssessmentType",
    # Phase 12: 考核系統
    "AssessmentStandard",
    "AssessmentCategory",
    "BonusCategory",
    "CalculationCycle",
    "AssessmentRecord",
    "FaultResponsibilityAssessment",
    "ResponsibilityLevel",
    "CHECKLIST_KEYS",
    "CHECKLIST_LABELS",
    "determine_responsibility",
    "CumulativeCounter",
    "R_CUMULATIVE_GROUP",
    "get_cumulative_category",
    "MonthlyReward",
]
