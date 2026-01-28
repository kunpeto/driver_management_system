# Tasks: 司機員管理系統 - 整體架構

**Feature**: 001-system-architecture
**Input**: Design documents from `/specs/001-system-architecture/`
**Prerequisites**: plan.md, spec.md, research.md

**Organization**: 任務按用戶故事分組，以實現獨立實作與測試。

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可並行執行（不同檔案，無依賴關係）
- **[Story]**: 任務所屬的用戶故事（如 US1, US2, US3）
- 描述中包含明確的檔案路徑

---

## Path Conventions

**三層混合架構**：
- 前端網頁：`frontend/src/`
- 雲端後端：`backend/src/`
- 本機後端：`desktop_app/src/`
- 測試：`backend/tests/`, `frontend/tests/`
- 文件：`docs/`
- 腳本：`scripts/`

---

## Phase 1: Setup (Shared Infrastructure) ✅ 完成

**目的**: 專案初始化與基礎結構建立

**完成日期**: 2026-01-28

- [x] T001 建立專案根目錄結構（frontend/, backend/, desktop_app/, docs/, scripts/）
- [x] T002 [P] 初始化前端 Vue.js 3 專案在 frontend/ 目錄
- [x] T003 [P] 初始化雲端後端 FastAPI 專案在 backend/ 目錄
- [x] T004 [P] 初始化本機後端 FastAPI 專案在 desktop_app/ 目錄
- [x] T005 [P] 建立 requirements.txt 在 backend/ 目錄（FastAPI, SQLAlchemy, pymysql, python-jose, bcrypt, APScheduler）
- [x] T006 [P] 建立 requirements.txt 在 desktop_app/ 目錄（FastAPI, python-docx, PyPDF2, python-barcode, google-api-python-client）
- [x] T007 [P] 建立 package.json 在 frontend/ 目錄（Vue 3, Vue Router 4, Pinia, Axios, Element Plus）
- [x] T008 建立 .gitignore 檔案（已更新，包含憑證排除規則）
- [x] T009 建立 .env.example 檔案（環境變數範本，已包含完整註解）
- [x] T010 [P] 設定前端 ESLint 與 Prettier 在 frontend/.eslintrc.js 與 .prettierrc
- [x] T011 [P] 設定後端 Black 與 Flake8 在 backend/pyproject.toml 與 .flake8

**Checkpoint**: ✅ 專案結構完成，可開始安裝依賴套件

---

## Phase 2: Foundational (Blocking Prerequisites)

**目的**: 核心基礎設施，必須完成才能開始任何用戶故事

**⚠️ CRITICAL**: 此階段完成前，無法開始用戶故事開發

### 資料庫與連線

- [x] T012 建立 TiDB 連線配置工具在 backend/src/config/database.py（SQLAlchemy 引擎、連線池設定）✅ 2026-01-28
- [x] T013 建立環境變數載入工具在 backend/src/config/settings.py（使用 pydantic-settings）✅ 2026-01-28
- [x] T014 建立資料庫 Base 模型在 backend/src/models/base.py（SQLAlchemy declarative_base）✅ 2026-01-28
- [x] T015 建立資料庫初始化腳本在 scripts/init_database.py（建立表、索引、預設資料）✅ 2026-01-29

### 憑證管理系統 ⭐

- [x] T016 實作 TokenEncryption 類別在 backend/src/utils/encryption.py（Fernet 加密/解密工具）✅ 2026-01-29
- [x] T017 實作服務帳戶憑證載入工具在 backend/src/utils/google_credentials.py（Base64 解碼、環境變數讀取）✅ 2026-01-29
- [x] T018 實作本機憑證管理器在 desktop_app/src/utils/credential_manager.py（OAuth 令牌加密檔案存儲）✅ 2026-01-29
- [x] T037a 實作憑證驗證服務在 backend/src/services/credential_validator.py（驗證 Service Account 格式、測試 Sheets 存取權限、驗證 OAuth 2.0 格式）⭐ **(新增：G1)** ✅ 2026-01-29

