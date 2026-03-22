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
    income_by_year: dict[str, int] | None = None,
    years: int = 10,
) -> dict:
    """yfinance 시가총액 + DB 자본총계/순이익으로 PBR/PER 계산 (1일 캐시).

    PBR = 시가총액 / 자본총계
    PER = 시가총액 / 순이익
    DB에 데이터 없으면 yfinance balance_sheet 폴백.
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
        last_price: float | None = getattr(fast, "last_price", None)

        # fast_info 미지원 소형주 → info dict 폴백
        info: dict = {}
        try:
            info = ticker.info or {}
        except Exception:
            pass

        if not market_cap:
            market_cap = _nz(info.get("marketCap")) or (
                last_price * shares if last_price and shares else None
            )
        if not shares:
            shares = _nz(info.get("sharesOutstanding")) or _nz(
                info.get("impliedSharesOutstanding")
            )
            if not shares and market_cap and last_price and last_price > 0:
                shares = market_cap / last_price

        # DB에 자본총계 없으면 yfinance balance_sheet로 폴백
        if not equity_by_year:
            equity_by_year = _equity_from_yfinance(ticker)

        # ── 현재 PBR: 시가총액 / 최신 자본총계 ──────────────
        current_pbr: float | None = None
        if market_cap and equity_by_year:
            latest_year = max(equity_by_year.keys())
            equity = equity_by_year.get(latest_year)
            if equity and equity > 0:
                current_pbr = round(market_cap / equity, 2)

        # ── 현재 PER: 시가총액 / 최신 순이익 ────────────────
        current_per: float | None = None
        if market_cap and income_by_year:
            latest_year = max(income_by_year.keys())
            net_income = income_by_year.get(latest_year)
            if net_income and net_income > 0:
                current_per = round(market_cap / net_income, 2)

        # ── 연도별 PBR/PER ───────────────────────────────────
        yearly = _compute_yearly(ticker, shares, equity_by_year or {}, income_by_year or {}, years)

        result = {"current_pbr": current_pbr, "current_per": current_per, "yearly": yearly}
        _valuation_cache[cache_key] = (now, result)
        logger.info(
            f"[Valuation] 조회 완료 stock={stock_code} pbr={current_pbr} per={current_per} years={len(yearly)}"
            f" | mktcap={market_cap} shares={shares}"
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
    """None/0/음수 제거용."""
    try:
        v = float(val)
        return v if v > 0 else None
    except Exception:
        return None


def _safe_float(val) -> float | None:
    try:
        v = float(val)
        return v if v > 0 else None
    except Exception:
        return None


def _empty() -> dict:
    return {"current_pbr": None, "current_per": None, "yearly": []}
