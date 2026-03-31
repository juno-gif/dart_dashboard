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
    finstate() (fnlttSinglAcnt)는 IS/BS만 반환하므로 CF는 finstate_all()로 별도 보완.
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
    rows = df.to_dict("records")

    # finstate()는 CF(현금흐름표) 미포함 경우 있음 → finstate_all()로 CF 행 보완
    has_cf = any(str(r.get("sj_div", "")).upper() == "CF" for r in rows)
    if not has_cf:
        cf_rows = _get_cf_rows_from_finstate_all(dart, corp_code, bsns_year, reprt_code)
        rows.extend(cf_rows)

    # finstate()가 IS 매출 계정을 누락하는 경우(영업수익 등 CIS 형식 기업) → finstate_all()로 보완
    # 이자수익·순이자손익은 제외: 비금융사(이글루 등)에서 하위 항목으로 등장해 has_revenue=True가 되면
    # finstate_all()을 통한 영업수익 수집이 스킵되는 버그 유발
    _REVENUE_NMS = {"매출액", "영업수익", "수익(매출액)", "영업수익(매출액)", "매출"}
    def _norm_nm(nm: str) -> str:
        s = nm.replace(" ", "").replace("\u3000", "")
        return re.sub(r"^[IVXLCDMivxlcdm\u2160-\u217F\d]+\.", "", s)
    has_revenue = any(
        _norm_nm(str(r.get("account_nm", ""))) in _REVENUE_NMS for r in rows
    )
    if not has_revenue:
        is_rows = _get_is_rows_from_finstate_all(dart, corp_code, bsns_year, reprt_code)
        rows.extend(is_rows)

    # finstate()는 현금및현금성자산(기말)을 표준 계정으로 반환하지 않음 → finstate_all() CF에서 보완
    _CASH_NMS = {"현금및현금성자산", "현금및현금성자산(기말)"}
    has_cash = any(
        str(r.get("account_nm", "")).replace(" ", "") in _CASH_NMS for r in rows
    )
    if not has_cash:
        cash_rows = _get_cash_rows_from_finstate_all(dart, corp_code, bsns_year, reprt_code)
        rows.extend(cash_rows)

    return rows


def _get_is_rows_from_finstate_all(
    dart, corp_code: str, bsns_year: str, reprt_code: str
) -> list[dict]:
    """finstate_all()에서 IS/CIS(손익계산서) 행 추출 — 매출 계정 누락 시 보완용.
    CFS/OFS 모두 수집해 반환 (연결·별도 둘 다 보완).
    """
    all_rows: list[dict] = []
    for fs_div in ("CFS", "OFS"):
        try:
            df = dart.finstate_all(corp_code, bsns_year, reprt_code, fs_div=fs_div)
        except Exception as e:
            logger.warning(f"[DART] finstate_all IS 조회 실패 corp={corp_code} year={bsns_year} fs={fs_div}: {e}")
            continue
        if df is None or isinstance(df, dict) or not hasattr(df, "empty") or df.empty:
            continue
        if "sj_div" not in df.columns:
            continue
        is_df = df[df["sj_div"].str.upper().isin(["IS", "CIS"])]
        if is_df.empty:
            continue
        logger.info(f"[DART] finstate_all IS 보완 corp={corp_code} year={bsns_year} fs={fs_div} rows={len(is_df)}")
        # finstate_all 응답에는 fs_div 컬럼이 없으므로 명시적으로 주입
        rows_list = is_df.to_dict("records")
        for r in rows_list:
            r["fs_div"] = fs_div
        all_rows.extend(rows_list)
    return all_rows


