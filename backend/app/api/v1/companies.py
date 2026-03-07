"""
기업 검색 API — Story 1.3, 3.3, 5.1, 5.2
DB-First: companies 테이블 먼저 조회 → 없으면 DART API → DB UPSERT
Story 3.3: GET /companies/new-data-status — 신규 분기 데이터 알림 상태 조회
Story 5.1: POST /companies/manual — 비상장사 수기 입력
Story 5.2: GET/PUT /companies/{corp_code}/manual — Admin 비상장사 재무 데이터 조회·수정
[Source: architecture.md - DB-First Caching Strategy]
"""
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user, require_admin
from app.core.database import get_supabase_client
from app.models.schemas import Company, ManualCompanyCreate, ManualCompanyFinancialsResponse, ManualFinancialEntry
from app.services.dart_client import search_companies as dart_search_companies

router = APIRouter()


# Story 3.3: new-data-status는 /companies/search 보다 앞에 등록 (경로 충돌 방지)
@router.get("/companies/new-data-status")
async def get_new_data_status(
    codes: str = Query(..., description="콤마 구분된 corp_code 목록 (예: 005930,035720)"),
    _: object = Depends(get_current_user),
):
    """분석 세트의 기업 중 신규 분기 데이터(7일 이내 last_new_data_at)가 있는 corp_code 목록 반환.
    DB 오류 시 빈 배열 반환 (알림 실패는 비치명적).
    """
    supabase = get_supabase_client()
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return {"new_data_codes": []}

    threshold = (datetime.utcnow() - timedelta(days=7)).isoformat()
    try:
        res = (
            supabase.table("companies")
            .select("corp_code")
            .in_("corp_code", code_list)
            .gte("last_new_data_at", threshold)
            .execute()
        )
    except Exception:
        return {"new_data_codes": []}

    return {"new_data_codes": [row["corp_code"] for row in (res.data or [])]}


@router.get("/companies/search", response_model=list[Company])
async def search_companies(
    q: str = Query(..., min_length=1, description="기업명 또는 종목코드"),
    limit: int = Query(8, ge=1, le=20),
    _: object = Depends(get_current_user),
):
    """DB-First 기업 검색: DB 조회 → 없으면 DART API → DB UPSERT"""
    supabase = get_supabase_client()

    # H1: PostgREST OR 필터 인젝션 방어 — 콤마·괄호 제거 후 필터 적용
    q_safe = q.replace(",", "").replace("(", "").replace(")", "").strip()

    # 1. DART API 검색 (항상 수행 — 정렬 신뢰도 높음)
    dart_results = dart_search_companies(q)
    dart_data = [
        {
            "corp_code": r["corp_code"],
            "company_name": r["corp_name"],
            "stock_code": r.get("stock_code") or None,
            "is_listed": bool(r.get("stock_code")),
        }
        for r in dart_results
    ]

    if dart_data:
        # DART 결과를 DB에 UPSERT (캐시 갱신)
        try:
            supabase.table("companies").upsert(dart_data, on_conflict="corp_code").execute()
        except Exception:
            pass
        return dart_data[:limit]

    # 2. DART 결과 없으면 DB 폴백 (종목코드 직접 검색 등 엣지케이스)
    res = (
        supabase.table("companies")
        .select("*")
        .or_(f"company_name.ilike.%{q_safe}%,stock_code.eq.{q_safe}")
        .limit(limit)
        .execute()
    )
    return res.data or []


# ── Story 5.1: 비상장사 수기 입력 ──────────────────────────────
@router.post("/companies/manual", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_manual_company(body: ManualCompanyCreate, user=Depends(get_current_user)):
    """비상장사 수기 입력 — companies IS_listed=False 저장, financial_statements PL 저장"""
    supabase = get_supabase_client()

    # 동일 company_name의 기존 비상장사 재사용 (중복 방지)
    try:
        existing = (
            supabase.table("companies")
            .select("corp_code")
            .eq("company_name", body.company_name)
            .eq("is_listed", False)
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if existing.data:
        corp_code = existing.data[0]["corp_code"]
    else:
        corp_code = "MAN_" + uuid.uuid4().hex[:8].upper()
        try:
            supabase.table("companies").insert({
                "corp_code": corp_code,
                "company_name": body.company_name,
                "is_listed": False,
                "stock_code": None,
            }).execute()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
            )

    # financial_statements UPSERT — PL 3계정
    rows = []
    for entry in body.financials:
        for account_key, amount in [
            ("revenue", entry.revenue),
            ("operating_profit", entry.operating_profit),
            ("net_income", entry.net_income),
        ]:
            if amount is not None:
                rows.append({
                    "corp_code": corp_code,
                    "bsns_year": entry.bsns_year,
                    "reprt_code": "11011",
                    "fs_div": "OFS",
                    "account_key": account_key,
                    "account_nm": None,
                    "amount": amount,
                })

    if rows:
        try:
            supabase.table("financial_statements").upsert(
                rows,
                on_conflict="corp_code,bsns_year,reprt_code,fs_div,account_key",
            ).execute()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "DB_UNAVAILABLE", "message": "재무 데이터 저장에 실패했습니다.", "status_code": 503},
            )

    return Company(
        corp_code=corp_code,
        company_name=body.company_name,
        stock_code=None,
        is_listed=False,
    )


