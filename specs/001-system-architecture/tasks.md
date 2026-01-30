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
- [x] T005 [P] 建立 requirements.txt 在 backend/ 目錄（FastAPI, SQLAlchemy, pymysql, python-jose, bcrypt, APScheduler, **python-docx, openpyxl, python-barcode, Pillow**）⭐ **新增 Office 文件與條碼生成依賴**
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

## Phase 3: User Story 1 - 系統管理員初始化系統配置 (Priority: P0) 🎯 MVP ✅ 完成

**Goal**: 管理員可為淡海和安坑兩個部門分別配置 Google 服務連接資訊

**Independent Test**: 管理員登入後進入系統設定頁面，分別設定淡海和安坑的 Google Sheets ID、Drive 資料夾 ID、API 憑證路徑，儲存後重新載入頁面確認設定保留。

**完成日期**: 2026-01-29

### 資料模型

- [x] T034 [P] [US1] 建立 SystemSetting 模型在 backend/src/models/system_setting.py（key, value, department, description, UniqueConstraint）✅ 2026-01-29
- [x] T035 [P] [US1] 建立 GoogleOAuthToken 模型在 backend/src/models/google_oauth_token.py（department, encrypted_refresh_token, encrypted_access_token）✅ 2026-01-29

### 後端服務

- [x] T036 [US1] 實作 SystemSettingService 在 backend/src/services/system_setting_service.py（CRUD、部門篩選、憑證驗證）✅ 2026-01-29
- [x] T037 [US1] 實作 Google 憑證驗證服務在 backend/src/services/google_credential_validator.py（Dry Run 測試連線）✅ 2026-01-29

### 後端 API 端點

- [x] T038 [US1] 實作系統設定 API 在 backend/src/api/system_settings.py（GET /api/settings, POST /api/settings, PUT /api/settings/{id}）✅ 2026-01-29
- [x] T039 [US1] 實作憑證驗證 API 在 backend/src/api/google_credentials.py（POST /api/google/validate-credentials）✅ 2026-01-29

### 前端實作

- [x] T040 [US1] 建立系統設定頁面在 frontend/src/views/SystemSettings.vue（淡海與安坑設定區塊）✅ 2026-01-29
- [x] T041 [US1] 建立系統設定 Store 在 frontend/src/stores/systemSettings.js（Pinia state、actions）✅ 2026-01-29
- [x] T042 [US1] 實作憑證上傳與驗證元件在 frontend/src/components/settings/CredentialUpload.vue（檔案選擇、驗證回饋）✅ 2026-01-29

**Checkpoint**: ✅ 系統設定功能完成，管理員可配置 Google 服務

---

## Phase 4: User Story 2 - 員工資料管理（含部門與調動） (Priority: P1) ✅ 完成

**Goal**: 值班台人員可管理員工基本資料，包含新增、編輯、標記離職、記錄調動

**Independent Test**: 淡海值班台人員新增一位員工，填寫編號、姓名、聯絡資訊，系統自動解析入職年月並設定部門為淡海。後續該員工調動到安坑，記錄調動歷史。

**完成日期**: 2026-01-29

### 資料模型

- [x] T043 [P] [US2] 建立 Employee 模型在 backend/src/models/employee.py（employee_id, employee_name, current_department, hire_year_month, 等欄位）✅ 2026-01-29
- [x] T044 [P] [US2] 建立 EmployeeTransfer 模型在 backend/src/models/employee_transfer.py（employee_id FK, from_department, to_department, transfer_date）✅ 2026-01-29

### 後端服務

- [x] T045 [US2] 實作員工編號解析工具在 backend/src/utils/employee_parser.py（從編號解析入職年月，如 1011M0095 → 2021-11）✅ 2026-01-29
- [x] T046 [US2] 實作 EmployeeService 在 backend/src/services/employee_service.py（CRUD、部門篩選、離職標記）✅ 2026-01-29
- [x] T047 [US2] 實作 EmployeeTransferService 在 backend/src/services/employee_transfer_service.py（記錄調動、更新部門、歷史查詢）✅ 2026-01-29
- [x] T048 [US2] 實作批次匯入服務在 backend/src/services/employee_import_service.py（Excel 匯入、資料驗證）✅ 2026-01-29
- [x] T049 [US2] 實作批次匯出服務在 backend/src/services/employee_export_service.py（Excel 匯出、部門篩選）✅ 2026-01-29

### 後端 API 端點

- [x] T050 [US2] 實作員工 CRUD API 在 backend/src/api/employees.py（GET /api/employees, POST, PUT, DELETE）✅ 2026-01-29
- [x] T051 [US2] 實作員工調動 API 在 backend/src/api/employee_transfers.py（POST /api/employees/{id}/transfer, GET /api/employees/{id}/transfers）✅ 2026-01-29
- [x] T052 [US2] 實作批次匯入/匯出 API 在 backend/src/api/employee_batch.py（POST /api/employees/import, GET /api/employees/export）✅ 2026-01-29

### 前端實作

- [x] T053 [P] [US2] 建立員工列表頁面在 frontend/src/views/Employees.vue（表格、搜尋、篩選）✅ 2026-01-29
- [x] T054 [P] [US2] 建立員工詳情元件在 frontend/src/components/employees/EmployeeDetail.vue（顯示完整資訊、調動歷史）✅ 2026-01-29
- [x] T055 [P] [US2] 建立員工編輯表單元件在 frontend/src/components/employees/EmployeeForm.vue（新增/編輯共用）✅ 2026-01-29
- [x] T056 [US2] 建立員工調動對話框元件在 frontend/src/components/employees/TransferDialog.vue（選擇部門、日期、原因）✅ 2026-01-29
- [x] T057 [US2] 建立員工 Store 在 frontend/src/stores/employees.js（Pinia state、actions、員工列表管理）✅ 2026-01-29
- [x] T058 [US2] 實作批次匯入/匯出元件在 frontend/src/components/employees/BatchOperations.vue（檔案上傳、匯出下載）✅ 2026-01-29

**Checkpoint**: ✅ 員工資料管理功能完成，可進行 CRUD 與調動操作

---

## Phase 5: User Story 3 - 權限控制與資料過濾 (Priority: P1) ✅ 完成

**Goal**: 系統根據使用者角色和部門限制資料存取權限

**Independent Test**: 淡海值班台人員登入後，列表預設顯示淡海部門資料，但可查詢安坑資料（唯讀）。主管可查看所有部門資料。

**完成日期**: 2026-01-29

### 資料模型

- [x] T059 [US3] 建立 User 模型在 backend/src/models/user.py（username, password_hash, role, department, is_active）✅ 2026-01-29

### 後端服務

- [x] T060 [US3] 實作 UserService 在 backend/src/services/user_service.py（CRUD、密碼驗證、角色管理）✅ 2026-01-29
- [x] T061 [US3] 實作 AuthService 在 backend/src/services/auth_service.py（登入、JWT 生成、Token 刷新）✅ 2026-01-29
- [x] T062 [US3] 實作權限檢查服務在 backend/src/services/permission_service.py（檢查使用者是否可編輯指定部門資料）✅ 2026-01-29

