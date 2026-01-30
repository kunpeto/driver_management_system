# 功能差異分析與補充方案

**分析日期**: 2026-01-29
**舊專案**: driver_profile_system_重構
**新專案**: driver_management_system

## 執行摘要

經過詳細分析，舊專案有 **8 大核心功能**是新專案目前缺少的。這些功能對於完整的司機員管理系統至關重要。

---

## 一、履歷管理系統（Profile Management System）

### 舊專案功能
這是舊專案的**核心架構**，所有事件都以「履歷」(Profile) 的形式存在。

#### 資料模型
```python
class Profile(Base):
    - id: 履歷 ID
    - profile_type: 履歷類型（5種）
      * BASIC: 基本履歷
      * EVENT_INVESTIGATION: 事件調查
      * PERSONNEL_INTERVIEW: 人員訪談
      * ASSESSMENT_NOTICE: 加扣分通知單
      * CORRECTIVE_MEASURES: 矯正措施
    - event_date: 事件日期
    - event_time: 事件時間
    - employee_id: 員工編號
    - employee_name: 員工姓名
    - event_location: 事件地點
    - train_number: 列車車號
    - event_description: 事件描述
    - assessment_item: 考核項目
    - assessment_score: 考核分數
    - conversion_status: 轉換狀態
      * PENDING: 待轉換
      * CONVERTED: 已轉換
      * COMPLETED: 已完成
    - file_path: 本機檔案路徑
    - gdrive_link: Google Drive 連結
    - version: 樂觀鎖版本號（防止並發編輯衝突）
```

#### 擴展資料表
每種履歷類型有對應的擴展表：

1. **EventInvestigation（事件調查）**
   - incident_time: 事故時間
   - incident_location: 事故地點
   - witness_name: 目擊者姓名
   - incident_cause: 事故原因
   - incident_process: 事故經過
   - improvement_suggestion: 改善建議
   - investigator: 調查人員
   - investigation_date: 調查日期

2. **PersonnelInterview（人員訪談）**
   - interview_date: 訪談日期
   - interviewer: 訪談人員
   - incident_cause: 事故經過
   - interview_content: 訪談記錄
   - interview_result: 訪談結果（多選）
   - follow_up_actions: 追蹤辦理事項（多選）
   - conclusion: 值班人員建議
   - **自動帶入欄位**：
     * hire_date: 到職日期（從員工編號解析）
     * shift1/shift2/shift3: 事件當天/前一天/前兩天班別（從 Google Sheets 班表取得）

3. **CorrectiveMeasures（矯正措施）**
   - incident_cause: 事件概述
   - corrective_action: 矯正措施

4. **AssessmentNotice（加扣分通知單）**
   - notice_type: 通知類型（加分/扣分）
   - reason: 理由
   - issuer: 核發人員
   - issue_date: 核發日期

#### 主要功能

1. **履歷 CRUD**
   - 建立基本履歷
   - 查詢履歷（支援多條件篩選）
   - 編輯履歷（含樂觀鎖版本控制）
   - 刪除履歷

2. **履歷類型轉換**
   - 從基本履歷轉換為特定類型
   - 填寫該類型的擴展欄位
   - 自動帶入資料（員工編號解析、班表查詢）

3. **Office 文件自動生成**
   - 從資料庫資料填充 Word/Excel 範本
   - 自動命名檔案：`類型_YYYYMMDD_車號_地點_標題_姓名.docx`
   - 儲存到對應資料夾：`可編輯資料/[類型]/[年份]/[月份]/`
   - 開啟文件供使用者確認

4. **多條件篩選查詢**
   - 日期區間
   - 員工姓名
   - 列車車號
   - 地點
   - 關鍵字（全文搜尋）
   - 組合篩選

#### API 端點
```
GET    /api/profiles                    # 查詢履歷列表
POST   /api/profiles                    # 建立履歷
GET    /api/profiles/{id}               # 取得履歷詳情
PUT    /api/profiles/{id}               # 更新履歷
DELETE /api/profiles/{id}               # 刪除履歷
POST   /api/profiles/{id}/convert       # 轉換履歷類型
GET    /api/profiles/export             # 匯出履歷
```

### 新專案現狀
- ❌ **完全沒有履歷管理概念**
- ❌ 缺少事件調查、人員訪談、矯正措施功能
- ❌ 缺少 Office 文件自動生成
- ❌ 缺少多條件篩選查詢

### 建議補充方式
建議在新專案中新增 **User Story 8: 司機員事件履歷管理系統**

---

## 二、駕駛時數詳細統計（Driving Stats）

