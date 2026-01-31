# 舊專案完整功能規格報告

**專案名稱**: driver_profile_system_重構
**分析日期**: 2026-01-29
**分析範圍**: 完整的資料模型、API 端點、業務邏輯和 Google Services 整合

---

## 1. 履歷管理系統核心功能

### 1.1 資料模型（Database Schema）

#### profiles（履歷主表）
```python
- id: Integer, PK, 自動遞增
- version: Integer, 預設1（樂觀鎖版本號）
- profile_type: Enum（basic, event_investigation, personnel_interview, assessment_notice, corrective_measures）
- event_date: Date, 必填
- event_time: String(5)（HH:MM 格式）
- event_title: String(200), 必填
- employee_id: String(20), 必填
- employee_name: String(50), 必填, 索引
- event_location: String(100), 索引
- train_number: String(20), 索引
- event_description: Text, 必填
- data_source: String(100)
- assessment_item: String(200)
- assessment_score: Decimal(5,2)
- conversion_status: Enum（pending, converted, completed）
- file_path: String(500)
- gdrive_link: String(500)
- created_by: Integer, FK(users.id)
- created_at, updated_at: DateTime
```

#### 子表擴展

**1. event_investigation（事件調查）** - 1:1 關係
```python
- id: Integer, PK
- profile_id: Integer, FK(profiles.id), Unique
- incident_time: DateTime
- incident_location: String(200)
- witness_name: String(100)
- incident_cause: Text
- incident_process: Text
- improvement_suggestion: Text
- investigator: String(50)
- investigation_date: Date
- created_at, updated_at: DateTime
```

**2. personnel_interview（人員訪談）** - 1:1 關係
```python
- id: Integer, PK
- profile_id: Integer, FK(profiles.id), Unique
- interview_date: Date
- interviewer: String(50)
- incident_cause: Text
- interview_content: Text
- interview_result: Text（多選，逗號分隔）
- interview_result_other: String(200)
- follow_up_actions: Text（多選，逗號分隔）
- follow_up_actions_other: String(200)
- conclusion: Text
# 自動帶入欄位（從員工編號與 Google Sheets 班表取得）
- hire_date: String(10)（如 2021/11）
- shift1: String(50)（事件當天班別）
- shift2: String(50)（事件前一天班別）
- shift3: String(50)（事件前兩天班別）
- created_at, updated_at: DateTime
```

**3. corrective_measures（矯正措施）** - 1:1 關係
```python
- id: Integer, PK
- profile_id: Integer, FK(profiles.id), Unique
- incident_cause: Text
- corrective_action: Text
- created_at, updated_at: DateTime
```

**4. assessment_notices（考核加扣分通知單）** - 1:1 關係
```python
- id: Integer, PK
- profile_id: Integer, FK(profiles.id), Unique
- notice_type: Enum（addition, deduction）
- reason: Text
- issuer: String(50)
- issue_date: Date
- created_at, updated_at: DateTime
```

### 1.2 API 端點

#### 基礎 CRUD
```
GET    /api/profiles                    # 查詢履歷列表（支援多條件篩選）
GET    /api/profiles/{id}               # 取得履歷詳情（含子表資料）
POST   /api/profiles                    # 新增履歷
PUT    /api/profiles/{id}               # 更新履歷（支援並發衝突檢測）
DELETE /api/profiles/{id}               # 刪除履歷（含關聯記錄）
```

#### 特殊功能
```
GET  /api/profiles/employees            # 取得員工清單（下拉選單）
GET  /api/profiles/employee-history     # 查詢員工歷史履歷（1年內）
POST /api/profiles/{id}/convert         # 履歷類型轉換並儲存表單資料
POST /api/profiles/{id}/generate-file   # 重新產生檔案
```

### 1.3 履歷類型轉換機制

#### 轉換流程
1. 使用者選擇基本履歷並指定目標類型
2. 前端彈出對應的表單讓使用者填寫
3. 系統將表單資料儲存到對應子表
4. 從資料庫讀取資料填充到 Office 範本（Word/Excel）
5. 在 Word 文件中嵌入 Code128 條碼
   - 編碼格式：`{profile_id}|{type_code}|{year}|{month}`
6. 檔案儲存到本機路徑：`可編輯資料/{類型}/{年份}/{月份}/`
7. 自動開啟已填好資料的 Office 文件供確認

