"""
DrivingCompetitionRanker 駕駛競賽排名服務
對應 tasks.md T108: 實作駕駛競賽排名服務

提供季度積分計算、資格檢查、部門排名、排名限額、獎金分配、在職驗證等功能。
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.models.driving_competition import DrivingCompetition
from src.models.driving_daily_stats import DrivingDailyStats
from src.models.employee import Employee
from src.models.google_oauth_token import Department
from src.services.driving_stats_calculator import DrivingStatsCalculator


class DrivingCompetitionRankerError(Exception):
    """駕駛競賽排名服務錯誤"""
    pass


class DrivingCompetitionRanker:
    """
    駕駛競賽排名服務

    實作季度競賽排名計算邏輯。

    核心規則：
    1. 資格檢查：季度累計時數 ≥ 300小時 且 季度最後一日 is_resigned = false
    2. 積分計算：final_score = (total_minutes + holiday_work_bonus_minutes) / (1 + incident_count)
    3. 部門排名：依 final_score 降序排列，積分相同時依 employee_id 升序
    4. 排名限額與獎金：
       - 淡海：rank ≤ 5 才獲獎金，金額 = [3600, 3000, 2400, 1800, 1200][rank-1]
       - 安坑：rank ≤ 3 才獲獎金，金額 = [3600, 3000, 2400][rank-1]
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.stats_calculator = DrivingStatsCalculator(db)

    # ============================================================
    # 季度日期計算
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
        return self.stats_calculator.get_quarter_dates(year, quarter)

    def get_quarter_last_day(self, year: int, quarter: int) -> date:
        """
        取得季度最後一天

        Args:
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            date: 季度最後一天
        """
        _, end_date = self.get_quarter_dates(year, quarter)
        return end_date

    # ============================================================
    # 資格檢查
    # ============================================================

    def is_employed_on_date(self, employee_id: int, check_date: date) -> bool:
        """
        檢查員工在指定日期是否在職

        Args:
            employee_id: 員工 ID
            check_date: 檢查日期

        Returns:
            bool: 是否在職
        """
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()

        if not employee:
            return False

        # 目前使用 is_resigned 欄位判斷
        # 如果需要更精確的判斷（如離職日期），需要擴充 Employee 模型
        return not employee.is_resigned

    def check_qualification(
        self,
        total_minutes: int,
        is_employed_on_last_day: bool
    ) -> bool:
        """
        檢查是否符合資格

        資格條件：
        1. 季度累計時數 ≥ 300小時（18000分鐘）
        2. 季度最後一日仍在職

        Args:
            total_minutes: 季度累計分鐘數
            is_employed_on_last_day: 季末是否在職

        Returns:
            bool: 是否符合資格
        """
        return DrivingCompetition.check_qualification(total_minutes, is_employed_on_last_day)

    # ============================================================
    # 積分計算
    # ============================================================

    def calculate_final_score(
        self,
        total_minutes: int,
        holiday_bonus_minutes: int,
        incident_count: int
    ) -> float:
        """
        計算最終積分

        公式: (total_minutes + holiday_bonus_minutes) / (1 + incident_count)

        Args:
            total_minutes: 總駕駛分鐘數
            holiday_bonus_minutes: R班加成分鐘數
            incident_count: 責任事件次數

        Returns:
            float: 最終積分
        """
        return DrivingCompetition.calculate_final_score(
            total_minutes, holiday_bonus_minutes, incident_count
        )

    # ============================================================
    # 獎金計算
    # ============================================================

    def get_bonus_amount(
        self,
        department: str,
        rank: int,
        is_qualified: bool
    ) -> int:
        """
        計算獎金金額

        Args:
            department: 部門
            rank: 排名
            is_qualified: 是否符合資格

        Returns:
            int: 獎金金額
        """
        return DrivingCompetition.get_bonus_amount(department, rank, is_qualified)

    # ============================================================
    # 排名計算
    # ============================================================

    def calculate_quarterly_ranking(
        self,
        year: int,
        quarter: int
    ) -> dict:
        """
        計算指定季度的競賽排名

        執行流程：
        1. 取得季度日期範圍
        2. 查詢各部門所有員工的季度累計時數
        3. 計算每位員工的積分
        4. 依部門分別排名
        5. 檢查資格並分配獎金
        6. 儲存排名結果

        Args:
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            dict: 排名計算結果
        """
        start_date, end_date = self.get_quarter_dates(year, quarter)

        results = {
            "year": year,
            "quarter": quarter,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "departments": {},
            "total_processed": 0,
            "errors": []
        }

        # 對每個部門進行排名計算
        for dept in [Department.DANHAI.value, Department.ANKENG.value]:
            try:
                dept_result = self._calculate_department_ranking(
                    year, quarter, dept, start_date, end_date
                )
                results["departments"][dept] = dept_result
                results["total_processed"] += dept_result["processed"]
            except Exception as e:
                results["errors"].append(f"{dept}: {str(e)}")

        return results

    def _calculate_department_ranking(
        self,
        year: int,
        quarter: int,
        department: str,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        計算指定部門的排名

        Args:
            year: 年份
            quarter: 季度
            department: 部門
            start_date: 起始日期
            end_date: 結束日期

        Returns:
            dict: 部門排名結果
        """
        # 查詢該部門所有在職員工的季度統計
        employee_stats = self.db.query(
            Employee.id.label("employee_id"),
            Employee.employee_id.label("employee_code"),
            Employee.employee_name,
            Employee.is_resigned,
            func.coalesce(func.sum(DrivingDailyStats.total_minutes), 0).label("total_minutes"),
            func.coalesce(func.sum(
                func.case(
                    (DrivingDailyStats.is_holiday_work == True, DrivingDailyStats.total_minutes),
                    else_=0
                )
            ), 0).label("holiday_work_minutes")
        ).outerjoin(
            DrivingDailyStats,
            and_(
                DrivingDailyStats.employee_id == Employee.id,
                DrivingDailyStats.record_date >= start_date,
                DrivingDailyStats.record_date <= end_date
            )
        ).filter(
            Employee.current_department == department
        ).group_by(
            Employee.id,
            Employee.employee_id,
            Employee.employee_name,
            Employee.is_resigned
        ).all()

        # 計算積分並排序
        rankings = []
        for stat in employee_stats:
            # 責任事件次數（待 US8 整合）
            incident_count = self.stats_calculator.count_incidents_for_quarter(
                stat.employee_id, year, quarter
            )

            # 計算積分
            final_score = self.calculate_final_score(
                stat.total_minutes,
                stat.holiday_work_minutes,
                incident_count
            )

            # 季末在職狀態
            is_employed_on_last_day = not stat.is_resigned

            # 資格檢查
            is_qualified = self.check_qualification(
                stat.total_minutes + stat.holiday_work_minutes,
                is_employed_on_last_day
            )

            rankings.append({
                "employee_id": stat.employee_id,
                "employee_code": stat.employee_code,
                "employee_name": stat.employee_name,
                "total_minutes": stat.total_minutes,
                "holiday_work_minutes": stat.holiday_work_minutes,
                "incident_count": incident_count,
                "final_score": final_score,
                "is_employed_on_last_day": is_employed_on_last_day,
                "is_qualified": is_qualified
            })

        # 排序：積分降序，員工編號升序（積分相同時）
        rankings.sort(key=lambda x: (-x["final_score"], x["employee_code"]))

        # 分配排名與獎金
        processed = 0
        for rank, entry in enumerate(rankings, 1):
            entry["rank"] = rank
            entry["bonus_amount"] = self.get_bonus_amount(
                department, rank, entry["is_qualified"]
            )

            # 儲存到資料庫
            self._save_competition_record(
                year=year,
                quarter=quarter,
                department=department,
                entry=entry
            )
            processed += 1

        # 統計資訊
        qualified_count = sum(1 for r in rankings if r["is_qualified"])
        bonus_recipients = sum(1 for r in rankings if r["bonus_amount"] > 0)
        total_bonus = sum(r["bonus_amount"] for r in rankings)

        return {
            "department": department,
            "processed": processed,
            "qualified_count": qualified_count,
            "bonus_recipients": bonus_recipients,
            "total_bonus": total_bonus,
            "rankings": rankings
        }

    def _save_competition_record(
        self,
        year: int,
        quarter: int,
        department: str,
        entry: dict
    ) -> DrivingCompetition:
        """
        儲存競賽排名記錄

        Args:
            year: 年份
            quarter: 季度
            department: 部門
            entry: 排名資料

        Returns:
            DrivingCompetition: 競賽記錄
        """
        # 檢查是否已存在
        existing = self.db.query(DrivingCompetition).filter(
            and_(
                DrivingCompetition.employee_id == entry["employee_id"],
                DrivingCompetition.competition_year == year,
                DrivingCompetition.competition_quarter == quarter
            )
        ).first()

        if existing:
            # 更新
            existing.department = department
            existing.total_driving_minutes = entry["total_minutes"]
            existing.holiday_work_bonus_minutes = entry["holiday_work_minutes"]
            existing.incident_count = entry["incident_count"]
            existing.final_score = entry["final_score"]
            existing.rank_in_department = entry["rank"]
            existing.is_qualified = entry["is_qualified"]
            existing.is_employed_on_last_day = entry["is_employed_on_last_day"]
            existing.bonus_amount = entry["bonus_amount"]
            self.db.commit()
            return existing
        else:
            # 新建
            record = DrivingCompetition(
                employee_id=entry["employee_id"],
                competition_year=year,
                competition_quarter=quarter,
                department=department,
                total_driving_minutes=entry["total_minutes"],
                holiday_work_bonus_minutes=entry["holiday_work_minutes"],
                incident_count=entry["incident_count"],
                final_score=entry["final_score"],
                rank_in_department=entry["rank"],
                is_qualified=entry["is_qualified"],
                is_employed_on_last_day=entry["is_employed_on_last_day"],
                bonus_amount=entry["bonus_amount"]
            )
            self.db.add(record)
            self.db.commit()
            return record

    # ============================================================
    # 查詢
    # ============================================================

    def get_quarterly_ranking(
        self,
        year: int,
        quarter: int,
        department: Optional[str] = None
    ) -> dict:
        """
        查詢季度排名

        Args:
            year: 年份
            quarter: 季度 (1-4)
            department: 篩選部門（可選）

        Returns:
            dict: 排名資料
        """
        query = self.db.query(DrivingCompetition).filter(
            and_(
                DrivingCompetition.competition_year == year,
                DrivingCompetition.competition_quarter == quarter
            )
        )

        if department:
            query = query.filter(DrivingCompetition.department == department)

        query = query.order_by(
            DrivingCompetition.department,
            DrivingCompetition.rank_in_department
        )

        records = query.all()

        # 組織結果
        results = {
            "year": year,
            "quarter": quarter,
            "quarter_label": f"{year} Q{quarter}",
            "rankings": []
        }

        for record in records:
            # 取得員工資訊
            employee = self.db.query(Employee).filter(
                Employee.id == record.employee_id
            ).first()

            results["rankings"].append({
                "id": record.id,
                "employee_id": record.employee_id,
                "employee_code": employee.employee_id if employee else None,
                "employee_name": employee.employee_name if employee else None,
                "department": record.department,
                "total_driving_minutes": record.total_driving_minutes,
                "total_hours": record.total_hours,
                "holiday_work_bonus_minutes": record.holiday_work_bonus_minutes,
                "effective_minutes": record.effective_minutes,
                "effective_hours": record.effective_hours,
                "incident_count": record.incident_count,
                "final_score": record.final_score,
                "rank_in_department": record.rank_in_department,
                "is_qualified": record.is_qualified,
                "is_employed_on_last_day": record.is_employed_on_last_day,
                "bonus_amount": record.bonus_amount
            })

        # 統計
        if department:
            dept_records = records
        else:
            dept_records = records

        results["stats"] = {
            "total_employees": len(records),
            "qualified_count": sum(1 for r in records if r.is_qualified),
            "bonus_recipients": sum(1 for r in records if r.bonus_amount > 0),
            "total_bonus": sum(r.bonus_amount for r in records)
        }

        return results

    def get_employee_history(
        self,
        employee_id: int,
        limit: int = 8
    ) -> list[dict]:
        """
        查詢員工競賽歷史

        Args:
            employee_id: 員工 ID
            limit: 限制筆數

        Returns:
            list[dict]: 競賽歷史列表
        """
        records = self.db.query(DrivingCompetition).filter(
            DrivingCompetition.employee_id == employee_id
        ).order_by(
            DrivingCompetition.competition_year.desc(),
            DrivingCompetition.competition_quarter.desc()
        ).limit(limit).all()

        return [
            {
                "year": r.competition_year,
                "quarter": r.competition_quarter,
                "quarter_label": r.quarter_label,
                "department": r.department,
                "total_hours": r.total_hours,
                "effective_hours": r.effective_hours,
                "final_score": r.final_score,
                "rank": r.rank_in_department,
                "is_qualified": r.is_qualified,
                "bonus_amount": r.bonus_amount
            }
            for r in records
        ]