### 舊專案功能

#### 資料模型
```python
class DrivingDailyStats(Base):
    - id: 記錄 ID
    - employee_id: 員工編號
    - employee_name: 員工姓名
    - record_date: 記錄日期
    - total_minutes: 當日駕駛分鐘數
    - incident_count: 當日責任事件次數（R+S）
    - fiscal_year: 年度
    - fiscal_month: 月份
    - created_at/updated_at: 時間戳

    UniqueConstraint: (employee_id, record_date)
    Indexes: employee_id, record_date, (fiscal_year, fiscal_month)
```

#### 主要功能

1. **每日駕駛時數計算**
   - 從 Google Sheets 勤務表讀取資料
   - 解析每日勤務路線（如 "淡安-全"、"安淡-全"）
   - 查詢勤務標準時間表（route_standard_times）
   - 計算當日總駕駛分鐘數
   - 統計當日責任事件次數

2. **月度彙總統計**
   - 按總駕駛分鐘數排序
   - 顯示每位駕駛員的月度統計
   - 支援年月篩選

3. **批次處理**
   - 處理單一日期
   - 處理日期範圍（最多 31 天）
   - 補齊缺失日期（自動找出最後處理日期到昨天的空缺）

4. **定時任務**
   - 每日自動執行（透過 APScheduler）
   - 處理前一天的駕駛時數
   - 手動觸發功能

#### API 端點
```
GET  /api/driving-stats/monthly-summary        # 月度彙總
GET  /api/driving-stats/daily/{date}           # 指定日期統計（即時計算）
POST /api/driving-stats/process-single         # 處理單一日期並儲存
POST /api/driving-stats/process-range          # 處理日期範圍
POST /api/driving-stats/process-missing        # 補齊缺失日期
GET  /api/driving-stats/last-processed-date    # 最後處理日期
GET  /api/driving-stats/scheduler/jobs         # 取得排程任務
POST /api/driving-stats/scheduler/run-now      # 立即執行任務
```

#### 與駕駛競賽的關係
- 舊專案：駕駛時數統計 → 用於駕駛競賽積分計算
- 新專案：直接從勤務表計算駕駛競賽，缺少每日統計細節

### 新專案現狀
- ✅ 有駕駛競賽功能（FR-032）
- ❌ **缺少每日駕駛時數詳細統計**
- ❌ 缺少月度彙總統計
- ❌ 缺少批次處理和補齊功能
- ❌ 缺少定時任務管理

### 建議補充方式
在新專案的 **User Story 5: 駕駛時數統計與競賽排名** 中補充：
- 每日駕駛時數詳細記錄
- 月度彙總統計功能
- 批次處理與補齊工具

---

## 三、考核系統 V2 升級（累計加重機制）

### 舊專案功能

#### V2 核心機制（2026年起）

**累計加重公式**：
```
倍率 = 1 + 係數 × (第N次 - 1)

範例（S 類違規，係數 = 0.5）：
- 第 1 次：1.0 倍（基本分數）
- 第 2 次：1.5 倍（+50%）
- 第 3 次：2.0 倍（+100%）
- 第 4 次：2.5 倍（+150%）
```

#### 資料模型擴充

**AssessmentStandard（考核標準表）V2 新增欄位**：
```python
- code: 項目代碼（如 "D01", "+A01"）
- category_code: 類別代碼（如 "D", "S", "R", "+A"）
- unit: 計分單位（每次、每月、每趟）
- is_accumulation_applicable: 是否適用累計加重（Boolean）
- custom_notes: 手寫備註
```

**AssessmentRecord（考核記錄）V2 新增欄位**：
```python
- accumulation_multiplier: 累計加重倍率（如 1.5）
- condition_flags: 條件加重標記（JSON）
- remarks: 備註說明
- occurred_at: 發生日期時間
- created_by: 建立者
- deleted_at: 軟刪除時間
```

#### 系統設定

**V2 考核規則配置**（`config/evaluation_rules_v2.json`）：
```json
{
  "version": "v2.0",
  "effective_date": "2026-01-01",
  "accumulation_coefficient": 0.5,  // 累計加重係數（可調整）
  "applicable_categories": ["D", "W", "O", "S", "R"]  // 適用類別
}
```

#### 主要功能

1. **雙版本並存**
   - 2025年以前：使用 V1（無累計加重）
   - 2026年起：使用 V2（含累計加重）
   - 根據事件日期自動選擇版本

2. **累計加重計算**
   - 自動統計該員工該類別的年度累計次數
   - 計算加重倍率
   - 套用至實際分數

