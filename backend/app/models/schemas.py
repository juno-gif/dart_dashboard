"""
Pydantic 요청/응답 스키마
점진적으로 각 스토리에서 확장됩니다
[Source: architecture.md - API & Communication Patterns]
"""
from pydantic import BaseModel


# ── 표준 에러 응답 ──────────────────────────────────────
class ApiError(BaseModel):
    error: str
    message: str
    status_code: int
    cached_at: str | None = None
