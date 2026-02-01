"""
DutySyncService 勤務表同步服務
對應 tasks.md T106: 實作勤務表同步服務

提供從 Google Sheets 勤務表讀取資料、計算駕駛時數的功能。
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.models.employee import Employee
from src.constants import Department
from src.models.schedule import Schedule
from src.services.driving_stats_calculator import DrivingStatsCalculator
from src.services.route_standard_time_service import RouteStandardTimeService


class DutySyncServiceError(Exception):
    """勤務表同步服務錯誤"""
    pass


class DutySyncService:
    """
    勤務表同步服務

    從 Google Sheets 勤務表讀取資料，計算駕駛時數並寫入 driving_daily_stats。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.stats_calculator = DrivingStatsCalculator(db)
        self.route_service = RouteStandardTimeService(db)

    # ============================================================
    # 同步作業
    # ============================================================

    def sync_daily_stats_for_date(
        self,
        department: str,
        target_date: date
    ) -> dict:
        """
        同步指定部門指定日期的駕駛時數

        從 schedules 表讀取班表資料，查詢 route_standard_times 取得分鐘數，
        計算每位員工的駕駛時數並寫入 driving_daily_stats。

        Args:
            department: 部門
            target_date: 目標日期

        Returns:
            dict: 同步結果統計
        """
        # 取得勤務代碼到分鐘數的映射
        route_minutes_map = self.route_service.get_minutes_map(department)

        # 查詢該部門該日期的所有班表
        schedules = self.db.query(Schedule).join(
            Employee, Schedule.employee_id == Employee.id
        ).filter(
            and_(
                Employee.current_department == department,
                Schedule.schedule_date == target_date,
                Employee.is_resigned == False
            )
        ).all()

        processed = 0
        skipped = 0
        errors = []

        for schedule in schedules:
            try:
                # 計算駕駛分鐘數
                total_minutes, is_holiday_work = self.stats_calculator.calculate_daily_minutes(
                    employee_id=schedule.employee_id,
                    record_date=target_date,
                    route_minutes_map=route_minutes_map
                )

                # 儲存統計資料
                self.stats_calculator.save_daily_stats(
                    employee_id=schedule.employee_id,
                    department=department,
                    record_date=target_date,
                    total_minutes=total_minutes,
                    is_holiday_work=is_holiday_work,
                    incident_count=0  # 責任事件待 US8 整合
                )
                processed += 1

            except Exception as e:
                errors.append(f"員工 {schedule.employee_id}: {str(e)}")

        return {
            "department": department,
            "date": target_date.isoformat(),
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "route_count": len(route_minutes_map)
        }

    def sync_daily_stats_for_date_range(
        self,
        department: str,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        同步指定部門指定日期範圍的駕駛時數

        Args:
            department: 部門
            start_date: 起始日期
            end_date: 結束日期

        Returns:
            dict: 同步結果統計
        """
        total_processed = 0
        total_skipped = 0
        all_errors = []
        days_processed = 0

        current_date = start_date
        while current_date <= end_date:
            result = self.sync_daily_stats_for_date(department, current_date)
            total_processed += result["processed"]
            total_skipped += result["skipped"]
            all_errors.extend(result["errors"])
            days_processed += 1
            current_date += timedelta(days=1)  # 使用 timedelta 正確遞增日期

        return {
            "department": department,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days_processed": days_processed,
            "total_processed": total_processed,
            "total_skipped": total_skipped,
            "errors": all_errors
        }

    def sync_all_departments_for_date(self, target_date: date) -> dict:
        """
        同步所有部門指定日期的駕駛時數

        Args:
            target_date: 目標日期

        Returns:
            dict: 同步結果統計
        """
        results = {}

        for dept in [Department.DANHAI.value, Department.ANKENG.value]:
            results[dept] = self.sync_daily_stats_for_date(dept, target_date)

        return {
            "date": target_date.isoformat(),
            "departments": results,
            "total_processed": sum(r["processed"] for r in results.values()),
            "total_errors": sum(len(r["errors"]) for r in results.values())
        }

    # ============================================================
    # 查詢輔助
    # ============================================================

    def get_unprocessed_dates(
        self,
        department: str,
        start_date: date,
        end_date: date
    ) -> list[date]:
        """
        取得尚未處理的日期列表

        Args:
            department: 部門
            start_date: 起始日期
            end_date: 結束日期

        Returns:
            list[date]: 尚未處理的日期列表
        """
        from src.models.driving_daily_stats import DrivingDailyStats

        # 查詢已處理的日期
        processed_dates = set(
            row.record_date for row in
            self.db.query(DrivingDailyStats.record_date).filter(
                and_(
                    DrivingDailyStats.department == department,
                    DrivingDailyStats.record_date >= start_date,
                    DrivingDailyStats.record_date <= end_date
                )
            ).distinct().all()
        )

        # 計算所有日期
        all_dates = []
        current = start_date
        while current <= end_date:
            all_dates.append(current)
            current += timedelta(days=1)

        # 返回未處理的日期
        return [d for d in all_dates if d not in processed_dates]

    def get_sync_status(self, department: str, year: int, month: int) -> dict:
        """
        取得指定月份的同步狀態

        Args:
            department: 部門
            year: 年份
            month: 月份

        Returns:
            dict: 同步狀態
        """
        from src.models.driving_daily_stats import DrivingDailyStats

        # 計算月份日期範圍
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # 計算總天數
        total_days = (end_date - start_date).days + 1

        # 查詢已處理天數
        processed_days = self.db.query(DrivingDailyStats.record_date).filter(
            and_(
                DrivingDailyStats.department == department,
                DrivingDailyStats.record_date >= start_date,
                DrivingDailyStats.record_date <= end_date
            )
        ).distinct().count()

        return {
            "department": department,
            "year": year,
            "month": month,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days": total_days,
            "processed_days": processed_days,
            "pending_days": total_days - processed_days,
            "progress_percent": round(processed_days / total_days * 100, 1) if total_days > 0 else 0
        }