#### 檔案命名規則
- **事件調查/人員訪談/矯正措施**：`類型-YYYYMMDD_車號_地點_司機員_姓名.docx`
- **考核加扣分**：`類型_YYYYMMDD_司機員_姓名.xlsx`

### 1.4 Office 文件自動生成功能

#### 技術實作
- **Word 文件**：使用 `python-docx` 進行段落替換和核取方塊處理
- **Excel 文件**：使用 `openpyxl` 進行儲存格填充
- **條碼生成**：使用 `python-barcode` 生成 Code128 格式
- **核取方塊符號**：☑（checked）、☐（unchecked）

#### 特殊處理
- **人員訪談表單**：自動從 Google Sheets 班表取得員工班次資訊（事件當天、前1天、前2天）
- **多選欄位**：轉換為核取方塊（如訪談結果、追蹤辦理事項）

---

## 2. 駕駛時數統計系統

### 2.1 資料模型

#### driving_daily_stats（每日駕駛時數統計）
```python
- id: Integer, PK
- employee_id: String(20), 必填
- employee_name: String(50), 必填
- record_date: Date, 必填
- total_minutes: Integer（當日駕駛分鐘數）, 預設0
- incident_count: Integer（當日責任事件次數 R+S）, 預設0
- fiscal_year: Integer, 必填
- fiscal_month: Integer, 必填
- created_at: DateTime
- updated_at: DateTime

# 約束與索引
UniqueConstraint: (employee_id, record_date)
Index: employee_id
Index: record_date
Index: (fiscal_year, fiscal_month)
```

### 2.2 API 端點

#### 查詢與統計
```
GET /api/driving-stats/monthly-summary?year={year}&month={month}
    # 月度彙總統計（依總駕駛分鐘數排序）

GET /api/driving-stats/daily/{date}
    # 即時計算指定日期統計（不儲存）

GET /api/driving-stats/last-processed-date
    # 取得最後處理日期
```

#### 批次處理
```
POST /api/driving-stats/process-single
    Body: { "target_date": "2026-01-15" }
    # 處理單一日期並儲存

POST /api/driving-stats/process-range
    Body: { "start_date": "2026-01-01", "end_date": "2026-01-31" }
    # 批次處理日期範圍（限31天）

POST /api/driving-stats/process-missing
    # 自動補齊缺失日期（從最後處理日期到昨天）
```

#### 定時任務
```
GET  /api/driving-stats/scheduler/jobs
    # 查看排程任務狀態

POST /api/driving-stats/scheduler/run-now
    # 手動觸發駕駛時數統計任務（背景執行）
```

### 2.3 計算邏輯

#### 資料來源
- **Google Sheets 勤務表**：ID `1HKGd2LzS8p93UvGiOfcePw4Tn_JoJyLbkQKCLtfnnE4`
- **分頁命名格式**：`{民國年}{月份}班表`（如 `11412班表`）
- **資料結構**：從第5列開始，第9欄（I欄）起為勤務內容

#### 計算流程
1. 解析班表找出每位員工的勤務內容
2. **正規化路線名稱**：
   - 移除月台標記：`(1)`, `(2)`, `（1）`, `（2）`
   - 全形數字轉半形
   - 統一分隔符號：`→`, `>`, `-`, `~` 都轉成 `往`
3. 從 Excel 對照表（`駕駛分數計算.xlsx`）查找駕駛分鐘數
4. 累計「駕駛」和「巡軌」任務的總分鐘數
5. **固定任務**加入固定分鐘數：
   - 整備、移車、收車、回送、清車
6. 計算責任事件次數（從 AssessmentRecord 查詢 R 類和 S 類扣分）

#### 路線正規化範例
```
"淡-紅(1)" → "淡往紅"
"淡→紅樹(2)" → "淡往紅樹"
"淡~紅" → "淡往紅"
"淡１紅" → "淡往紅"（全形數字轉半形並移除）
```

### 2.4 與駕駛競賽的關係

駕駛時數統計為未來的駕駛競賽功能提供基礎資料：
- **每月總駕駛分鐘數**排名
- **責任事件次數**（R+S 扣分）評比
- **安全駕駛指標**：駕駛時數 vs. 事件次數比率

---

## 3. 考核系統 V2 詳細功能