def _get_cash_rows_from_finstate_all(
    dart, corp_code: str, bsns_year: str, reprt_code: str
) -> list[dict]:
    """finstate_all()에서 현금및현금성자산(기말) 행만 추출 — cash_and_equivalents 누락 시 보완.
    CFS/OFS 모두 수집해 반환.
    기말 잔액만 추출 (기초/증가/감소 제외).
    """
    all_rows: list[dict] = []
    for fs_div in ("CFS", "OFS"):
        try:
            df = dart.finstate_all(corp_code, bsns_year, reprt_code, fs_div=fs_div)
        except Exception as e:
            logger.warning(f"[DART] finstate_all cash 조회 실패 corp={corp_code} year={bsns_year} fs={fs_div}: {e}")
            continue
        if df is None or isinstance(df, dict) or not hasattr(df, "empty") or df.empty:
            continue
        if "sj_div" not in df.columns:
            continue
        cf_df = df[df["sj_div"].str.upper() == "CF"]
        if cf_df.empty:
            continue
        # 기말 현금 계정 추출: "현금및현금성자산" 또는 "기말의현금" 포함 + 기초/증가/감소 제외
        nm = cf_df["account_nm"].str.replace(" ", "", regex=False)
        cash_df = cf_df[
            (
                nm.str.contains("현금및현금성자산", na=False)
                | nm.str.contains("기말의현금", na=False)
            )
            & ~nm.str.contains("기초", na=False)
            & ~nm.str.contains("증가|감소", na=False, regex=True)
        ]
        if cash_df.empty:
            logger.warning(f"[DART] finstate_all cash 없음 corp={corp_code} year={bsns_year} fs={fs_div} CF계정={cf_df['account_nm'].tolist()}")
            continue
        logger.info(f"[DART] finstate_all cash 보완 corp={corp_code} year={bsns_year} fs={fs_div} rows={len(cash_df)}")
        rows_list = cash_df.to_dict("records")
        for r in rows_list:
            r["fs_div"] = fs_div
        all_rows.extend(rows_list)
    return all_rows


def _get_cf_rows_from_finstate_all(
    dart, corp_code: str, bsns_year: str, reprt_code: str
) -> list[dict]:
    """finstate_all()에서 CF(현금흐름표) 행만 추출 — CFS 우선, 없으면 OFS."""
    for fs_div in ("CFS", "OFS"):
        try:
            df = dart.finstate_all(corp_code, bsns_year, reprt_code, fs_div=fs_div)
        except Exception as e:
            logger.warning(f"[DART] finstate_all CF 조회 실패 corp={corp_code} year={bsns_year} fs={fs_div}: {e}")
            continue
        if df is None or isinstance(df, dict) or not hasattr(df, "empty") or df.empty:
            continue
        if "sj_div" not in df.columns:
            continue
        cf_df = df[df["sj_div"].str.upper() == "CF"]
        if cf_df.empty:
            continue
        logger.info(f"[DART] finstate_all CF 보완 corp={corp_code} year={bsns_year} fs={fs_div} rows={len(cf_df)}")
        return cf_df.to_dict("records")
    return []


# ── 감사보고서 파싱 ──────────────────────────────────────────────────────────

_REPRT_CODES = ["11011", "11014", "11012", "11013"]  # 데이터 최신성 우선: 연간 → 3분기(9개월) → 반기(6개월) → 1분기(3개월)


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


def _is_standard_amount(cell: str) -> bool:
    """표준 한국 금액 형식 여부 확인: 쉼표는 3자리마다 구분자로만 허용.
    '4,6,17' (주석참조번호) 같은 비표준 쉼표 그룹을 금액으로 오인하는 것 방지.
    표준 예: '47,172,900,043' → True
    비표준 예: '4,6,17' (1,1,2자리 그룹) → False
    소수점 예: '1,470.00' (환율) → False
    """
    clean = cell.strip()
    if clean.startswith("(") and clean.endswith(")"):
        clean = clean[1:-1]
    if not re.fullmatch(r"[\d,]+", clean):
        return False
    parts = clean.split(",")
    if not parts[0].isdigit() or not (1 <= len(parts[0]) <= 3):
        return False
    return all(p.isdigit() and len(p) == 3 for p in parts[1:])


