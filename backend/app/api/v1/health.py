"""
헬스체크 엔드포인트
Render Free 인스턴스 슬립 방지용 + 배포 상태 확인
Supabase pg_cron이 매일 06:58 KST에 호출
[Source: architecture.md - 슬립 방지 (Render Free)]
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check() -> dict:
    """
    서비스 헬스체크

    Returns:
        {"status": "ok"} — 200 OK
    """
    return {"status": "ok"}
