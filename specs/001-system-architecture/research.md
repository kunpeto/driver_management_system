# Research Document: 001-system-architecture

**Feature**: 司機員管理系統整體架構
**Date**: 2026-01-28
**Status**: Completed

## Overview

本文件記錄 Phase 0 技術選型研究的結果，解決實作計畫中標記為 "NEEDS CLARIFICATION" 的技術問題。

---

## 1. Vue.js 3 + GitHub Pages 部署最佳實踐

### Decision
使用 **Vue Router with createWebHistory** + **404.html 重定向技巧** + **Vite base URL 配置**

### Rationale
GitHub Pages 是靜態網站託管服務，不支援 SPA 路由的伺服器端路由。當使用者直接存取 `/employees` 時，GitHub Pages 會返回 404 錯誤。

**解決方案**：
1. **404.html 重定向**：建立自訂 404.html，使用 JavaScript 將請求重定向回 index.html，並保留原始路徑
2. **Vite base URL**：設定 `vite.config.js` 中的 `base: '/driver_management_system/'`，確保資源路徑正確
3. **Vue Router 配置**：使用 `createWebHistory(import.meta.env.BASE_URL)`

### Implementation Details

**vite.config.js**:
```javascript
export default defineConfig({
  plugins: [vue()],
  base: '/driver_management_system/',
  server: {
    port: 5173,
    host: true
  }
})
```