### 憑證驗證測試 ⭐ **(新增：G1)**

- [x] T037b [P] 實作憑證驗證整合測試在 backend/tests/integration/test_credential_validation.py（測試有效/無效憑證、權限檢查、模擬無權限情境）✅ 2026-01-28

### 認證與授權

- [x] T019 建立 JWT 工具類別在 backend/src/utils/jwt.py（生成、驗證、解析 Token）✅ 2026-01-29
- [x] T020 實作密碼雜湊工具在 backend/src/utils/password.py（bcrypt 加密、驗證）✅ 2026-01-29
- [x] T021 實作認證中間件在 backend/src/middleware/auth.py（JWT Token 驗證）✅ 2026-01-29
- [x] T022 實作權限檢查中間件在 backend/src/middleware/permission.py（角色與部門權限控制）✅ 2026-01-29

### API 基礎設施

- [x] T023 建立 FastAPI 主程式在 backend/src/main.py（應用初始化、CORS 設定、路由註冊）✅ 2026-01-28
- [x] T024 建立錯誤處理中間件在 backend/src/middleware/error_handler.py（統一錯誤回應格式）✅ 2026-01-29
- [x] T025 建立日誌配置在 backend/src/utils/logger.py（結構化日誌、不記錄敏感資訊）✅ 2026-01-29
- [x] T026 [P] 建立健康檢查端點在 backend/src/main.py（GET /health, GET /health/database）✅ 2026-01-28（暫整合於 main.py）

### 前端基礎設施

- [x] T027 設定 Vue Router 在 frontend/src/router/index.js（路由表、導航守衛）✅ 2026-01-29
- [x] T028 設定 Pinia Store 在 frontend/src/stores/index.js（狀態管理初始化）✅ 2026-01-29
- [x] T029 設定 Axios 實例在 frontend/src/utils/api.js（攔截器、錯誤處理、Token 附加）✅ 2026-01-29
- [x] T030 建立全域錯誤處理器在 frontend/src/utils/errorHandler.js ✅ 2026-01-29
- [x] T031 [P] 建立 UI 元件庫封裝在 frontend/src/components/common/（Button, Input, Modal 等）✅ 2026-01-29

### 本機 API 基礎設施

- [x] T032 建立本機 FastAPI 主程式在 desktop_app/src/main.py（CORS 設定、健康檢查）✅ 2026-01-29
- [x] T033 建立系統托盤程式在 desktop_app/src/tray_app.py（啟動/停止 API、狀態顯示）✅ 2026-01-29

**Checkpoint**: 基礎設施完成 - 用戶故事實作可以開始

---

## Phase 3: User Story 1 - 系統管理員初始化系統配置 (Priority: P0) 🎯 MVP

**Goal**: 管理員可為淡海和安坑兩個部門分別配置 Google 服務連接資訊

**Independent Test**: 管理員登入後進入系統設定頁面，分別設定淡海和安坑的 Google Sheets ID、Drive 資料夾 ID、API 憑證路徑，儲存後重新載入頁面確認設定保留。

### 資料模型

- [ ] T034 [P] [US1] 建立 SystemSetting 模型在 backend/src/models/system_setting.py（key, value, department, description, UniqueConstraint）
- [ ] T035 [P] [US1] 建立 GoogleOAuthToken 模型在 backend/src/models/google_oauth_token.py（department, encrypted_refresh_token, encrypted_access_token）

### 後端服務

- [ ] T036 [US1] 實作 SystemSettingService 在 backend/src/services/system_setting_service.py（CRUD、部門篩選、憑證驗證）
- [ ] T037 [US1] 實作 Google 憑證驗證服務在 backend/src/services/google_credential_validator.py（Dry Run 測試連線）

### 後端 API 端點

- [ ] T038 [US1] 實作系統設定 API 在 backend/src/api/system_settings.py（GET /api/settings, POST /api/settings, PUT /api/settings/{id}）
- [ ] T039 [US1] 實作憑證驗證 API 在 backend/src/api/google_credentials.py（POST /api/google/validate-credentials）

