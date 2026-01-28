# 專案審查報告：Phase 0 完成度評估

**審查日期**: 2026-01-28
**審查範圍**: Phase 0 (研究與技術選型)
**審查者**: Claude Sonnet 4.5

---

## 執行摘要

**總體評分**: ⭐⭐⭐⭐☆ (4/5)

Phase 0 技術選型研究已完成，研究文件（research.md）詳細記錄了 5 個關鍵技術決策。前端專案結構已初始化，但尚未完成實作。整體方向正確，但存在一些需要關注的風險點。

**關鍵發現**:
- ✅ 技術選型合理且有充分研究支持
- ✅ 研究文件結構清晰，包含決策理由與替代方案
- ⚠️ 架構變更（從桌面應用改為網頁應用）需更新憲章
- ⚠️ 部分高風險點（如 PyInstaller 打包）需提前驗證
- ❌ 缺少 Phase 1 必要文件（data-model.md, contracts/, quickstart.md）

---

## 1. 憲章符合性檢查

### ✅ 完全符合的原則

#### I. 雙部門架構原則
**符合度**: 100%

- ✅ spec.md 明確定義雙部門架構（淡海、安坑）
- ✅ 資料模型計畫包含 `department` ENUM 欄位
- ✅ 系統設定支援部門級配置（SystemSetting 表）
- ✅ 前端設計包含部門篩選功能

**證據**:
```markdown
# spec.md Line 89-92
職責：
- ✅ 資料庫 CRUD 操作（員工、履歷、駕駛時數）
- ✅ 使用者認證與授權（JWT Token）
- ✅ 權限控制中間件（Admin / Staff / Manager）
```

---

#### II. 權限分離原則 (NON-NEGOTIABLE)
**符合度**: 100%

- ✅ spec.md 定義三種角色（Admin, Staff, Manager）
- ✅ JWT 認證計畫包含角色檢查
- ✅ 前端路由守衛檢查 `requiresAdmin` meta
- ✅ 工具函式包含權限檢查（`canEditDepartment`, `hasRole`）

**證據**:
```javascript
// frontend/src/router/index.js
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAdmin && authStore.user?.role !== 'admin') {
    next({ name: 'dashboard' })
  }
})
```

---

#### III. 資料來源多樣性
**符合度**: 95%

- ✅ spec.md 涵蓋所有資料來源（Google Sheets、Drive、TiDB）
- ✅ 雲端 API 計畫包含 Google Sheets 同步功能
- ⚠️ 缺少詳細的 Google API 憑證管理設計

**建議**: Phase 1 需補充 Google API 服務帳戶配置流程

---

### ⚠️ 部分符合的原則

#### IV. 混合架構原則
**符合度**: 70% - **需要憲章修訂**

**問題點**:
憲章描述：「雙模式顯示：內嵌瀏覽器（QWebEngineView）或開啟 Chrome」
實際設計：「GitHub Pages 網頁應用 + 本機 FastAPI 桌面應用」

**架構變更說明**:
| 憲章描述 | 實際設計 | 理由 |
|---------|---------|------|
| PyQt6 桌面應用（QWebEngineView） | Vue.js 網頁應用（GitHub Pages） | 提升跨平台性與維護性 |
| 桌面應用為主介面 | 網頁應用為主介面 | 核心功能無需本機應用即可運行 |
| 雙模式顯示（內嵌/外部瀏覽器） | 單一網頁模式（容錯設計） | 簡化使用者體驗 |

**建議措施**:
1. **立即更新憲章** - 將 IV. 混合架構原則改為：
   ```markdown
   ### IV. 混合架構原則（修訂版）
   系統採用三層架構：
   - **前端網頁應用**：GitHub Pages 部署，所有使用者的主要介面
   - **雲端 API**：Render FastAPI，處理資料 CRUD 與業務邏輯
   - **本機桌面應用 API**：FastAPI localhost 服務，處理檔案生成與 Google Drive 上傳
   - **容錯設計**：核心功能（資料瀏覽、編輯、報表）完全運行於網頁端，本機應用不可用時給予提示
   ```

