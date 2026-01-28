# Feature Specification: 司機員管理系統整體架構

**Feature Branch**: `001-system-architecture`
**Created**: 2026-01-28
**Status**: Draft
**Priority**: P0 (Foundation)

## Executive Summary

建立新北捷運輕軌營運處車務中心「司機員事件履歷與考核管理、駕駛時數管理系統」，支援淡海分處與安坑分處雙部門架構，整合 Google Sheets 班表/勤務表資料、Google Drive 文件管理、駕駛競賽排名計算。

**系統架構**（混合式三層架構）：
- **前端**：GitHub Pages 託管的網頁應用（Vue.js/React），作為主要使用者介面
- **雲端後端**：Render 部署的 FastAPI 服務 + TiDB MySQL 資料庫
- **本機應用**：桌面應用程式提供本機 API（localhost:8000），負責檔案操作（Word生成、PDF掃描、條碼生成、Google Drive上傳）

**容錯設計**：核心功能（資料瀏覽、履歷建立、員工管理、報表查詢）完全運行於網頁端，即使桌面應用程式發生錯誤或未啟動，仍可正常使用系統的基本功能。檔案生成功能在桌面應用不可用時，會給予明確提示。

---

## Glossary ⭐ **(新增：術語表)**

本章節定義專案中使用的關鍵術語，確保團隊溝通一致性。

### 憑證與認證

| 術語 | 定義 | 用途 | 範例 |
|------|------|------|------|
| **Service Account** | Google 服務帳戶憑證，用於伺服器端應用程式 | 讀取 Google Sheets（班表、勤務表） | `alarm-kunpeto@lateral-shore-461508-m0.iam.gserviceaccount.com` |
| **OAuth 2.0 憑證** | Google OAuth 2.0 客戶端憑證，用於使用者授權流程 | 使用者授權後上傳檔案到 Google Drive | `client_id`, `client_secret`, `redirect_uris` |
| **Refresh Token** | OAuth 2.0 長期有效令牌，用於自動更新 Access Token | 本機/雲端儲存，用於自動化上傳 | 有效期：無限期（直到使用者撤銷） |
| **Access Token** | OAuth 2.0 短期有效令牌，用於實際 API 請求 | 由 Refresh Token 換取，每次請求使用 | 有效期：1 小時 |

### 系統架構

| 術語 | 標準名稱 | 別名（避免使用） | 定義 |
|------|---------|----------------|------|
| **GitHub Pages** | GitHub Pages | 前端網頁、靜態網站 | 託管於 GitHub Pages 的 Vue.js 前端應用 |
| **雲端 API** | Render FastAPI | 雲端後端、Render 後端 | 部署於 Render 的 FastAPI 後端服務（包含資料 CRUD、認證、Google Sheets 同步） |
| **本機 API** | 本機桌面應用 API | 桌面應用、本機後端 | 執行於 localhost:8000 的 FastAPI 服務（檔案處理：Word、PDF、條碼、Drive 上傳） |
| **TiDB** | TiDB MySQL | 雲端資料庫、MySQL 資料庫 | TiDB Serverless（MySQL 8.0 相容）共享資料庫 |

### Google 服務

| 術語 | 定義 | 資料範例 |
|------|------|---------|
| **Google Sheets 班表** | 115年度_班表暨每月R出需求&加班工時總表 | Sheet ID: `15Y6H2GKFJQUUJvHkoBCmT4fW4HxET9qJWZi4sX08pCQ` |
| **Google Sheets 勤務表** | (目前使用中)202601_勤務表 | Sheet ID: `1HKGd2LzS8p93UvGiOfcePw4Tn_JoJyLbkQKCLtfnnE4` |
| **Google Drive 資料夾** | 淡海/安坑的文件儲存資料夾 | Folder ID: `1NhgiXcYQ5NTRQzmHgLSLqU8M8Ysf3-18`（淡海） |
| **R班** | 休息日出勤，駕駛競賽時數 × 2 | 從班表的「班別」欄位判定 |

### 部門與角色

| 術語 | 定義 | 值域 |
|------|------|------|
| **部門** | 新北捷運輕軌營運處車務中心的分處 | `淡海`、`安坑`（硬編碼，不可新增刪除） |
| **Admin（管理員）** | 系統管理人員，擁有所有權限 | 全部功能 + 後台參數管理 + 雙部門完整權限 |
| **Staff（值班台人員）** | 各分處值班台人員，負責資料維護 | 本部門資料 CRUD + 他部門資料唯讀 |
| **Manager（主管）** | 主管角色，僅查詢與報表產出 | 所有部門資料唯讀 + 報表產出 |

### 資料模型

| 術語 | 定義 | 說明 |
|------|------|------|
| **員工編號** | 員工唯一識別碼 | 格式：YYMMX0XXX（如 1011M0095 = 2021年11月入職） |
| **履歷** | 員工事件記錄（S類安全責任、R類維護責任） | `profiles` 資料表 |
| **調動記錄** | 員工部門調動歷史 | `employee_transfers` 資料表 |
| **駕駛時數** | 每日駕駛分鐘數統計 | `driving_daily_stats` 資料表 |
| **駕駛競賽** | 月度駕駛積分排名 | `driving_competition` 資料表 |
| **勤務標準時間** | 各勤務路線的標準駕駛時間（分鐘） | `route_standard_times` 資料表 |

### 技術術語

| 術語 | 定義 | 技術細節 |
|------|------|---------|
| **Fernet 加密** | 對稱加密演算法，用於加密敏感資料 | `cryptography.fernet`，金鑰長度 44 字元（Base64） |
| **Base64 編碼** | 二進制資料編碼為可儲存文字 | 用於 Service Account JSON 儲存於環境變數 |
| **bcrypt** | 密碼雜湊演算法 | 成本因子最低 12，用於使用者密碼 |
| **JWT (JSON Web Token)** | 使用者認證令牌 | payload 包含 `user_id`, `role`, `department`, `exp` (過期時間), `iat` (發行時間)，有效期限 24 小時 |
| **CORS (Cross-Origin Resource Sharing)** | 跨域資源共享 | GitHub Pages → Render API / localhost API |

---

## Technical Architecture ⭐ **(新增：架構說明)**

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                         使用者（瀏覽器）                              │
│                   Chrome / Edge / Firefox                        │
└──────────────┬────────────────────────────┬─────────────────────┘
               │                            │
               │ HTTPS                      │ HTTP (localhost)
               │                            │
               ▼                            ▼
┌─────────────────────────────┐  ┌──────────────────────────────┐
│  GitHub Pages (前端)          │  │  本機桌面應用 API             │
│  - Vue.js / React            │  │  - FastAPI (localhost:8000) │
│  - 靜態網頁託管               │  │  - Word / PDF / 條碼生成     │
│  - 主要使用者介面             │  │  - Google Drive 上傳         │
└──────────────┬──────────────┘  └──────────────┬───────────────┘
               │                                │
               │ HTTPS                          │
               │ (跨域請求)                      │ Google Drive API
               │                                │
               ▼                                ▼
┌─────────────────────────────┐  ┌──────────────────────────────┐
│  Render 雲端 FastAPI          │  │  Google Drive                │
│  - RESTful API               │  │  - 文件儲存                   │
│  - 使用者認證 (JWT)           │  └──────────────────────────────┘
│  - 資料 CRUD                 │
│  - 定時任務 (APScheduler)     │
└──────────────┬──────────────┘
               │
               │ MySQL Protocol (SSL/TLS)
               │
               ▼
┌─────────────────────────────┐
│  TiDB Serverless (資料庫)    │
│  - MySQL 8.0 相容             │
│  - 5GB 儲存空間               │
│  - 員工、履歷、駕駛時數資料    │
└─────────────────────────────┘
```

### 三層架構職責劃分

#### Layer 1: 前端網頁應用（GitHub Pages）
**技術堆疊**：Vue.js 3 / React + Axios + Element Plus / Ant Design

**職責**：
- ✅ 主要使用者介面（資料列表、表單、報表）
- ✅ 使用者互動處理（點擊、輸入、導航）
- ✅ 狀態管理（Pinia / Redux）
- ✅ 路由管理（Vue Router / React Router）
- ✅ 與雲端 API 通訊（資料 CRUD）
- ✅ 檢測本機桌面應用 API 可用性
- ✅ 容錯設計：桌面應用不可用時禁用檔案功能按鈕

**關鍵特性**：
- 無需安裝，開啟瀏覽器即可使用
- 跨平台支援（Windows / macOS / Linux）
- 自動部署（push 到 GitHub 即更新）

---

#### Layer 2: 雲端後端 API（Render FastAPI）
**技術堆疊**：FastAPI + SQLAlchemy + TiDB + APScheduler

**職責**：
- ✅ 資料庫 CRUD 操作（員工、履歷、駕駛時數）
- ✅ 使用者認證與授權（JWT Token）
- ✅ 權限控制中間件（Admin / Staff / Manager）
- ✅ Google Sheets 同步（班表、勤務表）
- ✅ 駕駛競賽排名計算
- ✅ 定時任務管理（APScheduler）
- ✅ 資料庫備份與監控

**關鍵特性**：
- 24/7 運行（UptimeRobot 保持喚醒）
- RESTful API 設計
- 完整錯誤處理與日誌記錄

---

#### Layer 3: 本機桌面應用 API（FastAPI localhost）
**技術堆疊**：FastAPI + python-docx + PyPDF2 + python-barcode + Google Drive API

**職責**：
- ✅ Word 文件生成（履歷報告、通知書）
- ✅ PDF 掃描與條碼識別（部門判斷）
- ✅ 條碼生成（TH/AK 前綴）
- ✅ Google Drive 檔案上傳
- ❌ 不負責資料庫操作（僅檔案處理）

**關鍵特性**：
- 僅在需要檔案操作時啟動
- CORS 設定允許 GitHub Pages 跨域請求
- 系統托盤常駐（啟動/停止 API）
- 失敗不影響核心功能

---

### 資料流向範例

#### 情境 1：使用者新增員工資料（核心功能）
```
使用者 → 前端網頁（填寫表單）
     → 雲端 API（POST /api/employees）
     → TiDB 資料庫（INSERT）
     → 回傳成功
     → 前端顯示成功訊息
```
**無需桌面應用參與** ✅

---

#### 情境 2：使用者生成履歷 Word 文件（檔案功能）
```
使用者 → 前端網頁（點擊「生成 Word」按鈕）
     → 檢測本機 API（localhost:8000/health）
     → 若本機 API 不可用：顯示「請啟動桌面應用程式」❌
     → 若本機 API 可用：
         → 本機 API（POST /api/generate-word）
         → 生成 Word 檔案
         → 回傳下載連結
         → 前端觸發下載