### 3.1 資料模型

#### assessment_standards（考核標準表）

**V1 欄位（2025年以前）**
```python
- id: Integer, PK
- item_name: String(200), 必填
- category: Enum（addition, deduction）, 必填
- base_score: Decimal(5,2), 必填
- description: Text
- version: String(20), 必填
- effective_date: Date, 必填
- created_at: DateTime
```

**V2 新增欄位（2026年起）**
```python
- code: String(10)（項目代碼，如 D01, +M01）
- category_code: String(5)（類別代碼，如 D, W, O, S, R, +M, +A, +B, +C, +R）
- unit: String(10)（計分單位：每次/每月/每趟）
- is_accumulation_applicable: Boolean（是否適用累計加重）
- custom_notes: Text（手寫備註，支援關鍵字搜尋）
- updated_at: DateTime
```

**索引**
```python
Index: item_name
Index: category
Index: code
Index: category_code
```

#### assessment_records（考核記錄）

**V1 欄位**
```python
- id: Integer, PK
- profile_id: Integer, FK(profiles.id), 必填
- employee_id: String(20), 必填
- employee_name: String(50), 必填
- item_id: Integer, FK(assessment_standards.id), 必填
- base_score: Decimal(5,2), 必填
- weighted_score: Decimal(5,2), 必填
- occurrence_count: Integer, 必填
- fiscal_year: Integer, 必填
- created_at: DateTime
```

**V2 新增欄位（2026年起）**
```python
- accumulation_multiplier: Decimal(4,2)（累計加重倍率）, 預設1.0
- condition_flags: Text（JSON 格式條件加重標記）
- remarks: Text（備註說明）
- occurred_at: DateTime（發生日期時間）
- created_by: String(50)
- deleted_at: DateTime（軟刪除時間）
```

**索引**
```python
Index: employee_id
Index: fiscal_year
Index: (employee_id, fiscal_year)
Index: occurred_at
```

### 3.2 累計加重機制

#### 公式
```
實際扣分 = 基本分 × [1 + 係數 × (N-1)]

其中：
- N = 當年度該類別的累計次數
- 係數 = 0.5（可在系統設定調整）
```

#### 範例（S 類違規，係數 = 0.5）
```
第1次：基本分 × 1.0 = 基本分
第2次：基本分 × 1.5 = 基本分 × 1.5
第3次：基本分 × 2.0 = 基本分 × 2.0
第4次：基本分 × 2.5 = 基本分 × 2.5
```

#### 不適用累計加重的項目
```
D05（曠職）
W04, W05, W07（重大業務違規）
S12, S13, S16（重大行車安全違規）
```

#### 計算邏輯
1. **累計按類別**：相同類別代碼（如 D 類）的所有項目累計
2. **年度歸零**：每年 1/1 歸零
3. **以履歷為單位**：同一履歷僅計入一次
4. **自動重算**：移除考核項目或改判非過失時，自動重算全年累計次數

### 3.3 API 端點

#### 考核記錄管理
```
POST /api/assessments/v2/records
    Body: { "profile_id", "employee_id", "code", "occurred_at", ... }
    # 新增考核記錄（自動計算累計加重）

GET /api/assessments/v2/occurrence-count/{employee_id}/{code}/{year}
    # 取得特定項目發生次數

GET /api/assessments/v2/yearly/{employee_id}/{year}
    # 取得年度考核摘要
```

#### 月度獎勵
```
GET /api/assessments/v2/monthly-bonus/{employee_id}/{year}/{month}
    # 取得月度獎勵判定（全勤、零違規等）
```

#### 考核標準管理
```
GET /api/assessments/v2/standards
    Query: category_code, type, keyword
    # 取得考核標準列表（支援類別/類型/關鍵字篩選）

GET /api/assessments/v2/standards/search?q={keyword}
    # 關鍵字搜尋考核項目

PATCH /api/assessments/v2/standards/{code}/notes
    Body: { "custom_notes": "..." }
    # 更新手寫備註
```

### 3.4 考核標準表管理

#### 考核項目結構

**5類扣分項目（共54項）**
- **D（差勤）**：D01~D06
- **W（業務）**：W01~W14
- **O（操作）**：O01~O12
- **S（行車安全）**：S01~S17
- **R（責任事件）**：R01~R05

