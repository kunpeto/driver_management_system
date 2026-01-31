"""
ProfileService 單元測試
對應 Gemini Review 建議：補充類型轉換與版本號遞增的邊界測試
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from src.models import Profile, ProfileType, ConversionStatus
from src.services.profile_service import (
    ProfileService,
    ProfileNotFoundError,
    InvalidConversionError,
    EmployeeNotFoundError,
)


class TestProfileServiceConversion:
    """類型轉換測試"""

    def test_convert_from_basic_success(self):
        """測試：基本履歷成功轉換"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.profile_type = ProfileType.BASIC.value
        mock_profile.conversion_status = ConversionStatus.PENDING.value
        mock_profile.event_investigation = None
        mock_profile.personnel_interview = None
        mock_profile.corrective_measures = None
        mock_profile.assessment_notice = None

        with patch.object(service, 'get_by_id', return_value=mock_profile):
            # Act
            result = service.convert_type(1, ProfileType.EVENT_INVESTIGATION.value, {})

            # Assert
            assert mock_profile.profile_type == ProfileType.EVENT_INVESTIGATION.value
            assert mock_profile.conversion_status == ConversionStatus.CONVERTED.value
            mock_db.commit.assert_called()

    def test_convert_from_non_basic_fails(self):
        """測試：非基本履歷無法轉換"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.profile_type = ProfileType.EVENT_INVESTIGATION.value
        mock_profile.conversion_status = ConversionStatus.CONVERTED.value

        with patch.object(service, 'get_by_id', return_value=mock_profile):
            # Act & Assert
            with pytest.raises(InvalidConversionError) as exc_info:
                service.convert_type(1, ProfileType.PERSONNEL_INTERVIEW.value, {})

            assert "僅允許基本履歷轉換" in str(exc_info.value)

    def test_convert_completed_profile_fails(self):
        """測試：已完成履歷無法轉換"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.profile_type = ProfileType.BASIC.value
        mock_profile.conversion_status = ConversionStatus.COMPLETED.value

        with patch.object(service, 'get_by_id', return_value=mock_profile):
            # Act & Assert
            with pytest.raises(InvalidConversionError) as exc_info:
                service.convert_type(1, ProfileType.EVENT_INVESTIGATION.value, {})

            assert "已完成的履歷不可轉換" in str(exc_info.value)

    def test_convert_to_basic_fails(self):
        """測試：無法轉換為基本履歷"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.profile_type = ProfileType.BASIC.value
        mock_profile.conversion_status = ConversionStatus.PENDING.value

        with patch.object(service, 'get_by_id', return_value=mock_profile):
            # Act & Assert
            with pytest.raises(InvalidConversionError) as exc_info:
                service.convert_type(1, ProfileType.BASIC.value, {})

            assert "不可轉換為基本履歷" in str(exc_info.value)


class TestProfileServiceReset:
    """重置功能測試（Gemini Review P1）"""

    def test_reset_converted_profile_success(self):
        """測試：成功重置已轉換的履歷"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.profile_type = ProfileType.EVENT_INVESTIGATION.value
        mock_profile.conversion_status = ConversionStatus.CONVERTED.value
        mock_profile.event_investigation = MagicMock()
        mock_profile.personnel_interview = None
        mock_profile.corrective_measures = None
        mock_profile.assessment_notice = None

        with patch.object(service, 'get_by_id', return_value=mock_profile):
            # Act
            result = service.reset_to_basic(1)

            # Assert
            assert mock_profile.profile_type == ProfileType.BASIC.value
            assert mock_profile.conversion_status == ConversionStatus.PENDING.value
            mock_db.delete.assert_called()
            mock_db.commit.assert_called()

    def test_reset_completed_profile_fails(self):
        """測試：已完成履歷無法重置"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.profile_type = ProfileType.EVENT_INVESTIGATION.value
        mock_profile.conversion_status = ConversionStatus.COMPLETED.value

        with patch.object(service, 'get_by_id', return_value=mock_profile):
            # Act & Assert
            with pytest.raises(InvalidConversionError) as exc_info:
                service.reset_to_basic(1)

            assert "已完成的履歷不可重置" in str(exc_info.value)

    def test_reset_basic_profile_fails(self):
        """測試：基本履歷不需要重置"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.profile_type = ProfileType.BASIC.value
        mock_profile.conversion_status = ConversionStatus.PENDING.value

        with patch.object(service, 'get_by_id', return_value=mock_profile):
            # Act & Assert
            with pytest.raises(InvalidConversionError) as exc_info:
                service.reset_to_basic(1)

            assert "基本履歷不需要重置" in str(exc_info.value)


class TestProfileServiceVersion:
    """版本號遞增測試"""

    def test_increment_version_success(self):
        """測試：成功遞增版本號"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        mock_profile = MagicMock(spec=Profile)
        mock_profile.id = 1
        mock_profile.document_version = 1
        mock_profile.increment_version.return_value = 2

        with patch.object(service, 'get_by_id', return_value=mock_profile):
            # Act
            new_version = service.increment_document_version(1)

            # Assert
            assert new_version == 2
            mock_profile.increment_version.assert_called_once()
            mock_db.commit.assert_called()

    def test_increment_version_not_found(self):
        """測試：履歷不存在時拋出異常"""
        # Arrange
        mock_db = MagicMock()
        service = ProfileService(mock_db)

        with patch.object(service, 'get_by_id', return_value=None):
            # Act & Assert
            with pytest.raises(ProfileNotFoundError):
                service.increment_document_version(999)


class TestProfilePolicy:
    """權限策略測試（Gemini Review P2）"""

    def test_can_view_admin_all_departments(self):
        """測試：Admin 可查看所有部門"""
        from src.services.profile_policy import ProfilePolicy
        from src.middleware.permission import Role

        mock_profile = MagicMock()
        mock_profile.department = "安坑"

        result = ProfilePolicy.can_view(Role.ADMIN.value, "淡海", mock_profile)

        assert result is True

    def test_can_view_staff_own_department_only(self):
        """測試：Staff 只能查看自己部門"""
        from src.services.profile_policy import ProfilePolicy
        from src.middleware.permission import Role

        mock_profile = MagicMock()
        mock_profile.department = "安坑"

        # 不同部門
        result = ProfilePolicy.can_view(Role.STAFF.value, "淡海", mock_profile)
        assert result is False

        # 相同部門
        result = ProfilePolicy.can_view(Role.STAFF.value, "安坑", mock_profile)
        assert result is True

    def test_filter_department_staff(self):
        """測試：Staff 的部門篩選被強制為自己部門"""
        from src.services.profile_policy import ProfilePolicy
        from src.middleware.permission import Role

        # Staff 請求其他部門，應被強制為自己部門
        result = ProfilePolicy.filter_department(Role.STAFF.value, "淡海", "安坑")
        assert result == "淡海"

        # Admin 請求其他部門，不受限制
        result = ProfilePolicy.filter_department(Role.ADMIN.value, "淡海", "安坑")
        assert result == "安坑"
