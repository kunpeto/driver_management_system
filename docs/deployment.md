# 部署指南

本文件說明如何將司機員管理系統部署到雲端環境。

---

## 目錄

1. [架構概覽](#架構概覽)
2. [環境需求](#環境需求)
3. [Render 部署](#render-部署)
4. [環境變數設定](#環境變數設定)
5. [TiDB Cloud 設定](#tidb-cloud-設定)
6. [Google API 設定](#google-api-設定)
7. [UptimeRobot 設定](#uptimerobot-設定)
8. [GitHub Pages 部署](#github-pages-部署)
9. [本機桌面應用](#本機桌面應用)
10. [常見問題](#常見問題)

---

## 架構概覽

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GitHub Pages  │────▶│   Render API    │────▶│   TiDB Cloud    │
│    (Frontend)   │     │   (Backend)     │     │   (Database)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Google APIs    │
                        │ (Sheets/Drive)  │
                        └─────────────────┘
                               ▲
                               │
┌─────────────────┐     ┌─────────────────┐
│   本機電腦      │────▶│  Desktop App    │
│   (Office 功能) │     │  (FastAPI)      │
└─────────────────┘     └─────────────────┘
```

---

## 環境需求

### 後端 (Render)
- Python 3.11+
- 512 MB RAM（最低）

### 前端 (GitHub Pages)
- Node.js 18+
- npm 或 pnpm

### 資料庫 (TiDB Cloud)
- TiDB Serverless（免費方案可用）
- MySQL 5.7 相容

### 本機應用
- Python 3.11+
- Windows 10/11
- Microsoft Office（用於文件生成）

---

## Render 部署

### 步驟 1: 建立 Web Service

1. 登入 [Render Dashboard](https://dashboard.render.com/)
2. 點擊 **New** → **Web Service**
3. 連接 GitHub 倉庫
4. 設定服務：

| 設定項目 | 值 |
|---------|---|
| Name | driver-management-api |
| Environment | Python 3 |
| Region | Singapore (東南亞) |
| Branch | main |
| Root Directory | backend |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn src.main:app --host 0.0.0.0 --port $PORT` |

### 步驟 2: 設定環境變數

在 Render Dashboard 的 **Environment** 分頁中設定以下變數（詳見[環境變數設定](#環境變數設定)）

### 步驟 3: 部署

1. 點擊 **Create Web Service**
2. 等待自動部署完成
3. 記下服務 URL（如 `https://driver-management-api.onrender.com`）

### 自動部署

每次推送到 `main` 分支時，Render 會自動重新部署。

---

## 環境變數設定

### 必要環境變數

```bash
# 資料庫連線（TiDB Cloud）
DATABASE_URL=mysql+pymysql://user:password@host:4000/database?ssl_verify_cert=true

# JWT 認證
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 加密金鑰（用於 OAuth Token 加密）
ENCRYPTION_KEY=your-fernet-encryption-key-base64

# Google API（Base64 編碼的 Service Account JSON）
GOOGLE_SERVICE_ACCOUNT_淡海=eyJwcm9qZWN0X2lkIjoi...
GOOGLE_SERVICE_ACCOUNT_安坑=eyJwcm9qZWN0X2lkIjoi...

# Google Sheets ID
GOOGLE_SHEETS_ID_淡海=1abc...
GOOGLE_SHEETS_ID_安坑=1xyz...

# 前端 URL（CORS 設定）
FRONTEND_URL=https://username.github.io

# 環境
ENVIRONMENT=production
DEBUG=false
```

### 可選環境變數

```bash
# 日誌等級
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=true

# 本機 API URL（用於桌面應用）
LOCAL_API_URL=http://localhost:8001

# 同步排程
SYNC_SCHEDULE_CRON=0 6 * * *
```

### 生成加密金鑰

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # 使用這個作為 ENCRYPTION_KEY
```

### 生成 JWT Secret

```python
import secrets
print(secrets.token_hex(32))  # 使用這個作為 JWT_SECRET_KEY
```

---

## TiDB Cloud 設定

### 步驟 1: 建立叢集

1. 登入 [TiDB Cloud](https://tidbcloud.com/)
2. 建立新的 **Serverless** 叢集
3. 選擇區域（建議 Singapore）
4. 設定叢集名稱

### 步驟 2: 取得連線資訊

1. 在叢集頁面點擊 **Connect**
2. 選擇 **Python (PyMySQL)**
3. 複製連線字串

### 步驟 3: 設定連線

連線字串格式：
```
mysql+pymysql://<user>:<password>@<host>:4000/<database>?ssl_verify_cert=true
```

### 步驟 4: 初始化資料庫

部署後執行資料庫初始化：

```bash
# 在 Render Shell 或本機執行
python scripts/init_database.py
```

---

## Google API 設定

### Service Account 設定（用於 Sheets 讀取）

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立或選擇專案
3. 啟用 **Google Sheets API**
4. 建立 **Service Account**
5. 下載 JSON 金鑰檔
6. 將 JSON 轉為 Base64：
   ```bash
   base64 -w 0 service-account.json
   ```
7. 將結果設為環境變數 `GOOGLE_SERVICE_ACCOUNT_淡海`

### OAuth 2.0 設定（用於 Drive 上傳）

1. 在 Google Cloud Console 建立 **OAuth 2.0 Client ID**
2. 設定授權重導向 URI：
   ```
   https://driver-management-api.onrender.com/api/auth/google/callback
   ```
3. 下載 Client Credentials JSON
4. 在系統設定頁面完成 OAuth 授權流程

### 共用試算表

將 Service Account 的 Email 加入 Google Sheets 的共用設定（至少需要「檢視者」權限）。

---

## UptimeRobot 設定

UptimeRobot 用於監控服務狀態並防止 Render 免費方案的冷啟動。

### 步驟 1: 建立帳號

1. 前往 [UptimeRobot](https://uptimerobot.com/)
2. 註冊免費帳號

### 步驟 2: 新增監控

1. 點擊 **Add New Monitor**
2. 設定：

| 設定項目 | 值 |
|---------|---|
| Monitor Type | HTTP(s) |
| Friendly Name | Driver Management API |
| URL | https://driver-management-api.onrender.com/health |
| Monitoring Interval | 5 minutes |

3. 選擇通知方式（Email、Telegram 等）
4. 儲存

### 健康檢查端點

系統提供以下健康檢查端點：

- `GET /health` - 基本健康檢查
- `GET /health/database` - 資料庫連線檢查
- `GET /health/google` - Google API 連線檢查

---

## GitHub Pages 部署

### 步驟 1: 建立 GitHub Actions

在 `.github/workflows/deploy.yml` 建立部署流程：

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Build
        working-directory: ./frontend
        run: npm run build
        env:
          VITE_API_URL: ${{ secrets.API_URL }}

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/dist
```

### 步驟 2: 設定 Repository Secrets

在 GitHub Repository Settings → Secrets 中新增：

| Secret | 值 |
|--------|---|
| API_URL | https://driver-management-api.onrender.com |

### 步驟 3: 啟用 GitHub Pages

1. 前往 Repository Settings → Pages
2. Source 選擇 **gh-pages** 分支
3. 儲存

---

## 本機桌面應用

### 安裝步驟

1. 下載最新版本的 Desktop App
2. 解壓縮到指定目錄
3. 建立 `.env` 檔案：

```bash
# 本機 API 設定
LOCAL_API_PORT=8001

# 雲端 API URL
CLOUD_API_URL=https://driver-management-api.onrender.com

# OAuth 設定
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

4. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```

5. 啟動應用：
   ```bash
   python -m uvicorn src.main:app --port 8001
   ```

### 開機自動啟動

建立 Windows 排程工作或捷徑放入啟動資料夾。

---

## 常見問題

### Q: Render 服務冷啟動很慢？

A: 免費方案在 15 分鐘無請求後會休眠。使用 UptimeRobot 每 5 分鐘發送請求可保持服務活躍。

### Q: 資料庫連線失敗？

A: 檢查以下項目：
1. DATABASE_URL 格式是否正確
2. TiDB Cloud 是否有設定允許的 IP（或設為允許所有）
3. SSL 設定是否正確

### Q: Google API 認證失敗？

A: 檢查以下項目：
1. Service Account JSON 是否正確轉為 Base64
2. Service Account 是否已加入 Sheets 共用
3. 是否已啟用相關 API

### Q: 前端無法連線後端？

A: 檢查以下項目：
1. CORS 設定是否包含前端網址
2. API URL 是否正確
3. 瀏覽器 Console 是否有錯誤訊息

### Q: 本機應用無法上傳檔案？

A: 檢查以下項目：
1. OAuth 是否已完成授權
2. Access Token 是否過期
3. Drive 資料夾權限是否正確

---

## 支援

如有問題，請提交 Issue 至 GitHub Repository。