def _detect_unit_multiplier(soup: BeautifulSoup) -> int:
    """HTML 문서 전체에서 금액 단위(원/천원/백만원) 감지 후 배수 반환. 테이블별 감지의 폴백용."""
    text_normalized = re.sub(r"[\s\u3000\u00a0\u202f\u2009\u200b\t]+", "", soup.get_text())
    if "단위:천원" in text_normalized:
        return 1_000
    if "단위:백만원" in text_normalized:
        return 1_000_000
    if "단위:원" in text_normalized:
        return 1
    if "백만원" in text_normalized:
        return 1_000_000
    if "천원" in text_normalized:
        return 1_000
    return 1  # 기본값: 원


def _detect_table_unit(table, global_multiplier: int) -> int:
    """테이블별 단위 감지 — 테이블 caption/헤더행 우선, 없으면 global_multiplier 사용.
    동일 문서 내 IS(원)·BS(천원) 혼용 감사보고서 대응.
    """
    # 테이블 직전 형제 요소 (p, div 등)에서 단위 탐색
    prev = table.find_previous_sibling()
    context_text = ""
    if prev:
        context_text += prev.get_text()
    caption = table.find("caption")
    if caption:
        context_text += caption.get_text()
    # 첫 3개 행 헤더에서도 탐색
    for tr in table.find_all("tr")[:3]:
        context_text += tr.get_text()

    t = re.sub(r"[\s\u3000\u00a0]+", "", context_text)
    if "단위:천원" in t:
        return 1_000
    if "단위:백만원" in t:
        return 1_000_000
    if "단위:원" in t:
        return 1
    return global_multiplier


