# Phase 12: 考核系統資料模型設計

## 概述

Phase 12 考核系統包含以下核心功能：
1. 考核標準表管理（61 項標準）
2. 依類別累計加重機制
3. R02-R05 雙因子評分（延誤時間 × 責任程度）
4. 月度獎勵自動計算
5. 年度自動重置
6. 與履歷系統深度整合

---

## 資料模型

### 1. AssessmentStandard (考核標準主檔)

**用途**: 儲存所有考核項目的基本資料（61 項扣分 + 加分標準）

```python
class AssessmentStandard(Base):
    """考核標準主檔"""
    __tablename__ = "assessment_standards"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 基本資料
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    # 代碼，例如：D01, W02, S03, +M01, +A02, +R03

    category: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    # 類別：D, W, O, S, R, +M, +A, +B, +C, +R

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 項目名稱，例如：「遲到/早退」、「月度全勤」

    base_points: Mapped[float] = mapped_column(nullable=False)
    # 基本分數，例如：-1.0, -5.0, +3.0

    has_cumulative: Mapped[bool] = mapped_column(default=True)
    # 是否適用累計加重（D02 不適用，固定 False）

    calculation_cycle: Mapped[str] = mapped_column(String(20), default="yearly")
    # 計算週期：yearly（年度累計）、monthly（月度發放，如 +M01/+M02/+M03）

    description: Mapped[str | None] = mapped_column(Text)
    # 詳細說明

    # 狀態
    is_active: Mapped[bool] = mapped_column(default=True)
    # 是否啟用

    # 時間戳
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    records: Mapped[list["AssessmentRecord"]] = relationship(back_populates="standard")
```

