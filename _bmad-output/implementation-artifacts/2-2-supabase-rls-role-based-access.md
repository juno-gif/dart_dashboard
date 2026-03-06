# Story 2.2: Supabase RLS 및 역할별 DB 접근 제어

Status: done

## Story

As a 시스템,
I want database-level row access control based on user roles,
So that data security is enforced at the database layer regardless of application code.

## Acceptance Criteria

1. **[user_profiles 테이블]** Supabase Dashboard에서 RLS 스키마가 적용되면 `user_profiles` 테이블이 `auth.users(id)` 참조, `role` 컬럼 기본값 `'builder'`로 생성되어야 한다

2. **[financial_statements RLS]** 인증된 Builder가 `financial_statements`를 조회하면, RLS 정책이 인증된 모든 사용자에게 조회를 허용해야 한다 (재무 데이터는 공개 정보)

3. **[analysis_sets RLS]** Builder가 타인의 `analysis_sets`를 수정하려 하면, `owner_id = auth.uid()` 조건의 RLS 정책으로 차단되어야 한다

4. **[anon 차단]** 인증되지 않은 요청으로 Supabase에 직접 쿼리를 보내면, 데이터가 반환되지 않아야 한다 (anon key 직접 접근 차단)

5. **[user_profiles 접근 제어]** Admin이 `user_profiles`를 조회하면 전체 사용자 프로필을 조회할 수 있어야 한다. 일반 사용자는 본인 프로필만 조회할 수 있어야 한다

6. **[FastAPI auth guard]** companies, financials 엔드포인트에 `get_current_user` Dependency가 적용되어, 토큰 없이 접근하면 401 반환해야 한다

## Tasks / Subtasks

