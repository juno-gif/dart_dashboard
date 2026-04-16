"""
FastAPI 애플리케이션 진입점
- CORS: Vercel 배포 도메인만 허용 (ALLOWED_ORIGINS 환경변수)
- Lifespan: APScheduler 시작/종료 (Story 3.3 구현 완료)
- 라우터: health, sync, companies, financials, users, analysis_sets
[Source: architecture.md - Infrastructure & Deployment]
"""
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(name)s: %(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import analysis_groups, analysis_sets, companies, financials, health, shared, sync, users
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    - 시작 시: APScheduler 초기화 (Story 3.3) + DART 웜업 (첫 검색 지연 방지)
    - 종료 시: scheduler.shutdown()으로 정리
    """
    import asyncio
    from app.scheduler.tasks import start_scheduler
    from app.services.dart_client import _get_dart

    scheduler = start_scheduler()

    # DART 웜업을 백그라운드 태스크로 실행 — yield 이전 블로킹 방지 (Render 헬스체크 타임아웃 해결)
    async def _warmup():
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, _get_dart)
            logger.info("[STARTUP] DART 웜업 완료")
        except Exception as e:
            logger.warning(f"[STARTUP] DART 웜업 실패 (첫 검색이 느릴 수 있음): {e}")

    asyncio.create_task(_warmup())

    yield
    scheduler.shutdown(wait=False)
    logger.info("[SCHEDULER] APScheduler 종료")


app = FastAPI(
    title="재무 분석 대시보드 API",
    description="DART OpenAPI 기반 내부 재무 분석 대시보드 백엔드",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정 — 전체 공개 앱이므로 모든 origin 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(financials.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(analysis_sets.router, prefix="/api/v1")
app.include_router(analysis_groups.router, prefix="/api/v1")
app.include_router(shared.router, prefix="/api/v1")