### 後端 API 端點

- [x] T063 [US3] 實作認證 API 在 backend/src/api/auth.py（POST /api/auth/login, POST /api/auth/refresh, POST /api/auth/logout）✅ 2026-01-29
- [x] T064 [US3] 實作使用者管理 API 在 backend/src/api/users.py（GET /api/users, POST, PUT, DELETE，僅 Admin 可存取）✅ 2026-01-29
- [x] T065 [US3] 更新員工 API 權限控制在 backend/src/api/employees.py（依角色與部門限制編輯權限）✅ 2026-01-29

### 前端實作

- [x] T066 [P] [US3] 建立登入頁面在 frontend/src/views/Login.vue（使用者名稱、密碼、記住我）✅ 2026-01-29
- [x] T067 [P] [US3] 建立使用者管理頁面在 frontend/src/views/Users.vue（使用者列表、新增、編輯，僅 Admin）✅ 2026-01-29
- [x] T068 [US3] 建立認證 Store 在 frontend/src/stores/auth.js（Pinia state、登入/登出 actions、Token 管理）✅ 2026-01-29
- [x] T069 [US3] 實作 Vue Router 導航守衛在 frontend/src/router/index.js（檢查登入狀態、權限重定向）✅ 2026-01-29
- [x] T070 [US3] 更新員工列表頁面在 frontend/src/views/Employees.vue（部門預設篩選、編輯按鈕權限控制）✅ 2026-01-29

**Checkpoint**: ✅ 權限控制功能完成，不同角色有不同的資料存取權限

---

## Phase 6: User Story 6 - 系統連線狀態監控與憑證驗證 (Priority: P2) ✅ 完成

**Goal**: 桌面應用常駐顯示雲端服務與 Google API 連線狀態，管理員上傳憑證時立即驗證有效性

**Independent Test**: 桌面應用啟動後在狀態列顯示「雲端連線：正常」與「Google API：正常」。管理員上傳淡海的 Google 憑證時，系統立即嘗試連接並回報結果。

**完成日期**: 2026-01-29

### 後端服務

- [x] T071 [P] [US6] 實作連線狀態檢查服務在 backend/src/services/connection_monitor.py（檢查 TiDB、Google Sheets、Google Drive 連線）✅ 2026-01-29
- [x] T072 [P] [US6] 實作 Google API 憑證測試服務在 backend/src/services/google_api_tester.py（測試服務帳戶與 OAuth 憑證）✅ 2026-01-29

### 後端 API 端點

- [x] T073 [US6] 實作連線狀態 API 在 backend/src/api/connection_status.py（GET /api/status/cloud, GET /api/status/google）✅ 2026-01-29

### 本機應用實作

- [x] T074 [US6] 實作連線狀態監控在 desktop_app/src/services/connection_monitor.py（定期檢查雲端 API 與 Google API）✅ 2026-01-29
- [x] T075 [US6] 更新系統托盤程式在 desktop_app/src/tray_app.py（狀態列圖示、連線狀態顯示）✅ 2026-01-29
- [x] T076 [US6] 實作憑證驗證介面在 desktop_app/src/ui/credential_validator.py（顯示驗證結果、錯誤訊息）✅ 2026-01-29

### 前端實作

- [x] T077 [US6] 建立連線狀態元件在 frontend/src/components/common/ConnectionStatus.vue（雲端、本機 API、Google API 狀態顯示）✅ 2026-01-29
- [x] T078 [US6] 更新系統設定頁面在 frontend/src/views/SystemSettings.vue（整合憑證驗證按鈕與即時回饋）✅ 2026-01-29

**Checkpoint**: ✅ 連線狀態監控與憑證驗證功能完成

---

## Phase 7: User Story 4 - Google Sheets 班表自動同步與手動觸發 (Priority: P2) ✅ 完成

**Goal**: 系統每日自動從 Google Sheets 同步班表資料，並提供手動同步功能

**Independent Test**: 系統在凌晨 2:00 自動執行同步任務，從淡海和安坑的 Google Sheets 讀取當月班表並寫入資料庫。管理員可在任何時間點點擊「立即同步」按鈕手動觸發同步。

**完成日期**: 2026-01-29

### 資料模型

- [x] T079 [US4] 建立 Schedule 模型在 backend/src/models/schedule.py（employee_id, department, schedule_date, shift_type 等欄位）✅ 2026-01-29

### 後端服務

- [x] T080 [US4] 實作 Google Sheets 讀取服務在 backend/src/services/google_sheets_reader.py（使用服務帳戶憑證、唯讀權限）✅ 2026-01-29
- [x] T081 [US4] 實作班表解析服務在 backend/src/services/schedule_parser.py（解析分頁資料、員工班別）✅ 2026-01-29
- [x] T082 [US4] 實作班表同步服務在 backend/src/services/schedule_sync_service.py（讀取、解析、寫入資料庫、錯誤處理）✅ 2026-01-29
- [x] T083 [US4] 實作定時任務管理在 backend/src/tasks/scheduler.py（APScheduler 配置、班表同步任務註冊）✅ 2026-01-29

### 後端 API 端點

- [x] T084 [US4] 實作班表查詢 API 在 backend/src/api/schedules.py（GET /api/schedules, 支援日期與部門篩選）✅ 2026-01-29
- [x] T085 [US4] 實作手動同步 API 在 backend/src/api/sync_tasks.py（POST /api/sync/schedule, GET /api/sync/status/{task_id}）✅ 2026-01-29

### 前端實作

- [x] T086 [P] [US4] 建立班表查詢頁面在 frontend/src/views/Schedules.vue（日曆視圖、員工班表）✅ 2026-01-29
- [x] T087 [P] [US4] 建立 Google 服務管理頁面在 frontend/src/views/GoogleServices.vue（手動同步按鈕、同步歷史）✅ 2026-01-29
- [x] T088 [US4] 建立同步進度元件在 frontend/src/components/sync/SyncProgress.vue（即時進度條、已處理/總數、取消按鈕）✅ 2026-01-29
- [x] T089 [US4] 建立同步結果元件在 frontend/src/components/sync/SyncResult.vue（新增/更新/失敗統計）✅ 2026-01-29

**Checkpoint**: ✅ Google Sheets 班表同步功能完成（自動與手動）

---

## Phase 8: User Story 7 - PDF 條碼識別（含部門判斷） (Priority: P2) ✅ 完成

**Goal**: 桌面應用處理 PDF 掃描文件，根據條碼前綴（TH/AK）自動判斷部門並上傳到對應的 Google Drive 資料夾

**Independent Test**: 使用者上傳一個包含多頁的 PDF，條碼為「TH-12345」和「AK-67890」，系統自動切分為兩個檔案並上傳到淡海和安坑的 Drive 資料夾。

