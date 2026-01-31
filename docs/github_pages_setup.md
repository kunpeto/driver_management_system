# GitHub Pages 部署設定指南

## 自動部署設定

本專案已配置 GitHub Actions 自動部署前端到 GitHub Pages。

---

## 一次性設定步驟

### 1. 啟用 GitHub Pages

1. 前往 GitHub Repository 頁面
2. 點擊 **Settings**（設定）
3. 在左側選單找到 **Pages**
4. 在 **Source** 下拉選單中選擇：
   - **Source**: `GitHub Actions`

   ![GitHub Pages Source](https://docs.github.com/assets/cb-47267/mw-1440/images/help/pages/publishing-source-dropdown.webp)

5. 點擊 **Save**（儲存）

### 2. 驗證設定

設定完成後，當您推送任何變更到 `frontend/` 目錄時，GitHub Actions 會自動：

1. ✅ 安裝依賴
2. ✅ 建置前端專案
3. ✅ 部署到 GitHub Pages

---

## 自動部署觸發條件

以下情況會自動觸發部署：

- ✅ 推送到 `main` 分支，且包含 `frontend/` 目錄的變更
- ✅ 修改 `.github/workflows/deploy-frontend.yml`
- ✅ 手動在 GitHub Actions 頁面觸發

---

## 部署 URL

部署成功後，前端網站會發布到：

```
https://<your-username>.github.io/driver_management_system/
```

例如：
```
https://kunpeto.github.io/driver_management_system/
```

---

## 手動觸發部署

如果需要手動觸發部署：

1. 前往 GitHub Repository
2. 點擊 **Actions** 標籤
3. 在左側選擇 **Deploy Frontend to GitHub Pages**
4. 點擊右側的 **Run workflow** 按鈕
5. 選擇 `main` 分支
6. 點擊 **Run workflow**

---

## 查看部署狀態

### 方法 1: Actions 頁面

1. 前往 **Actions** 標籤
2. 查看最近的 workflow 執行狀態
3. 點擊特定執行可查看詳細日誌

### 方法 2: Commit 狀態

在 commit 旁邊會顯示狀態圖示：
- ✅ 綠色勾勾：部署成功
- ❌ 紅色叉叉：部署失敗
- 🟡 黃色圓點：部署中

---

## 常見問題

### Q: 為什麼部署後網站顯示 404？

**A**: 確認以下設定：
1. `vite.config.js` 中的 `base` 設定為 `/driver_management_system/`
2. GitHub Pages Source 已設定為 `GitHub Actions`
3. 部署 workflow 成功執行

### Q: 如何查看部署日誌？

**A**:
1. 前往 **Actions** 標籤
2. 點擊最近的 workflow 執行
3. 展開 **Build** 和 **Deploy** 步驟查看詳細日誌

### Q: 部署需要多久？

**A**:
- **建置時間**: 約 1-2 分鐘
- **部署時間**: 約 30 秒 - 1 分鐘
- **總計**: 約 2-3 分鐘

### Q: 可以部署到自訂網域嗎？

**A**: 可以！步驟如下：
1. 在 `frontend/public/` 目錄建立 `CNAME` 檔案
2. 檔案內容為您的網域名稱（例如 `example.com`）
3. 在網域 DNS 設定中新增 CNAME 記錄指向 `<username>.github.io`
4. 在 GitHub Pages 設定中填入自訂網域

---

## 技術細節

### Workflow 配置

檔案位置: `.github/workflows/deploy-frontend.yml`

#### 觸發條件
```yaml
on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/deploy-frontend.yml'
  workflow_dispatch:
```

#### 建置步驟
1. Checkout 代碼
2. 安裝 Node.js 18
3. 使用 `npm ci` 安裝依賴（快速且可重現）
4. 執行 `npm run build`
5. 上傳 `dist/` 目錄作為 artifact

#### 部署步驟
1. 使用官方 `actions/deploy-pages@v4`
2. 部署到 GitHub Pages environment

### Vite 配置重點

```javascript
export default defineConfig({
  base: '/driver_management_system/',  // GitHub Pages 子路徑
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'element-plus': ['element-plus'],
          'utils': ['axios', 'dayjs']
        }
      }
    }
  }
})
```

### 快取策略

- **Node modules 快取**: 使用 `actions/setup-node@v4` 的內建快取
- **快取鍵**: 基於 `frontend/package-lock.json`
- **效果**: 第二次建置速度提升 50-70%

---

## 本機測試生產建置

在推送前，建議先在本機測試生產建置：

```bash
cd frontend

# 建置
npm run build

# 預覽生產建置
npm run preview
```

預覽服務會在 `http://localhost:4173` 啟動。

---

## 相關文檔

- [GitHub Pages 官方文檔](https://docs.github.com/en/pages)
- [GitHub Actions 文檔](https://docs.github.com/en/actions)
- [Vite 部署指南](https://vitejs.dev/guide/static-deploy.html)
