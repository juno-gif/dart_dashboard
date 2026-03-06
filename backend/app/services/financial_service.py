"""
재무 데이터 서비스 — Story 1.4, 1.6, 3.4, 3.5
DB-First P&L / B/S / CF 조회: DB 없으면 DART sync 후 재조회
DART 장애 시 DB 캐시로 폴백, DB도 없으면 예외 re-raise
[Source: architecture.md - DB-First Caching Strategy]
"""
import logging

from app.core.database import get_supabase_client
from app.services.dart_client import sync_company_financials

logger = logging.getLogger(__name__)

PL_ACCOUNT_KEYS = ["revenue", "operating_profit", "net_income"]
BS_ACCOUNT_KEYS = ["total_assets", "total_liabilities", "total_equity", "cash_and_equivalents"]
CF_ACCOUNT_KEYS = ["operating_cf", "investing_cf", "financing_cf"]


def get_pl_data(corp_code: str, years: int = 5) -> list:
    """DB-First P&L 조회.
    DB에 데이터 없으면 DART sync 후 재조회.
    DART 장애 시: DB 캐시 있으면 반환, 없으면 예외 re-raise (→ 503).
    CFS(연결) 우선, 없으면 OFS(개별) 사용.
    """
    supabase = get_supabase_client()

    rows = _query_pl(supabase, corp_code, years)

    if not rows:
        try:
            sync_company_financials(corp_code, years=years)
            rows = _query_pl(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            # DB도 비어 있음 → 호출부에서 DART_API_UNAVAILABLE 처리
            raise

    return _prefer_cfs(rows, years)


def _query_pl(supabase, corp_code: str, years: int) -> list:
    res = (
        supabase.table("financial_statements")
        .select("*")
        .eq("corp_code", corp_code)
        .in_("account_key", PL_ACCOUNT_KEYS)
        .order("bsns_year", desc=True)
        .limit(years * len(PL_ACCOUNT_KEYS) * 2)  # CFS+OFS 대비 버퍼
        .execute()
    )
    return res.data or []


def get_bs_data(corp_code: str, years: int = 5) -> list:
    """DB-First B/S 조회.
    DB에 데이터 없으면 DART sync 후 재조회.
    DART 장애 시: DB 캐시 있으면 반환, 없으면 예외 re-raise (→ 503).
    CFS(연결) 우선, 없으면 OFS(개별) 사용.
    """
    supabase = get_supabase_client()

    rows = _query_bs(supabase, corp_code, years)

    if not rows:
        try:
            sync_company_financials(corp_code, years=years)
            rows = _query_bs(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            raise

    return _prefer_cfs(rows, years)


def _query_bs(supabase, corp_code: str, years: int) -> list:
    res = (
        supabase.table("financial_statements")
        .select("*")
        .eq("corp_code", corp_code)
        .in_("account_key", BS_ACCOUNT_KEYS)
        .order("bsns_year", desc=True)
        .limit(years * len(BS_ACCOUNT_KEYS) * 2)  # CFS+OFS 대비 버퍼
        .execute()
    )
    return res.data or []


def get_cf_data(corp_code: str, years: int = 5) -> list:
    """DB-First CF 조회.
    DB에 데이터 없으면 DART sync 후 재조회.
    DART 장애 시: DB 캐시 있으면 반환, 없으면 예외 re-raise (→ 503).
    CFS(연결) 우선, 없으면 OFS(개별) 사용.
    """
    supabase = get_supabase_client()

    rows = _query_cf(supabase, corp_code, years)

    if not rows:
        try:
            sync_company_financials(corp_code, years=years)
            rows = _query_cf(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            raise

    return _prefer_cfs(rows, years)


def _query_cf(supabase, corp_code: str, years: int) -> list:
    res = (
        supabase.table("financial_statements")
        .select("*")
        .eq("corp_code", corp_code)
        .in_("account_key", CF_ACCOUNT_KEYS)
        .order("bsns_year", desc=True)
        .limit(years * len(CF_ACCOUNT_KEYS) * 2)  # CFS+OFS 대비 버퍼
        .execute()
    )
    return res.data or []


def _prefer_cfs(rows: list, years: int) -> list:
    """동일 연도+계정에 CFS/OFS 둘 다 있으면 CFS 선택, 최근 N연도만 반환"""
    best: dict = {}
    for row in rows:
        key = (row["bsns_year"], row["account_key"])
        existing = best.get(key)
        if existing is None or (
            row["fs_div"] == "CFS" and existing["fs_div"] != "CFS"
        ):
            best[key] = row

    # 최근 N개 연도만 추출
    result = sorted(best.values(), key=lambda r: r["bsns_year"], reverse=True)
    years_seen: set = set()
    filtered = []
    for row in result:
        years_seen.add(row["bsns_year"])
        if len(years_seen) <= years:
            filtered.append(row)
    return filtered
