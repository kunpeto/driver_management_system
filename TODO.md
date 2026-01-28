# 待辦事項

**最後更新**: 2026-01-28 20:15

---

## 🔴 高優先級（明天必做）

### Phase 2: Foundational - 認證與授權

1. **T016: TokenEncryption 類別**
   - 檔案：`backend/src/utils/encryption.py`
   - 實作 Fernet 加密/解密工具
   - 用於加密 OAuth refresh_token

2. **T019: JWT 工具類別**
   - 檔案：`backend/src/utils/jwt.py`
   - 生成、驗證、解析 Token
   - payload 包含 user_id, role, department

3. **T020: 密碼雜湊工具**
   - 檔案：`backend/src/utils/password.py`
   - bcrypt 加密（成本因子 12）
   - 密碼驗證函數

4. **T021: 認證中間件**
   - 檔案：`backend/src/middleware/auth.py`
   - JWT Token 驗證
   - 從 Header 提取 Bearer Token

5. **T022: 權限檢查中間件**
   - 檔案：`backend/src/middleware/permission.py`
   - 角色驗證（Admin, Staff, Manager）
   - 部門權限控制

---

## 🟡 中優先級（本週完成）

### 資料模型

- [ ] User 模型（id, username, password_hash, role, department）
- [ ] Employee 模型（employee_id, employee_name, current_department, ...）
- [ ] SystemSetting 模型（key, value, department）
- [ ] GoogleOAuthToken 模型（department, encrypted_refresh_token）

### API 端點

- [ ] POST /api/auth/login - 登入
- [ ] POST /api/auth/logout - 登出
- [ ] GET /api/auth/me - 取得當前使用者

### 前端

- [ ] 登入頁面
- [ ] 首頁 Layout
- [ ] 側邊選單

---

## 🟢 低優先級（可延後）

### 文件

- [ ] API 文件（OpenAPI 自動生成）
- [ ] 部署指南
- [ ] 使用者手冊

### 測試

- [ ] 單元測試框架設定
- [ ] 整合測試框架設定
- [ ] CI/CD 設定（GitHub Actions）

### 優化

- [ ] 日誌結構化
- [ ] 錯誤處理統一
- [ ] CORS 精細化配置

---

## 📋 待釐清事項

### PC-002: 安坑班表結構
- **狀態**: 待釐清
- **影響**: Phase 6 班表同步
- **行動**: 取得安坑 Google Sheets 存取權限後確認

### PC-003: 勤務表詳細結構
- **狀態**: 部分釐清
- **影響**: Phase 9 駕駛競賽
- **行動**: 已確認淡海勤務表有 48 個分頁（每天一個）

### PC-004: 報表需求細節
- **狀態**: 待釐清
- **影響**: Phase 9-10 報表功能
- **行動**: 與主管確認報表格式

---

## 🔧 技術債務

1. **Import 路徑一致性**
   - 根目錄執行用 `backend.src.xxx`
   - backend 目錄執行用 `src.xxx`
   - 考慮統一使用相對 import

2. **非同步資料庫**
   - 目前使用同步方式
   - 考慮引入 asyncmy 或 aiomysql

3. **測試覆蓋率**
   - 目前無測試
   - Phase 2 後應補充關鍵測試

---

## 📅 明天開發計畫

### 2026-01-29 開發目標

**上午**
1. 建立認證相關工具（T016, T019, T020）
2. 建立認證中間件（T021, T022）

**下午**
3. 建立 User 資料模型
4. 建立登入/登出 API
5. 測試認證流程

**晚上**
6. 建立 Employee 資料模型
7. 建立員工 CRUD API
8. 測試權限控制

---

## 📝 備忘錄

### 環境變數已設定（.env）
- ✅ TiDB 連線資訊
- ✅ API_SECRET_KEY
- ⏳ ENCRYPTION_KEY（需產生）
- ⏳ Google Service Account（需 Base64 編碼）

### 淡海 Google 服務 ID
```
勤務表: 1HKGd2LzS8p93UvGiOfcePw4Tn_JoJyLbkQKCLtfnnE4
班表: 15Y6H2GKFJQUUJvHkoBCmT4fW4HxET9qJWZi4sX08pCQ
Drive: 1NhgiXcYQ5NTRQzmHgLSLqU8M8Ysf3-18
```

### 憑證檔案位置（不上傳 Git）
```
不需git的資料/credentials.json          # OAuth 2.0
不需git的資料/google_sheets_api_credentials .json  # Service Account
```

### 啟動指令
```bash
# 後端（從 backend 目錄）
cd backend
../venv/Scripts/python -m uvicorn src.main:app --reload --port 8000

# 前端
cd frontend
npm run dev
```

---

## ✅ 已完成（今日）

- [x] 規格文件審查與修正
- [x] PC-001 駕駛競賽公式釐清
- [x] 開發環境設定
- [x] TiDB 連線測試
- [x] Google Sheets 存取測試
- [x] Phase 0 專案架構建立
- [x] Render 部署配置
- [x] Git commit 並 push
