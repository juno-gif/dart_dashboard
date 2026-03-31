from __future__ import annotations

import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# L1: in-memory 캐시 (프로세스 내 빠른 접근)
_valuation_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 86400  # 1일
_FAIL_TTL = 300     # 실패 시 5분 캐시


def _supabase_cache_get(stock_code: str) -> dict | None:
    """Supabase valuation_cache에서 유효한 캐시 조회 (TTL 24h)."""
    try:
        from app.core.database import get_supabase_client
        sb = get_supabase_client()
        res = sb.table("valuation_cache").select("data, cached_at").eq("stock_code", stock_code).maybe_single().execute()
        if not res.data:
            return None
        cached_at_str = res.data["cached_at"]
        cached_at = datetime.fromisoformat(cached_at_str.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        if age < _CACHE_TTL:
            return res.data["data"]
        return None
    except Exception as e:
        logger.debug(f"[Valuation] Supabase 캐시 읽기 실패 stock={stock_code}: {e}")
        return None


def _supabase_cache_set(stock_code: str, data: dict) -> None:
    """Supabase valuation_cache에 upsert."""
    try:
        from app.core.database import get_supabase_client
        sb = get_supabase_client()
        sb.table("valuation_cache").upsert({
            "stock_code": stock_code,
            "data": data,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.warning(f"[Valuation] Supabase 캐시 저장 실패 stock={stock_code}: {e}")


def _get_stock_info(stock_code: str) -> dict | None:
    """FinanceDataReader로 현재 시가총액·상장주식수 조회 (KOSPI → KOSDAQ 순)."""
    import FinanceDataReader as fdr
    for market in ("KOSPI", "KOSDAQ"):
        try:
            df = fdr.StockListing(market)
            row = df[df["Code"] == stock_code]
            if not row.empty:
                marcap = row.iloc[0].get("Marcap")
                shares = row.iloc[0].get("Stocks")
                if marcap and marcap > 0:
                    return {"marcap": float(marcap), "shares": float(shares) if shares else None}
        except Exception as e:
            logger.debug(f"[Valuation] StockListing {market} 실패: {e}")
    return None


def _get_year_end_price(stock_code: str, year: int) -> float | None:
    """연말 종가 조회 (FinanceDataReader)."""
    import FinanceDataReader as fdr
    try:
        df = fdr.DataReader(stock_code, f"{year}-12-01", f"{year}-12-31")
        if df.empty:
            return None
        return float(df.iloc[-1]["Close"])
    except Exception:
        return None


def get_valuation_data(
    stock_code: str,
    equity_by_year: dict[str, int] | None = None,
    income_by_year: dict[str, int] | None = None,
    years: int = 10,
) -> dict:
    """PBR/PER 계산 — L1(memory) → L2(Supabase) → FinanceDataReader 순으로 조회."""
    now = time.time()
    cache_key = f"{stock_code}:{years}"

    # L1: in-memory
    if cache_key in _valuation_cache:
        ts, data = _valuation_cache[cache_key]
        if now - ts < _CACHE_TTL:
            return data

    # L2: Supabase 영구 캐시
    cached = _supabase_cache_get(stock_code)
    if cached is not None:
        _valuation_cache[cache_key] = (now, cached)
        logger.info(f"[Valuation] Supabase 캐시 히트 stock={stock_code}")
        return cached

    # L3: FinanceDataReader 실시간 조회
    try:
        info = _get_stock_info(stock_code)
        if not info:
            logger.warning(f"[Valuation] 종목 정보 없음 stock={stock_code}")
            _valuation_cache[cache_key] = (now - _CACHE_TTL + _FAIL_TTL, _empty())
            return _empty()

        marcap = info["marcap"]
        shares = info["shares"]

        # 현재 PBR
        current_pbr: float | None = None
        if equity_by_year:
            latest_year = max(equity_by_year.keys())
            equity = equity_by_year.get(latest_year)
            if equity and equity > 0:
                current_pbr = round(marcap / equity, 2)

        # 현재 PER
        current_per: float | None = None
        if income_by_year:
            latest_year = max(income_by_year.keys())
            net_income = income_by_year.get(latest_year)
            if net_income and net_income > 0:
                current_per = round(marcap / net_income, 2)

        # 연도별 PBR/PER
        yearly = _compute_yearly(stock_code, shares, equity_by_year or {}, income_by_year or {}, years)

        result = {"current_pbr": current_pbr, "current_per": current_per, "yearly": yearly}

        # 유효한 데이터가 없으면 짧게 캐시 (5분), 있으면 24시간
        has_data = current_pbr is not None or len(yearly) > 0
        cache_ts = now if has_data else now - _CACHE_TTL + _FAIL_TTL
        _valuation_cache[cache_key] = (cache_ts, result)
        if has_data:
            _supabase_cache_set(stock_code, result)

        logger.info(
            f"[Valuation] 조회 완료 stock={stock_code} pbr={current_pbr} per={current_per} years={len(yearly)}"
        )
        return result

    except Exception as e:
        logger.warning(f"[Valuation] 조회 실패 stock={stock_code}: {e}")
        _valuation_cache[cache_key] = (now - _CACHE_TTL + _FAIL_TTL, _empty())
        return _empty()


def _compute_yearly(
    stock_code: str,
    shares: float | None,
    equity_by_year: dict,
    income_by_year: dict,
    years: int,
) -> list:
    if not equity_by_year or not shares or shares <= 0:
        return []

    current_year = datetime.now().year
    start_year = current_year - years + 1
    yearly = []

    for yr_str, equity in equity_by_year.items():
        yr = int(yr_str)
        if yr < start_year or equity <= 0:
            continue
        price = _get_year_end_price(stock_code, yr)
        if not price:
            continue
        mkt_cap = price * shares
        pbr = round(mkt_cap / equity, 2) if equity > 0 else None
        net_income = income_by_year.get(yr_str)
        per: float | None = None
        if net_income and net_income > 0:
            per = round(mkt_cap / net_income, 2)
        if pbr and pbr > 0:
            yearly.append({"year": yr_str, "pbr": pbr, "per": per})

    yearly.sort(key=lambda x: x["year"])
    return yearly


def _empty() -> dict:
    return {"current_pbr": None, "current_per": None, "yearly": []}