### 前端實作

- [ ] T040 [US1] 建立系統設定頁面在 frontend/src/views/SystemSettings.vue（淡海與安坑設定區塊）
- [ ] T041 [US1] 建立系統設定 Store 在 frontend/src/stores/systemSettings.js（Pinia state、actions）
- [ ] T042 [US1] 實作憑證上傳與驗證元件在 frontend/src/components/settings/CredentialUpload.vue（檔案選擇、驗證回饋）

**Checkpoint**: 系統設定功能完成，管理員可配置 Google 服務

---

## Phase 4: User Story 2 - 員工資料管理（含部門與調動） (Priority: P1)

**Goal**: 值班台人員可管理員工基本資料，包含新增、編輯、標記離職、記錄調動

**Independent Test**: 淡海值班台人員新增一位員工，填寫編號、姓名、聯絡資訊，系統自動解析入職年月並設定部門為淡海。後續該員工調動到安坑，記錄調動歷史。

### 資料模型

- [ ] T043 [P] [US2] 建立 Employee 模型在 backend/src/models/employee.py（employee_id, employee_name, current_department, hire_year_month, 等欄位）
- [ ] T044 [P] [US2] 建立 EmployeeTransfer 模型在 backend/src/models/employee_transfer.py（employee_id FK, from_department, to_department, transfer_date）

### 後端服務

- [ ] T045 [US2] 實作員工編號解析工具在 backend/src/utils/employee_parser.py（從編號解析入職年月，如 1011M0095 → 2021-11）
- [ ] T046 [US2] 實作 EmployeeService 在 backend/src/services/employee_service.py（CRUD、部門篩選、離職標記）
- [ ] T047 [US2] 實作 EmployeeTransferService 在 backend/src/services/employee_transfer_service.py（記錄調動、更新部門、歷史查詢）
- [ ] T048 [US2] 實作批次匯入服務在 backend/src/services/employee_import_service.py（Excel 匯入、資料驗證）
- [ ] T049 [US2] 實作批次匯出服務在 backend/src/services/employee_export_service.py（Excel 匯出、部門篩選）

### 後端 API 端點

- [ ] T050 [US2] 實作員工 CRUD API 在 backend/src/api/employees.py（GET /api/employees, POST, PUT, DELETE）
- [ ] T051 [US2] 實作員工調動 API 在 backend/src/api/employee_transfers.py（POST /api/employees/{id}/transfer, GET /api/employees/{id}/transfers）
- [ ] T052 [US2] 實作批次匯入/匯出 API 在 backend/src/api/employee_batch.py（POST /api/employees/import, GET /api/employees/export）

### 前端實作

- [ ] T053 [P] [US2] 建立員工列表頁面在 frontend/src/views/Employees.vue（表格、搜尋、篩選）
- [ ] T054 [P] [US2] 建立員工詳情頁面在 frontend/src/views/EmployeeDetail.vue（顯示完整資訊、調動歷史）
- [ ] T055 [P] [US2] 建立員工編輯表單元件在 frontend/src/components/employees/EmployeeForm.vue（新增/編輯共用）
- [ ] T056 [US2] 建立員工調動對話框元件在 frontend/src/components/employees/TransferDialog.vue（選擇部門、日期、原因）
- [ ] T057 [US2] 建立員工 Store 在 frontend/src/stores/employees.js（Pinia state、actions、員工列表管理）
- [ ] T058 [US2] 實作批次匯入/匯出元件在 frontend/src/components/employees/BatchOperations.vue（檔案上傳、匯出下載）

**Checkpoint**: 員工資料管理功能完成，可進行 CRUD 與調動操作

---

## Phase 5: User Story 3 - 權限控制與資料過濾 (Priority: P1)

**Goal**: 系統根據使用者角色和部門限制資料存取權限

**Independent Test**: 淡海值班台人員登入後，列表預設顯示淡海部門資料，但可查詢安坑資料（唯讀）。主管可查看所有部門資料。

### 資料模型

