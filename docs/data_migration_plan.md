# 歷史資料遷移方案

**建立日期**: 2026-01-28
**規劃範圍**: 從舊系統（SQLite）遷移 2026 年前的履歷資料到新系統（TiDB）

---

## 📊 舊資料庫分析結果

### 資料庫概況
- **資料庫類型**: SQLite
- **檔案大小**: 1,388 KB (約 1.4 MB)
- **位置**: `C:\Users\kunpe\claude專案\driver_profile_system_重構\database\driver_profiles.db`

### 核心資料表與資料量

| 資料表名稱 | 總筆數 | 2026前需遷移 | 2026後排除 | 說明 |
|-----------|--------|------------|----------|------|
| **profiles** | 675 | **580** | 95 | 事件履歷主表 |
| **employees** | 58 | 58 | 0 | 員工基本資料 |
| **event_investigation** | 404 | - | - | 事件調查詳細資料 |
| **personnel_interview** | 177 | - | - | 人員訪談記錄 |
| **assessment_standards** | 85 | 85 | - | 考核標準表 |
| **users** | 1 | 1 | - | 使用者帳號 |
| **system_settings** | 9 | 9 | - | 系統設定 |
| **driving_daily_stats** | 757 | 0 | 757 | 駕駛時數（全是2026年） |

**遷移資料量估計**: 約 580 筆履歷 + 58 位員工 + 相關聯資料，總計約 **1,200-1,500 筆記錄**

---

## 🔍 關鍵欄位差異分析

### 1. **employees** 資料表

#### 舊系統欄位
```python
- id (INTEGER PK)
- employee_id (VARCHAR(20), UNIQUE)
- employee_name (VARCHAR(50))
- is_resigned (BOOLEAN)
- created_at (DATETIME)
- updated_at (DATETIME)
```

#### 新系統欄位（根據 spec.md）
```python
- id (INTEGER PK)
- employee_id (VARCHAR(20), UNIQUE)
- employee_name (VARCHAR(50))
- current_department (ENUM: '淡海', '安坑')  ⚠️ 新增
- hire_year_month (VARCHAR(7))              ⚠️ 新增
- phone (VARCHAR(20), nullable)             ⚠️ 新增
- email (VARCHAR(100), nullable)            ⚠️ 新增
- emergency_contact (VARCHAR(50), nullable) ⚠️ 新增
- emergency_phone (VARCHAR(20), nullable)   ⚠️ 新增
- is_resigned (BOOLEAN)
- created_at (DATETIME)
- updated_at (DATETIME)
```

#### 🚨 **關鍵缺失欄位**
1. **current_department** - 舊資料無部門資訊
2. **hire_year_month** - 舊資料無入職年月（但可從 employee_id 解析）

---

### 2. **profiles** 資料表

#### 舊系統欄位
```python
- id, profile_type, event_date, event_time, event_title
- employee_id, employee_name
- event_location, train_number, event_description
- data_source, assessment_item, assessment_score
- conversion_status, file_path
- created_by, created_at, updated_at
- gdrive_link, version
```

#### 新系統預期欄位（根據業務邏輯推測）
```python
- 應包含 department (ENUM: '淡海', '安坑') ⚠️ 新增
- 其他欄位大致相容
```

---

## 🎯 解決方案：三階段遷移策略

### **方案 A：完整遷移（建議採用）** ✅

#### 階段 1：資料清理與部門判定
**問題**: 舊資料沒有 `department` 欄位
**解決方式**:
1. **預設所有歷史資料歸屬「淡海」部門**
   - 理由：前專案主要服務淡海分處
   - 安坑分處為新增需求，歷史資料不適用

2. **從員工編號解析入職年月**
   ```python
   # 範例：1011M0095 → hire_year_month = "2021-11"
   # 範例：1108M0296 → hire_year_month = "2021-08"
   def parse_hire_date(employee_id):
       year_code = employee_id[:2]   # "10" → 2010年代
       month_code = employee_id[2:4] # "11" → 11月
       year = 2000 + int(year_code)
       month = int(month_code)
       return f"{year}-{month:02d}"
   ```

3. **聯絡資訊欄位保持 NULL**
   - phone, email, emergency_contact, emergency_phone 設為 NULL
   - 後續由管理員手動補充

#### 階段 2：資料結構轉換
**實作工具**: Python 遷移腳本 `scripts/migrate_from_sqlite.py`

