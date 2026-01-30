"""
ProfileService 履歷服務
對應 tasks.md T135: 實作 ProfileService
對應 spec.md: User Story 8 - 履歷 CRUD、類型轉換、狀態管理

轉換規則（Gemini Review 建議）：
- 僅允許 basic → 其他類型
- 已完成履歷不可轉換
"""

from datetime import date
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, selectinload

from src.models import (
    AssessmentNotice,
    AssessmentType,
    ConversionStatus,
    CorrectiveMeasures,
    Department,
    Employee,
    EventInvestigation,
    PersonnelInterview,
    Profile,
    ProfileType,
)


class ProfileServiceError(Exception):
    """履歷服務錯誤"""
    pass


class ProfileNotFoundError(ProfileServiceError):
    """履歷不存在錯誤"""
    pass


class InvalidConversionError(ProfileServiceError):
    """無效的類型轉換錯誤"""
    pass


class EmployeeNotFoundError(ProfileServiceError):
    """員工不存在錯誤"""
    pass


class ProfileService:
    """
    履歷服務

    提供履歷的 CRUD、類型轉換、狀態管理等功能。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: SQLAlchemy Session
        """
        self.db = db

    # ============================================================
    # CRUD 操作
    # ============================================================

    def create(
        self,
        employee_id: int,
        event_date: date,
        department: str,
        event_location: Optional[str] = None,
        train_number: Optional[str] = None,
        event_title: Optional[str] = None,
        event_description: Optional[str] = None,
        event_time: Optional[str] = None,
        data_source: Optional[str] = None,
        assessment_item: Optional[str] = None,
        assessment_score: Optional[int] = None,
        auto_commit: bool = True
    ) -> Profile:
        """
        建立基本履歷

        Args:
            employee_id: 員工 ID
            event_date: 事件日期
            department: 部門
            event_location: 事件地點
            train_number: 列車車號
            event_title: 事件標題
            event_description: 事件描述
            event_time: 事件時間
            data_source: 資料來源
            assessment_item: 考核項目
            assessment_score: 考核分數
            auto_commit: 是否自動提交

        Returns:
            Profile: 新建立的履歷

        Raises:
            EmployeeNotFoundError: 員工不存在
        """
        # 驗證員工存在
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
        if not employee:
            raise EmployeeNotFoundError(f"員工 ID {employee_id} 不存在")

        profile = Profile(
            employee_id=employee_id,
            profile_type=ProfileType.BASIC.value,
            event_date=event_date,
            event_time=event_time,
            event_location=event_location,
            train_number=train_number,
            event_title=event_title,
            event_description=event_description,
            data_source=data_source,
            assessment_item=assessment_item,
            assessment_score=assessment_score,
            conversion_status=ConversionStatus.PENDING.value,
            department=department,
            document_version=1,
        )

        self.db.add(profile)

        if auto_commit:
            self.db.commit()
            self.db.refresh(profile)

        return profile

    def get_by_id(
        self,
        profile_id: int,
        load_relations: bool = True
    ) -> Optional[Profile]:
        """
        根據 ID 取得履歷

        Args:
            profile_id: 履歷 ID
            load_relations: 是否載入關聯資料

        Returns:
            Profile 或 None
        """
        query = self.db.query(Profile)

        if load_relations:
            query = query.options(
                selectinload(Profile.employee),
                selectinload(Profile.event_investigation),
                selectinload(Profile.personnel_interview),
                selectinload(Profile.corrective_measures),
                selectinload(Profile.assessment_notice),
            )

        return query.filter(Profile.id == profile_id).first()

    def get_list(
        self,
        department: Optional[str] = None,
        profile_type: Optional[str] = None,
        conversion_status: Optional[str] = None,
        employee_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Profile]:
        """
        取得履歷列表

        Args:
            department: 部門篩選
            profile_type: 類型篩選
            conversion_status: 狀態篩選
            employee_id: 員工 ID 篩選
            date_from: 起始日期
            date_to: 結束日期
            skip: 跳過筆數
            limit: 取得筆數

        Returns:
            履歷列表
        """
        query = self.db.query(Profile).options(
            selectinload(Profile.employee)
        )

        # 篩選條件
        filters = []

        if department:
            filters.append(Profile.department == department)

        if profile_type:
            filters.append(Profile.profile_type == profile_type)

        if conversion_status:
            filters.append(Profile.conversion_status == conversion_status)

        if employee_id:
            filters.append(Profile.employee_id == employee_id)

        if date_from:
            filters.append(Profile.event_date >= date_from)

        if date_to:
            filters.append(Profile.event_date <= date_to)

        if filters:
            query = query.filter(and_(*filters))

        return query.order_by(
            Profile.event_date.desc(),
            Profile.id.desc()
        ).offset(skip).limit(limit).all()

    def update(
        self,
        profile_id: int,
        **kwargs
    ) -> Profile:
        """
        更新履歷

        Args:
            profile_id: 履歷 ID
            **kwargs: 要更新的欄位

        Returns:
            更新後的履歷

        Raises:
            ProfileNotFoundError: 履歷不存在
        """
        profile = self.get_by_id(profile_id, load_relations=False)
        if not profile:
            raise ProfileNotFoundError(f"履歷 ID {profile_id} 不存在")

        # 可更新的欄位
        allowed_fields = {
            "event_date", "event_time", "event_location", "train_number",
            "event_title", "event_description", "data_source",
            "assessment_item", "assessment_score", "file_path", "gdrive_link"
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(profile, key, value)

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def delete(self, profile_id: int) -> bool:
        """
        刪除履歷

        Args:
            profile_id: 履歷 ID

        Returns:
            是否成功刪除

        Raises:
            ProfileNotFoundError: 履歷不存在
        """
        profile = self.get_by_id(profile_id, load_relations=False)
        if not profile:
            raise ProfileNotFoundError(f"履歷 ID {profile_id} 不存在")

        self.db.delete(profile)
        self.db.commit()

        return True

    # ============================================================
    # 類型轉換
    # ============================================================

    def convert_type(
        self,
        profile_id: int,
        target_type: str,
        sub_table_data: Optional[dict] = None
    ) -> Profile:
        """
        轉換履歷類型

        規則（Gemini Review 建議）：
        - 僅允許 basic → 其他類型
        - 已完成履歷不可轉換
        - 轉換時刪除舊子表資料

        Args:
            profile_id: 履歷 ID
            target_type: 目標類型
            sub_table_data: 子表資料

        Returns:
            轉換後的履歷

        Raises:
            ProfileNotFoundError: 履歷不存在
            InvalidConversionError: 無效的轉換
        """
        profile = self.get_by_id(profile_id)
        if not profile:
            raise ProfileNotFoundError(f"履歷 ID {profile_id} 不存在")

        # 檢查轉換規則
        if profile.conversion_status == ConversionStatus.COMPLETED.value:
            raise InvalidConversionError("已完成的履歷不可轉換")

        if profile.profile_type != ProfileType.BASIC.value:
            raise InvalidConversionError(
                f"僅允許基本履歷轉換，當前類型: {profile.profile_type}"
            )

        if target_type == ProfileType.BASIC.value:
            raise InvalidConversionError("不可轉換為基本履歷")

        # 驗證目標類型
        valid_types = [e.value for e in ProfileType]
        if target_type not in valid_types:
            raise InvalidConversionError(f"無效的目標類型: {target_type}")

        # 刪除現有子表資料（如果有的話）
        self._delete_sub_tables(profile)

        # 建立新的子表資料
        self._create_sub_table(profile, target_type, sub_table_data or {})

        # 更新履歷類型和狀態
        profile.profile_type = target_type
        profile.conversion_status = ConversionStatus.CONVERTED.value

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def _delete_sub_tables(self, profile: Profile) -> None:
        """刪除所有子表資料"""
        if profile.event_investigation:
            self.db.delete(profile.event_investigation)
        if profile.personnel_interview:
            self.db.delete(profile.personnel_interview)
        if profile.corrective_measures:
            self.db.delete(profile.corrective_measures)
        if profile.assessment_notice:
            self.db.delete(profile.assessment_notice)

    def _create_sub_table(
        self,
        profile: Profile,
        target_type: str,
        data: dict
    ) -> None:
        """建立子表資料"""
        if target_type == ProfileType.EVENT_INVESTIGATION.value:
            sub_table = EventInvestigation(
                profile_id=profile.id,
                incident_time=data.get("incident_time"),
                incident_location=data.get("incident_location"),
                witnesses=data.get("witnesses"),
                cause_analysis=data.get("cause_analysis"),
                process_description=data.get("process_description"),
                improvement_suggestions=data.get("improvement_suggestions"),
                investigator=data.get("investigator"),
                investigation_date=data.get("investigation_date"),
                has_responsibility=data.get("has_responsibility"),
                responsibility_ratio=data.get("responsibility_ratio"),
                category=data.get("category"),
            )
            self.db.add(sub_table)

        elif target_type == ProfileType.PERSONNEL_INTERVIEW.value:
            sub_table = PersonnelInterview(
                profile_id=profile.id,
                hire_date=data.get("hire_date"),
                shift_before_2days=data.get("shift_before_2days"),
                shift_before_1day=data.get("shift_before_1day"),
                shift_event_day=data.get("shift_event_day"),
                interview_content=data.get("interview_content"),
                interviewer=data.get("interviewer"),
                interview_date=data.get("interview_date"),
                interview_result_data=data.get("interview_result_data"),
                follow_up_action_data=data.get("follow_up_action_data"),
                conclusion=data.get("conclusion"),
            )
            self.db.add(sub_table)

        elif target_type == ProfileType.CORRECTIVE_MEASURES.value:
            sub_table = CorrectiveMeasures(
                profile_id=profile.id,
                event_summary=data.get("event_summary"),
                corrective_actions=data.get("corrective_actions"),
                responsible_person=data.get("responsible_person"),
                completion_deadline=data.get("completion_deadline"),
                completion_status=data.get("completion_status", "pending"),
            )
            self.db.add(sub_table)

        elif target_type == ProfileType.ASSESSMENT_NOTICE.value:
            sub_table = AssessmentNotice(
                profile_id=profile.id,
                assessment_type=data.get("assessment_type", AssessmentType.MINUS.value),
                assessment_item=data.get("assessment_item"),
                assessment_score=data.get("assessment_score"),
                issue_date=data.get("issue_date"),
                approver=data.get("approver"),
            )
            self.db.add(sub_table)

    # ============================================================
    # 狀態管理
    # ============================================================

    def reset_to_basic(self, profile_id: int) -> Profile:
        """
        重置履歷為基本類型（Gemini Review P1）

        刪除子表資料，將 profile_type 改回 basic，
        conversion_status 改回 pending。

        規則：
        - 已完成（completed）的履歷不可重置
        - 基本履歷不需要重置

        Args:
            profile_id: 履歷 ID

        Returns:
            重置後的履歷

        Raises:
            ProfileNotFoundError: 履歷不存在
            InvalidConversionError: 無效的重置操作
        """
        profile = self.get_by_id(profile_id)
        if not profile:
            raise ProfileNotFoundError(f"履歷 ID {profile_id} 不存在")

        # 檢查規則
        if profile.conversion_status == ConversionStatus.COMPLETED.value:
            raise InvalidConversionError("已完成的履歷不可重置")

        if profile.profile_type == ProfileType.BASIC.value:
            raise InvalidConversionError("基本履歷不需要重置")

        # 刪除子表資料
        self._delete_sub_tables(profile)

        # 重置類型和狀態
        profile.profile_type = ProfileType.BASIC.value
        profile.conversion_status = ConversionStatus.PENDING.value

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def mark_completed(
        self,
        profile_id: int,
        gdrive_link: str
    ) -> Profile:
        """
        標記履歷為已完成

        Args:
            profile_id: 履歷 ID
            gdrive_link: Google Drive 連結

        Returns:
            更新後的履歷
        """
        profile = self.get_by_id(profile_id, load_relations=False)
        if not profile:
            raise ProfileNotFoundError(f"履歷 ID {profile_id} 不存在")

        profile.conversion_status = ConversionStatus.COMPLETED.value
        profile.gdrive_link = gdrive_link

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def increment_document_version(self, profile_id: int) -> int:
        """
        遞增文件版本號

        Args:
            profile_id: 履歷 ID

        Returns:
            新的版本號
        """
        profile = self.get_by_id(profile_id, load_relations=False)
        if not profile:
            raise ProfileNotFoundError(f"履歷 ID {profile_id} 不存在")

        new_version = profile.increment_version()
        self.db.commit()

        return new_version

    # ============================================================
    # 查詢功能
    # ============================================================

    def search(
        self,
        keyword: Optional[str] = None,
        department: Optional[str] = None,
        profile_type: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        employee_name: Optional[str] = None,
        train_number: Optional[str] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Profile]:
        """
        搜尋履歷

        Args:
            keyword: 關鍵字（搜尋事件描述、標題）
            department: 部門
            profile_type: 類型
            date_from: 起始日期
            date_to: 結束日期
            employee_name: 員工姓名
            train_number: 車號
            location: 地點
            skip: 跳過筆數
            limit: 取得筆數

        Returns:
            搜尋結果
        """
        query = self.db.query(Profile).join(Employee).options(
            selectinload(Profile.employee)
        )

        filters = []

        if department:
            filters.append(Profile.department == department)

        if profile_type:
            filters.append(Profile.profile_type == profile_type)

        if date_from:
            filters.append(Profile.event_date >= date_from)

        if date_to:
            filters.append(Profile.event_date <= date_to)

        if employee_name:
            filters.append(Employee.employee_name.contains(employee_name))

        if train_number:
            filters.append(Profile.train_number.contains(train_number))

        if location:
            filters.append(Profile.event_location.contains(location))

        if keyword:
            filters.append(
                or_(
                    Profile.event_description.contains(keyword),
                    Profile.event_title.contains(keyword),
                )
            )

        if filters:
            query = query.filter(and_(*filters))

        return query.order_by(
            Profile.event_date.desc()
        ).offset(skip).limit(limit).all()

    def get_pending_profiles(
        self,
        department: Optional[str] = None,
        profile_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Profile]:
        """
        取得未結案履歷

        未結案定義：conversion_status = 'converted' AND gdrive_link IS NULL

        Args:
            department: 部門篩選
            profile_type: 類型篩選
            skip: 跳過筆數
            limit: 取得筆數

        Returns:
            未結案履歷列表
        """
        query = self.db.query(Profile).options(
            selectinload(Profile.employee)
        ).filter(
            Profile.conversion_status == ConversionStatus.CONVERTED.value,
            Profile.gdrive_link.is_(None)
        )

        if department:
            query = query.filter(Profile.department == department)

        if profile_type:
            query = query.filter(Profile.profile_type == profile_type)

        return query.order_by(
            Profile.event_date.asc()
        ).offset(skip).limit(limit).all()

    def count_pending(self, department: Optional[str] = None) -> dict:
        """
        統計未結案數量

        Args:
            department: 部門篩選

        Returns:
            各類型未結案數量
        """
        from sqlalchemy import func

        query = self.db.query(
            Profile.profile_type,
            func.count(Profile.id).label("count")
        ).filter(
            Profile.conversion_status == ConversionStatus.CONVERTED.value,
            Profile.gdrive_link.is_(None)
        )

        if department:
            query = query.filter(Profile.department == department)

        results = query.group_by(Profile.profile_type).all()

        return {r.profile_type: r.count for r in results}
