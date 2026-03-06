"""
FastAPI 애플리케이션 진입점
- CORS: Vercel 배포 도메인만 허용 (ALLOWED_ORIGINS 환경변수)
- Lifespan: APScheduler 시작/종료 (Story 3.3 구현 완료)
- 라우터: health, sync, companies, financials, users, analysis_sets
[Source: architecture.md - Infrastructure & Deployment]
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import analysis_sets, companies, financials, health, shared, sync, users
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    - 시작 시: APScheduler 초기화 (Story 3.3)
    - 종료 시: scheduler.shutdown()으로 정리
    """
    from app.scheduler.tasks import start_scheduler
    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)
    logger.info("[SCHEDULER] APScheduler 종료")


app = FastAPI(
    title="재무 분석 대시보드 API",
    description="DART OpenAPI 기반 내부 재무 분석 대시보드 백엔드",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정 — Vercel 배포 도메인만 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
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
app.include_router(shared.router, prefix="/api/v1")