3. **考核標準 Excel 匯入**
   - 管理員編輯 Excel 考核標準表
   - 點擊「匯入更新」批次匯入
   - 驗證資料格式
   - 更新資料庫

4. **考核歷史查詢**
   - 顯示員工所有考核記錄
   - 顯示每筆記錄的基本分數、倍率、實際分數
   - 統計年度總分

#### API 端點
```
GET  /api/assessments-v2/standards              # 取得 V2 考核標準
POST /api/assessments-v2/import-standards       # 匯入考核標準 Excel
GET  /api/assessments-v2/employee/{id}/history  # 員工考核歷史
POST /api/assessments-v2/calculate              # 計算累計加重分數
GET  /api/assessments-v2/rules                  # 取得考核規則設定
PUT  /api/assessments-v2/rules                  # 更新考核規則設定
```

### 新專案現狀
- ✅ 有責任事件懲罰係數（FR-032：`× 1/(1+N)`）
- ❌ **缺少累計加重機制**
- ❌ 缺少雙版本並存機制
- ❌ 缺少考核標準 Excel 匯入
- ❌ 缺少詳細的考核歷史查詢

### 建議補充方式
建議新增 **User Story 9: 考核系統 V2 升級（累計加重機制）**

---

## 四、差勤加分自動處理

### 舊專案功能

#### 核心概念
自動從 Google Sheets 班表讀取資料，逐員工判斷三種差勤加分情況並自動建立履歷。

#### 三種加分類型

1. **全勤（A01）**
   - 判斷邏輯：該月班表所有儲存格都沒有出現「(假)」字樣
   - 履歷描述：`{姓名}-{YYYYMM}-全勤`
   - 考核項目：A01

2. **R班出勤（A10）**
   - 判斷邏輯：識別格式 `R/...` 或 `R(國)/...`
   - 範例：`R/0905G`、`R(國)/1425G`
   - 履歷描述：`{姓名}-{YYYYMMDD}-R班出勤`
   - 考核項目：A10（+2分）
   - 每次出勤建立一筆獨立履歷

3. **臨時加班（A12~A15）**
   - 判斷邏輯：識別格式 `(+1)`, `(+2)`, `(+3)`, `(+4)`
   - 範例：`1425G(+2)` = 該班次加班 2 小時
   - 履歷描述：`{姓名}-{YYYYMMDD}-臨時加班{N}小時`
   - 考核項目：
     * (+1) → A12
     * (+2) → A13
     * (+3) → A14
     * (+4) → A15

#### 主要功能

1. **批次處理**
   - 選擇年月（如 2025年12月）
   - 系統自動讀取對應班表分頁（11412班表）
   - 逐員工處理全月資料

2. **防止重複**
   - 執行前檢查資料庫
   - 跳過已存在的履歷
   - 顯示「新增 X 筆」和「跳過 Y 筆（已存在）」

3. **處理結果統計**
   - 全勤新增 N 筆
   - R班出勤新增 N 筆
   - 臨時加班新增 N 筆
   - 詳細清單（員工姓名、類型、日期）

4. **複合情況處理**
   - 範例：`R/0905G(+2)`
   - 同時建立 R班出勤 + 臨時加班兩筆履歷

#### API 端點
```
POST /api/attendance-bonus/process              # 執行差勤加分處理
GET  /api/attendance-bonus/history/{year}/{month}  # 查詢處理歷史
```

#### 使用流程
```
1. 值班台人員進入「考核管理」頁面
2. 選擇年月（如 2025年12月）
3. 點擊「執行差勤加分處理」
4. 系統顯示進度（處理中...）
5. 顯示結果統計
6. 可展開查看詳細清單
```

### 新專案現狀
- ✅ 有 Google Sheets 班表同步（User Story 4）
- ❌ **完全沒有差勤加分自動處理功能**

### 建議補充方式
建議新增 **User Story 10: 差勤加分自動處理**

---

## 五、PDF OCR 切分功能

### 舊專案功能

#### 核心技術
- **OCR 引擎**: 使用 PyMuPDF + pyzbar
- **條碼識別**: Code128 條碼
- **文字識別**: 自動識別 PDF 文字內容

#### 主要功能

1. **條碼識別與 OCR**
   - 上傳多頁 PDF
   - 自動識別每頁的條碼
   - OCR 識別文字內容（備用方案）

2. **智慧切分**
   - 根據條碼自動切分 PDF
   - 每個條碼對應一個獨立檔案
   - 自動關聯資料庫履歷

3. **預覽修正**
   - 顯示識別結果
   - 允許手動修正未識別頁面
   - 手動指定履歷 ID

