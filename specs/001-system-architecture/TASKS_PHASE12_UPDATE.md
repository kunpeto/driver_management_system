# Phase 12 Tasks.md 更新記錄

**更新日期**: 2026-01-30
**更新依據**: Phase 12 規格修正（含 Gemini Review P1 修正）
**更新類型**: 完整重寫 Phase 12 任務列表

---

## 更新摘要

根據修正後的 Phase 12 規格（已整合 Gemini Review P1 修正），完整重寫了 tasks.md 中的 Phase 12 任務列表。

### 任務數量變化

- **原任務數**: 18 個（T159-T176）
- **更新後**: 34 個（T159-T192）
- **增加**: +16 個任務（+89%）

---

## 主要變更內容

### 1. 移除的功能

❌ **V1/V2 雙版本系統**
- 移除 T165（版本選擇服務）
- 移除相關的版本管理邏輯
- 理由：實際考核辦法不需要版本切換，統一使用 2026 年新規則

### 2. 新增的核心功能

#### A. R02-R05 雙因子評分機制 ⭐

**新增資料模型**:
- T161: FaultResponsibilityAssessment 模型（9 項疏失查核表、責任判定）

**新增服務**:
- T169: FaultResponsibilityService（計算疏失項數、判定責任程度）

**新增 API**:
- T179: R02-R05 責任判定 API（接收 9 項查核表、更新責任判定）

**新增前端元件**:
- T188: FaultResponsibilityChecklist 元件（時間節點、延誤秒數、9 項查核 checkbox）

---

#### B. 累計次數計數器 ⭐

**新增資料模型**:
- T162: CumulativeCounter 模型（employee_id + year + category → count）

**新增服務**:
- T167: 累計類別判定邏輯（R_CUMULATIVE_GROUP、get_cumulative_category()）⭐ **P1 修正**
- T168: 累計次數計算服務（支援 R 類合併計算）

---

#### C. 月度獎勵自動計算 ⭐

**新增資料模型**:
- T163: MonthlyReward 模型（+M01/+M02/+M03 發放記錄）

**新增服務**:
- T173: 月度獎勵計算服務（掃描當月考核、判定零違規、自動建立記錄）

**新增 API**:
- T181: 月度獎勵計算 API（觸發批次計算）

**新增前端頁面**:
- T190: MonthlyRewards 頁面（選擇年月、執行計算、顯示結果）

---

#### D. 年度重置機制 ⭐

**新增服務**:
- T174: 年度重置服務（每年 1/1 執行、重置分數與累計次數）

**新增 API**:
- T182: 年度重置 API（僅 Admin 可執行）

---

#### E. 履歷系統整合 ⭐

**新增服務**:
- T183: 擴充 ProfileService（create_with_assessment() 方法）

**新增前端整合**:
- T192: 整合履歷表單與責任判定（選擇 R02-R05 時自動顯示查核表）

**擴充 API**:
- T184: 擴充 Profile API（新增日期變更邏輯）

---

#### F. 履歷日期變更連動重算 ⭐ **P1 新增**

**新增服務**:
- T172: 履歷日期變更重算服務（同年/跨年自動重算、重新計算員工總分）

**擴充服務**:
- T171: 考核記錄重算服務（新增員工總分重算）

**依據**: Gemini Review 發現規格遺漏此場景

---

### 3. 更新的資料模型

#### 原有模型的欄位變更

**T159: AssessmentStandard** (原有，欄位更新)
- 原: `item_code, item_name, category, base_score, scoring_unit, apply_accumulation, custom_notes, is_active`
- 新: `code, category, name, base_points, has_cumulative, calculation_cycle, description, is_active`
- 變更: 欄位名稱統一、新增 calculation_cycle（區分 yearly/monthly）

