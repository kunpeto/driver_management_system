"""
本機 FastAPI 主程式
對應 tasks.md T032: 建立本機 FastAPI 主程式

功能：
- 本機 API 服務（localhost:8001）
- CORS 設定（允許 GitHub Pages）
- 健康檢查端點
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# 應用程式版本
APP_VERSION = "0.1.0"
BUILD_DATE = "2026-01-31"

# API 契約版本
API_CONTRACT_VERSION = "1.0.0"
MIN_BACKEND_VERSION = "1.0.0"
MAX_BACKEND_VERSION = "1.x.x"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    print(f"[*] 本機 API 啟動中...")
    print(f"[*] 版本: {APP_VERSION}")
    print(f"[*] API 契約版本: {API_CONTRACT_VERSION}")
    print(f"[*] 監聽: http://127.0.0.1:8001")

    # 檢查後端版本相容性
    _check_backend_on_startup()

    yield

    # 關閉時執行
    print("[*] 本機 API 關閉中...")


def _check_backend_on_startup():
    """
    啟動時檢查後端版本相容性

    注意：這是非阻塞檢查，即使後端不可達也允許桌面應用啟動。
    因為桌面應用可能在離線環境下使用某些功能。
    """
    try:
        from desktop_app.src.utils.backend_api_client import get_backend_client

        client = get_backend_client()
        result = client.check_backend_compatibility()

        if result.backend_reachable:
            if result.compatible:
                print(f"[✓] 後端版本檢查通過: {result.backend_version}")
            else:
                print(f"[!] 警告: {result.error_message}")
                print(f"[!] 部分功能可能無法正常運作")
        else:
            print(f"[!] 警告: 無法連接後端服務")
            print(f"[!] 需要後端連線的功能將無法使用")

    except Exception as e:
        print(f"[!] 版本檢查時發生錯誤: {e}")


# 建立 FastAPI 應用
app = FastAPI(
    title="司機員管理系統 - 本機 API",
    description="處理本機檔案操作（PDF、Word、條碼等）",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# CORS 設定
# 允許前端（GitHub Pages 和本機開發）存取
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.github.io",           # GitHub Pages
        "http://localhost:5173",          # Vite 開發伺服器
        "http://127.0.0.1:5173",
        "http://localhost:3000",          # 備用開發埠
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 健康檢查端點
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """根路徑"""
    return {
        "name": "司機員管理系統 - 本機 API",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    健康檢查

    API CONTRACT: CRITICAL
    CONSUMERS: 前端 Web 應用
    SINCE: 1.0.0

    警告：此端點被前端直接依賴
    任何破壞性變更都會導致前端無法正確檢測桌面應用狀態

    禁止的變更：
    - 移除回應欄位（status, timestamp, version, services）
    - 變更欄位類型
    - 變更 URL 路徑
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": APP_VERSION,
        "services": {
            "api": "running"
        }
    }


@app.get("/version", tags=["Health"])
async def get_version():
    """
    取得版本資訊

    API CONTRACT: STABLE
    SINCE: 1.0.0

    返回桌面應用的版本資訊、API 契約版本、支援功能列表。
    用於版本相容性檢查。
    """
    return {
        "app_name": "司機員管理系統 - 桌面應用",
        "version": APP_VERSION,
        "build_date": BUILD_DATE,
        "api_contract_version": API_CONTRACT_VERSION,
        "min_backend_version": MIN_BACKEND_VERSION,
        "max_backend_version": MAX_BACKEND_VERSION,
        "supported_features": [
            "pdf_scan",
            "pdf_split",
            "pdf_process",
            "barcode_generate"
        ],
        "contracted_endpoints": [
            {"path": "/health", "method": "GET", "protection_level": "CRITICAL"},
            {"path": "/api/pdf/scan", "method": "POST", "protection_level": "CRITICAL"},
            {"path": "/api/pdf/split", "method": "POST", "protection_level": "CRITICAL"},
            {"path": "/api/pdf/process", "method": "POST", "protection_level": "CRITICAL"},
            {"path": "/api/barcode/generate", "method": "POST", "protection_level": "CRITICAL"}
        ]
    }


@app.get("/health/credentials", tags=["Health"])
async def health_credentials():
    """憑證狀態檢查"""
    from desktop_app.src.utils.credential_manager import get_credential_manager

    manager = get_credential_manager()
    departments = manager.list_departments()

    status = {}
    for dept in ["淡海", "安坑"]:
        if dept in departments:
            expired = manager.is_token_expired(dept)
            status[dept] = {
                "has_token": True,
                "expired": expired,
                "status": "expired" if expired else "valid"
            }
        else:
            status[dept] = {
                "has_token": False,
                "status": "not_configured"
            }

    return {
        "status": "ok",
        "credentials": status
    }


# ============================================================
# API 路由
# ============================================================

from desktop_app.src.api.pdf_processor import router as pdf_router
from desktop_app.src.api.barcode_generator import router as barcode_router

app.include_router(pdf_router)
app.include_router(barcode_router)


# ============================================================
# 主程式入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )
