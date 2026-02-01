"""
FastAPI 主程式
對應 tasks.md T023: 建立 FastAPI 主程式

Gemini Review 優化:
- 加入 Rate Limiting 異常處理（防止 OOM）
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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

    # 驗證生產環境設定
    config_warnings = settings.validate_production_settings()
    if config_warnings:
        print("\n⚠️  設定驗證警告:")
        for warning in config_warnings:
            print(f"   {warning}")
        print()
        # 生產環境有嚴重問題時，建議中斷啟動
        if settings.is_production and any("CRITICAL" in w for w in config_warnings):
            print("🛑 生產環境存在嚴重設定問題，建議立即修正！")
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

    # 啟動定時任務排程器 (Phase 7)
    try:
        from src.tasks.scheduler import start_scheduler
        start_scheduler()
        print("[OK] 定時任務排程器已啟動")
    except Exception as e:
        print(f"[WARNING] 定時任務排程器啟動失敗: {e}")

    print("=" * 60)
    print(f"環境: {settings.api_environment}")
    print("=" * 60)

    yield

    # 關閉時執行
    print("=" * 60)
    print("司機員管理系統 - 雲端 API 關閉中...")

    # 停止定時任務排程器
    try:
        from src.tasks.scheduler import stop_scheduler
        stop_scheduler()
        print("[OK] 定時任務排程器已停止")
    except Exception as e:
        print(f"[WARNING] 定時任務排程器停止失敗: {e}")

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
# 允許的來源可透過環境變數 CORS_ALLOWED_ORIGINS 配置（以逗號分隔）
# 例如：CORS_ALLOWED_ORIGINS="https://kunpeto.github.io,https://custom-domain.com"
allowed_origins = settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Request-ID"],
)

# Rate Limiting 設置（Gemini Review P0: 防止 OOM）
from src.api.profiles import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================
# 顯式處理 CORS 預檢請求（解決 Render 冷啟動問題）
# ============================================================
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    """
    顯式處理所有 OPTIONS 請求

    解決 Render 免費服務冷啟動時 CORS 預檢失敗的問題
    動態讀取 CORS 設定，支援多個來源
    """
    from fastapi.responses import Response

    # 取得請求的 Origin
    origin = request.headers.get("origin", "")

    # 檢查是否在允許清單中
    if origin in allowed_origins:
        allow_origin = origin
    elif allowed_origins:
        # 預設使用第一個允許的來源
        allow_origin = allowed_origins[0]
    else:
        allow_origin = "*"

    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, X-Request-ID",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600",
        }
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
from src.api import (
    google_credentials_router,
    system_settings_router,
    employees_router,
    employee_transfers_router,
    employee_batch_router,
    auth_router,
    users_router,
    connection_status_router,
    schedules_router,
    sync_tasks_router,
    google_oauth_router,
    # Phase 9: 駕駛時數與競賽
    route_standard_time_router,
    driving_stats_router,
    driving_competition_router,
    # Phase 11: 履歷管理
    profiles_router,
    # Phase 12: 考核系統
    assessment_standards_router,
    assessment_records_router,
    # Phase 13: 差勤加分
    attendance_bonus_router,
)

# 系統設定 API
app.include_router(
    system_settings_router,
    prefix="/api/settings",
    tags=["System Settings"]
)

# Google 憑證驗證 API
app.include_router(
    google_credentials_router,
    prefix="/api/google",
    tags=["Google Credentials"]
)

# 員工管理 API
app.include_router(
    employees_router,
    prefix="/api/employees",
    tags=["Employees"]
)

# 員工調動 API（部分路由需要與員工路由整合）
app.include_router(
    employee_transfers_router,
    prefix="/api/employees",
    tags=["Employee Transfers"]
)

# 員工批次匯入/匯出 API
app.include_router(
    employee_batch_router,
    prefix="/api/employees",
    tags=["Employee Batch Operations"]
)

# 認證 API
app.include_router(
    auth_router,
    tags=["Authentication"]
)

# 使用者管理 API
app.include_router(
    users_router,
    tags=["Users"]
)

# 連線狀態 API
app.include_router(
    connection_status_router,
    tags=["Connection Status"]
)

# 班表管理 API (Phase 7)
app.include_router(
    schedules_router,
    tags=["Schedules"]
)

# 同步任務 API (Phase 7)
app.include_router(
    sync_tasks_router,
    tags=["Sync Tasks"]
)

# Google OAuth API (Phase 8)
app.include_router(
    google_oauth_router,
    tags=["Google OAuth"]
)

# 勤務標準時間 API (Phase 9)
app.include_router(
    route_standard_time_router,
    prefix="/api",
    tags=["Route Standard Times"]
)

# 駕駛時數統計 API (Phase 9)
app.include_router(
    driving_stats_router,
    prefix="/api",
    tags=["Driving Stats"]
)

# 駕駛競賽排名 API (Phase 9)
app.include_router(
    driving_competition_router,
    prefix="/api",
    tags=["Driving Competition"]
)

# 履歷管理 API (Phase 11)
app.include_router(
    profiles_router,
    prefix="/api/profiles",
    tags=["Profiles"]
)

# 考核標準 API (Phase 12)
app.include_router(
    assessment_standards_router,
    tags=["Assessment Standards"]
)

# 考核記錄 API (Phase 12)
app.include_router(
    assessment_records_router,
    tags=["Assessment Records"]
)

# 差勤加分 API (Phase 13)
app.include_router(
    attendance_bonus_router,
    tags=["Attendance Bonus"]
)


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
