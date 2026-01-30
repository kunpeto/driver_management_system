# API 文件

**版本**: 1.0.0
**基礎 URL**: `https://your-domain.com/api`
**更新日期**: 2026-01-30

---

## 目錄

1. [認證機制](#認證機制)
2. [錯誤碼說明](#錯誤碼說明)
3. [API 端點](#api-端點)
   - [認證 API](#認證-api)
   - [使用者管理 API](#使用者管理-api)
   - [員工管理 API](#員工管理-api)
   - [履歷系統 API](#履歷系統-api)
   - [班表與統計 API](#班表與統計-api)
   - [考核系統 API](#考核系統-api)
   - [差勤加分 API](#差勤加分-api)
   - [Google 整合 API](#google-整合-api)
   - [系統設定 API](#系統設定-api)

---

## 認證機制

### JWT Token 認證

所有需要認證的端點必須在請求標頭中攜帶 JWT Token：

```http
Authorization: Bearer <access_token>
```

### Token 有效期

| Token 類型 | 有效期 |
|-----------|--------|
| Access Token | 30 分鐘 |
| Refresh Token | 7 天 |

### 權限等級

| 等級 | 說明 |
|------|------|
| Admin | 系統管理員，擁有所有權限 |
| Manager | 主管，可管理所有部門資料 |
| Staff | 一般員工，僅能管理本部門資料 |

---

## 錯誤碼說明

### HTTP 狀態碼

| 狀態碼 | 說明 |
|-------|------|
| 200 | 成功 |
| 201 | 建立成功 |
| 400 | 請求格式錯誤 |
| 401 | 未認證或 Token 過期 |
| 403 | 權限不足 |
| 404 | 資源不存在 |
| 409 | 資源衝突（如重複建立）|
| 422 | 資料驗證失敗 |
| 429 | 請求過於頻繁 |
| 500 | 伺服器內部錯誤 |

### 錯誤回應格式

```json
{
  "detail": "錯誤訊息描述",
  "error_code": "ERROR_CODE",
  "field": "欄位名稱（若適用）"
}
```

### 常見錯誤碼

| 錯誤碼 | 說明 |
|-------|------|
| INVALID_CREDENTIALS | 帳號或密碼錯誤 |
| TOKEN_EXPIRED | Token 已過期 |
| TOKEN_INVALID | Token 格式無效 |
| PERMISSION_DENIED | 權限不足 |
| RESOURCE_NOT_FOUND | 資源不存在 |
| DUPLICATE_ENTRY | 重複的資料 |
| VALIDATION_ERROR | 資料驗證失敗 |
| RATE_LIMIT_EXCEEDED | 超過請求限制 |

---

## API 端點

### 認證 API

#### POST /auth/login

使用者登入，取得 JWT Token。

**請求**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**回應**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "department": null
  }
}
```

---

#### POST /auth/refresh

刷新 Access Token。

**請求**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**回應**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

#### POST /auth/logout

使用者登出（使 Token 失效）。

**權限**: 認證使用者

**回應**
```json
{
  "message": "登出成功"
}
```

---

#### GET /auth/me

取得當前登入使用者資訊。

**權限**: 認證使用者

**回應**
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "department": null,
  "is_active": true
}
```

---

#### POST /auth/change-password

變更密碼。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| old_password | string | 是 | 舊密碼 |
| new_password | string | 是 | 新密碼 |

**回應**
```json
{
  "message": "密碼變更成功"
}
```

---

### 使用者管理 API

#### GET /users

取得使用者列表。

**權限**: Admin

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| role | string | 否 | 篩選角色 (admin/manager/staff) |
| department | string | 否 | 篩選部門 (淡海/安坑) |
| is_active | boolean | 否 | 篩選啟用狀態 |
| skip | integer | 否 | 跳過筆數，預設 0 |
| limit | integer | 否 | 每頁筆數，預設 100 |

**回應**
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "department": null,
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 10
}
```

---

#### POST /users

建立新使用者。

**權限**: Admin

**請求**
```json
{
  "username": "newuser",
  "password": "password123",
  "role": "staff",
  "department": "淡海"
}
```

**回應**
```json
{
  "id": 2,
  "username": "newuser",
  "role": "staff",
  "department": "淡海",
  "is_active": true,
  "created_at": "2026-01-30T10:00:00Z"
}
```

---

#### PUT /users/{user_id}

更新使用者資訊。

**權限**: Admin

**請求**
```json
{
  "role": "manager",
  "department": "安坑"
}
```

---

#### POST /users/{user_id}/reset-password

重設使用者密碼（管理員不需舊密碼）。

**權限**: Admin

**請求**
```json
{
  "new_password": "newpassword123"
}
```

---

#### POST /users/{user_id}/activate

啟用使用者帳號。

**權限**: Admin

---

#### POST /users/{user_id}/deactivate

停用使用者帳號。

**權限**: Admin

---

#### DELETE /users/{user_id}

刪除使用者。

**權限**: Admin

---

### 員工管理 API

#### GET /employees

取得員工列表。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| department | string | 否 | 篩選部門 |
| include_resigned | boolean | 否 | 是否包含離職員工，預設 false |
| search | string | 否 | 關鍵字搜尋（姓名、編號）|
| skip | integer | 否 | 跳過筆數 |
| limit | integer | 否 | 每頁筆數 |

**回應**
```json
{
  "employees": [
    {
      "id": 1,
      "employee_id": "1011M0095",
      "employee_name": "張三",
      "department": "淡海",
      "hire_date": "2020-01-15",
      "is_resigned": false,
      "current_score": 80.0
    }
  ],
  "total": 150
}
```

---

#### GET /employees/statistics

取得員工統計資料。

**權限**: 認證使用者

**回應**
```json
{
  "total": 150,
  "active": 145,
  "resigned": 5,
  "by_department": {
    "淡海": 80,
    "安坑": 70
  }
}
```

---

#### GET /employees/{employee_id}

取得員工詳情。

**權限**: 認證使用者

---

#### GET /employees/by-employee-id/{employee_code}

根據員工編號取得員工詳情。

**權限**: 認證使用者

**範例**: `GET /employees/by-employee-id/1011M0095`

---

#### POST /employees

建立新員工。

**權限**: Staff（限本部門）, Manager/Admin（所有部門）

**請求**
```json
{
  "employee_id": "1140M0001",
  "employee_name": "王小明",
  "department": "淡海",
  "hire_date": "2026-01-15"
}
```

---

#### PUT /employees/{employee_id}

更新員工資料。

**權限**: 對應部門的 Staff/Manager/Admin

---

#### POST /employees/{employee_id}/resign

標記員工離職。

**權限**: 對應部門的 Staff/Manager/Admin

---

#### POST /employees/{employee_id}/activate

標記員工復職。

**權限**: 對應部門的 Staff/Manager/Admin

---

#### POST /employees/{employee_id}/transfer

執行員工調動。

**權限**: 對應部門權限

**請求**
```json
{
  "to_department": "安坑",
  "transfer_date": "2026-02-01",
  "reason": "組織調整"
}
```

---

#### GET /employees/{employee_id}/transfers

取得員工調動歷史。

**權限**: 認證使用者

---

#### POST /employees/import

批次匯入員工（Excel）。

**權限**: Manager/Admin

**請求**: `multipart/form-data`，上傳 Excel 檔案

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| skip_duplicates | boolean | 否 | 跳過重複資料，預設 true |

---

#### GET /employees/export

匯出員工資料。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| format | string | 否 | 格式 (excel/csv)，預設 excel |
| department | string | 否 | 篩選部門 |
| include_resigned | boolean | 否 | 是否包含離職員工 |

---

### 履歷系統 API

#### GET /profiles

取得履歷列表。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| department | string | 否 | 篩選部門 |
| profile_type | string | 否 | 履歷類型 |
| conversion_status | string | 否 | 轉換狀態 |
| employee_id | integer | 否 | 員工 ID |
| date_from | date | 否 | 起始日期 |
| date_to | date | 否 | 結束日期 |

**履歷類型**
- `basic`: 基本履歷
- `event_investigation`: 事件調查
- `personnel_interview`: 人員訪談
- `corrective_measures`: 矯正措施
- `assessment_notice`: 考核通知

---

#### POST /profiles

建立基本履歷。

**權限**: 認證使用者

**請求**
```json
{
  "employee_id": 1,
  "event_date": "2026-01-15",
  "event_time": "14:30:00",
  "event_location": "淡海站",
  "train_number": "C301",
  "event_title": "事件標題",
  "event_description": "事件描述內容"
}
```

---

#### POST /profiles/{profile_id}/convert

轉換履歷類型。

**權限**: 認證使用者

**限制**: 僅 `basic` 類型可轉換

**請求**
```json
{
  "target_type": "personnel_interview",
  "interview_content": "訪談內容",
  "interviewer": "李主管",
  "interview_date": "2026-01-16"
}
```

---

#### POST /profiles/{profile_id}/reset

重置履歷為基本類型。

**權限**: 認證使用者

---

#### POST /profiles/{profile_id}/generate-document

生成 Office 文件。

**權限**: 認證使用者

**限制**: Rate Limit 5 次/分鐘

**回應**: Word 文件流（application/vnd.openxmlformats-officedocument.wordprocessingml.document）

---

#### GET /profiles/schedule-lookup

查詢員工班表（用於填充訪談表單）。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| employee_id | integer | 是 | 員工 ID |
| event_date | date | 是 | 事件日期 |

**回應**
```json
{
  "shift_before_2days": "0600A",
  "shift_before_1day": "1400B",
  "shift_event_day": "R/0905G"
}
```

---

#### GET /profiles/pending

取得未結案履歷。

**權限**: 認證使用者

---

#### GET /profiles/pending/statistics

取得未結案統計。

**權限**: 認證使用者

**回應**
```json
{
  "total_pending": 15,
  "by_type": {
    "event_investigation": 5,
    "personnel_interview": 8,
    "corrective_measures": 2
  },
  "oldest_date": "2026-01-10",
  "this_month_completion_rate": 0.85
}
```

---

#### POST /profiles/with-assessment

建立履歷並同時建立考核記錄。

**權限**: 認證使用者

**請求**
```json
{
  "employee_id": 1,
  "event_date": "2026-01-15",
  "event_location": "淡海站",
  "standard_code": "R04",
  "fault_responsibility": {
    "delay_seconds": 420,
    "checklist_results": {
      "item_1": true,
      "item_2": false,
      "item_3": true
    }
  }
}
```

---

### 班表與統計 API

#### GET /schedules

查詢班表資料。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| department | string | 否 | 部門 |
| start_date | date | 否 | 起始日期 |
| end_date | date | 否 | 結束日期 |
| employee_id | integer | 否 | 員工 ID |
| page | integer | 否 | 頁碼 |
| page_size | integer | 否 | 每頁筆數 |

---

#### GET /schedules/employee/{employee_id}

查詢員工月班表。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| year | integer | 是 | 年份 |
| month | integer | 是 | 月份 |

---

#### GET /driving/stats

查詢每日駕駛時數統計。

**權限**: 認證使用者（非管理員僅能查詢自己）

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| employee_id | integer | 否 | 員工 ID |
| department | string | 否 | 部門 |
| start_date | date | 否 | 起始日期 |
| end_date | date | 否 | 結束日期 |

---

#### GET /driving/stats/quarter

查詢員工季度統計。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| employee_id | integer | 是 | 員工 ID |
| year | integer | 是 | 年份 |
| quarter | integer | 是 | 季度 (1-4) |

---

#### GET /driving/competition

查詢季度競賽排名。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| year | integer | 是 | 年份 |
| quarter | integer | 是 | 季度 |
| department | string | 否 | 篩選部門 |

**回應**
```json
{
  "rankings": [
    {
      "rank": 1,
      "employee_id": 1,
      "employee_name": "張三",
      "department": "淡海",
      "total_hours": 450.5,
      "total_points": 95.0,
      "is_qualified": true,
      "bonus_amount": 5000
    }
  ],
  "total_participants": 120
}
```

---

#### GET /routes

列出勤務標準時間。

**權限**: 認證使用者

---

#### POST /routes

建立勤務標準時間。

**權限**: Admin

**請求**
```json
{
  "route_code": "0905G",
  "department": "淡海",
  "standard_minutes": 120,
  "description": "淡海至安坑"
}
```

---

#### POST /routes/import-excel

從 Excel 匯入勤務標準時間。

**權限**: Admin

---

### 考核系統 API

#### GET /assessment-standards

取得所有考核標準。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| is_active | boolean | 否 | 篩選啟用狀態 |
| category | string | 否 | 篩選類別 (D/W/O/S/R/+M/+A) |

**回應**
```json
{
  "standards": [
    {
      "id": 1,
      "code": "D01",
      "category": "D",
      "name": "遲到",
      "base_points": -1.0,
      "has_cumulative": true,
      "calculation_cycle": "yearly",
      "is_active": true
    }
  ]
}
```

---

#### GET /assessment-standards/r-type

取得需要責任判定的 R02-R05 項目。

**權限**: 認證使用者

---

#### POST /assessment-standards/initialize-defaults

初始化預設的 61 項考核標準。

**權限**: Admin

---

#### GET /assessment-records

取得考核記錄列表。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| employee_id | integer | 否 | 員工 ID |
| year | integer | 否 | 年份 |
| month | integer | 否 | 月份 |
| category | string | 否 | 類別 |
| include_deleted | boolean | 否 | 包含已刪除 |

---

#### POST /assessment-records

建立考核記錄。

**權限**: 認證使用者

**請求**
```json
{
  "employee_id": 1,
  "standard_code": "D01",
  "record_date": "2026-01-15",
  "description": "遲到 5 分鐘"
}
```

---

#### POST /assessment-records/{record_id}/fault-responsibility

更新 R02-R05 責任判定。

**權限**: 認證使用者

**請求**
```json
{
  "time_t0": "14:30:00",
  "time_t1": "14:35:00",
  "time_t2": "14:37:00",
  "time_t3": "14:40:00",
  "time_t4": "14:45:00",
  "delay_seconds": 420,
  "checklist_results": {
    "item_1": true,
    "item_2": false,
    "item_3": true,
    "item_4": false,
    "item_5": true,
    "item_6": false,
    "item_7": true,
    "item_8": false,
    "item_9": true
  },
  "notes": "備註說明"
}
```

**回應**：包含計算後的責任係數和最終分數

---

#### GET /assessment-records/summary

取得員工年度考核摘要。

**權限**: 認證使用者

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| employee_id | integer | 是 | 員工 ID |
| year | integer | 是 | 年份 |

**回應**
```json
{
  "employee_id": 1,
  "employee_name": "張三",
  "current_score": 78.5,
  "year": 2026,
  "cumulative_counts": {
    "D": 2,
    "W": 1,
    "O": 0,
    "S": 0,
    "R": 1
  },
  "monthly_rewards": {
    "full_attendance_count": 3,
    "driving_zero_count": 5,
    "all_zero_count": 2
  },
  "total_records": 15
}
```

---

#### POST /assessment-records/monthly-rewards/calculate

計算月度獎勵（批次）。

**權限**: Admin

**請求**
```json
{
  "year": 2026,
  "month": 1
}
```

---

#### POST /assessment-records/annual-reset

執行年度重置。

**權限**: Admin

**請求**
```json
{
  "year": 2026,
  "confirm": true
}
```

---

### 差勤加分 API

#### POST /attendance-bonus/process

執行差勤加分處理。

**權限**: Admin

**請求**
```json
{
  "year": 2026,
  "month": 1,
  "department": "淡海"
}
```

**回應**
```json
{
  "success": true,
  "statistics": {
    "total_employees": 80,
    "full_attendance_count": 65,
    "r_shift_count": 120,
    "national_holiday_count": 15,
    "overtime_count": 45,
    "created_records": 245,
    "skipped_duplicates": 10
  }
}
```

---

#### POST /attendance-bonus/preview

預覽差勤加分處理（不寫入）。

**權限**: 認證使用者

---

#### GET /attendance-bonus/results/{year}/{month}

查詢月度加分統計。

**權限**: 認證使用者

---

#### GET /attendance-bonus/history

查詢差勤加分處理歷史。

**權限**: 認證使用者

---

### Google 整合 API

#### POST /credentials/{department}

儲存部門 Google 憑證。

**權限**: Admin

**請求**
```json
{
  "base64_json": "eyJwcm9qZWN0X2lkIjoi...",
  "authorized_email": "admin@company.com"
}
```

---

#### GET /credentials/{department}

取得部門憑證狀態。

**權限**: Admin

---

#### POST /validate-credentials

驗證 Service Account 格式。

**權限**: Admin

---

#### POST /test-sheets

測試 Google Sheets 連線。

**權限**: Admin

**請求**
```json
{
  "department": "淡海",
  "spreadsheet_id": "1abc..."
}
```

---

#### GET /api/google/auth-url

生成 OAuth 授權 URL。

**權限**: Admin

**查詢參數**
| 參數 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| department | string | 是 | 部門 |

---

#### GET /api/google/oauth-status

檢查所有部門 OAuth 狀態。

**權限**: 認證使用者

---

#### DELETE /api/google/revoke

撤銷 OAuth 授權。

**權限**: Admin

---

### 系統設定 API

#### GET /system-settings

取得系統設定。

**權限**: Admin

---

#### PUT /system-settings

更新系統設定。

**權限**: Admin

---

#### GET /connection-status

取得本機桌面應用連線狀態。

**權限**: 認證使用者

---

#### GET /sync-tasks

取得同步任務狀態。

**權限**: 認證使用者

---

#### POST /sync-tasks/trigger

手動觸發同步任務。

**權限**: Admin

---

## Rate Limiting

部分 API 端點設有請求頻率限制：

| 端點 | 限制 |
|------|------|
| POST /profiles/{id}/generate-document | 5 次/分鐘 |
| POST /auth/login | 10 次/分鐘 |
| POST /attendance-bonus/process | 1 次/分鐘 |

超過限制時會回傳 HTTP 429 狀態碼。

---

## 變更日誌

### v1.0.0 (2026-01-30)
- 初始版本
- 包含所有 Phase 1-14 功能的 API 端點