2. **記錄例外理由** - 在憲章中新增「修訂記錄」章節

---

#### V. 歷史資料完整性
**符合度**: 100%

- ✅ spec.md 包含 EmployeeTransfer 表設計（調動記錄）
- ✅ Employee 表包含 `is_resigned` 欄位（軟刪除）
- ✅ 無硬刪除設計

---

#### VI. 自動化優先
**符合度**: 90%

- ✅ spec.md 包含 APScheduler 定時任務設計
- ✅ 員工編號自動解析入職年月（`parseHireYearMonth` 工具函式）
- ⚠️ 缺少定時任務的詳細配置（執行時間、失敗重試機制）

**建議**: Phase 1 需補充定時任務設計文件

---

## 2. 技術選型合理性評估

### 2.1 前端技術棧：Vue.js 3 + GitHub Pages

**評分**: ⭐⭐⭐⭐⭐ (5/5)

**優點**:
- ✅ Vue.js 3 學習曲線平緩，適合快速開發
- ✅ GitHub Pages 免費且可靠，自動部署便利
- ✅ Element Plus UI 框架成熟，中文文檔完善
- ✅ Pinia 狀態管理輕量且易用

**風險點**:
- ⚠️ **SPA 路由問題已妥善處理** - research.md 提供詳細的 404.html 重定向方案
- ⚠️ **跨域請求已考慮** - CORS 配置清晰

**驗證建議**:
1. 優先測試 GitHub Pages 部署流程（避免後期發現問題）
2. 測試 404.html 重定向是否正常運作

---

### 2.2 雲端後端：FastAPI + TiDB + Render

**評分**: ⭐⭐⭐⭐☆ (4/5)

**優點**:
- ✅ FastAPI 效能優異，自動生成 OpenAPI 文檔
- ✅ TiDB Serverless 相容 MySQL，免費版足夠使用
- ✅ Render 部署簡單，免費版適合內部系統

**風險點**:
- ⚠️ **TiDB 連線池參數合理** - research.md 的 `pool_size=5, max_overflow=10` 符合 Render 512MB RAM 限制
- ⚠️ **Render 冷啟動問題** - 已規劃 UptimeRobot 保持喚醒
- ⚠️ **資料庫備份策略缺失** - TiDB Serverless 免費版不提供自動備份

**改善建議**:
1. **實作定期資料匯出功能** - 每週自動將資料匯出為 SQL 備份檔案
2. **監控 TiDB 儲存用量** - 設定警告閾值（例如超過 4GB）

---

### 2.3 本機 API：FastAPI + PyInstaller 打包

**評分**: ⭐⭐⭐☆☆ (3/5) - **高風險項目**

**優點**:
- ✅ FastAPI 統一技術棧，降低學習成本
- ✅ PyInstaller 打包為單一可執行檔，使用者友善

**風險點**:
- 🔴 **PyInstaller 打包失敗率高** - FastAPI 依賴複雜，容易遺漏模組
- 🔴 **打包後檔案過大** - 預估 50-100MB（包含 Python 執行環境）
- ⚠️ **uvicorn 隱藏依賴問題** - research.md 已列出 `hiddenimports`，但仍需驗證

**建議措施**:
1. **Phase 1 提前驗證打包** - 建立最小可行 FastAPI 專案並測試打包
2. **備用方案** - 若 PyInstaller 失敗，考慮使用 Nuitka 或提供 Python 虛擬環境安裝包
3. **優化打包大小** - 使用 `--exclude-module` 排除不必要的依賴（如 PIL、numpy）

---

### 2.4 JWT Token 儲存策略：localStorage

**評分**: ⭐⭐⭐⭐☆ (4/5)

**優點**:
- ✅ 實作簡單，適合 SPA 架構
- ✅ 短期 Token (1 小時) 降低安全風險
- ✅ Axios interceptor 自動附加 Token

