# Implementation Plan: Phase 0 - 專案初始結構建立

**Feature**: 001-system-architecture | **Date**: 2026-01-28
**Branch**: `main` (Phase 0 為基礎架構)
**Spec**: `specs/001-system-architecture/spec.md`

## Summary

建立司機員管理系統的三層混合架構初始專案結構：
1. **前端網頁應用**：Vue.js 3 專案（GitHub Pages 部署）
2. **雲端後端 API**：FastAPI 專案（Render 部署 + TiDB 連接）
3. **本機桌面應用 API**：FastAPI 本機服務（檔案處理功能）

**關鍵目標**：
- 建立完整的資料夾結構與設定檔
- 實作基礎資料模型（Employee, User, SystemSetting）
- 設定 TiDB 連線池與環境變數管理
- 實作使用者認證中間件（JWT）
- 設定 CORS 允許跨域請求（GitHub Pages → 本機 API）
- 完成前端基礎架構（Vue Router、Pinia、Axios）
- 部署雲端 API 到 Render 並設定 UptimeRobot

---

## Technical Context

**Language/Version**:
- 前端：JavaScript ES6+ / Vue.js 3.4+
- 後端：Python 3.11+

**Primary Dependencies**:
- 前端：Vue 3, Vue Router 4, Pinia, Axios, Element Plus
- 雲端後端：FastAPI 0.109+, SQLAlchemy 2.0+, pymysql, python-jose (JWT), bcrypt
- 本機後端：FastAPI, python-docx, PyPDF2, python-barcode, google-api-python-client

**Storage**:
- TiDB MySQL 8.0（雲端共享資料庫）
- 本機無資料庫需求（僅檔案處理）

**Testing**:
- 前端：Vitest（單元測試）
- 後端：pytest（單元測試 + 整合測試）

**Target Platform**:
- 前端：現代瀏覽器（Chrome、Edge、Firefox）
- 雲端後端：Linux (Render 容器)
- 本機後端：Windows 10/11（桌面應用打包成 .exe）

**Project Type**: Web + Desktop Hybrid（三層架構）

**Performance Goals**:
- 前端首次載入 < 3 秒
- API 響應時間 < 1 秒（資料 CRUD）
- 本機 API 檔案處理 < 3 秒

**Constraints**:
- TiDB 免費版 5GB 儲存限制
- Render 免費版 512MB RAM 限制
- 本機 API 僅處理檔案操作，不存取資料庫

**Scale/Scope**:
- 預計使用者：< 10 人同時在線
- 資料量：約 2000 筆履歷/年
- 部門數：2（淡海、安坑）硬編碼

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 雙部門架構原則
- **符合性**：資料模型包含 `department` ENUM('淡海', '安坑')，系統設定支援部門級配置
- **實作方式**：SystemSetting 表包含 `department` 欄位，前端依使用者部門過濾

### 權限分離原則 (NON-NEGOTIABLE)
- **符合性**：User 表包含 `role` ENUM('admin', 'staff', 'manager')
- **實作方式**：FastAPI 中間件檢查 JWT payload 的 `role` 與 `department`

### 混合架構原則
- **符合性**：三層架構符合憲章「本機處理 PDF、雲端處理資料」原則
- **變更點**：從「PyQt6 桌面應用」改為「GitHub Pages 網頁 + 本機 API」
- **理由**：提升跨平台性與維護性，核心功能無需桌面應用即可使用

### Constitution 需更新
**Action Required**: 憲章 IV. 混合架構原則需更新，反映新的三層架構：
- 移除「雙模式顯示（QWebEngineView / Chrome）」描述
- 新增「容錯設計：核心功能獨立於本機應用」原則

---

## Phase 0: Research & Unknowns

詳細研究內容請參閱 `research.md`，包含以下關鍵技術決策：

1. Vue.js 3 + GitHub Pages 部署最佳實踐
2. FastAPI CORS 設定（本機 API 跨域請求）
3. TiDB 連線池最佳化
4. PyInstaller 打包本機 API + 托盤程式
5. JWT Token 儲存策略（前端）

---

## Next Steps

完成本計畫後的下一階段工作：

### Phase 1: 員工管理模組完整實作
- 員工調動記錄功能
- 批次匯入/匯出功能
- 前端表單驗證與使用者體驗優化

### Phase 2: Google 服務整合
- 系統設定介面（部門配置）
- Google Sheets 同步模組
- 定時任務設定（APScheduler）

### Phase 3: 本機 API 檔案處理功能
- Word 文件生成端點
- PDF 掃描與切分
- 條碼生成
- Google Drive 上傳

---

**Plan Ready for Review**

此計畫涵蓋 Phase 0 的完整實作步驟。
詳細的實作路線圖（Implementation Roadmap）與驗證計畫（Verification Plan）
請參閱 research.md 文件與專案審查報告（REVIEW.md）。

預計完成時間：**10-14 天**