```
**需要桌面應用，但失敗不影響其他功能** ✅

---

### 容錯設計說明

| 情境 | 桌面應用狀態 | 核心功能 | 檔案功能 | 使用者體驗 |
|------|-------------|---------|---------|-----------|
| 正常運行 | ✅ 運行中 | ✅ 可用 | ✅ 可用 | 完整功能 |
| 桌面應用未啟動 | ❌ 未執行 | ✅ 可用 | ❌ 禁用 | 提示「請啟動桌面應用」 |
| 桌面應用錯誤 | ❌ 執行異常 | ✅ 可用 | ❌ 禁用 | 提示「桌面應用發生錯誤」 |
| 網路中斷 | N/A | ❌ 不可用 | ❌ 不可用 | 提示「無法連接伺服器」 |

**設計原則**：核心功能（資料瀏覽、履歷建立、員工管理）完全獨立於桌面應用，即使桌面應用故障，使用者仍可正常使用系統的 80% 功能。

---

## Pending Clarifications

### 🔴 HIGH PRIORITY - 需立即釐清

#### ~~PC-001: 駕駛競賽計算公式~~ ✅ **(已釐清 2026-01-28)**

**決策結果**：駕駛競賽計算公式已確認

**完整計算公式**（每月結算）：
```
最終積分 = Σ(每日勤務時數 × R班係數) × 責任事件懲罰係數

其中：
- 每日勤務時數 = Σ(當日各項勤務的標準分鐘數)
  ├─ 勤務標準時間由後台設定（route_standard_times 資料表）
  └─ 從 Google Sheets 勤務表讀取當日勤務項目

- R班係數：
  ├─ 當日為 R班出勤（休息日出勤）：× 2
  └─ 一般出勤：× 1

- 責任事件懲罰係數：× 1/(1+N)
  ├─ N = 0（當月無責任事件）：× 1
  ├─ N = 1（當月 1 件責任事件）：× 1/2
  ├─ N = 2（當月 2 件責任事件）：× 1/3
  └─ N ≥ 3：× 1/(1+N) 依此類推
