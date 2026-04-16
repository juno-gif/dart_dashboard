"""
DART 동기화 엔드포인트 — Story 1.2
POST /api/v1/sync/company/{corp_code}   : 단일 기업 수동 동기화
POST /api/v1/sync/all                   : 전체 기업 일괄 동기화 (pg_cron 호출용)
[Source: architecture.md - API & Communication Patterns]
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, status

from app.core.config import settings
from app.services.dart_client import sync_all_companies, sync_company_financials

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
    """기업 재무 데이터를 DART에서 백그라운드로 수집 (즉시 응답, 30초 타임아웃 우회)"""
    background_tasks.add_task(_run_sync, corp_code, years)
    return {"status": "started", "corp_code": corp_code, "years": years}


def _run_sync_all() -> None:
    try:
        result = sync_all_companies()
        logger.info(f"[SYNC_ALL] 완료: {result}")
    except Exception as e:
        logger.error(f"[SYNC_ALL] 실패: {e}")


@router.post("/sync/all", status_code=status.HTTP_202_ACCEPTED)
async def sync_all(
    background_tasks: BackgroundTasks,
    authorization: str = Header(default=""),
):
    """전체 기업 일괄 동기화 — pg_cron이 매일 07:00 KST에 호출.
    Authorization: Bearer {SYNC_SECRET_KEY} 헤더로 인증.
    SYNC_SECRET_KEY 미설정 시 비활성화 (503 반환).
    """
    if not settings.SYNC_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "SYNC_DISABLED", "message": "SYNC_SECRET_KEY가 설정되지 않았습니다.", "status_code": 503},
        )

    expected = f"Bearer {settings.SYNC_SECRET_KEY}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "UNAUTHORIZED", "message": "유효하지 않은 인증 키입니다.", "status_code": 401},
        )

    background_tasks.add_task(_run_sync_all)
    logger.info("[SYNC_ALL] 요청 수신 — 백그라운드 동기화 시작")
    return {"status": "started", "message": "전체 기업 동기화가 백그라운드에서 시작되었습니다."}