**T160: AssessmentRecord** (原有，欄位大幅更新)
- 原: `employee_id, assessment_standard_id, event_date, base_score, accumulation_multiplier, weighted_score, occurrence_count, assessment_year, notes`
- 新: `employee_id, standard_code, profile_id (nullable), record_date, base_points, responsibility_coefficient (nullable), actual_points, cumulative_count, cumulative_multiplier, final_points, is_deleted`
- 新增: profile_id（履歷關聯）、responsibility_coefficient（責任係數）、actual_points（實際扣分）、final_points（最終分數）、is_deleted（軟刪除）
- 移除: assessment_year（改用 record_date 的 YEAR() 函數）

**新增模型擴充任務**:
- T164: 擴充 Employee 模型（current_score、關聯）
- T165: 擴充 Profile 模型（assessment_record 關聯）

---

## 任務編號對照表

| 原任務 | 新任務 | 變更說明 |
|--------|--------|---------|
| T159 | T159 | AssessmentStandard 模型（欄位更新） |
| T160 | T160 | AssessmentRecord 模型（欄位大幅更新） |
| - | T161 | **新增**: FaultResponsibilityAssessment 模型 |
| - | T162 | **新增**: CumulativeCounter 模型 |
| - | T163 | **新增**: MonthlyReward 模型 |
| - | T164 | **新增**: 擴充 Employee 模型 |
| - | T165 | **新增**: 擴充 Profile 模型 |
| T161 | T166 | AssessmentStandardService（功能擴充） |
| - | T167 | **新增**: 累計類別判定邏輯（P1 修正） |
| T162 | T168 | 累計次數計算服務（支援 R 類合併） |
| T163 | - | ❌ **移除**: 加重分數計算服務（併入 T170） |
| T164 | T170 | AssessmentRecordService（整合責任判定） |
| T165 | - | ❌ **移除**: 版本選擇服務 |
| T166 | T171 | 考核記錄重算服務（新增總分重算） |
| - | T169 | **新增**: FaultResponsibilityService |
| - | T172 | **新增**: 履歷日期變更重算服務（P1） |
| - | T173 | **新增**: 月度獎勵計算服務 |
| - | T174 | **新增**: 年度重置服務 |
| T167 | T175 | 考核標準 CRUD API |
| T168 | T176 | 考核標準 Excel 匯入 API |
| T169 | T177 | 考核標準搜尋 API |
| T170 | T178 | 考核記錄 CRUD API（整合責任判定） |
| - | T179 | **新增**: R02-R05 責任判定 API |
| T171 | T180 | 員工年度考核摘要 API |
| - | T181 | **新增**: 月度獎勵計算 API |
| - | T182 | **新增**: 年度重置 API |
| - | T183 | **新增**: 擴充 ProfileService |
| - | T184 | **新增**: 擴充 Profile API |
| T172 | T185 | 考核標準管理頁面 |
| T173 | T186 | 考核記錄列表頁面 |
| T174 | T187 | 考核記錄表單元件（自動偵測 R02-R05） |
| - | T188 | **新增**: R02-R05 責任判定查核表元件 |
| T175 | T189 | 員工年度考核摘要元件 |
| - | T190 | **新增**: 月度獎勵管理頁面 |
| T176 | T191 | 考核 Store |
| - | T192 | **新增**: 整合履歷表單與責任判定 |

---

## 並行任務更新

### 資料模型階段（可並行）

- **原**: T159, T160（2 個）
- **新**: T159-T165（7 個）⭐
- **新增**: T161（FaultResponsibilityAssessment）、T162（CumulativeCounter）、T163（MonthlyReward）、T164（Employee 擴充）、T165（Profile 擴充）

### 前端實作階段（可並行）

- **原**: T172-T175（4 個）
- **新**: T185-T190（6 個）⭐
- **新增**: T188（責任判定查核表）、T190（月度獎勵頁面）

---

## 分工計畫更新

### 開發者 A（後端核心邏輯）

**原**: T159-T166（資料模型 + 累計加重邏輯）
**新**: T159-T174（資料模型 + 核心服務）

**新增職責**:
- 責任判定服務（T169）
- 月度獎勵計算服務（T173）
- 年度重置服務（T174）
- 履歷日期變更重算服務（T172）