**索引設計**:
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_code (code)` - 確保代碼唯一
- `INDEX idx_category (category)` - 加速依類別查詢
- `INDEX idx_is_active (is_active)` - 加速查詢啟用項目

**資料範例**:
```sql
INSERT INTO assessment_standards (code, category, name, base_points, has_cumulative, calculation_cycle) VALUES
('D01', 'D', '遲到/早退', -1.0, TRUE, 'yearly'),
('D02', 'D', '遲到但不影響勤務', 0, FALSE, 'yearly'),
('W02', 'W', '酒測不合格/未執行', -5.0, TRUE, 'yearly'),
('R02', 'R', '人為操作不當致需故障排除（未延誤）', -1.0, TRUE, 'yearly'),
('R03', 'R', '人為疏失延誤 90秒~5分鐘', -2.0, TRUE, 'yearly'),
('R04', 'R', '人為疏失延誤 5~10分鐘', -3.0, TRUE, 'yearly'),
('R05', 'R', '人為疏失延誤 超過10分鐘', -5.0, TRUE, 'yearly'),
('+M01', '+M', '月度全勤', 3.0, FALSE, 'monthly'),
('+M02', '+M', '月度行車零違規', 1.0, FALSE, 'monthly'),
('+M03', '+M', '月度全項目零違規', 2.0, FALSE, 'monthly');
```

---

### 2. AssessmentRecord (考核記錄)

**用途**: 儲存每筆考核扣分/加分記錄，包含累計倍率與最終分數

```python
class AssessmentRecord(Base):
    """考核記錄"""
    __tablename__ = "assessment_records"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 關聯
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    standard_code: Mapped[str] = mapped_column(ForeignKey("assessment_standards.code"), nullable=False, index=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profiles.id"), index=True)
    # 關聯到履歷（若透過履歷建立），NULL 表示手動建立或月度獎勵自動建立

    # 基本資料
    record_date: Mapped[date] = mapped_column(nullable=False, index=True)
    # 事件發生日期

    description: Mapped[str | None] = mapped_column(Text)
    # 事件描述

    # 分數計算
    base_points: Mapped[float] = mapped_column(nullable=False)
    # 基本分數（從 assessment_standards.base_points 複製）

    responsibility_coefficient: Mapped[float | None] = mapped_column(default=1.0)
    # 責任係數（僅 R02-R05 使用，一般項目為 1.0）
    # 完全責任: 1.0, 主要責任: 0.7, 次要責任: 0.3

    actual_points: Mapped[float] = mapped_column(nullable=False)
    # 實際扣分 = base_points × responsibility_coefficient

    cumulative_count: Mapped[int | None] = mapped_column()
    # 該類別年度累計次數（建立時的累計次數，如第 1 次、第 2 次）

    cumulative_multiplier: Mapped[float] = mapped_column(default=1.0)
    # 累計倍率 = 1 + 0.5 × (cumulative_count - 1)

    final_points: Mapped[float] = mapped_column(nullable=False)
    # 最終分數 = actual_points × cumulative_multiplier

    # 狀態
    is_deleted: Mapped[bool] = mapped_column(default=False)
    # 軟刪除標記

    # 時間戳
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column()

    # 關聯
    employee: Mapped["Employee"] = relationship(back_populates="assessment_records")
    standard: Mapped["AssessmentStandard"] = relationship(back_populates="records")
    profile: Mapped["Profile"] = relationship(back_populates="assessment_record")
    fault_responsibility: Mapped["FaultResponsibilityAssessment"] = relationship(
        back_populates="record", uselist=False
    )
```

**索引設計**:
- `PRIMARY KEY (id)`
- `INDEX idx_employee_date (employee_id, record_date DESC)` - 加速查詢員工考核記錄
- `INDEX idx_employee_year (employee_id, YEAR(record_date))` - 加速年度查詢
- `INDEX idx_standard (standard_code)` - 加速依項目查詢
- `INDEX idx_profile (profile_id)` - 關聯履歷查詢
- `INDEX idx_is_deleted (is_deleted)` - 加速軟刪除過濾

**計算範例**:
```python
# 範例 1: D01 遲到（第 2 次）
base_points = -1.0
responsibility_coefficient = 1.0  # 一般項目
actual_points = -1.0 × 1.0 = -1.0
cumulative_count = 2
cumulative_multiplier = 1 + 0.5 × (2 - 1) = 1.5
final_points = -1.0 × 1.5 = -1.5

# 範例 2: R04 主要責任（第 3 次）
base_points = -3.0
responsibility_coefficient = 0.7  # 主要責任
actual_points = -3.0 × 0.7 = -2.1
cumulative_count = 3
cumulative_multiplier = 1 + 0.5 × (3 - 1) = 2.0
final_points = -2.1 × 2.0 = -4.2
```

---

### 3. FaultResponsibilityAssessment (故障責任判定) ⭐ **新增**

**用途**: 儲存 R02-R05 責任判定的詳細資料（9 項疏失查核表結果）

```python
class FaultResponsibilityAssessment(Base):
    """故障責任判定（R02-R05 專用）"""
    __tablename__ = "fault_responsibility_assessments"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 關聯
    record_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_records.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    # 一對一關聯到 AssessmentRecord

    # 時間節點（用於計算延誤時間）
    time_t0: Mapped[datetime | None] = mapped_column()  # T0: 事件/故障發生
    time_t1: Mapped[datetime | None] = mapped_column()  # T1: 司機員察覺異常
    time_t2: Mapped[datetime | None] = mapped_column()  # T2: 開始通報/處理
    time_t3: Mapped[datetime | None] = mapped_column()  # T3: 故障排除完成
    time_t4: Mapped[datetime | None] = mapped_column()  # T4: 恢復正常運轉

    # 延誤時間
    delay_seconds: Mapped[int] = mapped_column(nullable=False)
    # 總延誤時間（秒），依 OCC 計算或 T4-T0

    # 9 項疏失查核結果（JSON 格式）
    checklist_results: Mapped[dict] = mapped_column(JSON, nullable=False)
    # 格式：
    # {
    #   "awareness_delay": true,         // 1. 察覺過晚或誤判
    #   "report_delay": false,           // 2. 通報延遲或不完整
    #   "unfamiliar_procedure": true,    // 3. 不熟悉故障排除程序
    #   "wrong_operation": true,         // 4. 故障排除決策/操作錯誤
    #   "slow_action": false,            // 5. 動作遲緩
    #   "unconfirmed_result": false,     // 6. 未確認結果或誤認完成
    #   "no_progress_report": true,      // 7. 未主動回報處理進度
    #   "repeated_error": false,         // 8. 重複性錯誤
    #   "mental_state_issue": false      // 9. 心理狀態影響表現
    # }

    # 責任判定結果
    fault_count: Mapped[int] = mapped_column(nullable=False)
    # 疏失項數（0-9），自動統計 checklist_results 中 true 的數量

    responsibility_level: Mapped[str] = mapped_column(String(20), nullable=False)
    # 責任程度：「完全責任」、「主要責任」、「次要責任」

    responsibility_coefficient: Mapped[float] = mapped_column(nullable=False)
    # 責任係數：1.0（完全）、0.7（主要）、0.3（次要）

    # 備註
    notes: Mapped[str | None] = mapped_column(Text)
    # 責任判定備註（選填）

    # 時間戳
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    record: Mapped["AssessmentRecord"] = relationship(back_populates="fault_responsibility")
```

**索引設計**:
- `PRIMARY KEY (id)`
- `UNIQUE INDEX idx_record (record_id)` - 確保一對一關聯
- `INDEX idx_responsibility_level (responsibility_level)` - 加速責任程度統計

**判定規則**:
```python
def determine_responsibility(fault_count: int) -> tuple[str, float]:
    """根據疏失項數判定責任程度"""
    if fault_count >= 7:
        return ("完全責任", 1.0)
    elif 4 <= fault_count <= 6:
        return ("主要責任", 0.7)
    elif 1 <= fault_count <= 3:
        return ("次要責任", 0.3)
    else:
        return ("無責任", 0.0)
```

**資料範例**:
```json
{
  "record_id": 123,
  "time_t0": "2026-02-15 10:30:00",
  "time_t4": "2026-02-15 10:37:00",
  "delay_seconds": 420,
  "checklist_results": {
    "awareness_delay": false,
    "report_delay": true,
    "unfamiliar_procedure": true,
    "wrong_operation": true,
    "slow_action": false,
    "unconfirmed_result": false,
    "no_progress_report": true,
    "repeated_error": false,
    "mental_state_issue": false
  },
  "fault_count": 4,
  "responsibility_level": "主要責任",
  "responsibility_coefficient": 0.7
}
```

---

### 4. CumulativeCounter (累計次數計數器) ⭐ **新增**

**用途**: 記錄每位員工每年度各類別的累計次數

```python
class CumulativeCounter(Base):
    """累計次數計數器（依類別獨立累計）"""
    __tablename__ = "cumulative_counters"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 關聯
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)

    # 累計範圍
    year: Mapped[int] = mapped_column(nullable=False)
    # 年度（如 2026）

    category: Mapped[str] = mapped_column(String(10), nullable=False)
    # 類別：D, W, O, S, R
    # 注意：R 類特殊，R02/R03/R04/R05 合併計算

    # 累計數據
    count: Mapped[int] = mapped_column(default=0, nullable=False)
    # 累計次數

    # 時間戳
    last_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    employee: Mapped["Employee"] = relationship(back_populates="cumulative_counters")

    # 複合唯一約束
    __table_args__ = (
        UniqueConstraint('employee_id', 'year', 'category', name='uq_employee_year_category'),
        Index('idx_employee_year', 'employee_id', 'year'),
    )
