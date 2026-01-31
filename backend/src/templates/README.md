# Office 文件模板說明

**最後更新**: 2026-01-30
**優化**: 全部改為 Word 格式，提升效能 2-3 倍

---

## 📁 **模板文件列表**

| 檔案名稱 | 用途 | 佔位符數量 | 格式 |
|---------|------|-----------|------|
| `personnel_interview.docx` | 人員訪談紀錄表 | 30 | Word |
| `event_investigation.docx` | 事件調查紀錄表 | 10 | Word |
| `corrective_measures.docx` | 事件矯正措施紀錄表 | 9 | Word |
| `assessment_notice_plus.docx` | 考核加分通知單 | 10 | Word ⭐ 新創建 |
| `assessment_notice_minus.docx` | 考核扣分通知單 | 9 | Word ⭐ 新創建 |

---

## 🔧 **佔位符格式**

所有模板使用統一的佔位符格式：`{variable_name}`

### **範例**：
```
{employee_name}  → 張三
{event_date}     → 2026-01-30
{assessment_score} → +3
```

---

## 📊 **各模板佔位符對應表**

### 1. 人員訪談紀錄表 (`personnel_interview.docx`)

#### 基本資訊
```python
{employee_name}      # 員工姓名
{employee_id}        # 員工編號
{hire_date}          # 到職日期
{event_date}         # 事件日期
```

#### 班表資訊（自動從 schedules 表查詢）
```python
{shift1}             # 事件當天班別
{shift2}             # 前 1 天班別
{shift3}             # 前 2 天班別
```

#### 訪談資訊
```python
{interviewer}        # 訪談人員
{interview_date}     # 訪談日期
{interview_content}  # 訪談內容
{incident_cause}     # 事故/事件經過
```

#### 訪談結果（勾選項目）
```python
{ir_1}  # □ 駕駛執照規定班別符合
{ir_2}  # □ 人員工作規定
{ir_3}  # □ 操作程序正確
{ir_4}  # □ 人員注意或作
{ir_5}  # □ 設備檢測正常
{ir_6}  # □ 人員規範熟練
{ir_7}  # □ 其他
{ir_other_text}  # 其他說明文字
```

#### 後續行動（勾選項目）
```python
{fa_1}  # □ 加強駕駛班前訓練
{fa_2}  # □ 列入駕駛缺點管
{fa_3}  # □ 培訓複訓
{fa_4}  # □ 追蹤作業執行
{fa_5}  # □ 設備維修
{fa_6}  # □ 人員改善教訓(簡訊/通知)
{fa_7}  # □ 其他
{fa_other_text}  # 其他說明文字
```

#### 考核關聯
```python
{assessment_item}    # 考核項目
{assessment_score}   # 考核分數
{conclusion}         # 結論
```

---

### 2. 事件調查紀錄表 (`event_investigation.docx`)

```python
# 基本資訊
{employee_name}      # 員工姓名
{event_date}         # 事件日期
{event_location}     # 事件地點
{train_number}       # 列車車號

# 事件詳情
{incident_cause}     # 事件發生時間/地點/經過/結果狀況
{incident_process}   # 由事件人員自述：1.異常發生原因 2.異常處理經過流程
{data_source}        # 調查來源
{improvement_suggestion}  # 調查人員改善建議

# 考核關聯
{assessment_item}    # 考核項目
{assessment_score}   # 加扣分
```

**新增欄位（支援 Phase 9 駕駛競賽統計）**:
```python
{has_responsibility}   # 是否歸責 (True/False)
{responsibility_ratio} # 責任比例 (0-100)
{category}             # 事件類別 (S/R/W/O/D)
```
*註：這些欄位在資料庫中，不一定顯示在文件中*

---

### 3. 事件矯正措施紀錄表 (`corrective_measures.docx`)

```python
# 基本資訊
{employee_name}      # 員工姓名
{event_date}         # 事件日期
{event_location}     # 事件地點
{train_number}       # 列車車號

# 事件分析
{incident_cause}     # 事件發生時間/地點/經過/結果狀況
{root_cause_analysis}    # 一、事件原因
{corrective_action}      # 二、矯正措施

# 考核關聯
{assessment_item}    # 考核項目
{assessment_score}   # 加扣分
```

---

### 4. 考核加分通知單 (`assessment_notice_plus.docx`) ⭐