4. **批次儲存**
   - 一次儲存所有切分後的 PDF
   - 自動命名：根據履歷資料命名
   - 儲存到對應目錄

5. **Google Drive 上傳**
   - 一鍵上傳到 Google Drive
   - 自動更新履歷狀態為「已完成」
   - 記錄 Google Drive 連結

#### API 端點
```
POST /api/pdf-processing/upload                 # 上傳 PDF
GET  /api/pdf-processing/sessions/{id}          # 取得處理階段狀態
POST /api/pdf-processing/sessions/{id}/save     # 儲存切分結果
POST /api/pdf-processing/sessions/{id}/upload   # 上傳到 Google Drive
```

### 新專案現狀
- ✅ 有條碼識別（User Story 7）
- ❌ **缺少 OCR 文字識別**
- ❌ 缺少預覽修正介面
- ❌ 缺少批次儲存功能

### 建議補充方式
在 **User Story 7: PDF 條碼識別** 中補充：
- OCR 文字識別功能
- 預覽修正介面

---

## 六、未結案管理

### 舊專案功能

#### 核心概念
專門管理「已建立表單但尚未上傳 PDF」的履歷，追蹤文件處理進度。

#### 資料模型
```python
class PendingCase(Base):
    - id: 記錄 ID
    - profile_id: 關聯的履歷 ID（Unique）
    - case_type: 案件類型（事件調查、人員訪談等）
    - status: 狀態（待處理、處理中、已完成）
    - created_at: 建立時間
    - updated_at: 更新時間
    - completed_at: 完成時間

    Relationship: profile (一對一)
```

#### 主要功能

1. **未結案列表**
   - 顯示所有待上傳 PDF 的履歷
   - 按類型分類顯示
   - 按日期排序

2. **快速上傳**
   - 選擇履歷
   - 上傳對應的 PDF 檔案
   - 自動更新狀態為「已完成」

3. **狀態追蹤**
   - 待處理：已建立履歷但未產生文件
   - 處理中：已產生文件但未上傳 PDF
   - 已完成：已上傳 PDF 到 Google Drive

4. **統計資訊**
   - 各類型待處理案件數量
   - 最舊未結案日期
   - 完成率

#### API 端點
```
GET  /api/pending-cases                         # 取得未結案列表
GET  /api/pending-cases/stats                   # 取得統計資訊
POST /api/pending-cases/{id}/upload             # 上傳 PDF
PUT  /api/pending-cases/{id}/complete           # 標記為已完成
```

#### 使用流程
```
1. 值班台人員進入「未結案專區」
2. 查看所有待處理履歷
3. 選擇一筆履歷
4. 上傳掃描後的 PDF
5. 系統自動上傳到 Google Drive
6. 履歷從未結案列表中移除
```

### 新專案現狀
- ❌ **完全沒有未結案管理概念**

### 建議補充方式
建議新增 **User Story 11: 未結案管理系統**

---

## 七、詳細報表功能

### 舊專案功能

#### 兩種報表模式

1. **完整匯出**
   - 匯出所有欄位的 Excel 檔案
   - 包含：日期、時間、姓名、地點、車號、事件標題、事件描述、考核項目、考核分數、類型、狀態等
   - 支援篩選條件匯出

2. **技安專用簡化版**
   - 僅含三個欄位：
     * 事件日期
     * 司機員姓名
     * 事件標題
   - 簡潔格式，便於技安人員快速瀏覽

#### 主要功能

1. **考核統計報表**
   - 按月份統計所有員工考核分數
   - 自動排除已離職員工
   - 按分數排序
   - 支援 Excel 匯出

2. **履歷完整匯出**
   - 根據篩選條件匯出
   - 包含所有擴展欄位資料
   - 支援日期範圍、員工、類型等篩選

3. **自訂欄位匯出**
   - 允許選擇要匯出的欄位
   - 自訂欄位順序
   - 儲存匯出範本

#### API 端點
```
GET  /api/reports/profiles/full                 # 完整匯出
GET  /api/reports/profiles/safety-simplified    # 技安專用簡化版
GET  /api/reports/assessments/monthly           # 月度考核統計
POST /api/reports/custom                         # 自訂欄位匯出
```

### 新專案現狀
- ✅ 有基本報表功能
- ❌ **缺少技安專用簡化版**
- ❌ 缺少自訂欄位匯出
- ❌ 缺少考核統計報表（自動排除離職員工）

### 建議補充方式
在現有報表功能中補充：
- 技安專用簡化版本
- 自訂欄位匯出功能

