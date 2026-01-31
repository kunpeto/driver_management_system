# 新舊專案架構對比與整合方案

**分析日期**: 2026-01-29
**新專案**: driver_management_system（員工+駕駛競賽為核心）
**舊專案**: driver_profile_system_重構（履歷為核心）

---

## 一、核心架構理念對比

### 新專案（driver_management_system）

**核心理念**: **員工與駕駛競賽管理**

**架構特點**:
- 以「員工」(Employee) 為中心
- 以「駕駛競賽」(Driving Competition) 為目標
- 強調自動化數據同步（Google Sheets → TiDB）
- 雲端優先（Render + TiDB Serverless）
- 雙部門獨立運作（淡海/安坑）

**核心實體**:
```
employees (員工) ← 核心
  ↓
driving_competition (駕駛競賽)
driving_daily_stats (駕駛時數)
employee_transfers (調動記錄)
schedules (班表)
route_standard_times (勤務標準時間)
```

### 舊專案（driver_profile_system_重構）

**核心理念**: **事件履歷與考核管理**

**架構特點**:
- 以「履歷」(Profile) 為中心
- 所有事件都是一筆履歷記錄
- 強調文件管理（Word/Excel 自動生成）
- 本機優先（SQLite + 本機檔案系統）
- 單一部門運作

**核心實體**:
```
profiles (履歷) ← 核心
  ├── event_investigation (事件調查)
  ├── personnel_interview (人員訪談)
  ├── corrective_measures (矯正措施)
  └── assessment_notices (加扣分通知單)
  ↓
assessment_records (考核記錄)
driving_daily_stats (駕駛時數)
pending_cases (未結案管理)
```

---

## 二、資料模型設計對比

### 2.1 員工管理

| 面向 | 新專案 | 舊專案 | 差異 |
|------|--------|--------|------|
| **核心資料表** | `employees` | `employees` | 相似 |
| **欄位** | id, employee_id, employee_name, current_department, is_active | id, employee_id, employee_name, is_resigned | 新專案多了部門和調動 |
| **調動記錄** | ✅ `employee_transfers` | ❌ 無 | 新專案支援部門調動 |
| **雙部門支援** | ✅ | ❌ | 新專案設計重點 |

### 2.2 事件記錄

| 面向 | 新專案 | 舊專案 | 差異 |
|------|--------|--------|------|
| **核心概念** | ❌ 無 | ✅ `profiles` | **重大差異** |
| **事件類型** | - | 5種（基本、事件調查、人員訪談、加扣分、矯正措施） | 舊專案核心 |
| **擴展資料** | - | 4張子表（1:1關係） | 舊專案核心 |
| **文件管理** | - | ✅ file_path, gdrive_link | 舊專案核心 |
| **樂觀鎖** | - | ✅ version | 舊專案防並發衝突 |

### 2.3 考核系統

| 面向 | 新專案 | 舊專案 | 差異 |
|------|--------|--------|------|
| **考核標準** | ❌ 無獨立表 | ✅ `assessment_standards` | 舊專案有 V2 版本 |
| **考核記錄** | ❌ 無 | ✅ `assessment_records` | 舊專案詳細記錄 |
| **累計加重** | ❌ 無 | ✅ accumulation_multiplier | 舊專案 V2 特色 |
| **手寫備註** | - | ✅ custom_notes | 舊專案可自訂關鍵字 |
| **責任事件懲罰** | ✅ `× 1/(1+N)` | ✅ `× [1 + 0.5 × (N-1)]` | **公式不同** |

### 2.4 駕駛時數統計

| 面向 | 新專案 | 舊專案 | 差異 |
|------|--------|--------|------|
| **資料表** | ✅ `driving_daily_stats` | ✅ `driving_daily_stats` | 相同 |
| **欄位** | employee_id, record_date, total_minutes | 相同 + incident_count | 舊專案多了事件次數 |
| **資料來源** | Google Sheets 勤務表 | Google Sheets 勤務表 | 相同 |
| **對照表** | ✅ `route_standard_times` (TiDB) | ✅ Excel 檔案（本機） | **儲存方式不同** |
| **批次處理** | ❌ 無 | ✅ 完整 API | 舊專案功能完整 |

