"""
PermissionService 權限檢查服務
對應 tasks.md T062: 實作權限檢查服務

提供更細緻的權限檢查邏輯，包含資料庫查詢。
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.models.user import User
from src.middleware.permission import Role, Department


class PermissionService:
    """
    權限檢查服務

    提供基於資料庫的權限檢查邏輯。
    與 middleware/permission.py 的 PermissionChecker 類似，
    但可以進行更複雜的資料庫查詢。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db

    def can_edit_department(self, user: User, target_department: str) -> bool:
        """
        檢查使用者是否可以編輯指定部門的資料

        規則：
        - Admin: 可以編輯所有部門
        - Manager: 可以編輯所有部門
        - Staff: 只能編輯自己所屬的部門

        Args:
            user: 使用者物件
            target_department: 目標部門

        Returns:
            bool: True 表示有權限
        """
        if user.role in [Role.ADMIN, Role.MANAGER]:
            return True

        return user.department == target_department

    def can_view_department(self, user: User, target_department: str) -> bool:
        """
        檢查使用者是否可以查看指定部門的資料

        規則：
        - 所有已登入使用者都可以查看所有部門（唯讀）

        Args:
            user: 使用者物件
            target_department: 目標部門

        Returns:
            bool: True 表示有權限
        """
        return True

    def can_manage_users(self, user: User) -> bool:
        """
        檢查使用者是否可以管理其他使用者

        規則：
        - 只有 Admin 可以管理使用者

        Args:
            user: 使用者物件

        Returns:
            bool: True 表示有權限
        """
        return user.role == Role.ADMIN

    def can_edit_employee(
        self,
        user: User,
        employee_department: str
    ) -> bool:
        """
        檢查使用者是否可以編輯指定員工

        規則：
        - Admin: 可以編輯所有員工
        - Manager: 可以編輯所有員工
        - Staff: 只能編輯自己部門的員工

        Args:
            user: 使用者物件
            employee_department: 員工所屬部門

        Returns:
            bool: True 表示有權限
        """
        return self.can_edit_department(user, employee_department)

    def can_transfer_employee(
        self,
        user: User,
        from_department: str,
        to_department: str
    ) -> bool:
        """
        檢查使用者是否可以調動員工

        規則：
        - Admin: 可以調動任何員工
        - Manager: 可以調動任何員工
        - Staff: 只能調動自己部門的員工（調出）

        Args:
            user: 使用者物件
            from_department: 調出部門
            to_department: 調入部門

        Returns:
            bool: True 表示有權限
        """
        # 檢查是否可以編輯來源部門的員工
        return self.can_edit_department(user, from_department)

    def can_access_system_settings(self, user: User) -> bool:
        """
        檢查使用者是否可以存取系統設定

        規則：
        - 只有 Admin 可以存取系統設定

        Args:
            user: 使用者物件

        Returns:
            bool: True 表示有權限
        """
        return user.role == Role.ADMIN

    def can_manage_department_settings(
        self,
        user: User,
        target_department: str
    ) -> bool:
        """
        檢查使用者是否可以管理指定部門的設定

        規則：
        - Admin: 可以管理所有部門的設定
        - Manager: 可以管理自己部門的設定
        - Staff: 無權限

        Args:
            user: 使用者物件
            target_department: 目標部門

        Returns:
            bool: True 表示有權限
        """
        if user.role == Role.ADMIN:
            return True

        if user.role == Role.MANAGER:
            return user.department == target_department or user.department is None

        return False

    def get_accessible_departments(self, user: User) -> list[str]:
        """
        取得使用者可存取的部門列表

        Args:
            user: 使用者物件

        Returns:
            list[str]: 可存取的部門列表
        """
        # 所有人都可以查看所有部門
        return Department.ALL

    def get_editable_departments(self, user: User) -> list[str]:
        """
        取得使用者可編輯的部門列表

        Args:
            user: 使用者物件

        Returns:
            list[str]: 可編輯的部門列表
        """
        if user.role in [Role.ADMIN, Role.MANAGER]:
            return Department.ALL

        if user.department:
            return [user.department]

        return []

    def get_default_department_filter(self, user: User) -> Optional[str]:
        """
        取得使用者的預設部門篩選

        用於列表查詢的預設篩選條件。

        Args:
            user: 使用者物件

        Returns:
            str | None: 預設部門，Admin/Manager 返回 None（表示不篩選）
        """
        if user.role in [Role.ADMIN, Role.MANAGER]:
            return None

        return user.department

    def filter_employees_by_permission(
        self,
        user: User,
        department_filter: Optional[str] = None
    ) -> Optional[str]:
        """
        根據權限調整部門篩選

        如果使用者指定了部門篩選，檢查是否有權限查看。
        如果沒有指定，返回預設篩選。

        Args:
            user: 使用者物件
            department_filter: 使用者指定的部門篩選

        Returns:
            str | None: 實際應套用的部門篩選
        """
        if department_filter:
            # 使用者指定了部門篩選，檢查是否有權限查看
            if self.can_view_department(user, department_filter):
                return department_filter
            else:
                # 無權限，返回使用者所屬部門
                return user.department

        # 沒有指定篩選，返回預設值
        return self.get_default_department_filter(user)
