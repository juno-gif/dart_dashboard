"""
DART OpenAPI 격리 모듈 — 완전 구현: Story 1.2, 1.6, 3.3
⚠️ DART API 호출은 이 파일에서만 허용. 다른 모듈에서 OpenDartReader 직접 import 금지
[Source: architecture.md - DART API 격리 경계]
Story 3.3: sync_all_companies() 추가 — APScheduler 07:00 KST 자동 호출
"""
import logging
from datetime import datetime
from typing import Optional

import OpenDartReader

from app.core.config import settings
from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)

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
    except Exception as e:
        logger.error(f"[DART] finstate 실패 corp={corp_code} year={bsns_year}: {e}")
        return []
    if df is None or df.empty:
        logger.warning(f"[DART] finstate 빈 결과 corp={corp_code} year={bsns_year}")
        return []
    logger.info(f"[DART] finstate 성공 corp={corp_code} year={bsns_year} rows={len(df)}")
    return df.to_dict("records")


def sync_company_financials(corp_code: str, years: int = 5) -> dict:
    """기업 재무 데이터를 DART에서 수집해 DB에 UPSERT
    - DB-First: 이미 있는 데이터는 덮어쓰지 않음 (UPSERT on_conflict 무시)
    - DART API Key와 Service Key는 이 함수 외부로 절대 노출 금지
    """
    supabase = get_supabase_client()
    current_year = datetime.now().year - 1  # 직전 사업연도 기준
    synced_count = 0

    # account_mappings 전체 로드 (DB 우선, 없으면 빌트인 폴백 사용)
    mappings_res = supabase.table("account_mappings").select("account_nm, account_key").execute()
    mappings: dict[str, str] = dict(_BUILTIN_ACCOUNT_MAPPINGS)
    mappings.update({row["account_nm"]: row["account_key"] for row in (mappings_res.data or [])})

    for year_offset in range(years):
        bsns_year = str(current_year - year_offset)
        rows = get_financial_statements(corp_code, bsns_year)
        if not rows:
            continue

        upsert_data = []
        for row in rows:
            account_nm: str = row.get("account_nm", "") or ""
            account_key = mappings.get(account_nm)
            if account_key is None:
                account_key = account_nm  # 원본명 그대로
                logger.warning(f"Unmapped account: '{account_nm}' for {corp_code}/{bsns_year}")

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


# ── Story 3.3: 전체 기업 자동 갱신 ────────────────────────────────────────

DART_RATE_LIMIT_THRESHOLD = 18_000  # 20,000건 한도 대비 조기 중단 임계값
YEARS_PER_COMPANY = 5  # sync_company_financials 기본 years — API 호출 추정에 사용

# 기본 계정 매핑 (account_mappings 테이블이 비어 있을 때 폴백)
_BUILTIN_ACCOUNT_MAPPINGS: dict[str, str] = {
    "매출액": "revenue",
    "수익(매출액)": "revenue",
    "영업수익": "revenue",
    "매출": "revenue",
    "영업이익": "operating_profit",
    "영업이익(손실)": "operating_profit",
    "당기순이익": "net_income",
    "당기순이익(손실)": "net_income",
    "분기순이익": "net_income",
    "분기순이익(손실)": "net_income",
    "반기순이익": "net_income",
    "반기순이익(손실)": "net_income",
    "자산총계": "total_assets",
    "부채총계": "total_liabilities",
    "자본총계": "total_equity",
    "현금및현금성자산": "cash_and_equivalents",
    "현금및현금성자산(기말)": "cash_and_equivalents",
    "영업활동으로인한현금흐름": "operating_cf",
    "영업활동현금흐름": "operating_cf",
    "투자활동으로인한현금흐름": "investing_cf",
    "투자활동현금흐름": "investing_cf",
    "재무활동으로인한현금흐름": "financing_cf",
    "재무활동현금흐름": "financing_cf",
}


def sync_all_companies() -> dict:
    """모든 등록 기업의 DART 데이터 자동 갱신. APScheduler가 매일 07:00 KST에 호출.

    - 기업별 예외를 격리하여 일부 실패해도 전체 동기화 중단 방지
    - DART 일일 API 호출 한도(20,000건) 초과 방지: 18,000건 추정치에서 조기 종료
    - 신규 bsns_year 감지 시 companies.last_new_data_at 업데이트 (DB migration 선행 필요)
    [Source: architecture.md - Infrastructure & Deployment > scheduler/tasks.py]
    """
    supabase = get_supabase_client()

    try:
        # Story 5.2: 비상장사(is_listed=False)는 DART 동기화 제외 — MAN_ 코드로 DART 호출 시 API 쿼터 낭비 방지
        corp_res = supabase.table("companies").select("corp_code").eq("is_listed", True).execute()
        corp_codes = [row["corp_code"] for row in (corp_res.data or [])]
    except Exception as e:
        logger.error(f"[DART_SYNC] 기업 목록 조회 실패: {e}")
        return {"companies_synced": 0, "records_synced": 0}

    total_synced = 0
    records_synced = 0
    api_call_count = 0

    for corp_code in corp_codes:
        if api_call_count >= DART_RATE_LIMIT_THRESHOLD:
            logger.warning("[DART_SYNC] 한도 초과 방지: 조기 종료")
            break

        try:
            # 동기화 전 기존 bsns_year 목록 조회 (신규 데이터 감지용)
            before_res = (
                supabase.table("financial_statements")
                .select("bsns_year")
                .eq("corp_code", corp_code)
                .execute()
            )
            existing_years = {row["bsns_year"] for row in (before_res.data or [])}

            # DART 동기화 (기존 데이터 UPSERT — 오류 시 원본 유지)
            result = sync_company_financials(corp_code, years=YEARS_PER_COMPANY)
            records_synced += result["synced_rows"]
            api_call_count += YEARS_PER_COMPANY
            total_synced += 1

            # 동기화 후 bsns_year 재조회 → 신규 연도 감지
            after_res = (
                supabase.table("financial_statements")
                .select("bsns_year")
                .eq("corp_code", corp_code)
                .execute()
            )
            new_years = {row["bsns_year"] for row in (after_res.data or [])} - existing_years

            if new_years:
                supabase.table("companies").update(
                    {"last_new_data_at": datetime.utcnow().isoformat()}
                ).eq("corp_code", corp_code).execute()

        except Exception as e:
            logger.error(f"[DART_SYNC] 실패: {corp_code} - {e}")
            api_call_count += YEARS_PER_COMPANY  # 실패해도 호출 추정 카운트 누적

    logger.info(f"[DART_SYNC] 완료: {total_synced}개 기업, {records_synced}개 레코드 갱신")
    return {"companies_synced": total_synced, "records_synced": records_synced}
