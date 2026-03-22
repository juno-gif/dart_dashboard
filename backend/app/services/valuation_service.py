import time
import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# in-memory 캐시: stock_code -> (timestamp, data)
_valuation_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 86400  # 1일


def get_valuation_data(
    stock_code: str,
    equity_by_year: dict[str, int] | None = None,
    years: int = 10,
) -> dict:
    """yfinance 시가총액 + DB 자본총계로 PBR 계산 (1일 캐시).

    PBR = 시가총액 / 자본총계 — ticker.info["priceToBook"] 대신
    fast_info.market_cap 을 사용해 한국 주식에서도 안정적으로 동작.
    """
    now = time.time()
    cache_key = f"{stock_code}:{years}"
    if cache_key in _valuation_cache:
        ts, data = _valuation_cache[cache_key]
        if now - ts < _CACHE_TTL:
            return data

    try:
        import yfinance as yf

        ticker = yf.Ticker(f"{stock_code}.KS")
        fast = ticker.fast_info

        market_cap: float | None = getattr(fast, "market_cap", None)
        shares: float | None = getattr(fast, "shares", None)

        # ── 현재 PBR: 시가총액 / 최신 자본총계 ──────────────
        current_pbr: float | None = None
        if market_cap and equity_by_year:
            latest_year = max(equity_by_year.keys())
            equity = equity_by_year.get(latest_year)
            if equity and equity > 0:
                current_pbr = round(market_cap / equity, 2)

        # ── 현재 PER: info dict 에서 취득 (실패해도 무시) ───
        current_per: float | None = None
        try:
            info = ticker.info
            current_per = _safe_float(info.get("trailingPE"))
        except Exception:
            pass

        # ── 연도별 PBR: 연말 주가 × 발행주식수 / 연도 자본총계 ──
        yearly = _compute_yearly(ticker, shares, equity_by_year or {}, years)

        result = {"current_pbr": current_pbr, "current_per": current_per, "yearly": yearly}
        _valuation_cache[cache_key] = (now, result)
        logger.info(
            f"[Valuation] 조회 완료 stock={stock_code} pbr={current_pbr} years={len(yearly)}"
        )
        return result

    except Exception as e:
        logger.warning(f"[Valuation] 조회 실패 stock={stock_code}: {e}")
        return _empty()


def _compute_yearly(
    ticker, shares: float | None, equity_by_year: dict, years: int
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
            pbr = round(mkt_cap / equity, 2)
            if pbr > 0:
                yearly.append({"year": yr_str, "pbr": pbr, "per": None})

        yearly.sort(key=lambda x: x["year"])
        return yearly

    except Exception as e:
        logger.warning(f"[Valuation] yearly PBR 계산 실패: {e}")
        return []


def _safe_float(val) -> float | None:
    try:
        v = float(val)
        return v if v > 0 else None
    except Exception:
        return None


def _empty() -> dict:
    return {"current_pbr": None, "current_per": None, "yearly": []}
