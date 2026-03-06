"""
APScheduler 태스크 — 완전 구현: Story 3.3
매일 07:00 KST DART 데이터 자동 갱신
[Source: architecture.md - Infrastructure & Deployment]
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.dart_client import sync_all_companies

logger = logging.getLogger(__name__)


def start_scheduler() -> AsyncIOScheduler:
    """APScheduler 초기화 및 시작. FastAPI lifespan에서 호출.

    - timezone: Asia/Seoul (07:00 KST)
    - misfire_grace_time: 3600초 — 서버 재시작으로 07:00을 놓쳐도 1시간 내 자동 실행
    """
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        sync_all_companies,
        "cron",
        hour=7,
        minute=0,
        misfire_grace_time=3600,
        id="dart_daily_sync",
    )
    scheduler.start()
    logger.info("[SCHEDULER] APScheduler 시작: DART 일일 동기화 07:00 KST 등록 완료")
    return scheduler