```

**索引設計**:
- `PRIMARY KEY (id)`
- `UNIQUE INDEX uq_employee_year_category (employee_id, year, category)` - 確保唯一性
- `INDEX idx_employee_year (employee_id, year)` - 加速年度查詢

**累計類別判定邏輯** ⭐ **P1 修正**:
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

**使用邏輯**:
```python
# 查詢員工 2026 年 D 類累計次數
standard_code = 'D01'
category = 'D'
cumulative_category = get_cumulative_category(standard_code, category)  # 返回 'D'

counter = db.query(CumulativeCounter).filter_by(
    employee_id=123,
    year=2026,
    category=cumulative_category
).first()

current_count = counter.count if counter else 0
next_count = current_count + 1

# 計算累計倍率
cumulative_multiplier = 1 + 0.5 * (next_count - 1)

# 更新累計次數
if counter:
    counter.count = next_count
else:
    db.add(CumulativeCounter(
        employee_id=123,
        year=2026,
        category=cumulative_category,
        count=next_count
    ))
```

**R 類合併計算範例**:
```python
# 範例：員工今年已有 R03 2次、R04 1次，則累計次數為 3
# 下次發生 R02 時，累計次數為 4（因為 R02 也在 R_CUMULATIVE_GROUP 中）

# R03 第1次
cumulative_category = get_cumulative_category('R03', 'R')  # 返回 'R'
# counter.count = 1

# R04 第1次（但 R 類合併，所以是第2次）
cumulative_category = get_cumulative_category('R04', 'R')  # 返回 'R'
# counter.count = 2

# R02 第1次（但 R 類合併，所以是第3次）
cumulative_category = get_cumulative_category('R02', 'R')  # 返回 'R'
# counter.count = 3

