"""
AssessmentStandardService 考核標準服務
對應 tasks.md T166: 實作 AssessmentStandardService
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: 考核標準主檔

此服務負責考核標準的 CRUD 操作、Excel 匯入、關鍵字搜尋等功能。
"""

from typing import Any, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from ..models.assessment_standard import (
    AssessmentStandard,
    CalculationCycle,
)


class AssessmentStandardService:
    """
    考核標準服務

    提供考核標準的 CRUD 操作、搜尋、Excel 匯入等功能。
    """

    def __init__(self, db: Session):
        """
        初始化服務

        Args:
            db: 資料庫 Session
        """
        self.db = db

    def get_all(
        self,
        is_active: Optional[bool] = True,
        category: Optional[str] = None
    ) -> list[AssessmentStandard]:
        """
        取得所有考核標準

        Args:
            is_active: 是否僅查詢啟用的標準（預設 True）
            category: 類別篩選（可選）

        Returns:
            考核標準列表
        """
        stmt = select(AssessmentStandard)

        conditions = []
        if is_active is not None:
            conditions.append(AssessmentStandard.is_active == is_active)
        if category:
            conditions.append(AssessmentStandard.category == category)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(AssessmentStandard.code)

        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, standard_id: int) -> Optional[AssessmentStandard]:
        """
        根據 ID 取得考核標準

        Args:
            standard_id: 考核標準 ID

        Returns:
            考核標準或 None
        """
        return self.db.execute(
            select(AssessmentStandard).where(AssessmentStandard.id == standard_id)
        ).scalar_one_or_none()

    def get_by_code(self, code: str) -> Optional[AssessmentStandard]:
        """
        根據代碼取得考核標準

        Args:
            code: 考核標準代碼

        Returns:
            考核標準或 None
        """
        return self.db.execute(
            select(AssessmentStandard).where(AssessmentStandard.code == code)
        ).scalar_one_or_none()

    def search(
        self,
        keyword: str,
        is_active: Optional[bool] = True
    ) -> list[AssessmentStandard]:
        """
        關鍵字搜尋考核標準

        搜尋範圍：代碼、名稱、說明

        Args:
            keyword: 搜尋關鍵字
            is_active: 是否僅查詢啟用的標準

        Returns:
            符合條件的考核標準列表
        """
        search_pattern = f"%{keyword}%"

        stmt = select(AssessmentStandard).where(
            or_(
                AssessmentStandard.code.ilike(search_pattern),
                AssessmentStandard.name.ilike(search_pattern),
                AssessmentStandard.description.ilike(search_pattern)
            )
        )

        if is_active is not None:
            stmt = stmt.where(AssessmentStandard.is_active == is_active)

        stmt = stmt.order_by(AssessmentStandard.code)

        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        code: str,
        category: str,
        name: str,
        base_points: float,
        has_cumulative: bool = True,
        calculation_cycle: str = "yearly",
        description: Optional[str] = None,
        is_active: bool = True
    ) -> AssessmentStandard:
        """
        建立考核標準

        Args:
            code: 考核代碼
            category: 類別
            name: 項目名稱
            base_points: 基本分數
            has_cumulative: 是否適用累計加重
            calculation_cycle: 計算週期
            description: 說明
            is_active: 是否啟用

        Returns:
            建立的考核標準
        """
        # 檢查代碼是否已存在
        existing = self.get_by_code(code)
        if existing:
            raise ValueError(f"考核代碼 '{code}' 已存在")

        standard = AssessmentStandard(
            code=code,
            category=category,
            name=name,
            base_points=base_points,
            has_cumulative=has_cumulative,
            calculation_cycle=calculation_cycle,
            description=description,
            is_active=is_active
        )

        self.db.add(standard)
        return standard

    def update(
        self,
        standard_id: int,
        **kwargs
    ) -> AssessmentStandard:
        """
        更新考核標準

        Args:
            standard_id: 考核標準 ID
            **kwargs: 要更新的欄位

        Returns:
            更新後的考核標準
        """
        standard = self.get_by_id(standard_id)
        if not standard:
            raise ValueError(f"找不到考核標準 ID: {standard_id}")

        # 如果要更新 code，檢查是否與其他記錄衝突
        if 'code' in kwargs and kwargs['code'] != standard.code:
            existing = self.get_by_code(kwargs['code'])
            if existing:
                raise ValueError(f"考核代碼 '{kwargs['code']}' 已存在")

        # 更新欄位
        allowed_fields = {
            'code', 'category', 'name', 'base_points',
            'has_cumulative', 'calculation_cycle', 'description', 'is_active'
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(standard, key, value)

        return standard

    def delete(self, standard_id: int) -> bool:
        """
        刪除考核標準

        注意：若該標準已有考核記錄，則無法刪除

        Args:
            standard_id: 考核標準 ID

        Returns:
            是否成功刪除
        """
        standard = self.get_by_id(standard_id)
        if not standard:
            raise ValueError(f"找不到考核標準 ID: {standard_id}")

        # 檢查是否有關聯的考核記錄
        if standard.records:
            raise ValueError(f"考核標準 '{standard.code}' 已有考核記錄，無法刪除")

        self.db.delete(standard)
        return True

    def toggle_active(self, standard_id: int) -> AssessmentStandard:
        """
        切換考核標準的啟用狀態

        Args:
            standard_id: 考核標準 ID

        Returns:
            更新後的考核標準
        """
        standard = self.get_by_id(standard_id)
        if not standard:
            raise ValueError(f"找不到考核標準 ID: {standard_id}")

        standard.is_active = not standard.is_active
        return standard

    def get_categories(self) -> dict[str, list[AssessmentStandard]]:
        """
        取得按類別分組的考核標準

        Returns:
            類別到考核標準列表的字典
        """
        standards = self.get_all(is_active=True)
        result: dict[str, list[AssessmentStandard]] = {}

        for standard in standards:
            if standard.category not in result:
                result[standard.category] = []
            result[standard.category].append(standard)

        return result

    def import_from_excel_data(
        self,
        data: list[dict[str, Any]],
        update_existing: bool = False
    ) -> dict[str, int]:
        """
        從 Excel 資料匯入考核標準

        Args:
            data: Excel 資料列表，每個字典包含 code, category, name, base_points 等欄位
            update_existing: 是否更新已存在的標準

        Returns:
            匯入結果統計 {"created": N, "updated": N, "skipped": N, "errors": N}
        """
        result = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        for row in data:
            try:
                code = str(row.get('code', '')).strip()
                if not code:
                    result['errors'] += 1
                    continue

                existing = self.get_by_code(code)

                if existing:
                    if update_existing:
                        # 更新現有記錄
                        existing.category = str(row.get('category', existing.category)).strip()
                        existing.name = str(row.get('name', existing.name)).strip()
                        existing.base_points = float(row.get('base_points', existing.base_points))
                        existing.has_cumulative = bool(row.get('has_cumulative', existing.has_cumulative))
                        existing.calculation_cycle = str(row.get('calculation_cycle', existing.calculation_cycle))
                        existing.description = row.get('description', existing.description)
                        existing.is_active = bool(row.get('is_active', existing.is_active))
                        result['updated'] += 1
                    else:
                        result['skipped'] += 1
                else:
                    # 建立新記錄
                    standard = AssessmentStandard(
                        code=code,
                        category=str(row.get('category', '')).strip(),
                        name=str(row.get('name', '')).strip(),
                        base_points=float(row.get('base_points', 0)),
                        has_cumulative=bool(row.get('has_cumulative', True)),
                        calculation_cycle=str(row.get('calculation_cycle', 'yearly')),
                        description=row.get('description'),
                        is_active=bool(row.get('is_active', True))
                    )
                    self.db.add(standard)
                    result['created'] += 1

            except Exception:
                result['errors'] += 1

        return result

    def get_deduction_standards(self) -> list[AssessmentStandard]:
        """
        取得所有扣分項目

        Returns:
            扣分項目列表
        """
        return [s for s in self.get_all() if s.base_points < 0]

    def get_bonus_standards(self) -> list[AssessmentStandard]:
        """
        取得所有加分項目

        Returns:
            加分項目列表
        """
        return [s for s in self.get_all() if s.base_points > 0]

    def get_r_type_standards(self) -> list[AssessmentStandard]:
        """
        取得 R02-R05 人為疏失項目（需責任判定）

        Returns:
            R02-R05 項目列表
        """
        return [
            s for s in self.get_all()
            if s.code in {'R02', 'R03', 'R04', 'R05'}
        ]

    def initialize_default_standards(self) -> int:
        """
        初始化預設的 61 項考核標準

        Returns:
            建立的標準數量
        """
        # 檢查是否已有資料
        existing = self.get_all(is_active=None)
        if existing:
            return 0  # 已有資料，不重複初始化

        default_standards = self._get_default_standards_data()

        for data in default_standards:
            standard = AssessmentStandard(**data)
            self.db.add(standard)

        return len(default_standards)

    def _get_default_standards_data(self) -> list[dict[str, Any]]:
        """
        取得預設考核標準資料（61 項）

        Returns:
            預設標準資料列表
        """
        # 扣分項目（41 項）
        deduction_standards = [
            # D 類：服勤類
            {"code": "D01", "category": "D", "name": "遲到/早退", "base_points": -1.0, "has_cumulative": True},
            {"code": "D02", "category": "D", "name": "遲到但不影響勤務", "base_points": 0, "has_cumulative": False},
            {"code": "D03", "category": "D", "name": "未依規定簽退", "base_points": -1.0, "has_cumulative": True},
            {"code": "D04", "category": "D", "name": "曠職", "base_points": -5.0, "has_cumulative": True},
            {"code": "D05", "category": "D", "name": "未經同意私自調班", "base_points": -2.0, "has_cumulative": True},
            # W 類：酒測類
            {"code": "W01", "category": "W", "name": "未依規定接受酒測", "base_points": -3.0, "has_cumulative": True},
            {"code": "W02", "category": "W", "name": "酒測不合格/未執行", "base_points": -5.0, "has_cumulative": True},
            # O 類：其他類
            {"code": "O01", "category": "O", "name": "未依規定穿著制服", "base_points": -1.0, "has_cumulative": True},
            {"code": "O02", "category": "O", "name": "服務態度不佳", "base_points": -2.0, "has_cumulative": True},
            {"code": "O03", "category": "O", "name": "未依規定回報", "base_points": -1.0, "has_cumulative": True},
            {"code": "O04", "category": "O", "name": "違反工作規定", "base_points": -2.0, "has_cumulative": True},
            {"code": "O05", "category": "O", "name": "其他輕微違規", "base_points": -1.0, "has_cumulative": True},
            # S 類：行車類
            {"code": "S01", "category": "S", "name": "未依規定執行運轉", "base_points": -2.0, "has_cumulative": True},
            {"code": "S02", "category": "S", "name": "超速或慢速行駛", "base_points": -3.0, "has_cumulative": True},
            {"code": "S03", "category": "S", "name": "未依規定停靠月台", "base_points": -2.0, "has_cumulative": True},
            {"code": "S04", "category": "S", "name": "未依規定開關門", "base_points": -2.0, "has_cumulative": True},
            {"code": "S05", "category": "S", "name": "違反 SOP 作業程序", "base_points": -3.0, "has_cumulative": True},
            {"code": "S06", "category": "S", "name": "行車安全疏失（無延誤）", "base_points": -2.0, "has_cumulative": True},
            {"code": "S07", "category": "S", "name": "行車安全疏失（輕微延誤）", "base_points": -3.0, "has_cumulative": True},
            {"code": "S08", "category": "S", "name": "行車安全疏失（嚴重延誤）", "base_points": -5.0, "has_cumulative": True},
            # R 類：責任類（R02-R05 需責任判定）
            {"code": "R01", "category": "R", "name": "設備故障（非人為）", "base_points": 0, "has_cumulative": False},
            {"code": "R02", "category": "R", "name": "人為操作不當致需故障排除（未延誤）", "base_points": -1.0, "has_cumulative": True},
            {"code": "R03", "category": "R", "name": "人為疏失延誤 90秒~5分鐘", "base_points": -2.0, "has_cumulative": True},
            {"code": "R04", "category": "R", "name": "人為疏失延誤 5~10分鐘", "base_points": -3.0, "has_cumulative": True},
            {"code": "R05", "category": "R", "name": "人為疏失延誤 超過10分鐘", "base_points": -5.0, "has_cumulative": True},
        ]

        # 加分項目（20 項）
        bonus_standards = [
            # +M 類：月度獎勵
            {"code": "+M01", "category": "+M", "name": "月度全勤", "base_points": 3.0, "has_cumulative": False, "calculation_cycle": "monthly"},
            {"code": "+M02", "category": "+M", "name": "月度行車零違規", "base_points": 1.0, "has_cumulative": False, "calculation_cycle": "monthly"},
            {"code": "+M03", "category": "+M", "name": "月度全項目零違規", "base_points": 2.0, "has_cumulative": False, "calculation_cycle": "monthly"},
            # +A 類：出勤類
            {"code": "+A01", "category": "+A", "name": "R班出勤（每日）", "base_points": 0.5, "has_cumulative": False},
            {"code": "+A02", "category": "+A", "name": "國定假日出勤", "base_points": 1.0, "has_cumulative": False},
            {"code": "+A03", "category": "+A", "name": "延長工時 1 小時", "base_points": 0.5, "has_cumulative": False},
            {"code": "+A04", "category": "+A", "name": "延長工時 2 小時", "base_points": 1.0, "has_cumulative": False},
            {"code": "+A05", "category": "+A", "name": "延長工時 3 小時", "base_points": 1.5, "has_cumulative": False},
            {"code": "+A06", "category": "+A", "name": "延長工時 4 小時", "base_points": 2.0, "has_cumulative": False},
            # +B 類：表揚類
            {"code": "+B01", "category": "+B", "name": "旅客感謝函", "base_points": 1.0, "has_cumulative": False},
            {"code": "+B02", "category": "+B", "name": "主管嘉獎", "base_points": 2.0, "has_cumulative": False},
            {"code": "+B03", "category": "+B", "name": "公司表揚", "base_points": 3.0, "has_cumulative": False},
            # +C 類：合理化建議
            {"code": "+C01", "category": "+C", "name": "合理化建議（採納）", "base_points": 1.0, "has_cumulative": False},
            {"code": "+C02", "category": "+C", "name": "合理化建議（優選）", "base_points": 2.0, "has_cumulative": False},
            {"code": "+C03", "category": "+C", "name": "合理化建議（特優）", "base_points": 3.0, "has_cumulative": False},
            # +R 類：特殊貢獻
            {"code": "+R01", "category": "+R", "name": "協助緊急事件處理", "base_points": 1.0, "has_cumulative": False},
            {"code": "+R02", "category": "+R", "name": "發現安全隱患", "base_points": 2.0, "has_cumulative": False},
            {"code": "+R03", "category": "+R", "name": "特殊貢獻（主管認定）", "base_points": 3.0, "has_cumulative": False},
        ]

        # 合併所有標準，設定預設值
        all_standards = deduction_standards + bonus_standards
        for std in all_standards:
            if 'has_cumulative' not in std:
                std['has_cumulative'] = True
            if 'calculation_cycle' not in std:
                std['calculation_cycle'] = 'yearly'
            if 'is_active' not in std:
                std['is_active'] = True

        return all_standards
