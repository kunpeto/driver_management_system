"""
SQLAlchemy Base 模型
對應 tasks.md T014: 建立資料庫 Base 模型
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    所有模型的基礎類別

    提供：
    - 自動 id 主鍵
    - 自動 created_at 和 updated_at 時間戳
    - 統一的 __repr__ 方法
    """

    # 型別註解對應
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }

    def __repr__(self) -> str:
        """模型的字串表示"""
        columns = ", ".join(
            f"{col.name}={getattr(self, col.name)!r}"
            for col in self.__table__.columns
            if col.name in ("id", "name", "employee_id", "username")
        )
        return f"<{self.__class__.__name__}({columns})>"

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典"""
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }


class TimestampMixin:
    """
    時間戳 Mixin

    提供 created_at 和 updated_at 欄位
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
