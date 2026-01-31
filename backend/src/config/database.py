"""
資料庫連線配置
對應 tasks.md T012: 建立 TiDB 連線配置工具

重要說明（Gemini Review 2026-01-28）：
- 使用同步 Session 配合 FastAPI 的 ThreadPool 機制
- 所有使用 get_db 的路由應宣告為 def（非 async def）
- FastAPI 會自動將同步路由放入 ThreadPool 執行，避免阻塞 Event Loop
"""

from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import get_settings

settings = get_settings()


# ============================================================
# 同步引擎
# ============================================================
# 說明：TiDB SSL 需要使用 pymysql，而 aiomysql 不完整支援 TiDB SSL
# 因此使用同步引擎，透過 FastAPI ThreadPool 機制處理併發
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


# ============================================================
# FastAPI 依賴注入
# ============================================================
def get_db() -> Generator[Session, None, None]:
    """
    取得資料庫 Session（FastAPI 依賴注入）

    重要：使用此依賴的路由函數應宣告為 def（非 async def）
    這樣 FastAPI 會自動將整個路由放入 ThreadPool 執行，
    避免同步資料庫操作阻塞主執行緒的 Event Loop。

    正確用法：
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):  # 注意是 def 不是 async def
            return db.query(User).all()

    錯誤用法（會阻塞 Event Loop）：
        @app.get("/users")
        async def get_users(db: Session = Depends(get_db)):  # 不要使用 async def
            return db.query(User).all()

    Yields:
        Session: SQLAlchemy 資料庫 Session
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 別名，保持向後相容
get_sync_db = get_db


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
    初始化資料庫（建立所有資料表並建立預設管理員帳號）

    應在應用程式啟動時呼叫
    """
    from src.models.base import Base

    # 導入所有模型以註冊到 Base.metadata
    from src.models.system_setting import SystemSetting  # noqa: F401
    from src.models.google_oauth_token import GoogleOAuthToken  # noqa: F401

    Base.metadata.create_all(bind=sync_engine)

    # 建立預設管理員帳號（如果不存在）
    _create_default_admin()


def _create_default_admin():
    """
    建立預設管理員帳號（如果不存在）

    預設帳號：admin / admin123
    """
    from src.models.user import User
    from src.utils.password import hash_password

    db = SyncSessionLocal()
    try:
        # 檢查是否已有 admin 帳號
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("[INFO] 預設管理員帳號已存在，跳過建立")
            return

        # 檢查是否有任何使用者（避免重複建立）
        user_count = db.query(User).count()
        if user_count > 0:
            print(f"[INFO] 系統中已有 {user_count} 個使用者，跳過建立預設管理員")
            return

        # 建立預設管理員帳號
        admin_user = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            display_name="系統管理員",
            role="admin",
            department=None,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("[OK] 預設管理員帳號建立成功 (admin / admin123)")
        print("[WARN] 請登入後立即修改預設密碼！")

    except Exception as e:
        print(f"[ERROR] 建立預設管理員帳號失敗: {e}")
        db.rollback()
    finally:
        db.close()
