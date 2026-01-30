"""
DrivingStatsCalculator 駕駛時數計算服務
對應 tasks.md T107: 實作駕駛時數計算服務

提供每日時數彙總、R班判定、責任事件統計、季度累計等功能。
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.models.assessment_record import AssessmentRecord
from src.models.assessment_standard import AssessmentStandard
from src.models.driving_daily_stats import DrivingDailyStats
from src.models.employee import Employee
from src.models.google_oauth_token import Department
from src.models.schedule import Schedule


class DrivingStatsCalculatorError(Exception):
    """駕駛時數計算服務錯誤"""
    pass


class DrivingStatsCalculator:
    """
    駕駛時數計算服務

    提供駕駛時數的計算與統計功能。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db

    # ============================================================
    # R班判定
    # ============================================================

    def is_holiday_work(self, shift_type: str) -> bool:
        """
        判斷是否為 R班出勤

        R班出勤判定條件：
        - shift_type 開頭為 "R/"
        - shift_type 開頭為 "R("
        - shift_type 包含 "R班"

        範例：
        - "R/0905G" → True
        - "R(國)/1425G" → True
        - "0905G" → False
        - "休" → False

        Args:
            shift_type: 班別類型

        Returns:
            bool: 是否為 R班出勤
        """
        if not shift_type:
            return False

        shift_upper = shift_type.strip().upper()

        # R班開頭的格式
        if shift_upper.startswith("R/") or shift_upper.startswith("R("):
            return True

        # 包含 R班 字樣
        if "R班" in shift_type:
            return True

        return False

    # ============================================================
    # 責任事件統計（已整合 Phase 12 考核系統）
    # ============================================================

    def count_incidents_for_date(
        self,
        employee_id: int,
        record_date: date
    ) -> int:
        """
        統計員工指定日期的責任事件次數

        責任事件定義：S類別（行車運轉）+ R類別（故障排除）扣分項目
        資料來源：assessment_records 表（Phase 12 考核系統）

        Args:
            employee_id: 員工 ID
            record_date: 日期

        Returns:
            int: 責任事件次數
        """
        # 查詢該日期的責任事件（S類或R類且有實際扣分）
        count = self.db.query(func.count(AssessmentRecord.id)).join(
            AssessmentStandard,
            AssessmentRecord.standard_code == AssessmentStandard.code
        ).filter(
            and_(
                AssessmentRecord.employee_id == employee_id,
                AssessmentRecord.record_date == record_date,
                AssessmentRecord.is_deleted == False,
                AssessmentRecord.final_points < 0,  # 負分才算責任事件
                AssessmentStandard.category.in_(['S', 'R'])  # S類或R類
            )
        ).scalar()

        return count or 0

    def count_incidents_for_quarter(
        self,
        employee_id: int,
        year: int,
        quarter: int
    ) -> int:
        """
        統計員工指定季度的責任事件次數

        責任事件定義：S類別（行車運轉）+ R類別（故障排除）扣分項目
        資料來源：assessment_records 表（Phase 12 考核系統）

        Args:
            employee_id: 員工 ID
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            int: 責任事件次數
        """
        # 取得季度起止日期
        start_date, end_date = self.get_quarter_dates(year, quarter)

        # 查詢該季度的責任事件（S類或R類且有實際扣分）
        count = self.db.query(func.count(AssessmentRecord.id)).join(
            AssessmentStandard,
            AssessmentRecord.standard_code == AssessmentStandard.code
        ).filter(
            and_(
                AssessmentRecord.employee_id == employee_id,
                AssessmentRecord.record_date >= start_date,
                AssessmentRecord.record_date <= end_date,
                AssessmentRecord.is_deleted == False,
                AssessmentRecord.final_points < 0,  # 負分才算責任事件
                AssessmentStandard.category.in_(['S', 'R'])  # S類或R類
            )
        ).scalar()

        return count or 0

    # ============================================================
    # 每日時數計算
    # ============================================================

    def calculate_daily_minutes(
        self,
        employee_id: int,
        record_date: date,
        route_minutes_map: dict[str, int]
    ) -> tuple[int, bool]:
        """
        計算員工指定日期的駕駛分鐘數

        Args:
            employee_id: 員工 ID
            record_date: 日期
            route_minutes_map: 勤務代碼到分鐘數映射

        Returns:
            tuple: (總分鐘數, 是否為R班出勤)
        """
        # 查詢該員工當天的班表
        schedule = self.db.query(Schedule).filter(
            and_(
                Schedule.employee_id == employee_id,
                Schedule.schedule_date == record_date
            )
        ).first()

        if not schedule or not schedule.shift_type:
            return 0, False

        # 判斷是否為 R班
        is_r_shift = self.is_holiday_work(schedule.shift_type)

        # 提取勤務代碼（移除 R/ 等前綴）
        shift_code = self._extract_shift_code(schedule.shift_type)

        # 查詢標準分鐘數
        total_minutes = route_minutes_map.get(shift_code, 0)

        return total_minutes, is_r_shift

    def _extract_shift_code(self, shift_type: str) -> str:
        """
        提取勤務代碼

        範例：
        - "R/0905G" → "0905G"
        - "R(國)/1425G" → "1425G"
        - "0905G(+2)" → "0905G"
        - "0905G" → "0905G"

        Args:
            shift_type: 班別類型

        Returns:
            str: 勤務代碼
        """
        if not shift_type:
            return ""

        code = shift_type.strip()

        # 移除 R/ 或 R(...)/  前綴
        if code.startswith("R/"):
            code = code[2:]
        elif code.startswith("R("):
            # 找到 )/ 並移除
            idx = code.find(")/")
            if idx != -1:
                code = code[idx + 2:]

        # 移除 (+N) 後綴
        if "(" in code:
            code = code.split("(")[0]

        return code.strip().upper()

    # ============================================================
    # 季度累計統計
    # ============================================================

    def get_quarter_dates(self, year: int, quarter: int) -> tuple[date, date]:
        """
        取得季度的起止日期

        Args:
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            tuple: (起始日期, 結束日期)
        """
        quarter_months = {
            1: (1, 3),
            2: (4, 6),
            3: (7, 9),
            4: (10, 12),
        }

        start_month, end_month = quarter_months.get(quarter, (1, 3))
        start_date = date(year, start_month, 1)

        # 計算結束日期（下個月1日減1天）
        if end_month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, end_month + 1, 1) - timedelta(days=1)

        return start_date, end_date

    def get_quarter_stats(
        self,
        employee_id: int,
        year: int,
        quarter: int
    ) -> dict:
        """
        取得員工季度統計

        Args:
            employee_id: 員工 ID
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            dict: 季度統計資料
        """
        start_date, end_date = self.get_quarter_dates(year, quarter)

        # 查詢季度內的每日統計
        stats = self.db.query(
            func.sum(DrivingDailyStats.total_minutes).label("total_minutes"),
            func.sum(
                func.case(
                    (DrivingDailyStats.is_holiday_work == True, DrivingDailyStats.total_minutes),
                    else_=0
                )
            ).label("holiday_work_minutes"),
            func.count(DrivingDailyStats.id).label("work_days")
        ).filter(
            and_(
                DrivingDailyStats.employee_id == employee_id,
                DrivingDailyStats.record_date >= start_date,
                DrivingDailyStats.record_date <= end_date
            )
        ).first()

        total_minutes = stats.total_minutes or 0
        holiday_work_minutes = stats.holiday_work_minutes or 0
        work_days = stats.work_days or 0

        # 責任事件次數
        incident_count = self.count_incidents_for_quarter(employee_id, year, quarter)

        return {
            "employee_id": employee_id,
            "year": year,
            "quarter": quarter,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_minutes": total_minutes,
            "total_hours": total_minutes / 60.0,
            "holiday_work_minutes": holiday_work_minutes,
            "holiday_work_bonus_minutes": holiday_work_minutes,  # R班額外加成
            "effective_minutes": total_minutes + holiday_work_minutes,
            "effective_hours": (total_minutes + holiday_work_minutes) / 60.0,
            "work_days": work_days,
            "incident_count": incident_count,
        }

    def get_quarter_stats_by_department(
        self,
        department: str,
        year: int,
        quarter: int,
        include_resigned: bool = False
    ) -> list[dict]:
        """
        取得部門所有員工的季度統計

        Args:
            department: 部門
            year: 年份
            quarter: 季度 (1-4)
            include_resigned: 是否包含離職員工

        Returns:
            list[dict]: 員工季度統計列表
        """
        start_date, end_date = self.get_quarter_dates(year, quarter)

        # 查詢部門員工
        employee_query = self.db.query(Employee).filter(
            Employee.current_department == department
        )
        if not include_resigned:
            employee_query = employee_query.filter(Employee.is_resigned == False)

        employees = employee_query.all()

        results = []
        for employee in employees:
            stats = self.get_quarter_stats(employee.id, year, quarter)
            stats["employee_name"] = employee.employee_name
            stats["employee_code"] = employee.employee_id
            stats["department"] = department
            results.append(stats)

        # 按有效分鐘數降序排列
        results.sort(key=lambda x: x["effective_minutes"], reverse=True)

        return results

    # ============================================================
    # 每日統計資料管理
    # ============================================================

    def save_daily_stats(
        self,
        employee_id: int,
        department: str,
        record_date: date,
        total_minutes: int,
        is_holiday_work: bool,
        incident_count: int = 0
    ) -> DrivingDailyStats:
        """
        儲存或更新每日統計資料

        Args:
            employee_id: 員工 ID
            department: 部門
            record_date: 日期
            total_minutes: 總分鐘數
            is_holiday_work: 是否為 R班出勤
            incident_count: 責任事件次數

        Returns:
            DrivingDailyStats: 每日統計資料
        """
        # 檢查是否已存在
        existing = self.db.query(DrivingDailyStats).filter(
            and_(
                DrivingDailyStats.employee_id == employee_id,
                DrivingDailyStats.record_date == record_date
            )
        ).first()

        if existing:
            # 更新
            existing.department = department
            existing.total_minutes = total_minutes
            existing.is_holiday_work = is_holiday_work
            existing.incident_count = incident_count
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # 新建
            stats = DrivingDailyStats(
                employee_id=employee_id,
                department=department,
                record_date=record_date,
                total_minutes=total_minutes,
                is_holiday_work=is_holiday_work,
                incident_count=incident_count
            )
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)
            return stats

    def get_daily_stats(
        self,
        employee_id: int,
        record_date: date
    ) -> Optional[DrivingDailyStats]:
        """取得員工指定日期的統計資料"""
        return self.db.query(DrivingDailyStats).filter(
            and_(
                DrivingDailyStats.employee_id == employee_id,
                DrivingDailyStats.record_date == record_date
            )
        ).first()

    def list_daily_stats(
        self,
        employee_id: Optional[int] = None,
        department: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[DrivingDailyStats]:
        """
        列出每日統計資料

        Args:
            employee_id: 篩選員工
            department: 篩選部門
            start_date: 起始日期
            end_date: 結束日期
            skip: 跳過筆數
            limit: 限制筆數

        Returns:
            list[DrivingDailyStats]: 每日統計列表
        """
        query = self.db.query(DrivingDailyStats)

        if employee_id:
            query = query.filter(DrivingDailyStats.employee_id == employee_id)
        if department:
            query = query.filter(DrivingDailyStats.department == department)
        if start_date:
            query = query.filter(DrivingDailyStats.record_date >= start_date)
        if end_date:
            query = query.filter(DrivingDailyStats.record_date <= end_date)

        query = query.order_by(DrivingDailyStats.record_date.desc())
        query = query.offset(skip).limit(limit)

        return query.all()
