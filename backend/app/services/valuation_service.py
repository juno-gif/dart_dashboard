import time
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# in-memory 캐시: stock_code -> (timestamp, data)
_valuation_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 86400  # 1일


def get_valuation_data(stock_code: str, years: int = 10) -> dict:
    """pykrx로 연도별 PBR/PER 데이터 조회 (1일 캐시).
    비상장 또는 조회 실패 시 빈 데이터 반환.
    """
    now = time.time()
    cache_key = f"{stock_code}:{years}"
    if cache_key in _valuation_cache:
        ts, data = _valuation_cache[cache_key]
        if now - ts < _CACHE_TTL:
            return data

    try:
        from pykrx import stock as pykrx_stock

        current_year = datetime.now().year
        start_year = current_year - years + 1

        df = pykrx_stock.get_market_fundamental_by_date(
            f"{start_year}0101",
            datetime.now().strftime("%Y%m%d"),
            stock_code,
        )

        if df is None or (hasattr(df, "empty") and df.empty):
            return _empty()

        df.index = pd.to_datetime(df.index)

        # 현재 PBR (가장 최근 거래일)
        latest = df.iloc[-1]
        current_pbr = _safe_float(latest, "PBR")
        current_per = _safe_float(latest, "PER")

        # 연도별 PBR (연말 마지막 거래일 기준)
        yearly = []
        for year in range(start_year, current_year + 1):
            year_df = df[df.index.year == year]
            if year_df.empty:
                continue
            last = year_df.iloc[-1]
            pbr = _safe_float(last, "PBR")
            per = _safe_float(last, "PER")
            if pbr is not None:
                yearly.append({"year": str(year), "pbr": pbr, "per": per})

        yearly.sort(key=lambda x: x["year"])
        result = {"current_pbr": current_pbr, "current_per": current_per, "yearly": yearly}
        _valuation_cache[cache_key] = (now, result)
        logger.info(f"[Valuation] pykrx 조회 완료 stock={stock_code} years={len(yearly)}")
        return result

    except Exception as e:
        logger.warning(f"[Valuation] pykrx 조회 실패 stock={stock_code}: {e}")
        return _empty()


def _safe_float(row, key: str) -> float | None:
    try:
        val = float(row[key])
        return val if val > 0 else None
    except Exception:
        return None


def _empty() -> dict:
    return {"current_pbr": None, "current_per": None, "yearly": []}