### 2.5 班表與勤務

| 面向 | 新專案 | 舊專案 | 差異 |
|------|--------|--------|------|
| **班表同步** | ✅ 自動同步到 TiDB | ❌ 即時讀取不儲存 | **策略不同** |
| **資料表** | ✅ `schedules` | ❌ 無 | 新專案儲存班表 |
| **用途** | 駕駛競賽、全勤判定 | 全勤判定、差勤加分 | 相似 |

---

## 三、API 設計模式對比

### 3.1 RESTful 設計

**新專案**:
```
符合 RESTful 標準
GET  /api/employees
POST /api/employees
GET  /api/employees/{id}
PUT  /api/employees/{id}
DELETE /api/employees/{id}
```

**舊專案**:
```
符合 RESTful 標準 + 額外操作端點
GET    /api/profiles
POST   /api/profiles
GET    /api/profiles/{id}
PUT    /api/profiles/{id}
DELETE /api/profiles/{id}
POST   /api/profiles/{id}/convert      # 類型轉換
POST   /api/profiles/{id}/generate-file # 產生檔案
```

### 3.2 批次操作

**新專案**:
```
較少批次操作 API
```

**舊專案**:
```
完整批次操作 API
POST /api/driving-stats/process-range        # 批次處理日期範圍
POST /api/driving-stats/process-missing      # 補齊缺失
POST /api/pdf-processing/upload-batch        # 批次上傳 PDF
POST /api/attendance-bonus/process           # 批次差勤加分
```

### 3.3 定時任務管理

**新專案**:
```
使用 APScheduler（內建）
無對外 API 管理介面
```

**舊專案**:
```
使用 APScheduler + 完整管理 API
GET  /api/driving-stats/scheduler/jobs
POST /api/driving-stats/scheduler/run-now
```

---

## 四、Google Services 整合對比

### 4.1 Google Sheets

| 面向 | 新專案 | 舊專案 | 差異 |
|------|--------|--------|------|
| **班表讀取** | ✅ 自動同步到 TiDB | ✅ 即時讀取 | 策略不同 |
| **勤務表讀取** | ✅ 計算駕駛競賽 | ✅ 計算駕駛時數 | 相似 |
| **憑證管理** | ✅ Service Account（Base64 環境變數） | ✅ Service Account（JSON 檔案） | **儲存方式不同** |
| **權限範圍** | ✅ readonly | ✅ readonly | 相同 |

### 4.2 Google Drive

| 面向 | 新專案 | 舊專案 | 差異 |
|------|--------|--------|------|
| **檔案上傳** | ✅ PDF 上傳 | ✅ PDF 上傳 | 相同 |
| **資料夾管理** | ✅ 雙部門獨立資料夾 | ✅ 按類型/年月分類 | 策略不同 |
| **憑證管理** | ✅ OAuth 2.0（refresh_token 加密） | ✅ OAuth 2.0（token.pickle） | **儲存方式不同** |
| **自動建立資料夾** | ❌ | ✅ | 舊專案自動化程度高 |

---

## 五、部署架構對比

### 新專案（雲端優先）

```
GitHub Pages (前端)
       ↓ HTTPS
Render FastAPI (後端)
       ↓ MySQL Protocol
TiDB Serverless (資料庫)

+ localhost FastAPI (桌面應用)
```

**特點**:
- ✅ 24/7 線上服務
- ✅ 多地存取
- ✅ 雙部門獨立運作
- ❌ 需要網路連線
- ❌ 成本考量（免費額度）

### 舊專案（本機優先）

```
localhost FastAPI (本機)
       ↓
SQLite (本機資料庫)
       ↓
本機檔案系統 (可編輯資料/)
```

