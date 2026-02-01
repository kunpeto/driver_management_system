# 登入 404 錯誤排查與系統設定觀察報告

**日期**: 2026年2月1日
**專案**: Driver Management System
**狀態**: ✅ 已修正程式碼，待部署驗證

---

## 1. 問題描述
在實際操作網頁時，使用者回報點擊「登入」後頁面跳轉至 404 錯誤頁面。此問題通常涉及前端路由配置 (Router)、部署路徑 (Base URL) 以及後端 API 連線設定之間的整合。

## 2. 排查過程與發現

### 2.1 前端部署路徑 (Vite Config) **[關鍵原因]**
- **觀察**: 檢查 `frontend/vite.config.js` 時發現 `base` 參數設定為 `/driver_management_system/`（使用底線）。
- **問題**: GitHub Repository 的命名慣例通常為連字號（例如 `driver-management-system`）。若 GitHub Pages 的網址是 `.../driver-management-system/` 但程式碼預期的是 `.../driver_management_system/`，瀏覽器在載入資源或處理路由時會因路徑不匹配而回傳 404。
- **修正**: 已將 `base` 修改為標準的 `/driver-management-system/`。

### 2.2 SPA 路由處理 (404.html)
- **觀察**: `frontend/public/404.html` 包含用於 GitHub Pages 的 SPA 重定向腳本。
- **設定**: `pathSegmentsToKeep = 1`。
- **分析**: 此設定正確。它會保留網址中的第一層路徑（即 Repository 名稱），確保路由重定向時不會遺失專案根目錄路徑。

### 2.3 後端環境變數 (Render Dashboard)
- **觀察**: 檢查 `render_env_variables.txt` 與 `render.yaml`。
- **風險**: 若 Render 上的 `CORS_ALLOWED_ORIGINS` 未包含前端 GitHub Pages 的網址，瀏覽器會因為 CORS 策略而阻擋登入請求（雖然這通常回傳 Network Error 或 403/401，但也可能導致異常跳轉）。
- **待確認**: 需確認 Render Dashboard 上的 `GOOGLE_OAUTH_REDIRECT_URI` 是否與後端網域名稱完全一致。

---

## 3. 已執行的修正

針對 **前端程式碼** 進行了以下修改：

| 檔案位置 | 修改內容 | 原因 |
|:---|:---|:---|
| `frontend/vite.config.js` | `base: '/driver_management_system/'` <br>⬇️<br> `base: '/driver-management-system/'` | 修正 GitHub Pages 部署路徑不匹配導致的 404 錯誤。 |

---

## 4. 後續建議操作步驟

為了確保系統完全正常運作，請執行以下設定檢查：

### 步驟 1: 確認 GitHub Repository 名稱
請確認您的 GitHub 專案名稱確實為 **`driver-management-system`** (連字號)。
> 若您的專案名稱實際上是 `driver_management_system` (底線)，請告知，我們需將設定改回原狀。

### 步驟 2: 更新 Render 環境變數
請登入 Render Dashboard，檢查 `driver-management-api` 服務的 **Environment** 設定：

1. **CORS_ALLOWED_ORIGINS**:
   - 加入前端網址：`https://<您的GitHub帳號>.github.io`
   - 確保沒有多餘的斜線。

2. **API_BASE_URL**:
   - 確認為：`https://driver-management-system-jff0.onrender.com`

3. **GOOGLE_OAUTH_REDIRECT_URI**:
   - 確認為：`https://driver-management-system-jff0.onrender.com/api/auth/google/callback`

### 步驟 3: 重新部署與驗證
1. 將修正後的程式碼 (`vite.config.js`) 推送 (Push) 至 GitHub。
2. 等待 GitHub Actions 完成前端部署。
3. 清除瀏覽器快取，重新進入登入頁面進行測試。

## 5. 架構連線圖 (參考)

```mermaid
graph LR
    User[使用者瀏覽器] -- 1. 存取頁面 --> GH[GitHub Pages (Frontend)]
    GH -- 2. 載入資源 (Base URL) --> User
    User -- 3. API 請求 (Login) --> Render[Render (Backend API)]
    Render -- 4. 驗證 (TiDB) --> DB[(TiDB Database)]
    Render -- 5. 回傳 Token --> User
    
    style GH fill:#f9f,stroke:#333,stroke-width:2px
    style Render fill:#bbf,stroke:#333,stroke-width:2px
    style User fill:#fff,stroke:#333,stroke-width:2px
```

若執行以上步驟後仍有問題，請提供瀏覽器 Console (F12) 的詳細錯誤訊息以便進一步分析。
