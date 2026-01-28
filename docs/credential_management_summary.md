# 憑證管理策略更新總結

**更新日期**: 2026-01-28
**版本**: v1.4
**相關文件**: `specs/001-system-architecture/spec.md`

---

## 📋 變更概要

根據專案需求，系統需使用兩種不同類型的 Google API 憑證：

1. **服務帳戶憑證（Service Account）** - 自動同步 Google Sheets
2. **OAuth 2.0 憑證** - 使用者授權上傳檔案到 Google Drive

本次更新完整規範了這兩種憑證的安全儲存與使用策略。

---

## 🔐 憑證類型對比

| 項目 | 服務帳戶憑證 | OAuth 憑證 |
|------|------------|-----------|
| **用途** | 班表、勤務表自動同步 | 檔案上傳到 Google Drive |
| **格式** | JSON（含 private_key） | Client ID/Secret + 令牌 |
| **權限** | `spreadsheets.readonly` | `drive.file` |
| **儲存位置** | Render 環境變數（Base64） | TiDB 加密欄位 |
| **風險等級** | 🔴 高（永久有效） | 🟡 中（可撤銷） |

---

## 📦 儲存方案

### 雲端後端（Render FastAPI）

#### ✅ 服務帳戶憑證

**儲存方式**: 環境變數（Base64 編碼）

```bash
# Render 環境變數設定
TANHAE_GOOGLE_SERVICE_ACCOUNT_JSON=eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsIC...
ANPING_GOOGLE_SERVICE_ACCOUNT_JSON=eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsIC...
```

**編碼指令**（Windows PowerShell）:
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("tanhae-service-account.json"))
```

**編碼指令**（Python）:
```python
import base64
with open("tanhae-service-account.json", "rb") as f:
    print(base64.b64encode(f.read()).decode())
```

**優點**:
- ✅ 不存在於程式碼或檔案系統
- ✅ Render 平台已加密環境變數
- ✅ 部署時自動載入

---

#### ✅ OAuth 令牌

**儲存方式**: 資料庫加密欄位

**新增資料表**:
```sql
CREATE TABLE google_oauth_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    department ENUM('淡海', '安坑') UNIQUE NOT NULL,
    encrypted_refresh_token BLOB NOT NULL,
    encrypted_access_token BLOB,
    access_token_expires_at DATETIME,
    authorized_user_email VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**加密方式**: Fernet 對稱加密（需環境變數 `ENCRYPTION_KEY`）

**產生加密金鑰**:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**優點**:
- ✅ refresh_token 加密後儲存
- ✅ 即使資料庫洩露，無金鑰無法解密
- ✅ 支援多部門獨立授權

---

### 本機桌面應用（localhost:8000）

#### ✅ OAuth 令牌

**儲存方式**: 本機加密檔案

**檔案位置**:
```
C:\Users\<username>\.driver_management_system\
├── .key                  # 本機加密金鑰（600 權限）
└── tokens.encrypted      # 加密的 OAuth 令牌（600 權限）
```

**優點**:
- ✅ 令牌不存在於明文檔案
- ✅ 加密金鑰與令牌分離
- ✅ 檔案權限限制（僅擁有者可讀寫）
- ✅ 桌面應用關閉時令牌仍保留

---

## 🛡️ 安全規範

### 🚫 絕對禁止

```python
# ❌ 禁止 1：硬編碼憑證
SERVICE_ACCOUNT = {"private_key": "-----BEGIN PRIVATE KEY-----..."}

# ❌ 禁止 2：明文儲存在 .env 並提交到 Git
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# ❌ 禁止 3：未加密的資料庫欄位
refresh_token = Column(String(500))  # 明文儲存

# ❌ 禁止 4：將憑證寫入日誌
logger.info(f"Service account: {credentials}")

# ❌ 禁止 5：在 GitHub 中儲存憑證檔案
git add tanhae-service-account.json
```

### ✅ 必須遵守

**開發階段**:
- [x] `.env` 檔案已加入 `.gitignore`
- [x] 提供 `.env.example` 範本（密碼留空）
- [x] 服務帳戶僅授予最小必要權限（唯讀 Sheets）
- [x] OAuth 應用僅請求必要 scopes（`drive.file`）

**部署階段**:
- [ ] Render 環境變數已設定所有必要憑證
- [ ] `ENCRYPTION_KEY` 已產生並設定
- [ ] TiDB 連線使用 SSL/TLS 加密

**運行階段**:
- [ ] 定期輪換服務帳戶金鑰（建議每 90 天）
- [ ] 監控異常 API 使用（偵測憑證洩露）
- [ ] 日誌不記錄敏感資訊

---

## 🔄 OAuth 授權流程

### 初次授權（管理員操作）