# ── Story 5.2: Admin 비상장사 재무 데이터 조회 및 수정 ────────────────
@router.get("/companies/{corp_code}/manual", response_model=ManualCompanyFinancialsResponse)
async def get_manual_company_financials(corp_code: str, user=Depends(get_current_user)):
    """Admin 전용: 비상장사 수기 입력 재무 데이터 조회 (ManualEntryDialog 편집 모드 prefill용)"""
    require_admin(user)
    supabase = get_supabase_client()

    # 회사 존재 및 비상장사 여부 확인
    try:
        company_res = (
            supabase.table("companies")
            .select("corp_code, company_name")
            .eq("corp_code", corp_code)
            .eq("is_listed", False)
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not company_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "COMPANY_NOT_FOUND", "message": "비상장사를 찾을 수 없습니다.", "status_code": 404},
        )

    company_name = company_res.data[0]["company_name"]

    # financial_statements에서 PL 3계정 조회 (reprt_code="11011", fs_div="OFS")
    try:
        fin_res = (
            supabase.table("financial_statements")
            .select("bsns_year, account_key, amount")
            .eq("corp_code", corp_code)
            .eq("reprt_code", "11011")
            .eq("fs_div", "OFS")
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "재무 데이터 조회에 실패했습니다.", "status_code": 503},
        )

    # 연도별 그룹핑 → ManualFinancialEntry 리스트 변환
    by_year: dict[str, dict[str, int]] = defaultdict(dict)
    for row in (fin_res.data or []):
        by_year[row["bsns_year"]][row["account_key"]] = row["amount"]

    financials = [
        ManualFinancialEntry(
            bsns_year=year,
            revenue=data.get("revenue"),
            operating_profit=data.get("operating_profit"),
            net_income=data.get("net_income"),
        )
        for year, data in sorted(by_year.items())
    ]

    return ManualCompanyFinancialsResponse(
        corp_code=corp_code,
        company_name=company_name,
        financials=financials,
    )


@router.put("/companies/{corp_code}/manual", response_model=Company)
async def update_manual_company(corp_code: str, body: ManualCompanyCreate, user=Depends(get_current_user)):
    """Admin 전용: 비상장사 수기 입력 재무 데이터 전체 교체 UPSERT"""
    require_admin(user)
    supabase = get_supabase_client()

    # 비상장사 존재 확인
    try:
        existing = (
            supabase.table("companies")
            .select("corp_code, company_name")
            .eq("corp_code", corp_code)
            .eq("is_listed", False)
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "COMPANY_NOT_FOUND", "message": "비상장사를 찾을 수 없습니다.", "status_code": 404},
        )

    company_name = existing.data[0]["company_name"]

    # 전체 교체: 기존 PL 레코드 먼저 삭제 후 UPSERT (is_listed=False 비상장사만 해당)
    try:
        supabase.table("financial_statements").delete().eq("corp_code", corp_code).eq(
            "reprt_code", "11011"
        ).eq("fs_div", "OFS").execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "기존 재무 데이터 삭제에 실패했습니다.", "status_code": 503},
        )

    rows = []
    for entry in body.financials:
        for account_key, amount in [
            ("revenue", entry.revenue),
            ("operating_profit", entry.operating_profit),
            ("net_income", entry.net_income),
        ]:
            if amount is not None:
                rows.append({
                    "corp_code": corp_code,
                    "bsns_year": entry.bsns_year,
                    "reprt_code": "11011",
                    "fs_div": "OFS",
                    "account_key": account_key,
                    "account_nm": None,
                    "amount": amount,
                })

    if rows:
        try:
            supabase.table("financial_statements").upsert(
                rows,
                on_conflict="corp_code,bsns_year,reprt_code,fs_div,account_key",
            ).execute()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "DB_UNAVAILABLE", "message": "재무 데이터 저장에 실패했습니다.", "status_code": 503},
            )

    return Company(
        corp_code=corp_code,
        company_name=company_name,
        stock_code=None,
        is_listed=False,
    )
