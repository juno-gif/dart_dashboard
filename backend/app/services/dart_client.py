"""
DART OpenAPI 격리 모듈 — 완전 구현: Story 1.2, 1.6, 3.3
⚠️ DART API 호출은 이 파일에서만 허용. 다른 모듈에서 OpenDartReader 직접 import 금지
[Source: architecture.md - DART API 격리 경계]
Story 3.3: sync_all_companies() 추가 — APScheduler 07:00 KST 자동 호출
"""
import logging
import re
from datetime import datetime
from typing import Optional

import requests
import OpenDartReader
from bs4 import BeautifulSoup

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
    """기업명으로 DART 기업 검색 (최대 8건)
    정렬 우선순위: 정확한 이름 일치 → 상장사(stock_code 있음) → 나머지
    """
    dart = _get_dart()
    df = dart.corp_codes
    if df is None or df.empty:
        return []
    filtered = df[df["corp_name"].str.contains(keyword, na=False, case=False)].copy()
    if filtered.empty:
        return []
    filtered["_exact"] = (filtered["corp_name"] == keyword).astype(int)
    filtered["_listed"] = (
        filtered["stock_code"].notna() & (filtered["stock_code"].astype(str).str.strip() != "")
    ).astype(int)
    filtered = filtered.sort_values(["_exact", "_listed"], ascending=[False, False])
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
    # OpenDartReader가 dict(상태코드) 또는 None을 반환하는 경우 방어
    if df is None or isinstance(df, dict) or not hasattr(df, "empty") or df.empty:
        logger.warning(f"[DART] finstate 빈 결과 corp={corp_code} year={bsns_year}")
        return []
    logger.info(f"[DART] finstate 성공 corp={corp_code} year={bsns_year} rows={len(df)}")
    return df.to_dict("records")


# ── 감사보고서 파싱 ──────────────────────────────────────────────────────────

_REPRT_CODES = ["11011", "11012", "11013", "11014"]  # 사업보고서 → 반기 → 분기 순서


def _parse_amount(text: str) -> Optional[int]:
    """금액 문자열을 정수로 변환. 괄호는 음수 처리."""
    text = text.strip().replace(",", "").replace(" ", "")
    if not text or text in ("-", "―", ""):
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.replace("(", "").replace(")", "")
    try:
        val = int(text)
        return -val if negative else val
    except ValueError:
        return None


def _detect_unit_multiplier(soup: BeautifulSoup) -> int:
    """HTML에서 금액 단위(원/천원/백만원) 감지 후 배수 반환.
    '단위:원' 명시를 가장 먼저 확인 — 주석 등에 '백만원'이 언급돼도 오탐 방지.
    """
    text_normalized = re.sub(r"[\s\u3000\u00a0\u202f\u2009\u200b\t]+", "", soup.get_text())
    # 명시적 단위 표기를 최우선으로 확인 (예: "(단위: 원)", "(단위 : 백만원)")
    if "단위:원" in text_normalized:
        return 1
    if "단위:백만원" in text_normalized:
        return 1_000_000
    if "단위:천원" in text_normalized:
        return 1_000
    # 명시 없을 때 폴백: 문서 내 단위 키워드 탐색
    if "백만원" in text_normalized:
        return 1_000_000
    if "천원" in text_normalized:
        return 1_000
    return 1  # 기본값: 원