```
管理員 → 網頁應用：進入「Google 服務設定」
網頁應用 → 雲端 API：GET /api/google/auth-url?department=淡海
雲端 API → Google：產生授權 URL
Google → 管理員：顯示授權畫面
管理員 → Google：同意授權
Google → 雲端 API：/api/auth/google/callback?code=xxx
雲端 API → Google：用 code 換取 refresh_token
雲端 API → TiDB：加密 refresh_token 並儲存
雲端 API → 網頁應用：授權成功
網頁應用 → 管理員：顯示「✓ Google Drive 已授權（淡海）」
```

### 檔案上傳時使用令牌

```
使用者 → 本機應用：點擊「上傳 PDF 到 Drive」
本機應用 → 雲端 API：POST /api/google/get-access-token?department=淡海
雲端 API → TiDB：讀取 encrypted_refresh_token
雲端 API → TiDB：解密 refresh_token
雲端 API → Google：用 refresh_token 換取 access_token
Google → 雲端 API：返回 access_token（有效期 1 小時）
雲端 API → 本機應用：返回 access_token
本機應用 → Google Drive：上傳檔案（使用 access_token）
Google Drive → 本機應用：上傳成功，返回檔案 URL
本機應用 → 使用者：顯示「✓ 上傳成功」
```

---

## 📝 更新的檔案清單

### 規格文件

1. **`specs/001-system-architecture/spec.md`**
   - 新增 "Credential Management & Security" 章節
   - 新增 `GoogleOAuthToken` 資料模型
   - 新增 FR-065 ~ FR-074 功能需求
   - 新增 SC-019 ~ SC-023 成功標準
   - 更新 Phase 0 與 Phase 2 實作內容

### 設定檔

2. **`.env.example`**
   - 重寫環境變數範本
   - 加入詳細的註解與說明
   - 新增服務帳戶憑證編碼指南
   - 新增 OAuth 憑證配置
   - 新增 `ENCRYPTION_KEY` 配置

3. **`.gitignore`**
   - 新增 Google API 憑證檔案排除規則
   - 新增本機加密令牌檔案排除規則
   - 新增資料庫備份檔案排除規則

---

## 🎯 下一步行動

### Phase 0: 基礎架構（需實作的憑證管理功能）

1. **雲端後端加密工具**
   - [ ] 實作 `TokenEncryption` 類別（Fernet 加密/解密）
   - [ ] 實作服務帳戶憑證載入（Base64 解碼）
   - [ ] 建立 `GoogleOAuthToken` 資料模型

2. **本機桌面應用**
   - [ ] 實作 `DesktopCredentialManager` 類別
   - [ ] 實作本機加密檔案讀寫
   - [ ] 實作檔案權限控制（0o600）

3. **環境變數配置**
   - [ ] 產生 `ENCRYPTION_KEY`
   - [ ] 編碼服務帳戶 JSON 為 Base64
   - [ ] 在 Render 設定環境變數
   - [ ] 在本機建立 `.env` 檔案（從 `.env.example` 複製）

### Phase 2: Google 服務整合（需實作的 OAuth 功能）

1. **OAuth 授權端點**
   - [ ] 實作 `GET /api/google/auth-url`（產生授權 URL）
   - [ ] 實作 `GET /api/auth/google/callback`（接收授權碼）
   - [ ] 實作 `POST /api/google/get-access-token`（令牌刷新）

2. **前端授權介面**
   - [ ] 建立「Google 服務設定」頁面
   - [ ] 實作「授權 Google Drive」按鈕
   - [ ] 實作授權狀態顯示（✓ 已授權 / ✗ 未授權）

---

## 📚 參考資源

### 官方文件
- [Google Cloud - Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Google Identity - OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Cryptography - Fernet](https://cryptography.io/en/latest/fernet/)

### 相關規格
- `specs/001-system-architecture/spec.md` - 系統架構完整規格
- `.env.example` - 環境變數設定範本

---

## ✅ 檢查清單

在開始實作前，請確認以下項目：

- [ ] 已閱讀 `specs/001-system-architecture/spec.md` 的 "Credential Management & Security" 章節
- [ ] 已複製 `.env.example` 為 `.env`
- [ ] 已準備好淡海與安坑的 Google 服務帳戶 JSON 檔案
- [ ] 已在 Google Cloud Console 建立 OAuth 2.0 Client ID
- [ ] 已產生 `ENCRYPTION_KEY` 並設定到環境變數
- [ ] 已確認 `.gitignore` 包含所有憑證檔案排除規則
- [ ] 已了解 OAuth 授權流程與令牌刷新機制

---

**問題或建議？**
請在 GitHub Issues 中提出，或直接詢問開發團隊。
