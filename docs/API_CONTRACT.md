# API 契約文檔

> **版本**: 1.0.0
> **最後更新**: 2026-01-31
> **維護者**: 開發團隊

## 概述

本文檔定義了司機員管理系統中跨系統 API 的穩定性契約。由於桌面應用打包為 .exe 後無法輕易更新，而雲端後端會透過 GitHub Actions 持續部署，因此需要嚴格的 API 契約管理機制。

---

## 保護等級定義

### CRITICAL（關鍵）
- **定義**: 絕對不可修改的 API 契約
- **原因**: 桌面應用 .exe 直接依賴這些端點
- **修改限制**:
  - ❌ 禁止移除端點
  - ❌ 禁止修改 URL 路徑
  - ❌ 禁止移除回應欄位
  - ❌ 禁止變更欄位類型
  - ✅ 允許新增可選回應欄位

### STABLE（穩定）
- **定義**: 僅可向後兼容修改
- **修改限制**:
  - ❌ 禁止移除現有欄位
  - ❌ 禁止變更欄位類型
  - ✅ 允許新增可選欄位
  - ✅ 允許新增可選參數（需有預設值）

### EVOLVING（演進中）
- **定義**: 可在主版本更新時進行破壞性修改
- **修改限制**:
  - ✅ 可在主版本更新時修改
  - ⚠️ 需提前通知並記錄在 CHANGELOG_API.md

---

## 變更政策

### 破壞性變更定義

以下行為被視為「破壞性變更」：
1. 移除現有 API 端點
2. 變更端點 URL 路徑
3. 移除回應中的欄位
4. 變更欄位的資料類型
5. 將可選參數變為必填
6. 變更回應的 HTTP 狀態碼語意

### 變更流程

#### CRITICAL 端點
1. **禁止直接修改** - 需重新評估系統架構
2. 如確實需要修改，必須：
   - 建立新端點（版本化，如 `/v2/...`）
   - 保留舊端點至少 6 個月
   - 更新桌面應用並重新發布
   - 等待所有用戶更新後才可棄用舊端點

#### STABLE 端點
1. 在 CHANGELOG_API.md 記錄變更
2. 確保新增欄位有合理預設值
3. 更新相關文檔

#### EVOLVING 端點
1. 在 CHANGELOG_API.md 記錄變更
2. 主版本升級時通知相關團隊

---

## CRITICAL 端點清單

### 雲端後端 → 桌面應用依賴

#### GET /api/settings/value/{key}

| 屬性 | 值 |
|------|-----|
| **保護等級** | CRITICAL |
| **依賴方** | `desktop_app/src/utils/backend_api_client.py` |
| **版本** | 1.0.0 |
| **用途** | 取得系統設定值 |

**請求**:
```
GET /api/settings/value/{key}?department={department}&default={default}
```

**參數**:
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| key | string | ✅ | 設定鍵名 |
| department | string | ❌ | 部門名稱（淡海/安坑） |
| default | string | ❌ | 預設值 |

**回應** (200 OK):
```json
{
  "key": "google_drive_folder_id",
  "department": "淡海",
  "value": "1ABC123..."
}
```

**回應欄位**:
| 欄位 | 類型 | 必定存在 | 說明 |
|------|------|----------|------|
| key | string | ✅ | 設定鍵名 |
| department | string \| null | ✅ | 部門名稱 |
| value | string \| null | ✅ | 設定值 |

---

### 桌面應用 → 前端依賴

#### GET /health

| 屬性 | 值 |
|------|-----|
| **保護等級** | CRITICAL |
| **依賴方** | 前端 Web 應用 |
| **版本** | 1.0.0 |
| **用途** | 健康檢查 |

**回應** (200 OK):
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

**回應欄位**:
| 欄位 | 類型 | 必定存在 | 說明 |
|------|------|----------|------|
| status | string | ✅ | 狀態（"healthy"） |
| timestamp | string | ✅ | ISO 8601 時間戳 |
| version | string | ✅ | 應用版本 |
| services | object | ✅ | 服務狀態 |

---

#### POST /api/pdf/scan

