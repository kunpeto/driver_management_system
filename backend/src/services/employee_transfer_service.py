"""
EmployeeTransferService 員工調動服務
對應 tasks.md T047: 實作 EmployeeTransferService

提供員工調動記錄、部門更新、歷史查詢等功能。
"""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from src.models.employee import Employee
from src.models.employee_transfer import EmployeeTransfer
from src.models.google_oauth_token import Department
from src.services.employee_service import EmployeeNotFoundError, EmployeeService


class EmployeeTransferServiceError(Exception):
    """員工調動服務錯誤"""
    pass


class SameDepartmentError(EmployeeTransferServiceError):
    """相同部門調動錯誤"""
    pass


class TransferNotFoundError(EmployeeTransferServiceError):
    """調動記錄不存在錯誤"""
    pass


class EmployeeTransferService:
    """
    員工調動服務

    提供調動記錄、部門更新、歷史查詢功能。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self._employee_service = EmployeeService(db)

    def transfer(
        self,
        employee_id: int,
        to_department: str,
        transfer_date: date,
        reason: Optional[str] = None,
        created_by: str = "system"
    ) -> EmployeeTransfer:
        """
        執行員工調動

        此方法會：
        1. 建立調動記錄
        2. 更新員工的現職部門

        Args:
            employee_id: 員工 ID（數字 ID，非員工編號）
            to_department: 目標部門
            transfer_date: 調動日期
            reason: 調動原因
            created_by: 操作人員

        Returns:
            EmployeeTransfer: 調動記錄

        Raises:
            EmployeeNotFoundError: 員工不存在
            SameDepartmentError: 目標部門與現職部門相同
        """
        # 取得員工
        employee = self._employee_service.get_by_id(employee_id)
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {employee_id} 不存在")

        # 驗證目標部門
        self._validate_department(to_department)

        # 檢查是否為相同部門
        if employee.current_department == to_department:
            raise SameDepartmentError(
                f"員工 {employee.employee_id} 已在 {to_department} 部門，無需調動"
            )

        from_department = employee.current_department

        # 建立調動記錄
        transfer = EmployeeTransfer(
            employee_id=employee.employee_id,
            from_department=from_department,
            to_department=to_department,
            transfer_date=transfer_date,
            reason=reason,
            created_by=created_by
        )

        self.db.add(transfer)

        # 更新員工部門
        employee.current_department = to_department

        self.db.commit()
        self.db.refresh(transfer)

        return transfer

    def transfer_by_employee_id(
        self,
        employee_id: str,
        to_department: str,
        transfer_date: date,
        reason: Optional[str] = None,
        created_by: str = "system"
    ) -> EmployeeTransfer:
        """
        根據員工編號執行調動

        Args:
            employee_id: 員工編號（字串）
            to_department: 目標部門
            transfer_date: 調動日期
            reason: 調動原因
            created_by: 操作人員

        Returns:
            EmployeeTransfer: 調動記錄
        """
        employee = self._employee_service.get_by_employee_id(employee_id)
        if not employee:
            raise EmployeeNotFoundError(f"員工編號 '{employee_id}' 不存在")

        return self.transfer(
            employee_id=employee.id,
            to_department=to_department,
            transfer_date=transfer_date,
            reason=reason,
            created_by=created_by
        )

    def get_transfer_history(
        self,
        employee_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[EmployeeTransfer]:
        """
        取得員工調動歷史

        Args:
            employee_id: 員工 ID
            skip: 跳過筆數
            limit: 限制筆數

        Returns:
            list[EmployeeTransfer]: 調動歷史列表（依日期降序）
        """
        employee = self._employee_service.get_by_id(employee_id)
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {employee_id} 不存在")

        return self.db.query(EmployeeTransfer).filter(
            EmployeeTransfer.employee_id == employee.employee_id
        ).order_by(
            EmployeeTransfer.transfer_date.desc()
        ).offset(skip).limit(limit).all()

    def get_transfer_history_by_employee_id(
        self,
        employee_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[EmployeeTransfer]:
        """
        根據員工編號取得調動歷史

        Args:
            employee_id: 員工編號
            skip: 跳過筆數
            limit: 限制筆數

        Returns:
            list[EmployeeTransfer]: 調動歷史列表
        """
        return self.db.query(EmployeeTransfer).filter(
            EmployeeTransfer.employee_id == employee_id.upper()
        ).order_by(
            EmployeeTransfer.transfer_date.desc()
        ).offset(skip).limit(limit).all()

    def get_transfer_by_id(self, transfer_id: int) -> Optional[EmployeeTransfer]:
        """根據 ID 取得調動記錄"""
        return self.db.query(EmployeeTransfer).filter(
            EmployeeTransfer.id == transfer_id
        ).first()

    def list_recent_transfers(
        self,
        days: int = 30,
        department: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[EmployeeTransfer]:
        """
        列出最近的調動記錄

        Args:
            days: 最近天數
            department: 篩選部門（調入或調出）
            skip: 跳過筆數
            limit: 限制筆數

        Returns:
            list[EmployeeTransfer]: 調動記錄列表
        """
        from datetime import timedelta

        cutoff_date = date.today() - timedelta(days=days)

        query = self.db.query(EmployeeTransfer).filter(
            EmployeeTransfer.transfer_date >= cutoff_date
        )

        if department:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    EmployeeTransfer.from_department == department,
                    EmployeeTransfer.to_department == department
                )
            )

        return query.order_by(
            EmployeeTransfer.transfer_date.desc()
        ).offset(skip).limit(limit).all()

    def count_transfers(
        self,
        employee_id: Optional[int] = None,
        department: Optional[str] = None
    ) -> int:
        """
        計算調動記錄數量

        Args:
            employee_id: 員工 ID（選填）
            department: 部門（選填）

        Returns:
            int: 調動記錄數量
        """
        query = self.db.query(EmployeeTransfer)

        if employee_id:
            employee = self._employee_service.get_by_id(employee_id)
            if employee:
                query = query.filter(
                    EmployeeTransfer.employee_id == employee.employee_id
                )

        if department:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    EmployeeTransfer.from_department == department,
                    EmployeeTransfer.to_department == department
                )
            )

        return query.count()

    def delete_transfer(self, transfer_id: int) -> bool:
        """
        刪除調動記錄

        注意：此操作不會還原員工部門，僅刪除記錄。

        Args:
            transfer_id: 調動記錄 ID

        Returns:
            bool: 是否成功刪除

        Raises:
            TransferNotFoundError: 調動記錄不存在
        """
        transfer = self.get_transfer_by_id(transfer_id)
        if not transfer:
            raise TransferNotFoundError(f"調動記錄 ID {transfer_id} 不存在")

        self.db.delete(transfer)
        self.db.commit()
        return True

    def get_statistics(self) -> dict:
        """
        取得調動統計

        Returns:
            dict: 統計資料
        """
        from datetime import timedelta
        from sqlalchemy import func

        total = self.db.query(EmployeeTransfer).count()

        # 最近 30 天
        cutoff_30 = date.today() - timedelta(days=30)
        recent_30 = self.db.query(EmployeeTransfer).filter(
            EmployeeTransfer.transfer_date >= cutoff_30
        ).count()

        # 本年度
        current_year = date.today().year
        year_start = date(current_year, 1, 1)
        this_year = self.db.query(EmployeeTransfer).filter(
            EmployeeTransfer.transfer_date >= year_start
        ).count()

        # 依部門統計（調入）
        dept_stats = {}
        for dept in [Department.DANHAI.value, Department.ANKENG.value]:
            transfer_in = self.db.query(EmployeeTransfer).filter(
                EmployeeTransfer.to_department == dept
            ).count()
            transfer_out = self.db.query(EmployeeTransfer).filter(
                EmployeeTransfer.from_department == dept
            ).count()
            dept_stats[dept] = {
                "transfer_in": transfer_in,
                "transfer_out": transfer_out,
                "net": transfer_in - transfer_out
            }

        return {
            "total": total,
            "recent_30_days": recent_30,
            "this_year": this_year,
            "by_department": dept_stats
        }

    def _validate_department(self, department: str) -> None:
        """驗證部門名稱"""
        valid_departments = [Department.DANHAI.value, Department.ANKENG.value]
        if department not in valid_departments:
            raise EmployeeTransferServiceError(
                f"無效的部門名稱 '{department}'，有效值為：{valid_departments}"
            )
