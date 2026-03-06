"""
공유 링크 읽기 전용 뷰어 API — Story 4.2
GET /api/v1/shared/{share_token}  (인증 불필요)
[Source: architecture.md - API & Communication Patterns]
"""
import logging

from fastapi import APIRouter, HTTPException

from app.core.database import get_supabase_client
from app.models.schemas import SharedAnalysisSetResponse
from app.services.financial_service import get_bs_data, get_cf_data, get_pl_data

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/shared/{share_token}", response_model=SharedAnalysisSetResponse)
async def get_shared_analysis_set(share_token: str):
    """공유 링크로 분석 세트 조회 — 인증 불필요"""
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("analysis_sets")
            .select("*")
            .eq("share_token", share_token)
            .execute()
        )
    except Exception as e:
        logger.error(f"DB error for share_token {share_token[:8]}...: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DB_UNAVAILABLE",
                "message": "데이터베이스에 일시적 오류가 발생했습니다.",
                "status_code": 503,
            },
        )

    if not res.data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SHARE_TOKEN_NOT_FOUND",
                "message": "유효하지 않은 공유 링크입니다.",
                "status_code": 404,
            },
        )

    analysis_set = res.data[0]
    company_codes = analysis_set["company_codes"]

    # 재무 데이터 조회 (PL + BS + CF)
    all_financials = []
    for corp_code in company_codes:
        try:
            all_financials.extend(get_pl_data(corp_code, years=5))
            all_financials.extend(get_bs_data(corp_code, years=5))
            all_financials.extend(get_cf_data(corp_code, years=5))
        except Exception as e:
            logger.warning(f"Financial data fetch failed for {corp_code}: {e}")
            # 재무 데이터 실패는 치명적이지 않음 — 빈 데이터로 계속

    return SharedAnalysisSetResponse(
        id=analysis_set["id"],
        name=analysis_set["name"],
        company_codes=company_codes,
        financials=all_financials,
    )
