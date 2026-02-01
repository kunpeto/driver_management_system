# 前後端整合與資料對接檢查報告

## 1. 總體評估

經過對核心模組（Employee, User/Auth）的程式碼審查，目前前後端的資料對接狀況**良好**。

- **命名慣例**：前後端統一使用 `snake_case` 進行 API 資料傳輸。
    - 後端 Pydantic 模型與 SQLAlchemy 模型欄位一致。
    - 前端 `EmployeeForm.vue` 直接綁定 `snake_case` 變數，與 API 介面吻合。
    - 前端 Axios 未設定全域轉換攔截器，這與目前直接傳送 `snake_case` 的實作策略一致。
- **常數定義**：`Department` (部門) 的 Enum 值在前後端定義一致 (`淡海`, `安坑`)。

## 2. 詳細檢查結果

### 2.1 員工模組 (Employee)
- **API 定義**: `backend/src/api/employees.py` 使用 `EmployeeCreate` / `EmployeeUpdate` 模型，欄位均為 `snake_case`。
- **前端實作**: `frontend/src/stores/employees.js` 在呼叫 API 時，部分參數手動轉為 snake_case (如 `include_resigned`)，這是正確的。
- **表單對接**: `frontend/src/components/employees/EmployeeForm.vue` 表單資料結構直接對應後端需求，無隱性轉換風險。

### 2.2 認證模組 (Auth/User)
- **API 定義**: 登入回傳的 `user` 物件欄位 (`display_name`, `department` 等) 均為 `snake_case`。
- **前端實作**: `useAuthStore` 正確讀取並儲存這些欄位，Getters 也正確存取。

### 2.3 資料型別與格式
- **日期**: 員工 `hire_year_month` 為字串格式 (YYYY-MM)，前端驗證邏輯與後端相符。
- **部門 Enum**: 前端 `frontend/src/constants/departments.js` 與後端 Enum 定義值一致。

## 3. 建議修改與優化項目

雖然目前功能正常，但發現以下架構上的小問題，建議進行優化以提升程式碼品質與維護性。

### [建議 1] 重構後端 Department Enum 位置 (Refactor)

**問題**: 目前 `Department` Enum 定義在 `backend/src/models/google_oauth_token.py` 中，但它被 `Employee` 模型等多處引用。這導致了不直觀的依賴關係（Employee 依賴於 GoogleOAuthToken 模組）。

**建議解法**:
1. 建立新檔案 `backend/src/constants/enums.py` 或 `backend/src/models/enums.py`。
2. 將 `Department` class 移動到該檔案。
3. 更新 `Employee` 和 `GoogleOAuthToken` 的 import 路徑。

### [建議 2] 強化前端 Store 資料邊界 (Robustness)

**問題**: `useEmployeesStore` 中的 `createEmployee` 與 `updateEmployee` 直接將 UI 傳來的 payload 送給 API。雖然目前 UI 組件使用了正確的欄位名稱，但這造成 Store 高度依賴 UI 實作細節。若未來 UI 欄位變更，可能導致 API 呼叫失敗。

**建議解法**:
在 Store action 中明確定義發送給後端的資料結構，過濾掉不必要的 UI 狀態欄位。

```javascript
// frontend/src/stores/employees.js

async function createEmployee(data) {
  // 明確提取需要的欄位，過濾掉 UI 雜訊
  const payload = {
    employee_id: data.employee_id,
    employee_name: data.employee_name,
    current_department: data.current_department,
    phone: data.phone,
    email: data.email,
    emergency_contact: data.emergency_contact,
    emergency_phone: data.emergency_phone
  }
  
  // ... call api
}
```

## 4. 待執行任務清單 (供 Claude 參考)

若要執行上述優化，請依序執行：

- [x] **後端重構**: 建立 `backend/src/constants/enums.py`，移動 `Department` Enum。
- [x] **後端重構**: 更新所有 models 和 services 的 import（共 20+ 個檔案）。
- [x] **後端重構**: 更新 `backend/src/api/schedules.py` 相關 import。
- [ ] **前端優化**: 在 `frontend/src/stores/employees.js` 中增加 payload 構建邏輯，確保資料純淨。