**完成日期**: 2026-01-29

### 本機應用服務

- [x] T090 [P] [US7] 實作 PDF 條碼識別服務在 desktop_app/src/services/barcode_reader.py（PyPDF2 + pyzbar）✅ 2026-01-29
- [x] T091 [P] [US7] 實作 PDF 切分服務在 desktop_app/src/services/pdf_splitter.py（依條碼切分多頁 PDF）✅ 2026-01-29
- [x] T092 [US7] 實作部門判斷服務在 desktop_app/src/services/department_detector.py（TH → 淡海、AK → 安坑）✅ 2026-01-29
- [x] T093 [US7] 實作 Google Drive 上傳服務在 desktop_app/src/services/google_drive_uploader.py（使用 OAuth 令牌、部門資料夾 ID）✅ 2026-01-29

### 本機 API 端點

- [x] T094 [US7] 實作 PDF 處理 API 在 desktop_app/src/api/pdf_processor.py（POST /api/pdf/process, 返回處理結果與 Drive 連結）✅ 2026-01-29
- [x] T095 [US7] 實作條碼生成 API 在 desktop_app/src/api/barcode_generator.py（POST /api/barcode/generate, 返回 Base64 圖片）✅ 2026-01-29

### 後端 OAuth 授權流程

- [x] T096 [US7] 實作 OAuth 授權 URL 生成端點在 backend/src/api/google_oauth.py（GET /api/google/auth-url?department=淡海）✅ 2026-01-29
- [x] T097 [US7] 實作 OAuth 回調端點在 backend/src/api/google_oauth.py（GET /api/auth/google/callback, 換取 refresh_token 並加密存儲）✅ 2026-01-29
- [x] T098 [US7] 實作 Access Token 取得端點在 backend/src/api/google_oauth.py（POST /api/google/get-access-token, 刷新令牌）✅ 2026-01-29

### OAuth 回調端點測試 ⭐ **(新增：U1)**

- [x] T098a [P] [US7] 實作 OAuth 回調端點單元測試在 backend/tests/unit/test_google_oauth.py（測試正常授權、拒絕授權 error='access_denied'、無效 code、遺失 code 參數、驗證 refresh_token 加密儲存）✅ 2026-01-29

### 前端實作

- [x] T099 [P] [US7] 建立 PDF 上傳頁面在 frontend/src/views/PdfUpload.vue（檔案拖放、處理進度、結果顯示）✅ 2026-01-29
- [x] T100 [P] [US7] 建立條碼生成頁面在 frontend/src/views/BarcodeGenerator.vue（輸入履歷 ID、選擇部門、下載條碼）✅ 2026-01-29
- [x] T101 [US7] 建立 Google Drive 授權元件在 frontend/src/components/google/DriveAuthorization.vue（授權按鈕、授權狀態顯示）✅ 2026-01-29

**Checkpoint**: ✅ PDF 條碼識別與 Google Drive 上傳功能完成

---

## Phase 9: User Story 5 - 駕駛時數統計與競賽排名 (Priority: P3) ⭐ **(季度制更新 2026-01-29)**

**Goal**: 系統每日同步勤務表資料，每季自動計算駕駛競賽排名

**Independent Test**: 系統每季首日（1/1, 4/1, 7/1, 10/1）凌晨 3:00 計算前一季度駕駛競賽排名，按部門分別排名（淡海前5名、安坑前3名）。

### 資料模型

- [x] T102 [P] [US5] 建立 RouteStandardTime 模型在 backend/src/models/route_standard_time.py（department, route_code, route_name, standard_minutes, is_active）✅ 2026-01-29
- [x] T103 [P] [US5] 建立 DrivingDailyStats 模型在 backend/src/models/driving_daily_stats.py（employee_id, department, record_date, total_minutes, is_holiday_work, incident_count）✅ 2026-01-29
  - **新增欄位**：is_holiday_work: BOOLEAN（是否為 R班出勤，用於 × 2 計算）
- [x] T104 [P] [US5] 建立 DrivingCompetition 模型在 backend/src/models/driving_competition.py（employee_id, competition_year, competition_quarter, department, total_driving_minutes, holiday_work_bonus_minutes, incident_count, final_score, rank_in_department, is_qualified, bonus_amount, is_employed_on_last_day）✅ 2026-01-29
  - **關鍵欄位**：
    - competition_quarter: INTEGER（1-4，季度識別）
    - is_qualified: BOOLEAN（是否符合資格：時數≥300小時 且 季末在職）
    - bonus_amount: INTEGER（獎金金額，依排名：淡海5階/安坑3階）
    - is_employed_on_last_day: BOOLEAN（季度最後一日是否在職）
    - 移除：rank_overall（不再需要全公司排名）

### 後端服務

- [x] T105 [US5] 實作勤務標準時間管理服務在 backend/src/services/route_standard_time_service.py（CRUD 操作、Excel 匯入驗證）✅ 2026-01-29
- [x] T106 [US5] 實作勤務表同步服務在 backend/src/services/duty_sync_service.py（讀取 Google Sheets 勤務表、查詢 route_standard_times、計算駕駛時數）✅ 2026-01-29
- [x] T107 [US5] 實作駕駛時數計算服務在 backend/src/services/driving_stats_calculator.py（每日時數彙總、R班判定、責任事件統計、季度累計）✅ 2026-01-29
  - **功能更新**：
    - R班判定：從 schedules 表查詢 shift_type 含「R」則標記
    - 責任事件統計：從 profiles 表統計 S/R 類別事件（待 US8 整合）
    - 季度累計：提供季度時數查詢方法
- [x] T108 [US5] 實作駕駛競賽排名服務在 backend/src/services/driving_competition_ranker.py（季度積分計算、資格檢查、部門排名、排名限額、獎金分配、在職驗證）✅ 2026-01-29
  - **核心邏輯**：
    1. 資格檢查：季度累計時數 ≥ 300小時 且 季度最後一日 is_resigned = false
    2. 積分計算：final_score = (total_minutes + holiday_work_bonus_minutes) / (1 + incident_count)
    3. 部門排名：依 final_score 降序排列，積分相同時依 employee_id 升序
    4. 排名限額與獎金：
       - 淡海：rank ≤ 5 才獲獎金，金額 = [3600, 3000, 2400, 1800, 1200][rank-1]
       - 安坑：rank ≤ 3 才獲獎金，金額 = [3600, 3000, 2400][rank-1]
- [x] T109 [US5] 更新定時任務在 backend/src/tasks/scheduler.py（勤務表同步維持每日2:30、競賽排名改為季度首日 3:00）✅ 2026-01-29
  - **任務調整**：
    - 勤務表同步：維持每日 02:30（無變更）
    - 競賽排名計算：改為每季首日 1/1, 4/1, 7/1, 10/1 凌晨 03:00
    - Cron 表達式：trigger=CronTrigger(month='1,4,7,10', day=1, hour=3, minute=0)

