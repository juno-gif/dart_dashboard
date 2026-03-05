"""
DART 동기화 엔드포인트 — Story 1.2
POST /api/v1/sync/company/{corp_code}
[Source: architecture.md - API & Communication Patterns]
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import SyncResult
from app.services.dart_client import sync_company_financials

router = APIRouter()


@router.post("/sync/company/{corp_code}", response_model=SyncResult)
async def sync_company(corp_code: str):
    """기업 재무 데이터를 DART에서 수집해 DB에 저장"""
    try:
        result = sync_company_financials(corp_code)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DART_API_UNAVAILABLE",
                "message": str(e),
                "status_code": 503,
            },
        )