```

**排名規則** ⭐ **(已補充 2026-01-28)**：
- **主要排序**：積分由高到低（積分最高者為第一名）
- **積分相同處理**：並列排名（如兩人並列第 2 名）
  - 下一名的排名跳號（並列第 2 名後，下一名為第 4 名）
  - 報表顯示格式：僅顯示排名數字（如「2」），不額外標註並列
  - 次要排序（積分相同時）：按員工編號升序（資料呈現穩定性）
- **排名範例**：
  | 排名 | 姓名 | 積分 |
  |------|------|------|
  | 1    | 張三 | 1250 |
  | 2    | 李四 | 1100 |
  | 2    | 王五 | 1100 |
  | 4    | 趙六 | 980  |
- **其他規則**：
  - 無最低出勤天數門檻
  - 每人每月皆有排名（含積分為 0 者）
  - 離職或不在職人員不納入排名計算

**責任事件判定**：
- **暫時保留此功能**，後續與考核模組整合（Phase 2+）
- 初版計算僅考慮駕駛時數與 R班加倍

**參考文件**：`C:\Users\kunpe\claude專案\115年度駕駛時數簽文製作\115年度當責駕駛時數激勵方案_最終版.docx`

#### PC-002: 安坑班表結構
**問題**：安坑分處的 Google Sheets 班表結構是否與淡海相同
- 欄位順序是否一致？
- 班別代碼是否一致？
- 分頁命名規則是否一致？

**影響範圍**：班表同步模組
**備選方案**：先實作淡海（使用前專案邏輯），安坑暫時手動輸入
**預計釐清**：Phase 3 安坑模組實作前

### 🟡 MEDIUM PRIORITY - 可延後釐清

#### PC-003: 勤務表詳細結構
**問題**：Google Sheets 勤務表的欄位定義
- 包含哪些欄位？（員工編號、日期、班別、駕駛時數、...？）
- 如何計算每日駕駛分鐘數？
- 責任事件數是否在勤務表中？還是從考核資料庫計算？

**影響範圍**：駕駛時數同步模組
**備選方案**：根據淡海現有資料反推結構
**預計釐清**：Phase 2 駕駛時數模組實作時

#### PC-004: 報表需求細節
**問題**：主管角色需要哪些具體報表
- 考核統計報表（格式？欄位？）
- 駕駛時數統計（日報？月報？年報？）
- 駕駛競賽排名報表（格式？）
- 其他自訂報表？

**影響範圍**：報表模組
**備選方案**：先實作前專案已有的報表，再根據需求擴充
**預計釐清**：Phase 4 報表模組實作時

#### ~~PC-005: 歷史資料遷移需求~~ ✅ **(已釐清 2026-01-28)**
**決策結果**：採用方案 A（完整遷移 2026 年前資料，預設淡海部門）

**資料量分析**：
- 需遷移履歷資料：580 筆（2023-2025 年）
- 員工資料：58 位
- 總資料量：約 1.4 MB（佔 TiDB 5GB 的 0.03%）

**欄位處理策略**：
1. ✅ `current_department`：所有歷史資料預設為「淡海」
2. ✅ `hire_year_month`：從員工編號自動解析（如 1011M0095 → 2021-11）
3. ✅ `phone/email/緊急聯絡人`：保持 NULL，後續手動補充
4. ❌ `assessment_standards`：不遷移，新系統使用新版本

**執行時程**：
- 遷移方案已確定（詳見 `docs/data_migration_plan.md`）
- 遷移腳本開發：Phase 0
- 正式執行：待使用者通知（Phase 0 完成後）

**影響範圍**：
- 資料模型需包含 `current_department` 與 `hire_year_month` 欄位
- 需提供員工編號解析函式
- 需開發遷移腳本 `scripts/migrate_from_sqlite.py`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 系統管理員初始化系統配置 (Priority: P0)

系統管理員需要為淡海和安坑兩個部門分別配置 Google 服務連接資訊。

**Why this priority**: 這是系統運行的前置條件，沒有配置就無法連接外部服務。

**Independent Test**: 管理員登入後進入系統設定頁面，分別設定淡海和安坑的 Google Sheets ID、Drive 資料夾 ID，完成 Google Drive OAuth 授權，儲存後重新載入頁面確認設定保留。

**Acceptance Scenarios**:

1. **Given** 管理員登入系統，**When** 進入「系統設定」頁面，**Then** 顯示淡海和安坑兩個部門的設定區塊
2. **Given** 在淡海設定區塊，**When** 填寫班表 Sheets ID、勤務表 Sheets ID、Drive 資料夾 ID（4個文件類型），**Then** 設定儲存到資料庫
3. **Given** 在淡海設定區塊，**When** 點擊「授權 Google Drive」按鈕並完成 OAuth 授權流程，**Then** 系統儲存加密的 refresh_token 並顯示「✓ Google Drive 已授權（淡海）」
4. **Given** 在安坑設定區塊，**When** 填寫相同類型的設定項目並完成獨立授權，**Then** 獨立儲存，不影響淡海設定
5. **Given** 設定已儲存，**When** 重新載入頁面，**Then** 所有設定項目正確顯示，OAuth 授權狀態保留

---

### User Story 2 - 員工資料管理（含部門與調動） (Priority: P1)

值班台人員需要能夠管理員工基本資料，包含新增、編輯、標記離職、記錄調動。

**Why this priority**: 員工資料是所有其他模組的基礎，必須優先建立。

**Independent Test**: 淡海值班台人員新增一位員工，填寫編號、姓名、聯絡資訊，系統自動解析入職年月並設定部門為淡海。後續該員工調動到安坑，記錄調動歷史。

**Acceptance Scenarios**:

1. **Given** 淡海值班台人員登入，**When** 點擊「新增員工」並填寫員工編號「1011M0095」、姓名「張三」，**Then** 系統自動解析入職年月為「2021-11」，部門預設為「淡海」
2. **Given** 填寫員工資料，**When** 填寫手機、Email、緊急聯絡人（選填），**Then** 資料儲存成功
3. **Given** 管理員登入，**When** 對員工「張三」執行「記錄調動」，選擇目標部門「安坑」、調動日期「2026-03-01」，**Then** 建立調動記錄，員工當前部門更新為「安坑」
4. **Given** 淡海值班台人員登入，**When** 查看員工「張三」的調動前記錄，**Then** 可查看但無法編輯（唯讀）
5. **Given** 安坑值班台人員登入，**When** 查看員工「張三」的調動後記錄，**Then** 可查看且可編輯

---

### User Story 3 - 權限控制與資料過濾 (Priority: P1)

系統必須根據使用者角色和部門限制資料存取權限。

**Why this priority**: 資料安全與權限控制是核心需求，必須從一開始就正確實作。

**Independent Test**: 淡海值班台人員登入後，列表預設顯示淡海部門資料，但可查詢安坑資料（唯讀）。主管可查看所有部門資料。

**Acceptance Scenarios**:

1. **Given** 淡海值班台人員登入，**When** 進入員工列表頁面，**Then** 預設篩選條件為「部門=淡海」，可切換查看安坑
2. **Given** 淡海值班台人員查看淡海員工，**When** 點擊編輯按鈕，**Then** 可以編輯所有欄位
3. **Given** 淡海值班台人員查看安坑員工，**When** 點擊編輯按鈕，**Then** 按鈕為灰色或提示「無權限編輯他部門資料」
4. **Given** 主管登入，**When** 查看員工列表，**Then** 可看到所有部門資料，但無編輯按鈕
5. **Given** 管理員登入，**When** 查看員工列表，**Then** 可看到所有部門資料，且可編輯所有記錄

---

### User Story 4 - Google Sheets 班表自動同步與手動觸發 (Priority: P2) ⭐ **(已擴充)**

系統每日自動從 Google Sheets 同步班表資料到資料庫，並提供手動同步功能供管理員即時更新資料。

**Why this priority**: 班表資料是差勤考核的基礎，需要自動化減少人工操作。手動同步功能可處理自動排程失敗或需要即時資料的情況。

**Independent Test**: 系統在凌晨 2:00 自動執行同步任務，從淡海和安坑的 Google Sheets 讀取當月班表並寫入資料庫。管理員可在任何時間點點擊「立即同步」按鈕手動觸發同步。

**Acceptance Scenarios**:

1. **Given** 系統在 Render 運行並由 UptimeRobot 保持喚醒，**When** 時間到達凌晨 2:00，**Then** 自動觸發班表同步任務（淡海）
2. **Given** 班表同步任務執行，**When** 連接淡海的 Google Sheets，**Then** 使用淡海的 API 憑證和唯讀權限
3. **Given** 班表資料讀取成功，**When** 解析班表分頁（如「11501班表」），**Then** 寫入資料庫並標記部門為「淡海」
4. **Given** 淡海同步完成，**When** 執行安坑同步任務，**Then** 使用安坑的 API 憑證與 Sheets ID
5. **Given** 同步過程發生錯誤，**When** 錯誤發生，**Then** 記錄錯誤日誌並通知管理員（Email 或系統通知）
6. **Given** 管理員登入系統，**When** 進入「Google 服務管理」頁面並點擊「立即同步班表（淡海）」，**Then** 立即觸發同步任務並顯示進度
7. **Given** 手動同步執行中，**When** 同步進行，**Then** 顯示即時進度（已處理 X 筆 / 共 Y 筆）並可取消
8. **Given** 手動同步完成，**When** 同步結束，**Then** 顯示結果統計（新增 N 筆、更新 N 筆、失敗 N 筆）

---

### User Story 5 - 駕駛時數統計與競賽排名 (Priority: P3)

系統每日同步勤務表資料，每月自動計算駕駛競賽排名。

**Why this priority**: 駕駛競賽是新增功能，優先級低於核心履歷與考核功能。

**Independent Test**: 系統每月 1 日計算上月駕駛競賽排名，按部門和全公司分別排名。

**Acceptance Scenarios**:

1. **Given** 管理員登入系統，**When** 進入「勤務標準時間管理」頁面，**Then** 可新增、編輯、刪除勤務標準時間（如「淡安-全」= 480 分鐘）
2. **Given** 管理員上傳勤務標準時間 Excel 檔案，**When** 系統驗證資料格式，**Then** 批次匯入成功並顯示匯入筆數
3. **Given** 系統在凌晨 2:30 執行勤務表同步，**When** 讀取淡海勤務表並查詢 `route_standard_times` 表，**Then** 計算每位員工的每日駕駛分鐘數並寫入 `driving_daily_stats`
4. **Given** 班表標示某員工當日為 R班出勤，**When** 計算駕駛時數，**Then** 該日時數 × 2
5. **Given** 每月 1 日凌晨 3:00，**When** 觸發競賽排名計算任務，**Then** 彙總上月所有員工的駕駛時數並套用公式計算最終積分
6. **Given** 計算最終積分（= Σ(每日勤務時數 × R班係數) × 責任事件懲罰係數），**When** 計算完成，**Then** 按積分由高到低排名並寫入 `driving_competition`
7. **Given** 排名計算完成，**When** 主管查詢駕駛競賽報表，**Then** 顯示所有員工排名、積分、部門內排名與全公司排名

---

### User Story 6 - 系統連線狀態監控與憑證驗證 (Priority: P2) ⭐ **(Gemini 建議新增)**

桌面應用程式必須常駐顯示雲端服務與 Google API 的連線狀態，並在管理員上傳 API 憑證時立即驗證其有效性。

**Why this priority**: 連線狀態即時回饋可幫助使用者快速診斷問題（網路 vs 伺服器），憑證驗證可避免配置錯誤導致後續功能異常。

**Independent Test**: 桌面應用啟動後在狀態列顯示「雲端連線：正常」與「Google API：正常」。管理員上傳淡海的 Google 憑證時，系統立即嘗試連接並回報結果。

**Acceptance Scenarios**:

1. **Given** 桌面應用啟動完成，**When** 連接雲端 FastAPI 成功，**Then** 狀態列顯示「☁️ 雲端：已連線」（綠色圖示）
2. **Given** 桌面應用運行中，**When** 雲端 API 無法連接（網路問題或 Render 休眠），**Then** 狀態列顯示「☁️ 雲端：連線失敗」（紅色圖示）並提示「請檢查網路連線」
3. **Given** 系統已配置 Google API 憑證，**When** 應用啟動時測試 Google Sheets 連線，**Then** 狀態列顯示「📊 Google：已連線（淡海✓ 安坑✓）」
4. **Given** Google API 憑證過期或權限不足，**When** 測試連線失敗，**Then** 狀態列顯示「📊 Google：連線異常（淡海✗）」並提示管理員檢查憑證
5. **Given** 管理員在系統設定上傳淡海的 Google 憑證 JSON，**When** 點擊「驗證憑證」按鈕，**Then** 系統立即嘗試連接 Google Sheets API（Dry Run）
6. **Given** 憑證驗證測試執行，**When** 權限正確且可連線，**Then** 顯示「✓ 憑證有效，已成功連接 Google Sheets」並允許儲存
7. **Given** 憑證驗證測試失敗，**When** 權限不足或檔案格式錯誤，**Then** 顯示具體錯誤訊息（如「權限不足：缺少 spreadsheets.readonly」）並拒絕儲存
8. **Given** 使用者嘗試上傳檔案時系統偵測 OAuth refresh_token 失效（使用者在 Google 撤銷授權），**When** 授權驗證失敗，**Then** 顯示「Google Drive 授權已失效，請聯繫管理員」並發送 Email 通知管理員（kunpeto.chen@gmail.com）
9. **Given** 使用者在無網路環境下操作，**When** 狀態列顯示連線失敗，**Then** 系統提示「已進入離線模式，部分功能不可用」（若實作本地快取）

---

### User Story 7 - PDF 條碼識別（含部門判斷） (Priority: P2)

桌面應用程式處理 PDF 掃描文件，根據條碼前綴（TH/AK）自動判斷部門並上傳到對應的 Google Drive 資料夾。

**Why this priority**: PDF 處理是前專案功能，需調整以支援雙部門。

**Independent Test**: 使用者上傳一個包含多頁的 PDF，條碼為「TH-12345」和「AK-67890」，系統自動切分為兩個檔案並上傳到淡海和安坑的 Drive 資料夾。

**Acceptance Scenarios**:

1. **Given** 使用者在桌面應用上傳 PDF，**When** 系統識別條碼「TH-12345」，**Then** 判定部門為「淡海」
2. **Given** 條碼識別完成，**When** 切分 PDF，**Then** 根據條碼對應的履歷 ID 自動命名檔案
3. **Given** 檔案準備上傳，**When** 上傳到 Google Drive，**Then** 使用淡海的 Drive 憑證和資料夾 ID
4. **Given** PDF 中包含「AK-67890」條碼，**When** 處理該頁面，**Then** 判定部門為「安坑」並上傳到安坑 Drive
5. **Given** 上傳完成，**When** 更新履歷狀態，**Then** 記錄 Google Drive 連結並標記為已結案

---

### Edge Cases

- **跨部門員工的歷史記錄**：員工調動後，原部門值班台查看調動前記錄為唯讀，新部門值班台查看調動前記錄也是唯讀
- **Google API 憑證過期**：顯示明確錯誤訊息並通知管理員，停用該部門的自動同步功能
- **OAuth 授權失效處理流程** ⭐ **(新增)**：
  - **情境**：使用者在 Google 帳戶中撤銷授權，導致 refresh_token 失效
  - **偵測失效**：系統嘗試上傳檔案到 Google Drive 時收到 401/403 錯誤
  - **使用者端提示**：前端顯示「Google Drive 授權已失效，請稍後再試或聯繫管理員」
  - **管理員通知**：系統立即發送 Email 給管理員（kunpeto.chen@gmail.com），內容包含失效部門、觸發使用者、發生時間、錯誤訊息
  - **管理員處理**：登入系統進入「系統設定」頁面，點擊「重新授權 Google Drive（該部門）」按鈕，完成 OAuth 授權流程
  - **恢復正常**：授權完成後，系統恢復正常運作
- **TiDB 儲存空間不足**：系統監控用量，接近 5GB 時發出警告，建議清理舊資料或升級
- **Render 服務休眠**：UptimeRobot 每 10 分鐘 ping 一次 `/health` 端點保持喚醒
- **員工編號解析失敗**：手動輸入入職年月（異常情況，如編號格式變更）
- **PDF 條碼無法識別**：提供手動選擇部門與履歷 ID 的介面
- **同步任務失敗**：記錄錯誤日誌，下次同步時重試，不影響系統其他功能
- **部門設定缺失**：首次啟動時檢查設定完整性，缺失時引導管理員設定

## Requirements *(mandatory)*

### Functional Requirements

#### 系統架構

- **FR-001**: 系統必須支援淡海與安坑雙部門架構，部門資訊硬編碼
- **FR-002**: 系統必須採用三層混合架構：GitHub Pages 網頁應用（前端） + Render FastAPI（雲端後端） + 本機桌面應用 API（檔案處理）
- **FR-002a**: 網頁應用必須託管於 GitHub Pages，使用前端框架（Vue.js 或 React）
- **FR-002b**: 本機桌面應用必須提供 FastAPI 本機 API（預設 localhost:8000），僅負責檔案操作
- **FR-002c**: 系統核心功能（資料瀏覽、履歷建立、員工管理）必須完全運行於網頁端，不依賴桌面應用 ⭐ **(容錯設計)**
- **FR-002d**: 網頁應用必須在啟動時檢測桌面應用 API 連線狀態（`http://localhost:8000/health`）
- **FR-002e**: 當桌面應用不可用時，系統必須禁用檔案生成功能按鈕並顯示「請啟動桌面應用程式」提示 ⭐ **(容錯設計)**
- **FR-003**: 系統必須使用 TiDB MySQL 作為雲端共享資料庫
- **FR-004**: 雲端 FastAPI 必須部署到 Render 免費版
- **FR-005**: 系統必須使用 UptimeRobot 保持 Render 服務 24/7 喚醒

#### 使用者角色與權限

- **FR-006**: 系統必須支援三種使用者角色：Admin、Staff、Manager
- **FR-007**: Admin 必須擁有所有功能權限與系統參數管理權限
- **FR-008**: Staff 必須僅能編輯本部門資料，其他部門資料唯讀
- **FR-009**: Manager 必須僅能查看所有部門資料（唯讀）與產生報表
- **FR-010**: 系統必須在 API 層實作權限檢查中間件

#### 員工資料管理

