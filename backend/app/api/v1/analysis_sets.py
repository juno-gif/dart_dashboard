"""
분석 세트 API — 전체 공개 (인증 없음, 전역 공유)
POST   /api/v1/analysis-sets               : 분석 세트 저장
GET    /api/v1/analysis-sets               : 전체 세트 목록 조회
GET    /api/v1/analysis-sets/{set_id}      : 단일 세트 조회
PATCH  /api/v1/analysis-sets/{set_id}      : 분석 세트 수정
DELETE /api/v1/analysis-sets/{set_id}      : 분석 세트 삭제
POST   /api/v1/analysis-sets/{set_id}/share : 공유 링크 생성
POST   /api/v1/analysis-sets/{set_id}/export/ppt : PPT 내보내기
POST   /api/v1/analysis-sets/{set_id}/ai-summary : AI 재무 요약
"""
import io
import logging
import secrets
from datetime import date
from urllib.parse import quote

from typing import Optional

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_supabase_client
from app.models.schemas import AnalysisSet, AnalysisSetCreate, AnalysisSetUpdate, ShareResponse
from app.services.ai_service import LLMAIError, answer_financial_question, generate_financial_summary
from app.services.financial_service import get_pl_data
from app.services.ppt_service import generate_analysis_ppt


class AiSummaryRequest(BaseModel):
    question: Optional[str] = Field(default=None, max_length=2000)


class AiSummaryResponse(BaseModel):
    type: str  # "summary" or "answer"
    content: str


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analysis-sets", status_code=status.HTTP_201_CREATED, response_model=AnalysisSet)
async def create_analysis_set(body: AnalysisSetCreate):
    """분석 세트 저장 (중복 이름 체크)"""
    supabase = get_supabase_client()

    try:
        dup = (
            supabase.table("analysis_sets")
            .select("id")
            .eq("name", body.name)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if dup.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "NAME_ALREADY_EXISTS",
                "message": "이미 사용 중인 이름입니다. 다른 이름을 입력하세요.",
                "status_code": 409,
            },
        )

    try:
        res = (
            supabase.table("analysis_sets")
            .insert({
                "name": body.name,
                "owner_id": None,
                "company_codes": body.company_codes,
            })
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    return res.data[0]


@router.get("/analysis-sets", response_model=list[AnalysisSet])
async def list_analysis_sets():
    """전체 분석 세트 목록 조회"""
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("analysis_sets")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )
    return res.data


@router.get("/analysis-sets/{set_id}", response_model=AnalysisSet)
async def get_analysis_set(set_id: str):
    """단일 분석 세트 조회"""
    supabase = get_supabase_client()
    try:
        res = (
            supabase.table("analysis_sets")
            .select("*")
            .eq("id", set_id)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ANALYSIS_SET_NOT_FOUND",
                "message": "분석 세트를 찾을 수 없습니다.",
                "status_code": 404,
            },
        )
    return res.data[0]


@router.patch("/analysis-sets/{set_id}", response_model=AnalysisSet)
async def update_analysis_set(set_id: str, body: AnalysisSetUpdate):
    """분석 세트 수정"""
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("analysis_sets")
            .select("*")
            .eq("id", set_id)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "ANALYSIS_SET_NOT_FOUND", "message": "분석 세트를 찾을 수 없습니다.", "status_code": 404},
        )

    existing = res.data[0]

    # name 변경 시 중복 체크
    if body.name is not None and body.name != existing["name"]:
        try:
            dup = (
                supabase.table("analysis_sets")
                .select("id")
                .eq("name", body.name)
                .execute()
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
            )
        if dup.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "NAME_ALREADY_EXISTS",
                    "message": "이미 사용 중인 이름입니다. 다른 이름을 입력하세요.",
                    "status_code": 409,
                },
            )

    update_data = {}
    if body.name is not None:
        update_data["name"] = body.name
    if body.company_codes is not None:
        update_data["company_codes"] = body.company_codes

    if not update_data:
        return existing

    try:
        updated = (
            supabase.table("analysis_sets")
            .update(update_data)
            .eq("id", set_id)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )
    return updated.data[0]


@router.delete("/analysis-sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_set(set_id: str):
    """분석 세트 삭제"""
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("analysis_sets")
            .select("id")
            .eq("id", set_id)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "ANALYSIS_SET_NOT_FOUND", "message": "분석 세트를 찾을 수 없습니다.", "status_code": 404},
        )

    try:
        supabase.table("analysis_sets").delete().eq("id", set_id).execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/analysis-sets/{set_id}/share", response_model=ShareResponse)
async def share_analysis_set(set_id: str):
    """공유 링크 생성 (멱등성: 기존 토큰 재사용, 없으면 신규 생성)"""
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("analysis_sets")
            .select("*")
            .eq("id", set_id)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ANALYSIS_SET_NOT_FOUND",
                "message": "분석 세트를 찾을 수 없습니다.",
                "status_code": 404,
            },
        )

    existing = res.data[0]
    token = existing.get("share_token")
    if not token:
        token = secrets.token_urlsafe(32)
        try:
            supabase.table("analysis_sets").update({"share_token": token}).eq("id", set_id).execute()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
            )

    share_url = f"{settings.FRONTEND_URL}/shared/{token}"
    return ShareResponse(share_token=token, share_url=share_url)


@router.post("/analysis-sets/{set_id}/export/ppt")
async def export_analysis_set_ppt(set_id: str):
    """분석 세트 PPT 내보내기"""
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("analysis_sets")
            .select("*")
            .eq("id", set_id)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "ANALYSIS_SET_NOT_FOUND", "message": "분석 세트를 찾을 수 없습니다.", "status_code": 404},
        )

    existing = res.data[0]

    financials_by_corp: dict = {}
    for corp_code in existing["company_codes"]:
        try:
            financials_by_corp[corp_code] = get_pl_data(corp_code, years=5)
        except Exception:
            financials_by_corp[corp_code] = []

    pptx_bytes = generate_analysis_ppt(
        set_name=existing["name"],
        company_codes=existing["company_codes"],
        financials_by_corp=financials_by_corp,
    )

    filename = f"{existing['name']}_{date.today().isoformat()}.pptx"
    encoded_filename = quote(filename.encode("utf-8"), safe="")
    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.post("/analysis-sets/{set_id}/ai-summary", response_model=AiSummaryResponse)
async def ai_summary_analysis_set(set_id: str, body: AiSummaryRequest):
    """AI 재무 요약 및 자연어 질의 응답"""
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("analysis_sets")
            .select("*")
            .eq("id", set_id)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "ANALYSIS_SET_NOT_FOUND", "message": "분석 세트를 찾을 수 없습니다.", "status_code": 404},
        )

    existing = res.data[0]

    financials_by_corp: dict = {}
    for corp_code in existing["company_codes"]:
        try:
            financials_by_corp[corp_code] = get_pl_data(corp_code, years=5)
        except Exception:
            financials_by_corp[corp_code] = []

    try:
        if body.question:
            content = answer_financial_question(
                question=body.question,
                set_name=existing["name"],
                company_codes=existing["company_codes"],
                financials_by_corp=financials_by_corp,
            )
            response_type = "answer"
        else:
            content = generate_financial_summary(
                set_name=existing["name"],
                company_codes=existing["company_codes"],
                financials_by_corp=financials_by_corp,
            )
            response_type = "summary"
    except LLMAIError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "LLM_API_UNAVAILABLE",
                "message": "AI 요약을 불러올 수 없습니다. 잠시 후 재시도해 주세요.",
                "status_code": 503,
            },
        )

    return AiSummaryResponse(type=response_type, content=content)