**轉換邏輯**:
```python
# employees 資料表轉換
old_employee = {
    'employee_id': '1011M0095',
    'employee_name': '張三',
    'is_resigned': False
}

new_employee = {
    'employee_id': '1011M0095',
    'employee_name': '張三',
    'current_department': '淡海',  # 預設值
    'hire_year_month': '2021-11',  # 從 employee_id 解析
    'phone': None,
    'email': None,
    'emergency_contact': None,
    'emergency_phone': None,
    'is_resigned': False,
    'created_at': old_employee['created_at'],
    'updated_at': datetime.now()
}
```

#### 階段 3：資料驗證與回滾機制
1. **遷移前備份**
   - 匯出 TiDB 當前資料
   - 建立 SQLite 備份檔案

2. **資料驗證檢查點**
   - 檢查員工編號唯一性
   - 檢查外鍵完整性（profiles → employees）
   - 檢查日期格式正確性
   - 統計遷移前後筆數

3. **回滾機制**
   - 若驗證失敗，自動回滾 TiDB
   - 保留詳細錯誤日誌

---

### **方案 B：選擇性遷移** (備選)

僅遷移以下資料：
- ✅ 2024-2025 年的 profiles（579 筆）
- ✅ 58 位員工資料
- ❌ 跳過 2023 年資料（僅 1 筆，可忽略）

**優點**: 資料量更小，遷移風險更低
**缺點**: 遺失 2023 年歷史資料

---

### **方案 C：舊系統保留供查詢** (不建議)

- 新系統從 2026 年 1 月 1 日重新開始
- 舊系統 SQLite 保留於本機供查詢
- 提供跨系統查詢介面

**優點**: 無遷移風險
**缺點**:
- 資料分散，查詢不便
- 無法進行跨年度統計分析
- 違背統一管理的初衷

---

## 🛠️ 實作計畫

### 遷移腳本功能需求

#### `scripts/migrate_from_sqlite.py` 功能清單

1. **連線管理**
   ```python
   - 連接舊 SQLite 資料庫（唯讀）
   - 連接新 TiDB 資料庫（讀寫）
   ```

2. **資料讀取與過濾**
   ```python
   - 讀取 employees 資料表（58 筆）
   - 讀取 profiles 資料表並過濾（event_date < '2026-01-01'）
   - 讀取 event_investigation、personnel_interview 等子表
   - 讀取 assessment_standards（考核標準表）
   ```

3. **資料轉換**
   ```python
   - 補充 current_department = '淡海'
   - 解析 employee_id → hire_year_month
   - 轉換日期格式（確保相容 TiDB）
   - 處理 NULL 值
   ```

4. **資料驗證**
   ```python
   - 檢查員工編號唯一性
   - 檢查 profiles.employee_id 存在於 employees
   - 檢查日期範圍（2023-2025）
   - 檢查必填欄位非空
   ```

5. **批次插入**
   ```python
   - 先插入 employees（避免外鍵衝突）
   - 再插入 profiles
   - 再插入子表（event_investigation, personnel_interview）
   - 使用 Transaction 確保原子性
   ```

6. **進度顯示與日誌**
   ```python
   - 顯示即時進度（已處理 X / 總共 Y 筆）
   - 記錄成功、失敗、跳過的筆數
   - 產生詳細遷移報告（Markdown 格式）
   ```

7. **回滾機制**
   ```python
   - 遷移前建立 TiDB 快照備份
   - 若驗證失敗，自動執行 ROLLBACK
   - 提供手動回滾指令
   ```

---

### 遷移步驟（SOP）

#### 前置作業
1. **備份舊資料庫**
   ```bash
   cp driver_profiles.db driver_profiles.db.backup_$(date +%Y%m%d)
   ```

2. **備份新資料庫（TiDB）**
   ```bash
   mysqldump -h gateway01.ap-northeast-1.prod.aws.tidbcloud.com \
     -P 4000 -u 3SQWVrWh5DieHsr.root -p \
     --ssl-mode=VERIFY_IDENTITY \
     --databases test > tidb_backup_$(date +%Y%m%d).sql
   ```

3. **測試連線**
   ```bash
   python test_tidb_connection.py
   ```

#### 執行遷移
```bash
# 1. 乾跑模式（Dry Run）- 僅驗證不寫入
python scripts/migrate_from_sqlite.py --dry-run

# 2. 正式遷移
python scripts/migrate_from_sqlite.py --execute

# 3. 檢查遷移報告
cat logs/migration_report_20260128.md
```