# 假設未來新增 R06（不在合併群組中）
cumulative_category = get_cumulative_category('R06', 'R')  # 返回 'R'（但不影響 R02-R05 的累計）
# 注意：若 R06 不應累計，需在 AssessmentStandard 設定 has_cumulative=False
```

---

### 5. MonthlyReward (月度獎勵記錄) ⭐ **新增**

**用途**: 記錄每位員工每月的月度獎勵發放情況

```python
class MonthlyReward(Base):
    """月度獎勵記錄"""
    __tablename__ = "monthly_rewards"

    # 主鍵
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 關聯
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)

    # 獎勵月份
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)
    # 格式：YYYY-MM，例如 "2026-01"

    # 獎勵項目
    full_attendance: Mapped[bool] = mapped_column(default=False)
    # +M01 月度全勤（+3 分，另外處理，此處僅記錄）

    driving_zero_violation: Mapped[bool] = mapped_column(default=False)
    # +M02 月度行車零違規（+1 分）
    # 條件：當月 R 類、S 類無任何扣分

    all_zero_violation: Mapped[bool] = mapped_column(default=False)
    # +M03 月度全項目零違規（+2 分）
    # 條件：當月所有類別（D/W/O/S/R）皆無扣分

    # 分數統計
    total_points: Mapped[float] = mapped_column(nullable=False)
    # 當月獎勵合計分數
    # 計算：full_attendance*3 + driving_zero_violation*1 + all_zero_violation*2

    # 時間戳
    calculated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    # 計算時間（通常為下個月 1 日凌晨）

    # 關聯
    employee: Mapped["Employee"] = relationship(back_populates="monthly_rewards")

    # 複合唯一約束
    __table_args__ = (
        UniqueConstraint('employee_id', 'year_month', name='uq_employee_year_month'),
        Index('idx_year_month', 'year_month'),
    )
```

**索引設計**:
- `PRIMARY KEY (id)`
- `UNIQUE INDEX uq_employee_year_month (employee_id, year_month)` - 確保每人每月僅一筆
- `INDEX idx_year_month (year_month)` - 加速月份查詢

**計算邏輯**:
```python
def calculate_monthly_rewards(year_month: str):
    """計算指定月份的月度獎勵"""
    year, month = map(int, year_month.split('-'))

    for employee in db.query(Employee).all():
        # 查詢當月考核記錄
        records = db.query(AssessmentRecord).join(AssessmentStandard).filter(
            AssessmentRecord.employee_id == employee.id,
            extract('year', AssessmentRecord.record_date) == year,
            extract('month', AssessmentRecord.record_date) == month,
            AssessmentRecord.is_deleted == False,
            AssessmentStandard.base_points < 0  # 僅查扣分項目
        ).all()

        # 判定各類別是否有扣分
        categories_with_deduction = {r.standard.category for r in records}

        # 判定 +M02（R、S 類零違規）
        driving_zero = not any(cat in ['R', 'S'] for cat in categories_with_deduction)

        # 判定 +M03（全類別零違規）
        all_zero = len(categories_with_deduction) == 0

        # 計算總分
        total = 0
        if driving_zero:
            total += 1  # +M02
        if all_zero:
            total += 2  # +M03

        # 儲存月度獎勵
        if total > 0:
            db.merge(MonthlyReward(
                employee_id=employee.id,
                year_month=year_month,
                driving_zero_violation=driving_zero,
                all_zero_violation=all_zero,
                total_points=total
            ))

            # 同時建立 AssessmentRecord
            if driving_zero:
                db.add(AssessmentRecord(
                    employee_id=employee.id,
                    standard_code='+M02',
                    record_date=date(year, month, 1),
                    base_points=1.0,
                    actual_points=1.0,
                    final_points=1.0
                ))
            if all_zero:
                db.add(AssessmentRecord(
                    employee_id=employee.id,
                    standard_code='+M03',
                    record_date=date(year, month, 1),
                    base_points=2.0,
                    actual_points=2.0,
                    final_points=2.0
                ))
