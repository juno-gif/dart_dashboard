"""
사용자 프로필 및 팀원 관리 API
Story 2.2: GET /api/v1/users/me
Story 2.3: POST /api/v1/users/invite, PATCH /api/v1/users/{user_id}/role,
           POST /api/v1/users/{user_id}/deactivate, GET /api/v1/users
[Source: architecture.md - API & Communication Patterns]
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user, require_admin
from app.core.database import get_supabase_client
from app.models.schemas import InviteUserRequest, UpdateRoleRequest, UserProfile

router = APIRouter()


@router.get("/users/me", response_model=UserProfile)
async def get_my_profile(user=Depends(get_current_user)):
    """현재 로그인 사용자의 프로필 조회
    user_profiles에 없으면 builder 역할로 자동 생성 (첫 로그인)
    """
    supabase = get_supabase_client()
    user_id = user.id

    res = supabase.table("user_profiles").select("*").eq("id", user_id).execute()

    if res.data:
        return res.data[0]

    # 첫 로그인: builder 역할로 자동 생성 (H2: upsert로 동시 요청 경쟁 조건 방어)
    new_profile = {"id": user_id, "role": "builder", "display_name": None}
    supabase.table("user_profiles").upsert(new_profile).execute()
    return new_profile


@router.get("/users", response_model=List[UserProfile])
async def list_users(user=Depends(get_current_user)):
    """팀원 목록 조회 (Admin 전용)
    user_profiles 전체 조회
    """
    require_admin(user)
    supabase = get_supabase_client()
    res = supabase.table("user_profiles").select("*").execute()
    return res.data


@router.post("/users/invite", status_code=status.HTTP_201_CREATED)
async def invite_user(body: InviteUserRequest, user=Depends(get_current_user)):
    """팀원 초대 (Admin 전용)
    Supabase Auth inviteUserByEmail + user_profiles upsert
    """
    require_admin(user)
    supabase = get_supabase_client()

    try:
        result = supabase.auth.admin.invite_user_by_email(
            body.email,
            options={"data": {"role": body.role}},
        )
    except Exception as e:
        err_str = str(e).lower()
        if "already" in err_str or "exists" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "USER_ALREADY_EXISTS",
                    "message": "이미 초대되었거나 가입된 이메일입니다.",
                    "status_code": 409,
                },
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INVITE_FAILED",
                "message": "초대 이메일 발송에 실패했습니다.",
                "status_code": 500,
            },
        )

    invited_user_id = result.user.id
    try:
        supabase.table("user_profiles").upsert({
            "id": invited_user_id,
            "role": body.role,
            "display_name": None,
        }).execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PROFILE_UPSERT_FAILED",
                "message": "사용자 프로필 저장에 실패했습니다.",
                "status_code": 500,
            },
        )

    return {
        "message": "초대 이메일이 발송되었습니다.",
        "email": body.email,
        "role": body.role,
    }


@router.patch("/users/{user_id}/role", response_model=UserProfile)
async def update_user_role(
    user_id: str,
    body: UpdateRoleRequest,
    user=Depends(get_current_user),
):
    """팀원 역할 변경 (Admin 전용)
    user_profiles.role 업데이트 → RLS 즉시 반영
    """
    require_admin(user)
    supabase = get_supabase_client()

    res = supabase.table("user_profiles").update({"role": body.role}).eq("id", user_id).execute()

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "USER_NOT_FOUND",
                "message": "사용자를 찾을 수 없습니다.",
                "status_code": 404,
            },
        )
    return res.data[0]


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, user=Depends(get_current_user)):
    """팀원 계정 비활성화 (Admin 전용)
    banned_until 방식으로 기존 JWT 포함 모든 접근 차단
    """
    require_admin(user)

    if user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "CANNOT_DEACTIVATE_SELF",
                "message": "자기 자신의 계정은 비활성화할 수 없습니다.",
                "status_code": 400,
            },
        )

    supabase = get_supabase_client()

    try:
        supabase.auth.admin.update_user_by_id(
            user_id,
            {"banned_until": "2099-12-31T23:59:59Z"},
        )
    except Exception as e:
        err_str = str(e).lower()
        if "not found" in err_str or "does not exist" in err_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "USER_NOT_FOUND",
                    "message": "사용자를 찾을 수 없습니다.",
                    "status_code": 404,
                },
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DEACTIVATE_FAILED",
                "message": "계정 비활성화에 실패했습니다.",
                "status_code": 500,
            },
        )

    return {
        "message": "계정이 비활성화되었습니다.",
        "user_id": user_id,
    }
