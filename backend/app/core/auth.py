"""
JWT 검증 미들웨어 (Supabase SDK 방식)
완전 구현: Story 2.1 (Magic Link 인증 설정)
Story 2.3: require_admin() 헬퍼 추가
[Source: architecture.md - Authentication & Security]

사용법:
    async def endpoint(user = Depends(get_current_user)):
        ...

    # Admin 전용 엔드포인트
    async def admin_endpoint(user = Depends(get_current_user)):
        require_admin(user)
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_supabase_client

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """FastAPI Dependency: Supabase JWT 검증 후 사용자 반환.
    실패 시 HTTP 401 Unauthorized raise.
    """
    token = credentials.credentials
    supabase = get_supabase_client()
    try:
        user = supabase.auth.get_user(token)
    except Exception as e:
        # M2: 인프라 오류(네트워크/타임아웃)와 인증 실패를 구분
        err_str = str(e).lower()
        if any(kw in err_str for kw in ("invalid", "expired", "unauthorized", "jwt", "token")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user or not user.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user.user


def get_user_role(user_id: str) -> str:
    """user_profiles에서 역할 조회. 없으면 'builder' 반환. DB 오류 시 503 raise.
    Story 3.2: 분석 세트 소유권 체크에 사용.
    """
    supabase = get_supabase_client()
    try:
        res = supabase.table("user_profiles").select("role").eq("id", user_id).execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DB_UNAVAILABLE",
                "message": "권한 확인 중 오류가 발생했습니다.",
                "status_code": 503,
            },
        )
    return res.data[0]["role"] if res.data else "builder"


def require_admin(user) -> None:
    """현재 사용자가 admin이 아니면 403 INSUFFICIENT_PERMISSION raise.
    Story 2.3: Admin 전용 엔드포인트에서 사용.
    [Source: architecture.md - API & Communication Patterns - 에러 코드 목록]
    """
    supabase = get_supabase_client()
    # M3: DB 쿼리 예외 처리 추가
    try:
        res = supabase.table("user_profiles").select("role").eq("id", user.id).execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DB_UNAVAILABLE",
                "message": "권한 확인 중 오류가 발생했습니다.",
                "status_code": 503,
            },
        )
    role = res.data[0]["role"] if res.data else "builder"
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "INSUFFICIENT_PERMISSION",
                "message": "관리자 권한이 필요합니다.",
                "status_code": 403,
            },
        )
