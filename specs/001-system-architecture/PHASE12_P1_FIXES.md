# Phase 12 P1 問題修正記錄

**修正日期**: 2026-01-30
**修正依據**: Gemini Code Review 審驗報告
**修正等級**: P1（重要，必須修改）

---

## 修正摘要

本次修正針對 Gemini 審驗報告中指出的兩個 P1 問題：

1. **R 類別累計範圍的模糊性**（P1-1）
2. **履歷日期變更的連動重算**（P1-2）

---

## P1-1: R 類別累計範圍的模糊性

### 問題描述

原始設計使用 `if category == 'R': category = 'R'` 判定 R 類合併，會導致**所有** category='R' 的項目都被合併計算。若未來新增 R01、R06 等非人為疏失的 R 類項目，會被錯誤納入累計。

### 修正方案

明確定義 R 類合併群組，使用白名單機制：

```python
# 明確定義 R 類合併群組（避免未來新增 R01、R06 時誤判）
R_CUMULATIVE_GROUP = {'R02', 'R03', 'R04', 'R05'}

def get_cumulative_category(standard_code: str, category: str) -> str:
    """
    取得累計計算的類別（處理 R 類特殊規則）

    規則：
    - R02/R03/R04/R05: 合併計算為 'R' 類別
    - 其他所有項目: 依原始類別獨立計算
    """
    if standard_code in R_CUMULATIVE_GROUP:
        return 'R'  # R02-R05 合併計算
    else:
        return category  # D, W, O, S 及其他 R 類項目各自獨立
```

### 修改的檔案

1. **data-model-phase12.md**
   - 新增 `get_cumulative_category()` 函數定義
   - 更新 `create_assessment_record()` 中的累計類別判定邏輯
   - 更新 `recalculate_cumulative_counts()` 中的查詢邏輯（區分 R 類與一般類別）
   - 新增 R 類合併計算範例

2. **spec.md**
   - 更新「累計類別規則」說明，明確標註「僅 R02-R05 合併」
   - 更新 FR-097，強調使用明確群組判定邏輯而非僅依賴 category

### 修正後的行為

| 考核代碼 | 原始 category | 累計類別 | 說明 |
|---------|--------------|---------|------|
| R02 | R | **R** | 合併計算 |
| R03 | R | **R** | 合併計算 |
| R04 | R | **R** | 合併計算 |
| R05 | R | **R** | 合併計算 |
| R01（未來可能新增） | R | **R01** | 獨立計算（未在 R_CUMULATIVE_GROUP 中） |
| R06（未來可能新增） | R | **R06** | 獨立計算（未在 R_CUMULATIVE_GROUP 中） |

---

## P1-2: 履歷日期變更的連動重算

### 問題描述

規格涵蓋了「刪除考核」、「修改責任判定」的重算，但**遺漏了「履歷日期變更」**的場景。累計是基於「年度」與「發生順序」，日期變更會影響所有後續記錄的累計倍率。

### 關鍵場景

```
原始狀態：
- 2026-01-15: D01 遲到（第1次，×1.0，-1分）
- 2026-02-20: D01 遲到（第2次，×1.5，-1.5分）

使用者將 2月的履歷改為 1月10日：
↓
重算後狀態：
- 2026-01-10: D01 遲到（第1次，×1.0，-1分）← 變成第1次
- 2026-01-15: D01 遲到（第2次，×1.5，-1.5分）← 原第1次變第2次，需重算！
```

### 修正方案

#### 1. 新增 Functional Requirements (FR-121 到 FR-125)

- **FR-121**: 履歷日期變更時，自動同步更新考核記錄日期
- **FR-122**: 考核記錄日期變更後，自動重算該年度該類別所有累計次數
- **FR-123**: 跨年變更時，同時重算兩個年度
- **FR-124**: 重算流程使用 Transaction + FOR UPDATE 鎖定
- **FR-125**: 重算完成後，重新計算員工總分

#### 2. 新增 Acceptance Scenarios (場景 28-33)

涵蓋以下測試場景：
- 同年日期變更
- 跨年日期變更
- 累計次數自動調整
- 員工總分自動更新
- 並發安全性保證

#### 3. 新增業務邏輯實作

