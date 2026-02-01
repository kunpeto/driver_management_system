"""
ProfilePolicy 權限策略
對應 Gemini Review P2: 統一權限邏輯至 Policy 層

將散落在 API 層的權限檢查邏輯集中管理，提升可維護性。
"""

from src.middleware.permission import Role
from src.models import Profile


class ProfilePolicy:
    """
    履歷權限策略

    提供履歷相關操作的權限檢查方法。
    所有權限檢查邏輯集中在此類別，便於維護和審計。
    """

    @staticmethod
    def can_view(user_role: str, user_department: str, profile: Profile) -> bool:
        """
        檢查是否可以查看履歷

        規則：
        - Admin 和 Manager 可查看所有履歷
        - Staff 只能查看自己部門的履歷

        Args:
            user_role: 使用者角色
            user_department: 使用者部門
            profile: 履歷物件

        Returns:
            是否有權限
        """
        if user_role in [Role.ADMIN, Role.MANAGER]:
            return True

        return profile.department == user_department

    @staticmethod
    def can_edit(user_role: str, user_department: str, profile: Profile) -> bool:
        """
        檢查是否可以編輯履歷

        規則：
        - Admin 和 Manager 可編輯所有履歷
        - Staff 只能編輯自己部門的履歷

        Args:
            user_role: 使用者角色
            user_department: 使用者部門
            profile: 履歷物件

        Returns:
            是否有權限
        """
        if user_role in [Role.ADMIN, Role.MANAGER]:
            return True

        return profile.department == user_department

    @staticmethod
    def can_convert(user_role: str, user_department: str, profile: Profile) -> bool:
        """
        檢查是否可以轉換履歷類型

        規則：
        - Admin 和 Manager 可轉換所有履歷
        - Staff 只能轉換自己部門的履歷

        Args:
            user_role: 使用者角色
            user_department: 使用者部門
            profile: 履歷物件

        Returns:
            是否有權限
        """
        if user_role in [Role.ADMIN, Role.MANAGER]:
            return True

        return profile.department == user_department

    @staticmethod
    def can_reset(user_role: str, user_department: str, profile: Profile) -> bool:
        """
        檢查是否可以重置履歷

        規則：
        - Admin 和 Manager 可重置所有履歷
        - Staff 只能重置自己部門的履歷

        Args:
            user_role: 使用者角色
            user_department: 使用者部門
            profile: 履歷物件

        Returns:
            是否有權限
        """
        if user_role in [Role.ADMIN, Role.MANAGER]:
            return True

        return profile.department == user_department

    @staticmethod
    def can_generate_document(
        user_role: str, user_department: str, profile: Profile
    ) -> bool:
        """
        檢查是否可以生成文件

        規則：
        - Admin 和 Manager 可為所有履歷生成文件
        - Staff 只能為自己部門的履歷生成文件

        Args:
            user_role: 使用者角色
            user_department: 使用者部門
            profile: 履歷物件

        Returns:
            是否有權限
        """
        if user_role in [Role.ADMIN, Role.MANAGER]:
            return True

        return profile.department == user_department

    @staticmethod
    def can_delete(user_role: str) -> bool:
        """
        檢查是否可以刪除履歷

        規則：
        - 僅 Admin 和 Manager 可刪除履歷

        Args:
            user_role: 使用者角色

        Returns:
            是否有權限
        """
        return user_role in [Role.ADMIN, Role.MANAGER]

    @staticmethod
    def can_mark_complete(
        user_role: str, user_department: str, profile: Profile
    ) -> bool:
        """
        檢查是否可以標記履歷為完成

        規則：
        - Admin 和 Manager 可標記所有履歷
        - Staff 只能標記自己部門的履歷

        Args:
            user_role: 使用者角色
            user_department: 使用者部門
            profile: 履歷物件

        Returns:
            是否有權限
        """
        if user_role in [Role.ADMIN, Role.MANAGER]:
            return True

        return profile.department == user_department

    @staticmethod
    def get_allowed_departments(user_role: str, user_department: str) -> list[str]:
        """
        取得使用者可存取的部門列表

        規則：
        - Admin 和 Manager 可存取所有部門
        - Staff 只能存取自己部門

        Args:
            user_role: 使用者角色
            user_department: 使用者部門

        Returns:
            可存取的部門列表
        """
        if user_role in [Role.ADMIN, Role.MANAGER]:
            return ["淡海", "安坑"]  # 所有部門

        return [user_department]

    @staticmethod
    def filter_department(
        user_role: str, user_department: str, requested_department: str | None
    ) -> str | None:
        """
        過濾部門參數

        如果使用者是 Staff，強制使用其所屬部門。

        Args:
            user_role: 使用者角色
            user_department: 使用者部門
            requested_department: 請求的部門篩選

        Returns:
            實際使用的部門篩選
        """
        if user_role == Role.STAFF:
            return user_department

        return requested_department
