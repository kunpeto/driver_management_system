"""
資料庫連線配置
對應 tasks.md T012: 建立 TiDB 連線配置工具
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import get_settings

settings = get_settings()


# ============================================================
# 同步引擎（用於資料遷移、初始化等）
# ============================================================
sync_engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=not settings.is_production,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


def get_sync_db() -> Session:
    """取得同步資料庫 Session（Generator）"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# 非同步引擎（用於 FastAPI 請求處理）
# ============================================================
# 注意：aiomysql 不支援 TiDB SSL，因此使用同步引擎的 run_sync
# 若需要非同步，可考慮使用 asyncmy 或其他方案

# 暫時使用同步方式，後續可優化為非同步
async def get_db() -> AsyncGenerator[Session, None]:
    """取得資料庫 Session（FastAPI 依賴注入）"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# 資料庫工具函數
# ============================================================
def check_database_connection() -> dict:
    """
    檢查資料庫連線狀態

    Returns:
        dict: 包含連線狀態、版本、資料庫名稱等資訊
    """
    try:
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()

            result = conn.execute(text("SELECT DATABASE()"))
            database = result.scalar()

            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]

        return {
            "status": "connected",
            "version": version,
            "database": database,
            "table_count": len(tables),
            "tables": tables
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def init_database():
    """
    初始化資料庫（建立所有資料表）

    應在應用程式啟動時呼叫
    """
    from src.models.base import Base

    # 導入所有模型以註冊到 Base.metadata
    # 這些導入會在模型建立後補充
    # from backend.src.models.user import User
    # from backend.src.models.employee import Employee
    # ...

    Base.metadata.create_all(bind=sync_engine)