```python
# 基本資訊
{employee_name}      # 姓名
{employee_id}        # 員編
{event_date}         # 事件日期
{event_time}         # 事件時間
{event_location}     # 事件地點

# 事件描述
{event_title}        # 事件標題
{event_description}  # 事件描述

# 查核資訊
# 查核來源：□ 路巡 / □ 監視器 / □ 旅客申訴 / □ 其他 (固定文字)
# 查核結果：空白欄位

# 考核項目
{assessment_item}    # 考核項目
{assessment_score}   # 加分

# 簽名欄位
# - 被考核人簽名（空白）
# - 考核人員簽名（空白）
# - 主管簽名（空白）

# 條碼
{barcode_id}         # 條碼編號 (例: 12345|AA|202601|V01)
```

---

### 5. 考核扣分通知單 (`assessment_notice_minus.docx`) ⭐

```python
# 與加分通知單相同，差異如下：

{data_source}        # 查核來源（扣分有此欄位，加分為固定勾選）
{assessment_score}   # 扣分（顯示為「扣分」而非「加分」）
```

---

## 🎯 **使用方式**

### Python 程式碼範例

```python
from docx import Document
from io import BytesIO

def generate_personnel_interview(profile_id: int) -> bytes:
    """生成人員訪談 Word 文件"""

    # 載入模板
    doc = Document('backend/src/templates/personnel_interview.docx')

    # 取得資料
    profile = get_profile(profile_id)
    interview = get_personnel_interview(profile_id)

    # 替換佔位符
    placeholders = {
        'employee_name': profile.employee_name,
        'employee_id': profile.employee_id,
        'hire_date': interview.hire_date.strftime('%Y-%m-%d'),
        'event_date': profile.event_date.strftime('%Y-%m-%d'),
        'shift1': interview.shift_event_day,
        'shift2': interview.shift_before_1day,
        'shift3': interview.shift_before_2days,
        'interviewer': interview.interviewer,
        'interview_date': interview.interview_date.strftime('%Y-%m-%d'),
        'interview_content': interview.interview_content,
        # ... 其他欄位
    }

    # 替換所有段落和表格中的佔位符
    for paragraph in doc.paragraphs:
        for key, value in placeholders.items():
            if f'{{{key}}}' in paragraph.text:
                paragraph.text = paragraph.text.replace(f'{{{key}}}', str(value))

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for key, value in placeholders.items():
                        if f'{{{key}}}' in paragraph.text:
                            paragraph.text = paragraph.text.replace(f'{{{key}}}', str(value))

    # 返回二進位流
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
```

---

## 🔄 **欄位映射邏輯** ⭐ **(Gemini Review 2026-01-30)**

### 資料模型更新

根據 Gemini Review 建議，資料模型已進行以下調整：

#### Profile 主表新增欄位
```python
# backend/src/models/profile.py
event_time = Column(Time, nullable=True)           # 事件時間
event_title = Column(String(200), nullable=True)   # 事件標題
data_source = Column(String(100), nullable=True)   # 資料來源/查核來源
assessment_item = Column(String(200), nullable=True)  # 考核項目
assessment_score = Column(Integer, nullable=True)     # 考核分數
```

**設計理由**：所有 Profile 類型（訪談、調查、矯正、考核通知）都可能需要考核資訊，將這些欄位提升至主表可確保資料一致性。

#### PersonnelInterview 新增欄位
```python
# backend/src/models/personnel_interview.py
interview_result_data = Column(JSON, nullable=True)    # 訪談結果勾選
follow_up_action_data = Column(JSON, nullable=True)    # 後續行動勾選
conclusion = Column(Text, nullable=True)               # 結論
```

**JSON 格式範例**：
```json
// interview_result_data
{
  "ir_1": true,   // 駕駛執照規定班別符合
  "ir_2": false,  // 人員工作規定
  "ir_3": true,   // 操作程序正確
  "ir_4": false,  // 人員注意或作
  "ir_5": true,   // 設備檢測正常
  "ir_6": false,  // 人員規範熟練
  "ir_7": false,  // 其他
  "ir_other_text": ""
}

// follow_up_action_data
{
  "fa_1": true,   // 加強駕駛班前訓練
  "fa_2": false,  // 列入駕駛缺點管
  "fa_3": true,   // 培訓複訓
  "fa_4": false,  // 追蹤作業執行
  "fa_5": false,  // 設備維修
  "fa_6": true,   // 人員改善教訓
  "fa_7": false,  // 其他
  "fa_other_text": ""
}
```

### 佔位符與資料庫欄位映射表

