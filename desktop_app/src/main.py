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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    print(f"[*] 本機 API 啟動中...")
    print(f"[*] 版本: {APP_VERSION}")
    print(f"[*] 監聽: http://127.0.0.1:8001")

    yield

    # 關閉時執行
    print("[*] 本機 API 關閉中...")


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
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": APP_VERSION,
        "services": {
            "api": "running"
        }
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
# API 路由（後續任務會新增）
# ============================================================

# TODO: T094 PDF 處理 API
# TODO: T095 條碼生成 API


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
