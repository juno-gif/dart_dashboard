"""
재무 데이터 API — Story 1.4, 1.5, 1.6
GET /api/v1/companies/{corp_code}/financials?years=5&type=pl
GET /api/v1/companies/compare?codes=005930,035720&type=pl
[Source: architecture.md - API & Communication Patterns]
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_user
from app.models.schemas import FinancialStatement
from app.services.financial_service import get_bs_data, get_cf_data, get_pl_data
from app.services.valuation_service import get_valuation_data
from app.core.database import get_supabase_client


logger = logging.getLogger(__name__)
router = APIRouter()


# ── Story 1.5: 다중 기업 비교 ──────────────────────────────
# ⚠️ /companies/compare 는 /companies/{corp_code}/... 보다 반드시 앞에 위치해야 함
@router.get("/companies/compare", response_model=list[FinancialStatement])
def compare_financials(
    codes: str,
    years: int = 5,
    chart_type: str = Query("pl", alias="type"),
    _: object = Depends(get_current_user),
):
    """다중 기업 재무 데이터 비교 조회 (DB-First)
    - codes: 콤마 구분 corp_code 목록 (예: 005930,035720), 1~5개
    - chart_type=pl, bs, cf 지원
    """
    if chart_type not in ("pl", "bs", "cf"):
        raise HTTPException(
            status_code=400,
            detail="type은 pl, bs, cf만 지원됩니다.",
        )
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, detail="years는 1~10 사이여야 합니다.")

    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list or len(code_list) > 5:
        raise HTTPException(status_code=400, detail="codes는 1~5개여야 합니다.")

    all_data: list = []
    if chart_type == "bs":
        fetch = get_bs_data
    elif chart_type == "cf":
        fetch = get_cf_data
    else:
        fetch = get_pl_data
    for corp_code in code_list:
        try:
            data = fetch(corp_code, years=years)
            all_data.extend(data)
        except Exception as e:
            logger.error(f"DART API unavailable for {corp_code}: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "DART_API_UNAVAILABLE",
                    "message": "DART API에 일시적 오류가 발생했습니다. 나중에 다시 시도해 주세요.",
                    "cached_at": None,
                    "status_code": 503,
                },
            )

    return all_data


# ── Story 1.4: 단일 기업 재무 조회 ────────────────────────
@router.get("/companies/{corp_code}/financials", response_model=list[FinancialStatement])
def get_financials(
    corp_code: str,
    years: int = 10,
    chart_type: str = Query("pl", alias="type"),
    fs_div: str | None = Query(None),
    _: object = Depends(get_current_user),
):
    """기업 재무 데이터 조회 (DB-First)
    - chart_type=pl: 매출·영업이익·순이익
    - chart_type=bs: 자산·부채·자본·현금 (Story 3.4)
    - chart_type=cf: 영업·투자·재무 현금흐름 (Story 3.5)
    - fs_div=None(기본) → CFS 우선, "CFS"/"OFS" → 해당 구분만, "ALL" → 전체
    """
    if chart_type not in ("pl", "bs", "cf"):
        raise HTTPException(
            status_code=400,
            detail="type은 pl, bs, cf만 지원됩니다.",
        )
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, detail="years는 1~10 사이여야 합니다.")
    if fs_div is not None and fs_div not in ("CFS", "OFS", "ALL"):
        raise HTTPException(status_code=400, detail="fs_div는 CFS, OFS, ALL만 지원됩니다.")

    try:
        if chart_type == "bs":
            data = get_bs_data(corp_code, years=years, fs_div=fs_div)
        elif chart_type == "cf":
            data = get_cf_data(corp_code, years=years, fs_div=fs_div)
        else:
            data = get_pl_data(corp_code, years=years, fs_div=fs_div)
    except Exception as e:
        logger.error(f"DART API unavailable for {corp_code}: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DART_API_UNAVAILABLE",
                "message": "DART API에 일시적 오류가 발생했습니다. 나중에 다시 시도해 주세요.",
                "cached_at": None,
                "status_code": 503,
            },
        )

    return data


# ── Valuation (PBR/PER) 조회 ────────────────────────────
@router.get("/companies/{corp_code}/valuation")
def get_valuation(
    corp_code: str,
    years: int = 10,
    _: object = Depends(get_current_user),
):
    """상장 기업 PBR/PER 조회 (yfinance + Supabase 자본총계, 1일 캐시)
    - PBR = 시가총액 / 자본총계 (DB의 total_equity 활용)
    - 비상장사 또는 조회 실패 시 current_pbr/current_per=null, yearly=[]
    """
    supabase = get_supabase_client()
    res = (
        supabase.table("companies")
        .select("stock_code")
        .eq("corp_code", corp_code)
        .single()
        .execute()
    )
    if not res.data or not res.data.get("stock_code"):
        return {"current_pbr": None, "current_per": None, "yearly": []}
    stock_code = res.data["stock_code"]

    # DB에서 연도별 자본총계 + 순이익 조회 (CFS 우선, 없으면 OFS)
    fs_res = (
        supabase.table("financial_statements")
        .select("bsns_year, account_key, amount, fs_div")
        .eq("corp_code", corp_code)
        .in_("account_key", ["total_equity", "net_income"])
        .in_("fs_div", ["CFS", "OFS"])
        .order("bsns_year", desc=True)
        .limit(years * 4)
        .execute()
    )

    equity_by_year: dict[str, int] = {}
    income_by_year: dict[str, int] = {}
    for r in fs_res.data or []:
        yr = r["bsns_year"]
        key = r["account_key"]
        target = equity_by_year if key == "total_equity" else income_by_year
        # PBR/PER 기준: 별도(OFS) 우선 — 네이버·KRX와 동일 기준
        # 연결 자본총계는 비지배지분 포함으로 PBR 왜곡 발생
        if yr not in target or r["fs_div"] == "OFS":
            target[yr] = r["amount"]

    return get_valuation_data(
        stock_code,
        equity_by_year=equity_by_year,
        income_by_year=income_by_year,
        years=years,
    )