### 後端 API 端點

- [x] T110 [US5] 實作勤務標準時間 CRUD API 在 backend/src/api/route_standard_time.py（GET/POST/PUT/DELETE /api/routes, 僅 Admin 可編輯）✅ 2026-01-29
- [x] T111 [US5] 實作勤務標準時間 Excel 匯入 API 在 backend/src/api/route_standard_time.py（POST /api/routes/import-excel, 驗證格式與欄位）✅ 2026-01-29
- [x] T112 [US5] 實作駕駛時數查詢 API 在 backend/src/api/driving_stats.py（GET /api/driving/stats, 支援日期與員工篩選）✅ 2026-01-29
- [x] T113 [US5] 實作駕駛競賽排名 API 在 backend/src/api/driving_competition.py（GET /api/driving/competition?year={year}&quarter={quarter}&department={department}）✅ 2026-01-29
  - **參數變更**：month → quarter（1-4）
  - **回應格式新增**：
    - is_qualified（資格狀態）
    - bonus_amount（獎金金額）
    - stats.qualified_count（符合資格人數）
    - stats.bonus_recipients（獲獎人數）

### 前端實作

- [x] T114 [P] [US5] 建立勤務標準時間管理頁面在 frontend/src/views/RouteStandardTimes.vue（僅管理員可見、CRUD 表單、Excel 匯入功能）✅ 2026-01-29
- [x] T115 [P] [US5] 建立駕駛時數查詢頁面在 frontend/src/views/DrivingStats.vue（員工時數統計、季度累計圖表）✅ 2026-01-29
- [x] T116 [P] [US5] 建立駕駛競賽排名頁面在 frontend/src/views/DrivingCompetition.vue（排名榜、積分顯示、部門排名、資格狀態、獎金金額）✅ 2026-01-29
  - **顯示欄位更新**：季度選擇器（year + quarter）、資格標記、獎金金額
- [x] T117 [US5] 建立駕駛時數 Store 在 frontend/src/stores/drivingStats.js（Pinia state、actions、季度參數）✅ 2026-01-29

**Checkpoint**: ✅ 駕駛時數統計與競賽排名功能完成（季度制）2026-01-29

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

## Phase 11: User Story 8 - 司機員事件履歷管理系統 (Priority: P1) ⭐ **(新增 + Gemini Review 優化)**

**Goal**: 值班台人員可記錄和管理司機員的各類事件履歷，包括事件調查、人員訪談、考核加扣分、矯正措施等，並自動產生對應的 Office 文件

**Independent Test**: 值班台人員建立一筆基本履歷後，將其轉換為「人員訪談」類型，系統自動從本地資料庫（schedules 表）查詢該員工事件當天前後的班別資訊，填充資料後在後端產生 Word 文件並嵌入條碼，直接下載到瀏覽器。

**架構優化** ⭐ **(Gemini Review 建議)**:
- ✅ Office 文件生成移至後端（python-docx/openpyxl 可在 Render 運行）
- ✅ 條碼編碼加入版本號（防止同一履歷多次生成時條碼重複）
- ✅ 班表查詢優先使用本地 DB（減少 Google API 呼叫）
- ✅ 移除樂觀鎖定機制（履歷不存在高並發編輯場景）
- ✅ EventInvestigation 增加結構化欄位（支援 Phase 9 駕駛競賽統計）

### 資料模型

- [x] T130 [P] [US8] 建立 Profile 模型在 backend/src/models/profile.py（id, employee_id FK, profile_type ENUM('basic','event_investigation','personnel_interview','corrective_measures','assessment_notice'), event_date, **event_time TIME**, event_location, train_number, **event_title VARCHAR(200)**, event_description, **data_source VARCHAR(100)**, **assessment_item VARCHAR(200)**, **assessment_score INTEGER**, conversion_status ENUM('pending','converted','completed'), file_path, gdrive_link, department, created_at, updated_at）⭐ **Gemini Review 2026-01-30：新增 event_time, event_title, data_source, assessment_item, assessment_score 欄位，讓所有 Profile 類型都能存取考核資訊**
- [x] T131 [P] [US8] 建立 EventInvestigation 模型在 backend/src/models/event_investigation.py（profile_id FK, incident_time, incident_location, witnesses, cause_analysis, process_description, improvement_suggestions, investigator, investigation_date, **has_responsibility BOOLEAN**, **responsibility_ratio INTEGER**, **category ENUM('S','R','W','O','D')**）⭐ **新增統計欄位支援 Phase 9**
- [x] T132 [P] [US8] 建立 PersonnelInterview 模型在 backend/src/models/personnel_interview.py（profile_id FK, hire_date, shift_before_2days, shift_before_1day, shift_event_day, interview_content, interviewer, interview_date, **interview_result_data JSON**, **follow_up_action_data JSON**, **conclusion TEXT**）⭐ **Gemini Review 2026-01-30：新增 JSON 欄位儲存訪談結果勾選(ir_1~ir_7)與後續行動勾選(fa_1~fa_7)，以及結論欄位**
- [x] T133 [P] [US8] 建立 CorrectiveMeasures 模型在 backend/src/models/corrective_measures.py（profile_id FK, event_summary, corrective_actions, responsible_person, completion_deadline, completion_status ENUM('pending','in_progress','completed')）
- [x] T134 [P] [US8] 建立 AssessmentNotice 模型在 backend/src/models/assessment_notice.py（profile_id FK, assessment_type ENUM('加分','扣分'), assessment_item, assessment_score, issue_date, approver）

### 後端服務

- [x] T135 [US8] 實作 ProfileService 在 backend/src/services/profile_service.py（CRUD、類型轉換帶規則檢查、狀態管理、查詢篩選）⭐ **轉換規則：僅允許 basic → 其他類型，已完成履歷不可轉換**
- [x] T136 [US8] 實作班表查詢服務在 backend/src/services/schedule_lookup_service.py（優先查詢本地 schedules 表，若無資料且距今 < 7 天才呼叫 Google Sheets API 並同步回本地）⭐ **Gemini Review 建議優化**
- [x] T137 [US8] 實作 Office 文件生成服務在 backend/src/services/office_document_service.py（使用 python-docx 生成 Word、openpyxl write-only 模式生成 Excel、模板填充、條碼嵌入、返回二進位流）⭐ **改為後端直接生成**
- [x] T138 [US8] 實作條碼編碼工具在 backend/src/utils/barcode_encoder.py（生成格式：`{profile_id}|{type_code}|{YYYYMM}|V{version:02d}`，支援版本號）⭐ **加入版本號**
- [x] T139 [US8] 實作檔案命名工具在 backend/src/utils/file_naming.py（根據履歷類型與資料生成檔案名稱，格式：`類型-YYYYMMDD_車號_地點_姓名.docx`）
- [x] T140 [US8] 準備 Office 文件模板在 backend/src/templates/（personnel_interview.docx, event_investigation.docx, corrective_measures.xlsx, assessment_notice.docx）⭐ **新增任務：模板檔案管理**

