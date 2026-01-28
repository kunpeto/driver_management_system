# 司機員管理系統 (Driver Management System)

使用雲端資料庫 (TiDB) 與 Render 部署的司機員事件履歷與考核管理、駕駛時數管理系統。

## 系統架構

- **前端應用**：PyQt6 桌面應用程式
- **後端 API**：FastAPI (部署於 Render)
- **資料庫**：TiDB Serverless (MySQL 相容)
- **外部整合**：Google Sheets、Google Drive

## 快速開始

### 1. 環境設定

複製環境變數範本並填入實際資訊：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入以下資訊：
- TiDB 資料庫連線資訊
- Google API 憑證路徑
- FastAPI 密鑰

### 2. 安裝相依套件

```bash
pip install -r requirements.txt
```

### 3. 測試資料庫連線

```bash
python test_tidb_connection.py
```

預期輸出：
```
============================================================
TiDB 連線測試
============================================================
Host: gateway01.ap-northeast-1.prod.aws.tidbcloud.com
Port: 4000
User: 3SQWVrWh5DieHsr.root
Database: test
============================================================

[OK] 使用 pymysql 連線...
[OK] 連線成功！
[OK] 資料庫版本: 8.0.11-TiDB-v7.5.6-serverless
[OK] 當前資料庫: test
[OK] 資料表數量: 0

[OK] 測試完成！連線正常。
```

### 4. 初始化資料庫

```bash
python scripts/init_database.py
```

### 5. 啟動應用程式

```bash
# 開發模式（本機 FastAPI）
python main.py

# 生產模式（連接 Render）
python main.py --production
```

## 資料庫資訊

- **平台**：TiDB Cloud Serverless
- **版本**：TiDB v7.5.6 (相容 MySQL 8.0.11)
- **連線方式**：SSL/TLS 加密連線
- **儲存限制**：5 GB (免費版)
- **連線驅動**：pymysql

詳細資料庫配置請參考：`specs/001-system-architecture/spec.md` 的 "Database Configuration" 章節。

## 專案結構

```
driver_management_system/
├── .env                    # 環境變數（不提交到 Git）
├── .env.example            # 環境變數範本
├── test_tidb_connection.py # 資料庫連線測試
├── requirements.txt        # Python 相依套件
├── main.py                 # 桌面應用主程式
├── specs/                  # 規格文件
│   └── 001-system-architecture/
│       └── spec.md         # 系統架構規格
├── scripts/                # 工具腳本
│   └── init_database.py    # 資料庫初始化
├── backend/                # FastAPI 後端
│   ├── api/                # API 路由
│   ├── models/             # 資料模型
│   ├── services/           # 業務邏輯
│   └── main.py             # FastAPI 主程式
└── frontend/               # PyQt6 前端
    ├── ui/                 # UI 介面
    └── widgets/            # 自訂元件
```

## 安全性注意事項

⚠️ **重要**：
- **不要**將 `.env` 檔案提交到版控系統
- `.env` 已包含在 `.gitignore` 中
- 在 Render 部署時，使用平台的環境變數設定功能
- Google API 憑證檔案應妥善保管，不要公開

## 相關文件

- [系統架構規格](specs/001-system-architecture/spec.md)
- [資料庫連線設定](specs/001-system-architecture/spec.md#database-configuration)
- [API 文件](docs/api.md) *(待建立)*

## 授權

MIT License
