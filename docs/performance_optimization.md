# 效能優化建議

本文件記錄效能審查結果及優化建議。

---

## 後端效能優化

### 資料庫索引現況

目前已有的索引覆蓋率約 75%，主要表都有基本索引。

### 建議新增的索引（高優先級）

```sql
-- 1. 員工年度考核統計
CREATE INDEX ix_assessment_records_employee_category_year
ON assessment_records(employee_id, standard_code, record_date);

-- 2. 履歷部門日期範圍查詢
CREATE INDEX ix_profiles_dept_date_type
ON profiles(department, event_date, profile_type);

-- 3. 員工分類累計
CREATE INDEX ix_assessment_records_emp_category_year
ON assessment_records(employee_id, standard_code, is_deleted, record_date);

-- 4. 競賽排名查詢
CREATE INDEX ix_driving_comp_dept_period_qualified
ON driving_competitions(department, competition_year, competition_quarter, is_qualified);

-- 5. 累計類別查詢
CREATE INDEX ix_cumulative_emp_cat_year
ON cumulative_counters(employee_id, category, year);

-- 6. 月度獎勵查詢
CREATE INDEX ix_monthly_reward_employee_year
ON monthly_rewards(employee_id, year_month);
```

### N+1 查詢問題

**高風險場景（建議優化）：**

1. **Employee 模型的關聯**
   - `transfers`, `profiles`, `assessment_records`, `cumulative_counters`, `monthly_rewards`
   - 建議改為 `lazy="selectin"`

2. **Profile 的子表關聯**
   - `event_investigation`, `personnel_interview`, `corrective_measures`, `assessment_notice`, `assessment_record`
   - 建議改為 `lazy="selectin"`

3. **AssessmentRecord 的標準關聯**
   - `standard` 關聯
   - 建議改為 `lazy="selectin"`

### 查詢優化範例

```python
from sqlalchemy.orm import selectinload

# 優化前（N+1 問題）
profiles = session.query(Profile).filter_by(department='淡海').all()
for profile in profiles:
    print(profile.employee.name)  # N+1

# 優化後
profiles = session.query(Profile)\
    .options(selectinload(Profile.employee))\
    .filter_by(department='淡海')\
    .all()
```

---

## 前端效能優化

### 已實施

1. **路由 Lazy Loading** ✅
   - 所有 25 個路由都使用動態 import

2. **Code Splitting** ✅
   - vite.config.js 已配置 manualChunks
   - 分離 vue-vendor、element-plus、utils

3. **生產環境優化** ✅
   - 移除 console 和 debugger
   - 啟用 CSS 代碼分割

### 建議後續優化

1. **Element Plus 按需導入**
   ```javascript
   // 使用 unplugin-vue-components 自動按需導入
   import { ElMessage } from 'element-plus'
   ```

2. **圖標按需導入**
   ```javascript
   import { House, User, Calendar } from '@element-plus/icons-vue'
   ```

3. **添加圖片壓縮插件**
   ```bash
   npm install -D vite-plugin-imagemin
   ```

4. **添加 Gzip 壓縮**
   ```bash
   npm install -D vite-plugin-compression
   ```

---

## 安全性優化

### 已實施

1. **CORS 設定強化** ✅
   - 生產環境限制特定域名
   - 明確指定允許的 HTTP 方法
   - 明確指定允許的 Headers

### 安全措施現況

| 項目 | 狀態 |
|------|------|
| SQL 注入防護 | ✅ 完整（ORM 參數化查詢）|
| XSS 防護 | ✅ 完整（Pydantic 驗證）|
| 認證實作 | ✅ 完整（JWT + bcrypt）|
| 授權檢查 | ✅ 完整（角色+部門權限）|
| 敏感資料保護 | ✅ 完整（加密、日誌遮蔽）|
| CSRF 防護 | ✅ 已強化（CORS 設定）|
| Rate Limiting | ⚠️ 部分（僅文件生成 API）|

### 建議後續加強

1. **擴展 Rate Limiting**
   - 登入端點：10 次/分鐘
   - 使用者管理端點：20 次/分鐘

2. **添加安全 Headers**
   ```python
   # middleware 中添加
   response.headers["X-Content-Type-Options"] = "nosniff"
   response.headers["X-Frame-Options"] = "DENY"
   response.headers["Strict-Transport-Security"] = "max-age=31536000"
   ```

3. **Token 黑名單機制**
   - 使用 Redis 存儲已登出 Token
   - TTL 設定為 Token 剩餘有效時間

---

## 更新日期

2026-01-30
