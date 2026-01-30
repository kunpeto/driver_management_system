"""
履歷 API 端點
對應 tasks.md T141-T145: 實作履歷相關 API
對應 spec.md: User Story 8 - 司機員事件履歷管理系統

API 端點：
- T141: GET/POST/PUT/DELETE /api/profiles
- T142: POST /api/profiles/{id}/convert
- T143: POST /api/profiles/{id}/generate-document
- T144: GET /api/profiles/schedule-lookup
- T145: GET /api/profiles/search

Gemini Review 優化:
- Rate Limiting 加入文件生成 API（防止 OOM）
- 重置為 Basic 功能（提升操作彈性）
"""

from datetime import date, time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import (
    PermissionChecker,
    require_role,
    Role,
)
from src.models import (
    AssessmentType,
    ConversionStatus,
    Employee,
    ProfileType,
)
from src.services.profile_service import (
    EmployeeNotFoundError,
    InvalidConversionError,
    ProfileNotFoundError,
    ProfileService,
)
from src.services.pending_profile_service import (
    PendingProfileService,
    get_pending_profile_service,
)
from src.services.pdf_upload_service import (
    PdfUploadService,
    get_pdf_upload_service,
)
from src.services.profile_policy import ProfilePolicy
from src.services.schedule_lookup_service import (
    ScheduleLookupService,
    EmployeeNotFoundError as ScheduleEmployeeNotFoundError,
)
from src.services.office_document_service import (
    OfficeDocumentService,
    InvalidProfileTypeError,
    TemplateNotFoundError,
)
from src.services.profile_date_updater import ProfileDateUpdaterService

router = APIRouter()

# Rate Limiter 設置（Gemini Review P0: 防止 OOM）
# 使用 IP 地址作為限制鍵，文件生成限制每分鐘 5 次
limiter = Limiter(key_func=get_remote_address)


# ============================================================
# Pydantic 模型
# ============================================================

class ProfileCreate(BaseModel):
    """建立履歷請求"""
    employee_id: int = Field(..., description="員工 ID")
    event_date: date = Field(..., description="事件日期")
    department: str = Field(..., description="部門")
    event_location: Optional[str] = Field(None, max_length=100, description="事件地點")
    train_number: Optional[str] = Field(None, max_length=20, description="列車車號")
    event_title: Optional[str] = Field(None, max_length=200, description="事件標題")
    event_description: Optional[str] = Field(None, description="事件描述")
    event_time: Optional[str] = Field(None, description="事件時間 (HH:MM)")
    data_source: Optional[str] = Field(None, max_length=100, description="資料來源")
    assessment_item: Optional[str] = Field(None, max_length=200, description="考核項目")
    assessment_score: Optional[int] = Field(None, description="考核分數")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "employee_id": 1,
                    "event_date": "2026-01-15",
                    "department": "淡海",
                    "event_location": "淡水站",
                    "train_number": "1234",
                    "event_description": "事件描述內容"
                }
            ]
        }
    }


class ProfileUpdate(BaseModel):
    """更新履歷請求"""
    event_date: Optional[date] = None
    event_location: Optional[str] = Field(None, max_length=100)
    train_number: Optional[str] = Field(None, max_length=20)
    event_title: Optional[str] = Field(None, max_length=200)
    event_description: Optional[str] = None
    event_time: Optional[str] = None
    data_source: Optional[str] = Field(None, max_length=100)
    assessment_item: Optional[str] = Field(None, max_length=200)
    assessment_score: Optional[int] = None


class EventInvestigationData(BaseModel):
    """事件調查資料"""
    incident_time: Optional[str] = None
    incident_location: Optional[str] = None
    witnesses: Optional[str] = None
    cause_analysis: Optional[str] = None
    process_description: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    investigator: Optional[str] = None
    investigation_date: Optional[date] = None
    has_responsibility: Optional[bool] = None
    responsibility_ratio: Optional[int] = Field(None, ge=0, le=100)
    category: Optional[str] = Field(None, pattern="^[SRWOD]$")


