"""
Pydantic 요청/응답 스키마
점진적으로 각 스토리에서 확장됩니다
[Source: architecture.md - API & Communication Patterns]
"""
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


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


# ── Story 2.2: 사용자 프로필 ────────────────────────────
UserRoleType = Literal["admin", "builder", "live_viewer", "read_only"]


class UserProfile(BaseModel):
    id: str
    role: UserRoleType
    display_name: Optional[str] = None


# ── Story 2.3: 팀원 초대 및 역할 관리 ───────────────────
# admin은 초대 불가 (admin은 수동 DB 설정)
InviteRoleType = Literal["builder", "live_viewer", "read_only"]


class InviteUserRequest(BaseModel):
    email: EmailStr
    role: InviteRoleType


class UpdateRoleRequest(BaseModel):
    role: UserRoleType


# ── Story 3.1: 분석 세트 저장 및 불러오기 ───────────────
# ── 분석 그룹 ────────────────────────────────────────────
class AnalysisGroup(BaseModel):
    id: str
    name: str
    display_order: int = 0
    created_at: str
    updated_at: Optional[str] = None


class AnalysisGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class AnalysisGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_order: Optional[int] = None


class AnalysisSetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    company_codes: list[str] = Field(..., min_length=1)
    group_id: Optional[str] = None


# ── Story 3.2: 분석 세트 수정 ───────────────────────────
class AnalysisSetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    company_codes: Optional[list[str]] = Field(None, min_length=1)
    group_id: Optional[str] = None  # None = 그룹 없음으로 변경, 미포함 시 유지


class AnalysisSet(BaseModel):
    id: str
    name: str
    owner_id: Optional[str] = None
    company_codes: list[str]
    share_token: Optional[str] = None
    group_id: Optional[str] = None
    created_at: str
    updated_at: str


# ── Story 4.1: 공유 링크 생성 ────────────────────────────
class ShareResponse(BaseModel):
    share_token: str
    share_url: str


# ── Story 4.2: 공유 링크 뷰어 ────────────────────────────
class SharedAnalysisSetResponse(BaseModel):
    id: str
    name: str
    company_codes: list[str]
    financials: list[FinancialStatement]


# ── Story 5.1: 비상장사 수기 입력 ────────────────────────
class ManualFinancialEntry(BaseModel):
    bsns_year: str = Field(..., pattern=r'^\d{4}$')
    revenue: Optional[float] = None
    operating_profit: Optional[float] = None
    net_income: Optional[float] = None


class ManualCompanyCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=100)
    financials: list[ManualFinancialEntry] = Field(..., min_length=1, max_length=5)


# ── Story 5.2: 비상장사 재무 데이터 조회 응답 ─────────────
class ManualCompanyFinancialsResponse(BaseModel):
    corp_code: str
    company_name: str
    financials: list[ManualFinancialEntry]
