# UI 設計優化規劃書：Minimalist Modern

## 0. 設計原則 (Design Principles)

1.  **少即是多 (Less is More)**：去除多餘的裝飾性陰影和漸變，改用**線條（Borders）**與**留白（Whitespace）**來區分層級。
2.  **高對比度 (High Contrast)**：文字顏色必須深邃清晰，避免使用過淺的灰色，確保在各種螢幕下都易於閱讀。
3.  **功能性色彩 (Functional Color)**：色彩僅用於引導操作（按鈕、連結）或標示狀態（成功、失敗），背景維持極致的中性色。
4.  **統一導角 (Consistent Radius)**：採用微導角（6px-8px），在現代感與親和力之間取得平衡。

---

## 1. 色彩系統設計 (Color System)

我們採用 **Slate (板岩灰)** 作為中性色基底，搭配高飽和度的 **Royal Blue (皇家藍)** 作為品牌色，打造專業且冷靜的視覺感受。

### 1.1 主色調 (Brand Colors)
這組藍色比 Element Plus 預設藍色（#409EFF）更深沉、更穩重，且在白底上對比度更高。

| 色彩名稱 | HEX 值 | 用途 |
| :--- | :--- | :--- |
| **Primary Main** | **#2563EB** | 主要按鈕、選中狀態、連結 (對比度 4.6:1+ on White) |
| **Primary Hover** | **#1D4ED8** | Hover 懸停互動狀態 |
| **Primary Surface**| **#EFF6FF** | 選中項目的背景色（極淺藍） |

### 1.2 中性色階 (Neutrals & Typography)
這是「高對比度」的關鍵。文字使用近乎黑色的深灰，背景使用極淺灰。

| 色彩名稱 | HEX 值 | 用途 |
| :--- | :--- | :--- |
| **Text Primary** | **#0F172A** | 主要標題、正文 (Slate-900) - **極致清晰** |
| **Text Regular** | **#334155** | 次要資訊、表格內容 (Slate-700) |
| **Text Secondary**| **#64748B** | 輔助說明、Placeholder (Slate-500) |
| **Border** | **#E2E8F0** | 邊框、分隔線 (Slate-200) |
| **Background Body**| **#F8FAFC** | 全局背景色 (Slate-50) |
| **Background Base**| **#FFFFFF** | 卡片、側邊欄、彈窗背景 |

### 1.3 狀態色 (Functional Status)
保持標準語意，但調整明度以符合現代感。

| 狀態 | HEX 值 | 用途 |
| :--- | :--- | :--- |
| **Success** | **#10B981** | 完成、通過 (Emerald-500) |
| **Warning** | **#F59E0B** | 提醒、待處理 (Amber-500) |
| **Danger** | **#EF4444** | 錯誤、刪除、嚴重違規 (Red-500) |

---

## 2. 版面配置優化 (Layout)