**特點**:
- ✅ 離線可用
- ✅ 零成本
- ✅ 資料完全掌控
- ❌ 單一電腦存取
- ❌ 資料備份靠手動

---

## 六、整合方案建議

### 方案 A：漸進式整合（推薦）⭐

**理念**: 保留新專案的雲端架構，逐步補充舊專案的功能

#### 階段 1：核心功能補充（2 週）

**新增 User Story 8: 司機員事件履歷管理**
- 建立 `profiles` 資料表及子表（TiDB）
- 實作履歷 CRUD API
- 實作履歷類型轉換
- 實作 Office 文件自動生成（透過本機 API）
- 條碼生成整合

**資料模型調整**:
```sql
-- 新增資料表（TiDB）
profiles
event_investigation
personnel_interview
corrective_measures
assessment_notices
pending_cases
```

**API 端點**:
```
新增 /api/profiles 路由群組（15+ 端點）
新增 /api/pending-cases 路由群組（4+ 端點）
擴充 /api/files 路由（Office 文件生成）
```

#### 階段 2：駕駛時數統計強化（1 週）

**擴充 User Story 5: 駕駛時數統計與競賽排名**
- 補充每日駕駛時數詳細記錄功能
- 實作月度彙總統計
- 實作批次處理與補齊功能
- 實作定時任務管理 API

**API 端點**:
```
擴充 /api/driving-stats 路由群組
新增批次處理端點
新增定時任務管理端點
```

#### 階段 3：考核系統 V2 升級（1 週）

**新增 User Story 9: 考核系統 V2 升級**
- 建立 `assessment_standards` 和 `assessment_records` 資料表
- 實作累計加重計算邏輯
- 實作雙版本並存機制（V1/V2）
- 實作考核標準 Excel 匯入

**資料模型調整**:
```sql
-- 新增資料表（TiDB）
assessment_standards
assessment_records
```

#### 階段 4：差勤加分自動處理（1 週）

**新增 User Story 10: 差勤加分自動處理**
- 實作班表解析邏輯
- 實作三種加分自動判定（全勤、R班、加班）
- 實作批次處理與防重複機制

#### 階段 5：報表功能強化（3 天）

**擴充現有報表功能**
- 新增技安專用簡化版報表
- 新增考核月報表（排名+明細）
- 新增個人統計圖表

**優點**:
- ✅ 保留新專案的雲端架構優勢
- ✅ 逐步驗證功能可行性
- ✅ 風險可控
- ✅ 可隨時調整優先級

**缺點**:
- ⏳ 需要 5-6 週完成
- 🔧 需要調整部分舊專案邏輯（雲端化）

---

### 方案 B：雙系統並存（過渡方案）

**理念**: 新舊系統同時運作，逐步遷移

#### 實施方式
1. 新專案專注於駕駛競賽和員工管理
2. 舊專案繼續負責事件履歷和考核管理
3. 雙方透過 API 或共享資料庫交換資料

**優點**:
- ✅ 快速啟用新專案
- ✅ 舊系統持續可用
- ✅ 零風險

**缺點**:
- ❌ 資料分散兩個系統
- ❌ 維護成本高
- ❌ 使用者需要切換系統
- ❌ 長期不可行

**適用情境**: 暫時性方案，不建議長期使用

---

### 方案 C：完全重構（不推薦）

**理念**: 完全按照新專案架構重寫舊專案功能

**優點**:
- ✅ 架構統一
- ✅ 程式碼品質高

**缺點**:
- ❌ 需要 2-3 個月
- ❌ 風險高
- ❌ 測試成本高
- ❌ 不符合敏捷開發原則

**不推薦原因**: 投入產出比不佳

---

## 七、推薦方案：方案 A 詳細實施計畫

### 7.1 規格文件更新方式

#### 選項 1：擴充現有 spec.md（推薦）

**理由**:
- 單一來源真實（Single Source of Truth）
- 方便查閱所有功能
- 避免文件分散

