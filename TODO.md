# 待辦事項 (TODO)

**狀態**: 專案開發階段已完成 (Phase 0 - Phase 14)
**最後更新**: 2026-01-31

---

## 🚀 上線前準備 (Deployment Readiness)

### 驗證與測試
- [ ] **完整系統測試 (End-to-End Testing)**
    - [ ] 測試從「Google Sheets 班表同步」到「差勤加分計算」的完整流程。
    - [ ] 測試「建立履歷」→「觸發考核」→「產生責任判定」→「影響總分」的連動流程。
    - [ ] 測試「PDF 上傳」至 Google Drive 的實際連線。
- [ ] **資料遷移 (Data Migration)**
    - [ ] 執行 `analyze_old_db.py` 確認舊資料格式（若有）。
    - [ ] 準備正式環境的 `initial_data` (員工名單、部門設定)。

### 部署配置
- [ ] **Render (Backend)**
    - [ ] 確認環境變數 (Secrets) 皆已在 Render Dashboard 設定。
    - [ ] 確認 `render.yaml` 配置正確。
- [ ] **GitHub Pages (Frontend)**
    - [ ] 確認 GitHub Actions (`ci.yml`) 部署流程順暢。
- [ ] **Client (Local API)**
    - [ ] 測試 PyInstaller 打包流程 (`pyinstaller desktop_app/src/main.py`)。
    - [ ] 在目標 Windows 環境測試執行檔。

---

## 🔧 長期優化項目 (Technical Debt & Optimization)

這些項目不影響上線功能，但建議在維護階段處理。

| 優先級 | 項目 | 說明 |
|:---:|:---|:---|
| 🟡 中 | **前端 Token 安全性** | 目前 Access Token 存於 Pinia/LocalStorage，建議改為 HttpOnly Cookie 或實作 Silent Refresh。 |
| 🟡 中 | **Content Security Policy** | 實作 CSP header 以增強 XSS 防護。 |
| 🟡 中 | **資料庫備份自動化** | TiDB Serverless 免費版無自動備份，需撰寫腳本定期透過 API 或 mysqldump 匯出。 |
| 🔵 低 | **JWT 套件升級** | 考慮將 `python-jose` 遷移至 `PyJWT` (目前功能正常，非急迫)。 |
| 🔵 低 | **前端效能優化** | 針對 `AssessmentRecords` 等大資料表格實作虛擬捲動 (Virtual Scrolling)。 |

---

## ✅ 已完成項目 (Completed)

> 僅列出主要模組，詳細清單請見 `PROGRESS.md`

### Phase 14: 未結案管理
- [x] 未結案列表 API 與前端頁面
- [x] Local API PDF 上傳功能
- [x] Google Drive 檔案連結整合

### Phase 13: 差勤加分
- [x] Google Sheets 班表分析器
- [x] 加分規則 (+M, +A) 自動判定引擎
- [x] 差勤結果預覽與執行 API

### Phase 12: 考核系統 (2026 新制)
- [x] 考核標準 (AssessmentStandard) 管理
- [x] 考核記錄 (AssessmentRecord) 與責任判定 (FaultResponsibility)
- [x] 累計加重邏輯與年度重置服務
- [x] 履歷日期變更連動重算機制 (P1 Fix)

### Phase 11: 事件履歷
- [x] 履歷 CRUD 與四種子表單
- [x] 履歷狀態流轉控制

### Phase 9: 駕駛競賽
- [x] 競賽積分公式實作
- [x] 排名查詢 API

### Phase 0-8: 基礎功能
- [x] 認證、授權、員工管理、系統設定、Google 整合、連線監控