### 2.1 側邊欄 (Sidebar) - 重大改變
*   **建議**：由原本的「深色 (#304156)」改為 **「純白背景 (#FFFFFF) + 右側細邊框」**。
*   **理由**：
    1.  **視覺延伸**：淺色側邊欄能讓視覺與內容區融合，減少視覺上的「切割感」，讓螢幕看起來更寬敞。
    2.  **現代感**：這是現代 SaaS 的主流設計（符合用戶需求的 Minimalist 風格）。
*   **選中狀態**：不再使用整塊深色背景，改為「左側藍色指示條 + 淺藍色背景 + 藍色文字」。

### 2.2 頂部欄 (Header)
*   **高度**：縮減至 56px 或 60px（更加緊湊）。
*   **樣式**：純白背景，底部增加 1px 邊框 (`border-bottom: 1px solid #E2E8F0`)，**移除陰影**。
*   **內容**：僅保留麵包屑（Breadcrumb）和用戶頭像/通知。麵包屑字體加深。

### 2.3 內容區 (Main Content)
*   **Grid System**：嚴格遵循 8px 倍數間距。
    *   卡片內邊距：24px (3x8)
    *   卡片間距：16px (2x8)
*   **卡片設計**：
    *   去除明顯的 Box-shadow。
    *   改用 **1px Border (#E2E8F0)** 區分邊界。
    *   若必須強調，使用極其微弱的陰影 (`0 1px 3px rgba(0,0,0,0.05)`)。

---

## 3. 組件風格統一 (Components)

### 3.1 按鈕 (Buttons)
*   **圓角**：6px (中等圓角，既不銳利也不過於圓潤)。
*   **樣式**：扁平化 (Flat)，移除漸層。
*   **陰影**：主要按鈕可帶有微弱的同色系投影 (`box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2)`)

### 3.2 表格 (Tables) - 重點優化
由於是管理系統，表格是最核心的組件。
*   **表頭**：淺灰色背景 (`#F1F5F9`)，深色文字 (`#475569`)，加粗 (`font-weight: 600`)。
*   **行高**：增加 Padding，設為舒適模式，避免密集恐懼。
*   **斑馬紋**：建議取消，改用 Hover 高亮 (`background-color: #F8FAFC`)。
*   **邊框**：僅保留水平分隔線，移除垂直分隔線，減少視覺雜訊。

### 3.3 表單 (Inputs)
*   **預設**：白色背景，淺灰邊框 (`#CBD5E1`)。
*   **Focus**：**加粗藍色邊框**，移除瀏覽器預設的 Glow 效果，改為清晰的 Ring (`box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1)`)
*   **文字**：輸入內容必須是深色 (`#0F172A`)。

---

## 4. 實施代碼 (CSS Variables)

### 4.1 核心變數定義

```css
:root {
  /* --- 1. 色彩系統 (Color Palette) --- */
  /* 主色 - Royal Blue */
  --color-primary: #2563EB;
  --color-primary-hover: #1D4ED8;
  --color-primary-light: #EFF6FF; /* 用於背景/hover */

  /* 文字顏色 - High Contrast Slate */
  --text-primary: #0F172A;   /* 標題 */
  --text-regular: #334155;   /* 正文 */
  --text-secondary: #64748B; /* 次要/Label */
  --text-placeholder: #94A3B8;

  /* 背景與邊框 */
  --bg-body: #F8FAFC;        /* 頁面背景 */
  --bg-white: #FFFFFF;       /* 卡片背景 */
  --border-color: #E2E8F0;   /* 淺邊框 */
  --border-color-dark: #CBD5E1; /* 輸入框邊框 */

  /* 狀態色 */
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;

  /* --- 2. 佈局尺寸 (Layout) --- */
  --sidebar-width: 240px;
  --header-height: 60px;
  --radius-base: 6px;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-card: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.01);
}
```

### 4.2 Element Plus 覆蓋 (SCSS)

```scss
/* Element Plus Theme Overrides */
:root {
  --el-color-primary: var(--color-primary);
  --el-color-success: var(--color-success);
  --el-color-warning: var(--color-warning);
  --el-color-danger: var(--color-danger);

  --el-text-color-primary: var(--text-primary);
  --el-text-color-regular: var(--text-regular);
  --el-text-color-secondary: var(--text-secondary);

  --el-border-color: var(--border-color);
  --el-border-color-light: var(--border-color); /* 統一邊框顏色 */

  --el-bg-color: var(--bg-white);
  --el-bg-color-page: var(--bg-body);

  --el-border-radius-base: 6px;
  --el-border-radius-small: 4px;
}

/* 針對特定組件的優化 */

/* 卡片去陰影，加邊框 */
.el-card {
  border: 1px solid var(--border-color) !important;
  box-shadow: var(--shadow-card) !important;
  border-radius: 8px;
}

/* 側邊欄改為淺色風格 */
.el-aside {
  background-color: var(--bg-white) !important;
  border-right: 1px solid var(--border-color);

  .el-menu {
    border-right: none;
    background-color: var(--bg-white);
  }

  /* 選單項目 */
  .el-menu-item {
    color: var(--text-regular);
    margin: 4px 8px;
    border-radius: 6px;
    height: 48px;
    line-height: 48px;

    &:hover {
      background-color: var(--bg-body);
      color: var(--color-primary);
    }

    &.is-active {
      background-color: var(--color-primary-light);
      color: var(--color-primary);
      font-weight: 600;
    }
  }
}

/* 表格優化 */
.el-table {
  --el-table-header-bg-color: #F1F5F9;
  --el-table-header-text-color: #475569;

  th.el-table__cell {
    font-weight: 600;
  }
}

/* 按鈕優化 */
.el-button {
  font-weight: 500;
}
```

---

## 5. 實施路線圖 (Roadmap)

### Phase 1: 基礎重塑 (Foundation)
1.  **全局變數替換**：在 `App.vue` 或 `main.js` 中引入上述 CSS 變數，替換 Element Plus 預設主題色。
2.  **背景與字體重置**：將 `body` 背景設為 `#F8FAFC`，強制所有文字顏色加深。
3.  **按鈕與輸入框**：調整圓角與 Border 顏色，確保清晰度。

### Phase 2: 框架佈局 (Layout Structure)
1.  **側邊欄改造**：去除深色背景，實作「淺色+選中高亮」樣式。
2.  **頂部欄簡化**：移除陰影，加入底邊框，簡化內容。
3.  **間距調整**：檢查所有頁面的 `padding` 和 `margin`，統一為 16px/24px。

### Phase 3: 組件優化 (Components & Details)
1.  **卡片平面化**：移除所有卡片的重陰影，改用細邊框。
2.  **表格可讀性**：調整表頭顏色與行高。
3.  **圖標替換**：若有資源，將現有的實心圖標（Solid）逐步替換為線性圖標（Outline），視覺會更輕盈。

---

## 色彩預覽

```
主色系列：
██ #2563EB (Primary)     ██ #1D4ED8 (Hover)     ░░ #EFF6FF (Surface)

文字色系：
██ #0F172A (Primary)     ██ #334155 (Regular)   ██ #64748B (Secondary)

狀態色：
██ #10B981 (Success)     ██ #F59E0B (Warning)   ██ #EF4444 (Danger)

背景/邊框：
░░ #F8FAFC (Body BG)     ░░ #FFFFFF (Card BG)   ── #E2E8F0 (Border)
```
