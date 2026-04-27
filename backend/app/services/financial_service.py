"""
재무 데이터 서비스 — Story 1.4, 1.6, 3.4, 3.5
DB-First P&L / B/S / CF 조회: DB 없으면 DART sync 후 재조회
DART 장애 시 DB 캐시로 폴백, DB도 없으면 예외 re-raise
[Source: architecture.md - DB-First Caching Strategy]
"""
import logging
import time
from typing import Optional

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


def get_pl_data(corp_code: str, years: int = 5, fs_div: Optional[str] = None) -> list:
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
        .limit(years * len(PL_ACCOUNT_KEYS) * 6)  # CFS+OFS × 최대 3개 reprt_code 대비 버퍼
        .execute()
    )
    return res.data or []


def get_bs_data(corp_code: str, years: int = 5, fs_div: Optional[str] = None) -> list:
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
        .limit(years * len(BS_ACCOUNT_KEYS) * 6)  # CFS+OFS × 최대 3개 reprt_code 대비 버퍼
        .execute()
    )
    return res.data or []


def get_cf_data(corp_code: str, years: int = 5, fs_div: Optional[str] = None) -> list:
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
        .limit(years * len(CF_ACCOUNT_KEYS) * 6)  # CFS+OFS × 최대 3개 reprt_code 대비 버퍼
        .execute()
    )
    return res.data or []


_REPRT_PRIORITY = {"11011": 0, "11012": 1, "11013": 2, "11014": 3}


def _reprt_beats(new_row: dict, existing: dict) -> bool:
    """new_row가 existing보다 우선되어야 하면 True.
    우선순위: CFS > OFS, 같은 fs_div면 reprt_code 낮을수록 우선 (11011=사업보고서 > 11014=3Q).
    """
    new_cfs = new_row["fs_div"] == "CFS"
    ex_cfs = existing["fs_div"] == "CFS"
    if new_cfs != ex_cfs:
        return new_cfs  # CFS 우선
    new_p = _REPRT_PRIORITY.get(new_row.get("reprt_code", ""), 9)
    ex_p = _REPRT_PRIORITY.get(existing.get("reprt_code", ""), 9)
    return new_p < ex_p


def _prefer_cfs(rows: list, years: int) -> list:
    """동일 연도+계정에 CFS/OFS 둘 다 있으면 CFS 선택, reprt_code 낮은 쪽(사업보고서) 우선, 최근 N연도만 반환"""
    best: dict = {}
    for row in rows:
        key = (row["bsns_year"], row["account_key"])
        existing = best.get(key)
        if existing is None or _reprt_beats(row, existing):
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


def _prefer_fs_div_with_fallback(rows: list, years: int, preferred: str) -> list:
    """preferred fs_div가 있는 연도는 그것을, 없는 연도는 반대 fs_div로 폴백.
    폴백 행에는 is_fallback=True 플래그 추가.
    전제: 이미 preferred fs_div가 하나 이상 존재하는 기업에서만 호출.
    """
    best: dict = {}
    for row in rows:
        key = (row["bsns_year"], row["account_key"])
        existing = best.get(key)
        is_fallback = row["fs_div"] != preferred
        if existing is None:
            best[key] = {**row, "is_fallback": is_fallback}
        else:
            ex_fallback = existing.get("is_fallback", True)
            # preferred fs_div 우선, 같은 fs_div 내에서는 reprt_code 낮은 쪽(사업보고서) 우선
            new_prio = _REPRT_PRIORITY.get(row.get("reprt_code", ""), 9)
            ex_prio = _REPRT_PRIORITY.get(existing.get("reprt_code", ""), 9)
            if (not is_fallback and ex_fallback) or (is_fallback == ex_fallback and new_prio < ex_prio):
                best[key] = {**row, "is_fallback": is_fallback}
    return _select_recent_years_all(list(best.values()), years)


def _apply_fs_div_filter(rows: list, years: int, fs_div: Optional[str]) -> list:
    """fs_div 파라미터에 따라 필터링:
    - None → CFS 우선 dedup (기본값, 비교 모드 호환)
    - "ALL" → CFS+OFS 모두 반환
    - "CFS" / "OFS" → preferred 우선, 없는 연도는 반대 fs_div 폴백 (is_fallback=True 플래그)
      단, 처음부터 preferred fs_div가 전혀 없는 기업은 엄격 필터 적용
    """
    if fs_div == "ALL":
        return _select_recent_years_all(rows, years)
    elif fs_div in ("CFS", "OFS"):
        has_preferred = any(r["fs_div"] == fs_div for r in rows)
        if has_preferred:
            return _prefer_fs_div_with_fallback(rows, years, fs_div)
        else:
            filtered = [r for r in rows if r["fs_div"] == fs_div]
            return _select_recent_years_all(filtered, years)
    else:
        return _prefer_cfs(rows, years)