- **FR-011**: 系統必須支援員工資料 CRUD（新增、編輯、查詢、標記離職）
- **FR-012**: 員工資料必須包含：編號、姓名、部門、入職年月、聯絡資訊（選填）
- **FR-013**: 系統必須從員工編號自動解析入職年月（格式：YYMM，如 1011M0095 → 2021-11）
- **FR-014**: 系統必須支援員工調動記錄，包含調動日期、原部門、目標部門、原因
- **FR-015**: 系統必須在員工調動後更新 `current_department`，保留調動歷史
- **FR-016**: 系統必須支援批次匯入員工資料（Excel）
- **FR-017**: 系統必須支援批次匯出員工資料（Excel）

#### Google 服務整合

- **FR-018**: 系統必須為每個部門獨立配置 Google Sheets ID（班表、勤務表）
- **FR-019**: 系統必須為每個部門獨立配置 Google Drive 資料夾 ID（4種文件類型）
- **FR-020**: 系統必須為每個部門獨立配置 Google API 憑證（服務帳戶憑證使用環境變數，OAuth 令牌使用加密儲存）
- **FR-021**: 系統必須使用唯讀權限連接 Google Sheets
- **FR-022**: 系統必須每日凌晨 2:00 自動同步班表資料（淡海與安坑）
- **FR-023**: 系統必須每日凌晨 2:30 自動同步勤務表資料（淡海與安坑）
- **FR-024**: 系統必須將同步資料標記部門欄位
- **FR-024a**: 系統必須提供「手動同步」功能，允許管理員在任何時間觸發同步 ⭐ **(Gemini 建議)**
- **FR-024b**: 手動同步必須顯示即時進度（已處理 X 筆 / 共 Y 筆）並可取消
- **FR-024c**: 手動同步完成後必須顯示結果統計（新增、更新、失敗筆數）
- **FR-024d**: 系統必須在管理員上傳 Google API 憑證時立即驗證其有效性（Dry Run） ⭐ **(Gemini 建議)**
- **FR-024e**: 憑證驗證必須測試連接 Google Sheets 與 Drive API，並回報具體錯誤（如權限不足）
- **FR-024f**: 憑證驗證失敗時必須拒絕儲存設定，並顯示詳細錯誤訊息

#### 駕駛時數與競賽

- **FR-025**: 系統必須記錄每位員工每日的駕駛時數（分鐘）
- **FR-026**: 系統必須記錄每位員工每日的責任事件次數
- **FR-027**: 系統必須每月 1 日凌晨 3:00 自動計算上月駕駛競賽排名
- **FR-028**: 系統必須分別計算部門內排名與全公司排名
- **FR-029**: 系統必須根據駕駛競賽方案計算最終積分（= Σ(每日勤務時數 × R班係數) × 責任事件懲罰係數）
- **FR-030**: 系統必須提供駕駛競賽排名報表（主管可查詢）
- **FR-031**: 系統必須提供勤務標準時間管理功能（僅管理員可編輯）⭐ **(新增)**
  - 支援新增、編輯、刪除勤務標準時間
  - 包含欄位：部門、勤務代碼、勤務名稱、標準分鐘數、啟用狀態
  - 部門間勤務設定獨立，不互相影響
  - **變更規則** ⭐ **(已補充 2026-01-28)**：
    - 變更僅影響「變更日期之後」的駕駛時數計算，歷史資料不重新計算
    - 刪除保護：有關聯記錄的勤務標準時間改為「軟刪除」（`is_active = false`），不允許實體刪除
    - 未知勤務代碼處理：勤務表出現未定義的勤務代碼時，該勤務時數計為 0 分鐘，並記錄警告日誌
- **FR-032**: 系統必須支援勤務標準時間的 Excel 批次匯入功能 ⭐ **(新增)**
  - 管理員可上傳 Excel 檔案批次建立勤務標準時間
  - 匯入前進行資料驗證（必填欄位、格式檢查）
  - 提供匯入預覽與錯誤提示
- **FR-033**: 駕駛時數計算必須基於勤務標準時間資料表 ⭐ **(新增)**
  - 從 Google Sheets 勤務表讀取員工當日勤務項目
  - 查詢 `route_standard_times` 表取得對應標準分鐘數
  - 彙總計算每日總駕駛時數

#### 本機桌面應用檔案處理功能 ⭐ **(架構調整)**

##### Word 文件生成
- **FR-031**: 桌面應用 API 必須提供 Word 文件生成端點（POST `/api/generate-word`）
- **FR-032**: 必須支援自訂範本（.docx 格式），從資料庫填充內容
- **FR-033**: 生成的 Word 檔案必須自動命名（員工編號_文件類型_日期.docx）
- **FR-034**: 生成完成後必須返回檔案下載連結或直接觸發下載

##### PDF 處理
- **FR-035**: 桌面應用必須在本機處理 PDF 條碼識別與切分
- **FR-036**: 系統必須在產生 PDF 條碼時加上部門前綴（淡海=TH、安坑=AK）
- **FR-037**: 系統必須根據條碼前綴判斷部門並上傳到對應 Google Drive 資料夾
- **FR-038**: 系統必須使用對應部門的 Google Drive API 憑證
- **FR-039**: PDF 掃描切分後必須自動命名（條碼_履歷ID_日期.pdf）

##### 條碼生成
- **FR-040**: 桌面應用 API 必須提供條碼生成端點（POST `/api/generate-barcode`）
- **FR-041**: 條碼格式必須包含部門前綴 + 履歷 ID（如 TH-12345、AK-67890）
- **FR-042**: 必須支援 Code128 或 QR Code 格式
- **FR-043**: 條碼圖片必須返回 Base64 編碼或 PNG 檔案

##### Google Drive 上傳
- **FR-044**: 桌面應用 API 必須提供檔案上傳端點（POST `/api/upload-to-drive`）
- **FR-045**: 必須支援根據部門選擇對應的 Drive 資料夾 ID 與憑證
- **FR-046**: 上傳成功後必須返回 Google Drive 檔案連結
- **FR-047**: 上傳失敗時必須記錄錯誤日誌並返回明確錯誤訊息

#### 前端網頁應用 ⭐ **(新增)**

- **FR-035**: 網頁應用必須使用前端框架（Vue.js 3 或 React）開發單頁應用（SPA）
- **FR-036**: 網頁應用必須支援響應式設計（RWD），適配桌面與平板裝置
- **FR-037**: 網頁應用必須透過 HTTPS 連接雲端 FastAPI（Render）
- **FR-038**: 網頁應用必須在啟動時檢測本機桌面應用 API 連線狀態
- **FR-039**: 檔案生成功能（Word、PDF、條碼）必須在桌面應用不可用時禁用並提示使用者 ⭐ **(容錯設計)**
- **FR-040**: 核心功能（資料 CRUD、查詢、報表）不得依賴桌面應用，必須完全透過雲端 API 實作 ⭐ **(容錯設計)**

#### 本機桌面應用（檔案處理）

- **FR-041**: 桌面應用必須提供本機 FastAPI API（預設 `http://localhost:8000`）
- **FR-042**: 桌面應用必須實作 CORS 設定，允許來自 GitHub Pages 的跨域請求
  - **允許的 Origin 清單**：
    - `https://kunpeto.github.io` (正式環境，GitHub Pages)
    - `http://localhost:5173` (開發環境，Vite 預設 port)
  - **CORS 配置要求**：
    - 允許的 HTTP 方法：GET, POST, PUT, DELETE, OPTIONS
    - 允許的 Headers：Content-Type, Authorization
    - 允許憑證 (credentials)：true
- **FR-043**: 桌面應用必須提供健康檢查端點（`/health`）供網頁應用檢測
- **FR-044**: 桌面應用必須提供系統托盤圖示，顯示運行狀態（綠色=正常運行、灰色=停止）
- **FR-045**: 桌面應用必須在系統托盤提供右鍵選單（啟動/停止 API、開啟設定、結束程式）
- **FR-046**: 桌面應用必須在啟動時自動啟動本機 FastAPI 服務
- **FR-047**: 桌面應用必須提供設定介面，配置 Google Drive API 憑證
- **FR-048**: 桌面應用 API 失敗時，不得影響網頁應用的核心功能運作 ⭐ **(容錯設計)**

#### 定時任務

- **FR-048**: 雲端 FastAPI 必須使用 APScheduler 管理所有定時任務
- **FR-049**: 定時任務必須包含：班表同步（2:00）、勤務表同步（2:30）、競賽排名計算（3:00）、資料庫備份（4:00）
- **FR-050**: 定時任務失敗必須記錄錯誤日誌並發送通知

#### 本地快取（可選實作） 💡 **(Gemini 建議)**

- **FR-051**: 網頁應用可選實作 IndexedDB 本地快取，儲存員工列表與基本設定
- **FR-052**: 本地快取必須在雲端 API 可用時自動同步更新
- **FR-053**: 本地快取必須在雲端 API 不可用時提供離線查詢功能（唯讀）
- **FR-054**: 系統必須在進入離線模式時明確提示使用者「部分功能不可用」

#### 歷史資料遷移（待確認需求） ⭐ **(Gemini 建議)**

- **FR-055**: 系統必須提供資料遷移工具，從前專案 SQLite 匯入歷史資料（需確認 PC-005）
- **FR-056**: 資料遷移必須支援選擇性匯入（指定年度範圍、特定資料類型）
- **FR-057**: 資料遷移必須包含資料驗證與格式轉換功能
- **FR-058**: 資料遷移完成後必須產生詳細報告（成功、失敗、跳過筆數）

### Database Configuration ⭐ **(新增)**

#### 連線資訊

系統使用 **TiDB Serverless** 作為雲端共享資料庫，相容 MySQL 8.0 協議。

**連線參數**：
```python
DATABASE_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3SQWVrWh5DieHsr.root',
    'password': 'pA6LsowKCFAVVJm2',  # ⚠️ 需環境變數保護
    'database': 'test',
    'charset': 'utf8mb4',
    'ssl_verify_cert': True,
    'ssl_verify_identity': True
}
```

**資料庫版本**：TiDB v7.5.6-serverless (相容 MySQL 8.0.11)

#### Python 連線套件

系統使用 `pymysql` 作為主要資料庫連線驅動。

**安裝指令**：
```bash
pip install pymysql
```

**連線範例**：
```python
import pymysql
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """取得資料庫連線（Context Manager）"""
    connection = pymysql.connect(
        host='gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
        port=4000,
        user='3SQWVrWh5DieHsr.root',
        password=os.getenv('TIDB_PASSWORD'),  # 從環境變數讀取
        database='test',
        charset='utf8mb4',
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        cursorclass=pymysql.cursors.DictCursor  # 回傳字典格式
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

# 使用範例
with get_db_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM employees")
        results = cursor.fetchall()
```