### 開發者 B（後端 API）

**原**: T167-T171（後端 API）
**新**: T175-T184（後端 API + 履歷整合）

**新增職責**:
- R02-R05 責任判定 API（T179）
- 月度獎勵計算 API（T181）
- 年度重置 API（T182）
- ProfileService 擴充（T183）
- Profile API 擴充（T184）

### 開發者 C（前端實作）

**原**: T172-T176（前端實作）
**新**: T185-T192（前端實作 + 履歷整合）

**新增職責**:
- 責任判定查核表元件（T188）
- 月度獎勵管理頁面（T190）
- 履歷表單與責任判定整合（T192）

---

## 執行里程碑更新

### Week 4: Phase 12（US9）考核系統

**原規劃**:
- 考核標準表管理
- 累計加重機制實作
- 雙版本並存（V1/V2）

**更新規劃**:
- 考核標準表管理（61 項標準）
- 依類別累計加重機制（**明確 R02-R05 合併**）⭐ P1 修正
- **R02-R05 雙因子評分**（9 項疏失查核表）⭐ 核心新增
- **月度獎勵自動計算**（+M02/+M03）⭐ 核心新增
- **履歷系統整合**（R02-R05 自動觸發責任判定）⭐ 核心新增
- **履歷日期變更連動重算**（同年/跨年）⭐ P1 新增

**Milestone**: 2026 年考核規則完整運作，**符合 Gemini Review 標準**

---

## Gemini Review P1 修正整合

### P1-1: R 類別累計範圍的模糊性

**問題**: 原 `if category == 'R': category = 'R'` 會誤將未來新增的 R01、R06 納入合併

**修正**:
- 明確定義 `R_CUMULATIVE_GROUP = {'R02', 'R03', 'R04', 'R05'}`
- 新增 `get_cumulative_category()` 函數

**影響任務**:
- T167: 累計類別判定邏輯（新增）
- T168: 累計次數計算服務（更新）

### P1-2: 履歷日期變更的連動重算

**問題**: 規格遺漏履歷日期變更場景，累計次數基於年度與發生順序

**修正**:
- 新增 `update_profile_date()` 函數（同年/跨年自動重算）
- 新增 `recalculate_employee_total_score()` 函數
- 新增 5 個 FR（FR-121 到 FR-125）
- 新增 6 個 Acceptance Scenarios（場景 28-33）

**影響任務**:
- T172: 履歷日期變更重算服務（新增）
- T171: 考核記錄重算服務（更新，新增總分重算）
- T184: 擴充 Profile API（新增日期變更邏輯）

---

## 總結

### 功能完整性提升

| 功能模組 | 原規格 | 更新後 |
|---------|--------|--------|
| 資料模型 | 2 個 | **7 個**（+5） |
| 後端服務 | 6 個 | **9 個**（+3） |
| 後端 API | 5 個 | **10 個**（+5） |
| 前端元件 | 5 個 | **8 個**（+3） |
| **總任務數** | **18 個** | **34 個**（+16） |

### 功能覆蓋度

✅ 61 項考核標準管理
✅ 依類別累計加重機制（明確 R02-R05 合併）
✅ R02-R05 雙因子評分（9 項疏失查核表）
✅ 月度獎勵自動計算（+M02/+M03 疊加）
✅ 年度自動重置（每年 1/1）
✅ 履歷系統整合（R02-R05 自動觸發責任判定）
✅ 履歷日期變更連動重算（同年/跨年）
✅ 員工總分自動同步
✅ 並發安全保證（Transaction + FOR UPDATE）

### 符合 Gemini Review 標準

✅ P1-1 修正：R 類累計範圍明確化
✅ P1-2 修正：履歷日期變更連動重算
✅ 資料一致性設計（Transaction 鎖定）
✅ 歷史可追溯性（冗餘欄位快照）
✅ 靈活擴展性（JSON 查核表）

---

**更新完成日期**: 2026-01-30
**下一步**: 開始實作 Phase 12（使用 `/speckit.implement Phase 12`）
