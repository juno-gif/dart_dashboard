"""
DART 동기화 엔드포인트 — Story 1.2
POST /api/v1/sync/company/{corp_code}
[Source: architecture.md - API & Communication Patterns]
"""
import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Query

from app.services.dart_client import sync_company_financials

router = APIRouter()
logger = logging.getLogger(__name__)


def _run_sync(corp_code: str, years: int) -> None:
    try:
        result = sync_company_financials(corp_code, years=years)
        logger.info(f"[SYNC] 완료 corp={corp_code} rows={result['synced_rows']}")
    except Exception as e:
        logger.error(f"[SYNC] 실패 corp={corp_code}: {e}")


@router.post("/sync/company/{corp_code}")
async def sync_company(
    corp_code: str,
    background_tasks: BackgroundTasks,
    years: int = Query(default=5, ge=1, le=10),
):
    """기업 재무 데이터를 DART에서 백그라운드로 수집 (즉시 응답, Render 30초 타임아웃 우회)"""
    background_tasks.add_task(_run_sync, corp_code, years)
    return {"status": "started", "corp_code": corp_code, "years": years}