def _get_financial_from_audit_report(corp_code: str, bsns_year: str) -> list[dict]:
    """감사보고서(F001) HTML에서 재무제표 계정과목·금액 추출.
    연결/별도 감사보고서를 모두 처리해 fs_div를 제목 키워드로 자동 판별.
    """
    logger.warning(f"[DART] _get_financial_from_audit_report 진입 corp={corp_code} year={bsns_year}")
    dart = _get_dart()

    # 감사보고서는 사업연도 다음 해 초(1~9월)에 제출
    next_year = str(int(bsns_year) + 1)
    start_dt = f"{next_year}0101"
    end_dt = f"{next_year}0930"

    try:
        filings = dart.list(corp_code, start=start_dt, end=end_dt, kind="F", kind_detail="F001")
    except Exception as e:
        logger.warning(f"[DART] 감사보고서 목록 조회 실패 corp={corp_code} year={bsns_year}: {e}")
        return []

    if filings is None or (hasattr(filings, "empty") and filings.empty):
        logger.warning(f"[DART] 감사보고서 없음 corp={corp_code} year={bsns_year}")
        return []

    # 모든 감사보고서 접수번호 수집 (연결/별도가 별도 파일링인 경우 대응)
    rcp_nos: list[str] = []
    if hasattr(filings, "iterrows"):
        for _, row in filings.iterrows():
            rcp_no = row.get("rcept_no") or row.get("rcp_no")
            if rcp_no:
                rcp_nos.append(str(rcp_no))
    elif filings:
        rcp_nos = [str(filings[0].get("rcept_no") or filings[0].get("rcp_no", ""))]

    if not rcp_nos:
        return []

    # 제목 키워드: 연결 여부 판별
    CFS_KWS = ["연결재무제표", "연결포괄손익", "연결재무상태표", "연결손익계산서"]
    FINANCIAL_KWS = ["재무제표", "손익계산서", "재무상태표", "포괄손익"]

    results: list[dict] = []
    seen: set[tuple[str, str]] = set()  # (fs_div, account_nm) dedup

    for rcp_no in rcp_nos:
        logger.warning(f"[DART] 감사보고서 처리 corp={corp_code} year={bsns_year} rcp={rcp_no}")
        try:
            sub_docs = dart.sub_docs(rcp_no)
        except Exception as e:
            logger.warning(f"[DART] 서브문서 조회 실패 rcp={rcp_no}: {e}")
            continue

        if sub_docs is None or (hasattr(sub_docs, "empty") and sub_docs.empty):
            continue

        if hasattr(sub_docs, "iterrows"):
            titles = [str(doc.get("title", "")) for _, doc in sub_docs.iterrows()]
            logger.warning(f"[DART] sub_docs rcp={rcp_no} titles={titles}")

        # sub_docs에서 연결/별도 재무제표 URL 수집 (중복 URL 제외)
        target_docs: list[tuple[str, str]] = []  # (url, fs_div)
        seen_urls: set[str] = set()
        if hasattr(sub_docs, "iterrows"):
            for _, doc in sub_docs.iterrows():
                title = str(doc.get("title", ""))
                title_clean = title.replace(" ", "").replace("\u3000", "")
                url = doc.get("url")
                if not url or url in seen_urls:
                    continue
                if any(kw in title_clean for kw in CFS_KWS):
                    target_docs.append((url, "CFS"))
                    seen_urls.add(url)
                    logger.warning(f"[DART] 연결 재무제표 발견 title={title!r}")
                elif any(kw in title_clean for kw in FINANCIAL_KWS):
                    target_docs.append((url, "OFS"))
                    seen_urls.add(url)
                    logger.warning(f"[DART] 별도 재무제표 발견 title={title!r}")

        # 연결/별도 구분 문서가 없으면 첫 번째 재무 문서를 OFS로 폴백 (기존 동작 유지)
        if not target_docs and hasattr(sub_docs, "iterrows"):
            for _, doc in sub_docs.iterrows():
                url = doc.get("url")
                title = str(doc.get("title", ""))
                title_clean = title.replace(" ", "").replace("\u3000", "")
                if url and any(kw in title_clean for kw in FINANCIAL_KWS):
                    target_docs.append((url, "OFS"))
                    logger.warning(f"[DART] 폴백 재무제표 선택 title={title!r}")
                    break

        # 각 문서 파싱
        for url, fs_div in target_docs:
            try:
                resp = requests.get(url, timeout=15)
                resp.encoding = resp.apparent_encoding or "utf-8"
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as e:
                logger.warning(f"[DART] HTML 다운로드 실패 url={url}: {e}")
                continue

            global_multiplier = _detect_unit_multiplier(soup)

            for table in soup.find_all("table"):
                multiplier = _detect_table_unit(table, global_multiplier)
                for tr in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if len(cells) < 2:
                        continue

                    account_nm = cells[0]
                    if not account_nm or account_nm in ("과목", "계정과목", "구분"):
                        continue

                    dedup_key = (fs_div, account_nm)
                    if dedup_key in seen:
                        continue

                    non_text = [c for c in cells[1:] if not re.search(r"[가-힣a-zA-Z]", c)]
                    financial = [
                        c for c in non_text
                        if "," in c
                        and len(c.replace(",", "").replace("(", "").replace(")", "").strip()) >= 4
                        and _is_standard_amount(c)
                    ]
                    amount = None
                    for cell in (financial if financial else non_text):
                        amount = _parse_amount(cell)
                        if amount is not None:
                            break

                    if amount is None:
                        continue

                    seen.add(dedup_key)
                    results.append({
                        "account_nm": account_nm,
                        "thstrm_amount": str(amount * multiplier),
                        "reprt_code": "F001",
                        "fs_div": fs_div,
                    })

    logger.warning(f"[DART] 감사보고서 파싱 완료 corp={corp_code} year={bsns_year} rows={len(results)}")
    return results


# ── 기본 계정 매핑 ────────────────────────────────────────────────────────────

# 순손실/영업손실 등 "손실" 계정은 DART가 양수로 반환 → 저장 시 부호 반전 필요
_NEGATE_ACCOUNT_NMS: set[str] = {
    "영업손실",
    "당기순손실",
    "분기순손실",
    "반기순손실",
}