**404.html** (根據 [spa-github-pages](https://github.com/rafgraph/spa-github-pages)):
```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Single Page Apps for GitHub Pages</title>
    <script type="text/javascript">
      var pathSegmentsToKeep = 1;
      var l = window.location;
      l.replace(
        l.protocol + '//' + l.hostname + (l.port ? ':' + l.port : '') +
        l.pathname.split('/').slice(0, 1 + pathSegmentsToKeep).join('/') + '/?/' +
        l.pathname.slice(1).split('/').slice(pathSegmentsToKeep).join('/').replace(/&/g, '~and~') +
        (l.search ? '&' + l.search.slice(1).replace(/&/g, '~and~') : '') +
        l.hash
      );
    </script>
  </head>
  <body>
  </body>
</html>
```

**index.html** (加入重定向處理腳本):
```html
<script type="text/javascript">
  (function(l) {
    if (l.search[1] === '/' ) {
      var decoded = l.search.slice(1).split('&').map(function(s) {
        return s.replace(/~and~/g, '&')
      }).join('?');
      window.history.replaceState(null, null,
          l.pathname.slice(0, -1) + decoded + l.hash
      );
    }
  }(window.location))
</script>
```

### Alternatives Considered
- **createWebHashHistory**：使用 `#/` 路徑（例如 `/#/employees`），不需要 404.html 處理，但 URL 不美觀，且不利於 SEO

### References
- https://github.com/rafgraph/spa-github-pages
- https://vitejs.dev/guide/static-deploy.html#github-pages

---

## 2. FastAPI CORS 設定（本機 API → GitHub Pages）

### Decision
使用 **CORSMiddleware** 允許 GitHub Pages 域名與本機開發域名

### Rationale
前端部署於 GitHub Pages（`https://username.github.io`），需要跨域呼叫本機 API（`http://localhost:8001`）。瀏覽器的同源政策（Same-Origin Policy）會阻止此類請求，需要在本機 API 設定 CORS。

### Implementation Details

**backend-local/src/main.py**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Driver Management System - Local API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.github.io",          # 允許所有 GitHub Pages 子域名
        "http://localhost:5173",         # 允許本機開發伺服器
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],                 # 允許所有 HTTP 方法
    allow_headers=["*"],                 # 允許所有 Headers
)
```

### Security Considerations
1. **無需認證**：本機 API 不處理敏感資料（僅檔案生成），無需 JWT 認證
2. **localhost 限制**：本機 API 僅監聽 `127.0.0.1`，外部網路無法存取
3. **功能限制**：本機 API 不存取資料庫，降低安全風險

### Alternatives Considered
- **Nginx 反向代理**：過於複雜，不適合桌面應用場景
- **僅允許特定 GitHub Pages URL**：需要硬編碼使用者的 GitHub username，缺乏彈性

### References
- https://fastapi.tiangolo.com/tutorial/cors/
- https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS

---

## 3. TiDB 連線池最佳化

### Decision
使用 **SQLAlchemy QueuePool** with `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`, `pool_recycle=3600`

### Rationale
- **TiDB Serverless 限制**：免費版每日連線數限制為 5000 次
- **Render 免費版限制**：512MB RAM，連線池不能過大
- **連線穩定性**：TiDB 會自動斷開閒置連線，需要 `pool_pre_ping` 檢測

### Implementation Details

**backend-cloud/src/core/database.py**:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,               # 常駐連線數（低於 Render RAM 限制）
    max_overflow=10,           # 最大額外連線數
    pool_pre_ping=True,        # 每次從連線池取出連線時檢測是否仍有效
    pool_recycle=3600,         # 1小時回收連線（避免 TiDB 自動斷線）
    echo=False,                # 生產環境關閉 SQL 日誌
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """依賴注入：取得資料庫 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Performance Metrics
- **預期連線數**：5 (pool_size) + 10 (max_overflow) = 最多 15 個併發連線
- **記憶體使用**：每個連線約 10-20MB，總計 150-300MB（符合 Render 512MB 限制）
- **每日連線數**：假設平均每個請求使用 1 個連線，持續 0.5 秒，每日可處理約 8,640,000 次請求（遠超實際需求）

### Alternatives Considered
- **NullPool**：每次請求建立新連線，效能差且容易超過連線數限制
- **更大的 pool_size**：可能超過 Render RAM 限制

### References
- https://docs.sqlalchemy.org/en/20/core/pooling.html
- https://docs.pingcap.com/tidb/stable/connection-pooling

---

## 4. PyInstaller 打包本機 API + 托盤程式

### Decision
使用 **PyInstaller --onefile --noconsole** 打包 FastAPI + pystray 為單一可執行檔

### Rationale
- **使用者友善**：單一 .exe 檔案，無需安裝 Python 環境
- **隱藏 CMD 視窗**：`--noconsole` 避免黑色命令列視窗干擾使用者
- **托盤程式整合**：使用 `pystray` 提供系統托盤圖示與右鍵選單

### Implementation Details

**backend-local/build.spec**:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['desktop/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('desktop/icon.ico', '.'),
        ('src', 'src'),  # 包含 FastAPI 源碼
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DriverManagementAPI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 隱藏 CMD 視窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='desktop/icon.ico'
)
```

**desktop/main.py**:
```python
import subprocess
import sys
import os
from pystray import Icon, Menu, MenuItem
from PIL import Image

class DriverManagementTray:
    def __init__(self):
        self.api_process = None
        self.icon = None

    def start_api(self, icon, item):
        """啟動 FastAPI"""
        if self.api_process is None:
            # 使用 subprocess 啟動 FastAPI（隱藏視窗）
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            self.api_process = subprocess.Popen(
                [sys.executable, '-m', 'uvicorn', 'src.main:app', '--host', '127.0.0.1', '--port', '8001'],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

    def stop_api(self, icon, item):
        """停止 FastAPI"""
        if self.api_process:
            self.api_process.terminate()
            self.api_process = None

    def quit_app(self, icon, item):
        """結束程式"""
        self.stop_api(icon, item)
        icon.stop()

    def run(self):
        # 載入托盤圖示
        image = Image.open("icon.ico")
        menu = Menu(
            MenuItem('啟動 API', self.start_api),
            MenuItem('停止 API', self.stop_api),
            MenuItem('結束程式', self.quit_app)
        )
        self.icon = Icon("DriverManagementAPI", image, "司機員管理系統 API", menu)
        self.icon.run()

if __name__ == '__main__':
    app = DriverManagementTray()
    app.run()
```