### 後端 API 端點

- [x] T141 [US8] 實作履歷 CRUD API 在 backend/src/api/profiles.py（GET /api/profiles, POST, PUT, DELETE, GET /api/profiles/{id}）
- [x] T142 [US8] 實作履歷類型轉換 API 在 backend/src/api/profiles.py（POST /api/profiles/{id}/convert，限制僅 basic 可轉換，轉換時刪除舊子表資料）⭐ **加入轉換規則驗證**
- [x] T143 [US8] 實作 Office 文件生成 API 在 backend/src/api/profiles.py（POST /api/profiles/{id}/generate-document?doc_type=word|excel，返回 StreamingResponse 二進位流）⭐ **改為返回檔案流**
- [x] T144 [US8] 實作班表查詢 API 在 backend/src/api/profiles.py（GET /api/profiles/schedule-lookup?employee_id={id}&date={date}，返回前2天、當天班別）
- [x] T145 [US8] 實作履歷查詢 API 在 backend/src/api/profiles.py（GET /api/profiles/search，支援日期區間、員工姓名、車號、地點、關鍵字篩選）

### 條碼生成服務（後端實作）⭐ **與 Office 文件生成整合**

- [x] T146 [US8] 實作條碼生成服務在 backend/src/services/barcode_service.py（使用 python-barcode + Pillow 生成 Code128 條碼，返回 PNG 圖片 bytes，供 Office 文件生成服務嵌入文件）⭐ **完全雲端化，無需本機 API**

### 前端實作

- [x] T150 [P] [US8] 建立履歷列表頁面在 frontend/src/views/Profiles.vue（表格、搜尋、篩選、類型圖示、狀態標記）✅ 2026-01-30
- [x] T151 [P] [US8] 建立基本履歷新增表單在 frontend/src/components/profiles/BasicProfileForm.vue（事件日期、員工選擇、地點、車號、描述）✅ 2026-01-30
- [x] T152 [P] [US8] 建立履歷類型轉換對話框在 frontend/src/components/profiles/ConversionDialog.vue（選擇目標類型、顯示對應表單、轉換規則提示）⭐ **加入規則驗證提示** ✅ 2026-01-30
- [x] T153 [P] [US8] 建立事件調查表單在 frontend/src/components/profiles/EventInvestigationForm.vue（事故時間、地點、原因、改善建議、**是否歸責選項、責任比例輸入、事件類別選擇**）⭐ **支援 Phase 9 統計** ✅ 2026-01-30
- [x] T154 [P] [US8] 建立人員訪談表單在 frontend/src/components/profiles/PersonnelInterviewForm.vue（自動帶入班別、訪談內容、訪談人員、訪談日期）✅ 2026-01-30
- [x] T155 [P] [US8] 建立矯正措施表單在 frontend/src/components/profiles/CorrectiveMeasuresForm.vue（事件概述、矯正行動、負責人、完成期限、完成狀態）✅ 2026-01-30
- [x] T156 [P] [US8] 建立考核通知表單在 frontend/src/components/profiles/AssessmentNoticeForm.vue（加分/扣分、項目選擇、分數、核發日期、核准人）✅ 2026-01-30
- [x] T157 [US8] 建立履歷 Store 在 frontend/src/stores/profiles.js（Pinia state、actions、履歷列表管理、轉換狀態管理）✅ 2026-01-30
- [x] T158 [US8] 實作文件生成與下載功能在 frontend/src/components/profiles/DocumentDownload.vue（呼叫後端 API、顯示載入狀態、觸發瀏覽器下載、錯誤處理）⭐ **改為直接下載，無需預覽** ✅ 2026-01-30

**Checkpoint**: ✅ 履歷管理系統功能完成，可建立、轉換、查詢履歷並在後端產生 Office 文件直接下載

---

## Phase 12: User Story 9 - 考核系統 V2 升級（累計加重機制） (Priority: P2) ⭐ **(新增)**

**Goal**: 系統支援 2026 年度起的新考核規則，包含累計加重機制、考核標準表管理、雙版本並存（V1/V2）

**Independent Test**: 員工「張三」在 2026 年 1 月發生第 1 次遲到扣 1 分，2 月發生第 2 次遲到扣 1.5 分（累計加重 1.5 倍），3 月發生第 3 次遲到扣 2 分（累計加重 2.0 倍）。系統自動計算累計次數並套用加重公式。

### 資料模型

- [ ] T159 [P] [US9] 建立 AssessmentStandard 模型在 backend/src/models/assessment_standard.py（item_code, item_name, category ENUM('D','W','O','S','R','+M','+A','+B','+C','+R'), base_score, scoring_unit, apply_accumulation, custom_notes, is_active）
- [ ] T160 [P] [US9] 建立 AssessmentRecord 模型在 backend/src/models/assessment_record.py（employee_id FK, assessment_standard_id FK, event_date, base_score, accumulation_multiplier, weighted_score, occurrence_count, assessment_year, notes）

### 後端服務

- [ ] T161 [US9] 實作 AssessmentStandardService 在 backend/src/services/assessment_standard_service.py（CRUD、Excel 匯入、關鍵字搜尋）
- [ ] T162 [US9] 實作累計次數計算服務在 backend/src/services/accumulation_calculator.py（查詢員工年度同類別累計次數）
- [ ] T163 [US9] 實作加重分數計算服務在 backend/src/services/weighted_score_calculator.py（套用公式：實際扣分 = 基本分 × [1 + 係數 × (第N次 - 1)]）
- [ ] T164 [US9] 實作 AssessmentRecordService 在 backend/src/services/assessment_record_service.py（建立記錄、自動計算加重、年度摘要、重算機制）
- [ ] T165 [US9] 實作版本選擇服務在 backend/src/services/assessment_version_selector.py（根據事件日期選擇 V1/V2 規則）
- [ ] T166 [US9] 實作考核記錄重算服務在 backend/src/services/assessment_recalculator.py（刪除或修改記錄後重算所有累計次數）

### 後端 API 端點

- [ ] T167 [US9] 實作考核標準 CRUD API 在 backend/src/api/assessment_standards.py（GET/POST/PUT/DELETE /api/assessment-standards, 僅 Admin 可編輯）
- [ ] T168 [US9] 實作考核標準 Excel 匯入 API 在 backend/src/api/assessment_standards.py（POST /api/assessment-standards/import-excel, 驗證格式）
- [ ] T169 [US9] 實作考核標準搜尋 API 在 backend/src/api/assessment_standards.py（GET /api/assessment-standards/search?keyword={keyword}）
- [ ] T170 [US9] 實作考核記錄 CRUD API 在 backend/src/api/assessment_records.py（GET/POST/PUT/DELETE /api/assessment-records）
- [ ] T171 [US9] 實作員工年度考核摘要 API 在 backend/src/api/assessment_records.py（GET /api/assessment-records/summary?employee_id={id}&year={year}）