```

---

### 6. Employee 擴充欄位

**用途**: 在 Employee 模型中新增考核相關欄位

```python
class Employee(Base):
    """員工資料（擴充）"""
    __tablename__ = "employees"

    # ... 原有欄位 ...

    # 考核分數
    current_score: Mapped[float] = mapped_column(default=80.0)
    # 當前考核分數（起始分數 80 分）

    # 關聯
    assessment_records: Mapped[list["AssessmentRecord"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    cumulative_counters: Mapped[list["CumulativeCounter"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    monthly_rewards: Mapped[list["MonthlyReward"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
```

---

### 7. Profile 擴充欄位（履歷系統整合）

**用途**: 在 Profile 模型中新增考核記錄關聯

```python
class Profile(Base):
    """履歷資料（擴充）"""
    __tablename__ = "profiles"

    # ... 原有欄位 ...

    # 關聯
    assessment_record: Mapped["AssessmentRecord"] = relationship(
        back_populates="profile", uselist=False
    )
    # 一對一關聯到考核記錄（若履歷建立時包含考核項目）
```

---

## 業務邏輯

### 1. 建立考核記錄流程

```python
def create_assessment_record(
    employee_id: int,
    standard_code: str,
    record_date: date,
    description: str = None,
    profile_id: int = None,
    fault_responsibility_data: dict = None  # R02-R05 專用
) -> AssessmentRecord:
    """建立考核記錄"""

    # 1. 查詢考核標準
    standard = db.query(AssessmentStandard).filter_by(code=standard_code).first()
    if not standard or not standard.is_active:
        raise ValueError(f"考核標準 {standard_code} 不存在或未啟用")

    # 2. 計算責任係數（R02-R05 專用）
    responsibility_coefficient = 1.0
    if standard_code in ['R02', 'R03', 'R04', 'R05'] and fault_responsibility_data:
        fault_count = sum(fault_responsibility_data['checklist_results'].values())
        if fault_count >= 7:
            responsibility_coefficient = 1.0
        elif 4 <= fault_count <= 6:
            responsibility_coefficient = 0.7
        elif 1 <= fault_count <= 3:
            responsibility_coefficient = 0.3

    # 3. 計算實際扣分
    actual_points = standard.base_points * responsibility_coefficient

    # 4. 查詢累計次數（依類別，使用明確判定邏輯）⭐ P1 修正
    year = record_date.year
    cumulative_category = get_cumulative_category(standard_code, standard.category)

    counter = db.query(CumulativeCounter).filter_by(
        employee_id=employee_id,
        year=year,
        category=cumulative_category
    ).first()

    current_count = counter.count if counter else 0
    next_count = current_count + 1 if standard.has_cumulative else 1

    # 5. 計算累計倍率
    cumulative_multiplier = 1.0
    if standard.has_cumulative:
        cumulative_multiplier = 1 + 0.5 * (next_count - 1)

    # 6. 計算最終分數
    final_points = actual_points * cumulative_multiplier

    # 7. 建立考核記錄
    record = AssessmentRecord(
        employee_id=employee_id,
        standard_code=standard_code,
        profile_id=profile_id,
        record_date=record_date,
        description=description,
        base_points=standard.base_points,
        responsibility_coefficient=responsibility_coefficient,
        actual_points=actual_points,
        cumulative_count=next_count if standard.has_cumulative else None,
        cumulative_multiplier=cumulative_multiplier,
        final_points=final_points
    )
    db.add(record)
    db.flush()

    # 8. 建立責任判定記錄（R02-R05 專用）
    if fault_responsibility_data:
        fault_count = sum(fault_responsibility_data['checklist_results'].values())
        if fault_count >= 7:
            responsibility_level = "完全責任"
        elif 4 <= fault_count <= 6:
            responsibility_level = "主要責任"
        else:
            responsibility_level = "次要責任"

        fault_assessment = FaultResponsibilityAssessment(
            record_id=record.id,
            time_t0=fault_responsibility_data.get('time_t0'),
            time_t1=fault_responsibility_data.get('time_t1'),
            time_t2=fault_responsibility_data.get('time_t2'),
            time_t3=fault_responsibility_data.get('time_t3'),
            time_t4=fault_responsibility_data.get('time_t4'),
            delay_seconds=fault_responsibility_data['delay_seconds'],
            checklist_results=fault_responsibility_data['checklist_results'],
            fault_count=fault_count,
            responsibility_level=responsibility_level,
            responsibility_coefficient=responsibility_coefficient
        )
        db.add(fault_assessment)

    # 9. 更新累計次數（使用 cumulative_category）⭐ P1 修正
    if standard.has_cumulative:
        if counter:
            counter.count = next_count
        else:
            db.add(CumulativeCounter(
                employee_id=employee_id,
                year=year,
                category=cumulative_category,
                count=next_count
            ))

    # 10. 更新員工總分
    employee = db.query(Employee).get(employee_id)
    employee.current_score += final_points

    db.commit()
    return record
```

### 2. 刪除/修改後重算流程

```python
def recalculate_cumulative_counts(employee_id: int, year: int, category: str):
    """
    重算員工該年度該類別的累計次數（Transaction）

    注意：category 應該是經過 get_cumulative_category() 處理後的值
    例如：R02/R03/R04/R05 應傳入 'R'，而非原始 category
    """

    with db.begin():  # 開始交易
        # 1. 鎖定該員工該年度該類別所有記錄
        # 注意：這裡的 category 是累計類別（R02-R05 已合併為 'R'）
        # 需要反向查詢所有屬於該累計類別的記錄
        if category == 'R':
            # R 類特殊處理：查詢所有 R02-R05 的記錄
            records = db.query(AssessmentRecord).join(AssessmentStandard).filter(
                AssessmentRecord.employee_id == employee_id,
                AssessmentRecord.is_deleted == False,
                extract('year', AssessmentRecord.record_date) == year,
                AssessmentStandard.code.in_(R_CUMULATIVE_GROUP),
                AssessmentStandard.has_cumulative == True
            ).order_by(
                AssessmentRecord.record_date
            ).with_for_update().all()  # 鎖定記錄
        else:
            # 一般類別：依 category 查詢
            records = db.query(AssessmentRecord).join(AssessmentStandard).filter(
                AssessmentRecord.employee_id == employee_id,
                AssessmentRecord.is_deleted == False,
                extract('year', AssessmentRecord.record_date) == year,
                AssessmentStandard.category == category,
                AssessmentStandard.has_cumulative == True
            ).order_by(
                AssessmentRecord.record_date
            ).with_for_update().all()  # 鎖定記錄

        # 2. 重新計算累計次數
        for idx, record in enumerate(records, start=1):
            cumulative_count = idx
            cumulative_multiplier = 1 + 0.5 * (cumulative_count - 1)

            # 重新計算實際扣分（考慮責任係數）
            actual_points = record.base_points * (record.responsibility_coefficient or 1.0)
            final_points = actual_points * cumulative_multiplier

            # 更新記錄
            record.cumulative_count = cumulative_count
            record.cumulative_multiplier = cumulative_multiplier
            record.final_points = final_points

        # 3. 更新累計次數計數器
        counter = db.query(CumulativeCounter).filter_by(
            employee_id=employee_id,
            year=year,
            category=category
        ).first()

        if counter:
            counter.count = len(records)
        elif len(records) > 0:
            db.add(CumulativeCounter(
                employee_id=employee_id,
                year=year,
                category=category,
                count=len(records)
            ))

        # 4. 重新計算員工總分 ⭐ P1 新增
        recalculate_employee_total_score(employee_id)
```

### 3. 履歷日期變更的連動重算流程 ⭐ **P1 新增（Gemini Review 建議）**

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
        # 1. 查詢履歷與關聯的考核記錄
        profile = db.query(Profile).get(profile_id)
        if not profile:
            raise ValueError(f"履歷 {profile_id} 不存在")

        old_date = profile.event_date
        old_year = old_date.year
        new_year = new_date.year

        # 2. 更新履歷日期
        profile.event_date = new_date

        # 3. 若有關聯的考核記錄，更新考核記錄日期
        if profile.assessment_record:
            assessment_record = profile.assessment_record
            old_category = get_cumulative_category(
                assessment_record.standard_code,
                assessment_record.standard.category
            )

            # 更新考核記錄日期
            assessment_record.record_date = new_date

            # 4. 跨年變更：重算兩個年度
            if old_year != new_year:
                # 重算舊年度（移除該筆後的狀態）
                recalculate_cumulative_counts(
                    profile.employee_id,
                    old_year,
                    old_category
                )
                # 重算新年度（新增該筆後的狀態）
                recalculate_cumulative_counts(
                    profile.employee_id,
                    new_year,
                    old_category
                )
            # 5. 同年變更：重算該年度
            else:
                recalculate_cumulative_counts(
                    profile.employee_id,
                    new_year,
                    old_category
                )

        db.commit()


def recalculate_employee_total_score(employee_id: int):
    """
    重新計算員工總分

    總分 = 起始分數 80 + 所有考核記錄的 final_points 總和
    """
    employee = db.query(Employee).get(employee_id)
    if not employee:
        raise ValueError(f"員工 {employee_id} 不存在")

    # 查詢所有未刪除的考核記錄
    records = db.query(AssessmentRecord).filter_by(
        employee_id=employee_id,
        is_deleted=False
    ).all()

    # 計算總分
    total_score = 80.0  # 起始分數
    for record in records:
        total_score += record.final_points

    # 更新員工分數
    employee.current_score = total_score
    db.commit()
```

**使用範例**:
```python
# 場景：將履歷日期從 2026-02-15 改為 2026-01-10
update_profile_date(profile_id=123, new_date=date(2026, 1, 10))

# 結果：
# 1. Profile.event_date 已更新為 2026-01-10
# 2. AssessmentRecord.record_date 已更新為 2026-01-10
# 3. 該員工 2026 年度該類別所有記錄的累計次數已重算
# 4. 員工總分已自動更新
```

### 4. 年度重置流程

```python
def annual_reset():
    """年度重置（每年 1/1 執行）"""

    with db.begin():
        # 1. 重置所有員工分數為 80 分
        db.query(Employee).update({'current_score': 80.0})

        # 2. 重置所有累計次數為 0
        db.query(CumulativeCounter).update({'count': 0})

        # 3. 歷史記錄保留不刪除

        db.commit()
```

---

## 履歷系統整合流程

### 建立 R02-R05 履歷時的完整流程

```python
def create_profile_with_assessment(
    employee_id: int,
    event_date: date,
    profile_type: str,  # 'EVENT_INVESTIGATION'
    assessment_code: str,  # 'R03'
    fault_responsibility_data: dict,  # 9 項查核表資料
    **profile_kwargs
) -> Profile:
    """建立包含考核的履歷"""

    # 1. 建立履歷基本資料
    profile = Profile(
        employee_id=employee_id,
        event_date=event_date,
        profile_type=profile_type,
        conversion_status='pending',
        **profile_kwargs
    )
    db.add(profile)
    db.flush()

    # 2. 建立考核記錄（含責任判定）
    assessment_record = create_assessment_record(
        employee_id=employee_id,
        standard_code=assessment_code,
        record_date=event_date,
        profile_id=profile.id,
        fault_responsibility_data=fault_responsibility_data
    )

    # 3. 產生 Word 文件時，自動包含責任判定結果
    # （在 document generation service 中實作）

    return profile
```

---

## 資料表關聯圖

```
Employee (員工)
  │
  ├─ 1:N ─> AssessmentRecord (考核記錄)
  │           │
  │           ├─ N:1 ─> AssessmentStandard (考核標準)
  │           ├─ N:1 ─> Profile (履歷，可為 NULL)
  │           └─ 1:1 ─> FaultResponsibilityAssessment (責任判定)
  │
  ├─ 1:N ─> CumulativeCounter (累計次數)
  └─ 1:N ─> MonthlyReward (月度獎勵)

Profile (履歷)
  └─ 1:1 ─> AssessmentRecord (考核記錄，可為 NULL)
```

---

## 資料遷移建議

### Phase 12 實作前準備

1. **建立考核標準主檔**: 匯入 61 項考核標準（從 Excel 匯入）
2. **初始化員工分數**: 所有員工 `current_score` 設為 80 分
3. **建立 2026 年累計次數計數器**: 為所有員工建立 D/W/O/S/R 五個類別的初始記錄（count=0）
4. **歷史資料處理**: 若需遷移舊系統考核記錄，需要重新計算累計次數

---

## 效能優化建議

1. **索引優化**: 所有查詢頻繁的欄位都已建立索引
2. **批次操作**: 月度獎勵計算使用批次插入
3. **快取策略**: 考核標準表可快取（變更頻率低）
4. **分頁查詢**: 考核記錄查詢使用分頁（避免一次載入過多資料）
5. **資料庫 Transaction**: 重算流程使用 FOR UPDATE 鎖定，確保並發安全

---

## 結語

此資料模型設計完整支援 Phase 12 的所有功能需求，包含：
- 61 項考核標準管理
- 依類別獨立累計加重機制
- R02-R05 雙因子評分與 9 項疏失查核
- 月度獎勵自動計算
- 年度自動重置
- 與履歷系統深度整合

所有欄位、索引、關聯關係、業務邏輯均已詳細定義，可直接用於實作。
