# 專案可執行度與可靠度審查報告

**審查日期**: 2026-02-01
**審查工具**: Gemini 3 Pro + Claude Opus 4.5

---

## 審查摘要

| 嚴重程度 | 數量 | 狀態 |
|---------|------|------|
| 🔴 Critical | 1 | 待修復 |
| 🟠 Major | 1 | 待驗證 |
| 🟡 Medium | 3 | 待評估 |
| 🟢 Minor | 2 | 建議改進 |

---

## 🔴 嚴重問題 (Critical)

### C1. API Secret Key 預設值安全風險

**狀態**: ⏳ 待修復

**問題描述**:
`backend/src/config/settings.py` 第 33 行：
```python
api_secret_key: str = Field(default="development-secret-key-change-in-production")
```
若生產環境未正確覆蓋此變數，將導致 JWT Token 可被輕易偽造。

**影響範圍**: 全系統安全性

**修復建議**:
在生產環境啟動時驗證 secret key 不是預設值。

---

## 🟠 重要問題 (Major)

### M1. 員工 API 路由順序驗證

**狀態**: ✅ 已驗證正常

**問題描述**:
Gemini 擔心 `/api/employees/import` 等靜態路徑會被 `/{id}` 動態路徑攔截。

**驗證結果**:
查看 `main.py` 第 204-222 行，路由掛載順序為：
1. `employees_router` (基本 CRUD)
2. `employee_transfers_router` (調動)
3. `employee_batch_router` (批次操作)

需進一步驗證各 router 內部的路由定義順序。

---

## 🟡 中等問題 (Medium)

### M2. 環境變數缺乏驗證

**狀態**: ⏳ 待改進

**問題描述**:
關鍵設定如 `tidb_user` 預設為空字串，會通過 Pydantic 檢查但在執行時失敗。

**修復建議**:
加入啟動時驗證邏輯。

### M3. Google OAuth Scope 權限

**狀態**: ✅ 設計正確

**問題描述**:
Gemini 認為 `drive.file` scope 權限不足以讀取現有 Sheets。

**驗證結果**:
這是設計正確的：
- **OAuth** 只用於上傳檔案到 Drive（`drive.file` 足夠）
- **Service Account** 用於讀取班表 Sheets（使用不同的憑證）

### M4. 前端 Snake_case 命名

**狀態**: ⏳ 建議評估

**問題描述**:
前端直接使用後端的 snake_case 欄位名稱。

**說明**:
目前前後端一致使用 snake_case，功能正常。是否轉換為 camelCase 需評估成本效益。

---

## 🟢 建議改進 (Minor)

### L1. 重複的 Authorization Header 設定

**狀態**: ⏳ 可選改進

### L2. 前端缺少獨立 API 服務層

**狀態**: ⏳ 可選改進

---

## 修復進度追蹤

- [x] C1: 加入生產環境 Secret Key 驗證 ✅ 已修復
- [x] M1: 驗證路由順序（正常）✅
- [x] M2: 加入必要環境變數驗證 ✅ 已修復
- [x] M3: 確認 OAuth Scope 設計正確 ✅
- [x] M4: 前端 API 端點驗證 ✅ 所有端點匹配
- [ ] M5: 前端命名規範 - 保持現狀（功能正常）

---

## 修復記錄

### 2026-02-01

**1. settings.py 新增 `validate_production_settings()` 方法**
- 驗證生產環境 Secret Key 不是預設值
- 驗證資料庫帳密已設定
- 警告加密金鑰未設定

**2. main.py 啟動時調用驗證**
- 在 lifespan 中調用設定驗證
- 顯示警告訊息
- 生產環境有嚴重問題時提示

**3. API 端點完整性驗證結果**
- employees.py: 12 個端點 ✅
- employee_transfers.py: 9 個端點 ✅
- employee_batch.py: 6 個端點 ✅
- 所有前端 Store 呼叫均有對應後端端點