**實施方式**:
```
specs/001-system-architecture/
  ├── spec.md               # 擴充新增 User Story 8-11
  ├── plan.md               # 擴充實作計畫
  ├── tasks.md              # 擴充任務分解
  └── data-model.md         # 新增資料模型文檔
```

**spec.md 結構**:
```markdown
## User Stories & Testing

### User Story 1 - 系統配置初始化 (已有)
### User Story 2 - 員工管理 (已有)
### User Story 3 - 權限控制 (已有)
### User Story 4 - Google Sheets 班表同步 (已有)
### User Story 5 - 駕駛時數統計與競賽排名 (擴充)
### User Story 6 - 系統連線監控 (已有)
### User Story 7 - PDF 條碼識別 (已有)

### User Story 8 - 司機員事件履歷管理 (新增) ⭐
### User Story 9 - 考核系統 V2 升級 (新增) ⭐
### User Story 10 - 差勤加分自動處理 (新增) ⭐
### User Story 11 - 未結案管理 (新增) ⭐
```

#### 選項 2：創建獨立規格文件

**理由**:
- 清晰區分新舊功能
- 保持原規格簡潔

**實施方式**:
```
specs/
  ├── 001-system-architecture/      # 原有規格（7個 User Stories）
  └── 002-profile-management/       # 新規格（履歷管理相關）
      ├── spec.md
      ├── plan.md
      └── tasks.md
```

**缺點**: 文件分散，查閱不便

---

### 7.2 資料模型整合策略

#### 新增資料表清單

**核心資料表（TiDB）**:
```sql
-- 履歷管理
profiles                    -- 履歷主表
event_investigation         -- 事件調查
personnel_interview         -- 人員訪談
corrective_measures         -- 矯正措施
assessment_notices          -- 加扣分通知單
pending_cases               -- 未結案管理

-- 考核系統
assessment_standards        -- 考核標準表（V2）
assessment_records          -- 考核記錄（V2）

-- 已有資料表擴充
driving_daily_stats         -- 補充 incident_count 欄位
```

#### 欄位調整

**employees** - 無需調整（已完整）

**driving_daily_stats** - 補充欄位:
```sql
ALTER TABLE driving_daily_stats
ADD COLUMN incident_count INTEGER DEFAULT 0 COMMENT '當日責任事件次數（R+S）';
```

---

### 7.3 API 路由整合

#### 新增路由群組

```python
# backend/src/api/profiles.py (新增)
router = APIRouter(prefix="/profiles", tags=["履歷管理"])

# backend/src/api/assessments_v2.py (新增)
router = APIRouter(prefix="/assessments-v2", tags=["考核系統V2"])

# backend/src/api/pending_cases.py (新增)
router = APIRouter(prefix="/pending-cases", tags=["未結案管理"])

# backend/src/api/attendance_bonus.py (新增)
router = APIRouter(prefix="/attendance-bonus", tags=["差勤加分處理"])

# backend/src/api/driving_stats.py (擴充)
# 新增批次處理和定時任務管理端點
```

#### 主程式註冊

```python
# backend/src/main.py

from backend.src.api import (
    auth, employees, system_settings,
    google_sheets, driving_competition,
    files, pdf_processing, reports,
    profiles,           # 新增
    assessments_v2,     # 新增
    pending_cases,      # 新增
    attendance_bonus    # 新增
)

app.include_router(profiles.router, prefix="/api")
app.include_router(assessments_v2.router, prefix="/api")
app.include_router(pending_cases.router, prefix="/api")
app.include_router(attendance_bonus.router, prefix="/api")
```

---

### 7.4 雲端化調整重點

#### 原本機功能的雲端化

**1. Office 文件生成**
```
舊專案：本機生成 → 本機儲存
新專案：本機 API 生成 → 上傳到 Google Drive → 雲端記錄連結
```

**2. 條碼生成**
```
舊專案：本機生成條碼並嵌入 Word
新專案：本機 API 生成條碼 → 回傳 Base64 → 雲端 API 記錄
```