- [ ] T059 [US3] 建立 User 模型在 backend/src/models/user.py（username, password_hash, role, department, is_active）

### 後端服務

- [ ] T060 [US3] 實作 UserService 在 backend/src/services/user_service.py（CRUD、密碼驗證、角色管理）
- [ ] T061 [US3] 實作 AuthService 在 backend/src/services/auth_service.py（登入、JWT 生成、Token 刷新）
- [ ] T062 [US3] 實作權限檢查服務在 backend/src/services/permission_service.py（檢查使用者是否可編輯指定部門資料）

### 後端 API 端點

- [ ] T063 [US3] 實作認證 API 在 backend/src/api/auth.py（POST /api/auth/login, POST /api/auth/refresh, POST /api/auth/logout）
- [ ] T064 [US3] 實作使用者管理 API 在 backend/src/api/users.py（GET /api/users, POST, PUT, DELETE，僅 Admin 可存取）
- [ ] T065 [US3] 更新員工 API 權限控制在 backend/src/api/employees.py（依角色與部門限制編輯權限）

### 前端實作

- [ ] T066 [P] [US3] 建立登入頁面在 frontend/src/views/Login.vue（使用者名稱、密碼、記住我）
- [ ] T067 [P] [US3] 建立使用者管理頁面在 frontend/src/views/Users.vue（使用者列表、新增、編輯，僅 Admin）
- [ ] T068 [US3] 建立認證 Store 在 frontend/src/stores/auth.js（Pinia state、登入/登出 actions、Token 管理）
- [ ] T069 [US3] 實作 Vue Router 導航守衛在 frontend/src/router/index.js（檢查登入狀態、權限重定向）
- [ ] T070 [US3] 更新員工列表頁面在 frontend/src/views/Employees.vue（部門預設篩選、編輯按鈕權限控制）

**Checkpoint**: 權限控制功能完成，不同角色有不同的資料存取權限

---

## Phase 6: User Story 6 - 系統連線狀態監控與憑證驗證 (Priority: P2)

**Goal**: 桌面應用常駐顯示雲端服務與 Google API 連線狀態，管理員上傳憑證時立即驗證有效性

**Independent Test**: 桌面應用啟動後在狀態列顯示「雲端連線：正常」與「Google API：正常」。管理員上傳淡海的 Google 憑證時，系統立即嘗試連接並回報結果。

### 後端服務

- [ ] T071 [P] [US6] 實作連線狀態檢查服務在 backend/src/services/connection_monitor.py（檢查 TiDB、Google Sheets、Google Drive 連線）
- [ ] T072 [P] [US6] 實作 Google API 憑證測試服務在 backend/src/services/google_api_tester.py（測試服務帳戶與 OAuth 憑證）

### 後端 API 端點

- [ ] T073 [US6] 實作連線狀態 API 在 backend/src/api/connection_status.py（GET /api/status/cloud, GET /api/status/google）

### 本機應用實作

- [ ] T074 [US6] 實作連線狀態監控在 desktop_app/src/services/connection_monitor.py（定期檢查雲端 API 與 Google API）
- [ ] T075 [US6] 更新系統托盤程式在 desktop_app/src/tray_app.py（狀態列圖示、連線狀態顯示）
- [ ] T076 [US6] 實作憑證驗證介面在 desktop_app/src/ui/credential_validator.py（顯示驗證結果、錯誤訊息）

### 前端實作

- [ ] T077 [US6] 建立連線狀態元件在 frontend/src/components/common/ConnectionStatus.vue（雲端、本機 API、Google API 狀態顯示）
- [ ] T078 [US6] 更新系統設定頁面在 frontend/src/views/SystemSettings.vue（整合憑證驗證按鈕與即時回饋）

**Checkpoint**: 連線狀態監控與憑證驗證功能完成

---

## Phase 7: User Story 4 - Google Sheets 班表自動同步與手動觸發 (Priority: P2)

**Goal**: 系統每日自動從 Google Sheets 同步班表資料，並提供手動同步功能