#### 環境變數設定

**必要環境變數**（存放於 `.env` 檔案）：

```env
# TiDB 資料庫連線
TIDB_HOST=gateway01.ap-northeast-1.prod.aws.tidbcloud.com
TIDB_PORT=4000
TIDB_USER=3SQWVrWh5DieHsr.root
TIDB_PASSWORD=pA6LsowKCFAVVJm2
TIDB_DATABASE=test

# FastAPI 設定
API_SECRET_KEY=<隨機生成的密鑰>
API_ENVIRONMENT=production  # development / production
```

**安全性規範**：
- ❌ **禁止將 `.env` 檔案提交到版控系統**
- ✅ `.gitignore` 必須包含 `.env`
- ✅ 提供 `.env.example` 作為範本（密碼留空）
- ✅ Render 部署時使用平台的環境變數設定功能

#### 連線池設定（FastAPI）

FastAPI 應用程式應使用連線池提升效能。

**使用 SQLAlchemy（建議）**：
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# 建立連線字串（使用環境變數）
DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('TIDB_USER')}:{os.getenv('TIDB_PASSWORD')}"
    f"@{os.getenv('TIDB_HOST')}:{os.getenv('TIDB_PORT')}/{os.getenv('TIDB_DATABASE')}"
    f"?charset=utf8mb4&ssl_verify_cert=true&ssl_verify_identity=true"
)

# 建立引擎（連線池）
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,           # 常駐連線數
    max_overflow=10,       # 最大額外連線數
    pool_pre_ping=True,    # 自動檢測斷線
    pool_recycle=3600,     # 1小時回收連線
    echo=False             # 開發時可設為 True 顯示 SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 資料庫初始化

**初始化腳本位置**：`scripts/init_database.py`

**執行順序**：
1. 建立資料表（使用 SQLAlchemy ORM 或原始 SQL）
2. 建立索引（加速查詢）
3. 插入預設資料（管理員帳號、系統設定）
4. （可選）匯入歷史資料（從前專案 SQLite，待確認 PC-005）

**索引建議**：
```sql
-- 員工資料
CREATE INDEX idx_employee_id ON employees(employee_id);
CREATE INDEX idx_department ON employees(current_department);
CREATE INDEX idx_is_resigned ON employees(is_resigned);

-- 勤務標準時間
CREATE INDEX idx_route_department ON route_standard_times(department);
CREATE INDEX idx_route_code ON route_standard_times(department, route_code);
CREATE INDEX idx_route_active ON route_standard_times(is_active);

-- 駕駛時數
CREATE INDEX idx_driving_date ON driving_daily_stats(record_date);
CREATE INDEX idx_driving_employee_date ON driving_daily_stats(employee_id, record_date);
CREATE INDEX idx_driving_fiscal ON driving_daily_stats(fiscal_year, fiscal_month);

-- 駕駛競賽
CREATE INDEX idx_competition_period ON driving_competition(competition_year, competition_month);
CREATE INDEX idx_competition_employee ON driving_competition(employee_id);
```

#### 儲存空間監控

**TiDB 免費版限制**：
- 儲存空間：5 GB
- 連線數：5000 個/天
- Request Units (RU)：50M RU/月

**監控策略**：
- 每日定時檢查資料庫大小（FastAPI 定時任務）
- 當用量達 4 GB（80%）時發送警告通知
- 提供資料清理建議（舊資料歸檔、日誌清理）
- 監控腳本範例：

```python
def check_database_size():
    """檢查資料庫大小"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    table_schema AS 'database',
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'size_mb'
                FROM information_schema.TABLES
                WHERE table_schema = %s
                GROUP BY table_schema
            """, (os.getenv('TIDB_DATABASE'),))
            result = cursor.fetchone()
            size_mb = result['size_mb']

            # 警告門檻：4 GB = 4096 MB
            if size_mb > 4096:
                send_alert(f"資料庫用量已達 {size_mb} MB，接近 5GB 限制！")

            return size_mb
```

#### 備份策略

**自動備份**：
- 每日凌晨 4:00 執行備份（FastAPI 定時任務）
- 備份方式：mysqldump 匯出 SQL（透過 TiDB Cloud 管理介面或 CLI）
- 備份儲存：Google Drive 或本機備份資料夾
- 保留策略：最近 7 天每日備份 + 最近 4 週每週備份

**手動備份**：
```bash
# 使用 mysqldump（需安裝 MySQL Client）
mysqldump -h gateway01.ap-northeast-1.prod.aws.tidbcloud.com \
  -P 4000 \
  -u 3SQWVrWh5DieHsr.root \
  -p \
  --ssl-mode=VERIFY_IDENTITY \
  --databases test \
  > backup_$(date +%Y%m%d).sql
```

#### 連線測試

系統必須提供資料庫連線測試功能（健康檢查端點）。

**FastAPI 健康檢查端點**：
```python
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/health")
async def health_check():
    """健康檢查端點（用於 UptimeRobot）"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@router.get("/health/database")
async def database_detailed_check():
    """詳細資料庫狀態檢查"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()

                cursor.execute("SELECT DATABASE()")
                database = cursor.fetchone()

                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()

        return {
            "status": "connected",
            "version": version['VERSION()'],
            "database": database['DATABASE()'],
            "tables_count": len(tables),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

#### 相關功能需求

- **FR-003**: 系統必須使用 TiDB MySQL 作為雲端共享資料庫（已確認）
- **FR-059**: 系統必須使用環境變數儲存資料庫敏感資訊 ⭐ **(新增)**
- **FR-060**: FastAPI 必須實作資料庫連線池，常駐連線數 5，最大連線數 15 ⭐ **(新增)**
- **FR-061**: 系統必須提供 `/health` 端點供 UptimeRobot 監控（已包含資料庫連線測試）
- **FR-062**: 系統必須每日監控資料庫儲存用量，達 80% 時發出警告 ⭐ **(新增)**
- **FR-063**: 系統必須每日凌晨 4:00 自動備份資料庫到 Google Drive ⭐ **(新增)**
- **FR-064**: 網頁應用啟動時必須測試雲端 API 與資料庫連線，失敗時顯示明確錯誤訊息 ⭐ **(新增)**

#### 成功標準

- **SC-015**: 資料庫連線池命中率 > 90%，減少連線建立開銷 ⭐ **(新增)**
- **SC-016**: 資料庫健康檢查響應時間 < 500ms ⭐ **(新增)**
- **SC-017**: 資料庫儲存用量在 2 年內不超過 4.5 GB ⭐ **(新增)**
- **SC-018**: 自動備份成功率 > 99% ⭐ **(新增)**

---

## Non-Functional Requirements ⭐ **(新增)**

### 認證與授權

#### JWT 認證機制規範

**Token 結構**：
- Payload 包含欄位：`user_id`, `role`, `department`, `exp` (過期時間), `iat` (發行時間)
- 簽章演算法：HS256
- Secret Key：使用環境變數 `API_SECRET_KEY`（最少 32 字元）

**有效期限**：
- **NFR-001**: JWT Token 有效期限為 24 小時（從發行時間起算）
- 使用者登入成功後，系統發行 Token，24 小時內無需重新登入

**過期處理**：
- **NFR-002**: Token 過期時，前端必須自動重導向至登入頁面
- **NFR-003**: 登入頁面顯示提示訊息：「登入已逾時，請重新登入」
- **NFR-004**: API 回傳 401 Unauthorized 時，前端 Axios 攔截器統一處理重導向邏輯

**安全規範**：
- Token 儲存於瀏覽器 localStorage
- 每次 API 請求必須在 Header 攜帶 `Authorization: Bearer <token>`
- 後端中間件驗證 Token 有效性（簽章、過期時間、必要欄位）

---

### 前端健康檢查與連線監控

#### 本機桌面應用連線檢測策略

**檢測機制**：
- **NFR-005**: 網頁應用啟動時立即檢測本機 API（http://localhost:8000/health）
- **NFR-006**: HTTP 請求超時時間設定為 3 秒
- **NFR-007**: 背景輪詢頻率為 60 秒（運行中每分鐘檢測一次）
- **NFR-008**: 連續 3 次檢測失敗後，將本機 API 狀態標記為「不可用」
- **NFR-009**: 即使標記為不可用，仍持續輪詢以偵測恢復

**使用者介面**：
- 狀態列持續顯示連線狀態：
  - ✅ 本機應用：已連線
  - ❌ 本機應用：未連線
  - ⚠️ 本機應用：連線中...
- 本機 API 不可用時，所有檔案功能按鈕自動禁用（灰色）
- 不使用彈窗提示（避免打擾使用者）

---

### 安全與金鑰管理

#### 加密金鑰管理策略

**ENCRYPTION_KEY 生命週期**：
- 金鑰在專案生命週期內固定不變
- 不實作自動輪替機制（內部系統，使用者規模小，輪替優先級低）
- 僅在發生安全事件時進行緊急輪替（手動處理）

**金鑰保護措施**：
- 儲存於 Render 環境變數（平台級加密）
- 僅管理員可存取 Render Dashboard
- 本機金鑰檔案權限設定為 0o600（僅擁有者可讀寫）
- 不記錄於日誌或任何明文檔案
- 使用 Fernet 標準演算法（NIST 認證）

**緊急輪替流程**（安全事件發生時）：
1. 生成新的 ENCRYPTION_KEY
2. 選擇低流量時段（凌晨 4:00）進入維護模式
3. 執行腳本重新加密所有資料
4. 更新 Render 環境變數
5. 重啟服務並驗證
6. 預估停機時間：10-15 分鐘

---

## Credential Management & Security ⭐ **(新增：憑證管理策略)**

系統需使用兩種不同類型的 Google API 憑證，各有不同的儲存與安全需求。

### 憑證類型與用途

#### 1. 服務帳戶憑證（Service Account Credentials）

**用途**：
- 自動同步 Google Sheets（班表、勤務表）
- 背景定時任務執行（無需使用者授權）

**格式**：
- JSON 檔案，包含 `private_key`、`client_email`、`project_id` 等

**權限範圍**：
- `https://www.googleapis.com/auth/spreadsheets.readonly`（唯讀 Sheets）

**風險等級**：🔴 **高風險**
- `private_key` 洩露將導致服務帳戶全面控制權限
- 必須加密儲存，不得明文存在於任何檔案或程式碼中

---

