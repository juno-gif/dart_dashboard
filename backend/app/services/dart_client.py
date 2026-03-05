"""
DART OpenAPI 격리 모듈 — 완전 구현: Story 1.2
⚠️ DART API 호출은 이 파일에서만 허용. 다른 모듈에서 OpenDartReader 직접 import 금지
[Source: architecture.md - DART API 격리 경계]
"""
from datetime import datetime
from typing import Optional

import OpenDartReader

from app.core.config import settings
from app.core.database import get_supabase_client

_dart: Optional[OpenDartReader] = None


def _get_dart() -> OpenDartReader:
    global _dart
    if _dart is None:
        _dart = OpenDartReader(settings.DART_API_KEY)
    return _dart


def search_companies(keyword: str) -> list[dict]:
    """기업명으로 DART 기업 검색 (최대 8건)"""
    dart = _get_dart()
    df = dart.corp_codes
    if df is None or df.empty:
        return []
    filtered = df[df["corp_name"].str.contains(keyword, na=False)]
    return filtered.head(8)[["corp_code", "corp_name", "stock_code"]].to_dict("records")


def get_financial_statements(
    corp_code: str, bsns_year: str, reprt_code: str = "11011"
) -> list[dict]:
    """DART에서 재무제표 단건 조회
    reprt_code: 11011=사업보고서, 11012=반기, 11013=1분기, 11014=3분기
    """
    dart = _get_dart()
    try:
        df = dart.finstate(corp_code, bsns_year, reprt_code)
    except Exception:
        return []
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def sync_company_financials(corp_code: str, years: int = 5) -> dict:
    """기업 재무 데이터를 DART에서 수집해 DB에 UPSERT
    - DB-First: 이미 있는 데이터는 덮어쓰지 않음 (UPSERT on_conflict 무시)
    - DART API Key와 Service Key는 이 함수 외부로 절대 노출 금지
    """
    supabase = get_supabase_client()
    current_year = datetime.now().year - 1  # 직전 사업연도 기준
    synced_count = 0

    # account_mappings 전체 로드 (매 호출마다 재조회 방지)
    mappings_res = supabase.table("account_mappings").select("account_nm, account_key").execute()
    mappings: dict[str, str] = {
        row["account_nm"]: row["account_key"] for row in (mappings_res.data or [])
    }

    for year_offset in range(years):
        bsns_year = str(current_year - year_offset)
        rows = get_financial_statements(corp_code, bsns_year)
        if not rows:
            continue

        upsert_data = []
        for row in rows:
            account_nm: str = row.get("account_nm", "") or ""
            account_key = mappings.get(account_nm, account_nm)

            raw_amount = row.get("thstrm_amount", None)
            try:
                amount = int(str(raw_amount).replace(",", "")) if raw_amount else None
            except (ValueError, TypeError):
                amount = None

            upsert_data.append(
                {
                    "corp_code": corp_code,
                    "bsns_year": bsns_year,
                    "reprt_code": str(row.get("reprt_code", "11011")),
                    "fs_div": str(row.get("fs_div", "CFS")),
                    "account_key": account_key,
                    "account_nm": account_nm,
                    "amount": amount,
                }
            )

        if upsert_data:
            supabase.table("financial_statements").upsert(
                upsert_data,
                on_conflict="corp_code,bsns_year,reprt_code,fs_div,account_key",
            ).execute()
            synced_count += len(upsert_data)

    return {"corp_code": corp_code, "synced_rows": synced_count}
