"""
API 端點整合測試

測試 API 端點的完整流程，包含認證和權限。
"""

import pytest
from datetime import date


class TestHealthEndpoints:
    """健康檢查端點測試"""

    def test_health_check(self, client):
        """測試健康檢查端點"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_database(self, client):
        """測試資料庫健康檢查"""
        response = client.get("/health/database")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAuthEndpoints:
    """認證端點測試"""

    def test_login_success(self, client, admin_user):
        """測試登入成功"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin_test",
                "password": "admin123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "admin_test"

    def test_login_wrong_password(self, client, admin_user):
        """測試登入密碼錯誤"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin_test",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """測試登入不存在的使用者"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "notexist",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, admin_token):
        """測試取得當前使用者"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin_test"
        assert data["role"] == "admin"

    def test_get_current_user_without_token(self, client):
        """測試無 Token 存取受保護端點"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401


class TestEmployeeEndpoints:
    """員工 API 端點測試"""

    def test_list_employees_empty(self, client, admin_token):
        """測試列出空員工列表"""
        response = client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "employees" in data

    def test_create_employee(self, client, admin_token):
        """測試建立員工"""
        response = client.post(
            "/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "employee_id": "1140M0001",
                "employee_name": "測試員工",
                "department": "淡海",
                "hire_date": "2026-01-15"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["employee_id"] == "1140M0001"
        assert data["employee_name"] == "測試員工"

    def test_create_employee_without_auth(self, client):
        """測試無認證建立員工"""
        response = client.post(
            "/api/employees",
            json={
                "employee_id": "1140M0001",
                "employee_name": "測試員工",
                "department": "淡海",
                "hire_date": "2026-01-15"
            }
        )

        assert response.status_code == 401

    def test_get_employee_statistics(self, client, admin_token):
        """測試取得員工統計"""
        response = client.get(
            "/api/employees/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data or "active" in data


class TestUserEndpoints:
    """使用者 API 端點測試"""

    def test_list_users_as_admin(self, client, admin_token):
        """測試管理員列出使用者"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_list_users_as_staff(self, client, staff_token):
        """測試一般員工列出使用者（應被拒絕）"""
        response = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {staff_token}"}
        )

        # Staff 沒有權限查看使用者列表
        assert response.status_code == 403

    def test_create_user_as_admin(self, client, admin_token):
        """測試管理員建立使用者"""
        response = client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "newuser",
                "password": "password123",
                "role": "staff",
                "department": "淡海"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "staff"


class TestProfileEndpoints:
    """履歷 API 端點測試"""

    @pytest.fixture
    def setup_employee_for_profile(self, client, admin_token, db_session):
        """建立測試用員工"""
        from src.models.employee import Employee

        employee = Employee(
            employee_id="1140M0001",
            employee_name="測試員工",
            department="淡海",
            current_department="淡海",
            hire_date=date(2020, 1, 1),
            is_resigned=False
        )
        db_session.add(employee)
        db_session.commit()
        return employee

    def test_list_profiles_empty(self, client, admin_token):
        """測試列出空履歷列表"""
        response = client.get(
            "/api/profiles",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_profile(self, client, admin_token, setup_employee_for_profile):
        """測試建立履歷"""
        employee = setup_employee_for_profile

        response = client.post(
            "/api/profiles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "employee_id": employee.id,
                "event_date": "2026-01-15",
                "event_location": "淡海站",
                "train_number": "C301",
                "event_description": "測試事件描述"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["event_location"] == "淡海站"
        assert data["profile_type"] == "basic"

    def test_get_pending_profiles(self, client, admin_token):
        """測試取得未結案履歷"""
        response = client.get(
            "/api/profiles/pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_get_pending_statistics(self, client, admin_token):
        """測試取得未結案統計"""
        response = client.get(
            "/api/profiles/pending/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_pending" in data or "pending_count" in data


class TestAssessmentEndpoints:
    """考核 API 端點測試"""

    def test_list_assessment_standards(self, client, admin_token):
        """測試列出考核標準"""
        response = client.get(
            "/api/assessment-standards",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_list_assessment_records(self, client, admin_token):
        """測試列出考核記錄"""
        response = client.get(
            "/api/assessment-records",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_get_r_type_standards(self, client, admin_token):
        """測試取得需要責任判定的標準"""
        response = client.get(
            "/api/assessment-standards/r-type",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200


class TestScheduleEndpoints:
    """班表 API 端點測試"""

    def test_list_schedules(self, client, admin_token):
        """測試列出班表"""
        response = client.get(
            "/api/schedules",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

    def test_get_schedule_statistics(self, client, admin_token):
        """測試取得班表統計"""
        response = client.get(
            "/api/schedules/statistics",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"year": 2026, "month": 1}
        )

        assert response.status_code == 200


class TestDrivingCompetitionEndpoints:
    """駕駛競賽 API 端點測試"""

    def test_get_competition_ranking(self, client, admin_token):
        """測試取得競賽排名"""
        response = client.get(
            "/api/driving/competition",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"year": 2026, "quarter": 1}
        )

        assert response.status_code == 200

    def test_get_bonus_tiers(self, client, admin_token):
        """測試取得獎金階層"""
        response = client.get(
            "/api/driving/competition/bonus-tiers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
