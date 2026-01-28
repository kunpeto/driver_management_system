"""
權限檢查中間件
對應 tasks.md T022: 實作權限檢查中間件

功能：
- 角色驗證（Admin, Staff, Manager）
- 部門權限控制
- 組合權限檢查
"""

from typing import List, Optional, Callable

from fastapi import HTTPException, status, Depends

from src.middleware.auth import TokenData, get_current_user


# 角色定義
class Role:
    """角色常量"""
    ADMIN = "admin"      # 系統管理員（全權限）
    MANAGER = "manager"  # 主管（可查看所有部門）
    STAFF = "staff"      # 值班台人員（僅限本部門）


# 部門定義
class Department:
    """部門常量"""
    TANHAE = "淡海"
    ANPING = "安坑"

    ALL = [TANHAE, ANPING]


def require_role(*allowed_roles: str) -> Callable:
    """
    建立角色驗證依賴

    使用方式：
    ```python
    @router.get("/admin-only")
    async def admin_endpoint(user: TokenData = Depends(require_role(Role.ADMIN))):
        ...
    ```

    Args:
        *allowed_roles: 允許的角色列表

    Returns:
        FastAPI 依賴函數
    """
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {', '.join(allowed_roles)} 角色才能執行此操作"
            )
        return current_user

    return role_checker


def require_admin() -> Callable:
    """
    建立管理員驗證依賴

    簡化版的 require_role(Role.ADMIN)
    """
    return require_role(Role.ADMIN)


def require_manager_or_admin() -> Callable:
    """
    建立主管或管理員驗證依賴

    允許 Manager 或 Admin 角色。
    """
    return require_role(Role.ADMIN, Role.MANAGER)


class PermissionChecker:
    """
    權限檢查器

    用於複雜的權限檢查邏輯，例如：
    - 使用者是否可以編輯指定部門的資料
    - 使用者是否可以查看指定員工的資訊
    """

    @staticmethod
    def can_edit_department(user: TokenData, target_department: str) -> bool:
        """
        檢查使用者是否可以編輯指定部門的資料

        規則：
        - Admin: 可以編輯所有部門
        - Manager: 可以編輯所有部門
        - Staff: 只能編輯自己所屬的部門

        Args:
            user: 當前使用者
            target_department: 目標部門

        Returns:
            bool: True 表示有權限
        """
        if user.role in [Role.ADMIN, Role.MANAGER]:
            return True

        return user.department == target_department

    @staticmethod
    def can_view_department(user: TokenData, target_department: str) -> bool:
        """
        檢查使用者是否可以查看指定部門的資料

        規則：
        - Admin: 可以查看所有部門
        - Manager: 可以查看所有部門
        - Staff: 可以查看所有部門（唯讀）

        Args:
            user: 當前使用者
            target_department: 目標部門

        Returns:
            bool: True 表示有權限（所有人都可查看）
        """
        # 所有已登入使用者都可以查看
        return True

    @staticmethod
    def get_editable_departments(user: TokenData) -> List[str]:
        """
        取得使用者可編輯的部門列表

        Args:
            user: 當前使用者

        Returns:
            List[str]: 可編輯的部門列表
        """
        if user.role in [Role.ADMIN, Role.MANAGER]:
            return Department.ALL

        if user.department:
            return [user.department]

        return []

    @staticmethod
    def get_default_department(user: TokenData) -> Optional[str]:
        """
        取得使用者的預設部門

        用於列表篩選的預設值。

        Args:
            user: 當前使用者

        Returns:
            str | None: 預設部門，Admin/Manager 返回 None（表示顯示全部）
        """
        if user.role in [Role.ADMIN, Role.MANAGER]:
            return None  # 顯示全部

        return user.department


def check_department_permission(
    target_department: str,
    edit_mode: bool = False
) -> Callable:
    """
    建立部門權限檢查依賴

    使用方式：
    ```python
    @router.put("/employees/{id}")
    async def update_employee(
        id: int,
        department: str,
        user: TokenData = Depends(check_department_permission(department, edit_mode=True))
    ):
        ...
    ```

    Args:
        target_department: 目標部門
        edit_mode: 是否為編輯模式（True 需要編輯權限，False 只需查看權限）

    Returns:
        FastAPI 依賴函數
    """
    async def department_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        checker = PermissionChecker()

        if edit_mode:
            if not checker.can_edit_department(current_user, target_department):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"無權限編輯 {target_department} 部門的資料"
                )
        else:
            if not checker.can_view_department(current_user, target_department):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"無權限查看 {target_department} 部門的資料"
                )

        return current_user

    return department_checker


# 便捷依賴
AdminRequired = Depends(require_admin())
ManagerOrAdminRequired = Depends(require_manager_or_admin())
StaffOrAbove = Depends(require_role(Role.ADMIN, Role.MANAGER, Role.STAFF))
