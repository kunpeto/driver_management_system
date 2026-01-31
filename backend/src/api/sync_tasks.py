"""
同步任務 API
對應 tasks.md T085: 實作手動同步 API

功能：
- 手動觸發班表同步（POST /api/sync/schedule）
- 查詢同步狀態（GET /api/sync/status/{task_id}）
- 查詢同步歷史（GET /api/sync/history）
- 管理定時任務（GET/POST /api/sync/scheduler）

Gemini Review Fix: 使用 BackgroundTasks 實作真正的背景執行
"""

from datetime import datetime
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.services.schedule_sync_service import get_schedule_sync_service
from src.tasks.scheduler import get_task_scheduler
from src.middleware.auth import get_current_user
from src.middleware.permission import require_role
from src.utils.logger import logger


router = APIRouter(prefix="/api/sync", tags=["同步任務"])


# ===== Pydantic Models =====

class SyncScheduleRequest(BaseModel):
    """班表同步請求"""
    department: Optional[Literal["淡海", "安坑"]] = Field(
        None,
        description="部門（空表示同步所有部門）"
    )
    year: int = Field(..., description="年份")
    month: int = Field(..., ge=1, le=12, description="月份")


class SyncResponse(BaseModel):
    """同步回應"""
    success: bool
    batch_id: Optional[str] = None
    message: str
    department: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None


class SyncStatusResponse(BaseModel):
    """同步狀態回應"""
    batch_id: str
    task_type: str
    department: Optional[str]
    year: int
    month: int
    status: str
    total_rows: Optional[int]
    success_count: Optional[int]
    error_count: Optional[int]
    progress: float
    started_at: Optional[str]
    completed_at: Optional[str]
    error_details: Optional[List[str]]


class SyncHistoryResponse(BaseModel):
    """同步歷史回應"""
    items: List[dict]
    total: int


class SchedulerJobResponse(BaseModel):
    """排程任務回應"""
    id: str
    name: str
    next_run_time: Optional[str]
    trigger: str


class SchedulerStatusResponse(BaseModel):
    """排程器狀態回應"""
    running: bool
    jobs: List[SchedulerJobResponse]


# ===== API Endpoints =====

@router.post("/schedule", response_model=SyncResponse)
async def sync_schedule(
    request: SyncScheduleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    手動觸發班表同步

    可同步單一部門或所有部門的班表。
    同步操作在背景執行，立即返回任務 ID 供前端輪詢進度。

    Gemini Review Fix: 使用 BackgroundTasks 實作真正的背景執行
    """
    sync_service = get_schedule_sync_service()
    username = current_user.get("username", "unknown")

    if request.department:
        # 同步單一部門
        logger.info(
            "手動觸發班表同步（單一部門）",
            department=request.department,
            year=request.year,
            month=request.month,
            triggered_by=username
        )

        # Gemini Review Fix: 先建立任務記錄，再背景執行
        batch_id = sync_service.create_sync_task(
            task_type="schedule_sync",
            department=request.department,
            year=request.year,
            month=request.month,
            triggered_by="manual",
            triggered_by_user=username,
            db=db
        )

        # 將同步操作加入背景任務
        background_tasks.add_task(
            sync_service.execute_sync,
            batch_id=batch_id,
            department=request.department,
            year=request.year,
            month=request.month
        )

        return SyncResponse(
            success=True,
            batch_id=batch_id,
            message="同步已啟動，請透過 batch_id 查詢進度",
            department=request.department,
            year=request.year,
            month=request.month
        )
    else:
        # 同步所有部門 - 為每個部門分別建立背景任務
        logger.info(
            "手動觸發班表同步（所有部門）",
            year=request.year,
            month=request.month,
            triggered_by=username
        )

        # Gemini Review Fix: 為每個部門建立獨立的背景任務
        batch_ids = []
        for department in ["淡海", "安坑"]:
            batch_id = sync_service.create_sync_task(
                task_type="schedule_sync",
                department=department,
                year=request.year,
                month=request.month,
                triggered_by="manual",
                triggered_by_user=username,
                db=db
            )
            batch_ids.append(batch_id)

            background_tasks.add_task(
                sync_service.execute_sync,
                batch_id=batch_id,
                department=department,
                year=request.year,
                month=request.month
            )

        return SyncResponse(
            success=True,
            batch_id=batch_ids[0] if batch_ids else None,  # 返回第一個 batch_id
            message=f"已啟動 {len(batch_ids)} 個部門的同步任務",
            year=request.year,
            month=request.month
        )


@router.get("/status/{batch_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    查詢同步任務狀態

    根據批次 ID 查詢同步進度與結果。
    """
    sync_service = get_schedule_sync_service()
    status = sync_service.get_sync_task_status(batch_id)

    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"找不到同步任務: {batch_id}"
        )

    return SyncStatusResponse(**status)


