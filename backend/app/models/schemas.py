"""
Pydantic 요청/응답 스키마
점진적으로 각 스토리에서 확장됩니다
[Source: architecture.md - API & Communication Patterns]
"""
from typing import Optional

from pydantic import BaseModel


# ── 표준 에러 응답 ──────────────────────────────────────
class ApiError(BaseModel):
    error: str
    message: str
    status_code: int
    cached_at: Optional[str] = None


# ── Story 1.2: 기업 / 재무 / 계정과목 ──────────────────
class Company(BaseModel):
    corp_code: str
    company_name: str
    stock_code: Optional[str] = None
    is_listed: bool = True


class FinancialStatement(BaseModel):
    corp_code: str
    bsns_year: str
    reprt_code: str
    fs_div: str
    account_key: str
    account_nm: Optional[str] = None
    amount: Optional[int] = None


class AccountMapping(BaseModel):
    account_nm: str
    account_key: str
    display_name: Optional[str] = None
    category: Optional[str] = None


class SyncResult(BaseModel):
    corp_code: str
    synced_rows: int