**打包命令**:
```bash
pyinstaller --onefile --noconsole --icon=desktop/icon.ico desktop/main.py
```

### Known Issues & Solutions
- **Issue**: FastAPI 依賴複雜，PyInstaller 可能遺漏模組
  **Solution**: 使用 `hiddenimports` 明確指定 `uvicorn` 相關模組

- **Issue**: 打包後檔案過大（> 50MB）
  **Solution**: 使用 `upx=True` 壓縮可執行檔

### Alternatives Considered
- **cx_Freeze**：功能類似，但 PyInstaller 社群支援更好
- **Nuitka**：編譯為原生機器碼，但編譯時間長且相容性問題多

### References
- https://pyinstaller.org/en/stable/
- https://github.com/moses-palmer/pystray

---

## 5. JWT Token 儲存策略（前端）

### Decision
使用 **localStorage 儲存 JWT Token** + **Axios interceptor 自動附加 Token** + **短期 Token (1 小時)**

### Rationale
**為何使用 localStorage 而非 Cookie？**
- 前端為 SPA（Single Page Application），無法設定 HttpOnly Cookie（需要後端設定）
- GitHub Pages 為靜態網站託管，無法執行伺服器端邏輯
- LocalStorage 允許前端完全控制 Token 生命週期

**安全性考量**：
1. **XSS 攻擊風險**：localStorage 可被 JavaScript 讀取，若網站存在 XSS 漏洞，Token 可能被竊取
   - **緩解措施**：實作 Content Security Policy (CSP)，禁止內聯腳本
   - **緩解措施**：使用短期 Token（1 小時過期）

2. **CSRF 攻擊風險**：不適用（Token 不會自動附加於請求）

### Implementation Details

**frontend/src/stores/auth.js**:
```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)

  function setAuth(accessToken, userData) {
    token.value = accessToken
    user.value = userData
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function clearAuth() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  return {
    token,
    user,
    isAuthenticated,
    setAuth,
    clearAuth
  }
})
```

**frontend/src/services/api.js** (Axios interceptor):
```javascript
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const cloudApi = axios.create({
  baseURL: import.meta.env.VITE_CLOUD_API_URL,
  timeout: 10000
})

// 請求攔截器：附加 JWT Token
cloudApi.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 響應攔截器：處理 401 錯誤（Token 過期）
cloudApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.clearAuth()
      router.push({ name: 'login' })
    }
    return Promise.reject(error)
  }
)
```

**backend-cloud JWT 配置**:
```python
# src/core/security.py
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 小時

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### Token Refresh Strategy
**Option 1: 靜默刷新（未實作）**
- 當 Token 即將過期時（例如剩餘 5 分鐘），自動呼叫 `/auth/refresh`
- 需要實作 Refresh Token 機制

**Option 2: 重新登入（當前實作）**
- Token 過期後，使用者需重新登入
- 簡單且安全，適合內部系統（使用者數量少）

### Alternatives Considered
- **SessionStorage**：瀏覽器關閉即清除，使用者體驗差
- **Cookie (SameSite=Strict)**：需要後端設定 Set-Cookie，不適合 GitHub Pages

### References
- https://auth0.com/blog/secure-browser-storage-the-facts/
- https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html

---

## Summary

所有 Phase 0 的技術選型研究已完成，關鍵決策如下：

| 議題 | 決策 | 風險等級 |
|------|------|---------|
| Vue.js + GitHub Pages 部署 | 使用 404.html 重定向 + Vite base URL | 低 |
| CORS 設定（本機 API） | CORSMiddleware 允許 GitHub Pages 與 localhost | 低 |
| TiDB 連線池 | QueuePool (pool_size=5, max_overflow=10) | 中 |
| PyInstaller 打包 | --onefile --noconsole + hiddenimports | 中 |
| JWT Token 儲存 | localStorage + 短期 Token (1 小時) | 中 |

**Phase 1 Prerequisites Met**: ✅ 所有技術選型已確定，可進入資料模型設計階段。