**5類加分項目（共31項）**
- **+M（月度獎勵）**：+M01~+M03
- **+A（差勤加分）**：+A01~+A06
- **+B（業務加分）**：+B01~+B06
- **+C（進修競賽）**：+C01~+C07
- **+R（責任加分）**：+R01~+R09

#### 手寫備註功能
- 允許值班台人員為考核項目新增**自訂關鍵字**
- 支援透過手寫備註搜尋項目
  - 範例：為 +R07 加註 "ERR" 方便搜尋
- 欄位上限：500 字元

### 3.5 差勤加分自動處理

#### 資料來源
- **Google Sheets 班表**：ID `15Y6H2GKFJQUUJvHkoBCmT4fW4HxET9qJWZi4sX08pCQ`
- **分頁格式**：`{民國年}{月份}班表`（如 `11412班表` = 2025年12月）

#### 自動判定項目

**1. 月度全勤（+M01）**
- **條件**：當月無 D01（遲到/早退）、D05（曠職）
- **分數**：+3 分

**2. 月度行車零違規（+M02）**
- **條件**：當月無 O 類、S 類扣分
- **分數**：+1 分

**3. 月度全項目零違規（+M03）**
- **條件**：當月無任何扣分
- **分數**：+2 分

**4. R班出勤（+A01）**
- **判斷邏輯**：班表有 `R/...` 或 `R(國)/...`
- **範例**：`R/0905G`, `R(國)/1425G`
- **分數**：+3 分/次
- **建立規則**：每次出勤建立一筆獨立履歷

**5. 延長工時（+A03~+A06）**
- **判斷邏輯**：班表有 `(+1)`, `(+2)`, `(+3)`, `(+4)`
- **範例**：`1425G(+2)` = 該班次加班 2 小時
- **分數**：
  - (+1) → +A03 → +0.5 分
  - (+2) → +A04 → +1.0 分
  - (+3) → +A05 → +1.5 分
  - (+4) → +A06 → +2.0 分

#### 處理邏輯

**1. 全勤判定**
- 掃描整月班表
- 所有儲存格都不包含「(假)」字樣 → 符合全勤

**2. 防止重複**
- 建立前檢查資料庫
- 比對事件描述（如 `{姓名}-202512-全勤`）
- 已存在則跳過

**3. 批次處理**
- 一次處理整個月份的所有員工
- 逐員工判斷三種加分情況

**4. 結果統計**
- 分類顯示：
  - 全勤新增 X 筆
  - R班出勤新增 Y 筆
  - 延長工時新增 Z 筆
  - 跳過 N 筆（已存在）

---

## 4. 其他關鍵功能

### 4.1 PDF 條碼識別與切分功能

#### 資料模型
- **會話管理**：記憶體內的 Session Manager（不儲存資料庫）
- **處理流程**：Upload → Barcode Recognition → Preview → Save/Upload to GDrive

#### API 端點
```
POST /api/pdf-processing/upload
    # 上傳 PDF 並條碼識別

POST /api/pdf-processing/upload-batch
    # 批次上傳多個 PDF

GET /api/pdf-processing/sessions/{id}
    # 取得處理會話狀態

POST /api/pdf-processing/sessions/{id}/update-barcode
    # 手動修正條碼資訊

POST /api/pdf-processing/sessions/{id}/skip-page
    # 跳過頁面

POST /api/pdf-processing/sessions/{id}/save
    # 儲存切分後的 PDF

POST /api/pdf-processing/sessions/{id}/upload-to-gdrive
    # 上傳到 Google Drive
```

#### 條碼識別流程
1. 從每頁**底部 10% 區域**識別 Code128 條碼
2. 解碼條碼內容：`{profile_id}|{type_code}|{year}|{month}`
3. 依條碼內容分組頁面（相同 ID 的連續頁面合併）
4. 查詢資料庫取得履歷資料
5. 依空白表單命名規則產生建議檔名
6. 提供預覽介面供使用者確認或修正

#### 條碼編碼格式
```
Format: {profile_id}|{type_code}|{year}|{month}

profile_id: 履歷 ID（純數字）
type_code: 事件種類代碼
  - EI: 事件調查（Event Investigation）
  - PI: 人員訪談（Personnel Interview）
  - CM: 矯正措施（Corrective Measures）
  - AA: 考核加分（Assessment Addition）
  - AD: 考核扣分（Assessment Deduction）
  - OT: 其他（Other）
year: 年份（YYYY）
month: 月份（MM，補零）

範例：123|EI|2026|01
```