```python
def update_profile_date(profile_id: int, new_date: date):
    """
    更新履歷日期並觸發考核記錄重算

    處理場景：
    1. 同年變更：重算該年度該類別所有記錄
    2. 跨年變更：重算兩個年度該類別所有記錄
    3. 並發安全：使用 Transaction + FOR UPDATE 鎖定
    """
    with db.begin():
        profile = db.query(Profile).get(profile_id)
        old_date = profile.event_date
        old_year = old_date.year
        new_year = new_date.year

        # 更新履歷日期
        profile.event_date = new_date

        # 更新考核記錄日期
        if profile.assessment_record:
            assessment_record = profile.assessment_record
            old_category = get_cumulative_category(
                assessment_record.standard_code,
                assessment_record.standard.category
            )
            assessment_record.record_date = new_date

            # 跨年變更：重算兩個年度
            if old_year != new_year:
                recalculate_cumulative_counts(profile.employee_id, old_year, old_category)
                recalculate_cumulative_counts(profile.employee_id, new_year, old_category)
            # 同年變更：重算該年度
            else:
                recalculate_cumulative_counts(profile.employee_id, new_year, old_category)

        db.commit()


def recalculate_employee_total_score(employee_id: int):
    """
    重新計算員工總分

    總分 = 起始分數 80 + 所有考核記錄的 final_points 總和
    """
    employee = db.query(Employee).get(employee_id)
    records = db.query(AssessmentRecord).filter_by(
        employee_id=employee_id,
        is_deleted=False
    ).all()

    total_score = 80.0
    for record in records:
        total_score += record.final_points

    employee.current_score = total_score
    db.commit()
```

### 修改的檔案

1. **spec.md**
   - 新增 FR-121 到 FR-125（履歷日期變更的連動重算）
   - 原 FR-121 到 FR-124 重新編號為 FR-126 到 FR-129
   - 新增 Acceptance Scenarios 場景 28-33（Section G）
   - 原場景 28-29 重新編號為 34-35（Section H）

2. **data-model-phase12.md**
   - 新增 `update_profile_date()` 函數實作
   - 新增 `recalculate_employee_total_score()` 函數實作
   - 更新 `recalculate_cumulative_counts()` 函數，在結尾處自動重算員工總分
   - 新增使用範例

### 修正後的資料流

```
履歷日期變更
  ↓
更新 Profile.event_date
  ↓
更新 AssessmentRecord.record_date
  ↓
判斷是否跨年
  ├─ 跨年 → 重算舊年度 + 重算新年度
  └─ 同年 → 重算該年度
  ↓
依 record_date 排序重新計算累計次數
  ↓
更新所有記錄的 cumulative_count, cumulative_multiplier, final_points
  ↓
重新計算員工總分（Employee.current_score）
  ↓
完成
```

---

## 修正影響範圍

### 影響的功能模組

1. **履歷管理模組** - 需新增日期變更觸發重算的邏輯
2. **考核記錄模組** - 需支援日期同步更新
3. **累計次數計算模組** - 需優化查詢邏輯（區分 R 類與一般類別）
4. **員工總分計算模組** - 需確保所有變更後都重算總分

### 影響的 API 端點

- `PATCH /api/profiles/{id}` - 更新履歷（含日期變更）
- `PATCH /api/assessment/records/{id}` - 更新考核記錄（含日期變更）

### 影響的資料表

- `profiles` - event_date 變更
- `assessment_records` - record_date 變更、累計次數重算
- `cumulative_counters` - count 更新
- `employees` - current_score 更新

---

## 測試建議

### 單元測試

1. **test_get_cumulative_category()**
   - 測試 R02-R05 返回 'R'
   - 測試其他 R 類項目返回原 category
   - 測試 D/W/O/S 類返回原 category

2. **test_update_profile_date_same_year()**
   - 同年變更，累計次數正確調整

3. **test_update_profile_date_cross_year()**
   - 跨年變更，兩個年度累計次數都正確

4. **test_recalculate_employee_total_score()**
   - 總分 = 80 + 所有 final_points 總和

### 整合測試

1. **並發日期變更測試**
   - 多個使用者同時修改同一員工的不同履歷日期
   - 驗證 Transaction 鎖定機制

2. **跨年邊界測試**
   - 12/31 → 1/1 的變更
   - 1/1 → 12/31 的變更

---

## 實作檢查清單

### Phase 12 實作時必須確認

- [ ] `get_cumulative_category()` 函數已實作
- [ ] `R_CUMULATIVE_GROUP` 常數已定義
- [ ] `update_profile_date()` API 已實作
- [ ] `recalculate_employee_total_score()` 函數已實作
- [ ] `recalculate_cumulative_counts()` 已更新（區分 R 類與一般類別）
- [ ] Profile 更新 API 包含日期變更觸發重算的邏輯
- [ ] Transaction + FOR UPDATE 鎖定機制已正確實作
- [ ] 所有單元測試與整合測試已通過

---

## 結論

透過本次 P1 修正，Phase 12 規格已達到：

1. **明確性**：R 類累計範圍使用白名單機制，避免歧義
2. **完整性**：涵蓋履歷日期變更的所有場景（同年、跨年、並發）
3. **一致性**：所有資料變更後都確保累計次數與總分正確
4. **可維護性**：未來新增考核項目時不會影響現有邏輯

規格現已符合 Gemini 審驗標準，可進入實作階段。

---

**修正完成日期**: 2026-01-30
**下一步**: 更新 tasks.md，根據新規格重新規劃任務
