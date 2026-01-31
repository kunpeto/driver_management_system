"""
RouteStandardTimeService 勤務標準時間管理服務
對應 tasks.md T105: 實作勤務標準時間管理服務

提供勤務標準時間的 CRUD 操作、Excel 匯入驗證等功能。
"""

from typing import Optional

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.google_oauth_token import Department
from src.models.route_standard_time import RouteStandardTime


class RouteStandardTimeServiceError(Exception):
    """勤務標準時間服務錯誤"""
    pass


class DuplicateRouteError(RouteStandardTimeServiceError):
    """勤務代碼重複錯誤"""
    pass


class RouteNotFoundError(RouteStandardTimeServiceError):
    """勤務標準時間不存在錯誤"""
    pass


class RouteInUseError(RouteStandardTimeServiceError):
    """勤務標準時間正在使用中錯誤"""
    pass


class RouteStandardTimeService:
    """
    勤務標準時間服務

    提供勤務標準時間的 CRUD 操作。
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
        department: str,
        route_code: str,
        route_name: str,
        standard_minutes: int,
        description: Optional[str] = None
    ) -> RouteStandardTime:
        """
        建立勤務標準時間

        如果相同部門/勤務代碼已存在但為停用狀態，會重新啟用並更新資料。

        Args:
            department: 部門
            route_code: 勤務代碼
            route_name: 勤務名稱
            standard_minutes: 標準分鐘數
            description: 說明備註

        Returns:
            RouteStandardTime: 新建立或重新啟用的勤務標準時間

        Raises:
            DuplicateRouteError: 勤務代碼已存在且為啟用狀態
            RouteStandardTimeServiceError: 參數驗證錯誤
        """
        # 驗證部門
        self._validate_department(department)

        # 驗證分鐘數
        if standard_minutes < 0:
            raise RouteStandardTimeServiceError("標準分鐘數不可為負數")

        normalized_code = route_code.strip().upper()

        # 檢查是否已存在（包含停用的）
        existing = self.get_by_code(department, normalized_code, include_inactive=True)

        if existing:
            if existing.is_active:
                # 已啟用的記錄，報錯
                raise DuplicateRouteError(
                    f"部門 '{department}' 的勤務代碼 '{route_code}' 已存在"
                )
            else:
                # 已停用的記錄，重新啟用並更新資料
                existing.route_name = route_name.strip()
                existing.standard_minutes = standard_minutes
                existing.description = description
                existing.is_active = True
                self.db.commit()
                self.db.refresh(existing)
                return existing

        # 新建記錄
        route = RouteStandardTime(
            department=department,
            route_code=normalized_code,
            route_name=route_name.strip(),
            standard_minutes=standard_minutes,
            description=description,
            is_active=True
        )

        try:
            self.db.add(route)
            self.db.commit()
            self.db.refresh(route)
            return route
        except IntegrityError:
            self.db.rollback()
            raise DuplicateRouteError(
                f"部門 '{department}' 的勤務代碼 '{route_code}' 已存在"
            )

    def get_by_id(self, id: int) -> Optional[RouteStandardTime]:
        """根據 ID 取得勤務標準時間"""
        return self.db.query(RouteStandardTime).filter(
            RouteStandardTime.id == id
        ).first()

    def get_by_code(
        self,
        department: str,
        route_code: str,
        include_inactive: bool = False
    ) -> Optional[RouteStandardTime]:
        """根據部門和勤務代碼取得勤務標準時間"""
        query = self.db.query(RouteStandardTime).filter(
            and_(
                RouteStandardTime.department == department,
                RouteStandardTime.route_code == route_code.strip().upper()
            )
        )
        if not include_inactive:
            query = query.filter(RouteStandardTime.is_active == True)
        return query.first()

    def update(
        self,
        id: int,
        route_name: Optional[str] = None,
        standard_minutes: Optional[int] = None,
        description: Optional[str] = None
    ) -> RouteStandardTime:
        """
        更新勤務標準時間

        注意：部門和勤務代碼不可透過此方法修改。
        變更僅影響「變更日期之後」的駕駛時數計算。

        Args:
            id: 勤務標準時間 ID
            route_name: 勤務名稱
            standard_minutes: 標準分鐘數
            description: 說明備註

        Returns:
            RouteStandardTime: 更新後的勤務標準時間

        Raises:
            RouteNotFoundError: 勤務標準時間不存在
        """
        route = self.get_by_id(id)
        if not route:
            raise RouteNotFoundError(f"勤務標準時間 ID {id} 不存在")

        if route_name is not None:
            route.route_name = route_name.strip()
        if standard_minutes is not None:
            if standard_minutes < 0:
                raise RouteStandardTimeServiceError("標準分鐘數不可為負數")
            route.standard_minutes = standard_minutes
        if description is not None:
            route.description = description

        self.db.commit()
        self.db.refresh(route)
        return route

    def soft_delete(self, id: int) -> RouteStandardTime:
        """
        軟刪除勤務標準時間

        將 is_active 設為 False，保留歷史資料。

        Args:
            id: 勤務標準時間 ID

        Returns:
            RouteStandardTime: 更新後的勤務標準時間

        Raises:
            RouteNotFoundError: 勤務標準時間不存在
        """
        route = self.get_by_id(id)
        if not route:
            raise RouteNotFoundError(f"勤務標準時間 ID {id} 不存在")

        route.is_active = False
        self.db.commit()
        self.db.refresh(route)
        return route

    def restore(self, id: int) -> RouteStandardTime:
        """
        恢復已刪除的勤務標準時間

        Args:
            id: 勤務標準時間 ID

        Returns:
            RouteStandardTime: 更新後的勤務標準時間

        Raises:
            RouteNotFoundError: 勤務標準時間不存在
        """
        route = self.get_by_id(id)
        if not route:
            raise RouteNotFoundError(f"勤務標準時間 ID {id} 不存在")

        route.is_active = True
        self.db.commit()
        self.db.refresh(route)
        return route

    # ============================================================
    # 查詢操作
    # ============================================================

    def list_all(
        self,
        department: Optional[str] = None,
        include_inactive: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[RouteStandardTime]:
        """
        列出勤務標準時間

        Args:
            department: 篩選部門
            include_inactive: 是否包含已刪除的
            search: 搜尋關鍵字（勤務代碼或名稱）
            skip: 跳過筆數
            limit: 限制筆數

        Returns:
            list[RouteStandardTime]: 勤務標準時間列表
        """
        query = self.db.query(RouteStandardTime)

        # 篩選啟用狀態
        if not include_inactive:
            query = query.filter(RouteStandardTime.is_active == True)

        # 篩選部門
        if department:
            query = query.filter(RouteStandardTime.department == department)

        # 搜尋
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (RouteStandardTime.route_code.like(search_pattern)) |
                (RouteStandardTime.route_name.like(search_pattern))
            )

        # 排序與分頁
        query = query.order_by(
            RouteStandardTime.department,
            RouteStandardTime.route_code
        )
        query = query.offset(skip).limit(limit)

        return query.all()

    def count(
        self,
        department: Optional[str] = None,
        include_inactive: bool = False
    ) -> int:
        """計算勤務標準時間數量"""
        query = self.db.query(RouteStandardTime)

        if not include_inactive:
            query = query.filter(RouteStandardTime.is_active == True)

        if department:
            query = query.filter(RouteStandardTime.department == department)

        return query.count()

    def list_by_department(
        self,
        department: str,
        include_inactive: bool = False
    ) -> list[RouteStandardTime]:
        """列出指定部門的勤務標準時間"""
        return self.list_all(
            department=department,
            include_inactive=include_inactive,
            limit=10000
        )

    def get_minutes_map(self, department: str) -> dict[str, int]:
        """
        取得部門的勤務代碼到分鐘數映射

        Args:
            department: 部門

        Returns:
            dict: {route_code: standard_minutes}
        """
        routes = self.list_by_department(department)
        return {route.route_code: route.standard_minutes for route in routes}

    # ============================================================
    # Excel 匯入
    # ============================================================

    def validate_import_data(
        self,
        rows: list[dict],
        department: str
    ) -> tuple[list[dict], list[str]]:
        """
        驗證匯入資料

        Args:
            rows: 匯入的資料列表，每列為 dict
            department: 目標部門

        Returns:
            tuple: (有效資料列表, 錯誤訊息列表)
        """
        valid_rows = []
        errors = []

        required_fields = ["route_code", "route_name", "standard_minutes"]

        for i, row in enumerate(rows, start=2):  # Excel 從第 2 行開始（第 1 行為標題）
            row_errors = []

            # 檢查必填欄位
            for field in required_fields:
                if field not in row or row[field] is None or str(row[field]).strip() == "":
                    row_errors.append(f"缺少必填欄位 '{field}'")

            if row_errors:
                errors.append(f"第 {i} 行: {', '.join(row_errors)}")
                continue

            # 驗證標準分鐘數
            try:
                minutes = int(row["standard_minutes"])
                if minutes < 0:
                    row_errors.append("標準分鐘數不可為負數")
            except (ValueError, TypeError):
                row_errors.append("標準分鐘數必須為整數")

            if row_errors:
                errors.append(f"第 {i} 行: {', '.join(row_errors)}")
                continue

            # 資料正規化
            valid_rows.append({
                "route_code": str(row["route_code"]).strip().upper(),
                "route_name": str(row["route_name"]).strip(),
                "standard_minutes": minutes,
                "description": str(row.get("description", "")).strip() or None
            })

        return valid_rows, errors

    def bulk_import(
        self,
        rows: list[dict],
        department: str,
        update_existing: bool = True
    ) -> dict:
        """
        批次匯入勤務標準時間

        Args:
            rows: 已驗證的資料列表
            department: 目標部門
            update_existing: 是否更新已存在的資料

        Returns:
            dict: 匯入結果統計
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for row in rows:
            try:
                existing = self.get_by_code(
                    department,
                    row["route_code"],
                    include_inactive=True
                )

                if existing:
                    if update_existing:
                        existing.route_name = row["route_name"]
                        existing.standard_minutes = row["standard_minutes"]
                        existing.description = row["description"]
                        existing.is_active = True
                        updated += 1
                    else:
                        skipped += 1
                else:
                    route = RouteStandardTime(
                        department=department,
                        route_code=row["route_code"],
                        route_name=row["route_name"],
                        standard_minutes=row["standard_minutes"],
                        description=row["description"],
                        is_active=True
                    )
                    self.db.add(route)
                    created += 1

            except Exception as e:
                errors.append(f"勤務代碼 '{row['route_code']}': {str(e)}")

        self.db.commit()

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total": len(rows)
        }

    # ============================================================
    # 輔助方法
    # ============================================================

    def _validate_department(self, department: str) -> None:
        """驗證部門名稱"""
        valid_departments = [Department.DANHAI.value, Department.ANKENG.value]
        if department not in valid_departments:
            raise RouteStandardTimeServiceError(
                f"無效的部門名稱 '{department}'，有效值為：{valid_departments}"
            )

    def exists(self, department: str, route_code: str) -> bool:
        """檢查勤務代碼是否存在"""
        return self.get_by_code(department, route_code) is not None
