"""
定時任務管理
對應 tasks.md T083: 實作定時任務管理 (APScheduler)
對應 tasks.md T109: 更新定時任務（季度制競賽排名）

功能：
- 配置 APScheduler
- 註冊班表同步定時任務（每日凌晨 2:00）
- 註冊勤務表同步定時任務（每日凌晨 2:30）
- 註冊駕駛競賽排名計算任務（每季首日凌晨 3:00）
- 提供任務管理介面
"""

from datetime import datetime
from typing import Optional, List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

from src.config.settings import get_settings
from src.utils.logger import logger


class TaskScheduler:
    """
    定時任務排程器

    使用 APScheduler 管理定時任務，包括：
    - 班表同步（每日凌晨 2:00）
    - 勤務表同步（每日凌晨 2:30）
    - 駕駛競賽排名計算（每季首日凌晨 3:00，季度制）
    """

    def __init__(self):
        self._settings = get_settings()
        self._scheduler: Optional[BackgroundScheduler] = None
        self._initialized = False

    def _create_scheduler(self) -> BackgroundScheduler:
        """
        建立 APScheduler 排程器

        Returns:
            BackgroundScheduler: 排程器實例
        """
        # 執行緒池設定
        executors = {
            "default": ThreadPoolExecutor(max_workers=3),
        }

        # 任務設定
        job_defaults = {
            "coalesce": True,  # 錯過的任務合併為一次
            "max_instances": 1,  # 同一任務最多執行一個實例
            "misfire_grace_time": 60 * 60,  # 錯過執行的容忍時間（1小時）
        }

        # 建立排程器
        scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults,
            timezone="Asia/Taipei"
        )

        return scheduler

    def initialize(self):
        """
        初始化排程器並註冊任務
        """
        if self._initialized:
            logger.warning("排程器已初始化，跳過重複初始化")
            return

        self._scheduler = self._create_scheduler()
        self._register_jobs()
        self._initialized = True

        logger.info("定時任務排程器已初始化")

    def _register_jobs(self):
        """
        註冊所有定時任務
        """
        # 註冊班表同步任務（每日凌晨 2:00）
        self._scheduler.add_job(
            func=self._schedule_sync_job,
            trigger=CronTrigger(hour=2, minute=0),
            id="schedule_sync_daily",
            name="班表同步（每日）",
            replace_existing=True
        )
        logger.info("已註冊定時任務: schedule_sync_daily (每日 02:00)")

        # 註冊勤務表同步任務（每日凌晨 2:30）- Phase 9
        self._scheduler.add_job(
            func=self._duty_sync_job,
            trigger=CronTrigger(hour=2, minute=30),
            id="duty_sync_daily",
            name="勤務表同步（每日）",
            replace_existing=True
        )
        logger.info("已註冊定時任務: duty_sync_daily (每日 02:30)")

        # 註冊駕駛競賽排名計算任務（每季首日凌晨 3:00）- Phase 9
        # 季度首日：1/1, 4/1, 7/1, 10/1
        self._scheduler.add_job(
            func=self._competition_ranking_job,
            trigger=CronTrigger(month="1,4,7,10", day=1, hour=3, minute=0),
            id="competition_ranking_quarterly",
            name="駕駛競賽排名計算（每季）",
            replace_existing=True
        )
        logger.info("已註冊定時任務: competition_ranking_quarterly (每季首日 03:00)")

    def _schedule_sync_job(self):
        """
        班表同步任務

        每日凌晨執行，同步當月班表。
        """
        logger.info("執行定時班表同步任務")

        try:
            from src.services.schedule_sync_service import get_schedule_sync_service

            now = datetime.now()
            year = now.year
            month = now.month

            sync_service = get_schedule_sync_service()
            result = sync_service.sync_all_departments(
                year=year,
                month=month,
                triggered_by="auto"
            )

            if result["success"]:
                logger.info(
                    "定時班表同步完成",
                    year=year,
                    month=month,
                    results=result["results"]
                )
            else:
                logger.error(
                    "定時班表同步失敗",
                    year=year,
                    month=month,
                    results=result["results"]
                )

        except Exception as e:
            logger.error("定時班表同步例外", error=str(e))

    def _duty_sync_job(self):
        """
        勤務表同步任務

        每日凌晨 2:30 執行，同步駕駛時數統計。
        從 schedules 表讀取班表，計算每位員工的駕駛時數並寫入 driving_daily_stats。
        """
        logger.info("執行定時勤務表同步任務")

        try:
            from src.config.database import get_db
            from src.services.duty_sync_service import DutySyncService
            from datetime import timedelta

            now = datetime.now()
            # 同步前一天的資料
            target_date = (now - timedelta(days=1)).date()

            # 取得資料庫連線
            db = next(get_db())
            try:
                sync_service = DutySyncService(db)
                result = sync_service.sync_all_departments_for_date(target_date)

                logger.info(
                    "定時勤務表同步完成",
                    date=target_date.isoformat(),
                    total_processed=result["total_processed"],
                    total_errors=result["total_errors"]
                )
            finally:
                db.close()

        except Exception as e:
            logger.error("定時勤務表同步例外", error=str(e))

    def _competition_ranking_job(self):
        """
        駕駛競賽排名計算任務（季度制）

        每季首日（1/1, 4/1, 7/1, 10/1）凌晨 3:00 執行。
        計算前一季度的駕駛競賽排名。

        規則：
        - 資格門檻：季度累計≥300小時 且 季末在職
        - 排名名額：淡海前5名、安坑前3名
        - 獎金：淡海 3600/3000/2400/1800/1200、安坑 3600/3000/2400
        """
        logger.info("執行定時駕駛競賽排名計算任務")

        try:
            from src.config.database import get_db
            from src.services.driving_competition_ranker import DrivingCompetitionRanker

            now = datetime.now()
            year = now.year
            month = now.month

            # 計算前一季度
            # 1月 → Q4 (去年), 4月 → Q1, 7月 → Q2, 10月 → Q3
            if month == 1:
                target_year = year - 1
                target_quarter = 4
            elif month == 4:
                target_year = year
                target_quarter = 1
            elif month == 7:
                target_year = year
                target_quarter = 2
            elif month == 10:
                target_year = year
                target_quarter = 3
            else:
                # 非季度首日，不應執行
                logger.warning(f"非季度首日執行競賽排名計算: {now}")
                return

            # 取得資料庫連線
            db = next(get_db())
            try:
                ranker = DrivingCompetitionRanker(db)
                result = ranker.calculate_quarterly_ranking(target_year, target_quarter)

                if not result["errors"]:
                    logger.info(
                        "定時駕駛競賽排名計算完成",
                        year=target_year,
                        quarter=target_quarter,
                        total_processed=result["total_processed"],
                        departments=list(result["departments"].keys())
                    )
                else:
                    logger.error(
                        "定時駕駛競賽排名計算部分失敗",
                        year=target_year,
                        quarter=target_quarter,
                        errors=result["errors"]
                    )
            finally:
                db.close()

        except Exception as e:
            logger.error("定時駕駛競賽排名計算例外", error=str(e))

    def start(self):
        """
        啟動排程器
        """
        if not self._initialized:
            self.initialize()

        if self._scheduler and not self._scheduler.running:
            self._scheduler.start()
            logger.info("定時任務排程器已啟動")

    def stop(self):
        """
        停止排程器
        """
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("定時任務排程器已停止")

    def get_jobs(self) -> List[dict]:
        """
        取得所有已註冊的任務

        Returns:
            List[dict]: 任務列表
        """
        if not self._scheduler:
            return []

        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return jobs

    def trigger_job(self, job_id: str) -> bool:
        """
        立即觸發指定任務

        Args:
            job_id: 任務 ID

        Returns:
            bool: 是否成功觸發
        """
        if not self._scheduler:
            return False

        try:
            job = self._scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"已觸發任務: {job_id}")
                return True
            else:
                logger.warning(f"找不到任務: {job_id}")
                return False
        except Exception as e:
            logger.error(f"觸發任務失敗: {job_id}", error=str(e))
            return False

    def pause_job(self, job_id: str) -> bool:
        """
        暫停指定任務

        Args:
            job_id: 任務 ID

        Returns:
            bool: 是否成功暫停
        """
        if not self._scheduler:
            return False

        try:
            self._scheduler.pause_job(job_id)
            logger.info(f"已暫停任務: {job_id}")
            return True
        except Exception as e:
            logger.error(f"暫停任務失敗: {job_id}", error=str(e))
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        恢復指定任務

        Args:
            job_id: 任務 ID

        Returns:
            bool: 是否成功恢復
        """
        if not self._scheduler:
            return False

        try:
            self._scheduler.resume_job(job_id)
            logger.info(f"已恢復任務: {job_id}")
            return True
        except Exception as e:
            logger.error(f"恢復任務失敗: {job_id}", error=str(e))
            return False

    @property
    def is_running(self) -> bool:
        """排程器是否正在執行"""
        return self._scheduler is not None and self._scheduler.running


# 單例實例
_scheduler_instance: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    """取得定時任務排程器實例（單例）"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance


def start_scheduler():
    """啟動排程器（供 FastAPI 啟動時呼叫）"""
    scheduler = get_task_scheduler()
    scheduler.start()


def stop_scheduler():
    """停止排程器（供 FastAPI 關閉時呼叫）"""
    scheduler = get_task_scheduler()
    scheduler.stop()