| 屬性 | 值 |
|------|-----|
| **保護等級** | CRITICAL |
| **依賴方** | 前端 Web 應用 |
| **版本** | 1.0.0 |
| **用途** | 掃描 PDF 中的條碼 |

**請求**: `multipart/form-data`
| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| file | File | ✅ | PDF 檔案 |

**回應** (200 OK):
```json
{
  "success": true,
  "file_name": "document.pdf",
  "total_pages": 10,
  "barcodes": [
    {
      "page_number": 1,
      "barcode_type": "CODE128",
      "barcode_data": "TH-12345",
      "department": "淡海"
    }
  ],
  "error_message": null
}
```

---

#### POST /api/pdf/split

| 屬性 | 值 |
|------|-----|
| **保護等級** | CRITICAL |
| **依賴方** | 前端 Web 應用 |
| **版本** | 1.0.0 |
| **用途** | 依條碼切分 PDF |

**請求**: `multipart/form-data`
| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| file | File | ✅ | PDF 檔案 |
| output_dir | string | ❌ | 輸出目錄 |

**回應**: 同 `/api/pdf/process`

---

#### POST /api/pdf/process

| 屬性 | 值 |
|------|-----|
| **保護等級** | CRITICAL |
| **依賴方** | 前端 Web 應用 |
| **版本** | 1.0.0 |
| **用途** | 完整處理 PDF（識別、切分、上傳） |

**請求**: `multipart/form-data`
| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| file | File | ✅ | PDF 檔案 |
| upload_to_drive | bool | ❌ | 是否上傳到 Drive（預設 true） |
| output_dir | string | ❌ | 本機輸出目錄 |

**回應** (200 OK):
```json
{
  "success": true,
  "task_id": "abc12345",
  "file_name": "document.pdf",
  "total_pages": 10,
  "barcodes_found": 3,
  "files_created": 3,
  "files_uploaded": 3,
  "split_files": [...],
  "error_message": null,
  "processing_time_ms": 1500
}
```

---

#### POST /api/barcode/generate

| 屬性 | 值 |
|------|-----|
| **保護等級** | CRITICAL |
| **依賴方** | 前端 Web 應用 |
| **版本** | 1.0.0 |
| **用途** | 生成條碼圖片 |

**請求**: `application/json`
```json
{
  "data": "TH-12345",
  "format": "code128",
  "image_format": "png",
  "width": null,
  "height": 100,
  "include_text": true,
  "font_size": 10,
  "quiet_zone": 6
}
```

**回應** (200 OK):
```json
{
  "success": true,
  "data": "TH-12345",
  "format": "code128",
  "image_format": "png",
  "base64_image": "iVBORw0KGgo...",
  "data_uri": "data:image/png;base64,iVBORw0KGgo...",
  "error_message": null
}
```

---

## 版本相容性矩陣

| 桌面應用版本 | API 契約版本 | 最低後端版本 | 最高後端版本 |
|-------------|-------------|-------------|-------------|
| 0.1.0 | 1.0.0 | 1.0.0 | 1.x.x |

---

## 給 AI 代理的指示

> **重要警告**
>
> 此文檔中標記為 **CRITICAL** 的端點被桌面應用 (.exe) 直接依賴。
>
> 在修改任何標記為 CRITICAL 的 API 時：
> 1. **停止** - 不要直接修改
> 2. **檢查** - 確認是否真的需要修改
> 3. **詢問** - 如果不確定，先詢問用戶
> 4. **記錄** - 在 CHANGELOG_API.md 記錄任何變更
>
> 破壞 CRITICAL API 契約會導致已部署的桌面應用完全失效，
> 而用戶無法輕易更新桌面應用。

---

## 附錄：快速參考

### 禁止修改的項目（CRITICAL 端點）
- URL 路徑
- HTTP 方法
- 必要的請求參數
- 回應中已存在的欄位名稱
- 回應欄位的資料類型

### 允許的修改（CRITICAL 端點）
- 新增可選的請求參數（需有預設值）
- 新增可選的回應欄位
- 改善錯誤訊息的文字內容
- 效能優化（不改變介面）