def _get_financial_from_audit_report(corp_code: str, bsns_year: str) -> list[dict]:
    """감사보고서(F001) HTML에서 재무제표 계정과목·금액 추출.
    사업보고서/분기보고서 없는 기업 전용 폴백.
    """
    logger.warning(f"[DART] _get_financial_from_audit_report 진입 corp={corp_code} year={bsns_year}")
    dart = _get_dart()

    # 감사보고서는 사업연도 다음 해 초(1~9월)에 제출
    next_year = str(int(bsns_year) + 1)
    start_dt = f"{next_year}0101"
    end_dt = f"{next_year}0930"

    try:
        filings = dart.list(
            corp_code,
            start=start_dt,
            end=end_dt,
            kind="F",
            kind_detail="F001",
        )
    except Exception as e:
        logger.warning(f"[DART] 감사보고서 목록 조회 실패 corp={corp_code} year={bsns_year}: {e}")
        return []

    if filings is None or (hasattr(filings, "empty") and filings.empty):
        logger.warning(f"[DART] 감사보고서 없음 corp={corp_code} year={bsns_year}")
        return []

    try:
        row = filings.iloc[0] if hasattr(filings, "iloc") else filings[0]
        # DART API 반환 컬럼명: rcept_no (접수번호)
        rcp_no = row.get("rcept_no") or row.get("rcp_no") if hasattr(row, "get") else row["rcept_no"]
    except (KeyError, IndexError) as e:
        logger.warning(f"[DART] 감사보고서 접수번호 추출 실패 corp={corp_code}: {e}")
        return []
    logger.warning(f"[DART] 감사보고서 발견 corp={corp_code} year={bsns_year} rcp={rcp_no}")

    try:
        sub_docs = dart.sub_docs(rcp_no)
    except Exception as e:
        logger.warning(f"[DART] 감사보고서 서브문서 조회 실패 rcp={rcp_no}: {e}")
        return []

    if sub_docs is None or (hasattr(sub_docs, "empty") and sub_docs.empty):
        return []

    # sub_docs 전체 제목 디버그 로그
    if hasattr(sub_docs, "iterrows"):
        titles = [str(doc.get("title", "")) for _, doc in sub_docs.iterrows()]
        logger.warning(f"[DART] 감사보고서 sub_docs rcp={rcp_no} titles={titles}")

    # 재무제표 관련 문서 URL 우선순위: 재무제표 > 손익계산서 > 재무상태표
    # 제목의 공백을 제거해서 비교 (DART 제목: '재 무 제 표', '(첨부)재 무 제 표' 등)
    target_url = None
    priority_keywords = ["재무제표", "손익계산서", "재무상태표", "포괄손익"]
    if hasattr(sub_docs, "iterrows"):
        for _, doc in sub_docs.iterrows():
            title = str(doc.get("title", ""))
            title_normalized = title.replace(" ", "").replace("\u3000", "")
            if any(kw in title_normalized for kw in priority_keywords):
                target_url = doc.get("url")
                logger.warning(f"[DART] 감사보고서 재무제표 문서 선택 title={title!r} url={target_url}")
                break

    if not target_url:
        logger.warning(f"[DART] 감사보고서 재무제표 문서 없음 rcp={rcp_no}")
        return []

    try:
        resp = requests.get(target_url, timeout=15)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.warning(f"[DART] 감사보고서 HTML 다운로드 실패 url={target_url}: {e}")
        return []

    multiplier = _detect_unit_multiplier(soup)
    results = []

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if len(cells) < 2:
                continue

            account_nm = cells[0]
            if not account_nm or account_nm in ("과목", "계정과목", "구분"):
                continue

            # 당기 금액 추출:
            # 1) 한글/영문 셀 제거 (주석 레이블 등)
            # 2) 쉼표 포함 + 4자리 이상 숫자 셀 우선 (실제 금액 형식: "927,389,000,000")
            # 3) 없으면 일반 숫자 셀 폴백 (주석번호 "4", "20" 등은 쉼표 없어 우선순위 낮음)
            non_text = [c for c in cells[1:] if not re.search(r"[가-힣a-zA-Z]", c)]
            financial = [
                c for c in non_text
                if "," in c
                and len(c.replace(",", "").replace("(", "").replace(")", "").strip()) >= 4
            ]
            amount = None
            for cell in (financial if financial else non_text):
                amount = _parse_amount(cell)
                if amount is not None:
                    break

            if amount is None:
                continue

            results.append(
                {
                    "account_nm": account_nm,
                    "thstrm_amount": str(amount * multiplier),
                    "reprt_code": "F001",
                    "fs_div": "OFS",
                }
            )

    logger.warning(
        f"[DART] 감사보고서 파싱 완료 corp={corp_code} year={bsns_year} rows={len(results)}"
    )
    return results


# ── 기본 계정 매핑 ────────────────────────────────────────────────────────────