**3. SQLite → TiDB**
```
舊專案：SQLite（本機）
新專案：TiDB Serverless（雲端 MySQL）
調整：移除 WAL mode，使用標準 MySQL
```

**4. 憑證管理**
```
舊專案：credentials.json, token.pickle（本機檔案）
新專案：Service Account（Base64 環境變數） + OAuth（加密 refresh_token）
調整：統一使用環境變數 + 資料庫儲存
```

---

### 7.5 前端整合

#### Vue.js 元件結構

```
frontend/src/views/
  ├── profiles/                    # 履歷管理（新增）
  │   ├── ProfileList.vue          # 履歷列表
  │   ├── ProfileDetail.vue        # 履歷詳情
  │   ├── ProfileCreate.vue        # 新增履歷
  │   ├── ProfileEdit.vue          # 編輯履歷
  │   └── ProfileConvert.vue       # 類型轉換表單
  │
  ├── assessments/                 # 考核管理（新增）
  │   ├── AssessmentStandards.vue  # 考核標準管理
  │   ├── AssessmentRecords.vue    # 考核記錄查詢
  │   └── AttendanceBonus.vue      # 差勤加分處理
  │
  ├── pending-cases/               # 未結案管理（新增）
  │   └── PendingCaseList.vue
  │
  └── driving-stats/               # 駕駛統計（擴充）
      ├── DailyStats.vue           # 每日統計（新增）
      ├── MonthlySummary.vue       # 月度彙總（新增）
      └── Competition.vue          # 駕駛競賽（已有）
```

#### 路由配置

```javascript
// frontend/src/router/index.js

const routes = [
  // ... 已有路由

  // 履歷管理
  {
    path: '/profiles',
    component: () => import('@/views/profiles/ProfileList.vue'),
    meta: { requiresAuth: true, role: ['Admin', 'Staff'] }
  },

  // 考核管理
  {
    path: '/assessments',
    component: () => import('@/views/assessments/AssessmentRecords.vue'),
    meta: { requiresAuth: true }
  },

  // 未結案管理
  {
    path: '/pending-cases',
    component: () => import('@/views/pending-cases/PendingCaseList.vue'),
    meta: { requiresAuth: true, role: ['Admin', 'Staff'] }
  }
]
```

---

## 八、總結與建議

### 8.1 推薦方案

**方案 A（漸進式整合）** ⭐

**理由**:
1. ✅ 保留新專案的雲端優勢
2. ✅ 補充舊專案的核心功能
3. ✅ 風險可控，階段性驗證
4. ✅ 符合敏捷開發原則
5. ✅ 5-6 週可完成所有核心功能

### 8.2 實施時程

```
Week 1-2:  User Story 8（履歷管理）
Week 3:    User Story 5 擴充（駕駛時數統計強化）
Week 4:    User Story 9（考核系統 V2）
Week 5:    User Story 10（差勤加分處理）
Week 6:    報表強化 + 測試 + 文檔
```

### 8.3 規格文件更新建議

**推薦**: 擴充現有 `specs/001-system-architecture/spec.md`

**新增內容**:
- User Story 8: 司機員事件履歷管理
- User Story 9: 考核系統 V2 升級
- User Story 10: 差勤加分自動處理
- User Story 11: 未結案管理

**同步更新**:
- `plan.md`: 補充實作計畫
- `tasks.md`: 新增任務分解（約 50+ 新任務）
- 新增 `data-model.md`: 資料模型文檔

### 8.4 下一步行動

1. **確認整合方案**：與團隊討論選擇方案 A、B 或 C
2. **更新規格文件**：根據選定方案更新 spec.md
3. **資料模型設計**：詳細設計新增資料表的 Schema
4. **API 介面設計**：定義所有新增 API 的 Request/Response
5. **開始實作**：按階段逐步實施

---

**結論**: 建議採用**方案 A（漸進式整合）**，擴充現有規格文件，在保留新專案雲端架構優勢的前提下，補充舊專案的履歷管理和考核系統功能，形成一個更完整的司機員管理系統。
