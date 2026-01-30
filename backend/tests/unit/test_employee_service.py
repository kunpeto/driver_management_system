"""
員工服務單元測試

測試 EmployeeService 的核心功能。
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from src.services.employee_service import EmployeeService
from src.models.employee import Employee


class TestEmployeeService:
    """員工服務測試類"""

    def test_get_all_employees_empty(self, db_session):
        """測試空資料庫時取得員工列表"""
        service = EmployeeService(db_session)
        result = service.get_all()

        assert result == []

    def test_create_employee(self, db_session):
        """測試建立員工"""
        service = EmployeeService(db_session)

        employee = service.create(
            employee_id="1140M0001",
            employee_name="測試員工",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )

        assert employee is not None
        assert employee.employee_id == "1140M0001"
        assert employee.employee_name == "測試員工"
        assert employee.department == "淡海"
        assert employee.current_department == "淡海"
        assert employee.is_resigned is False

    def test_create_duplicate_employee_id(self, db_session):
        """測試建立重複員工編號"""
        service = EmployeeService(db_session)

        # 建立第一個員工
        service.create(
            employee_id="1140M0001",
            employee_name="員工一",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )

        # 嘗試建立重複編號
        with pytest.raises(Exception):
            service.create(
                employee_id="1140M0001",
                employee_name="員工二",
                department="安坑",
                hire_date=date(2026, 1, 16)
            )

    def test_get_employee_by_id(self, db_session):
        """測試根據 ID 取得員工"""
        service = EmployeeService(db_session)

        # 建立員工
        created = service.create(
            employee_id="1140M0001",
            employee_name="測試員工",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )

        # 取得員工
        employee = service.get_by_id(created.id)

        assert employee is not None
        assert employee.id == created.id
        assert employee.employee_id == "1140M0001"

    def test_get_employee_by_employee_id(self, db_session):
        """測試根據員工編號取得員工"""
        service = EmployeeService(db_session)

        # 建立員工
        service.create(
            employee_id="1140M0001",
            employee_name="測試員工",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )

        # 根據員工編號取得
        employee = service.get_by_employee_id("1140M0001")

        assert employee is not None
        assert employee.employee_id == "1140M0001"

    def test_get_nonexistent_employee(self, db_session):
        """測試取得不存在的員工"""
        service = EmployeeService(db_session)

        employee = service.get_by_id(99999)
        assert employee is None

        employee = service.get_by_employee_id("NOTEXIST")
        assert employee is None

    def test_update_employee(self, db_session):
        """測試更新員工資料"""
        service = EmployeeService(db_session)

        # 建立員工
        created = service.create(
            employee_id="1140M0001",
            employee_name="原始姓名",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )

        # 更新員工
        updated = service.update(
            employee_id=created.id,
            employee_name="更新姓名"
        )

        assert updated is not None
        assert updated.employee_name == "更新姓名"

    def test_resign_employee(self, db_session):
        """測試員工離職"""
        service = EmployeeService(db_session)

        # 建立員工
        created = service.create(
            employee_id="1140M0001",
            employee_name="測試員工",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )

        assert created.is_resigned is False

        # 標記離職
        resigned = service.resign(created.id)

        assert resigned is not None
        assert resigned.is_resigned is True

    def test_activate_employee(self, db_session):
        """測試員工復職"""
        service = EmployeeService(db_session)

        # 建立並離職
        created = service.create(
            employee_id="1140M0001",
            employee_name="測試員工",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )
        service.resign(created.id)

        # 復職
        activated = service.activate(created.id)

        assert activated is not None
        assert activated.is_resigned is False

    def test_get_by_department(self, db_session):
        """測試根據部門取得員工"""
        service = EmployeeService(db_session)

        # 建立多個員工
        service.create(
            employee_id="1140M0001",
            employee_name="淡海員工1",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )
        service.create(
            employee_id="1140M0002",
            employee_name="淡海員工2",
            department="淡海",
            hire_date=date(2026, 1, 16)
        )
        service.create(
            employee_id="1140M0003",
            employee_name="安坑員工1",
            department="安坑",
            hire_date=date(2026, 1, 17)
        )

        # 取得淡海員工
        tanhai_employees = service.get_by_department("淡海")
        assert len(tanhai_employees) == 2

        # 取得安坑員工
        ankeng_employees = service.get_by_department("安坑")
        assert len(ankeng_employees) == 1

    def test_search_employees(self, db_session):
        """測試搜尋員工"""
        service = EmployeeService(db_session)

        # 建立員工
        service.create(
            employee_id="1140M0001",
            employee_name="張三",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )
        service.create(
            employee_id="1140M0002",
            employee_name="李四",
            department="淡海",
            hire_date=date(2026, 1, 16)
        )

        # 搜尋姓名
        results = service.search("張")
        assert len(results) == 1
        assert results[0].employee_name == "張三"

        # 搜尋員工編號
        results = service.search("1140M0002")
        assert len(results) == 1
        assert results[0].employee_name == "李四"

    def test_get_statistics(self, db_session):
        """測試取得員工統計"""
        service = EmployeeService(db_session)

        # 建立員工
        emp1 = service.create(
            employee_id="1140M0001",
            employee_name="在職員工",
            department="淡海",
            hire_date=date(2026, 1, 15)
        )
        emp2 = service.create(
            employee_id="1140M0002",
            employee_name="離職員工",
            department="淡海",
            hire_date=date(2026, 1, 16)
        )
        service.resign(emp2.id)

        service.create(
            employee_id="1140M0003",
            employee_name="安坑員工",
            department="安坑",
            hire_date=date(2026, 1, 17)
        )

        # 取得統計
        stats = service.get_statistics()

        assert stats["total"] == 3
        assert stats["active"] == 2
        assert stats["resigned"] == 1
        assert stats["by_department"]["淡海"] == 2
        assert stats["by_department"]["安坑"] == 1