| 模板佔位符 | 資料來源 | 說明 |
|-----------|---------|------|
| `{employee_name}` | `Employee.name` (透過 Profile.employee_id 關聯) | 員工姓名 |
| `{employee_id}` | `Employee.employee_id` | 員工編號 |
| `{hire_date}` | `Employee.hire_date` 或 `PersonnelInterview.hire_date` | 到職日期 |
| `{event_date}` | `Profile.event_date` | 事件日期 |
| `{event_time}` | `Profile.event_time` ⭐ **新增** | 事件時間 |
| `{event_location}` | `Profile.event_location` | 事件地點 |
| `{train_number}` | `Profile.train_number` | 列車車號 |
| `{event_title}` | `Profile.event_title` ⭐ **新增** | 事件標題 |
| `{event_description}` | `Profile.event_description` | 事件描述 |
| `{data_source}` | `Profile.data_source` ⭐ **新增** | 查核來源 |
| `{assessment_item}` | `Profile.assessment_item` ⭐ **新增** | 考核項目 |
| `{assessment_score}` | `Profile.assessment_score` ⭐ **新增** | 考核分數 |
| `{shift1}` | `PersonnelInterview.shift_event_day` | 事件當天班別 |
| `{shift2}` | `PersonnelInterview.shift_before_1day` | 前1天班別 |
| `{shift3}` | `PersonnelInterview.shift_before_2days` | 前2天班別 |
| `{interviewer}` | `PersonnelInterview.interviewer` | 訪談人員 |
| `{interview_date}` | `PersonnelInterview.interview_date` | 訪談日期 |
| `{interview_content}` | `PersonnelInterview.interview_content` | 訪談內容 |
| `{ir_1}` ~ `{ir_7}` | `PersonnelInterview.interview_result_data` (JSON) ⭐ **新增** | 訪談結果勾選 |
| `{ir_other_text}` | `PersonnelInterview.interview_result_data.ir_other_text` | 其他說明 |
| `{fa_1}` ~ `{fa_7}` | `PersonnelInterview.follow_up_action_data` (JSON) ⭐ **新增** | 後續行動勾選 |
| `{fa_other_text}` | `PersonnelInterview.follow_up_action_data.fa_other_text` | 其他說明 |
| `{conclusion}` | `PersonnelInterview.conclusion` ⭐ **新增** | 結論 |
| `{incident_cause}` | 映射邏輯：優先 `EventInvestigation.cause_analysis`，否則 `Profile.event_description` | 事件經過 |
| `{incident_process}` | `EventInvestigation.process_description` | 處理過程 |
| `{improvement_suggestion}` | `EventInvestigation.improvement_suggestions` | 改善建議 |
| `{root_cause_analysis}` | `EventInvestigation.cause_analysis` | 原因分析 |
| `{corrective_action}` | `CorrectiveMeasures.corrective_actions` | 矯正措施 |
| `{barcode_id}` | 動態生成：`{profile_id}\|{type_code}\|{YYYYMM}\|V{version}` | 條碼編號 |

### 勾選框轉換邏輯

在生成 Word 文件時，需要將 JSON 中的 Boolean 值轉換為勾選符號：

```python
def convert_checkbox(value: bool) -> str:
    """將布林值轉換為勾選符號"""
    return "V" if value else ""  # 或使用 Unicode: "☑" / "☐"
```

---

## ⚠️ **注意事項**

1. **編碼問題**：
   - 所有模板使用 UTF-8 編碼
   - 中文字型設定為「標楷體」

2. **佔位符命名規範**：
   - 使用小寫蛇形命名法（snake_case）
   - 與資料庫欄位名稱對應

3. **條碼嵌入**：
   - 條碼編號欄位：`{barcode_id}`
   - 實際條碼圖片需使用 `python-barcode` 生成後插入

4. **簽名欄位**：
   - 預留空白儲存格供手寫簽名
   - 或使用電子簽名圖片插入

---

## 📝 **版本歷史**

| 日期 | 版本 | 變更內容 |
|------|------|---------|
| 2026-01-30 | 2.1 | Gemini Review 修正：新增欄位映射邏輯、Profile 主表擴充、PersonnelInterview JSON 欄位 |
| 2026-01-30 | 2.0 | 將考核通知單從 Excel 改為 Word，提升效能 2-3 倍 |
| 2026-01-13 | 1.0 | 初始版本（原專案格式） |

---

## 🔗 **相關文件**

- 資料模型定義：`backend/src/models/`
- Office 文件生成服務：`backend/src/services/office_document_service.py`
- 條碼生成服務：`backend/src/services/barcode_service.py`
- API 端點：`backend/src/api/profiles.py`