**Independent Test**: 系統在凌晨 2:00 自動執行同步任務，從淡海和安坑的 Google Sheets 讀取當月班表並寫入資料庫。管理員可在任何時間點點擊「立即同步」按鈕手動觸發同步。

### 資料模型

- [ ] T079 [US4] 建立 Schedule 模型在 backend/src/models/schedule.py（employee_id, department, schedule_date, shift_type 等欄位）

### 後端服務

- [ ] T080 [US4] 實作 Google Sheets 讀取服務在 backend/src/services/google_sheets_reader.py（使用服務帳戶憑證、唯讀權限）
- [ ] T081 [US4] 實作班表解析服務在 backend/src/services/schedule_parser.py（解析分頁資料、員工班別）
- [ ] T082 [US4] 實作班表同步服務在 backend/src/services/schedule_sync_service.py（讀取、解析、寫入資料庫、錯誤處理）
- [ ] T083 [US4] 實作定時任務管理在 backend/src/tasks/scheduler.py（APScheduler 配置、班表同步任務註冊）

### 後端 API 端點

- [ ] T084 [US4] 實作班表查詢 API 在 backend/src/api/schedules.py（GET /api/schedules, 支援日期與部門篩選）
- [ ] T085 [US4] 實作手動同步 API 在 backend/src/api/sync_tasks.py（POST /api/sync/schedule, GET /api/sync/status/{task_id}）

### 前端實作

- [ ] T086 [P] [US4] 建立班表查詢頁面在 frontend/src/views/Schedules.vue（日曆視圖、員工班表）
- [ ] T087 [P] [US4] 建立 Google 服務管理頁面在 frontend/src/views/GoogleServices.vue（手動同步按鈕、同步歷史）
- [ ] T088 [US4] 建立同步進度元件在 frontend/src/components/sync/SyncProgress.vue（即時進度條、已處理/總數、取消按鈕）
- [ ] T089 [US4] 建立同步結果元件在 frontend/src/components/sync/SyncResult.vue（新增/更新/失敗統計）

**Checkpoint**: Google Sheets 班表同步功能完成（自動與手動）

---

## Phase 8: User Story 7 - PDF 條碼識別（含部門判斷） (Priority: P2)

**Goal**: 桌面應用處理 PDF 掃描文件，根據條碼前綴（TH/AK）自動判斷部門並上傳到對應的 Google Drive 資料夾

**Independent Test**: 使用者上傳一個包含多頁的 PDF，條碼為「TH-12345」和「AK-67890」，系統自動切分為兩個檔案並上傳到淡海和安坑的 Drive 資料夾。

### 本機應用服務

- [ ] T090 [P] [US7] 實作 PDF 條碼識別服務在 desktop_app/src/services/barcode_reader.py（PyPDF2 + pyzbar）
- [ ] T091 [P] [US7] 實作 PDF 切分服務在 desktop_app/src/services/pdf_splitter.py（依條碼切分多頁 PDF）
- [ ] T092 [US7] 實作部門判斷服務在 desktop_app/src/services/department_detector.py（TH → 淡海、AK → 安坑）
- [ ] T093 [US7] 實作 Google Drive 上傳服務在 desktop_app/src/services/google_drive_uploader.py（使用 OAuth 令牌、部門資料夾 ID）

### 本機 API 端點

- [ ] T094 [US7] 實作 PDF 處理 API 在 desktop_app/src/api/pdf_processor.py（POST /api/pdf/process, 返回處理結果與 Drive 連結）
- [ ] T095 [US7] 實作條碼生成 API 在 desktop_app/src/api/barcode_generator.py（POST /api/barcode/generate, 返回 Base64 圖片）

### 後端 OAuth 授權流程

- [ ] T096 [US7] 實作 OAuth 授權 URL 生成端點在 backend/src/api/google_oauth.py（GET /api/google/auth-url?department=淡海）
- [ ] T097 [US7] 實作 OAuth 回調端點在 backend/src/api/google_oauth.py（GET /api/auth/google/callback, 換取 refresh_token 並加密存儲）
- [ ] T098 [US7] 實作 Access Token 取得端點在 backend/src/api/google_oauth.py（POST /api/google/get-access-token, 刷新令牌）

