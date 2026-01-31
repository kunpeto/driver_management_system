"""
AuthService 認證服務
對應 tasks.md T061: 實作 AuthService

提供登入、JWT 生成、Token 刷新功能。
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from src.models.user import User
from src.services.user_service import UserService
from src.utils.jwt import JWTHandler, get_jwt_handler


class AuthenticationError(Exception):
    """認證錯誤"""
    pass


class InvalidTokenError(Exception):
    """無效 Token 錯誤"""
    pass


class UserInactiveError(Exception):
    """使用者已停用"""
    pass


@dataclass
class AuthResult:
    """認證結果"""
    user: User
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass
class TokenRefreshResult:
    """Token 刷新結果"""
    access_token: str
    token_type: str = "bearer"


class AuthService:
    """
    認證服務

    提供使用者認證相關的業務邏輯。
    """

    def __init__(self, db: Session, jwt_handler: Optional[JWTHandler] = None):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
            jwt_handler: JWT 處理器（可選，預設使用單例）
        """
        self.db = db
        self._user_service = UserService(db)
        self._jwt_handler = jwt_handler or get_jwt_handler()

    def login(self, username: str, password: str) -> AuthResult:
        """
        使用者登入

        Args:
            username: 使用者名稱
            password: 明文密碼

        Returns:
            AuthResult: 認證結果，包含使用者資訊與 Token

        Raises:
            AuthenticationError: 帳號或密碼錯誤
            UserInactiveError: 使用者已停用
        """
        # 驗證憑證
        user = self._user_service.get_by_username(username)

        if not user:
            raise AuthenticationError("帳號或密碼錯誤")

        if not user.is_active:
            raise UserInactiveError("此帳號已停用，請聯繫管理員")

        # 驗證密碼
        from src.utils.password import verify_password
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("帳號或密碼錯誤")

        # 更新最後登入時間
        self._user_service.update_last_login(user.id)

        # 生成 Token
        access_token = self._jwt_handler.create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            department=user.department
        )

        refresh_token = self._jwt_handler.create_refresh_token(user_id=user.id)

        return AuthResult(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token
        )

    def refresh_token(self, refresh_token: str) -> TokenRefreshResult:
        """
        刷新 Access Token

        Args:
            refresh_token: Refresh Token

        Returns:
            TokenRefreshResult: 新的 Access Token

        Raises:
            InvalidTokenError: Token 無效或過期
            UserInactiveError: 使用者已停用
        """
        # 驗證 Refresh Token
        if not self._jwt_handler.is_refresh_token(refresh_token):
            raise InvalidTokenError("無效的 Refresh Token")

        try:
            payload = self._jwt_handler.verify_token(refresh_token)
        except Exception:
            raise InvalidTokenError("Refresh Token 已過期或無效")

        # 取得使用者
        user_id = int(payload.get("sub"))
        user = self._user_service.get_by_id(user_id)

        if not user:
            raise InvalidTokenError("使用者不存在")

        if not user.is_active:
            raise UserInactiveError("此帳號已停用")

        # 生成新的 Access Token
        access_token = self._jwt_handler.create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            department=user.department
        )

        return TokenRefreshResult(access_token=access_token)

    def verify_access_token(self, access_token: str) -> User:
        """
        驗證 Access Token 並取得使用者

        Args:
            access_token: Access Token

        Returns:
            User: 使用者物件

        Raises:
            InvalidTokenError: Token 無效或過期
            UserInactiveError: 使用者已停用
        """
        # 驗證是否為 Access Token
        if not self._jwt_handler.is_access_token(access_token):
            raise InvalidTokenError("無效的 Access Token")

        try:
            payload = self._jwt_handler.verify_token(access_token)
        except Exception:
            raise InvalidTokenError("Access Token 已過期或無效")

        # 取得使用者
        user_id = int(payload.get("sub"))
        user = self._user_service.get_by_id(user_id)

        if not user:
            raise InvalidTokenError("使用者不存在")

        if not user.is_active:
            raise UserInactiveError("此帳號已停用")

        return user

    def logout(self, access_token: str) -> bool:
        """
        使用者登出

        注意：由於 JWT 是無狀態的，這裡只是驗證 Token 有效性。
        實際的登出行為由前端清除 Token 完成。

        如果需要實作 Token 黑名單，可以在這裡擴充。

        Args:
            access_token: Access Token

        Returns:
            bool: 是否成功
        """
        # 驗證 Token 有效性（可選）
        try:
            self.verify_access_token(access_token)
        except (InvalidTokenError, UserInactiveError):
            pass  # 即使 Token 無效也允許「登出」

        # TODO: 如果需要，可以在這裡將 Token 加入黑名單
        # 例如：將 Token 的 jti 存入 Redis，設定過期時間與 Token 剩餘時間相同

        return True

    def get_current_user_from_token(self, access_token: str) -> dict:
        """
        從 Token 取得當前使用者資訊

        Args:
            access_token: Access Token

        Returns:
            dict: 使用者資訊

        Raises:
            InvalidTokenError: Token 無效
        """
        user = self.verify_access_token(access_token)

        return {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        }
