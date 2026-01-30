"""
差勤加分處理服務
對應 tasks.md T199-T200: 實作差勤加分處理服務與複合情況處理

功能：
- 呼叫 Parser 取得班表數據
- 批次建立 +A 系列考核紀錄（R班、國定假日、延長工時）
- 彙整全勤名單
- 呼叫 Phase 12 MonthlyRewardCalculatorService 執行月度獎勵計算
- 處理複合情況（如 R/0905G(+2) 同時建立多筆記錄）
- 返回處理統計結果
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from sqlalchemy import and_, extract, select
from sqlalchemy.orm import Session

from src.models.assessment_record import AssessmentRecord
from src.models.employee import Employee
from src.services.attendance_sheet_parser import (
    AttendanceSheetParser,
    AttendanceParseResult,
    EmployeeAttendanceSummary,
    get_attendance_sheet_parser
)
from src.services.attendance_overtime_detector import (
    AttendanceOvertimeDetector
)
from src.services.monthly_reward_calculator import MonthlyRewardCalculatorService
from src.utils.logger import logger


@dataclass
class BonusRecordResult:
    """加分記錄建立結果"""
    standard_code: str
    employee_id: int
    employee_code: str
    employee_name: str
    record_date: date
    points: float
    description: str
    created: bool
    skipped_reason: Optional[str] = None


@dataclass
class AttendanceBonusResult:
    """差勤加分處理結果"""
    success: bool
    year: int
    month: int
    department: str

    # 統計
    total_employees: int = 0

    # +M 系列（月度獎勵）
    m01_count: int = 0  # 全勤
    m02_count: int = 0  # 行車零違規
    m03_count: int = 0  # 全項目零違規

    # +A 系列（差勤加分）
    a01_count: int = 0  # R班出勤
    a02_count: int = 0  # 國定假日出勤
    a03_count: int = 0  # 延長工時 1 小時
    a04_count: int = 0  # 延長工時 2 小時
    a05_count: int = 0  # 延長工時 3 小時
    a06_count: int = 0  # 延長工時 4 小時

    skipped_count: int = 0  # 跳過（已存在）

    # 詳細記錄
    records: List[BonusRecordResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AttendanceBonusProcessor:
    """
    差勤加分處理服務

    整合班表解析與考核記錄建立，自動處理差勤加分。
    """

    # +A 系列分數對照表
    A_SERIES_POINTS = {
        "+A01": 3.0,   # R班出勤
        "+A02": 1.0,   # 國定假日出勤
        "+A03": 0.5,   # 延長工時 1 小時
        "+A04": 1.0,   # 延長工時 2 小時
        "+A05": 1.5,   # 延長工時 3 小時
        "+A06": 2.0,   # 延長工時 4 小時
    }

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.parser = get_attendance_sheet_parser()
        self.monthly_calculator = MonthlyRewardCalculatorService(db)

    def _get_employee_by_code(self, employee_code: str) -> Optional[Employee]:
        """
        根據員工編號取得員工

        Args:
            employee_code: 員工編號（如 1011M0095）

        Returns:
            Employee 或 None
        """
        return self.db.execute(
            select(Employee).where(Employee.employee_id == employee_code)
        ).scalar_one_or_none()

    def _check_record_exists(
        self,
        employee_id: int,
        standard_code: str,
        record_date: date
    ) -> bool:
        """
        檢查考核記錄是否已存在

        Args:
            employee_id: 員工 ID
            standard_code: 考核代碼
            record_date: 記錄日期

        Returns:
            是否已存在
        """
        existing = self.db.execute(
            select(AssessmentRecord).where(
                and_(
                    AssessmentRecord.employee_id == employee_id,
                    AssessmentRecord.standard_code == standard_code,
                    AssessmentRecord.record_date == record_date,
                    AssessmentRecord.is_deleted == False
                )
            )
        ).scalar_one_or_none()

        return existing is not None

    def _create_assessment_record(
        self,
        employee: Employee,
        standard_code: str,
        record_date: date,
        description: str,
        points: float
    ) -> AssessmentRecord:
        """
        建立考核記錄

        Args:
            employee: 員工
            standard_code: 考核代碼
            record_date: 記錄日期
            description: 說明
            points: 分數

        Returns:
            建立的考核記錄
        """
        record = AssessmentRecord(
            employee_id=employee.id,
            standard_code=standard_code,
            record_date=record_date,
            description=description,
            base_points=points,
            responsibility_coefficient=1.0,
            actual_points=points,
            cumulative_multiplier=1.0,
            final_points=points
        )
        self.db.add(record)

        # 更新員工分數
        employee.current_score += points

        return record

    def _process_r_shift_records(
        self,
        summary: EmployeeAttendanceSummary,
        employee: Employee,
        result: AttendanceBonusResult
    ) -> None:
        """
        處理 R班出勤記錄（+A01、+A02）

        Args:
            summary: 員工出勤摘要
            employee: 員工
            result: 處理結果（會被修改）
        """
        for r_record in summary.r_shift_records:
            # +A01 R班出勤
            if self._check_record_exists(
                employee.id, "+A01", r_record.record_date
            ):
                result.records.append(BonusRecordResult(
                    standard_code="+A01",
                    employee_id=employee.id,
                    employee_code=summary.employee_id,
                    employee_name=summary.employee_name,
                    record_date=r_record.record_date,
                    points=self.A_SERIES_POINTS["+A01"],
                    description=f"R班出勤 {r_record.shift_code}",
                    created=False,
                    skipped_reason="已存在"
                ))
                result.skipped_count += 1
            else:
                self._create_assessment_record(
                    employee=employee,
                    standard_code="+A01",
                    record_date=r_record.record_date,
                    description=f"R班出勤 {r_record.shift_code}",
                    points=self.A_SERIES_POINTS["+A01"]
                )
                result.records.append(BonusRecordResult(
                    standard_code="+A01",
                    employee_id=employee.id,
                    employee_code=summary.employee_id,
                    employee_name=summary.employee_name,
                    record_date=r_record.record_date,
                    points=self.A_SERIES_POINTS["+A01"],
                    description=f"R班出勤 {r_record.shift_code}",
                    created=True
                ))
                result.a01_count += 1

            # +A02 國定假日出勤（如果是國定假日 R班）
            if r_record.is_national_holiday:
                if self._check_record_exists(
                    employee.id, "+A02", r_record.record_date
                ):
                    result.records.append(BonusRecordResult(
                        standard_code="+A02",
                        employee_id=employee.id,
                        employee_code=summary.employee_id,
                        employee_name=summary.employee_name,
                        record_date=r_record.record_date,
                        points=self.A_SERIES_POINTS["+A02"],
                        description=f"國定假日出勤 {r_record.shift_code}",
                        created=False,
                        skipped_reason="已存在"
                    ))
                    result.skipped_count += 1
                else:
                    self._create_assessment_record(
                        employee=employee,
                        standard_code="+A02",
                        record_date=r_record.record_date,
                        description=f"國定假日出勤 {r_record.shift_code}",
                        points=self.A_SERIES_POINTS["+A02"]
                    )
                    result.records.append(BonusRecordResult(
                        standard_code="+A02",
                        employee_id=employee.id,
                        employee_code=summary.employee_id,
                        employee_name=summary.employee_name,
                        record_date=r_record.record_date,
                        points=self.A_SERIES_POINTS["+A02"],
                        description=f"國定假日出勤 {r_record.shift_code}",
                        created=True
                    ))
                    result.a02_count += 1

    def _process_overtime_records(
        self,
        summary: EmployeeAttendanceSummary,
        employee: Employee,
        result: AttendanceBonusResult
    ) -> None:
        """
        處理延長工時記錄（+A03~+A06）

        Args:
            summary: 員工出勤摘要
            employee: 員工
            result: 處理結果（會被修改）
        """
        for ot_record in summary.overtime_records:
            standard_code = AttendanceOvertimeDetector.get_assessment_code(
                ot_record.overtime_hours
            )
            points = AttendanceOvertimeDetector.get_assessment_points(
                ot_record.overtime_hours
            )

            if self._check_record_exists(
                employee.id, standard_code, ot_record.record_date
            ):
                result.records.append(BonusRecordResult(
                    standard_code=standard_code,
                    employee_id=employee.id,
                    employee_code=summary.employee_id,
                    employee_name=summary.employee_name,
                    record_date=ot_record.record_date,
                    points=points,
                    description=f"延長工時 {ot_record.overtime_hours} 小時 {ot_record.shift_code}",
                    created=False,
                    skipped_reason="已存在"
                ))
                result.skipped_count += 1
            else:
                self._create_assessment_record(
                    employee=employee,
                    standard_code=standard_code,
                    record_date=ot_record.record_date,
                    description=f"延長工時 {ot_record.overtime_hours} 小時 {ot_record.shift_code}",
                    points=points
                )
                result.records.append(BonusRecordResult(
                    standard_code=standard_code,
                    employee_id=employee.id,
                    employee_code=summary.employee_id,
                    employee_name=summary.employee_name,
                    record_date=ot_record.record_date,
                    points=points,
                    description=f"延長工時 {ot_record.overtime_hours} 小時 {ot_record.shift_code}",
                    created=True
                ))

                # 更新統計
                if standard_code == "+A03":
                    result.a03_count += 1
                elif standard_code == "+A04":
                    result.a04_count += 1
                elif standard_code == "+A05":
                    result.a05_count += 1
                elif standard_code == "+A06":
                    result.a06_count += 1

    def process(
        self,
        sheet_data: List[List[Any]],
        department: str,
        year: int,
        month: int,
        dry_run: bool = False
    ) -> AttendanceBonusResult:
        """
        執行差勤加分處理

        Args:
            sheet_data: Google Sheets 班表原始資料
            department: 部門
            year: 年份
            month: 月份
            dry_run: 預覽模式（不實際寫入）

        Returns:
            AttendanceBonusResult: 處理結果
        """
        result = AttendanceBonusResult(
            success=False,
            year=year,
            month=month,
            department=department
        )

        logger.info(
            "開始差勤加分處理",
            department=department,
            year=year,
            month=month,
            dry_run=dry_run
        )

        # 1. 解析班表
        parse_result = self.parser.parse(sheet_data, department, year, month)

        if not parse_result.success:
            result.errors.extend(parse_result.errors)
            result.warnings.extend(parse_result.warnings)
            return result

        result.total_employees = parse_result.total_employees
        result.warnings.extend(parse_result.warnings)

        # 2. 處理每位員工
        full_attendance_map: Dict[int, bool] = {}

        for summary in parse_result.employees:
            # 取得員工資料
            employee = self._get_employee_by_code(summary.employee_id)
            if not employee:
                result.warnings.append(
                    f"找不到員工：{summary.employee_id} ({summary.employee_name})"
                )
                continue

            # 記錄全勤狀態
            full_attendance_map[employee.id] = summary.is_full_attendance

            if dry_run:
                # 預覽模式：只統計不建立記錄
                if summary.is_full_attendance:
                    result.m01_count += 1
                result.a01_count += len(summary.r_shift_records)
                result.a02_count += sum(
                    1 for r in summary.r_shift_records if r.is_national_holiday
                )
                for ot in summary.overtime_records:
                    code = AttendanceOvertimeDetector.get_assessment_code(
                        ot.overtime_hours
                    )
                    if code == "+A03":
                        result.a03_count += 1
                    elif code == "+A04":
                        result.a04_count += 1
                    elif code == "+A05":
                        result.a05_count += 1
                    elif code == "+A06":
                        result.a06_count += 1
            else:
                # 正式處理：建立 +A 系列記錄
                self._process_r_shift_records(summary, employee, result)
                self._process_overtime_records(summary, employee, result)

        # 3. 呼叫 Phase 12 月度獎勵計算
        if not dry_run:
            for emp_id, is_full in full_attendance_map.items():
                try:
                    reward = self.monthly_calculator.calculate_employee_month(
                        employee_id=emp_id,
                        year=year,
                        month=month,
                        include_full_attendance=is_full
                    )
                    if reward:
                        if reward.full_attendance:
                            result.m01_count += 1
                        if reward.driving_zero_violation:
                            result.m02_count += 1
                        if reward.all_zero_violation:
                            result.m03_count += 1
                except Exception as e:
                    result.warnings.append(
                        f"月度獎勵計算失敗（員工 {emp_id}）：{str(e)}"
                    )

            # 提交事務
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                result.errors.append(f"資料庫提交失敗：{str(e)}")
                return result
        else:
            # 預覽模式：計算 +M02/+M03 預估數量
            for emp_id, is_full in full_attendance_map.items():
                preview = self.monthly_calculator.preview_month_calculation(
                    year=year, month=month
                )
                for p in preview.get("preview", []):
                    if p.get("driving_zero_violation"):
                        result.m02_count += 1
                    if p.get("all_zero_violation"):
                        result.m03_count += 1
                break  # 預覽只需執行一次

        result.success = True

        logger.info(
            "差勤加分處理完成",
            department=department,
            year=year,
            month=month,
            m01_count=result.m01_count,
            m02_count=result.m02_count,
            m03_count=result.m03_count,
            a01_count=result.a01_count,
            a02_count=result.a02_count,
            a03_count=result.a03_count,
            a04_count=result.a04_count,
            a05_count=result.a05_count,
            a06_count=result.a06_count,
            skipped_count=result.skipped_count
        )

        return result

    def preview(
        self,
        sheet_data: List[List[Any]],
        department: str,
        year: int,
        month: int
    ) -> AttendanceBonusResult:
        """
        預覽差勤加分處理（不實際寫入）

        Args:
            sheet_data: Google Sheets 班表原始資料
            department: 部門
            year: 年份
            month: 月份

        Returns:
            AttendanceBonusResult: 預覽結果
        """
        return self.process(sheet_data, department, year, month, dry_run=True)