### OAuth 回調端點測試 ⭐ **(新增：U1)**

- [ ] T098a [P] [US7] 實作 OAuth 回調端點單元測試在 backend/tests/unit/test_google_oauth.py（測試正常授權、拒絕授權 error='access_denied'、無效 code、遺失 code 參數、驗證 refresh_token 加密儲存）

### 前端實作

- [ ] T099 [P] [US7] 建立 PDF 上傳頁面在 frontend/src/views/PdfUpload.vue（檔案拖放、處理進度、結果顯示）
- [ ] T100 [P] [US7] 建立條碼生成頁面在 frontend/src/views/BarcodeGenerator.vue（輸入履歷 ID、選擇部門、下載條碼）
- [ ] T101 [US7] 建立 Google Drive 授權元件在 frontend/src/components/google/DriveAuthorization.vue（授權按鈕、授權狀態顯示）

**Checkpoint**: PDF 條碼識別與 Google Drive 上傳功能完成

---

## Phase 9: User Story 5 - 駕駛時數統計與競賽排名 (Priority: P3)

**Goal**: 系統每日同步勤務表資料，每月自動計算駕駛競賽排名

**Independent Test**: 系統每月 1 日計算上月駕駛競賽排名，按部門和全公司分別排名。

### 資料模型

- [ ] T102 [P] [US5] 建立 RouteStandardTime 模型在 backend/src/models/route_standard_time.py（department, route_code, route_name, standard_minutes, is_active）
- [ ] T103 [P] [US5] 建立 DrivingDailyStats 模型在 backend/src/models/driving_daily_stats.py（employee_id, department, record_date, total_minutes, incident_count）
- [ ] T104 [P] [US5] 建立 DrivingCompetition 模型在 backend/src/models/driving_competition.py（employee_id, competition_year, competition_month, total_driving_minutes, safety_score, rank_in_department, rank_overall）

### 後端服務

- [ ] T105 [US5] 實作勤務標準時間管理服務在 backend/src/services/route_standard_time_service.py（CRUD 操作、Excel 匯入驗證）
- [ ] T106 [US5] 實作勤務表同步服務在 backend/src/services/duty_sync_service.py（讀取 Google Sheets 勤務表、查詢 route_standard_times、計算駕駛時數）
- [ ] T107 [US5] 實作駕駛時數計算服務在 backend/src/services/driving_stats_calculator.py（彙總每日時數、R班係數 × 2、責任事件懲罰係數 × 1/(1+N)）
- [ ] T108 [US5] 實作駕駛競賽排名服務在 backend/src/services/driving_competition_ranker.py（計算最終積分、部門排名、全公司排名、排除離職員工）
- [ ] T109 [US5] 新增定時任務在 backend/src/tasks/scheduler.py（勤務表同步 2:30、競賽排名計算每月 1 日 3:00）

### 後端 API 端點

- [ ] T110 [US5] 實作勤務標準時間 CRUD API 在 backend/src/api/route_standard_time.py（GET/POST/PUT/DELETE /api/routes, 僅 Admin 可編輯）
- [ ] T111 [US5] 實作勤務標準時間 Excel 匯入 API 在 backend/src/api/route_standard_time.py（POST /api/routes/import-excel, 驗證格式與欄位）
- [ ] T112 [US5] 實作駕駛時數查詢 API 在 backend/src/api/driving_stats.py（GET /api/driving/stats, 支援日期與員工篩選）
- [ ] T113 [US5] 實作駕駛競賽排名 API 在 backend/src/api/driving_competition.py（GET /api/driving/competition, 支援年月與部門篩選）

### 前端實作