---

## 八、Office 文件自動生成

### 舊專案功能

#### 核心機制
從資料庫資料自動填充 Word/Excel 範本檔案。

#### 支援格式

1. **Word 文件（.docx）**
   - 使用 python-docx
   - 支援書籤填充
   - 支援內容控制項填充
   - 適用於：事件調查、人員訪談、矯正措施

2. **Excel 文件（.xlsx）**
   - 使用 openpyxl
   - 支援指定儲存格填充
   - 適用於：加扣分通知單

#### 主要功能

1. **範本管理**
   - 空白表單儲存在 `空白表單/` 目錄
   - 每種類型有對應範本
   - 支援範本版本管理

2. **自動填充**
   - 從履歷主表取得基本資料
   - 從擴展表取得詳細資料
   - 自動帶入員工資料
   - 自動帶入班別資訊（從 Google Sheets）

3. **檔案命名**
   - 事件調查/人員訪談/矯正措施：
     `類型_YYYYMMDD_車號_地點_標題_姓名.docx`
   - 加扣分通知單：
     `類型_YYYYMMDD_標題_姓名.xlsx`

4. **檔案儲存**
   - 儲存到：`可編輯資料/[類型]/[年份]/[月份]/`
   - 自動建立資料夾結構
   - 同名檔案自動附加序號（_001, _002）

5. **自動開啟**
   - 填充完成後自動開啟文件
   - 使用者可確認內容
   - 需要時可手動編輯

#### API 端點
```
POST /api/files/generate-word                   # 產生 Word 文件
POST /api/files/generate-excel                  # 產生 Excel 文件
GET  /api/files/templates                       # 取得範本列表
POST /api/files/templates/upload                # 上傳新範本
```

### 新專案現狀
- ❌ **完全沒有 Office 文件自動生成功能**

### 建議補充方式
在 **User Story 8（履歷管理）** 中包含此功能

---

## 補充優先級建議

### P0（立即補充 - 核心功能）
1. ✅ **履歷管理系統** - 這是舊系統的核心，新系統缺少完整的事件記錄機制
2. ✅ **駕駛時數詳細統計** - 補充目前駕駛競賽功能的細節

### P1（短期補充 - 重要功能）
3. ✅ **考核系統 V2 升級** - 2026年需要累計加重機制
4. ✅ **差勤加分自動處理** - 大幅減少手動建立履歷的工作量
5. ✅ **未結案管理** - 追蹤文件處理進度

### P2（中期補充 - 輔助功能）
6. ⏸ **PDF OCR 切分** - 條碼識別已有，OCR 可延後
7. ⏸ **詳細報表功能** - 基本報表已有，進階功能可延後
8. ⏸ **Office 文件自動生成** - 可與履歷管理一起實作

---

## 下一步行動

### 建議的規格文件更新方式

1. **新增 User Story 8**: 司機員事件履歷管理系統
   - 涵蓋履歷 CRUD、類型轉換、Office 文件生成

2. **擴充 User Story 5**: 駕駛時數統計與競賽排名
   - 補充每日駕駛時數詳細記錄功能

3. **新增 User Story 9**: 考核系統 V2 升級
   - 涵蓋累計加重機制、雙版本並存

4. **新增 User Story 10**: 差勤加分自動處理
   - 涵蓋全勤、R班出勤、臨時加班自動判斷

5. **新增 User Story 11**: 未結案管理系統
   - 涵蓋待處理履歷追蹤、狀態管理

### 資料模型補充

需要新增的資料表：
```sql
profiles                    -- 履歷主表
event_investigation         -- 事件調查
personnel_interview         -- 人員訪談
corrective_measures         -- 矯正措施
assessment_notices          -- 加扣分通知單
pending_cases               -- 未結案管理
driving_daily_stats         -- 每日駕駛時數統計（已有部分）
assessment_standards        -- 考核標準表（V2 版本）
assessment_records          -- 考核記錄（V2 版本）
```

---

## 總結

舊專案是一個**以履歷為核心的事件管理系統**，新專案則是**以員工和駕駛競賽為核心的管理系統**。兩者的設計理念和核心架構有本質差異。

建議採取**漸進式整合**策略：
1. 先補充 P0 級別的核心功能（履歷管理、駕駛時數統計）
2. 再補充 P1 級別的重要功能（考核 V2、差勤加分、未結案管理）
3. 最後根據實際需求補充 P2 級別的輔助功能

這樣可以確保新專案既保留原有的駕駛競賽功能，又補充了舊專案的事件管理能力，形成一個更完整的司機員管理系統。