@router.get("/history", response_model=SyncHistoryResponse)
async def get_sync_history(
    task_type: Optional[str] = Query(None, description="任務類型篩選"),
    limit: int = Query(20, ge=1, le=100, description="限制數量"),
    current_user: dict = Depends(get_current_user)
):
    """
    查詢同步歷史

    返回最近的同步任務記錄。
    """
    sync_service = get_schedule_sync_service()
    tasks = sync_service.get_recent_sync_tasks(
        limit=limit,
        task_type=task_type
    )

    return SyncHistoryResponse(
        items=tasks,
        total=len(tasks)
    )


@router.get("/scheduler", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    current_user: dict = Depends(require_role("admin", "manager"))
):
    """
    取得排程器狀態

    僅管理員和主管可存取。
    """
    scheduler = get_task_scheduler()

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(SchedulerJobResponse(
            id=job["id"],
            name=job["name"],
            next_run_time=job["next_run_time"],
            trigger=job["trigger"]
        ))

    return SchedulerStatusResponse(
        running=scheduler.is_running,
        jobs=jobs
    )


@router.post("/scheduler/start")
async def start_scheduler(
    current_user: dict = Depends(require_role("admin"))
):
    """
    啟動排程器

    僅管理員可操作。
    """
    scheduler = get_task_scheduler()

    if scheduler.is_running:
        return {"success": True, "message": "排程器已在執行中"}

    scheduler.start()
    logger.info("排程器已由使用者啟動", user=current_user.get("username"))

    return {"success": True, "message": "排程器已啟動"}


@router.post("/scheduler/stop")
async def stop_scheduler(
    current_user: dict = Depends(require_role("admin"))
):
    """
    停止排程器

    僅管理員可操作。
    """
    scheduler = get_task_scheduler()

    if not scheduler.is_running:
        return {"success": True, "message": "排程器未在執行"}

    scheduler.stop()
    logger.info("排程器已由使用者停止", user=current_user.get("username"))

    return {"success": True, "message": "排程器已停止"}


@router.post("/scheduler/trigger/{job_id}")
async def trigger_job(
    job_id: str,
    current_user: dict = Depends(require_role("admin", "manager"))
):
    """
    立即觸發指定任務

    僅管理員和主管可操作。
    """
    scheduler = get_task_scheduler()
    success = scheduler.trigger_job(job_id)

    if success:
        logger.info(
            "任務已由使用者觸發",
            job_id=job_id,
            user=current_user.get("username")
        )
        return {"success": True, "message": f"任務 {job_id} 已觸發"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"找不到任務: {job_id}"
        )


@router.post("/scheduler/pause/{job_id}")
async def pause_job(
    job_id: str,
    current_user: dict = Depends(require_role("admin"))
):
    """
    暫停指定任務

    僅管理員可操作。
    """
    scheduler = get_task_scheduler()
    success = scheduler.pause_job(job_id)

    if success:
        logger.info(
            "任務已暫停",
            job_id=job_id,
            user=current_user.get("username")
        )
        return {"success": True, "message": f"任務 {job_id} 已暫停"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"找不到任務: {job_id}"
        )


@router.post("/scheduler/resume/{job_id}")
async def resume_job(
    job_id: str,
    current_user: dict = Depends(require_role("admin"))
):
    """
    恢復指定任務

    僅管理員可操作。
    """
    scheduler = get_task_scheduler()
    success = scheduler.resume_job(job_id)

    if success:
        logger.info(
            "任務已恢復",
            job_id=job_id,
            user=current_user.get("username")
        )
        return {"success": True, "message": f"任務 {job_id} 已恢復"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"找不到任務: {job_id}"
        )
