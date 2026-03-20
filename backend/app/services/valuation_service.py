import time
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# in-memory 캐시: stock_code -> (timestamp, data)
_valuation_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 86400  # 1일


def get_valuation_data(stock_code: str, years: int = 10) -> dict:
    """yfinance로 연도별 PBR/PER 데이터 조회 (1일 캐시).
    비상장 또는 조회 실패 시 빈 데이터 반환.
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
        info = ticker.info

        current_pbr = _safe_float(info.get("priceToBook"))
        current_per = _safe_float(info.get("trailingPE"))
        yearly = _yearly_pbr(ticker, years)

        result = {"current_pbr": current_pbr, "current_per": current_per, "yearly": yearly}
        _valuation_cache[cache_key] = (now, result)
        logger.info(f"[Valuation] yfinance 조회 완료 stock={stock_code} pbr={current_pbr}")
        return result

    except Exception as e:
        logger.warning(f"[Valuation] yfinance 조회 실패 stock={stock_code}: {e}")
        return _empty()


def _yearly_pbr(ticker, years: int) -> list:
    try:
        bs = ticker.balance_sheet
        hist = ticker.history(period="max", interval="1mo")
        shares = getattr(ticker.fast_info, "shares", None)

        if bs is None or bs.empty or hist.empty or not shares or shares <= 0:
            return []

        # Stockholders equity 행 탐색
        equity_key = next(
            (k for k in bs.index if "equity" in str(k).lower() and "total" in str(k).lower()),
            None,
        )
        if equity_key is None:
            equity_key = next(
                (k for k in bs.index if "stockholder" in str(k).lower()),
                None,
            )
        if equity_key is None:
            return []

        current_year = datetime.now().year
        start_year = current_year - years + 1
        yearly = []

        for col in bs.columns:
            year = pd.Timestamp(col).year
            if year < start_year:
                continue
            equity = bs.loc[equity_key, col]
            if pd.isna(equity) or equity <= 0:
                continue
            bvps = float(equity) / float(shares)
            year_hist = hist[hist.index.year == year]
            if year_hist.empty:
                continue
            price = float(year_hist.iloc[-1]["Close"])
            pbr = round(price / bvps, 2) if bvps > 0 else None
            if pbr and pbr > 0:
                yearly.append({"year": str(year), "pbr": pbr, "per": None})

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