### 前端實作

- [ ] T172 [P] [US9] 建立考核標準管理頁面在 frontend/src/views/AssessmentStandards.vue（僅管理員可見、CRUD 表單、Excel 匯入功能）
- [ ] T173 [P] [US9] 建立考核記錄列表頁面在 frontend/src/views/AssessmentRecords.vue（表格、篩選、累計次數顯示）
- [ ] T174 [P] [US9] 建立考核記錄表單元件在 frontend/src/components/assessments/AssessmentRecordForm.vue（選擇項目、自動計算加重分數、顯示公式）
- [ ] T175 [P] [US9] 建立員工年度考核摘要元件在 frontend/src/components/assessments/AssessmentSummary.vue（圖表、分類統計）
- [ ] T176 [US9] 建立考核 Store 在 frontend/src/stores/assessments.js（Pinia state、actions）

**Checkpoint**: 考核系統 V2 功能完成，支援累計加重機制與雙版本並存

---

## Phase 13: User Story 10 - 差勤加分自動處理 (Priority: P2) ⭐ **(新增)**

**Goal**: 系統能夠自動從 Google Sheets 班表讀取資料，逐員工判斷全勤、R班出勤、延長工時三種差勤加分情況，並批次建立對應的履歷記錄

**Independent Test**: 管理員選擇「2026 年 1 月」並點擊「執行差勤加分處理」，系統讀取淡海班表，發現員工「張三」當月全勤、員工「李四」有 2 次 R班出勤、員工「王五」有 1 次延長工時 2 小時，系統自動建立對應的履歷記錄並顯示處理統計。

### 後端服務

- [ ] T177 [P] [US10] 實作全勤判定服務在 backend/src/services/attendance_full_month_detector.py（掃描班表所有儲存格，檢查是否包含「(假)」）
- [ ] T178 [P] [US10] 實作 R班出勤判定服務在 backend/src/services/attendance_r_shift_detector.py（正則匹配 `R/...` 或 `R(國)/...`）
- [ ] T179 [P] [US10] 實作延長工時判定服務在 backend/src/services/attendance_overtime_detector.py（正則匹配 `(+1)`, `(+2)`, `(+3)`, `(+4)`）
- [ ] T180 [US10] 實作差勤加分處理服務在 backend/src/services/attendance_bonus_processor.py（讀取班表、逐員工掃描、批次建立履歷、去重檢查）
- [ ] T181 [US10] 實作複合情況處理服務在 backend/src/services/attendance_composite_handler.py（如 `R/0905G(+2)` 同時建立兩筆履歷）

### 後端 API 端點

- [ ] T182 [US10] 實作差勤加分處理 API 在 backend/src/api/attendance_bonus.py（POST /api/attendance-bonus/process, 參數：year, month, department）
- [ ] T183 [US10] 實作差勤處理結果查詢 API 在 backend/src/api/attendance_bonus.py（GET /api/attendance-bonus/results/{task_id}）

### 前端實作

- [ ] T184 [P] [US10] 建立差勤加分處理頁面在 frontend/src/views/AttendanceBonus.vue（選擇年月與部門、執行按鈕、進度條）
- [ ] T185 [P] [US10] 建立差勤處理結果元件在 frontend/src/components/attendance/BonusProcessResult.vue（統計資訊：全勤 X 筆、R班 Y 筆、延長工時 Z 筆、跳過 N 筆）

**Checkpoint**: 差勤加分自動處理功能完成，可批次建立履歷記錄

---

## Phase 14: User Story 11 - 未結案管理系統 (Priority: P3) ⭐ **(新增)**

**Goal**: 系統提供專門的未結案管理功能，透過查詢 `Profile` 表（`conversion_status = 'converted' AND gdrive_link IS NULL`）列出所有已產生文件但尚未上傳 PDF 到 Google Drive 的履歷，追蹤文件處理進度

**Independent Test**: 值班台人員進入「未結案專區」，看到 5 筆待上傳的事件調查履歷和 3 筆待上傳的人員訪談履歷，選擇其中一筆上傳掃描後的 PDF，系統自動上傳到 Google Drive 並更新 `conversion_status` 為「completed」，履歷從未結案列表中消失。

**注意**: ⚠️ 根據 Gemini Review 建議，已移除 `PendingCase` 資料表，改用 `Profile.conversion_status` + 複合索引 `(conversion_status, department)` 查詢未結案項目，確保資料一致性並遵循 "Single Source of Truth" 原則。

### 後端服務

- [ ] T186 [US11] 實作未結案查詢服務在 backend/src/services/pending_profile_service.py（查詢 `conversion_status = 'converted' AND gdrive_link IS NULL` 的履歷、按類型分組統計、最舊未結案日期計算、本月完成率計算）
- [ ] T187 [US11] 實作 PDF 上傳服務在 backend/src/services/pdf_upload_service.py（委派本機 API 上傳到 Google Drive、上傳成功後更新 Profile.gdrive_link 和 conversion_status）

### 後端 API 端點

- [ ] T188 [US11] 實作未結案列表 API 在 backend/src/api/profiles.py（GET /api/profiles/pending, 查詢條件：conversion_status='converted' AND gdrive_link IS NULL，支援類型與部門篩選，使用複合索引提升效能）
- [ ] T189 [US11] 實作未結案統計 API 在 backend/src/api/profiles.py（GET /api/profiles/pending/statistics, 統計各類型待處理數量、最舊未結案日期、本月完成率）
- [ ] T190 [US11] 實作 PDF 上傳 API 在 backend/src/api/profiles.py（POST /api/profiles/{id}/upload-pdf, 接收檔案並委派本機 API 上傳，成功後更新 conversion_status='completed'）

### 本機 API 端點（複用 Phase 8 服務）⭐

- [ ] T191 [US11] 擴充 Google Drive 上傳服務在 desktop_app/src/services/google_drive_uploader.py（複用 T093 服務，新增依履歷類型與日期自動分類資料夾的邏輯，設定權限為「僅網域內可檢視」）
- ~~T192 已合併至 T191~~（不需獨立 API 端點，直接使用 T093 的現有端點）

### 前端實作

- [ ] T193 [P] [US11] 建立未結案專區頁面在 frontend/src/views/PendingProfiles.vue（查詢 conversion_status='converted' 的履歷、類型分類、統計資訊）
- [ ] T194 [P] [US11] 建立 PDF 上傳元件在 frontend/src/components/profiles/PdfUploadDialog.vue（檔案選擇、上傳進度、錯誤處理）
- [ ] T195 [US11] 建立未結案統計元件在 frontend/src/components/profiles/PendingStatistics.vue（各類型待處理數量、最舊未結案日期、本月完成率）

