"""
FastAPI 애플리케이션 진입점
- CORS: 전체 공개 앱이므로 모든 origin 허용
- Lifespan: DART 웜업 (첫 검색 지연 방지)
- 일일 동기화: APScheduler 대신 Supabase pg_cron + pg_net → POST /api/v1/sync/all
- 라우터: health, sync, companies, financials, users, analysis_sets
[Source: architecture.md - Infrastructure & Deployment]
"""
import asyncio
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
    - 시작 시: DART 웜업 (첫 검색 지연 방지)
    - 일일 동기화: Supabase pg_cron이 POST /api/v1/sync/all 호출
    """
    from app.services.dart_client import _get_dart

    async def _warmup():
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, _get_dart)
            logger.info("[STARTUP] DART 웜업 완료")
        except Exception as e:
            logger.warning(f"[STARTUP] DART 웜업 실패 (첫 검색이 느릴 수 있음): {e}")

    asyncio.create_task(_warmup())
    yield


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
