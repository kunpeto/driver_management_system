"""
UserService 使用者服務
對應 tasks.md T060: 實作 UserService

提供使用者 CRUD、密碼驗證、角色管理功能。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.user import User
from src.utils.password import hash_password, verify_password, is_password_strong


class UserNotFoundError(Exception):
    """使用者不存在錯誤"""
    pass


class DuplicateUsernameError(Exception):
    """使用者名稱重複錯誤"""
    pass


class InvalidPasswordError(Exception):
    """密碼錯誤"""
    pass


class WeakPasswordError(Exception):
    """密碼強度不足"""
    pass


class UserService:
    """
    使用者服務

    提供使用者相關的業務邏輯。
    """

    # 有效的角色
    VALID_ROLES = ["admin", "manager", "staff"]

    # 有效的部門
    VALID_DEPARTMENTS = ["淡海", "安坑"]

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        根據 ID 取得使用者

        Args:
            user_id: 使用者 ID

        Returns:
            User | None: 使用者物件或 None
        """
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        """
        根據使用者名稱取得使用者

        Args:
            username: 使用者名稱

        Returns:
            User | None: 使用者物件或 None
        """
        stmt = select(User).where(User.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_users(
        self,
        role: Optional[str] = None,
        department: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[User]:
        """
        取得使用者列表

        Args:
            role: 角色篩選
            department: 部門篩選
            is_active: 是否啟用篩選
            skip: 跳過筆數
            limit: 回傳筆數上限

        Returns:
            list[User]: 使用者列表
        """
        stmt = select(User)

        if role:
            stmt = stmt.where(User.role == role)

        if department:
            stmt = stmt.where(User.department == department)

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        stmt = stmt.order_by(User.id).offset(skip).limit(limit)

        return list(self.db.execute(stmt).scalars().all())

    def count_users(
        self,
        role: Optional[str] = None,
        department: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """
        計算使用者數量

        Args:
            role: 角色篩選
            department: 部門篩選
            is_active: 是否啟用篩選

        Returns:
            int: 使用者數量
        """
        stmt = select(func.count(User.id))

        if role:
            stmt = stmt.where(User.role == role)

        if department:
            stmt = stmt.where(User.department == department)

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        return self.db.execute(stmt).scalar() or 0

    def create(
        self,
        username: str,
        password: str,
        display_name: str,
        role: str = "staff",
        department: Optional[str] = None,
        email: Optional[str] = None,
        is_active: bool = True,
        check_password_strength: bool = True
    ) -> User:
        """
        建立新使用者

        Args:
            username: 使用者名稱
            password: 明文密碼
            display_name: 顯示名稱
            role: 角色（admin, manager, staff）
            department: 所屬部門
            email: 電子郵件
            is_active: 是否啟用
            check_password_strength: 是否檢查密碼強度

        Returns:
            User: 新建立的使用者

        Raises:
            DuplicateUsernameError: 使用者名稱重複
            WeakPasswordError: 密碼強度不足
            ValueError: 無效的角色或部門
        """
        # 驗證角色
        if role not in self.VALID_ROLES:
            raise ValueError(f"無效的角色：{role}，有效值為：{self.VALID_ROLES}")

        # 驗證部門（非 admin 必須有部門）
        if role != "admin" and department is None:
            raise ValueError(f"角色 {role} 必須指定部門")

        if department and department not in self.VALID_DEPARTMENTS:
            raise ValueError(f"無效的部門：{department}，有效值為：{self.VALID_DEPARTMENTS}")

        # 檢查密碼強度
        if check_password_strength:
            is_strong, error_msg = is_password_strong(password)
            if not is_strong:
                raise WeakPasswordError(error_msg)

        # 雜湊密碼
        password_hash = hash_password(password)

        # 建立使用者
        user = User(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            department=department,
            email=email,
            is_active=is_active
        )

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise DuplicateUsernameError(f"使用者名稱 {username} 已存在")

    def update(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        department: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """
        更新使用者資訊

        Args:
            user_id: 使用者 ID
            display_name: 顯示名稱
            email: 電子郵件
            role: 角色
            department: 部門
            is_active: 是否啟用

        Returns:
            User: 更新後的使用者

        Raises:
            UserNotFoundError: 使用者不存在
            ValueError: 無效的角色或部門
        """
        user = self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"使用者 ID {user_id} 不存在")

        # 更新欄位
        if display_name is not None:
            user.display_name = display_name

        if email is not None:
            user.email = email

        if role is not None:
            if role not in self.VALID_ROLES:
                raise ValueError(f"無效的角色：{role}")
            user.role = role

        if department is not None:
            if department and department not in self.VALID_DEPARTMENTS:
                raise ValueError(f"無效的部門：{department}")
            user.department = department

        if is_active is not None:
            user.is_active = is_active

        # 驗證角色與部門一致性
        if user.role != "admin" and user.department is None:
            raise ValueError(f"角色 {user.role} 必須指定部門")

        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        check_password_strength: bool = True
    ) -> User:
        """
        變更密碼

        Args:
            user_id: 使用者 ID
            old_password: 舊密碼
            new_password: 新密碼
            check_password_strength: 是否檢查密碼強度

        Returns:
            User: 更新後的使用者

        Raises:
            UserNotFoundError: 使用者不存在
            InvalidPasswordError: 舊密碼錯誤
            WeakPasswordError: 新密碼強度不足
        """
        user = self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"使用者 ID {user_id} 不存在")

        # 驗證舊密碼
        if not verify_password(old_password, user.password_hash):
            raise InvalidPasswordError("舊密碼錯誤")

        # 檢查新密碼強度
        if check_password_strength:
            is_strong, error_msg = is_password_strong(new_password)
            if not is_strong:
                raise WeakPasswordError(error_msg)

        # 更新密碼
        user.password_hash = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def reset_password(
        self,
        user_id: int,
        new_password: str,
        check_password_strength: bool = True
    ) -> User:
        """
        重設密碼（管理員操作，不需要舊密碼）

        Args:
            user_id: 使用者 ID
            new_password: 新密碼
            check_password_strength: 是否檢查密碼強度

        Returns:
            User: 更新後的使用者

        Raises:
            UserNotFoundError: 使用者不存在
            WeakPasswordError: 新密碼強度不足
        """
        user = self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"使用者 ID {user_id} 不存在")

        # 檢查新密碼強度
        if check_password_strength:
            is_strong, error_msg = is_password_strong(new_password)
            if not is_strong:
                raise WeakPasswordError(error_msg)

        # 更新密碼
        user.password_hash = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def verify_credentials(self, username: str, password: str) -> Optional[User]:
        """
        驗證使用者憑證

        Args:
            username: 使用者名稱
            password: 明文密碼

        Returns:
            User | None: 驗證成功返回使用者，失敗返回 None
        """
        user = self.get_by_username(username)

        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def update_last_login(self, user_id: int) -> User:
        """
        更新最後登入時間

        Args:
            user_id: 使用者 ID

        Returns:
            User: 更新後的使用者

        Raises:
            UserNotFoundError: 使用者不存在
        """
        user = self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"使用者 ID {user_id} 不存在")

        user.last_login_at = datetime.now()
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate(self, user_id: int) -> User:
        """
        停用使用者

        Args:
            user_id: 使用者 ID

        Returns:
            User: 更新後的使用者

        Raises:
            UserNotFoundError: 使用者不存在
        """
        return self.update(user_id, is_active=False)

    def activate(self, user_id: int) -> User:
        """
        啟用使用者

        Args:
            user_id: 使用者 ID

        Returns:
            User: 更新後的使用者

        Raises:
            UserNotFoundError: 使用者不存在
        """
        return self.update(user_id, is_active=True)

    def delete(self, user_id: int) -> bool:
        """
        刪除使用者

        Args:
            user_id: 使用者 ID

        Returns:
            bool: 是否刪除成功

        Raises:
            UserNotFoundError: 使用者不存在
        """
        user = self.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"使用者 ID {user_id} 不存在")

        self.db.delete(user)
        self.db.commit()
        return True