**風險點**:
- ⚠️ **XSS 攻擊風險** - localStorage 可被 JavaScript 讀取
- ⚠️ **缺少 Content Security Policy (CSP)** - research.md 提到但未實作

**改善建議**:
1. **實作 CSP Header** - 在 `index.html` 加入 `<meta>` tag 或透過 Render 設定 HTTP Header
   ```html
   <meta http-equiv="Content-Security-Policy"
         content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
   ```

2. **考慮實作 Refresh Token** - 提升使用者體驗（避免頻繁登入）

---

## 3. 架構完整性檢查

### 3.1 前端架構

**已完成**:
- ✅ Vue Router 配置（路由守衛）
- ✅ Pinia stores（auth, employee, system）
- ✅ Axios 服務層（cloudApi, localApi）
- ✅ 工具函式（auth 權限檢查、validators 表單驗證）

**缺失項目**:
- ❌ **View 元件未建立** - LoginView, DashboardView, EmployeeListView, SystemSettingsView
- ❌ **Layout 元件未建立** - 導航列、側邊欄
- ❌ **Common 元件未建立** - 按鈕、表單、對話框
- ❌ **App.vue 未更新** - 仍為 Vite 預設範本

**建議**: Phase 2 需完成前端頁面開發

---

### 3.2 後端架構

**已規劃但未實作**:
- ⏳ backend-cloud/ 目錄結構（完整規劃於 plan.md）
- ⏳ backend-local/ 目錄結構（完整規劃於 plan.md）
- ⏳ 資料模型（Employee, User, SystemSetting）
- ⏳ API 端點（認證、員工管理、系統設定）

**建議**: 按照 plan.md 的 Implementation Roadmap 逐步執行

---

### 3.3 文件完整性

| 文件 | 狀態 | 重要性 | 備註 |
|------|------|--------|------|
| spec.md | ✅ 完成 | 高 | 1089 行，內容詳盡 |
| research.md | ✅ 完成 | 高 | 480 行，技術選型完整 |
| plan.md | ❌ 未保存 | 高 | 需從對話記錄提取 |
| data-model.md | ❌ 缺失 | 高 | Phase 1 必要文件 |
| contracts/cloud-api.yaml | ❌ 缺失 | 高 | Phase 1 必要文件 |
| contracts/local-api.yaml | ❌ 缺失 | 中 | Phase 1 必要文件 |
| quickstart.md | ❌ 缺失 | 中 | 開發環境設定指南 |
| tasks.md | ❌ 缺失 | 高 | speckit 流程必需 |

---

## 4. 風險識別與緩解措施

### 🔴 高風險項目

#### 風險 1: PyInstaller 打包失敗
**影響**: 本機 API 無法部署，檔案處理功能不可用
**機率**: 60%
**緩解措施**:
1. Phase 1 提前驗證打包（最小可行專案）
2. 準備備用方案：Nuitka 編譯或 Python 虛擬環境
3. 實作容錯設計：前端檢測本機 API 不可用時禁用功能

---

#### 風險 2: GitHub Pages SPA 路由失效
**影響**: 直接存取 `/employees` 導致 404 錯誤
**機率**: 30%
**緩解措施**:
1. 依照 research.md 的 404.html 重定向方案
2. 部署後立即測試所有路由
3. 文檔化重定向機制供後續維護

---

#### 風險 3: TiDB 免費版儲存空間不足
**影響**: 資料無法寫入，系統崩潰
**機率**: 20%（2-3 年後）
**緩解措施**:
1. 實作定期資料清理（離職員工超過 5 年自動封存）
2. 監控儲存用量並設定警告
3. 規劃升級至付費版或遷移至其他資料庫

---

### ⚠️ 中風險項目

#### 風險 4: CORS 跨域請求失敗
**影響**: 前端無法呼叫本機 API
**機率**: 40%
**緩解措施**:
1. 測試 CORSMiddleware 配置
2. 檢查瀏覽器 preflight 請求是否正常
3. 提供詳細的錯誤訊息指引使用者

---

