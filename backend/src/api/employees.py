"""
員工 CRUD API 端點
對應 tasks.md T050: 實作員工 CRUD API

提供員工資料的 CRUD 操作，支援部門篩選、離職標記、搜尋功能。
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import (
    PermissionChecker,
    require_admin,
    require_role,
    Role,
)
from src.services.employee_service import (
    DuplicateEmployeeError,
    EmployeeNotFoundError,
    EmployeeService,
    EmployeeServiceError,
    InvalidEmployeeIdError,
)

router = APIRouter()


# ============================================================
# Pydantic 模型
# ============================================================

class EmployeeCreate(BaseModel):
    """建立員工請求"""
    employee_id: str = Field(
        ...,
        min_length=9,
        max_length=20,
        description="員工編號（如 1011M0095）"
    )
    employee_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="員工姓名"
    )
    current_department: str = Field(
        ...,
        description="部門（淡海 或 安坑）"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="電話"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="電子郵件"
    )
    emergency_contact: Optional[str] = Field(
        None,
        max_length=50,
        description="緊急聯絡人"
    )
    emergency_phone: Optional[str] = Field(
        None,
        max_length=20,
        description="緊急聯絡電話"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "employee_id": "1011M0095",
                    "employee_name": "張三",
                    "current_department": "淡海",
                    "phone": "0912345678",
                    "email": "example@mail.com",
                    "emergency_contact": "李四",
                    "emergency_phone": "0987654321"
                }
            ]
        }
    }


class EmployeeUpdate(BaseModel):
    """更新員工請求"""
    employee_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="員工姓名"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="電話"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="電子郵件"
    )
    emergency_contact: Optional[str] = Field(
        None,
        max_length=50,
        description="緊急聯絡人"
    )
    emergency_phone: Optional[str] = Field(
        None,
        max_length=20,
        description="緊急聯絡電話"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "employee_name": "張三",
                    "phone": "0912345678",
                    "email": "new_email@mail.com"
                }
            ]
        }
    }


class EmployeeResponse(BaseModel):
    """員工回應"""
    id: int
    employee_id: str
    employee_name: str
    current_department: str
    hire_year_month: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    is_resigned: bool

    model_config = {"from_attributes": True}


class EmployeeListResponse(BaseModel):
    """員工列表回應"""
    total: int
    items: list[EmployeeResponse]


class EmployeeStatisticsResponse(BaseModel):
    """員工統計回應"""
    total: int
    active: int
    resigned: int
    by_department: dict


# ============================================================
# API 端點
# ============================================================

@router.get(
    "",
    response_model=EmployeeListResponse,
    summary="取得員工列表",
    description="取得員工列表，支援部門篩選、離職狀態篩選、關鍵字搜尋"
)
def list_employees(
    department: Optional[str] = Query(None, description="篩選部門（淡海、安坑）"),
    include_resigned: bool = Query(False, description="是否包含離職員工"),
    search: Optional[str] = Query(None, description="搜尋關鍵字（員工編號或姓名）"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="限制筆數"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    取得員工列表

    - 依角色預設篩選部門：Staff 預設顯示所屬部門，Manager/Admin 顯示全部
    - 所有登入使用者都可以查看全部員工（唯讀）
    """
    service = EmployeeService(db)

    # 取得使用者預設部門
    if department is None:
        department = PermissionChecker.get_default_department(current_user)

    employees = service.list_all(
        include_resigned=include_resigned,
        department=department,
        search=search,
        skip=skip,
        limit=limit
    )

    total = service.count(
        include_resigned=include_resigned,
        department=department,
        search=search
    )

    return EmployeeListResponse(
        total=total,
        items=[EmployeeResponse.model_validate(emp) for emp in employees]
    )