- [ ] T114 [P] [US5] 建立勤務標準時間管理頁面在 frontend/src/views/RouteStandardTimes.vue（僅管理員可見、CRUD 表單、Excel 匯入功能）
- [ ] T115 [P] [US5] 建立駕駛時數查詢頁面在 frontend/src/views/DrivingStats.vue（員工時數統計、圖表顯示）
- [ ] T116 [P] [US5] 建立駕駛競賽排名頁面在 frontend/src/views/DrivingCompetition.vue（排名榜、積分顯示、部門與全公司排名）
- [ ] T117 [US5] 建立駕駛時數 Store 在 frontend/src/stores/drivingStats.js（Pinia state、actions）

**Checkpoint**: 駕駛時數統計與競賽排名功能完成

---

## Phase 10: Polish & Cross-Cutting Concerns

**目的**: 跨用戶故事的改進與最終優化

- [ ] T118 [P] 撰寫 API 文件在 docs/api.md（所有端點、請求/回應格式、錯誤碼）
- [ ] T119 [P] 撰寫部署指南在 docs/deployment.md（Render 部署步驟、環境變數設定、UptimeRobot 配置）
- [ ] T120 [P] 撰寫使用者手冊在 docs/user_manual.md（各功能操作說明、常見問題）
- [ ] T121 [P] 建立開發者快速入門在 docs/quickstart.md（本機開發環境設定、測試指令）
- [ ] T122 後端效能優化（資料庫查詢最佳化、快取策略、索引檢查）
- [ ] T123 前端效能優化（Code Splitting、Lazy Loading、圖片壓縮）
- [ ] T124 安全性審查（OWASP Top 10 檢查、SQL 注入防護、XSS 防護）
- [ ] T125 [P] 前端單元測試在 frontend/tests/unit/（關鍵元件測試）
- [ ] T126 [P] 後端單元測試在 backend/tests/unit/（服務層測試）
- [ ] T127 [P] 後端整合測試在 backend/tests/integration/（API 端點測試）
- [ ] T128 建立 GitHub Actions CI/CD 在 .github/workflows/ci.yml（自動測試、部署）
- [ ] T129 執行完整系統測試（所有用戶故事驗收標準）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 無依賴 - 可立即開始
- **Foundational (Phase 2)**: 依賴 Setup 完成 - **阻塞所有用戶故事**
- **User Stories (Phase 3-9)**: 全部依賴 Foundational 完成
  - US1, US2, US3 可並行開發（不同檔案）
  - US4, US5, US6, US7 可並行開發（不同檔案）
  - 或按優先級順序執行（P0 → P1 → P2 → P3）
- **Polish (Phase 10)**: 依賴所有期望的用戶故事完成

### User Story Dependencies

- **US1 (P0)**: 可在 Foundational 後開始 - 無其他用戶故事依賴
- **US2 (P1)**: 可在 Foundational 後開始 - 無其他用戶故事依賴
- **US3 (P1)**: 可在 Foundational 後開始 - 建議在 US2 後（需要 User 模型）
- **US4 (P2)**: 可在 Foundational 後開始 - 無其他用戶故事依賴
- **US5 (P3)**: 可在 Foundational 後開始 - 建議在 US4 後（共用 Google Sheets 服務）
- **US6 (P2)**: 可在 Foundational 後開始 - 無其他用戶故事依賴
- **US7 (P2)**: 可在 Foundational 後開始 - 建議在 US1 後（需要 OAuth 配置）

### Within Each User Story

- 資料模型 → 服務層 → API 端點 → 前端實作
- 標記 [P] 的任務可並行執行（不同檔案）
- 完成一個故事後再進入下一個優先級

### Parallel Opportunities

- **Setup 階段**: T002, T003, T004, T005, T006, T007, T010, T011 可並行
- **Foundational 階段**: 多數任務可並行（不同檔案）
- **US1**: T034, T035 可並行（不同模型）
- **US2**: T043, T044 可並行；T053, T054, T055 可並行
- **US4**: T086, T087 可並行
- **US5**: T102, T103 可並行；T110, T111 可並行
- **US7**: T090, T091 可並行；T099, T100 可並行
- **Polish**: T113, T114, T115, T116, T120, T121, T122 可並行

