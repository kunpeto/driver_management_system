"""
EmployeeService 員工服務
對應 tasks.md T046: 實作 EmployeeService

提供員工資料的 CRUD 操作、部門篩選、離職標記等功能。
"""

from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.employee import Employee
from src.constants import Department
from src.utils.employee_parser import EmployeeIdParser


class EmployeeServiceError(Exception):
    """員工服務錯誤"""
    pass


class DuplicateEmployeeError(EmployeeServiceError):
    """員工編號重複錯誤"""
    pass


class EmployeeNotFoundError(EmployeeServiceError):
    """員工不存在錯誤"""
    pass


class InvalidEmployeeIdError(EmployeeServiceError):
    """員工編號格式錯誤"""
    pass


class EmployeeService:
    """
    員工服務

    提供員工資料的 CRUD 操作。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db

    # ============================================================
    # CRUD 操作
    # ============================================================

    def create(
        self,
        employee_id: str,
        employee_name: str,
        current_department: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        emergency_contact: Optional[str] = None,
        emergency_phone: Optional[str] = None,
        hire_year_month: Optional[str] = None,
        auto_commit: bool = True
    ) -> Employee:
        """
        建立員工

        Args:
            employee_id: 員工編號
            employee_name: 員工姓名
            current_department: 部門
            phone: 電話
            email: 電子郵件
            emergency_contact: 緊急聯絡人
            emergency_phone: 緊急聯絡電話
            hire_year_month: 入職年月（若未提供則從編號解析）
            auto_commit: 是否自動提交（批次匯入時設為 False 提升效能）

        Returns:
            Employee: 新建立的員工

        Raises:
            InvalidEmployeeIdError: 員工編號格式錯誤
            DuplicateEmployeeError: 員工編號已存在
        """
        # 驗證並解析員工編號
        parse_result = EmployeeIdParser.parse(employee_id)
        if not parse_result.valid:
            raise InvalidEmployeeIdError(parse_result.error)

        # 若未提供入職年月，則從編號解析
        if not hire_year_month:
            hire_year_month = parse_result.hire_year_month

        # 驗證部門
        self._validate_department(current_department)

        employee = Employee(
            employee_id=parse_result.employee_id,
            employee_name=employee_name,
            current_department=current_department,
            hire_year_month=hire_year_month,
            phone=phone,
            email=email,
            emergency_contact=emergency_contact,
            emergency_phone=emergency_phone,
            is_resigned=False
        )

        try:
            self.db.add(employee)
            if auto_commit:
                self.db.commit()
                self.db.refresh(employee)
            else:
                # 批次模式：只 flush 確保 ID 可用，不 commit
                self.db.flush()
            return employee
        except IntegrityError:
            self.db.rollback()
            raise DuplicateEmployeeError(f"員工編號 '{employee_id}' 已存在")

    def commit(self) -> None:
        """手動提交事務（批次操作後使用）"""
        self.db.commit()

    def get_by_id(self, id: int) -> Optional[Employee]:
        """根據 ID 取得員工"""
        return self.db.query(Employee).filter(Employee.id == id).first()

    def get_by_employee_id(self, employee_id: str) -> Optional[Employee]:
        """根據員工編號取得員工"""
        return self.db.query(Employee).filter(
            Employee.employee_id == employee_id.upper()
        ).first()

    def update(
        self,
        id: int,
        employee_name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        emergency_contact: Optional[str] = None,
        emergency_phone: Optional[str] = None
    ) -> Employee:
        """
        更新員工資料

        注意：員工編號、部門、入職年月不可透過此方法修改。
        部門變更需透過調動流程。

        Args:
            id: 員工 ID
            employee_name: 員工姓名
            phone: 電話
            email: 電子郵件
            emergency_contact: 緊急聯絡人
            emergency_phone: 緊急聯絡電話

        Returns:
            Employee: 更新後的員工

        Raises:
            EmployeeNotFoundError: 員工不存在
        """
        employee = self.get_by_id(id)
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {id} 不存在")

        if employee_name is not None:
            employee.employee_name = employee_name
        if phone is not None:
            employee.phone = phone
        if email is not None:
            employee.email = email
        if emergency_contact is not None:
            employee.emergency_contact = emergency_contact
        if emergency_phone is not None:
            employee.emergency_phone = emergency_phone

        self.db.commit()
        self.db.refresh(employee)
        return employee

    def mark_resigned(self, id: int) -> Employee:
        """
        標記員工離職

        Args:
            id: 員工 ID

        Returns:
            Employee: 更新後的員工

        Raises:
            EmployeeNotFoundError: 員工不存在
        """
        employee = self.get_by_id(id)
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {id} 不存在")

        employee.is_resigned = True
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def mark_active(self, id: int) -> Employee:
        """
        標記員工復職

        Args:
            id: 員工 ID

        Returns:
            Employee: 更新後的員工

        Raises:
            EmployeeNotFoundError: 員工不存在
        """
        employee = self.get_by_id(id)
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {id} 不存在")

        employee.is_resigned = False
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def delete(self, id: int) -> bool:
        """
        刪除員工（軟刪除建議改用 mark_resigned）

        Args:
            id: 員工 ID

        Returns:
            bool: 是否成功刪除

        Raises:
            EmployeeNotFoundError: 員工不存在
        """
        employee = self.get_by_id(id)
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {id} 不存在")

        self.db.delete(employee)
        self.db.commit()
        return True

    # ============================================================
    # 查詢操作
    # ============================================================

    def list_all(
        self,
        include_resigned: bool = False,
        department: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Employee]:
        """
        列出員工

        Args:
            include_resigned: 是否包含離職員工
            department: 篩選部門
            search: 搜尋關鍵字（員工編號或姓名）
            skip: 跳過筆數
            limit: 限制筆數

        Returns:
            list[Employee]: 員工列表
        """
        query = self.db.query(Employee)

        # 篩選離職狀態
        if not include_resigned:
            query = query.filter(Employee.is_resigned == False)

        # 篩選部門
        if department:
            query = query.filter(Employee.current_department == department)

        # 搜尋
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.employee_id.like(search_pattern),
                    Employee.employee_name.like(search_pattern)
                )
            )

        # 排序與分頁
        query = query.order_by(Employee.employee_id)
        query = query.offset(skip).limit(limit)

        return query.all()

    def count(
        self,
        include_resigned: bool = False,
        department: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        """
        計算員工數量

        Args:
            include_resigned: 是否包含離職員工
            department: 篩選部門
            search: 搜尋關鍵字

        Returns:
            int: 員工數量
        """
        query = self.db.query(Employee)

        if not include_resigned:
            query = query.filter(Employee.is_resigned == False)

        if department:
            query = query.filter(Employee.current_department == department)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.employee_id.like(search_pattern),
                    Employee.employee_name.like(search_pattern)
                )
            )

        return query.count()

    def list_by_department(
        self,
        department: str,
        include_resigned: bool = False
    ) -> list[Employee]:
        """
        列出指定部門的員工

        Args:
            department: 部門名稱
            include_resigned: 是否包含離職員工

        Returns:
            list[Employee]: 員工列表
        """
        return self.list_all(
            include_resigned=include_resigned,
            department=department,
            limit=10000
        )

    def get_statistics(self) -> dict:
        """
        取得員工統計資料

        Returns:
            dict: 統計資料
        """
        total = self.db.query(Employee).count()
        active = self.db.query(Employee).filter(Employee.is_resigned == False).count()
        resigned = total - active

        danhai = self.db.query(Employee).filter(
            and_(
                Employee.current_department == Department.DANHAI.value,
                Employee.is_resigned == False
            )
        ).count()

        ankeng = self.db.query(Employee).filter(
            and_(
                Employee.current_department == Department.ANKENG.value,
                Employee.is_resigned == False
            )
        ).count()

        return {
            "total": total,
            "active": active,
            "resigned": resigned,
            "by_department": {
                Department.DANHAI.value: danhai,
                Department.ANKENG.value: ankeng
            }
        }

    # ============================================================
    # 部門變更（內部使用，由 EmployeeTransferService 呼叫）
    # ============================================================

    def update_department(self, id: int, new_department: str) -> Employee:
        """
        更新員工部門（內部方法）

        此方法僅供 EmployeeTransferService 呼叫，
        不應直接使用，請透過調動流程變更部門。

        Args:
            id: 員工 ID
            new_department: 新部門

        Returns:
            Employee: 更新後的員工
        """
        employee = self.get_by_id(id)
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {id} 不存在")

        self._validate_department(new_department)
        employee.current_department = new_department

        self.db.commit()
        self.db.refresh(employee)
        return employee

    # ============================================================
    # 輔助方法
    # ============================================================

    def _validate_department(self, department: str) -> None:
        """驗證部門名稱"""
        valid_departments = [Department.DANHAI.value, Department.ANKENG.value]
        if department not in valid_departments:
            raise EmployeeServiceError(
                f"無效的部門名稱 '{department}'，有效值為：{valid_departments}"
            )

    def exists(self, employee_id: str) -> bool:
        """檢查員工編號是否存在"""
        return self.get_by_employee_id(employee_id) is not None
