import time
import logging
from datetime import datetime, timezone
from functools import wraps

import pandas as pd

logger = logging.getLogger(__name__)

# L1: in-memory 캐시 (프로세스 내 빠른 접근)
_valuation_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 86400  # 1일


def _retry_on_rate_limit(max_retries: int = 2, delay: float = 10.0):
    """Yahoo Finance rate limit(429) 시 delay 후 재시도."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries and (
                        "Too Many Requests" in str(e) or "Rate" in str(e) or "429" in str(e)
                    ):
                        wait = delay * (attempt + 1)
                        logger.warning(f"[Valuation] rate limit, {wait}s 후 재시도 (attempt {attempt+1})")
                        time.sleep(wait)
                        continue
                    raise
        return wrapper
    return decorator


def _supabase_cache_get(stock_code: str) -> dict | None:
    """Supabase valuation_cache에서 유효한 캐시 조회 (TTL 24h)."""
    try:
        from app.core.database import get_supabase_client
        sb = get_supabase_client()
        res = sb.table("valuation_cache").select("data, cached_at").eq("stock_code", stock_code).maybe_single().execute()
        if not res.data:
            return None
        cached_at_str = res.data["cached_at"]
        # UTC 기준 TTL 체크
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


def get_valuation_data(
    stock_code: str,
    equity_by_year: dict[str, int] | None = None,
    income_by_year: dict[str, int] | None = None,
    years: int = 10,
) -> dict:
    """PBR/PER 계산 — L1(memory) → L2(Supabase) → yfinance 순으로 조회.

    PBR = 시가총액 / 별도 자본총계
    PER = 시가총액 / 별도 순이익
    """
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

    # L3: yfinance 실시간 조회
    try:
        import yfinance as yf

        ticker, market_cap, shares, last_price, info = _resolve_ticker_with_retry(yf, stock_code)

        if not equity_by_year:
            equity_by_year = _equity_from_yfinance(ticker)

        # 현재 PBR
        current_pbr: float | None = None
        if market_cap and equity_by_year:
            latest_year = max(equity_by_year.keys())
            equity = equity_by_year.get(latest_year)
            if equity and equity > 0:
                current_pbr = round(market_cap / equity, 2)

        # 현재 PER
        current_per: float | None = None
        if market_cap and income_by_year:
            latest_year = max(income_by_year.keys())
            net_income = income_by_year.get(latest_year)
            if net_income and net_income > 0:
                current_per = round(market_cap / net_income, 2)

        yearly = _compute_yearly(ticker, shares, equity_by_year or {}, income_by_year or {}, years)

        result = {"current_pbr": current_pbr, "current_per": current_per, "yearly": yearly}

        # L1 + L2 저장
        _valuation_cache[cache_key] = (now, result)
        _supabase_cache_set(stock_code, result)

        logger.info(
            f"[Valuation] yfinance 조회 완료 stock={stock_code} pbr={current_pbr} per={current_per}"
            f" years={len(yearly)} | mktcap={market_cap} shares={shares}"
        )
        return result

    except Exception as e:
        logger.warning(f"[Valuation] 조회 실패 stock={stock_code}: {e}")
        return _empty()


def _compute_yearly(
    ticker,
    shares: float | None,
    equity_by_year: dict,
    income_by_year: dict,
    years: int,
) -> list:
    if not equity_by_year or not shares or shares <= 0:
        return []
    try:
        hist = ticker.history(period="max", interval="1mo")
        if hist.empty:
            return []

        current_year = datetime.now().year
        start_year = current_year - years + 1
        yearly = []

        for yr_str, equity in equity_by_year.items():
            yr = int(yr_str)
            if yr < start_year or equity <= 0:
                continue
            year_hist = hist[hist.index.year == yr]
            if year_hist.empty:
                continue
            price = float(year_hist.iloc[-1]["Close"])
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

    except Exception as e:
        logger.warning(f"[Valuation] yearly PBR/PER 계산 실패: {e}")
        return []


@_retry_on_rate_limit(max_retries=2, delay=10.0)
def _resolve_ticker_with_retry(yf, stock_code: str):
    return _resolve_ticker(yf, stock_code)


def _resolve_ticker(yf, stock_code: str):
    """KOSPI(.KS) 우선, market_cap 없으면 KOSDAQ(.KQ) 재시도."""
    for i, suffix in enumerate((".KS", ".KQ")):
        if i > 0:
            time.sleep(1.0)
        t = yf.Ticker(f"{stock_code}{suffix}")
        fast = t.fast_info
        mktcap = _nz(getattr(fast, "market_cap", None))
        shares = _nz(getattr(fast, "shares", None))
        last_price = _nz(getattr(fast, "last_price", None))

        info: dict = {}
        try:
            info = t.info or {}
        except Exception:
            pass

        if not mktcap:
            mktcap = _nz(info.get("marketCap")) or (
                last_price * shares if last_price and shares else None
            )
        if not shares:
            shares = _nz(info.get("sharesOutstanding")) or _nz(
                info.get("impliedSharesOutstanding")
            )
            if not shares and mktcap and last_price and last_price > 0:
                shares = mktcap / last_price

        if mktcap:
            return t, mktcap, shares, last_price, info

    t = yf.Ticker(f"{stock_code}.KS")
    return t, None, None, None, {}


def _equity_from_yfinance(ticker) -> dict:
    """DB에 자본총계 없을 때 yfinance balance_sheet 폴백 (최근 4년)."""
    try:
        bs = ticker.balance_sheet
        if bs is None or bs.empty:
            return {}
        equity_key = next(
            (k for k in bs.index if "equity" in str(k).lower() and "total" in str(k).lower()),
            None,
        )
        if equity_key is None:
            equity_key = next(
                (k for k in bs.index if "stockholder" in str(k).lower()), None
            )
        if equity_key is None:
            return {}
        result = {}
        for col in bs.columns:
            yr = str(pd.Timestamp(col).year)
            val = bs.loc[equity_key, col]
            if not pd.isna(val) and float(val) > 0:
                result[yr] = float(val)
        return result
    except Exception:
        return {}


def _nz(val) -> float | None:
    try:
        v = float(val)
        return v if v > 0 else None
    except Exception:
        return None


def _empty() -> dict:
    return {"current_pbr": None, "current_per": None, "yearly": []}
