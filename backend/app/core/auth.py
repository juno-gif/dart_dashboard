"""
인증 비활성화 — 전체 공개 접근으로 전환.
get_current_user는 익명 사용자를 반환합니다.
"""

from fastapi import Request


async def get_current_user(request: Request) -> dict:
    """인증 없이 익명 사용자를 반환합니다."""
    return {"id": "anonymous", "role": "builder"}


def get_user_role(user_id: str) -> str:
    return "builder"


def require_admin(user) -> None:
    pass