#### 2. OAuth 2.0 使用者憑證（User OAuth Credentials）

**用途**：
- 使用者授權上傳檔案到 Google Drive
- 需使用者互動完成授權流程

**格式**：
- `client_id`、`client_secret`（公開配置）
- `refresh_token`、`access_token`（敏感資料）

**權限範圍**：
- `https://www.googleapis.com/auth/drive.file`（僅限建立/修改應用程式建立的檔案）

**風險等級**：🟡 **中風險**
- `refresh_token` 洩露可持續存取使用者 Drive
- `access_token` 洩露僅短期風險（1小時有效期）

---

### 憑證儲存方案

#### 雲端後端（Render FastAPI）

##### 服務帳戶憑證儲存

**方案**：環境變數（Base64 編碼）

```bash
# Render 環境變數設定
TANHAE_GOOGLE_SERVICE_ACCOUNT_JSON=<Base64 編碼的 JSON 內容>
ANPING_GOOGLE_SERVICE_ACCOUNT_JSON=<Base64 編碼的 JSON 內容>
```

**設定步驟**：
```bash
# 本機準備（DO NOT COMMIT）
base64 -w 0 tanhae-service-account.json > tanhae-encoded.txt

# 透過 Render Dashboard 或 CLI 設定環境變數
render env set TANHAE_GOOGLE_SERVICE_ACCOUNT_JSON="$(cat tanhae-encoded.txt)"
```

**讀取範例**：
```python
import json
import base64
import os

def get_service_account_credentials(department: str) -> dict:
    """從環境變數取得服務帳戶憑證"""
    env_key = f"{department.upper()}_GOOGLE_SERVICE_ACCOUNT_JSON"
    encoded = os.getenv(env_key)

    if not encoded:
        raise ValueError(f"Missing service account for {department}")

    decoded = base64.b64decode(encoded).decode('utf-8')
    return json.loads(decoded)
```

**優點**：
- ✅ 不存在於程式碼或檔案系統
- ✅ Render 平台已加密環境變數
- ✅ 部署時自動載入，無需額外配置步驟

---

##### OAuth 令牌儲存

**方案**：資料庫加密欄位

**資料模型**（新增）：
```python
class GoogleOAuthToken(Base):
    """OAuth 令牌安全儲存表"""
    __tablename__ = "google_oauth_tokens"

    id = Column(Integer, primary_key=True)
    department = Column(Enum('淡海', '安坑'), unique=True, nullable=False)

    # 加密儲存（使用 Fernet 對稱加密）
    encrypted_refresh_token = Column(LargeBinary, nullable=False)
    encrypted_access_token = Column(LargeBinary, nullable=True)

    # 訪問令牌到期時間
    access_token_expires_at = Column(DateTime, nullable=True)

    # 授權使用者資訊
    authorized_user_email = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**加密工具**：
```python
from cryptography.fernet import Fernet
import os

class TokenEncryption:
    """令牌加密/解密工具"""

    @staticmethod
    def get_cipher():
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        return Fernet(key.encode())

    @staticmethod
    def encrypt_token(token: str) -> bytes:
        cipher = TokenEncryption.get_cipher()
        return cipher.encrypt(token.encode())

    @staticmethod
    def decrypt_token(encrypted: bytes) -> str:
        cipher = TokenEncryption.get_cipher()
        return cipher.decrypt(encrypted).decode()
```

**環境變數**（必須設定）：
```bash
# 加密金鑰（使用 Fernet.generate_key() 產生）
ENCRYPTION_KEY=<44 字元 Base64 字串>

# OAuth 客戶端配置
GOOGLE_OAUTH_CLIENT_ID=<your-app-id>.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=https://your-app.onrender.com/api/auth/google/callback
```

**產生加密金鑰**：
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**優點**：
- ✅ `refresh_token` 加密後儲存於資料庫
- ✅ 即使資料庫洩露，無 `ENCRYPTION_KEY` 無法解密
- ✅ 支援多部門獨立授權

---

#### 本機桌面應用（localhost:8000）

##### OAuth 令牌儲存

**方案**：本機加密檔案

**儲存位置**：`~/.driver_management_system/tokens.encrypted`

**實作範例**：
```python
from pathlib import Path
from cryptography.fernet import Fernet
import json
import os

class DesktopCredentialManager:
    """本機憑證管理器"""

    CONFIG_DIR = Path.home() / ".driver_management_system"
    TOKENS_FILE = CONFIG_DIR / "tokens.encrypted"
    KEY_FILE = CONFIG_DIR / ".key"

    @classmethod
    def save_oauth_token(cls, department: str, refresh_token: str):
        """儲存 OAuth 刷新令牌（加密）"""
        cls.CONFIG_DIR.mkdir(exist_ok=True, mode=0o700)  # 僅擁有者可存取

        # 取得或建立加密金鑰
        key = cls._get_or_create_local_key()
        cipher = Fernet(key)

        # 讀取現有令牌（若存在）
        tokens = {}
        if cls.TOKENS_FILE.exists():
            with open(cls.TOKENS_FILE, 'rb') as f:
                encrypted = f.read()
                tokens = json.loads(cipher.decrypt(encrypted).decode())

        # 更新令牌
        tokens[department] = {
            "refresh_token": refresh_token,
            "created_at": datetime.now().isoformat()
        }

        # 加密後寫入
        with open(cls.TOKENS_FILE, 'wb') as f:
            encrypted = cipher.encrypt(json.dumps(tokens).encode())
            f.write(encrypted)

        # 設定檔案權限（僅擁有者可讀寫）
        os.chmod(cls.TOKENS_FILE, 0o600)

    @classmethod
    def get_oauth_token(cls, department: str) -> str:
        """讀取 OAuth 刷新令牌（解密）"""
        if not cls.TOKENS_FILE.exists():
            raise FileNotFoundError("No tokens found, please authorize first")

        key = cls._get_or_create_local_key()
        cipher = Fernet(key)

        with open(cls.TOKENS_FILE, 'rb') as f:
            encrypted = f.read()
            tokens = json.loads(cipher.decrypt(encrypted).decode())

        if department not in tokens:
            raise ValueError(f"No token for department: {department}")

        return tokens[department]["refresh_token"]

    @classmethod
    def _get_or_create_local_key(cls) -> bytes:
        """取得或建立本機加密金鑰"""
        if cls.KEY_FILE.exists():
            return cls.KEY_FILE.read_bytes()

        # 首次執行時產生
        key = Fernet.generate_key()
        cls.KEY_FILE.write_bytes(key)
        os.chmod(cls.KEY_FILE, 0o600)  # 僅擁有者可讀
        return key
```

**檔案結構**：
```
C:\Users\<username>\.driver_management_system\
├── .key                  # 本機加密金鑰（600 權限）
└── tokens.encrypted      # 加密的 OAuth 令牌（600 權限）
```

**優點**：
- ✅ 令牌不存在於明文檔案
- ✅ 加密金鑰與令牌分離
- ✅ 檔案權限限制防止其他使用者讀取
- ✅ 桌面應用關閉時令牌仍保留（無需重新授權）

---

### 安全規範與檢查清單

#### 🚫 絕對禁止的做法

```python
# ❌ 禁止 1：硬編碼憑證
SERVICE_ACCOUNT = {
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg..."
}

# ❌ 禁止 2：明文儲存在 .env 並提交到 Git
# .env 檔案內容
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","private_key":"..."}

# ❌ 禁止 3：未加密的資料庫欄位
refresh_token = Column(String(500))  # 明文儲存

# ❌ 禁止 4：將憑證寫入日誌
logger.info(f"Service account: {credentials}")

# ❌ 禁止 5：在 GitHub 中儲存憑證檔案
git add tanhae-service-account.json  # 災難性錯誤
```

---

#### ✅ 必須遵守的安全檢查清單

**開發階段**：
- [ ] `.env` 檔案已加入 `.gitignore`
- [ ] 提供 `.env.example` 範本（密碼留空）
- [ ] 本機測試憑證與正式環境憑證分離
- [ ] 服務帳戶僅授予最小必要權限（唯讀 Sheets）
- [ ] OAuth 應用僅請求必要 scopes（`drive.file`）

**部署階段**：
- [ ] Render 環境變數已設定所有必要憑證
- [ ] `ENCRYPTION_KEY` 已產生並設定（不得重複使用）
- [ ] TiDB 連線使用 SSL/TLS 加密
- [ ] 資料庫備份檔案已加密或限制存取權限

**運行階段**：
- [ ] 定期輪換服務帳戶金鑰（建議每 90 天）
- [ ] 監控異常 API 使用（偵測憑證洩露）
- [ ] 日誌不記錄敏感資訊（token、private_key）
- [ ] OAuth `access_token` 快取時間不超過 55 分鐘

**本機應用**：
- [ ] 加密檔案權限設為 `0o600`（僅擁有者可讀寫）
- [ ] 本機加密金鑰不備份到雲端（風險：金鑰洩露）
- [ ] 解除安裝時提示使用者刪除 `~/.driver_management_system`

---

### OAuth 授權流程設計

#### 初次授權流程（管理員操作）

```mermaid
sequenceDiagram
    participant A as 管理員
    participant W as 網頁應用
    participant C as 雲端 API
    participant G as Google OAuth

    A->>W: 進入「Google 服務設定」
    W->>C: GET /api/google/auth-url?department=淡海
    C->>G: 產生授權 URL（含 state 參數）
    G-->>C: 返回授權 URL
    C-->>W: 返回授權 URL
    W->>A: 顯示「點擊授權 Google Drive」按鈕
    A->>G: 點擊授權（開啟新視窗）
    G->>A: 顯示 Google 授權畫面
    A->>G: 同意授權
    G->>C: 重定向到 /api/auth/google/callback?code=xxx
    C->>G: 用 code 換取 refresh_token
    G-->>C: 返回 refresh_token + access_token
    C->>C: 加密 refresh_token 並儲存到資料庫
    C-->>W: 授權成功
    W->>A: 顯示「✓ Google Drive 已授權（淡海）」
```

#### 檔案上傳時使用令牌

```mermaid
sequenceDiagram
    participant U as 使用者
    participant D as 本機桌面應用
    participant C as 雲端 API
    participant DB as TiDB
    participant G as Google Drive

    U->>D: 點擊「上傳 PDF 到 Drive」
    D->>C: POST /api/google/get-access-token?department=淡海
    C->>DB: 讀取 encrypted_refresh_token
    DB-->>C: 返回加密令牌
    C->>C: 解密 refresh_token
    C->>G: 用 refresh_token 換取 access_token
    G-->>C: 返回 access_token（有效期 1 小時）
    C-->>D: 返回 access_token
    D->>G: 上傳檔案（使用 access_token）
    G-->>D: 上傳成功，返回檔案 URL
    D-->>U: 顯示「✓ 上傳成功」