class PersonnelInterviewData(BaseModel):
    """人員訪談資料"""
    hire_date: Optional[date] = None
    shift_before_2days: Optional[str] = None
    shift_before_1day: Optional[str] = None
    shift_event_day: Optional[str] = None
    interview_content: Optional[str] = None
    interviewer: Optional[str] = None
    interview_date: Optional[date] = None
    interview_result_data: Optional[dict[str, Any]] = None
    follow_up_action_data: Optional[dict[str, Any]] = None
    conclusion: Optional[str] = None


class CorrectiveMeasuresData(BaseModel):
    """矯正措施資料"""
    event_summary: Optional[str] = None
    corrective_actions: Optional[str] = None
    responsible_person: Optional[str] = None
    completion_deadline: Optional[date] = None
    completion_status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed)$")


class AssessmentNoticeData(BaseModel):
    """考核通知資料"""
    assessment_type: str = Field(..., pattern="^(加分|扣分)$")
    assessment_item: Optional[str] = None
    assessment_score: Optional[int] = None
    issue_date: Optional[date] = None
    approver: Optional[str] = None


class ProfileConvert(BaseModel):
    """履歷類型轉換請求"""
    target_type: str = Field(
        ...,
        description="目標類型: event_investigation, personnel_interview, corrective_measures, assessment_notice"
    )
    event_investigation: Optional[EventInvestigationData] = None
    personnel_interview: Optional[PersonnelInterviewData] = None
    corrective_measures: Optional[CorrectiveMeasuresData] = None
    assessment_notice: Optional[AssessmentNoticeData] = None


# ============================================================
# Phase 12 整合：考核系統（T183, T184）
# ============================================================

class FaultResponsibilityChecklistData(BaseModel):
    """9 項疏失查核結果"""
    awareness_delay: bool = Field(False, description="1. 察覺過晚或誤判")
    report_delay: bool = Field(False, description="2. 通報延遲或不完整")
    unfamiliar_procedure: bool = Field(False, description="3. 不熟悉故障排除程序")
    wrong_operation: bool = Field(False, description="4. 故障排除決策/操作錯誤")
    slow_action: bool = Field(False, description="5. 動作遲緩")
    unconfirmed_result: bool = Field(False, description="6. 未確認結果或誤認完成")
    no_progress_report: bool = Field(False, description="7. 未主動回報處理進度")
    repeated_error: bool = Field(False, description="8. 重複性錯誤")
    mental_state_issue: bool = Field(False, description="9. 心理狀態影響表現")


class ProfileFaultResponsibilityData(BaseModel):
    """R02-R05 責任判定資料"""
    delay_seconds: int = Field(..., ge=0, description="延誤時間（秒）")
    checklist_results: FaultResponsibilityChecklistData = Field(..., description="9 項疏失查核結果")
    time_t0: Optional[str] = Field(None, description="T0: 事件/故障發生時間")
    time_t1: Optional[str] = Field(None, description="T1: 司機員察覺異常時間")
    time_t2: Optional[str] = Field(None, description="T2: 開始通報/處理時間")
    time_t3: Optional[str] = Field(None, description="T3: 故障排除完成時間")
    time_t4: Optional[str] = Field(None, description="T4: 恢復正常運轉時間")
    notes: Optional[str] = Field(None, description="備註")


class ProfileCreateWithAssessment(BaseModel):
    """建立履歷並同時建立考核記錄請求（Phase 12）"""
    employee_id: int = Field(..., description="員工 ID")
    event_date: date = Field(..., description="事件日期")
    department: str = Field(..., description="部門")
    assessment_code: str = Field(..., max_length=10, description="考核代碼（如 D01, R03）")
    event_location: Optional[str] = Field(None, max_length=100, description="事件地點")
    train_number: Optional[str] = Field(None, max_length=20, description="列車車號")
    event_title: Optional[str] = Field(None, max_length=200, description="事件標題")
    event_description: Optional[str] = Field(None, description="事件描述")
    event_time: Optional[str] = Field(None, description="事件時間 (HH:MM)")
    data_source: Optional[str] = Field(None, max_length=100, description="資料來源")
    fault_responsibility_data: Optional[ProfileFaultResponsibilityData] = Field(
        None, description="R02-R05 責任判定資料（R02-R05 必填）"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "employee_id": 1,
                    "event_date": "2026-01-15",
                    "department": "淡海",
                    "assessment_code": "R03",
                    "event_description": "人為疏失延誤 3 分鐘",
                    "fault_responsibility_data": {
                        "delay_seconds": 180,
                        "checklist_results": {
                            "awareness_delay": True,
                            "report_delay": False,
                            "unfamiliar_procedure": True,
                            "wrong_operation": False,
                            "slow_action": True,
                            "unconfirmed_result": False,
                            "no_progress_report": False,
                            "repeated_error": False,
                            "mental_state_issue": False
                        }
                    }
                }
            ]
        }
    }


