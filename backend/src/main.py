"""
FastAPI 主程式
對應 tasks.md T023: 建立 FastAPI 主程式
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.database import check_database_connection, init_database
from src.config.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理

    啟動時：
    - 初始化資料庫連線
    - 建立資料表（如果不存在）

    關閉時：
    - 清理資源
    """
    # 啟動時執行
    print("=" * 60)
    print("司機員管理系統 - 雲端 API 啟動中...")
    print("=" * 60)

    # 檢查資料庫連線
    db_status = check_database_connection()
    if db_status["status"] == "connected":
        print(f"[OK] 資料庫連線成功")
        print(f"     版本: {db_status['version']}")
        print(f"     資料庫: {db_status['database']}")
        print(f"     資料表數量: {db_status['table_count']}")
    else:
        print(f"[ERROR] 資料庫連線失敗: {db_status.get('error')}")

    # 初始化資料庫（建立資料表）
    try:
        init_database()
        print("[OK] 資料庫初始化完成")
    except Exception as e:
        print(f"[ERROR] 資料庫初始化失敗: {e}")

    print("=" * 60)
    print(f"環境: {settings.api_environment}")
    print("=" * 60)

    yield

    # 關閉時執行
    print("=" * 60)
    print("司機員管理系統 - 雲端 API 關閉中...")
    print("=" * 60)


# 建立 FastAPI 應用程式
app = FastAPI(
    title="司機員管理系統 API",
    description="新北捷運輕軌營運處車務中心 - 司機員事件履歷與考核管理、駕駛時數管理系統",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# CORS 設定
# 允許 GitHub Pages 和本機開發存取
allowed_origins = [
    "http://localhost:3000",  # 本機 Vue 開發
    "http://localhost:5173",  # Vite 開發伺服器
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # GitHub Pages（部署後補充）
    # "https://your-username.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 健康檢查端點
# ============================================================
@app.get("/health", tags=["Health"])
async def health_check():
    """
    健康檢查端點

    用於 UptimeRobot 監控和負載均衡器健康檢查
    """
    return {"status": "healthy", "service": "driver-management-system"}


@app.get("/health/database", tags=["Health"])
async def database_health_check():
    """
    資料庫健康檢查端點

    返回資料庫連線狀態和基本資訊
    """
    return check_database_connection()


# ============================================================
# API 路由註冊
# ============================================================
# 這些路由會在建立後補充
# from backend.src.api import auth, employees, profiles, system_settings, ...
# app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
# app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
# ...


# ============================================================
# 根路由
# ============================================================
@app.get("/", tags=["Root"])
async def root():
    """API 根路由"""
    return {
        "message": "歡迎使用司機員管理系統 API",
        "version": "1.0.0",
        "docs": "/docs" if not settings.is_production else None,
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
    )