```

---

### 功能需求更新

#### 憑證管理相關需求

- **FR-065**: 系統必須支援雙部門獨立的 Google 服務帳戶憑證配置 ⭐ **(新增)**
- **FR-066**: 服務帳戶憑證必須儲存於 Render 環境變數，使用 Base64 編碼 ⭐ **(新增)**
- **FR-067**: 系統必須提供加密工具類別（Fernet），加密 OAuth `refresh_token` ⭐ **(新增)**
- **FR-068**: OAuth 令牌必須儲存於資料庫加密欄位（`encrypted_refresh_token`）⭐ **(新增)**
- **FR-069**: 系統必須提供 OAuth 授權流程端點（`/api/google/auth-url`、`/api/auth/google/callback`）⭐ **(新增)**
- **FR-070**: 本機桌面應用必須將 OAuth 令牌加密儲存於 `~/.driver_management_system/tokens.encrypted` ⭐ **(新增)**
- **FR-071**: 加密檔案與金鑰檔案必須設定 `0o600` 權限（僅擁有者可讀寫）⭐ **(新增)**
- **FR-072**: 系統日誌不得記錄任何憑證內容（`private_key`、`refresh_token`、`access_token`）⭐ **(新增)**
- **FR-073**: 系統必須在 `.gitignore` 中排除所有憑證相關檔案（`.env`、`*.json` 服務帳戶憑證）⭐ **(新增)**
- **FR-074**: 系統必須提供憑證健康檢查功能（測試服務帳戶與 OAuth 連線狀態）⭐ **(新增)**

---

### 成功標準更新

- **SC-019**: 服務帳戶憑證不得出現在任何 Git 提交記錄中 ⭐ **(新增)**
- **SC-020**: OAuth 令牌加密/解密效能 < 10ms ⭐ **(新增)**
- **SC-021**: 憑證輪換流程可在 5 分鐘內完成（不影響系統運行）⭐ **(新增)**
- **SC-022**: OAuth 授權流程使用者完成時間 < 2 分鐘 ⭐ **(新增)**
- **SC-023**: 本機加密檔案權限檢查通過率 100%（開發、測試、生產環境）⭐ **(新增)**

---

### Key Entities

#### Employee (員工資料)
```python
- id: Integer (PK)
- employee_id: String(20) (唯一索引)
- employee_name: String(50)
- current_department: Enum('淡海', '安坑')
- hire_year_month: String(7)  # 2026-01
- phone: String(20) (nullable)
- email: String(100) (nullable)
- emergency_contact: String(50) (nullable)
- emergency_phone: String(20) (nullable)
- is_resigned: Boolean
- created_at: DateTime
- updated_at: DateTime
```

#### EmployeeTransfer (員工調動歷史)
```python
- id: Integer (PK)
- employee_id: String(20) (FK → Employee)
- from_department: Enum('淡海', '安坑')
- to_department: Enum('淡海', '安坑')
- transfer_date: Date
- reason: Text (nullable)
- created_by: String(50)
- created_at: DateTime
```

#### User (使用者帳號)
```python
- id: Integer (PK)
- username: String(50) (唯一)
- password_hash: String(255)
- role: Enum('admin', 'staff', 'manager')
- department: Enum('淡海', '安坑', 'all')
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

#### SystemSetting (系統設定)
```python
- id: Integer (PK)
- key: String(100)
- value: Text
- department: Enum('淡海', '安坑', 'global') (nullable)
- description: String(255)
- created_at: DateTime
- updated_at: DateTime
- UniqueConstraint(key, department)
```

#### GoogleOAuthToken (OAuth 令牌加密儲存) ⭐ **(新增)**
```python
- id: Integer (PK)
- department: Enum('淡海', '安坑') (唯一索引)
- encrypted_refresh_token: LargeBinary (使用 Fernet 加密)
- encrypted_access_token: LargeBinary (nullable, 快取用)
- access_token_expires_at: DateTime (nullable)
- authorized_user_email: String(100) (nullable, 授權者 Email)
- created_at: DateTime
- updated_at: DateTime
```

**說明**：
- `encrypted_refresh_token`：加密後的 Google OAuth refresh_token，用於長期存取 Google Drive
- `encrypted_access_token`：快取的 access_token（選用），避免頻繁刷新
- `access_token_expires_at`：access_token 到期時間，用於判斷是否需要刷新
- `authorized_user_email`：授權的 Google 帳號 Email，便於追蹤與管理
- 加密金鑰儲存於環境變數 `ENCRYPTION_KEY`

#### RouteStandardTime (勤務標準時間) ⭐ **(新增)**
```python
- id: Integer (PK)
- department: Enum('淡海', '安坑')
- route_code: String(50)  # 勤務代碼（如「淡安-全」、「淡海專」）
- route_name: String(100)  # 勤務名稱（如「淡海安坑全程」）
- standard_minutes: Integer  # 標準所需時間（分鐘）
- is_active: Boolean  # 是否啟用
- created_at: DateTime
- updated_at: DateTime
- UniqueConstraint(department, route_code)
```

**說明**：
- 每個部門獨立設定勤務標準時間
- 管理員可透過後台介面編輯（CRUD 操作）
- 駕駛競賽計算時，從此表讀取標準時間
- 支援匯入 Excel 初始資料

#### DrivingDailyStats (每日駕駛時數)
```python
- id: Integer (PK)
- employee_id: String(20)
- employee_name: String(50)
- department: Enum('淡海', '安坑')
- record_date: Date
- total_minutes: Integer
- incident_count: Integer
- fiscal_year: Integer
- fiscal_month: Integer
- created_at: DateTime
- updated_at: DateTime
- UniqueConstraint(employee_id, record_date)
```

