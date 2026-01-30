"""
FaultResponsibilityService 故障責任判定服務
對應 tasks.md T169: 實作 FaultResponsibilityService
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 故障責任判定（R02-R05 專用）

此服務負責 R02-R05 雙因子評分的責任判定邏輯，
包含 9 項疏失查核表的計算與責任係數判定。
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.assessment_record import AssessmentRecord
from ..models.fault_responsibility import (
    CHECKLIST_KEYS,
    CHECKLIST_LABELS,
    FaultResponsibilityAssessment,
    ResponsibilityLevel,
    determine_responsibility,
)


class FaultResponsibilityService:
    """
    故障責任判定服務

    提供 R02-R05 責任判定的業務邏輯，
    包含查核表驗證、責任計算、記錄管理等功能。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: 資料庫 Session
        """
        self.db = db

    def validate_checklist(self, checklist_results: dict[str, bool]) -> tuple[bool, list[str]]:
        """
        驗證查核表資料格式

        Args:
            checklist_results: 9 項查核結果字典

        Returns:
            (是否有效, 錯誤訊息列表) 元組
        """
        errors = []

        # 檢查必要的鍵
        for key in CHECKLIST_KEYS:
            if key not in checklist_results:
                errors.append(f"缺少查核項目: {CHECKLIST_LABELS[key]}")

        # 檢查值是否為布林
        for key, value in checklist_results.items():
            if key in CHECKLIST_KEYS and not isinstance(value, bool):
                errors.append(f"查核項目 '{CHECKLIST_LABELS.get(key, key)}' 值必須為布林")

        # 檢查是否有多餘的鍵
        extra_keys = set(checklist_results.keys()) - set(CHECKLIST_KEYS)
        if extra_keys:
            errors.append(f"未知的查核項目: {extra_keys}")

        return (len(errors) == 0, errors)

    def normalize_checklist(self, checklist_results: dict[str, Any]) -> dict[str, bool]:
        """
        正規化查核表資料

        將各種輸入格式轉換為標準布林格式

        Args:
            checklist_results: 查核結果字典

        Returns:
            正規化後的查核結果字典
        """
        normalized = {}
        for key in CHECKLIST_KEYS:
            value = checklist_results.get(key, False)
            # 處理各種可能的輸入格式
            if isinstance(value, bool):
                normalized[key] = value
            elif isinstance(value, (int, float)):
                normalized[key] = bool(value)
            elif isinstance(value, str):
                normalized[key] = value.lower() in ('true', '1', 'yes')
            else:
                normalized[key] = False
        return normalized

    def calculate_fault_count(self, checklist_results: dict[str, bool]) -> int:
        """
        計算疏失項數

        Args:
            checklist_results: 查核結果字典

        Returns:
            疏失項數（0-9）
        """
        return sum(
            1 for key in CHECKLIST_KEYS
            if checklist_results.get(key, False)
        )

    def determine_responsibility_level(
        self,
        fault_count: int
    ) -> tuple[str, float]:
        """
        根據疏失項數判定責任程度

        Args:
            fault_count: 疏失項數

        Returns:
            (責任程度, 責任係數) 元組
        """
        return determine_responsibility(fault_count)

    def calculate_actual_points(
        self,
        base_points: float,
        responsibility_coefficient: float
    ) -> float:
        """
        計算實際扣分

        公式：實際扣分 = 基本分 × 責任係數

        Args:
            base_points: 基本分數
            responsibility_coefficient: 責任係數

        Returns:
            實際扣分
        """
        return base_points * responsibility_coefficient

    def create_assessment(
        self,
        record_id: int,
        delay_seconds: int,
        checklist_results: dict[str, bool],
        time_t0: Optional[datetime] = None,
        time_t1: Optional[datetime] = None,
        time_t2: Optional[datetime] = None,
        time_t3: Optional[datetime] = None,
        time_t4: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> FaultResponsibilityAssessment:
        """
        建立責任判定記錄

        Args:
            record_id: 考核記錄 ID
            delay_seconds: 延誤時間（秒）
            checklist_results: 9 項查核結果
            time_t0: T0 時間（可選）
            time_t1: T1 時間（可選）
            time_t2: T2 時間（可選）
            time_t3: T3 時間（可選）
            time_t4: T4 時間（可選）
            notes: 備註（可選）

        Returns:
            建立的責任判定記錄
        """
        # 正規化並驗證查核表
        normalized = self.normalize_checklist(checklist_results)
        is_valid, errors = self.validate_checklist(normalized)
        if not is_valid:
            raise ValueError(f"查核表資料無效: {', '.join(errors)}")

        # 計算責任判定
        fault_count = self.calculate_fault_count(normalized)
        level, coefficient = self.determine_responsibility_level(fault_count)

        # 建立記錄
        assessment = FaultResponsibilityAssessment(
            record_id=record_id,
            time_t0=time_t0,
            time_t1=time_t1,
            time_t2=time_t2,
            time_t3=time_t3,
            time_t4=time_t4,
            delay_seconds=delay_seconds,
            checklist_results=normalized,
            fault_count=fault_count,
            responsibility_level=level,
            responsibility_coefficient=coefficient,
            notes=notes
        )

        self.db.add(assessment)
        return assessment

    def update_assessment(
        self,
        assessment_id: int,
        checklist_results: Optional[dict[str, bool]] = None,
        delay_seconds: Optional[int] = None,
        time_t0: Optional[datetime] = None,
        time_t1: Optional[datetime] = None,
        time_t2: Optional[datetime] = None,
        time_t3: Optional[datetime] = None,
        time_t4: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> FaultResponsibilityAssessment:
        """
        更新責任判定記錄

        Args:
            assessment_id: 責任判定記錄 ID
            checklist_results: 9 項查核結果（可選）
            delay_seconds: 延誤時間（可選）
            time_t0-t4: 時間節點（可選）
            notes: 備註（可選）

        Returns:
            更新後的責任判定記錄
        """
        assessment = self.db.execute(
            select(FaultResponsibilityAssessment).where(
                FaultResponsibilityAssessment.id == assessment_id
            )
        ).scalar_one_or_none()

        if not assessment:
            raise ValueError(f"找不到責任判定記錄 ID: {assessment_id}")

        # 更新時間節點
        if time_t0 is not None:
            assessment.time_t0 = time_t0
        if time_t1 is not None:
            assessment.time_t1 = time_t1
        if time_t2 is not None:
            assessment.time_t2 = time_t2
        if time_t3 is not None:
            assessment.time_t3 = time_t3
        if time_t4 is not None:
            assessment.time_t4 = time_t4

        # 更新延誤時間
        if delay_seconds is not None:
            assessment.delay_seconds = delay_seconds

        # 更新備註
        if notes is not None:
            assessment.notes = notes

        # 更新查核表並重新計算責任
        if checklist_results is not None:
            normalized = self.normalize_checklist(checklist_results)
            is_valid, errors = self.validate_checklist(normalized)
            if not is_valid:
                raise ValueError(f"查核表資料無效: {', '.join(errors)}")

            assessment.checklist_results = normalized
            assessment.fault_count = self.calculate_fault_count(normalized)
            level, coefficient = self.determine_responsibility_level(assessment.fault_count)
            assessment.responsibility_level = level
            assessment.responsibility_coefficient = coefficient

        return assessment

    def get_by_record_id(self, record_id: int) -> Optional[FaultResponsibilityAssessment]:
        """
        根據考核記錄 ID 取得責任判定記錄

        Args:
            record_id: 考核記錄 ID

        Returns:
            責任判定記錄或 None
        """
        return self.db.execute(
            select(FaultResponsibilityAssessment).where(
                FaultResponsibilityAssessment.record_id == record_id
            )
        ).scalar_one_or_none()

    def get_checklist_template(self) -> dict[str, Any]:
        """
        取得查核表模板（用於前端顯示）

        Returns:
            查核表模板字典
        """
        return {
            "keys": CHECKLIST_KEYS,
            "labels": CHECKLIST_LABELS,
            "template": {key: False for key in CHECKLIST_KEYS},
            "responsibility_rules": {
                "完全責任": {"min_faults": 7, "max_faults": 9, "coefficient": 1.0},
                "主要責任": {"min_faults": 4, "max_faults": 6, "coefficient": 0.7},
                "次要責任": {"min_faults": 1, "max_faults": 3, "coefficient": 0.3},
            }
        }

    def calculate_assessment_preview(
        self,
        base_points: float,
        checklist_results: dict[str, bool],
        cumulative_multiplier: float = 1.0
    ) -> dict[str, Any]:
        """
        預覽責任判定計算結果

        Args:
            base_points: 基本分數
            checklist_results: 查核結果
            cumulative_multiplier: 累計倍率

        Returns:
            計算結果預覽
        """
        normalized = self.normalize_checklist(checklist_results)
        fault_count = self.calculate_fault_count(normalized)
        level, coefficient = self.determine_responsibility_level(fault_count)
        actual_points = self.calculate_actual_points(base_points, coefficient)
        final_points = actual_points * cumulative_multiplier

        return {
            "fault_count": fault_count,
            "responsibility_level": level,
            "responsibility_coefficient": coefficient,
            "base_points": base_points,
            "actual_points": actual_points,
            "cumulative_multiplier": cumulative_multiplier,
            "final_points": final_points,
            "checked_items": [
                CHECKLIST_LABELS[key]
                for key in CHECKLIST_KEYS
                if normalized.get(key, False)
            ]
        }
