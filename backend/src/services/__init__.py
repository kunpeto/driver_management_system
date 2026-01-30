"""
服務模組

匯出所有服務供外部使用。
"""

from .credential_validator import (
    CredentialValidator,
    ValidationResult,
    get_credential_validator,
)
from .google_credential_validator import DryRunResult, GoogleCredentialValidator
from .google_oauth_token_service import (
    EncryptionError,
    GoogleOAuthTokenService,
    GoogleOAuthTokenServiceError,
    TokenNotFoundError,
)
from .system_setting_service import (
    DuplicateSettingError,
    SettingNotFoundError,
    SystemSettingService,
    SystemSettingServiceError,
)

# Phase 12: 考核系統服務
from .cumulative_category import (
    R_CUMULATIVE_GROUP,
    calculate_cumulative_multiplier,
    calculate_next_cumulative_multiplier,
    get_cumulative_category,
    get_r_cumulative_group,
    is_r_cumulative_group_member,
)
from .cumulative_calculator import CumulativeCalculatorService
from .fault_responsibility_service import FaultResponsibilityService
from .assessment_standard_service import AssessmentStandardService
from .assessment_record_service import AssessmentRecordService
from .assessment_recalculator import AssessmentRecalculatorService
from .profile_date_updater import ProfileDateUpdaterService
from .monthly_reward_calculator import MonthlyRewardCalculatorService
from .annual_reset_service import AnnualResetService

__all__ = [
    # SystemSettingService
    "SystemSettingService",
    "SystemSettingServiceError",
    "DuplicateSettingError",
    "SettingNotFoundError",
    # CredentialValidator
    "CredentialValidator",
    "ValidationResult",
    "get_credential_validator",
    # GoogleCredentialValidator
    "GoogleCredentialValidator",
    "DryRunResult",
    # GoogleOAuthTokenService
    "GoogleOAuthTokenService",
    "GoogleOAuthTokenServiceError",
    "TokenNotFoundError",
    "EncryptionError",
    # Phase 12: 考核系統
    "R_CUMULATIVE_GROUP",
    "calculate_cumulative_multiplier",
    "calculate_next_cumulative_multiplier",
    "get_cumulative_category",
    "get_r_cumulative_group",
    "is_r_cumulative_group_member",
    "CumulativeCalculatorService",
    "FaultResponsibilityService",
    "AssessmentStandardService",
    "AssessmentRecordService",
    "AssessmentRecalculatorService",
    "ProfileDateUpdaterService",
    "MonthlyRewardCalculatorService",
    "AnnualResetService",
]