**Checkpoint**: 未結案管理系統功能完成，可追蹤文件處理進度

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
- **User Stories 8-11 (Phase 11-14)** ⭐ **(新增)**: 全部依賴 Foundational 完成
  - US8, US9, US10, US11 可並行開發（不同檔案）
  - 或按建議順序執行：US8 → US5 → US9 → US10 → US11

### User Story Dependencies

- **US1 (P0)**: 可在 Foundational 後開始 - 無其他用戶故事依賴
- **US2 (P1)**: 可在 Foundational 後開始 - 無其他用戶故事依賴
- **US3 (P1)**: 可在 Foundational 後開始 - 建議在 US2 後（需要 User 模型）
- **US4 (P2)**: 可在 Foundational 後開始 - 無其他用戶故事依賴
- **US5 (P3)**: 可在 Foundational 後開始 - 建議在 US4 後（共用 Google Sheets 服務）
- **US6 (P2)**: 可在 Foundational 後開始 - 無其他用戶故事依賴
- **US7 (P2)**: 可在 Foundational 後開始 - 建議在 US1 後（需要 OAuth 配置）
- **US8 (P1)** ⭐: 可在 Foundational 後開始 - 建議在 US4 後（需要 Google Sheets 班表服務、Office 文件生成服務）
- **US9 (P2)** ⭐: 可在 Foundational 後開始 - 建議在 US8 後（考核記錄與履歷整合）
- **US10 (P2)** ⭐: 可在 Foundational 後開始 - 建議在 US8 與 US9 後（依賴履歷系統與考核標準）
- **US11 (P3)** ⭐: 可在 Foundational 後開始 - 建議在 US8 後（依賴履歷系統與 PDF 上傳功能）

### Within Each User Story

- 資料模型 → 服務層 → API 端點 → 前端實作
- 標記 [P] 的任務可並行執行（不同檔案）
- 完成一個故事後再進入下一個優先級

### Parallel Opportunities

**原有功能**:
- **Setup 階段**: T002, T003, T004, T005, T006, T007, T010, T011 可並行
- **Foundational 階段**: 多數任務可並行（不同檔案）
- **US1**: T034, T035 可並行（不同模型）
- **US2**: T043, T044 可並行；T053, T054, T055 可並行
- **US4**: T086, T087 可並行
- **US5**: T102, T103 可並行；T110, T111 可並行
- **US7**: T090, T091 可並行；T099, T100 可並行
- **Polish**: T113, T114, T115, T116, T120, T121, T122 可並行

**新增功能** ⭐:
- **US8**: T130-T134 可並行（5 個資料模型）；T146, T147, T148 可並行；T150-T156 可並行（7 個前端表單）
- **US9**: T159, T160 可並行（2 個資料模型）；T172-T175 可並行（4 個前端元件）
- **US10**: T177, T178, T179 可並行（3 個判定服務）；T184, T185 可並行（2 個前端元件）
- **US11**: T195, T196, T197 可並行（3 個前端元件）

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

### Incremental Delivery（原有功能）

1. Setup + Foundational → 基礎完成
2. 加入 US1 → 測試獨立 → 部署（系統可配置）
3. 加入 US2 → 測試獨立 → 部署（可管理員工）
4. 加入 US3 → 測試獨立 → 部署（權限控制完成，MVP！）
5. 加入 US4 → 測試獨立 → 部署（班表同步）
6. 加入 US6 → 測試獨立 → 部署（連線監控）
7. 加入 US7 → 測試獨立 → 部署（PDF 處理）
8. 加入 US5 → 測試獨立 → 部署（駕駛競賽，完整功能）

### Progressive Integration（新增功能 - 建議順序）⭐

**參考**: `docs/architecture_comparison_and_integration_plan.md` - 5-6 週漸進式整合計畫

1. **Week 1-2**: Phase 11（US8）履歷管理系統
   - 核心資料模型與 CRUD
   - Office 文件生成與條碼系統
   - 班表查詢整合
   - **Milestone**: 可建立、轉換、查詢履歷並產生文件

2. **Week 3**: Phase 9（US5）駕駛時數統計增強
   - 整合履歷系統的責任事件懲罰係數
   - 勤務表同步與時數計算
   - **Milestone**: 駕駛競賽排名完整功能

3. **Week 4**: Phase 12（US9）考核系統 V2
   - 考核標準表管理
   - 累計加重機制實作
   - 雙版本並存（V1/V2）
   - **Milestone**: 2026 年起考核規則完整運作

4. **Week 5**: Phase 13（US10）差勤加分自動處理
   - 全勤/R班/延長工時判定服務
   - 批次建立履歷記錄
   - **Milestone**: 每月差勤加分自動化

5. **Week 6**: Phase 14（US11）未結案管理
   - 未結案列表與統計
   - PDF 上傳與 Google Drive 整合
   - **Milestone**: 完整的履歷追蹤流程

6. **Week 6+**: Phase 10（Polish）最終優化
   - 跨模組整合測試
   - 效能優化與安全審查
   - 完整文件與部署

### Parallel Team Strategy

若有多位開發者：

**階段 1: 基礎建設**
1. 團隊共同完成 Setup + Foundational

**階段 2: MVP 開發（原有功能）**
2. Foundational 完成後：
   - **開發者 A**: US1（系統設定）
   - **開發者 B**: US2（員工管理）
   - **開發者 C**: US3（權限控制）前期準備
3. MVP 完成後：
   - **開發者 A**: US4（班表同步）
   - **開發者 B**: US6（連線監控）
   - **開發者 C**: US7（PDF 處理）
4. 共同完成 US5（駕駛競賽）

**階段 3: 履歷系統整合（新增功能）⭐**
5. Phase 11（US8）履歷管理系統：
   - **開發者 A**: 資料模型 + 後端服務（T130-T140）
   - **開發者 B**: 後端 API + 本機 API（T141-T149）
   - **開發者 C**: 前端實作（T150-T158）
6. Phase 12（US9）考核系統 V2：
   - **開發者 A**: 資料模型 + 累計加重邏輯（T159-T166）
   - **開發者 B**: 後端 API（T167-T171）
   - **開發者 C**: 前端實作（T172-T176）
7. 並行開發：
   - **開發者 A**: Phase 13（US10）差勤加分自動處理
   - **開發者 B**: Phase 14（US11）未結案管理
   - **開發者 C**: Phase 9（US5）駕駛時數統計增強

**階段 4: 最終整合**
8. 團隊共同完成 Phase 10（Polish）

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