_BUILTIN_ACCOUNT_MAPPINGS: dict[str, str] = {
    "매출액": "revenue",
    "수익(매출액)": "revenue",
    "영업수익": "revenue",
    "영업수익(매출액)": "revenue",  # 카카오게임즈 등 (영업수익+매출액 복합 표기)
    "매출": "revenue",
    "이자수익": "revenue",    # 은행업 하위항목 (토스뱅크 등)
    "순이자손익": "revenue",  # 은행업 최상위 항목 (이자수익-이자비용)
    "영업이익": "operating_profit",
    "영업이익(손실)": "operating_profit",
    "영업손실": "operating_profit",
    "영업손익": "operating_profit",
    "영업손익(손실)": "operating_profit",
    "당기순이익": "net_income",
    "당기순이익(손실)": "net_income",
    "당기순손실": "net_income",
    "당기순손익": "net_income",
    "분기순이익": "net_income",
    "분기순이익(손실)": "net_income",
    "분기순손실": "net_income",
    "반기순이익": "net_income",
    "반기순이익(손실)": "net_income",
    "반기순손실": "net_income",
    "자산총계": "total_assets",
    "부채총계": "total_liabilities",
    "자본총계": "total_equity",
    "현금및현금성자산": "cash_and_equivalents",
    "현금및현금성자산(기말)": "cash_and_equivalents",
    "기말현금및현금성자산": "cash_and_equivalents",
    "기말의현금및현금성자산": "cash_and_equivalents",
    "기말의 현금및현금성자산": "cash_and_equivalents",
    "현금및현금성자산의기말잔액": "cash_and_equivalents",
    "현금및현금성자산기말잔액": "cash_and_equivalents",
    "기말의현금": "cash_and_equivalents",
    "기말의현금및현금성자산등": "cash_and_equivalents",
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

    # audit_only=True 기업도 최신 연도에 한해 finstate 탐색 — 사업보고서로 전환한 기업 자동 감지
    if audit_only:
        probe_year = str(current_year)
        for reprt_code in _REPRT_CODES:
            probe_rows = get_financial_statements(corp_code, probe_year, reprt_code)
            if probe_rows:
                audit_only = False
                try:
                    supabase.table("companies").update({"audit_only": False}).eq("corp_code", corp_code).execute()
                    logger.info(f"[DART] audit_only 자동 해제 corp={corp_code} (사업보고서 발견 year={probe_year})")
                except Exception as e:
                    logger.warning(f"[DART] audit_only 해제 실패 corp={corp_code}: {e}")
                break

    for year_offset in range(years):
        bsns_year = str(current_year - year_offset)

        rows: list[dict] = []

        if not audit_only:
            # Step 1: 사업보고서/반기/분기 순서로 시도
            for reprt_code in _REPRT_CODES:
                rows = get_financial_statements(corp_code, bsns_year, reprt_code)
                if rows:
                    break
            # 연도별 finstate 실패는 해당 연도만 audit 폴백 — 루프 전체에 audit_only 전파 금지
            # (연속 실패로 audit_only 플래그 설정은 sync_all_companies 에서만 판단)

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
            # \s·\u3000·\u00a0 등 모든 유니코드 공백 제거 (DART 감사보고서의 비표준 공백 대응)
            account_nm_normalized = re.sub(r"[\s\u3000\u00a0\u202f\u2009\u200b\u2003\u2002]+", "", account_nm)
            # 로마자/아라비아숫자 접두사 제거 (예: "I.영업수익" → "영업수익", "Ⅰ.영업수익" → "영업수익", "1.매출액" → "매출액")
            # \u2160-\u217F: 유니코드 로마자 (Ⅰ Ⅱ Ⅲ ... DART에서 실제 사용하는 전각 로마자)
            account_nm_no_prefix = re.sub(r"^[IVXLCDMivxlcdm\u2160-\u217F\d]+\.", "", account_nm_normalized)
            # 주석번호 제거 (예: "영업수익(주25,32)" → "영업수익", "매출액(주석14와20)" → "매출액")
            account_nm_no_note = re.sub(r"\(주[^)]*\)", "", account_nm_no_prefix)
            account_key = (
                mappings.get(account_nm)
                or mappings.get(account_nm_normalized)
                or mappings.get(account_nm_no_prefix)
                or mappings.get(account_nm_no_note)
            )
            if account_key is None:
                account_key = account_nm[:200]  # 원본명 그대로 (DB 컬럼 길이 초과 방지)
                logger.warning(f"Unmapped account: '{account_nm}' for {corp_code}/{bsns_year}")

            # 분기/반기 보고서의 IS·CF 계정은 누적(YTD) 금액 사용
            # thstrm_amount = 해당 분기 단독 금액 (3개월치)
            # thstrm_add_amount = 당해 연도 누적 금액 → IS·CF에 올바른 값
            sj_div = str(row.get("sj_div", ""))
            row_reprt_code = str(row.get("reprt_code", "11011"))
            use_cumulative = row_reprt_code in ("11012", "11013", "11014") and sj_div in ("IS", "CIS", "CF")
            if use_cumulative:
                raw_amount = row.get("thstrm_add_amount") or row.get("thstrm_amount")
            else:
                raw_amount = row.get("thstrm_amount", None)
            try:
                amount = int(str(raw_amount).replace(",", "")) if raw_amount else None
            except (ValueError, TypeError):
                amount = None

            # 손실 계정(영업손실·당기순손실 등)은 DART가 양수 반환 → 부호 반전
            if amount is not None and account_nm_no_note in _NEGATE_ACCOUNT_NMS:
                amount = -amount

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
            # 자산총계 누락 시 자본총계 + 부채총계로 파생 계산 (BS 좌우 양식 감사보고서 대응)
            for fs_div_val in ("OFS", "CFS"):
                has_assets = any(d["account_key"] == "total_assets" and d["fs_div"] == fs_div_val for d in upsert_data)
                if not has_assets:
                    equity = next((d["amount"] for d in upsert_data if d["account_key"] == "total_equity" and d["fs_div"] == fs_div_val and d["amount"]), None)
                    liabilities = next((d["amount"] for d in upsert_data if d["account_key"] == "total_liabilities" and d["fs_div"] == fs_div_val and d["amount"]), None)
                    if equity is not None and liabilities is not None:
                        reprt = next((d["reprt_code"] for d in upsert_data if d["fs_div"] == fs_div_val), "11011")
                        upsert_data.append({
                            "corp_code": corp_code,
                            "bsns_year": bsns_year,
                            "reprt_code": reprt,
                            "fs_div": fs_div_val,
                            "account_key": "total_assets",
                            "account_nm": "자산총계(파생)",
                            "amount": equity + liabilities,
                        })

            # 감사보고서 HTML 파싱 시 동일 account_key가 여러 테이블에서 중복 추출될 수 있음
            # UPSERT 배치 내 중복 → "ON CONFLICT DO UPDATE command cannot affect row a second time" 오류 방지
            # 동일 키 충돌 시 절댓값이 큰 항목 유지 (예: 영업수익 1432억 vs 이자수익 8억 → 영업수익 선택)
            dedup_map: dict = {}
            for item in upsert_data:
                key = (item["corp_code"], item["bsns_year"], item["reprt_code"], item["fs_div"], item["account_key"])
                if key not in dedup_map or abs(item.get("amount", 0)) > abs(dedup_map[key].get("amount", 0)):
                    dedup_map[key] = item
            deduped = list(dedup_map.values())
            logger.info(f"[DART] UPSERT 시작 corp={corp_code} year={bsns_year} rows={len(deduped)}")
            try:
                res = supabase.table("financial_statements").upsert(
                    deduped,
                    on_conflict="corp_code,bsns_year,reprt_code,fs_div,account_key",
                ).execute()
                if hasattr(res, "data") and res.data is not None:
                    logger.info(f"[DART] UPSERT 완료 corp={corp_code} year={bsns_year} saved={len(res.data)}")
                else:
                    logger.warning(f"[DART] UPSERT 응답 비정상 corp={corp_code} year={bsns_year} res={res}")
            except Exception as e:
                logger.error(f"[DART] UPSERT 실패 corp={corp_code} year={bsns_year}: {e}", exc_info=True)
                continue
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
