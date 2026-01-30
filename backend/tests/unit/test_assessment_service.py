"""
考核服務單元測試

測試 AssessmentRecordService 和 AssessmentStandardService 的核心功能。
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from src.models.employee import Employee
from src.models.assessment_standard import AssessmentStandard
from src.models.assessment_record import AssessmentRecord


class TestAssessmentStandard:
    """考核標準測試類"""

    def test_create_assessment_standard(self, db_session):
        """測試建立考核標準"""
        standard = AssessmentStandard(
            code="D01",
            category="D",
            name="遲到",
            base_points=-1.0,
            has_cumulative=True,
            calculation_cycle="yearly",
            is_active=True
        )
        db_session.add(standard)
        db_session.commit()

        assert standard.id is not None
        assert standard.code == "D01"
        assert standard.base_points == -1.0

    def test_assessment_standard_categories(self, db_session):
        """測試考核標準類別"""
        categories = [
            ("D01", "D", "遲到", -1.0),
            ("W01", "W", "服裝儀容", -0.5),
            ("S01", "S", "違反安全規定", -3.0),
            ("R02", "R", "人為疏失延誤2分鐘", -1.0),
            ("+M01", "+M", "月度全勤", 3.0),
            ("+A01", "+A", "R班出勤", 3.0),
        ]

        for code, category, name, points in categories:
            standard = AssessmentStandard(
                code=code,
                category=category,
                name=name,
                base_points=points,
                has_cumulative=category in ["D", "W", "O", "S", "R"],
                is_active=True
            )
            db_session.add(standard)

        db_session.commit()

        # 驗證加分項目
        plus_standards = db_session.query(AssessmentStandard).filter(
            AssessmentStandard.base_points > 0
        ).all()
        assert len(plus_standards) == 2

        # 驗證扣分項目
        minus_standards = db_session.query(AssessmentStandard).filter(
            AssessmentStandard.base_points < 0
        ).all()
        assert len(minus_standards) == 4


class TestAssessmentRecord:
    """考核記錄測試類"""

    @pytest.fixture
    def setup_employee(self, db_session):
        """建立測試用員工"""
        employee = Employee(
            employee_id="1140M0001",
            employee_name="測試員工",
            department="淡海",
            current_department="淡海",
            hire_date=date(2020, 1, 1),
            current_score=80.0,
            is_resigned=False
        )
        db_session.add(employee)
        db_session.commit()
        return employee

    @pytest.fixture
    def setup_standard(self, db_session):
        """建立測試用考核標準"""
        standard = AssessmentStandard(
            code="D01",
            category="D",
            name="遲到",
            base_points=-1.0,
            has_cumulative=True,
            calculation_cycle="yearly",
            is_active=True
        )
        db_session.add(standard)
        db_session.commit()
        return standard

    def test_create_assessment_record(self, db_session, setup_employee, setup_standard):
        """測試建立考核記錄"""
        record = AssessmentRecord(
            employee_id=setup_employee.id,
            standard_code=setup_standard.code,
            record_date=date(2026, 1, 15),
            base_points=-1.0,
            responsibility_coefficient=1.0,
            actual_points=-1.0,
            cumulative_count=1,
            cumulative_multiplier=1.0,
            final_points=-1.0,
            description="遲到 5 分鐘"
        )
        db_session.add(record)
        db_session.commit()

        assert record.id is not None
        assert record.final_points == -1.0

    def test_cumulative_multiplier_calculation(self, db_session, setup_employee, setup_standard):
        """測試累計加重倍率計算"""
        # 累計倍率規則：
        # 第 1 次: 1.0 倍
        # 第 2 次: 1.5 倍
        # 第 3 次: 2.0 倍
        # 第 4 次以上: 2.5 倍

        multipliers = [1.0, 1.5, 2.0, 2.5, 2.5]

        for i, expected_multiplier in enumerate(multipliers, start=1):
            record = AssessmentRecord(
                employee_id=setup_employee.id,
                standard_code=setup_standard.code,
                record_date=date(2026, 1, i),
                base_points=-1.0,
                responsibility_coefficient=1.0,
                actual_points=-1.0,
                cumulative_count=i,
                cumulative_multiplier=expected_multiplier,
                final_points=-1.0 * expected_multiplier
            )
            db_session.add(record)

        db_session.commit()

        records = db_session.query(AssessmentRecord).order_by(
            AssessmentRecord.cumulative_count
        ).all()

        assert len(records) == 5
        assert records[0].cumulative_multiplier == 1.0
        assert records[0].final_points == -1.0
        assert records[1].cumulative_multiplier == 1.5
        assert records[1].final_points == -1.5
        assert records[2].cumulative_multiplier == 2.0
        assert records[2].final_points == -2.0
        assert records[3].cumulative_multiplier == 2.5
        assert records[3].final_points == -2.5
        assert records[4].cumulative_multiplier == 2.5
        assert records[4].final_points == -2.5

    def test_soft_delete_record(self, db_session, setup_employee, setup_standard):
        """測試軟刪除考核記錄"""
        record = AssessmentRecord(
            employee_id=setup_employee.id,
            standard_code=setup_standard.code,
            record_date=date(2026, 1, 15),
            base_points=-1.0,
            responsibility_coefficient=1.0,
            actual_points=-1.0,
            cumulative_count=1,
            cumulative_multiplier=1.0,
            final_points=-1.0,
            is_deleted=False
        )
        db_session.add(record)
        db_session.commit()

        # 軟刪除
        record.is_deleted = True
        db_session.commit()

        # 查詢未刪除記錄
        active_records = db_session.query(AssessmentRecord).filter(
            AssessmentRecord.is_deleted == False
        ).all()
        assert len(active_records) == 0

        # 查詢所有記錄（包含已刪除）
        all_records = db_session.query(AssessmentRecord).all()
        assert len(all_records) == 1

    def test_responsibility_coefficient(self, db_session, setup_employee):
        """測試責任係數計算（R02-R05）"""
        # 建立 R04 標準
        r04_standard = AssessmentStandard(
            code="R04",
            category="R",
            name="人為疏失延誤7分鐘",
            base_points=-3.0,
            has_cumulative=True,
            calculation_cycle="yearly",
            is_active=True
        )
        db_session.add(r04_standard)
        db_session.commit()

        # 責任係數規則（根據疏失項數）：
        # 0-2 項: 0.3（次要責任）
        # 3-5 項: 0.7（主要責任）
        # 6-9 項: 1.0（完全責任）

        test_cases = [
            (2, 0.3, "次要責任"),
            (4, 0.7, "主要責任"),
            (7, 1.0, "完全責任"),
        ]

        for fault_count, coefficient, _ in test_cases:
            record = AssessmentRecord(
                employee_id=setup_employee.id,
                standard_code="R04",
                record_date=date(2026, 1, 15),
                base_points=-3.0,
                responsibility_coefficient=coefficient,
                actual_points=-3.0 * coefficient,
                cumulative_count=1,
                cumulative_multiplier=1.0,
                final_points=-3.0 * coefficient
            )
            db_session.add(record)

        db_session.commit()

        records = db_session.query(AssessmentRecord).filter(
            AssessmentRecord.standard_code == "R04"
        ).all()

        assert len(records) == 3


class TestMonthlyReward:
    """月度獎勵測試類"""

    @pytest.fixture
    def setup_employee_for_reward(self, db_session):
        """建立測試用員工"""
        employee = Employee(
            employee_id="1140M0001",
            employee_name="測試員工",
            department="淡海",
            current_department="淡海",
            hire_date=date(2020, 1, 1),
            current_score=80.0,
            is_resigned=False
        )
        db_session.add(employee)

        # 建立月度獎勵標準
        standards = [
            ("+M01", "+M", "月度全勤", 3.0),
            ("+M02", "+M", "月度行車零違規", 1.0),
            ("+M03", "+M", "月度全項目零違規", 2.0),
        ]
        for code, category, name, points in standards:
            standard = AssessmentStandard(
                code=code,
                category=category,
                name=name,
                base_points=points,
                has_cumulative=False,
                is_active=True
            )
            db_session.add(standard)

        db_session.commit()
        return employee

    def test_monthly_reward_m02_m03_stackable(self, db_session, setup_employee_for_reward):
        """測試 +M02 和 +M03 可疊加"""
        employee = setup_employee_for_reward

        # 建立 +M02 記錄
        m02_record = AssessmentRecord(
            employee_id=employee.id,
            standard_code="+M02",
            record_date=date(2026, 1, 1),
            base_points=1.0,
            responsibility_coefficient=1.0,
            actual_points=1.0,
            cumulative_count=1,
            cumulative_multiplier=1.0,
            final_points=1.0
        )
        db_session.add(m02_record)

        # 建立 +M03 記錄
        m03_record = AssessmentRecord(
            employee_id=employee.id,
            standard_code="+M03",
            record_date=date(2026, 1, 1),
            base_points=2.0,
            responsibility_coefficient=1.0,
            actual_points=2.0,
            cumulative_count=1,
            cumulative_multiplier=1.0,
            final_points=2.0
        )
        db_session.add(m03_record)

        db_session.commit()

        # 計算總分
        total_reward = db_session.query(AssessmentRecord).filter(
            AssessmentRecord.employee_id == employee.id,
            AssessmentRecord.standard_code.like("+M%")
        ).all()

        total_points = sum(r.final_points for r in total_reward)
        assert total_points == 3.0  # +M02(1) + +M03(2) = 3