@router.get(
    "/statistics",
    response_model=EmployeeStatisticsResponse,
    summary="取得員工統計",
    description="取得員工統計資料（在職、離職、部門分布）"
)
def get_employee_statistics(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得員工統計資料"""
    service = EmployeeService(db)
    stats = service.get_statistics()

    return EmployeeStatisticsResponse(**stats)


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="取得員工詳情",
    description="根據員工 ID（數字）取得員工詳細資料"
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得員工詳情"""
    service = EmployeeService(db)
    employee = service.get_by_id(employee_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"員工 ID {employee_id} 不存在"
        )

    return EmployeeResponse.model_validate(employee)


@router.get(
    "/by-employee-id/{employee_code}",
    response_model=EmployeeResponse,
    summary="根據員工編號取得員工",
    description="根據員工編號（如 1011M0095）取得員工詳細資料"
)
def get_employee_by_code(
    employee_code: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """根據員工編號取得員工"""
    service = EmployeeService(db)
    employee = service.get_by_employee_id(employee_code)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"員工編號 '{employee_code}' 不存在"
        )

    return EmployeeResponse.model_validate(employee)


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="建立員工",
    description="建立新員工（需要對應部門的編輯權限）"
)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    建立新員工

    - 員工編號會自動解析入職年月
    - Staff 只能建立本部門員工
    - Manager/Admin 可建立任何部門員工
    """
    # 檢查部門編輯權限
    if not PermissionChecker.can_edit_department(current_user, data.current_department):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權限在 {data.current_department} 部門建立員工"
        )

    service = EmployeeService(db)

    try:
        employee = service.create(
            employee_id=data.employee_id,
            employee_name=data.employee_name,
            current_department=data.current_department,
            phone=data.phone,
            email=data.email,
            emergency_contact=data.emergency_contact,
            emergency_phone=data.emergency_phone
        )
        return EmployeeResponse.model_validate(employee)

    except InvalidEmployeeIdError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateEmployeeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except EmployeeServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="更新員工",
    description="更新員工資料（需要對應部門的編輯權限）"
)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    更新員工資料

    注意：員工編號、部門、入職年月不可透過此方法修改。
    部門變更需透過調動流程（/employees/{id}/transfer）。
    """
    service = EmployeeService(db)

    # 先取得員工確認存在
    employee = service.get_by_id(employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"員工 ID {employee_id} 不存在"
        )

    # 檢查部門編輯權限
    if not PermissionChecker.can_edit_department(current_user, employee.current_department):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權限編輯 {employee.current_department} 部門的員工"
        )

    try:
        employee = service.update(
            id=employee_id,
            employee_name=data.employee_name,
            phone=data.phone,
            email=data.email,
            emergency_contact=data.emergency_contact,
            emergency_phone=data.emergency_phone
        )
        return EmployeeResponse.model_validate(employee)

    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{employee_id}/resign",
    response_model=EmployeeResponse,
    summary="標記員工離職",
    description="將員工標記為離職狀態（需要對應部門的編輯權限）"
)
def resign_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """標記員工離職"""
    service = EmployeeService(db)

    # 先取得員工確認存在
    employee = service.get_by_id(employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"員工 ID {employee_id} 不存在"
        )

    # 檢查部門編輯權限
    if not PermissionChecker.can_edit_department(current_user, employee.current_department):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權限編輯 {employee.current_department} 部門的員工"
        )

    try:
        employee = service.mark_resigned(employee_id)
        return EmployeeResponse.model_validate(employee)

    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{employee_id}/activate",
    response_model=EmployeeResponse,
    summary="標記員工復職",
    description="將離職員工標記為在職狀態（需要對應部門的編輯權限）"
)
def activate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """標記員工復職"""
    service = EmployeeService(db)

    # 先取得員工確認存在
    employee = service.get_by_id(employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"員工 ID {employee_id} 不存在"
        )

    # 檢查部門編輯權限
    if not PermissionChecker.can_edit_department(current_user, employee.current_department):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權限編輯 {employee.current_department} 部門的員工"
        )

    try:
        employee = service.mark_active(employee_id)
        return EmployeeResponse.model_validate(employee)

    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除員工",
    description="永久刪除員工資料（僅管理員可操作，建議改用離職標記）"
)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    刪除員工

    注意：此操作會永久刪除員工資料，建議使用離職標記（/employees/{id}/resign）。
    僅管理員可執行此操作。
    """
    service = EmployeeService(db)

    try:
        service.delete(employee_id)

    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/department/{department}",
    response_model=EmployeeListResponse,
    summary="取得部門員工",
    description="取得指定部門的所有員工"
)
def list_department_employees(
    department: str,
    include_resigned: bool = Query(False, description="是否包含離職員工"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得指定部門的所有員工"""
    service = EmployeeService(db)

    employees = service.list_by_department(
        department=department,
        include_resigned=include_resigned
    )

    return EmployeeListResponse(
        total=len(employees),
        items=[EmployeeResponse.model_validate(emp) for emp in employees]
    )


@router.get(
    "/check/{employee_code}",
    summary="檢查員工編號是否存在",
    description="快速檢查員工編號是否已被使用"
)
def check_employee_exists(
    employee_code: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """檢查員工編號是否存在"""
    service = EmployeeService(db)
    exists = service.exists(employee_code)

    return {"employee_id": employee_code, "exists": exists}