---

## Parallel Example: User Story 2

```bash
# 並行建立資料模型:
Task: "建立 Employee 模型在 backend/src/models/employee.py"
Task: "建立 EmployeeTransfer 模型在 backend/src/models/employee_transfer.py"

# 並行建立前端頁面:
Task: "建立員工列表頁面在 frontend/src/views/Employees.vue"
Task: "建立員工詳情頁面在 frontend/src/views/EmployeeDetail.vue"
Task: "建立員工編輯表單元件在 frontend/src/components/employees/EmployeeForm.vue"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2 & 3 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational (**CRITICAL** - 阻塞所有故事)
3. 完成 Phase 3: US1（系統設定）
4. 完成 Phase 4: US2（員工管理）
5. 完成 Phase 5: US3（權限控制）
6. **STOP and VALIDATE**: 測試核心功能（設定、員工管理、權限）
7. 部署/演示 MVP

### Incremental Delivery

1. Setup + Foundational → 基礎完成
2. 加入 US1 → 測試獨立 → 部署（系統可配置）
3. 加入 US2 → 測試獨立 → 部署（可管理員工）
4. 加入 US3 → 測試獨立 → 部署（權限控制完成，MVP！）
5. 加入 US4 → 測試獨立 → 部署（班表同步）
6. 加入 US6 → 測試獨立 → 部署（連線監控）
7. 加入 US7 → 測試獨立 → 部署（PDF 處理）
8. 加入 US5 → 測試獨立 → 部署（駕駛競賽，完整功能）

### Parallel Team Strategy

若有多位開發者：

1. 團隊共同完成 Setup + Foundational
2. Foundational 完成後：
   - **開發者 A**: US1（系統設定）
   - **開發者 B**: US2（員工管理）
   - **開發者 C**: US3（權限控制）前期準備
3. MVP 完成後：
   - **開發者 A**: US4（班表同步）
   - **開發者 B**: US6（連線監控）
   - **開發者 C**: US7（PDF 處理）
4. 最後共同完成 US5（駕駛競賽）

---

## Notes

- **[P] 任務**: 不同檔案，無依賴關係，可並行執行
- **[Story] 標籤**: 映射任務到特定用戶故事，便於追蹤
- **每個用戶故事**: 應獨立完成與測試
- **提交頻率**: 每完成一個任務或邏輯群組後提交
- **檢查點驗證**: 在每個檢查點停下來獨立驗證用戶故事
- **避免**: 模糊的任務描述、同一檔案衝突、破壞獨立性的跨故事依賴

---

## Summary

- **總任務數**: 131 個任務（新增勤務標準時間管理、憑證驗證、OAuth 回調測試任務）
- **已完成任務**: 35 個（Phase 1: 11 個 + Phase 2: 24 個）
- **進度**: 26.7%
- **用戶故事數**: 7 個（US1-US7，對應 spec.md 的 P0-P3 優先級）
- **可並行任務**: 約 40% 的任務標記為 [P]，可並行執行
- **建議 MVP 範圍**: Phase 1-5（Setup + Foundational + US1 + US2 + US3）
- **駕駛競賽模組**: PC-001 已釐清，Phase 9 任務可立即執行
- **測試覆蓋**: 新增憑證驗證測試（G1: T037a, T037b）與 OAuth 回調測試（U1: T098a）
- **完整功能交付**: 全部 10 個階段（包含所有用戶故事與優化）

### 進度更新記錄

| 日期 | 完成任務 | 累計完成 | 進度 |
|------|----------|----------|------|
| 2026-01-28 | T001-T014, T023, T026 | 16 | 12.2% |
| 2026-01-29 | T015-T033, T037a | 34 | 26.0% |
| 2026-01-28 | T037b (憑證驗證整合測試) | 35 | 26.7% |

---

**任務清單已生成完成！**

檔案位置：`specs/001-system-architecture/tasks.md`

按照此任務清單執行，可確保每個用戶故事獨立實作、獨立測試、漸進式交付價值。