### 4.2 未結案管理

#### 資料模型

**pending_cases（未結案項目）**
```python
- id: Integer, PK
- profile_id: Integer, FK(profiles.id), Unique
- profile_type: String(20)
- event_date: Date
- employee_name: String(50)
- status: Enum（pending, uploaded）
- gdrive_file_id: String(100)
- gdrive_web_link: String(500)
- created_at: DateTime
- updated_at: DateTime
```

#### 業務邏輯
1. **自動建立**：當履歷轉換為特定類型時，自動建立 PendingCase 記錄
2. **狀態更新**：使用者上傳 PDF 到 Google Drive 成功後，更新狀態為 uploaded
3. **同步更新**：同時更新 Profile 表的 conversion_status 為 completed
4. **顯示規則**：未結案專區只顯示 status = pending 的記錄

#### API 端點
```
GET /api/pending-cases
    # 取得未結案列表

GET /api/pending-cases/stats
    # 取得統計資訊（各類型待處理數量）

POST /api/pending-cases/{id}/upload
    # 上傳 PDF

PUT /api/pending-cases/{id}/complete
    # 標記為已完成
```

### 4.3 報表功能

#### 資料模型
- 無獨立資料表
- 從 Profile 和 AssessmentRecord 動態查詢

#### API 端點

**考核月報表**
```
GET /api/reports/monthly-ranking?year={year}&month={month}
    # 考核月報表排名查詢

GET /api/reports/monthly-details?year={year}&month={month}
    # 考核月報表明細查詢

GET /api/reports/monthly-export?year={year}&month={month}
    # 考核月報表匯出（Excel）
```

**個人統計圖表**
```
GET /api/reports/personal-statistics?employee_id={id}&keywords={k1,k2}&types={t1,t2}
    # 個人統計圖表查詢

GET /api/reports/personal-export?employee_id={id}&...
    # 個人統計圖表匯出（Excel）
```

#### 報表功能詳細

**1. 考核月報表**

**排名表格**：
- 欄位：排名、員工編號、姓名、加分總分、扣分總分、淨分數、總分
- **並列排名（跳號）**：總分相同時排名並列
  - 範例：1, 1, 3, 4（沒有第2名）

**考核明細分頁**：
- 顯示所有考核事件詳細資料
- 欄位：日期、員工、考核項目、分數、累計次數、倍率、實際分數

**Excel 匯出**：
- **第一分頁**：排名 + 簽章欄位
- **第二分頁**：考核明細

**2. 個人統計圖表**

**折線圖呈現**：
- **橫軸**：月份（1-12月）
- **縱軸**：履歷次數

**篩選功能**：
- **關鍵字篩選**：同時搜尋事件標題、事件描述、考核項目
- **履歷類型篩選**：加分履歷、扣分履歷、無關考核

**多線條顯示**：
- 不同關鍵字/類型以不同顏色區分
- 支援同時顯示多條趨勢線

**Excel 匯出**：
- 包含圖表和數據表格

---

## 5. Google Services 整合

### 5.1 Google Drive 整合

#### 認證方式
- **OAuth 2.0**（使用 credentials.json）
- **Token 儲存**：`config/token.pickle`
- **授權範圍**：`https://www.googleapis.com/auth/drive.file`

#### 主要功能
1. **自動建立資料夾結構**：`{類型}/{年份}/{月份}/`
2. **上傳 PDF 檔案**並取得分享連結
3. **資料夾 ID 儲存**於 SystemSetting 表

#### 服務類別
```python
class GoogleDriveService:
    def find_folder(name, parent_id)
        # 在指定父資料夾中尋找子資料夾

    def create_folder(name, parent_id)
        # 建立資料夾

    def upload_file(file_content, filename, folder_id, mime_type)
        # 上傳檔案到指定資料夾

    def upload_file_to_configured_folder(profile_type, year, month, file_content, filename)
        # 上傳到已設定的資料夾結構
```

### 5.2 Google Sheets 整合

#### 使用場景
1. **班表讀取（駕駛時數統計）**
2. **班表讀取（差勤加分處理）**
3. **班表讀取（人員訪談表單填充）**