class ProfileUpdateDate(BaseModel):
    """履歷日期變更請求（Phase 12 T184）"""
    new_date: date = Field(..., description="新的事件日期")


class ProfileWithAssessmentResponse(BaseModel):
    """建立履歷並考核記錄的回應"""
    profile: ProfileResponse
    assessment_record: dict
    responsibility_assessment: Optional[dict] = None


class ProfileResponse(BaseModel):
    """履歷回應"""
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    profile_type: str
    event_date: date
    event_time: Optional[str] = None
    event_location: Optional[str] = None
    train_number: Optional[str] = None
    event_title: Optional[str] = None
    event_description: Optional[str] = None
    data_source: Optional[str] = None
    assessment_item: Optional[str] = None
    assessment_score: Optional[int] = None
    conversion_status: str
    file_path: Optional[str] = None
    gdrive_link: Optional[str] = None
    department: str
    document_version: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ScheduleLookupResponse(BaseModel):
    """班表查詢回應"""
    shift_before_2days: Optional[str] = None
    shift_before_1day: Optional[str] = None
    shift_event_day: Optional[str] = None
    source: str = "local"


class PendingStatsResponse(BaseModel):
    """未結案統計回應（T186 增強）"""
    total: int
    by_type: dict[str, int]
    oldest_pending_date: Optional[date] = None
    this_month_completed: int = 0
    this_month_total: int = 0
    completion_rate: float = 0.0


class UploadParamsResponse(BaseModel):
    """上傳參數回應（T190）"""
    profile_id: int
    profile_type: str
    employee_id: str
    employee_name: str
    event_date: Optional[date] = None
    department: str
    suggested_folder_name: str
    suggested_file_name: str
    can_upload: bool
    error_message: Optional[str] = None


# ============================================================
# T141: 履歷 CRUD API
# ============================================================

@router.get("", response_model=list[ProfileResponse])
async def get_profiles(
    department: Optional[str] = Query(None, description="部門篩選"),
    profile_type: Optional[str] = Query(None, description="類型篩選"),
    conversion_status: Optional[str] = Query(None, description="狀態篩選"),
    employee_id: Optional[int] = Query(None, description="員工 ID 篩選"),
    date_from: Optional[date] = Query(None, description="起始日期"),
    date_to: Optional[date] = Query(None, description="結束日期"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=500, description="取得筆數"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    取得履歷列表

    支援部門、類型、狀態、日期等多維度篩選。
    """
    service = ProfileService(db)

    # 使用 Policy 過濾部門（Gemini Review P2）
    department = ProfilePolicy.filter_department(
        current_user.role, current_user.department, department
    )

    profiles = service.get_list(
        department=department,
        profile_type=profile_type,
        conversion_status=conversion_status,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )

    return [_profile_to_response(p) for p in profiles]


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    建立基本履歷
    """
    service = ProfileService(db)

    # Staff 只能建立自己部門的履歷
    department = data.department
    if current_user.role == Role.STAFF.value:
        department = current_user.department

    try:
        profile = service.create(
            employee_id=data.employee_id,
            event_date=data.event_date,
            department=department,
            event_location=data.event_location,
            train_number=data.train_number,
            event_title=data.event_title,
            event_description=data.event_description,
            event_time=data.event_time,
            data_source=data.data_source,
            assessment_item=data.assessment_item,
            assessment_score=data.assessment_score,
        )
        return _profile_to_response(profile)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    取得單一履歷
    """
    service = ProfileService(db)
    profile = service.get_by_id(profile_id)

    if not profile:
        raise HTTPException(status_code=404, detail="履歷不存在")

    # 使用 Policy 檢查權限（Gemini Review P2）
    if not ProfilePolicy.can_view(
        current_user.role, current_user.department, profile
    ):
        raise HTTPException(status_code=403, detail="無權限查看此履歷")

    return _profile_to_response(profile)


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: int,
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    更新履歷
    """
    service = ProfileService(db)

    # 檢查權限（使用 Policy，Gemini Review P2）
    profile = service.get_by_id(profile_id, load_relations=False)
    if not profile:
        raise HTTPException(status_code=404, detail="履歷不存在")

    if not ProfilePolicy.can_edit(
        current_user.role, current_user.department, profile
    ):
        raise HTTPException(status_code=403, detail="無權限編輯此履歷")

    try:
        updated = service.update(
            profile_id,
            **data.model_dump(exclude_unset=True)
        )
        return _profile_to_response(updated)
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_role([Role.ADMIN, Role.MANAGER])),
):
    """
    刪除履歷（僅管理員和主管可操作）
    """
    service = ProfileService(db)

    try:
        service.delete(profile_id)
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# T142: 履歷類型轉換 API
# ============================================================