#### DrivingCompetition (駕駛競賽排名)
```python
- id: Integer (PK)
- employee_id: String(20)
- employee_name: String(50)
- department: Enum('淡海', '安坑')
- competition_year: Integer
- competition_month: Integer
- total_driving_minutes: Integer
- total_incidents: Integer
- safety_score: Float
- rank_in_department: Integer
- rank_overall: Integer
- created_at: DateTime
- updated_at: DateTime
- UniqueConstraint(employee_id, competition_year, competition_month)
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 管理員能在 10 分鐘內完成雙部門的 Google 服務配置
- **SC-002**: 員工資料 CRUD 操作響應時間 < 1 秒
- **SC-003**: 權限檢查正確率達 100%（無越權操作）
- **SC-004**: 班表與勤務表同步成功率 > 99%（排除網路問題）
- **SC-005**: 定時任務執行準時率 > 99%（誤差 < 1 分鐘）
- **SC-006**: PDF 條碼識別與部門判斷正確率達 100%
- **SC-007**: 駕駛競賽排名計算準確率達 100%（與手動計算一致）
- **SC-008**: 系統在 Render 的運行時間達 24/7（UptimeRobot 監控）
- **SC-009**: TiDB 資料庫用量監控，提前 20% 發出警告
- **SC-010**: 網頁應用首次載入時間 < 3 秒
- **SC-011**: 桌面應用啟動時間 < 5 秒
- **SC-012**: 憑證驗證測試完成時間 < 5 秒 ⭐ **(新增)**
- **SC-013**: 連線狀態檢測延遲 < 1 秒 ⭐ **(新增)**
- **SC-014**: 手動同步功能可在管理員發起後 3 秒內開始執行 ⭐ **(新增)**
- **SC-015a**: 本地快取（若實作）命中率 > 80%，減少 API 請求 50% ⭐ **(新增)**
- **SC-015b**: 桌面應用不可用時，核心功能（資料瀏覽、履歷建立）仍能正常運作 ⭐ **(容錯設計)**
- **SC-015c**: 桌面應用檔案處理 API 響應時間 < 3 秒（Word生成、條碼生成）⭐ **(新增)**

### Assumptions

#### 資料與服務
- 淡海與安坑的考核標準表相同（V1 與 V2）
- Google Sheets API 配額足夠每日同步使用
- TiDB 免費版 5GB 儲存空間足夠 2 年使用
- Render 免費版 750 小時/月額度足夠 24/7 運行
- 員工編號格式保持一致（YYMMM0XXX）
- 駕駛競賽方案在年度內不變更規則
- 安坑班表結構與淡海相似，差異可在 Phase 3 處理
- 使用者同時在線人數 < 10 人
- 網路連線穩定，Google API 可用性 > 99%

#### 架構與使用環境 ⭐ **(新增)**
- 使用者瀏覽器支援現代 JavaScript（ES6+）與 HTTPS
- 使用者裝置為 Windows 作業系統（桌面應用僅支援 Windows）
- 檔案生成功能使用頻率較低（每日 < 50 次），可接受需啟動桌面應用
- 使用者可存取 GitHub Pages（https://username.github.io），無企業防火牆限制
- 本機桌面應用 API（localhost:8000）不會與其他本機服務衝突
- 核心功能（資料瀏覽、履歷建立）使用頻率高，必須隨時可用

## Implementation Phases

### Phase 0: 基礎架構 (估計 10-14 天) ⭐ **(架構調整)**
- 建立專案結構（前端 + 雲端 API + 本機 API）
  - 前端：GitHub Pages（Vue.js/React）專案初始化
  - 雲端後端：FastAPI 專案結構（Render）
  - 本機後端：FastAPI 本機 API（桌面應用）
- 設定 TiDB 資料庫連接與連線池
- 實作使用者認證與權限中間件（JWT）
- 建立基礎資料模型（Employee, User, SystemSetting, GoogleOAuthToken）⭐ **(已更新)**
- **憑證管理系統**（環境變數讀取、加密工具類別）⭐ **(新增)**
  - 實作 `TokenEncryption` 類別（Fernet 加密/解密）
  - 實作服務帳戶憑證載入（Base64 解碼）
  - 建立 `.env.example` 範本與 `.gitignore` 規則
- **前端連線狀態檢測功能**（檢測雲端 API 與本機 API）⭐ **(新增)**
- **本機 API CORS 設定**（允許 GitHub Pages 跨域請求）⭐ **(新增)**
- **本機憑證管理器**（OAuth 令牌加密檔案存儲）⭐ **(新增)**
- 部署雲端 FastAPI 到 Render
- 部署前端到 GitHub Pages
- 設定 UptimeRobot 監控
- 開發歷史資料遷移腳本（`scripts/migrate_from_sqlite.py`）

### Phase 1: 員工管理模組 (估計 10-14 天) ⭐ **(架構調整)**
- 雲端 API：員工資料 CRUD 端點
- 雲端 API：員工調動記錄功能
- 雲端 API：員工編號解析入職年月
- 雲端 API：批次匯入/匯出功能
- 權限控制實作（API 中間件）
- **前端網頁介面**（員工列表、詳情、編輯表單）⭐ **(網頁應用)**
- **前端路由設定**（Vue Router / React Router）⭐ **(網頁應用)**
- **前端狀態管理**（Pinia / Redux）⭐ **(網頁應用)**

### Phase 2: Google 服務整合 (估計 12-16 天) ⭐ **(時程已調整)**
- Google 服務管理器（多憑證支援）
- **OAuth 授權流程實作** ⭐ **(新增)**
  - 實作 `/api/google/auth-url` 端點（產生授權 URL）
  - 實作 `/api/auth/google/callback` 端點（接收授權碼）
  - 實作 `/api/google/get-access-token` 端點（令牌刷新）
  - OAuth 令牌加密存儲與讀取
- 系統設定介面（部門配置）
- **憑證驗證功能（Dry Run）** ⭐ **(新增)**
- 班表同步模組（淡海，使用前專案邏輯）
- **手動同步功能與進度顯示** ⭐ **(新增)**
- 勤務表同步模組（待釐清結構後實作）
- 駕駛時數統計
- 定時任務設定

### Phase 3: 安坑模組適配 (估計 5-7 天)
- 安坑班表結構解析（待釐清）
- 安坑勤務表同步
- 雙部門測試

### Phase 4: 駕駛競賽模組 (估計 7-10 天)
- 勤務標準時間管理功能（後台 CRUD + Excel 匯入）
- 駕駛競賽計算邏輯（最終積分公式已確認，見 PC-001）
- 月度排名自動計算（部門排名 + 全公司排名）
- 競賽報表產出
- 前端介面（勤務標準時間管理、競賽排名顯示）

### Phase 5: 本機 API 檔案處理功能 (估計 10-14 天) ⭐ **(架構調整)**
- **本機 API：Word 文件生成端點**（`POST /api/generate-word`）⭐ **(新增)**
- **本機 API：條碼生成端點**（`POST /api/generate-barcode`，加入部門前綴）⭐ **(新增)**
- **本機 API：PDF 掃描與切分**（條碼識別、部門判斷）
- **本機 API：Google Drive 上傳端點**（`POST /api/upload-to-drive`）⭐ **(新增)**
- 多部門 Google Drive 憑證管理
- **前端網頁：檔案生成功能按鈕**（檢測本機 API 可用性）⭐ **(容錯設計)**
- **前端網頁：檔案生成進度顯示**（Word、PDF、條碼）⭐ **(新增)**
- 桌面應用托盤程式開發（啟動/停止本機 API）

### Phase 6: 報表與主管功能 (估計 5-7 天)
- 主管角色權限實作
- 各類報表產出
- 報表匯出功能

### Phase 7: 測試與優化 (估計 7-10 天)
- 整合測試
- 權限測試
- 效能優化
- 使用者驗收測試

**總估計時間：66-92 天（約 3.0-4.1 個月）** ⭐ **(已根據架構調整更新)**

---

## 更新記錄

### v1.4 (2026-01-28) - 憑證管理與安全策略規範

**新增章節**：
- ✅ Credential Management & Security 完整章節
  - 兩種憑證類型說明（服務帳戶、OAuth 2.0）
  - 雲端後端憑證儲存方案（環境變數 + 資料庫加密）
  - 本機應用憑證儲存方案（加密檔案）
  - OAuth 授權流程設計（Sequence Diagram）
  - 安全規範與檢查清單

**新增資料模型**：
- ✅ GoogleOAuthToken 表（OAuth 令牌加密儲存）
  - `encrypted_refresh_token` (LargeBinary)
  - `encrypted_access_token` (LargeBinary, nullable)
  - `access_token_expires_at` (DateTime)
  - `department` (Enum)

**新增功能需求**：
- ✅ FR-065 ~ FR-074：憑證管理相關需求
  - 雙部門獨立憑證配置
  - Base64 編碼服務帳戶憑證
  - Fernet 加密工具類別
  - OAuth 授權流程端點
  - 本機加密檔案存儲
  - 檔案權限控制（0o600）
  - 日誌安全（不記錄憑證）
  - `.gitignore` 規則
  - 憑證健康檢查

**新增成功標準**：
- ✅ SC-019 ~ SC-023：憑證安全相關標準
  - Git 記錄不含憑證
  - 加密效能 < 10ms
  - 憑證輪換 < 5 分鐘
  - OAuth 授權完成 < 2 分鐘
  - 檔案權限檢查 100%

**實作階段更新**：
- ✅ Phase 0：加入憑證管理系統開發
  - TokenEncryption 類別實作
  - 服務帳戶憑證載入
  - 本機憑證管理器
- ✅ Phase 2：加入 OAuth 授權流程實作
  - `/api/google/auth-url` 端點
  - `/api/auth/google/callback` 端點
  - `/api/google/get-access-token` 端點

**技術決策**：
- 加密方案：Fernet (對稱加密)
- 服務帳戶儲存：Render 環境變數（Base64）
- OAuth 令牌儲存：TiDB 加密欄位
- 本機令牌儲存：`~/.driver_management_system/tokens.encrypted`
- 檔案權限：`0o600`（僅擁有者可讀寫）

**安全規範強化**：
- ❌ 禁止硬編碼憑證
- ❌ 禁止明文儲存敏感資訊
- ❌ 禁止將憑證寫入日誌
- ❌ 禁止提交憑證檔案到 Git
- ✅ 必須使用環境變數或加密存儲
- ✅ 必須定期輪換憑證（建議 90 天）

---

### v1.3 (2026-01-28) - 架構調整：混合式三層架構

**架構重大變更**：
- ✅ 從 `PyQt6 桌面應用 + FastAPI 雲端 API` 改為 `GitHub Pages 網頁應用 + Render FastAPI + 本機桌面應用 API`
- ✅ 網頁應用為主要使用者介面，取代 PyQt6 桌面應用
- ✅ 本機桌面應用角色調整為「檔案處理工具」，提供本機 API（localhost:8000）
- ✅ 核心功能（資料瀏覽、履歷建立、員工管理）完全運行於網頁端

**容錯設計新增**：
- ✅ FR-002c：核心功能不依賴桌面應用，桌面應用失敗不影響系統運作
- ✅ FR-002e：桌面應用不可用時，禁用檔案生成功能並提示使用者
- ✅ FR-039、FR-048：檔案功能與核心功能解耦
- ✅ SC-015b：容錯設計成功標準

**前端網頁應用新增**：
- ✅ FR-035 ~ FR-040：網頁應用功能需求
- ✅ GitHub Pages 託管方案確認（免費、支援 SPA、自動部署）
- ✅ CORS 跨域請求處理（本機 API）

**本機桌面應用調整**：
- ✅ FR-041 ~ FR-047：本機 API 功能需求（檔案處理）
- ✅ FR-031 ~ FR-047：Word 生成、PDF 處理、條碼生成、Google Drive 上傳端點
- ✅ 系統托盤程式（啟動/停止 API、狀態顯示）

**實作階段調整**：
- ✅ Phase 0：10-14 天（原 7-10 天，新增前端專案初始化、CORS 設定）
- ✅ Phase 1：10-14 天（原 7-10 天，新增前端網頁介面、路由、狀態管理）
- ✅ Phase 5：10-14 天（原 5-7 天，新增本機 API 端點開發、前端整合）
- ✅ 總時程：66-92 天（約 3.0-4.1 個月）

**技術堆疊調整**：
- 前端：Vue.js 3 / React（GitHub Pages）
- 雲端後端：FastAPI（Render）+ TiDB MySQL
- 本機後端：FastAPI（本機 API）+ Python 檔案處理套件

---

### v1.2 (2026-01-28) - 資料庫連線規格新增

**新增內容：**
1. ✅ Database Configuration 章節：完整資料庫連線配置說明
2. ✅ TiDB 連線資訊與測試結果
3. ✅ 環境變數設定規範（`.env` 檔案）
4. ✅ 連線池設定建議（SQLAlchemy）
5. ✅ 資料庫初始化流程與索引建議
6. ✅ 儲存空間監控策略（5GB 限制管理）
7. ✅ 自動備份策略（每日凌晨 4:00）
8. ✅ 健康檢查端點範例（`/health` 與 `/health/database`）
9. ✅ FR-049 ~ FR-054：資料庫相關功能需求
10. ✅ SC-015 ~ SC-018：資料庫相關成功標準

**技術決策：**
- 資料庫：TiDB v7.5.6-serverless（相容 MySQL 8.0.11）
- Python 驅動：pymysql（支援 SSL/TLS）
- ORM：SQLAlchemy（連線池管理）
- 連線池：5 個常駐連線 + 10 個額外連線

**安全性：**
- 敏感資訊使用環境變數保護
- SSL/TLS 加密連線啟用
- `.env` 檔案加入 `.gitignore`
- 提供 `.env.example` 範本

---

### v1.1 (2026-01-28) - Gemini 審驗建議採納

**新增功能：**
1. ✅ PC-005：歷史資料遷移需求釐清
2. ✅ User Story 4 擴充：手動同步功能與進度顯示
3. ✅ User Story 6（新增）：系統連線狀態監控與憑證驗證
4. ✅ FR-024a ~ FR-024f：手動同步與憑證驗證需求
5. ✅ FR-037a ~ FR-037e：連線狀態顯示需求
6. ✅ FR-041 ~ FR-044：本地快取（可選）
7. ✅ FR-045 ~ FR-048：歷史資料遷移（待確認）
8. ✅ SC-011 ~ SC-014：新增成功標準
9. ✅ 時程調整：Phase 0（+2天）、Phase 2（+2天）

**改進項目：**
- 提升使用者體驗：即時連線狀態回饋
- 降低操作風險：憑證驗證避免配置錯誤
- 增強可靠性：手動同步補救自動排程失敗
- 提升效能：本地快取減少 API 請求

---

**下一步**：
1. 使用者確認規格文件無誤
2. 釐清 Pending Clarifications 中的問題
3. 開始 Phase 0 實作