#### 認證方式
- **Service Account**（使用 `google_sheets_api_credentials .json`）
- **授權範圍**：`https://www.googleapis.com/auth/spreadsheets.readonly`（唯讀）

#### 服務類別
```python
class ScheduleService:
    SPREADSHEET_ID = "15Y6H2GKFJQUUJvHkoBCmT4fW4HxET9qJWZi4sX08pCQ"

    def read_monthly_schedule(year, month)
        # 讀取指定月份的班表資料
        # 回傳：{ employee_id: { date: shift_code, ... }, ... }

    def process_attendance_bonus(year, month, db, username)
        # 處理差勤加分（全勤、R班出勤、延長工時）
        # 回傳：處理統計結果

    def get_employee_shifts(employee_name, target_date)
        # 取得員工事件當天前後3天班次
        # 用於人員訪談表單自動填充
        # 回傳：{ "shift1": "...", "shift2": "...", "shift3": "..." }
```

---

## 6. 技術架構總結

### 後端技術棧
```
Framework: FastAPI
ORM: SQLAlchemy
Database: SQLite（WAL mode）
Validation: Pydantic
Scheduler: APScheduler
```

### 前端技術棧
```
Template: Jinja2
Languages: HTML, CSS, JavaScript
Chart: Chart.js
```

### 關鍵套件

**Office 檔案處理**
```
python-docx    # Word 文件生成
openpyxl       # Excel 文件生成
```

**條碼與 PDF**
```
python-barcode # 條碼生成
Pillow         # 圖像處理
PyPDF2         # PDF 處理
pdf2image      # PDF 轉圖片
pyzbar         # 條碼識別
opencv-python  # 圖像預處理
```

**Google Services**
```
google-api-python-client  # Google API 客戶端
google-auth               # 認證
google-auth-oauthlib      # OAuth
google-auth-httplib2      # HTTP 傳輸
```

### 專案結構
```
driver_profile_system/
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI 路由
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── services/     # 業務邏輯服務
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── utils/        # 工具函式
│   │   └── main.py       # FastAPI 入口
│   └── tests/            # 測試
│
├── frontend/
│   ├── static/           # 靜態檔案（CSS, JS, 圖片）
│   └── templates/        # Jinja2 模板
│
├── config/               # 設定檔
│   ├── credentials.json           # OAuth 2.0 憑證
│   ├── google_sheets_api_credentials .json  # Service Account
│   ├── token.pickle               # OAuth Token
│   ├── evaluation_standards.json  # V1 考核標準
│   ├── evaluation_standards_v2.json  # V2 考核標準
│   └── evaluation_rules_v2.json   # V2 考核規則
│
├── database/             # SQLite 資料庫
│   ├── driver_profile.db
│   └── backups/          # 自動備份
│
├── 可編輯資料/           # 產生的 Office 檔案
│   ├── 事件調查/
│   ├── 人員訪談/
│   ├── 加扣分資料/
│   └── 矯正措施/
│
├── 空白表單/             # Office 範本檔案
│   ├── 事件調查紀錄表.docx
│   ├── 人員訪談紀錄表.docx
│   ├── 矯正措施紀錄表.docx
│   └── 考核加扣分通知單.xlsx
│
└── 考核標準表/           # 考核標準 Excel 原始檔
```

---

## 7. 資料庫 Schema 完整列表

```sql
-- 使用者管理
users                   -- 使用者帳號

-- 員工管理
employees               -- 員工基本資料

-- 履歷管理
profiles                -- 履歷主表
event_investigation     -- 事件調查
personnel_interview     -- 人員訪談
corrective_measures     -- 矯正措施
assessment_notices      -- 加扣分通知單
pending_cases           -- 未結案項目

-- 考核管理
assessment_standards    -- 考核標準表
assessment_records      -- 考核記錄

-- 駕駛統計
driving_daily_stats     -- 每日駕駛時數統計

-- 系統設定
system_settings         -- 系統設定（Google Drive 資料夾 ID 等）
audit_logs              -- 操作日誌
```

---

這份報告涵蓋了 `driver_profile_system_重構` 專案的所有核心功能規格，包含資料模型、API 端點、業務邏輯和 Google Services 整合方式的詳細說明。可作為新專案 `driver_management_system` 的完整參考資料。
