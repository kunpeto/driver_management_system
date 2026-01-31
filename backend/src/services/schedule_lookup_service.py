"""
ScheduleLookupService 班表查詢服務
對應 tasks.md T136: 實作班表查詢服務
對應 spec.md: User Story 8 - 班表查詢（人員訪談自動帶入）

Gemini Review 2026-01-30 優化：
- 優先查詢本地 schedules 表
- 僅在必要時（距今 < 7 天且本地無資料）才呼叫 Google Sheets API
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.models import Department, Employee
from src.models.schedule import Schedule


class ScheduleLookupError(Exception):
    """班表查詢錯誤"""
    pass


class EmployeeNotFoundError(ScheduleLookupError):
    """員工不存在錯誤"""
    pass


class ScheduleResult:
    """班表查詢結果"""

    def __init__(
        self,
        shift_before_2days: Optional[str] = None,
        shift_before_1day: Optional[str] = None,
        shift_event_day: Optional[str] = None,
        source: str = "local"
    ):
        self.shift_before_2days = shift_before_2days
        self.shift_before_1day = shift_before_1day
        self.shift_event_day = shift_event_day
        self.source = source  # "local" 或 "google_api"

    def to_dict(self) -> dict:
        return {
            "shift_before_2days": self.shift_before_2days,
            "shift_before_1day": self.shift_before_1day,
            "shift_event_day": self.shift_event_day,
            "source": self.source,
        }


class ScheduleLookupService:
    """
    班表查詢服務

    提供員工班表查詢功能，優先使用本地資料庫。
    """

    # 查詢本地資料的最大天數差距（超過此天數不呼叫 API）
    MAX_DAYS_FOR_API_SYNC = 7

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db

    def lookup_shifts(
        self,
        employee_id: int,
        event_date: date,
        force_api: bool = False
    ) -> ScheduleResult:
        """
        查詢員工班表（事件當天及前兩天）

        Gemini Review 優化邏輯：
        1. 優先查詢本地 schedules 表
        2. 若本地無資料且距今 < 7 天，才呼叫 Google Sheets API
        3. 查詢結果同步回本地

        Args:
            employee_id: 員工 ID
            event_date: 事件日期
            force_api: 是否強制使用 API（忽略本地資料）

        Returns:
            ScheduleResult: 班表查詢結果
        """
        # 驗證員工存在
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {employee_id} 不存在")

        # 計算查詢日期
        dates = [
            event_date - timedelta(days=2),  # 前2天
            event_date - timedelta(days=1),  # 前1天
            event_date,                       # 當天
        ]

        # 嘗試從本地資料庫查詢
        if not force_api:
            result = self._lookup_from_local(employee, dates)
            if result:
                return result

        # 檢查是否應該呼叫 API
        if self._should_call_api(event_date):
            result = self._lookup_from_api(employee, dates)
            if result:
                return result

        # 返回空結果
        return ScheduleResult(source="local")

    def _lookup_from_local(
        self,
        employee: Employee,
        dates: list[date]
    ) -> Optional[ScheduleResult]:
        """
        從本地資料庫查詢班表

        Args:
            employee: 員工
            dates: 查詢日期列表 [前2天, 前1天, 當天]

        Returns:
            ScheduleResult 或 None（無資料）
        """
        shifts = []

        for query_date in dates:
            schedule = self.db.query(Schedule).filter(
                and_(
                    Schedule.employee_id == employee.employee_id,
                    Schedule.department == employee.current_department,
                    Schedule.schedule_date == query_date,
                )
            ).first()

            if schedule:
                shifts.append(schedule.shift_code)
            else:
                shifts.append(None)

        # 如果至少有一個班別資料，返回結果
        if any(shifts):
            return ScheduleResult(
                shift_before_2days=shifts[0],
                shift_before_1day=shifts[1],
                shift_event_day=shifts[2],
                source="local"
            )

        return None

    def _should_call_api(self, event_date: date) -> bool:
        """
        判斷是否應該呼叫 Google Sheets API

        條件：事件日期距今不超過 7 天

        Args:
            event_date: 事件日期

        Returns:
            是否應該呼叫 API
        """
        days_diff = (date.today() - event_date).days
        return days_diff <= self.MAX_DAYS_FOR_API_SYNC

    def _lookup_from_api(
        self,
        employee: Employee,
        dates: list[date]
    ) -> Optional[ScheduleResult]:
        """
        從 Google Sheets API 查詢班表並同步回本地

        Args:
            employee: 員工
            dates: 查詢日期列表

        Returns:
            ScheduleResult 或 None
        """
        # TODO: 整合 Google Sheets 班表讀取服務
        # 這裡需要呼叫 schedule_sync_service 來同步資料
        # 目前先返回 None，等待整合時實作

        # 嘗試觸發同步
        try:
            from src.services.schedule_sync_service import ScheduleSyncService

            sync_service = ScheduleSyncService(self.db)

            # 取得員工所屬部門的月份資料
            for query_date in dates:
                year_month = query_date.strftime("%Y-%m")
                # 同步該月份資料（如果尚未同步）
                # sync_service.sync_month(employee.current_department, year_month)

            # 同步後再次查詢本地
            result = self._lookup_from_local(employee, dates)
            if result:
                result.source = "google_api"
                return result

        except ImportError:
            # schedule_sync_service 不存在時忽略
            pass
        except Exception:
            # API 呼叫失敗時忽略，返回 None
            pass

        return None

    def get_shift_by_date(
        self,
        employee_id: int,
        query_date: date
    ) -> Optional[str]:
        """
        查詢員工單一日期的班別

        Args:
            employee_id: 員工 ID
            query_date: 查詢日期

        Returns:
            班別代碼或 None
        """
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {employee_id} 不存在")

        schedule = self.db.query(Schedule).filter(
            and_(
                Schedule.employee_id == employee.employee_id,
                Schedule.department == employee.current_department,
                Schedule.schedule_date == query_date,
            )
        ).first()

        return schedule.shift_code if schedule else None

    def batch_lookup(
        self,
        employee_ids: list[int],
        event_date: date
    ) -> dict[int, ScheduleResult]:
        """
        批次查詢多位員工的班表

        Args:
            employee_ids: 員工 ID 列表
            event_date: 事件日期

        Returns:
            員工 ID -> ScheduleResult 的對應
        """
        results = {}

        for emp_id in employee_ids:
            try:
                results[emp_id] = self.lookup_shifts(emp_id, event_date)
            except EmployeeNotFoundError:
                results[emp_id] = ScheduleResult()

        return results
