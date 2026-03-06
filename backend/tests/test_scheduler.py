"""
scheduler/tasks.py 테스트 — Story 3.3
APScheduler start_scheduler() 검증
"""
from unittest.mock import patch


class TestScheduler:
    """start_scheduler() 동작 검증"""

    def test_start_scheduler_returns_scheduler_object(self):
        """start_scheduler()가 AsyncIOScheduler 인스턴스를 반환하는지 확인"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        with patch("app.scheduler.tasks.sync_all_companies"):
            with patch.object(AsyncIOScheduler, "start"):
                from app.scheduler.tasks import start_scheduler
                scheduler = start_scheduler()

        assert isinstance(scheduler, AsyncIOScheduler)

    def test_scheduler_has_daily_cron_job(self):
        """매일 07:00 cron job이 등록되었는지 확인"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        with patch("app.scheduler.tasks.sync_all_companies"):
            with patch.object(AsyncIOScheduler, "start"):
                from app.scheduler.tasks import start_scheduler
                scheduler = start_scheduler()

        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "dart_daily_sync"

    def test_scheduler_job_runs_at_7am_kst(self):
        """job이 07:00 KST cron 설정인지 확인"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        with patch("app.scheduler.tasks.sync_all_companies"):
            with patch.object(AsyncIOScheduler, "start"):
                from app.scheduler.tasks import start_scheduler
                scheduler = start_scheduler()

        job = scheduler.get_job("dart_daily_sync")
        assert job is not None
        trigger = job.trigger
        assert str(trigger.timezone) == "Asia/Seoul"
        # cron 필드 확인: hour=7, minute=0
        fields = {f.name: f for f in trigger.fields}
        assert str(fields["hour"]) == "7"
        assert str(fields["minute"]) == "0"