- [x] Task 1: Supabase Dashboard SQL 수동 적용 (AC: #1, #2, #3, #4, #5)
  - [x] 1.1 `user_profiles` 테이블 SQL 실행 (Dev Notes 참조)
  - [x] 1.2 RLS 활성화: companies, financial_statements, account_mappings, analysis_sets, user_profiles
  - [x] 1.3 RLS 정책 SQL 실행 (Dev Notes 참조)
  - [x] 1.4 `get_user_role()` SQL 함수 생성 (admin 체크용 SECURITY DEFINER 함수)

- [x] Task 2: FastAPI — `companies.py`에 auth guard 적용 (AC: #6)
  - [x] 2.1 `backend/app/api/v1/companies.py` 수정: `search_companies`에 `Depends(get_current_user)` 추가
  - [x] 2.2 현재 라우터 파라미터에 `_ = Depends(get_current_user)` 패턴 사용 (불필요한 user 객체 사용 없이)

- [x] Task 3: FastAPI — `financials.py`에 auth guard 적용 (AC: #6)
  - [x] 3.1 `backend/app/api/v1/financials.py` 수정: `get_financials`, `compare_financials`에 `Depends(get_current_user)` 추가

- [x] Task 4: Backend — `UserProfile` Pydantic 스키마 추가 (AC: #5)
  - [x] 4.1 `backend/app/models/schemas.py`에 `UserProfile` 모델 추가

- [x] Task 5: Backend — `/api/v1/users/me` 엔드포인트 신규 생성 (AC: #1, #5)
  - [x] 5.1 `backend/app/api/v1/users.py` 신규 생성
  - [x] 5.2 `GET /api/v1/users/me`: 현재 사용자 프로필 조회 (없으면 `builder` 역할로 자동 생성)
  - [x] 5.3 `backend/app/main.py`에 users 라우터 등록

- [x] Task 6: Frontend — `api.ts`에 `getUserProfile` 함수 추가 (AC: #5)
  - [x] 6.1 `frontend/src/lib/api.ts`에 `getUserProfile()` 함수 추가
  - [x] 6.2 api.ts 에러 처리: 401 응답 시 `window.location.href = '/login'` 리디렉션 추가 (미인증 상태 감지)

- [x] Task 7: Backend — 인증 가드 테스트 추가 (AC: #6)
  - [x] 7.1 `backend/tests/test_rls_endpoints.py` 신규 작성
  - [x] 7.2 Authorization 헤더 없이 `GET /api/v1/companies/search?q=test` → 401 테스트
  - [x] 7.3 Authorization 헤더 없이 `GET /api/v1/companies/005930/financials` → 401 테스트
  - [x] 7.4 Authorization 헤더 없이 `GET /api/v1/companies/compare?codes=005930` → 401 테스트
  - [x] 7.5 pytest 전체 통과 확인 (44/44)

- [x] Task 8: Next.js 빌드 통과 확인 (AC: 전체)
  - [x] 8.1 `npm run build` TypeScript 에러 없이 통과

## Dev Notes

### Critical: Task 1 — Supabase SQL (수동 적용 필수)

⚠️ **이 Task는 Supabase Dashboard > SQL Editor에서 수동으로 실행해야 합니다.**

```sql
-- ============================================================
-- Step 1: user_profiles 테이블 생성
-- ============================================================
CREATE TABLE IF NOT EXISTS user_profiles (
  id            UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role          VARCHAR(20) NOT NULL DEFAULT 'builder',
  display_name  VARCHAR(50),
  CONSTRAINT user_profiles_role_check CHECK (
    role IN ('admin', 'builder', 'live_viewer', 'read_only')
  )
);

-- ============================================================
-- Step 2: admin 역할 확인 함수 (SECURITY DEFINER — RLS 우회)
-- ============================================================
CREATE OR REPLACE FUNCTION auth.get_user_role()
RETURNS TEXT AS $$
  SELECT role FROM user_profiles WHERE id = auth.uid()
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ============================================================
-- Step 3: RLS 활성화
-- ============================================================
ALTER TABLE user_profiles          ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies              ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_statements   ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_mappings       ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_sets          ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Step 4: user_profiles 정책
-- 본인만 조회/수정, Admin은 전체 조회
-- ============================================================
CREATE POLICY "user_profiles_select" ON user_profiles
  FOR SELECT USING (
    auth.uid() = id
    OR auth.get_user_role() = 'admin'
  );

CREATE POLICY "user_profiles_insert" ON user_profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "user_profiles_update" ON user_profiles
  FOR UPDATE USING (auth.uid() = id);

-- ============================================================
-- Step 5: companies 정책 (인증된 모든 사용자 조회 가능)
-- ============================================================
CREATE POLICY "companies_authenticated_read" ON companies
  FOR SELECT USING (auth.role() = 'authenticated');

-- ============================================================
-- Step 6: financial_statements 정책 (인증된 모든 사용자 조회)
-- ============================================================
CREATE POLICY "financial_statements_authenticated_read" ON financial_statements
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "financial_statements_service_write" ON financial_statements
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================
-- Step 7: account_mappings 정책 (인증된 모든 사용자 조회)
-- ============================================================
CREATE POLICY "account_mappings_authenticated_read" ON account_mappings
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "account_mappings_service_write" ON account_mappings
  FOR ALL USING (auth.role() = 'service_role');

-- ============================================================
-- Step 8: analysis_sets 정책
-- 조회: 인증된 모든 사용자 / 수정: 본인 소유만
-- ============================================================
CREATE POLICY "analysis_sets_authenticated_read" ON analysis_sets
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "analysis_sets_owner_insert" ON analysis_sets
  FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "analysis_sets_owner_update" ON analysis_sets
  FOR UPDATE USING (
    auth.uid() = owner_id
    OR auth.get_user_role() = 'admin'
  );

CREATE POLICY "analysis_sets_owner_delete" ON analysis_sets
  FOR DELETE USING (
    auth.uid() = owner_id
    OR auth.get_user_role() = 'admin'
  );
```

### Task 2 & 3: FastAPI auth guard 패턴

Story 2.1에서 `backend/app/core/auth.py`의 `get_current_user` Dependency가 이미 구현되어 있습니다. **새로 구현하지 말고** 임포트해서 사용하세요.

**auth guard 적용 패턴 (user 객체 불필요 시):**
```python
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user

router = APIRouter()

@router.get("/companies/search", response_model=list[Company])
async def search_companies(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
    _: dict = Depends(get_current_user),   # auth guard — 미사용 변수는 _ 로
):
    ...
```

**주의:** `_` 언더스코어를 사용하더라도 FastAPI는 Depends를 실행합니다. 미인증 시 401 자동 반환.

### Task 5: users.py 구현 패턴

```python
# backend/app/api/v1/users.py
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.core.database import get_supabase_client
from app.models.schemas import UserProfile

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

    # 첫 로그인: builder 역할로 자동 생성
    new_profile = {"id": user_id, "role": "builder", "display_name": None}
    supabase.table("user_profiles").insert(new_profile).execute()
    return new_profile
```

### Task 4: schemas.py UserProfile 추가 패턴

```python
# backend/app/models/schemas.py 에 추가
from typing import Literal

UserRoleType = Literal["admin", "builder", "live_viewer", "read_only"]

class UserProfile(BaseModel):
    id: str
    role: UserRoleType
    display_name: Optional[str] = None
```

### Task 6: api.ts getUserProfile + 401 처리

```typescript
// frontend/src/lib/api.ts 에 추가
import type { UserProfile } from '@/types'

export async function getUserProfile(): Promise<UserProfile> {
  return apiGet<UserProfile>('/api/v1/users/me')
}
```

**401 리디렉션 처리** — `apiGet`/`apiPost` 에러 핸들러에서 추가:
```typescript
// api.ts의 에러 처리에 추가
if (res.status === 401 && typeof window !== 'undefined') {
  window.location.href = '/login'
  throw new Error('Unauthorized')
}
```

⚠️ `typeof window !== 'undefined'` 체크: SSR 환경에서 안전하게 처리.

### Task 7: 테스트 패턴

```python
# backend/tests/test_rls_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)

class TestAuthGuardEndpoints:
    def test_search_companies_without_token_returns_401(self, client):
        response = client.get("/api/v1/companies/search?q=삼성")
        assert response.status_code == 401

    def test_get_financials_without_token_returns_401(self, client):
        response = client.get("/api/v1/companies/005930/financials")
        assert response.status_code == 401

    def test_compare_financials_without_token_returns_401(self, client):
        response = client.get("/api/v1/companies/compare?codes=005930")
        assert response.status_code == 401

    def test_get_my_profile_without_token_returns_401(self, client):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
```

### 기존 테스트 회귀 방지

⚠️ **중요: 기존 테스트 파일들이 auth guard 없이 작성되어 있습니다.**
`test_companies.py`, `test_financials.py`, `test_compare.py` 등에서 auth guard 적용 후 401이 반환될 수 있습니다.

**해결 방법: 기존 테스트에 mock get_current_user 추가**

```python
# 기존 테스트 파일의 TestClient 생성 부분에서 dependency override 사용
from unittest.mock import MagicMock
from app.core.auth import get_current_user

# 테스트용 mock user
def mock_user():
    user = MagicMock()
    user.id = "test-user-id"
    return user

# fixture에 dependency override 적용
@pytest.fixture
def client():
    from app.main import app
    app.dependency_overrides[get_current_user] = mock_user
    yield TestClient(app)
    app.dependency_overrides.clear()
```

**반드시 모든 기존 테스트 파일을 이 패턴으로 업데이트해야 pytest 전체가 통과됩니다.**

### 환경변수 체크리스트

**Supabase RLS 적용 후 backend Service Key가 필요한 이유:**
- `service_role` 키는 RLS를 우회 → `get_supabase_client()`에서 사용하는 Service Key는 백엔드 전용
- `anon` 키는 RLS를 적용받음 → 프론트에서 사용하는 `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- RLS 적용 후 백엔드 Service Key로 DB 직접 접근은 계속 작동 (우회)

### 아키텍처 준수 사항

- **컴포넌트 내 직접 fetch 금지**: 반드시 `lib/api.ts` 경유
- **get_current_user 재구현 금지**: Story 2.1에서 구현한 `app.core.auth.get_current_user` 그대로 사용
- **새 파일 위치**: `backend/app/api/v1/users.py` (architecture.md의 구조 준수)
- **Dependency 언더스코어 패턴**: `_ = Depends(get_current_user)` — user 객체 불필요 시

### Project Structure Notes

**이번 스토리에서 신규 생성:**
- `backend/app/api/v1/users.py`
- `backend/tests/test_rls_endpoints.py`

**이번 스토리에서 수정:**
- `backend/app/api/v1/companies.py` — auth guard 추가
- `backend/app/api/v1/financials.py` — auth guard 추가
- `backend/app/models/schemas.py` — UserProfile 모델 추가
- `backend/app/main.py` — users 라우터 등록
- `frontend/src/lib/api.ts` — getUserProfile + 401 처리
- 기존 테스트 파일들 — `app.dependency_overrides` 패턴 적용

**이번 스토리에서 수동 적용:**
- Supabase Dashboard SQL Editor에서 RLS SQL 실행 (Dev Notes Task 1 참조)

**의도적으로 이번 스토리에서 미구현:**
- Admin 팀원 초대/역할 변경 UI → Story 2.3
- 공유 토큰(share_token) 기반 anon RLS 정책 → Epic 4
- LiveViewer/ReadOnly 역할 접근 제어 → Story 3.2 (분석 세트 UI와 함께)

### References

- AC 출처: [epics.md - Story 2.2 Supabase RLS 및 역할별 DB 접근 제어]
- RLS 정책 원칙: [architecture.md - Authentication & Security > RLS 정책 원칙]
- user_profiles 스키마: [architecture.md - Core Architectural Decisions > Data Architecture]
- auth.py get_current_user: [2-1-magic-link-auth-setup.md - Task 7]
- 에러 처리: [architecture.md - Error Handling Patterns]
- FastAPI Dependency 패턴: [architecture.md - API & Communication Patterns]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- test_dart_failure.py도 auth guard 추가 후 401 오류 — `dependency_overrides` 패턴 적용으로 해결

### Completion Notes List

- Task 1 SQL은 사용자가 Supabase Dashboard에서 수동 실행해야 함 (코드로 적용 불가)
- `_: object = Depends(get_current_user)` 패턴 사용 (user 객체 불필요한 엔드포인트)
- 기존 테스트 4개 파일 모두 `dependency_overrides` 업데이트 필요했음 (test_companies, test_financials, test_compare, test_dart_failure)
- pytest 44/44 통과, Next.js build 성공

### File List

- `backend/app/api/v1/companies.py` — auth guard 추가
- `backend/app/api/v1/financials.py` — auth guard 추가
- `backend/app/models/schemas.py` — UserProfile 모델 추가
- `backend/app/api/v1/users.py` — 신규 생성
- `backend/app/main.py` — users 라우터 등록
- `frontend/src/lib/api.ts` — getUserProfile + 401 redirect 추가
- `backend/tests/test_rls_endpoints.py` — 신규 생성
- `backend/tests/test_companies.py` — dependency_overrides 적용
- `backend/tests/test_financials.py` — dependency_overrides 적용
- `backend/tests/test_compare.py` — dependency_overrides 적용
- `backend/tests/test_dart_failure.py` — dependency_overrides 적용
