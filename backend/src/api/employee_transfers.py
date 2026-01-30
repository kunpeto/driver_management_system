"""
員工調動 API 端點
對應 tasks.md T051: 實作員工調動 API

提供員工調動記錄、歷史查詢、統計功能。
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.middleware.auth import TokenData, get_current_user
from src.middleware.permission import (
    PermissionChecker,
    require_admin,
    Role,
)
from src.services.employee_service import EmployeeNotFoundError, EmployeeService
from src.services.employee_transfer_service import (
    EmployeeTransferService,
    EmployeeTransferServiceError,
    SameDepartmentError,
    TransferNotFoundError,
)

router = APIRouter()


# ============================================================
# Pydantic 模型
# ============================================================

class TransferRequest(BaseModel):
    """調動請求"""
    to_department: str = Field(
        ...,
        description="目標部門（淡海 或 安坑）"
    )
    transfer_date: date = Field(
        ...,
        description="調動日期"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="調動原因"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "to_department": "安坑",
                    "transfer_date": "2026-02-01",
                    "reason": "人力調配"
                }
            ]
        }
    }


class TransferResponse(BaseModel):
    """調動記錄回應"""
    id: int
    employee_id: str
    from_department: str
    to_department: str
    transfer_date: date
    reason: Optional[str]
    created_by: str
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class TransferListResponse(BaseModel):
    """調動記錄列表回應"""
    total: int
    items: list[TransferResponse]


class TransferStatisticsResponse(BaseModel):
    """調動統計回應"""
    total: int
    recent_30_days: int
    this_year: int
    by_department: dict


# ============================================================
# API 端點
# ============================================================

@router.post(
    "/{employee_id}/transfer",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="執行員工調動",
    description="將員工調動到另一個部門（需要對員工現職部門的編輯權限）"
)
def transfer_employee(
    employee_id: int,
    data: TransferRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    執行員工調動

    此操作會：
    1. 建立調動記錄
    2. 更新員工的現職部門

    需要對員工現職部門（來源部門）有編輯權限。
    """
    # 先取得員工資料
    employee_service = EmployeeService(db)
    employee = employee_service.get_by_id(employee_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"員工 ID {employee_id} 不存在"
        )

    # 檢查對員工現職部門（來源部門）的編輯權限
    # 修正：權限應基於員工目前歸屬的部門，而非目標部門
    if not PermissionChecker.can_edit_department(current_user, employee.current_department):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權限調動 {employee.current_department} 部門的員工"
        )

    service = EmployeeTransferService(db)

    try:
        transfer = service.transfer(
            employee_id=employee_id,
            to_department=data.to_department,
            transfer_date=data.transfer_date,
            reason=data.reason,
            created_by=current_user.username
        )
        return TransferResponse.model_validate(transfer)

    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except SameDepartmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except EmployeeTransferServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/by-employee-id/{employee_code}/transfer",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="根據員工編號執行調動",
    description="根據員工編號（如 1011M0095）將員工調動到另一個部門（需要對員工現職部門的編輯權限）"
)
def transfer_employee_by_code(
    employee_code: str,
    data: TransferRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """根據員工編號執行調動"""
    # 先取得員工資料
    employee_service = EmployeeService(db)
    employee = employee_service.get_by_employee_id(employee_code)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"員工編號 '{employee_code}' 不存在"
        )

    # 檢查對員工現職部門（來源部門）的編輯權限
    # 修正：權限應基於員工目前歸屬的部門，而非目標部門
    if not PermissionChecker.can_edit_department(current_user, employee.current_department):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權限調動 {employee.current_department} 部門的員工"
        )

    service = EmployeeTransferService(db)

    try:
        transfer = service.transfer_by_employee_id(
            employee_id=employee_code,
            to_department=data.to_department,
            transfer_date=data.transfer_date,
            reason=data.reason,
            created_by=current_user.username
        )
        return TransferResponse.model_validate(transfer)

    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except SameDepartmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except EmployeeTransferServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{employee_id}/transfers",
    response_model=TransferListResponse,
    summary="取得員工調動歷史",
    description="取得指定員工的調動歷史記錄"
)
def get_employee_transfer_history(
    employee_id: int,
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="限制筆數"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得員工調動歷史"""
    service = EmployeeTransferService(db)

    try:
        transfers = service.get_transfer_history(
            employee_id=employee_id,
            skip=skip,
            limit=limit
        )

        return TransferListResponse(
            total=len(transfers),
            items=[TransferResponse.model_validate(t) for t in transfers]
        )

    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/by-employee-id/{employee_code}/transfers",
    response_model=TransferListResponse,
    summary="根據員工編號取得調動歷史",
    description="根據員工編號取得調動歷史記錄"
)
def get_employee_transfer_history_by_code(
    employee_code: str,
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="限制筆數"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """根據員工編號取得調動歷史"""
    service = EmployeeTransferService(db)

    transfers = service.get_transfer_history_by_employee_id(
        employee_id=employee_code,
        skip=skip,
        limit=limit
    )

    return TransferListResponse(
        total=len(transfers),
        items=[TransferResponse.model_validate(t) for t in transfers]
    )


@router.get(
    "/transfers/recent",
    response_model=TransferListResponse,
    summary="取得最近調動記錄",
    description="取得最近的調動記錄，可按天數和部門篩選"
)
def list_recent_transfers(
    days: int = Query(30, ge=1, le=365, description="最近天數"),
    department: Optional[str] = Query(None, description="篩選部門（調入或調出）"),
    skip: int = Query(0, ge=0, description="跳過筆數"),
    limit: int = Query(100, ge=1, le=1000, description="限制筆數"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得最近調動記錄"""
    service = EmployeeTransferService(db)

    transfers = service.list_recent_transfers(
        days=days,
        department=department,
        skip=skip,
        limit=limit
    )

    return TransferListResponse(
        total=len(transfers),
        items=[TransferResponse.model_validate(t) for t in transfers]
    )


@router.get(
    "/transfers/statistics",
    response_model=TransferStatisticsResponse,
    summary="取得調動統計",
    description="取得調動統計資料"
)
def get_transfer_statistics(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得調動統計"""
    service = EmployeeTransferService(db)
    stats = service.get_statistics()

    return TransferStatisticsResponse(**stats)


@router.get(
    "/transfers/{transfer_id}",
    response_model=TransferResponse,
    summary="取得調動記錄詳情",
    description="根據調動記錄 ID 取得詳細資料"
)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """取得調動記錄詳情"""
    service = EmployeeTransferService(db)
    transfer = service.get_transfer_by_id(transfer_id)

    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"調動記錄 ID {transfer_id} 不存在"
        )

    return TransferResponse.model_validate(transfer)


@router.delete(
    "/transfers/{transfer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="刪除調動記錄",
    description="刪除調動記錄（僅管理員可操作，注意：不會還原員工部門）"
)
def delete_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_admin())
):
    """
    刪除調動記錄

    注意：此操作僅刪除記錄，不會還原員工的部門。
    如需還原，請執行新的調動操作。
    """
    service = EmployeeTransferService(db)

    try:
        service.delete_transfer(transfer_id)

    except TransferNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