_BUILTIN_ACCOUNT_MAPPINGS: dict[str, str] = {
    "매출액": "revenue",
    "수익(매출액)": "revenue",
    "영업수익": "revenue",
    "매출": "revenue",
    "영업이익": "operating_profit",
    "영업이익(손실)": "operating_profit",
    "영업손익": "operating_profit",
    "영업손익(손실)": "operating_profit",
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


def sync_company_financials(corp_code: str, years: int = 5) -> dict:
    """기업 재무 데이터를 DART에서 수집해 DB에 UPSERT
    - reprt_code 폴백: 11011 → 11012 → 11013 → 11014 → 감사보고서(F001)
    - audit_only=True 기업은 finstate 시도 없이 바로 감사보고서 파싱
    - DB-First: UPSERT on_conflict 무시
    """
    supabase = get_supabase_client()
    current_year = datetime.now().year - 1  # 직전 사업연도 기준
    synced_count = 0

    # account_mappings 전체 로드 (DB 우선, 없으면 빌트인 폴백 사용)
    mappings_res = supabase.table("account_mappings").select("account_nm, account_key").execute()
    mappings: dict[str, str] = dict(_BUILTIN_ACCOUNT_MAPPINGS)
    mappings.update({row["account_nm"]: row["account_key"] for row in (mappings_res.data or [])})

    # audit_only 플래그 조회 — True면 finstate 20번 시도 스킵
    try:
        corp_res = supabase.table("companies").select("audit_only").eq("corp_code", corp_code).single().execute()
        audit_only: bool = bool((corp_res.data or {}).get("audit_only", False))
    except Exception:
        audit_only = False

    for year_offset in range(years):
        bsns_year = str(current_year - year_offset)

        rows: list[dict] = []

        if not audit_only:
            # Step 1: 사업보고서/반기/분기 순서로 시도
            for reprt_code in _REPRT_CODES:
                rows = get_financial_statements(corp_code, bsns_year, reprt_code)
                if rows:
                    break

            # finstate 전부 실패 → 이 기업은 감사보고서 전용으로 플래그 저장
            if not rows:
                audit_only = True
                try:
                    supabase.table("companies").update({"audit_only": True}).eq("corp_code", corp_code).execute()
                    logger.warning(f"[DART] audit_only=True 저장 corp={corp_code}")
                except Exception as e:
                    logger.warning(f"[DART] audit_only 저장 실패 corp={corp_code}: {e}")

        # Step 2: audit_only 기업은 감사보고서 HTML 파싱
        if not rows:
            logger.warning(f"[DART] 감사보고서 폴백 시작 corp={corp_code} year={bsns_year}")
            try:
                rows = _get_financial_from_audit_report(corp_code, bsns_year)
            except Exception as e:
                logger.error(f"[DART] 감사보고서 폴백 예외 corp={corp_code} year={bsns_year}: {e}", exc_info=True)
                rows = []

        if not rows:
            continue

        upsert_data = []
        for row in rows:
            account_nm: str = row.get("account_nm", "") or ""
            # 글자 사이 공백 포함된 계정명도 매핑 가능하도록 정규화하여 조회
            account_nm_normalized = account_nm.replace(" ", "").replace("\u3000", "")
            # 로마자/아라비아숫자 접두사 제거 (예: "I.영업수익" → "영업수익", "1.매출액" → "매출액")
            account_nm_no_prefix = re.sub(r"^[IVXLCDMivxlcdm\d]+\.", "", account_nm_normalized)
            account_key = (
                mappings.get(account_nm)
                or mappings.get(account_nm_normalized)
                or mappings.get(account_nm_no_prefix)
            )
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
            # 감사보고서 HTML 파싱 시 동일 account_key가 여러 테이블에서 중복 추출될 수 있음
            # UPSERT 배치 내 중복 → "ON CONFLICT DO UPDATE command cannot affect row a second time" 오류 방지
            seen_keys: set = set()
            deduped: list[dict] = []
            for item in upsert_data:
                key = (item["corp_code"], item["bsns_year"], item["reprt_code"], item["fs_div"], item["account_key"])
                if key not in seen_keys:
                    seen_keys.add(key)
                    deduped.append(item)
            supabase.table("financial_statements").upsert(
                deduped,
                on_conflict="corp_code,bsns_year,reprt_code,fs_div,account_key",
            ).execute()
            synced_count += len(deduped)

    return {"corp_code": corp_code, "synced_rows": synced_count}


# ── Story 3.3: 전체 기업 자동 갱신 ────────────────────────────────────────

DART_RATE_LIMIT_THRESHOLD = 18_000  # 20,000건 한도 대비 조기 중단 임계값
YEARS_PER_COMPANY = 5  # sync_company_financials 기본 years — API 호출 추정에 사용


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