- **總任務數**: 189 個任務（原 131 個 + 新增 User Stories 8-11 共 66 個 - Gemini Review 優化移除 8 個）
- **已完成任務**: 103 個（Phase 1: 11 個 + Phase 2: 24 個 + Phase 3: 9 個 + Phase 4: 16 個 + Phase 5: 12 個 + Phase 6: 8 個 + Phase 7: 11 個 + Phase 8: 12 個 + Phase 9: 0 個）
- **進度**: 54.5%
- **用戶故事數**: 11 個（US1-US7 原有 + US8-US11 新增，對應 spec.md 的 P0-P3 優先級）
- **可並行任務**: 約 45% 的任務標記為 [P]，可並行執行
- **建議 MVP 範圍**: Phase 1-5（Setup + Foundational + US1 + US2 + US3）
- **駕駛競賽模組**: PC-001 已釐清，Phase 9 任務可立即執行
- **測試覆蓋**: 新增憑證驗證測試（G1: T037a, T037b）與 OAuth 回調測試（U1: T098a）
- **履歷管理模組** ⭐: Phase 11（US8）包含 22 個任務（Gemini Review 優化後），**完全雲端化**（Office 文件生成與條碼生成皆在後端）
- **考核系統 V2** ⭐: Phase 12（US9）包含 18 個任務，實作累計加重機制
- **差勤加分自動化** ⭐: Phase 13（US10）包含 9 個任務，自動判定全勤、R班、延長工時
- **未結案管理** ⭐: Phase 14（US11）包含 6 個任務（Gemini Review 優化後，複用 Phase 8 Google Drive 服務），透過 Profile.conversion_status 追蹤文件處理進度
- **完整功能交付**: 全部 14 個階段（包含所有用戶故事與優化）

### Gemini Code Review 架構優化 ✅ (2026-01-30)

**Phase 11 (US8) 優化**:
1. ✅ **Office 文件生成移至後端**（python-docx/openpyxl 可在 Render 免費版運行，每天 < 10 份文件無記憶體壓力）
2. ✅ **條碼生成移至後端**（python-barcode + Pillow，套件大小僅 2-3 MB，對 Render 無影響）
3. ✅ **條碼編碼加入版本號**（格式：`{profile_id}|{type_code}|{YYYYMM}|V{version}`，防止重複）
4. ✅ **班表查詢優先使用本地 DB**（減少 Google API 呼叫，提升效能）
5. ✅ **移除樂觀鎖定機制**（履歷不存在高並發編輯場景，簡化架構）
6. ✅ **EventInvestigation 增加統計欄位**（has_responsibility、category、responsibility_ratio，支援 Phase 9 駕駛競賽）
7. ✅ **履歷轉換規則明確化**（僅允許 basic → 其他類型，防止資料遺失）

**Phase 14 (US11) 優化**:
8. ✅ **移除 PendingCase 資料表**（改用 Profile.conversion_status 查詢，遵循 Single Source of Truth 原則）

**優化成果**:
- **移除/合併冗餘任務 8 個**：
  - T140（樂觀鎖定服務）
  - T147-T149（本機 API Office 生成 3 個任務）
  - T192（本機 PDF 上傳 API，合併至 T191）
  - T146-ALT（本機條碼生成選項）
  - 未建立的 PendingCase 資料表與相關任務（Phase 14 優化）
- **完全雲端化**：無需桌面應用即可生成文件與條碼，Web/手機端功能完整
- **簡化部署**：僅需 Render + TiDB + GitHub Pages，桌面應用僅用於 PDF 掃描識別（Phase 8）與 Drive 上傳
- **提升效能**：本地 DB 優先查詢班表資料，減少 Google Sheets API 呼叫
- **資料一致性**：單一資料來源（Profile 表），避免同步問題

**技術評估依據**:
- Render 免費版限制：512 MB RAM，15 分鐘無活動休眠，30 秒超時
- 單份文件生成：5-15 MB 記憶體，0.3-1 秒 CPU 時間
- 使用情境：每天 < 10 份文件，無批次需求
- 結論：✅ Render 免費版完全足夠

### Gemini 模板欄位驗證修正 ✅ (2026-01-30)

**發現的問題與修正**:

1. **Profile 主表擴充** (T130 更新):
   - 新增 `event_time` (Time)：解決考核通知單需要時間的問題
   - 新增 `event_title` (VARCHAR 200)：解決考核通知單需要標題的問題
   - 新增 `data_source` (VARCHAR 100)：統一存放資料來源/查核來源
   - 新增 `assessment_item` (VARCHAR 200)：所有類型的 Profile 都能存取考核項目
   - 新增 `assessment_score` (INTEGER)：所有類型的 Profile 都能存取考核分數
   - **設計理由**：遵循「一事一檔」原則，所有 Profile 類型都可能需要考核資訊

2. **PersonnelInterview 模型補完** (T132 更新):
   - 新增 `interview_result_data` (JSON)：儲存訪談結果勾選 (ir_1~ir_7, ir_other_text)
   - 新增 `follow_up_action_data` (JSON)：儲存後續行動勾選 (fa_1~fa_7, fa_other_text)
   - 新增 `conclusion` (TEXT)：結論欄位
   - **設計理由**：使用 JSON 欄位保持彈性，避免新增 16+ 個 Boolean 欄位

3. **欄位映射邏輯標準化**:
   - 建立完整的佔位符與資料庫欄位映射表
   - `{incident_cause}` 映射邏輯：優先 `EventInvestigation.cause_analysis`，否則 `Profile.event_description`
   - 勾選框轉換邏輯：Boolean → "V" / ""

**修正檔案**:
- `specs/001-system-architecture/tasks.md`：T130, T132 定義更新
- `backend/src/templates/README.md`：新增欄位映射邏輯章節 (v2.1)

### 進度更新記錄

| 日期 | 完成任務 | 累計完成 | 進度 | 備註 |
|------|----------|----------|------|------|
| 2026-01-28 | T001-T014, T023, T026 | 16 | 12.2% | Phase 1 完成 |
| 2026-01-29 | T015-T033, T037a | 34 | 26.0% | Phase 2 基本完成 |
| 2026-01-28 | T037b (憑證驗證整合測試) | 35 | 26.7% | Phase 2 完成 |
| 2026-01-29 | 新增 User Stories 8-11 | 35 | 17.6% | 新增 68 個任務（T130-T197），總任務數從 131 增至 199 |
| 2026-01-29 | T034-T042 (Phase 3) | 44 | 22.1% | Phase 3 (US1 系統設定) 完成 |
| 2026-01-29 | T043-T058 (Phase 4) | 60 | 30.2% | Phase 4 (US2 員工管理) 完成 |
| 2026-01-29 | T059-T070 (Phase 5) | 72 | 36.2% | Phase 5 (US3 權限控制) 完成，MVP 完成 |
| 2026-01-29 | T071-T078 (Phase 6) | 80 | 40.6% | Phase 6 (US6 連線狀態監控) 完成 |
| 2026-01-29 | T079-T089 (Phase 7) | 91 | 46.2% | Phase 7 (US4 班表同步) 完成 |
| 2026-01-29 | T090-T101 (Phase 8) | 103 | 52.3% | Phase 8 (US7 PDF條碼識別) 完成 |

---

**任務清單已生成完成！**

檔案位置：`specs/001-system-architecture/tasks.md`

按照此任務清單執行，可確保每個用戶故事獨立實作、獨立測試、漸進式交付價值。
