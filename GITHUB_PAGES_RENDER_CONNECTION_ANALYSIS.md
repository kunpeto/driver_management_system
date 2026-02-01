# GitHub Pages 與 Render 後端連接分析報告

## 1. 執行摘要

經檢查 `.github/workflows/ci.yml`、`frontend/vite.config.js` 與後端 CORS 設定，發現一個**關鍵的環境變數名稱不一致**錯誤，這很可能是導致前端無法連接後端的主因。

此外，也針對 CORS 設定與 Render 環境變數提出了檢查建議，以確保連接的穩定性。

## 2. 關鍵錯誤分析

### 2.1 環境變數名稱不符 (CRITICAL)

- **前端程式碼**: `frontend/src/utils/api.js` 預期讀取 `import.meta.env.VITE_CLOUD_API_URL`。
- **CI/CD 設定**: `.github/workflows/ci.yml` 在建置階段注入的是 `VITE_API_URL`。

**影響**: 前端在 GitHub Pages 上運行時，`VITE_CLOUD_API_URL` 會是 `undefined`（或是 fallback 到程式碼中的預設值），導致無法正確發送請求到後端。

**證據**:
- `frontend/.env.example`: `VITE_CLOUD_API_URL=http://localhost:8000`
- `.github/workflows/ci.yml`:
  ```yaml
  env:
    VITE_API_URL: https://driver-management-system-jff0.onrender.com  # 錯誤的變數名稱
  ```

### 2.2 CORS 設定風險

- **後端邏輯**: `backend/src/config/settings.py` 只有在 `is_production` 為 `True` 時，才會將 `https://kunpeto.github.io` 加入允許清單。
- **風險**: 如果 Render 上的環境變數 `API_ENVIRONMENT` 未設定為 `production`，後端會預設為開發模式，僅允許 `localhost` 連線，導致 GitHub Pages 被 CORS 擋下。

## 3. 修正建議與步驟

### 步驟 1: 修正 GitHub Actions Workflow ✅ 已完成

已修改 `.github/workflows/ci.yml`，將環境變數名稱統一為 `VITE_CLOUD_API_URL`。

### 步驟 2: 確認 Render 環境變數

請登入 [Render Dashboard](https://dashboard.render.com/)，檢查該服務的 **Environment** 設定，確保包含以下變數：

| Key | Value | 用途 |
|-----|-------|------|
| `API_ENVIRONMENT` | `production` | 啟用生產環境模式與正確的 CORS 設定 |
| `CORS_ALLOWED_ORIGINS` | `https://kunpeto.github.io` | (選用) 明確指定允許的來源，覆蓋預設值 |

### 步驟 3: 驗證前端 API 客戶端

在 `frontend/src/utils/api.js` 中，目前的程式碼有 fallback 機制：

```javascript
const CLOUD_API_URL =
  import.meta.env.VITE_CLOUD_API_URL ||
  (import.meta.env.MODE === 'production'
    ? 'https://driver-management-system-jff0.onrender.com'
    : 'http://localhost:8000')
```

雖然有 fallback，但建議確保 CI 注入正確的變數，以便未來更改 URL 時不需修改程式碼。

## 4. 進階檢查 (如果上述修正後仍有問題)

若修正後仍無法連線，請檢查瀏覽器 Console (F12) 的錯誤訊息：

1.  **CORS Error**: 若看到 "Access-Control-Allow-Origin" 相關錯誤，請再次確認 Render 的 `API_ENVIRONMENT` 是否為 `production`。
2.  **404 Not Found**: 若 API 回傳 404，可能是 API 路徑前綴問題。目前後端路由大多包含 `/api` 前綴，請確認前端請求是否正確包含（目前看來前端 `API_BASE` 設定正確）。
3.  **Mixed Content**: 若看到 "blocked loading mixed active content"，表示前端 (HTTPS) 試圖呼叫 HTTP 的後端。請確認 `VITE_CLOUD_API_URL` 是以 `https://` 開頭。

## 5. 結論

請優先執行 **步驟 1**，這應能解決主要的連接問題。
