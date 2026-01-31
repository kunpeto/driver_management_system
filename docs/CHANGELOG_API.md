# API 變更日誌

本文檔記錄所有 API 的變更歷史。

## 格式說明

每個變更條目包含：
- **變更類型標記**:
  - 🔴 `BREAKING`: 破壞性變更（需要特別注意）
  - 🟡 `MINOR`: 非破壞性變更（新增功能）
  - 🟢 `PATCH`: 修復或改善
- **保護等級標記**: `[CRITICAL]`, `[STABLE]`, `[EVOLVING]`
- **影響的端點**
- **變更說明**

---

## [1.0.0] - 2026-01-31

### 初始版本發布

建立 API 契約管理機制，定義所有穩定性 API。

---

### 🟢 [ADDED] 系統設定 API

#### `GET /api/settings/value/{key}` **[CRITICAL CONTRACT]**

- **狀態**: 新增
- **保護等級**: CRITICAL
- **依賴方**: `desktop_app/src/utils/backend_api_client.py`
- **說明**: 桌面應用透過此端點取得系統設定值（如 Google Drive Folder ID）

**回應格式**:
```json
{
  "key": "google_drive_folder_id",
  "department": "淡海",
  "value": "1ABC123..."
}
```

---

### 🟢 [ADDED] 桌面應用 健康檢查 API

#### `GET /health` **[CRITICAL CONTRACT]**

- **狀態**: 新增
- **保護等級**: CRITICAL
- **依賴方**: 前端 Web 應用
- **說明**: 前端透過此端點檢查桌面應用是否運行中

**回應格式**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T12:00:00",
  "version": "0.1.0",
  "services": {
    "api": "running"
  }
}
```

---

### 🟢 [ADDED] PDF 處理 API

#### `POST /api/pdf/scan` **[CRITICAL CONTRACT]**

- **狀態**: 新增
- **保護等級**: CRITICAL
- **依賴方**: 前端 Web 應用
- **說明**: 掃描 PDF 中的條碼

#### `POST /api/pdf/split` **[CRITICAL CONTRACT]**

- **狀態**: 新增
- **保護等級**: CRITICAL
- **依賴方**: 前端 Web 應用
- **說明**: 依條碼切分 PDF

#### `POST /api/pdf/process` **[CRITICAL CONTRACT]**

- **狀態**: 新增
- **保護等級**: CRITICAL
- **依賴方**: 前端 Web 應用
- **說明**: 完整處理 PDF（識別、切分、上傳到 Google Drive）

---

### 🟢 [ADDED] 條碼生成 API

#### `POST /api/barcode/generate` **[CRITICAL CONTRACT]**

- **狀態**: 新增
- **保護等級**: CRITICAL
- **依賴方**: 前端 Web 應用
- **說明**: 生成條碼圖片（返回 Base64）

**回應格式**:
```json
{
  "success": true,
  "data": "TH-12345",
  "format": "code128",
  "image_format": "png",
  "base64_image": "...",
  "data_uri": "data:image/png;base64,...",
  "error_message": null
}
```

---

### 🟢 [ADDED] 版本資訊 API

#### `GET /version` **[STABLE]**

- **狀態**: 新增
- **保護等級**: STABLE
- **說明**: 返回桌面應用版本、API 契約版本、支援功能列表

**回應格式**:
```json
{
  "app_name": "司機員管理系統 - 桌面應用",
  "version": "0.1.0",
  "build_date": "2026-01-31",
  "api_contract_version": "1.0.0",
  "min_backend_version": "1.0.0",
  "max_backend_version": "1.x.x",
  "supported_features": ["pdf_scan", "pdf_split", "pdf_process", "barcode_generate"],
  "contracted_endpoints": [...]
}
```

---

## 變更記錄模板

在記錄新變更時，請使用以下模板：

```markdown
## [版本號] - YYYY-MM-DD

### 🔴/🟡/🟢 [BREAKING/MINOR/PATCH] 變更標題

#### `HTTP_METHOD /path` **[CRITICAL/STABLE/EVOLVING]**

- **狀態**: 新增/修改/棄用/移除
- **保護等級**: CRITICAL/STABLE/EVOLVING
- **依賴方**: 受影響的系統/檔案
- **說明**: 變更的詳細說明

**變更前** (如適用):
\`\`\`json
{ ... }
\`\`\`

**變更後** (如適用):
\`\`\`json
{ ... }
\`\`\`

**遷移指南** (如為破壞性變更):
1. 步驟一
2. 步驟二
```
