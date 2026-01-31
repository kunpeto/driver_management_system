# API 路徑修正摘要

## 問題描述

前端在登入後載入時出現 404 錯誤,原因是前端的 API 路徑配置與後端不一致。

## 錯誤原因

後端的路由註冊使用了 `/api` 前綴,但前端的部分 API 呼叫沒有加上此前綴。

## 修正內容

### 1. Store 檔案的 API_BASE 常數修正

| 檔案 | 原路徑 | 修正後路徑 |
|------|--------|-----------|
| `stores/profiles.js` | `/profiles` | `/api/profiles` |
| `stores/attendanceBonus.js` | `/attendance-bonus` | `/api/attendance-bonus` |
| `stores/assessments.js` | `/assessment-standards`<br>`/assessment-records` | `/api/assessment-standards`<br>`/api/assessment-records` |
| `stores/employees.js` | `/employees` | `/api/employees` |
| `stores/systemSettings.js` | `/settings`<br>`/google` | `/api/settings`<br>`/api/google` |

### 2. drivingStats.js 中的所有 API 呼叫修正

修正了以下路徑:
- `/routes` → `/api/routes`
- `/routes/import-excel` → `/api/routes/import-excel`
- `/driving/stats` → `/api/driving/stats`
- `/driving/stats/quarter` → `/api/driving/stats/quarter`
- `/driving/stats/quarter/department` → `/api/driving/stats/quarter/department`
- `/driving/competition` → `/api/driving/competition`
- `/driving/competition/calculate` → `/api/driving/competition/calculate`
- `/driving/competition/bonus-tiers` → `/api/driving/competition/bonus-tiers`

### 3. 組件和視圖中的 API 呼叫修正

| 檔案 | 修正內容 |
|------|---------|
| `components/profiles/BasicProfileForm.vue` | `/employees` → `/api/employees` |
| `views/Dashboard.vue` | `/employees/statistics` → `/api/employees/statistics`<br>`/profiles/pending/statistics` → `/api/profiles/pending/statistics`<br>`/profiles/pending` → `/api/profiles/pending`<br>`/assessment-records/monthly-summary` → `/api/assessment-records/monthly-summary` |

## 後端路由對照表

| 路由 | Prefix | 完整路徑範例 |
|------|--------|-------------|
| `system_settings_router` | `/api/settings` | `/api/settings` |
| `google_credentials_router` | `/api/google` | `/api/google` |
| `employees_router` | `/api/employees` | `/api/employees` |
| `auth_router` | `/api/auth` | `/api/auth/login` |
| `profiles_router` | `/api/profiles` | `/api/profiles/pending/statistics` |
| `assessment_standards_router` | `/api/assessment-standards` | `/api/assessment-standards` |
| `assessment_records_router` | `/api/assessment-records` | `/api/assessment-records/monthly-summary` |
| `attendance_bonus_router` | `/api/attendance-bonus` | `/api/attendance-bonus` |
| `route_standard_time_router` | `/api` | `/api/routes` |
| `driving_stats_router` | `/api` | `/api/driving/stats` |
| `driving_competition_router` | `/api` | `/api/driving/competition` |

## 特殊端點

以下端點不使用 `/api` 前綴(符合後端設計):
- `/health` - 健康檢查端點
- `/health/database` - 資料庫健康檢查端點
- `/` - API 根路由

## 測試建議

1. 重新啟動前端開發伺服器
2. 清除瀏覽器快取和 localStorage
3. 使用 admin / admin123 登入
4. 檢查 F12 Console 是否還有 404 錯誤
5. 驗證以下功能:
   - 儀表板載入未結案統計
   - 員工列表載入
   - 事件履歷查詢
   - 考核記錄查詢
   - 駕駛統計查詢

## 修正日期

2026-02-01
