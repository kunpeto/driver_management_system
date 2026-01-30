"""
班表同步服務
對應 tasks.md T082: 實作班表同步服務

功能：
- 從 Google Sheets 讀取班表資料
- 解析班表並寫入資料庫
- 處理同步錯誤與重試
- 記錄同步歷史

Gemini Review Fix:
- 交易原子性：刪除與寫入在同一 Transaction 中
- 背景執行：拆分為 create_task 與 execute_sync
- 詳細錯誤日誌：輸出 stack trace
"""

import json
import traceback
import uuid
from datetime import datetime, date
from typing import Optional, List, Literal, Dict, Any

from sqlalchemy import delete, and_
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.models.schedule import Schedule, SyncTask
from src.models.google_oauth_token import Department
from src.services.google_sheets_reader import GoogleSheetsReader, get_google_sheets_reader
from src.services.schedule_parser import ScheduleParser, get_schedule_parser, ParsedShift
from src.utils.logger import logger


class ScheduleSyncService:
    """
    班表同步服務

    負責將 Google Sheets 班表資料同步到資料庫。

    Gemini Review Fix: 支援背景執行模式，先建立任務再執行同步。
    """

    def __init__(
        self,
        sheets_reader: Optional[GoogleSheetsReader] = None,
        parser: Optional[ScheduleParser] = None
    ):
        self._reader = sheets_reader or get_google_sheets_reader()
        self._parser = parser or get_schedule_parser()

    def create_sync_task(
        self,
        task_type: str,
        department: Optional[str],
        year: int,
        month: int,
        triggered_by: str = "manual",
        triggered_by_user: Optional[str] = None,
        db: Optional[Session] = None
    ) -> str:
        """
        建立同步任務記錄（Gemini Review Fix: 拆分出來支援背景執行）

        Args:
            task_type: 任務類型
            department: 部門
            year: 年份
            month: 月份
            triggered_by: 觸發方式
            triggered_by_user: 觸發使用者
            db: 資料庫會話

        Returns:
            str: 批次 ID
        """
        db_session = db or next(get_db())
        close_db = db is None

        try:
            task = SyncTask(
                batch_id=str(uuid.uuid4()),
                task_type=task_type,
                department=department,
                target_year=year,
                target_month=month,
                status="pending",
                triggered_by=triggered_by,
                triggered_by_user=triggered_by_user
            )
            db_session.add(task)
            db_session.commit()
            db_session.refresh(task)

            logger.info(
                "建立同步任務",
                batch_id=task.batch_id,
                task_type=task_type,
                department=department
            )

            return task.batch_id

        finally:
            if close_db:
                db_session.close()

    def _update_task_status(
        self,
        db: Session,
        task: SyncTask,
        status: str,
        total_rows: Optional[int] = None,
        success_count: Optional[int] = None,
        error_count: Optional[int] = None,
        error_details: Optional[List[str]] = None,
        commit: bool = True
    ):
        """
        更新任務狀態

        Args:
            db: 資料庫會話
            task: 任務記錄
            status: 新狀態
            total_rows: 總行數
            success_count: 成功數量
            error_count: 錯誤數量
            error_details: 錯誤詳情
            commit: 是否提交（Gemini Review Fix: 支援外部控制 commit）
        """
        task.status = status

        if total_rows is not None:
            task.total_rows = total_rows
        if success_count is not None:
            task.success_count = success_count
        if error_count is not None:
            task.error_count = error_count
        if error_details is not None:
            task.error_details = json.dumps(error_details, ensure_ascii=False)

        if status == "running":
            task.started_at = datetime.now()
        elif status in ("completed", "failed"):
            task.completed_at = datetime.now()

        if commit:
            db.commit()

    def _delete_existing_schedules(
        self,
        db: Session,
        department: str,
        year: int,
        month: int
    ) -> int:
        """
        刪除現有的班表資料（不提交，由外層控制 Transaction）

        Gemini Review Fix: 移除內部 commit，交由外層統一管理交易

        Args:
            db: 資料庫會話
            department: 部門
            year: 年份
            month: 月份

        Returns:
            int: 刪除的記錄數
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        result = db.execute(
            delete(Schedule).where(
                and_(
                    Schedule.department == department,
                    Schedule.schedule_date >= start_date,
                    Schedule.schedule_date < end_date
                )
            )
        )
        # Gemini Review Fix: 不在此處 commit，由外層統一管理

        deleted_count = result.rowcount
        logger.info(
            "刪除現有班表資料（未提交）",
            department=department,
            year=year,
            month=month,
            deleted_count=deleted_count
        )
        return deleted_count

    def _insert_schedules(
        self,
        db: Session,
        shifts: List[ParsedShift],
        department: str,
        batch_id: str,
        sync_source: str
    ) -> tuple[int, int, List[str]]:
        """
        批次寫入班表資料（不提交，由外層控制 Transaction）

        Gemini Review Fix:
        - 移除內部 commit
        - 簡化為純 INSERT（因為已先刪除舊資料）
        - 增加詳細錯誤日誌

        Args:
            db: 資料庫會話
            shifts: 解析後的班別列表
            department: 部門
            batch_id: 批次 ID
            sync_source: 同步來源

        Returns:
            tuple: (成功數, 錯誤數, 錯誤訊息列表)
        """
        success_count = 0
        error_count = 0
        errors = []

        synced_at = datetime.now()

        for shift in shifts:
            try:
                schedule = Schedule(
                    employee_id=shift.employee_id,
                    employee_name=shift.employee_name,
                    department=department,
                    schedule_date=shift.schedule_date,
                    shift_code=shift.shift_code,
                    shift_type=shift.shift_type,
                    start_time=shift.start_time,
                    end_time=shift.end_time,
                    overtime_hours=shift.overtime_hours,
                    sync_source=sync_source,
                    sync_batch_id=batch_id,
                    synced_at=synced_at
                )
                db.add(schedule)
                success_count += 1

            except Exception as e:
                error_count += 1
                error_msg = f"員工 {shift.employee_id} 日期 {shift.schedule_date}: {str(e)}"
                errors.append(error_msg)
                # Gemini Review Fix: 輸出詳細 stack trace
                logger.error(
                    "班表寫入失敗",
                    employee_id=shift.employee_id,
                    schedule_date=str(shift.schedule_date),
                    error=str(e),
                    traceback=traceback.format_exc()
                )

        # Gemini Review Fix: 不在此處 commit，由外層統一管理
        return (success_count, error_count, errors)

    def execute_sync(
        self,
        batch_id: str,
        department: str,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        執行同步任務（Gemini Review Fix: 拆分出來的執行方法，支援背景呼叫）

        此方法實作交易原子性：刪除與寫入在同一 Transaction 中。

        Args:
            batch_id: 批次 ID
            department: 部門
            year: 年份
            month: 月份

        Returns:
            dict: 同步結果
        """
        db_session = next(get_db())

        try:
            # 取得任務記錄
            task = db_session.query(SyncTask).filter(
                SyncTask.batch_id == batch_id
            ).first()

            if not task:
                logger.error("找不到同步任務", batch_id=batch_id)
                return {
                    "success": False,
                    "batch_id": batch_id,
                    "error": "找不到同步任務"
                }

            # 更新狀態為執行中
            self._update_task_status(db_session, task, "running")

            logger.info(
                "開始執行班表同步",
                batch_id=batch_id,
                department=department,
                year=year,
                month=month
            )

            # 1. 讀取 Google Sheets
            read_result = self._reader.read_schedule_sheet(
                department=department,
                year=year,
                month=month
            )

            if not read_result.success:
                self._update_task_status(
                    db_session, task, "failed",
                    error_details=[read_result.error or "讀取失敗"]
                )
                return {
                    "success": False,
                    "batch_id": batch_id,
                    "error": read_result.error,
                    "department": department,
                    "year": year,
                    "month": month
                }

            # 2. 解析班表資料
            parse_result = self._parser.parse(
                data=read_result.data,
                department=department,
                year=year,
                month=month
            )

            if not parse_result.success:
                self._update_task_status(
                    db_session, task, "failed",
                    total_rows=parse_result.total_rows,
                    error_details=parse_result.errors
                )
                return {
                    "success": False,
                    "batch_id": batch_id,
                    "error": "班表解析失敗",
                    "errors": parse_result.errors,
                    "department": department,
                    "year": year,
                    "month": month
                }

            # ============================================================
            # Gemini Review Fix: 交易原子性 - 刪除與寫入在同一 Transaction
            # ============================================================
            try:
                # 3. 刪除現有資料（不 commit）
                self._delete_existing_schedules(db_session, department, year, month)

                # 4. 寫入新資料（不 commit）
                sync_source = f"{department}_schedule_{year}{month:02d}"
                success_count, error_count, errors = self._insert_schedules(
                    db=db_session,
                    shifts=parse_result.shifts,
                    department=department,
                    batch_id=batch_id,
                    sync_source=sync_source
                )

                # 5. 統一提交 Transaction
                db_session.commit()

                logger.info(
                    "班表同步 Transaction 提交成功",
                    batch_id=batch_id,
                    success_count=success_count,
                    error_count=error_count
                )

            except Exception as e:
                # Gemini Review Fix: 發生錯誤時 Rollback
                db_session.rollback()
                logger.error(
                    "班表同步 Transaction 失敗，已 Rollback",
                    batch_id=batch_id,
                    error=str(e),
                    traceback=traceback.format_exc()
                )

                self._update_task_status(
                    db_session, task, "failed",
                    error_details=[f"Transaction 失敗: {str(e)}"]
                )

                return {
                    "success": False,
                    "batch_id": batch_id,
                    "error": f"Transaction 失敗: {str(e)}",
                    "department": department,
                    "year": year,
                    "month": month
                }

            # 合併解析警告
            all_errors = parse_result.errors + parse_result.warnings + errors

            # 6. 更新任務狀態為完成
            final_status = "completed"
            self._update_task_status(
                db_session, task, final_status,
                total_rows=len(parse_result.shifts),
                success_count=success_count,
                error_count=error_count,
                error_details=all_errors if all_errors else None
            )

            logger.info(
                "班表同步完成",
                batch_id=batch_id,
                department=department,
                year=year,
                month=month,
                success_count=success_count,
                error_count=error_count
            )

            return {
                "success": True,
                "batch_id": batch_id,
                "department": department,
                "year": year,
                "month": month,
                "total_rows": len(parse_result.shifts),
                "success_count": success_count,
                "error_count": error_count,
                "warnings": parse_result.warnings[:10] if parse_result.warnings else []
            }

        except Exception as e:
            logger.error(
                "班表同步例外",
                batch_id=batch_id,
                department=department,
                year=year,
                month=month,
                error=str(e),
                traceback=traceback.format_exc()
            )

            # 嘗試更新任務狀態
            try:
                task = db_session.query(SyncTask).filter(
                    SyncTask.batch_id == batch_id
                ).first()
                if task:
                    self._update_task_status(
                        db_session, task, "failed",
                        error_details=[str(e)]
                    )
            except Exception:
                pass

            return {
                "success": False,
                "batch_id": batch_id,
                "error": str(e),
                "department": department,
                "year": year,
                "month": month
            }

        finally:
            db_session.close()

    def sync_department(
        self,
        department: Literal["淡海", "安坑"],
        year: int,
        month: int,
        triggered_by: str = "manual",
        triggered_by_user: Optional[str] = None,
        db: Optional[Session] = None
    ) -> dict:
        """
        同步指定部門的班表（同步執行版本，適用於定時任務）

        Args:
            department: 部門
            year: 年份
            month: 月份
            triggered_by: 觸發方式（auto/manual）
            triggered_by_user: 觸發使用者
            db: 資料庫會話（可選）

        Returns:
            dict: 同步結果
        """
        # 建立任務
        batch_id = self.create_sync_task(
            task_type="schedule_sync",
            department=department,
            year=year,
            month=month,
            triggered_by=triggered_by,
            triggered_by_user=triggered_by_user,
            db=db
        )

        # 執行同步
        return self.execute_sync(
            batch_id=batch_id,
            department=department,
            year=year,
            month=month
        )

    def sync_all_departments(
        self,
        year: int,
        month: int,
        triggered_by: str = "auto",
        triggered_by_user: Optional[str] = None
    ) -> dict:
        """
        同步所有部門的班表

        Args:
            year: 年份
            month: 月份
            triggered_by: 觸發方式
            triggered_by_user: 觸發使用者

        Returns:
            dict: 同步結果
        """
        results = {
            "淡海": self.sync_department(
                department="淡海",
                year=year,
                month=month,
                triggered_by=triggered_by,
                triggered_by_user=triggered_by_user
            ),
            "安坑": self.sync_department(
                department="安坑",
                year=year,
                month=month,
                triggered_by=triggered_by,
                triggered_by_user=triggered_by_user
            )
        }

        overall_success = all(r["success"] for r in results.values())

        return {
            "success": overall_success,
            "year": year,
            "month": month,
            "results": results
        }

    def get_sync_task_status(
        self,
        batch_id: str,
        db: Optional[Session] = None
    ) -> Optional[dict]:
        """
        取得同步任務狀態

        Args:
            batch_id: 批次 ID
            db: 資料庫會話

        Returns:
            dict: 任務狀態，找不到返回 None
        """
        db_session = db or next(get_db())
        close_db = db is None

        try:
            task = db_session.query(SyncTask).filter(
                SyncTask.batch_id == batch_id
            ).first()

            if not task:
                return None

            return {
                "batch_id": task.batch_id,
                "task_type": task.task_type,
                "department": task.department,
                "year": task.target_year,
                "month": task.target_month,
                "status": task.status,
                "total_rows": task.total_rows,
                "success_count": task.success_count,
                "error_count": task.error_count,
                "progress": task.progress_percentage,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error_details": json.loads(task.error_details) if task.error_details else None
            }

        finally:
            if close_db:
                db_session.close()

    def get_recent_sync_tasks(
        self,
        limit: int = 10,
        task_type: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[dict]:
        """
        取得最近的同步任務

        Args:
            limit: 限制數量
            task_type: 任務類型篩選
            db: 資料庫會話

        Returns:
            List[dict]: 任務列表
        """
        db_session = db or next(get_db())
        close_db = db is None

        try:
            query = db_session.query(SyncTask)

            if task_type:
                query = query.filter(SyncTask.task_type == task_type)

            tasks = query.order_by(SyncTask.created_at.desc()).limit(limit).all()

            return [
                {
                    "batch_id": task.batch_id,
                    "task_type": task.task_type,
                    "department": task.department,
                    "year": task.target_year,
                    "month": task.target_month,
                    "status": task.status,
                    "total_rows": task.total_rows,
                    "success_count": task.success_count,
                    "error_count": task.error_count,
                    "triggered_by": task.triggered_by,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                for task in tasks
            ]

        finally:
            if close_db:
                db_session.close()


# 單例實例
_sync_service_instance: Optional[ScheduleSyncService] = None


def get_schedule_sync_service() -> ScheduleSyncService:
    """取得班表同步服務實例（單例）"""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = ScheduleSyncService()
    return _sync_service_instance