#### 風險 5: JWT Token XSS 攻擊
**影響**: Token 被竊取，使用者身份冒用
**機率**: 10%（內部系統，風險較低）
**緩解措施**:
1. 實作 Content Security Policy
2. 定期安全稽核（檢查 XSS 漏洞）
3. 短期 Token + 自動登出機制

---

## 5. 改善建議

### 立即執行（Phase 1 之前）

1. **保存 plan.md** - 將使用者提供的 Implementation Plan 保存至 `specs/001-system-architecture/plan.md`

2. **更新憲章** - 修訂 IV. 混合架構原則，反映架構變更

3. **驗證 PyInstaller 打包** - 建立測試專案驗證可行性

---

### Phase 1 執行期間

4. **建立 data-model.md** - 詳細定義資料庫 schema（含索引、外鍵、約束）

5. **建立 API 合約** - 使用 OpenAPI 3.0 規格撰寫 `contracts/cloud-api.yaml` 與 `local-api.yaml`

6. **建立 quickstart.md** - 記錄開發環境設定步驟（Python 虛擬環境、Node.js、TiDB 連線測試）

7. **補充 Google API 設計** - 服務帳戶配置流程、權限設定、憑證管理

---

### Phase 2 執行期間

8. **實作 CSP** - Content Security Policy 防禦 XSS 攻擊

9. **實作資料備份功能** - 定期匯出 SQL 備份檔案至本機

10. **測試所有路由** - 確保 GitHub Pages 部署後所有頁面可直接存取

---

## 6. Phase 0 完成度總結

### ✅ 已完成項目（90%）

1. ✅ 技術選型研究（research.md，480 行）
2. ✅ 前端專案初始化（Vue.js 3 + Vite）
3. ✅ 前端基礎架構（Router, Pinia, Axios, 工具函式）
4. ✅ 環境變數配置（.env, .env.example）

### ⏳ 進行中項目（10%）

5. ⏳ 前端 View 元件開發（已建立目錄但未實作）
6. ⏳ 後端專案初始化（尚未開始）

### ❌ 待執行項目（0%）

7. ❌ plan.md 保存至專案
8. ❌ 憲章更新（架構變更）
9. ❌ Phase 1 文件（data-model.md, contracts/, quickstart.md）
10. ❌ tasks.md 生成（speckit 流程）

---

## 7. 下一步建議

### 短期（今日/明日）

1. **保存 plan.md** - 將 Implementation Plan 保存至正確位置
2. **更新憲章** - 修訂混合架構原則
3. **生成 tasks.md** - 使用 `/speckit.tasks` 從 plan.md 生成任務清單

### 中期（本週）

4. **執行 Phase 1** - 建立 data-model.md, contracts/, quickstart.md
5. **初始化後端專案** - backend-cloud/ 與 backend-local/ 目錄結構
6. **驗證高風險項目** - PyInstaller 打包測試

### 長期（下週）

7. **執行 Phase 2** - 實作資料模型、API 端點、前端頁面
8. **部署測試** - GitHub Pages + Render 部署驗證
9. **安全強化** - CSP 實作、XSS 防禦測試

---

## 8. 總結

**Phase 0 完成度**: 90%

**總體評價**:
研究工作紮實，技術選型合理且有充分理由支持。前端專案結構清晰，但後端尚未開始。存在一些需要關注的風險點（PyInstaller 打包、GitHub Pages 路由），但都有明確的緩解措施。

**關鍵行動項**:
1. 🔴 **立即更新憲章**（架構變更需記錄）
2. 🔴 **保存 plan.md**（避免遺失實作計畫）
3. 🟡 **驗證 PyInstaller 打包**（高風險項目需提前測試）
4. 🟢 **繼續執行 Phase 1**（按 speckit 流程生成必要文件）

**審查結論**:
專案基礎穩固，方向正確。建議優先處理憲章更新與高風險項目驗證，然後按 speckit 流程繼續執行 Phase 1。

---

**審查完成** | **建議下次審查時機**: Phase 1 完成後