@router.post("/{profile_id}/convert", response_model=ProfileResponse)
async def convert_profile(
    profile_id: int,
    data: ProfileConvert,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    轉換履歷類型

    規則：
    - 僅允許 basic → 其他類型
    - 已完成履歷不可轉換
    """
    service = ProfileService(db)

    # 檢查權限（使用 Policy，Gemini Review P2）
    profile = service.get_by_id(profile_id, load_relations=False)
    if not profile:
        raise HTTPException(status_code=404, detail="履歷不存在")

    if not ProfilePolicy.can_convert(
        current_user.role, current_user.department, profile
    ):
        raise HTTPException(status_code=403, detail="無權限轉換此履歷")

    # 準備子表資料
    sub_table_data = {}
    if data.target_type == ProfileType.EVENT_INVESTIGATION.value and data.event_investigation:
        sub_table_data = data.event_investigation.model_dump(exclude_unset=True)
    elif data.target_type == ProfileType.PERSONNEL_INTERVIEW.value and data.personnel_interview:
        sub_table_data = data.personnel_interview.model_dump(exclude_unset=True)
    elif data.target_type == ProfileType.CORRECTIVE_MEASURES.value and data.corrective_measures:
        sub_table_data = data.corrective_measures.model_dump(exclude_unset=True)
    elif data.target_type == ProfileType.ASSESSMENT_NOTICE.value and data.assessment_notice:
        sub_table_data = data.assessment_notice.model_dump(exclude_unset=True)

    try:
        converted = service.convert_type(
            profile_id=profile_id,
            target_type=data.target_type,
            sub_table_data=sub_table_data,
        )
        return _profile_to_response(converted)
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidConversionError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 重置為 Basic API（Gemini Review P1）
# ============================================================

@router.post("/{profile_id}/reset", response_model=ProfileResponse)
async def reset_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    重置履歷為基本類型

    刪除子表資料，將類型改回 basic，狀態改回 pending。
    適用於選錯類型需要重新轉換的情況。

    規則（Gemini Review P1）：
    - 已完成履歷不可重置
    - 基本履歷不需要重置
    """
    service = ProfileService(db)

    # 檢查權限（使用 Policy，Gemini Review P2）
    profile = service.get_by_id(profile_id, load_relations=False)
    if not profile:
        raise HTTPException(status_code=404, detail="履歷不存在")

    if not ProfilePolicy.can_reset(
        current_user.role, current_user.department, profile
    ):
        raise HTTPException(status_code=403, detail="無權限重置此履歷")

    try:
        reset = service.reset_to_basic(profile_id)
        return _profile_to_response(reset)
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidConversionError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# T143: Office 文件生成 API
# ============================================================

@router.post("/{profile_id}/generate-document")
@limiter.limit("5/minute")
async def generate_document(
    request: Request,
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    生成 Office 文件

    返回 Word 文件流，供瀏覽器直接下載。

    Rate Limit: 每用戶每分鐘 5 次請求（Gemini Review P0）
    """
    profile_service = ProfileService(db)
    doc_service = OfficeDocumentService()

    # 取得履歷（含子表）
    profile = profile_service.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="履歷不存在")

    # 使用 Policy 檢查權限（Gemini Review P2）
    if not ProfilePolicy.can_generate_document(
        current_user.role, current_user.department, profile
    ):
        raise HTTPException(status_code=403, detail="無權限存取此履歷")

    # 取得員工
    employee = profile.employee
    if not employee:
        raise HTTPException(status_code=404, detail="關聯員工不存在")

    try:
        # 遞增版本號
        profile_service.increment_document_version(profile_id)
        db.refresh(profile)

        # 生成文件
        doc_bytes = doc_service.generate(profile, employee)

        # 生成檔名
        filename = doc_service.generate_filename(profile, employee)

        # 返回文件流
        return StreamingResponse(
            iter([doc_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            }
        )
    except InvalidProfileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# T144: 班表查詢 API
# ============================================================

@router.get("/schedule-lookup", response_model=ScheduleLookupResponse)
async def schedule_lookup(
    employee_id: int = Query(..., description="員工 ID"),
    event_date: date = Query(..., description="事件日期"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    查詢員工班表

    返回事件當天、前1天、前2天的班別資訊。
    """
    service = ScheduleLookupService(db)

    try:
        result = service.lookup_shifts(employee_id, event_date)
        return ScheduleLookupResponse(
            shift_before_2days=result.shift_before_2days,
            shift_before_1day=result.shift_before_1day,
            shift_event_day=result.shift_event_day,
            source=result.source,
        )
    except ScheduleEmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# T145: 履歷查詢 API
# ============================================================

@router.get("/search", response_model=list[ProfileResponse])
async def search_profiles(
    keyword: Optional[str] = Query(None, description="關鍵字"),
    department: Optional[str] = Query(None, description="部門"),
    profile_type: Optional[str] = Query(None, description="類型"),
    date_from: Optional[date] = Query(None, description="起始日期"),
    date_to: Optional[date] = Query(None, description="結束日期"),
    employee_name: Optional[str] = Query(None, description="員工姓名"),
    train_number: Optional[str] = Query(None, description="車號"),
    location: Optional[str] = Query(None, description="地點"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    搜尋履歷

    支援關鍵字、日期區間、員工姓名、車號、地點等多維度搜尋。
    """
    service = ProfileService(db)

    # 使用 Policy 過濾部門（Gemini Review P2）
    department = ProfilePolicy.filter_department(
        current_user.role, current_user.department, department
    )

    profiles = service.search(
        keyword=keyword,
        department=department,
        profile_type=profile_type,
        date_from=date_from,
        date_to=date_to,
        employee_name=employee_name,
        train_number=train_number,
        location=location,
        skip=skip,
        limit=limit,
    )

    return [_profile_to_response(p) for p in profiles]


# ============================================================
# 未結案相關 API（支援 Phase 14）
# ============================================================

@router.get("/pending", response_model=list[ProfileResponse])
async def get_pending_profiles(
    department: Optional[str] = Query(None, description="部門"),
    profile_type: Optional[str] = Query(None, description="類型"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    取得未結案履歷

    未結案定義：conversion_status = 'converted' AND gdrive_link IS NULL
    """
    service = ProfileService(db)

    # 使用 Policy 過濾部門（Gemini Review P2）
    department = ProfilePolicy.filter_department(
        current_user.role, current_user.department, department
    )

    profiles = service.get_pending_profiles(
        department=department,
        profile_type=profile_type,
        skip=skip,
        limit=limit,
    )

    return [_profile_to_response(p) for p in profiles]


@router.get("/pending/statistics", response_model=PendingStatsResponse)
async def get_pending_statistics(
    department: Optional[str] = Query(None, description="部門"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    取得未結案統計（T186 增強）

    包含：
    - 各類型未結案數量
    - 最舊未結案日期
    - 本月完成數 / 本月轉換總數
    - 本月完成率
    """
    # 使用 Policy 過濾部門（Gemini Review P2）
    department = ProfilePolicy.filter_department(
        current_user.role, current_user.department, department
    )

    pending_service = get_pending_profile_service(db)
    stats = pending_service.get_full_statistics(department)

    return PendingStatsResponse(
        total=stats.total,
        by_type=stats.by_type,
        oldest_pending_date=stats.oldest_pending_date,
        this_month_completed=stats.this_month_completed,
        this_month_total=stats.this_month_total,
        completion_rate=stats.completion_rate
    )


@router.get("/{profile_id}/upload-params", response_model=UploadParamsResponse)
async def get_upload_params(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    取得 PDF 上傳參數（T190）

    前端在上傳 PDF 前呼叫此 API 取得：
    - 建議的檔案名稱
    - 建議的資料夾路徑
    - 是否可以上傳

    實際上傳流程：
    1. 前端呼叫此 API 取得參數
    2. 前端呼叫本機 API 上傳 PDF 到 Google Drive
    3. 前端呼叫 POST /{profile_id}/complete 更新 gdrive_link
    """
    upload_service = get_pdf_upload_service(db)
    params = upload_service.get_upload_params(profile_id)

    if not params.can_upload and "不存在" in (params.error_message or ""):
        raise HTTPException(status_code=404, detail=params.error_message)

    return UploadParamsResponse(
        profile_id=params.profile_id,
        profile_type=params.profile_type,
        employee_id=params.employee_id,
        employee_name=params.employee_name,
        event_date=params.event_date,
        department=params.department,
        suggested_folder_name=params.suggested_folder_name,
        suggested_file_name=params.suggested_file_name,
        can_upload=params.can_upload,
        error_message=params.error_message
    )


@router.post("/{profile_id}/complete", response_model=ProfileResponse)
async def mark_profile_complete(
    profile_id: int,
    gdrive_link: str = Query(..., description="Google Drive 連結"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    標記履歷為已完成（上傳 PDF 後呼叫）
    """
    service = ProfileService(db)

    profile = service.get_by_id(profile_id, load_relations=False)
    if not profile:
        raise HTTPException(status_code=404, detail="履歷不存在")

    # 使用 Policy 檢查權限（Gemini Review P2）
    if not ProfilePolicy.can_mark_complete(
        current_user.role, current_user.department, profile
    ):
        raise HTTPException(status_code=403, detail="無權限操作此履歷")

    try:
        updated = service.mark_completed(profile_id, gdrive_link)
        return _profile_to_response(updated)
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================
# Phase 12 整合 API（T183, T184）
# ============================================================

@router.post("/with-assessment", response_model=ProfileWithAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_profile_with_assessment(
    data: ProfileCreateWithAssessment,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    建立履歷並同時建立考核記錄（Phase 12 整合）

    當考核代碼為 R02-R05 時，會同時建立：
    - Profile（基本履歷）
    - AssessmentRecord（考核記錄）
    - FaultResponsibilityAssessment（責任判定）

    注意：R02-R05 必須提供 fault_responsibility_data
    """
    service = ProfileService(db)

    # Staff 只能建立自己部門的履歷
    department = data.department
    if current_user.role == Role.STAFF.value:
        department = current_user.department

    # 準備責任判定資料
    fault_data = None
    if data.fault_responsibility_data:
        fault_data = {
            "delay_seconds": data.fault_responsibility_data.delay_seconds,
            "checklist_results": data.fault_responsibility_data.checklist_results.model_dump(),
            "time_t0": data.fault_responsibility_data.time_t0,
            "time_t1": data.fault_responsibility_data.time_t1,
            "time_t2": data.fault_responsibility_data.time_t2,
            "time_t3": data.fault_responsibility_data.time_t3,
            "time_t4": data.fault_responsibility_data.time_t4,
            "notes": data.fault_responsibility_data.notes
        }

    try:
        profile, assessment_record = service.create_with_assessment(
            employee_id=data.employee_id,
            event_date=data.event_date,
            department=department,
            assessment_code=data.assessment_code,
            event_location=data.event_location,
            train_number=data.train_number,
            event_title=data.event_title,
            event_description=data.event_description,
            event_time=data.event_time,
            data_source=data.data_source,
            fault_responsibility_data=fault_data,
        )

        # 準備回應
        profile_response = _profile_to_response(profile)

        assessment_response = {
            "id": assessment_record.id,
            "standard_code": assessment_record.standard_code,
            "base_points": assessment_record.base_points,
            "responsibility_coefficient": assessment_record.responsibility_coefficient,
            "actual_points": assessment_record.actual_points,
            "cumulative_count": assessment_record.cumulative_count,
            "cumulative_multiplier": assessment_record.cumulative_multiplier,
            "final_points": assessment_record.final_points,
        }

        responsibility_response = None
        if assessment_record.fault_responsibility:
            fr = assessment_record.fault_responsibility
            responsibility_response = {
                "id": fr.id,
                "fault_count": fr.fault_count,
                "responsibility_level": fr.responsibility_level,
                "responsibility_coefficient": fr.responsibility_coefficient,
                "checked_items": fr.checked_items_labels,
            }

        return ProfileWithAssessmentResponse(
            profile=profile_response,
            assessment_record=assessment_response,
            responsibility_assessment=responsibility_response
        )

    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{profile_id}/update-date")
async def update_profile_date(
    profile_id: int,
    data: ProfileUpdateDate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    更新履歷日期（Phase 12 T184）

    此 API 會：
    1. 更新 Profile.event_date
    2. 若有關聯的 AssessmentRecord，同步更新 record_date
    3. 若日期變更會影響累計次數，觸發重算
    4. 跨年變更時會重算兩個年度的累計次數

    注意：使用 Transaction + FOR UPDATE 確保並發安全
    """
    profile_service = ProfileService(db)
    date_updater = ProfileDateUpdaterService(db)

    # 檢查履歷是否存在
    profile = profile_service.get_by_id(profile_id, load_relations=False)
    if not profile:
        raise HTTPException(status_code=404, detail="履歷不存在")

    # 使用 Policy 檢查權限
    if not ProfilePolicy.can_edit(
        current_user.role, current_user.department, profile
    ):
        raise HTTPException(status_code=403, detail="無權限編輯此履歷")

    try:
        result = date_updater.update_profile_date(profile_id, data.new_date)
        db.commit()

        return {
            "success": True,
            "message": "履歷日期已更新",
            "result": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"日期更新失敗：{str(e)}")


@router.get("/{profile_id}/date-change-preview")
async def preview_date_change(
    profile_id: int,
    new_date: date = Query(..., description="新的事件日期"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """
    預覽履歷日期變更的影響（Phase 12 T184）

    返回：
    - 是否為跨年變更
    - 是否會觸發累計次數重算
    - 受影響的年度列表
    - 關聯的考核記錄資訊
    """
    profile_service = ProfileService(db)
    date_updater = ProfileDateUpdaterService(db)

    # 檢查履歷是否存在
    profile = profile_service.get_by_id(profile_id, load_relations=False)
    if not profile:
        raise HTTPException(status_code=404, detail="履歷不存在")

    # 使用 Policy 檢查權限
    if not ProfilePolicy.can_view(
        current_user.role, current_user.department, profile
    ):
        raise HTTPException(status_code=403, detail="無權限查看此履歷")

    try:
        preview = date_updater.preview_date_change(profile_id, new_date)
        return preview

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assessment-codes/responsibility-required")
async def get_responsibility_required_codes(
    db: Session = Depends(get_db),
    _: TokenData = Depends(get_current_user),
):
    """
    取得需要責任判定的考核代碼列表

    返回 R02-R05 代碼列表，供前端判斷是否需要顯示責任判定表單
    """
    service = ProfileService(db)
    return {
        "codes": service.get_assessment_codes_requiring_responsibility(),
        "description": "R02-R05 人為疏失項目需要填寫 9 項疏失查核表"
    }


# ============================================================
# Helper Functions
# ============================================================

def _profile_to_response(profile) -> ProfileResponse:
    """轉換 Profile 為回應格式"""
    employee_name = None
    if profile.employee:
        employee_name = profile.employee.employee_name

    return ProfileResponse(
        id=profile.id,
        employee_id=profile.employee_id,
        employee_name=employee_name,
        profile_type=profile.profile_type,
        event_date=profile.event_date,
        event_time=str(profile.event_time) if profile.event_time else None,
        event_location=profile.event_location,
        train_number=profile.train_number,
        event_title=profile.event_title,
        event_description=profile.event_description,
        data_source=profile.data_source,
        assessment_item=profile.assessment_item,
        assessment_score=profile.assessment_score,
        conversion_status=profile.conversion_status,
        file_path=profile.file_path,
        gdrive_link=profile.gdrive_link,
        department=profile.department,
        document_version=profile.document_version,
        created_at=profile.created_at.isoformat() if profile.created_at else "",
        updated_at=profile.updated_at.isoformat() if profile.updated_at else "",
    )