#### 驗證結果
```python
# 檢查筆數
SELECT COUNT(*) FROM employees;  -- 應為 58
SELECT COUNT(*) FROM profiles WHERE event_date < '2026-01-01';  -- 應為 580

# 檢查部門分佈
SELECT current_department, COUNT(*) FROM employees GROUP BY current_department;
# 預期結果：淡海=58, 安坑=0

# 檢查入職年月解析
SELECT employee_id, hire_year_month FROM employees LIMIT 10;

# 檢查外鍵完整性
SELECT COUNT(*) FROM profiles p
WHERE NOT EXISTS (SELECT 1 FROM employees e WHERE e.employee_id = p.employee_id);
# 預期結果：0
```

---

## 📦 TiDB 儲存空間評估

### 估算依據
- **profiles**: 580 筆 × 1 KB/筆 ≈ 580 KB
- **employees**: 58 筆 × 0.5 KB/筆 ≈ 29 KB
- **event_investigation**: 404 筆 × 1 KB/筆 ≈ 404 KB
- **personnel_interview**: 177 筆 × 1 KB/筆 ≈ 177 KB
- **assessment_standards**: 85 筆 × 0.5 KB/筆 ≈ 43 KB
- **索引與元資料**: 約 200 KB

**總計**: 約 **1.4 MB**（僅佔 TiDB 5GB 限制的 0.03%）

### 結論
✅ **歷史資料遷移對 TiDB 儲存空間影響極小，完全可行**

---

## ⚠️ 風險與應對

| 風險項目 | 影響程度 | 應對措施 |
|---------|---------|---------|
| 部門判定錯誤 | 中 | 預設淡海，後續可手動調整 |
| 入職年月解析失敗 | 低 | 異常員工編號保留 NULL，手動補充 |
| 外鍵衝突 | 中 | 先插入 employees，再插入 profiles |
| 遷移中斷 | 高 | 使用 Transaction，失敗自動回滾 |
| 資料驗證失敗 | 中 | Dry Run 模式預先檢測 |

---

## 📅 時程估計

| 階段 | 預計時間 | 負責人 |
|------|---------|-------|
| 遷移腳本開發 | 2-3 天 | 開發者 |
| 測試與驗證 | 1 天 | 開發者 |
| 正式遷移執行 | 0.5 天 | 管理員 |
| 資料驗證與修正 | 0.5 天 | 管理員 |

**總計**: 約 **4-5 天**

---

## ✅ 建議採用方案

### **方案 A：完整遷移（預設淡海部門）**

**理由**:
1. ✅ 保留完整歷史資料（2023-2025），便於統計分析
2. ✅ 部門判定邏輯清晰（歷史資料 = 淡海）
3. ✅ 入職年月可從員工編號自動解析
4. ✅ 儲存空間影響極小（<2MB）
5. ✅ 提供完整的回滾機制，風險可控

**下一步**:
1. 使用者確認此方案
2. 開發 `scripts/migrate_from_sqlite.py` 遷移腳本
3. 執行 Dry Run 測試
4. 正式遷移並驗證

---

## 附錄：員工編號解析邏輯

### 格式說明
```
員工編號格式: YYMMX0XXX
範例: 1011M0095

解析規則:
- YY (前2碼): 入職年份 (10 → 2010年代)
- MM (3-4碼): 入職月份 (11 → 11月)
- X0XXX (後5碼): 流水號

結果: 1011M0095 → 2021年11月
```

### Python 實作
```python
import re

def parse_employee_hire_date(employee_id: str) -> str:
    """
    從員工編號解析入職年月

    Args:
        employee_id: 員工編號（如 1011M0095）

    Returns:
        入職年月（YYYY-MM 格式，如 "2021-11"）
        若解析失敗則返回 None
    """
    # 格式驗證：YYMMX0XXX（9碼以上）
    if not re.match(r'^\d{4}[A-Z]\d{4}$', employee_id):
        return None

    try:
        year_code = int(employee_id[:2])   # 10 → 10
        month_code = int(employee_id[2:4]) # 11 → 11

        # 轉換為西元年（假設 10-99 為 2010-2099）
        year = 2000 + year_code

        # 驗證月份有效性
        if not (1 <= month_code <= 12):
            return None

        return f"{year}-{month_code:02d}"

    except (ValueError, IndexError):
        return None

# 測試
print(parse_employee_hire_date("1011M0095"))  # 2021-11
print(parse_employee_hire_date("1108M0296"))  # 2021-08
print(parse_employee_hire_date("1207M0685"))  # 2022-07
```

---

**文件版本**: v1.0
**最後更新**: 2026-01-28
