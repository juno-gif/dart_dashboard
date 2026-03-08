"""
재무 데이터 서비스 — Story 1.4, 1.6, 3.4, 3.5
DB-First P&L / B/S / CF 조회: DB 없으면 DART sync 후 재조회
DART 장애 시 DB 캐시로 폴백, DB도 없으면 예외 re-raise
[Source: architecture.md - DB-First Caching Strategy]
"""
import logging
import time

from app.core.database import get_supabase_client
from app.services.dart_client import sync_company_financials

logger = logging.getLogger(__name__)

PL_ACCOUNT_KEYS = ["revenue", "operating_profit", "net_income"]
BS_ACCOUNT_KEYS = ["total_assets", "total_liabilities", "total_equity", "cash_and_equivalents"]
CF_ACCOUNT_KEYS = ["operating_cf", "investing_cf", "financing_cf"]

# 부분 sync 후 과도한 재호출 방지용 in-memory 쿨다운 (재시작 시 초기화됨)
_last_sync: dict[str, float] = {}
_SYNC_COOLDOWN = 3600  # 1시간 (초)


def _needs_sync(corp_code: str, rows: list, years: int) -> bool:
    """sync 필요 여부 판단:
    - 데이터 없음 → 항상 sync
    - 데이터 있지만 연도 부족 → 쿨다운 지난 경우에만 sync (무한 루프 방지)
    """
    if not rows:
        return True
    distinct_years = len({r["bsns_year"] for r in rows})
    if distinct_years >= years:
        return False
    # 부분 데이터: 쿨다운(1시간) 경과 시에만 재시도
    last = _last_sync.get(corp_code, 0)
    return time.time() - last > _SYNC_COOLDOWN


def get_pl_data(corp_code: str, years: int = 5, fs_div: str | None = None) -> list:
    """DB-First P&L 조회.
    DB에 데이터 없거나 연도 부족 시 DART sync 후 재조회.
    DART 장애 시: DB 캐시 있으면 반환, 없으면 예외 re-raise (→ 503).
    fs_div=None → CFS 우선(기본), "CFS"/"OFS" → 해당 구분만, "ALL" → CFS+OFS 모두 반환.
    """
    supabase = get_supabase_client()

    rows = _query_pl(supabase, corp_code, years)

    if _needs_sync(corp_code, rows, years):
        try:
            _last_sync[corp_code] = time.time()
            sync_company_financials(corp_code, years=years)
            rows = _query_pl(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            if not rows:
                # DB도 비어 있음 → 호출부에서 DART_API_UNAVAILABLE 처리
                raise

    return _apply_fs_div_filter(rows, years, fs_div)


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


def get_bs_data(corp_code: str, years: int = 5, fs_div: str | None = None) -> list:
    """DB-First B/S 조회.
    DB에 데이터 없거나 연도 부족 시 DART sync 후 재조회.
    DART 장애 시: DB 캐시 있으면 반환, 없으면 예외 re-raise (→ 503).
    fs_div=None → CFS 우선(기본), "CFS"/"OFS" → 해당 구분만, "ALL" → CFS+OFS 모두 반환.
    """
    supabase = get_supabase_client()

    rows = _query_bs(supabase, corp_code, years)

    if _needs_sync(corp_code, rows, years):
        try:
            _last_sync[corp_code] = time.time()
            sync_company_financials(corp_code, years=years)
            rows = _query_bs(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            if not rows:
                raise

    return _apply_fs_div_filter(rows, years, fs_div)


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


def get_cf_data(corp_code: str, years: int = 5, fs_div: str | None = None) -> list:
    """DB-First CF 조회.
    DB에 데이터 없거나 연도 부족 시 DART sync 후 재조회.
    DART 장애 시: DB 캐시 있으면 반환, 없으면 예외 re-raise (→ 503).
    fs_div=None → CFS 우선(기본), "CFS"/"OFS" → 해당 구분만, "ALL" → CFS+OFS 모두 반환.
    """
    supabase = get_supabase_client()

    rows = _query_cf(supabase, corp_code, years)

    if _needs_sync(corp_code, rows, years):
        try:
            _last_sync[corp_code] = time.time()
            sync_company_financials(corp_code, years=years)
            rows = _query_cf(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            if not rows:
                raise

    return _apply_fs_div_filter(rows, years, fs_div)


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


def _select_recent_years_all(rows: list, years: int) -> list:
    """최근 N개 연도의 모든 행(CFS+OFS) 반환 — 중복 제거 없음"""
    sorted_rows = sorted(rows, key=lambda r: r["bsns_year"], reverse=True)
    years_seen: set = set()
    filtered = []
    for row in sorted_rows:
        years_seen.add(row["bsns_year"])
        if len(years_seen) <= years:
            filtered.append(row)
    return filtered


def _apply_fs_div_filter(rows: list, years: int, fs_div: str | None) -> list:
    """fs_div 파라미터에 따라 필터링:
    - None → CFS 우선 dedup (기본값, 비교 모드 호환)
    - "ALL" → CFS+OFS 모두 반환
    - "CFS" / "OFS" → 해당 구분만 반환
    """
    if fs_div == "ALL":
        return _select_recent_years_all(rows, years)
    elif fs_div in ("CFS", "OFS"):
        filtered = [r for r in rows if r["fs_div"] == fs_div]
        return _select_recent_years_all(filtered, years)
    else:
        return _prefer_cfs(rows, years)
