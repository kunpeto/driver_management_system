"""
User 使用者模型
對應 tasks.md T059: 建立 User 模型

使用者資料與認證資訊。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    使用者模型

    儲存使用者帳號、密碼雜湊、角色與部門資訊。

    屬性:
        id: 主鍵
        username: 使用者名稱（唯一）
        password_hash: 密碼雜湊（bcrypt）
        display_name: 顯示名稱
        email: 電子郵件（選填）
        role: 角色（admin, manager, staff）
        department: 所屬部門（淡海/安坑，admin 可為 null）
        is_active: 是否啟用
        last_login_at: 最後登入時間
        created_at: 建立時間
        updated_at: 更新時間
    """

    __tablename__ = "users"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 帳號資訊
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="使用者名稱"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密碼雜湊（bcrypt）"
    )

    # 基本資訊
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="顯示名稱"
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="電子郵件"
    )

    # 角色與權限
    role: Mapped[str] = mapped_column(
        Enum("admin", "manager", "staff", name="user_role"),
        nullable=False,
        default="staff",
        comment="角色：admin=管理員, manager=主管, staff=值班台人員"
    )

    department: Mapped[Optional[str]] = mapped_column(
        Enum("淡海", "安坑", name="department_enum"),
        nullable=True,
        comment="所屬部門（admin 可為 null）"
    )

    # 狀態
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否啟用"
    )

    # 登入追蹤
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="最後登入時間"
    )

    # 索引
    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_department", "department"),
        Index("ix_users_is_active", "is_active"),
        {"comment": "使用者資料表"},
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username!r}, role={self.role!r})>"
