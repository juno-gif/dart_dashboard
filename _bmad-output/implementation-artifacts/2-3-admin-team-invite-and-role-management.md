# Story 2.3: Admin 팀원 초대 및 역할 관리

Status: done

## Story

As an Admin,
I want to invite team members by email and assign their roles,
So that each team member can access the dashboard with the right permissions via a single email click.

## Acceptance Criteria

1. **[초대 이메일 발송]** Admin이 이메일과 역할(builder/live_viewer/read_only)을 입력하고 초대를 제출하면, Supabase Auth `inviteUserByEmail` API로 Magic Link 초대 이메일이 발송되고, `user_profiles`에 지정된 역할이 미리 저장(upsert)되어야 한다. 초대받은 팀원이 Magic Link를 클릭하면 비밀번호 설정 없이 즉시 대시보드에 접근할 수 있어야 한다.

2. **[역할 변경]** Admin이 팀원의 역할을 변경하면, `user_profiles.role`이 즉시 업데이트되고, 변경된 역할이 RLS 정책에 즉시 반영되어야 한다.

3. **[Builder 초대 시도 차단]** Builder가 팀원 초대를 시도하면(POST /api/v1/users/invite), `INSUFFICIENT_PERMISSION` 에러 코드와 403 응답이 반환되어야 한다.

4. **[계정 비활성화]** Admin이 팀원 계정을 비활성화하면, Supabase Admin API로 해당 사용자의 `banned_until`을 `'2099-12-31T23:59:59Z'`으로 설정해 이후 Magic Link 요청과 기존 JWT 토큰 모두 API 접근이 차단되어야 한다.

## Tasks / Subtasks

- [x] Task 1: Backend — `POST /api/v1/users/invite` 엔드포인트 신규 생성 (AC: #1, #3)
  - [x] 1.1 `backend/app/api/v1/users.py`에 `invite_user` 핸들러 추가
  - [x] 1.2 Admin 권한 체크: `user.role != 'admin'`이면 403 INSUFFICIENT_PERMISSION 반환
  - [x] 1.3 Supabase Admin API (`supabase.auth.admin.invite_user_by_email`) 호출로 초대 이메일 발송
  - [x] 1.4 `user_profiles` 테이블에 `{id: invited_user_id, role: role, display_name: None}` upsert
  - [x] 1.5 요청 스키마: `InviteUserRequest(email: str, role: InviteRoleType)` — `backend/app/models/schemas.py`에 추가
  - [x] 1.6 응답: 201 + `{"message": "초대 이메일이 발송되었습니다.", "email": email, "role": role}`

- [x] Task 2: Backend — `PATCH /api/v1/users/{user_id}/role` 엔드포인트 신규 생성 (AC: #2)
  - [x] 2.1 `backend/app/api/v1/users.py`에 `update_user_role` 핸들러 추가
  - [x] 2.2 Admin 권한 체크: `user.role != 'admin'`이면 403 반환
  - [x] 2.3 `user_profiles` 테이블에서 `{id: user_id}` 행의 `role`을 업데이트
  - [x] 2.4 요청 스키마: `UpdateRoleRequest(role: UserRoleType)` — `backend/app/models/schemas.py`에 추가
  - [x] 2.5 응답: 200 + 업데이트된 `UserProfile`

- [x] Task 3: Backend — `POST /api/v1/users/{user_id}/deactivate` 엔드포인트 신규 생성 (AC: #4)
  - [x] 3.1 `backend/app/api/v1/users.py`에 `deactivate_user` 핸들러 추가
  - [x] 3.2 Admin 권한 체크: `user.role != 'admin'`이면 403 반환
  - [x] 3.3 Supabase Admin API (`supabase.auth.admin.update_user_by_id`) 호출: `banned_until='2099-12-31T23:59:59Z'` 설정
  - [x] 3.4 응답: 200 + `{"message": "계정이 비활성화되었습니다.", "user_id": user_id}`

- [x] Task 4: Backend — Admin 권한 체크 헬퍼 함수 추가 (AC: #1, #2, #3, #4)
  - [x] 4.1 `backend/app/core/auth.py`에 `require_admin(user)` 헬퍼 추가
  - [x] 4.2 users.py의 모든 Admin 전용 핸들러에서 이 헬퍼 호출

- [x] Task 5: Backend — `GET /api/v1/users` (팀원 목록 조회) 엔드포인트 추가 (Admin 전용)
  - [x] 5.1 `backend/app/api/v1/users.py`에 `list_users` 핸들러 추가
  - [x] 5.2 Admin 권한 체크 후 `user_profiles` 전체 조회 반환
  - [x] 5.3 응답: `List[UserProfile]`

- [x] Task 6: Frontend — 팀원 초대 UI 컴포넌트 (AC: #1, #3)
  - [x] 6.1 `frontend/src/components/layout/InviteTeamDialog.tsx` 신규 생성
  - [x] 6.2 `frontend/src/lib/api.ts`에 `inviteUser(email, role)` 함수 추가
  - [x] 6.3 `frontend/src/lib/api.ts`에 `updateUserRole(userId, role)` 함수 추가
  - [x] 6.4 `frontend/src/lib/api.ts`에 `deactivateUser(userId)` 함수 추가
  - [x] 6.5 `frontend/src/lib/api.ts`에 `listUsers()` 함수 추가

- [x] Task 7: Frontend — 팀원 관리 페이지 (AC: #1, #2, #4)
  - [x] 7.1 `frontend/src/app/(auth)/dashboard/team/page.tsx` 신규 생성
  - [x] 7.2 `frontend/src/hooks/use-team-management.ts` 신규 생성
  - [x] 7.3 `frontend/src/app/(auth)/layout.tsx`에 Admin 전용 팀 관리 네비게이션 추가 (AppSidebar 미존재로 layout에 추가)

- [x] Task 8: Backend 테스트 작성 (AC: #1, #2, #3, #4)
  - [x] 8.1 `backend/tests/test_user_management.py` 신규 생성 (7개 테스트)
  - [x] 8.2 기존 `test_rls_endpoints.py`에 4개 신규 엔드포인트 401 테스트 추가

- [x] Task 9: Next.js 빌드 확인
  - [x] `cd frontend && npm run build` 실행 — 에러 없음 확인 (57 pytest passed, build success)

## Dev Notes

### Admin 권한 확인 패턴

Story 2.2에서 `user_profiles` 테이블과 RLS 정책이 설정됨. Admin 체크는 FastAPI 레이어에서 수행:

```python
# backend/app/core/auth.py 에 추가할 헬퍼
from fastapi import HTTPException, status
from app.core.database import get_supabase_client

def require_admin(user) -> None:
    """현재 사용자가 admin이 아니면 403 raise"""
    supabase = get_supabase_client()
    res = supabase.table("user_profiles").select("role").eq("id", user.id).execute()
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
```

### Supabase Admin API 사용법

`SUPABASE_SERVICE_KEY`로 초기화된 클라이언트만 Admin API 사용 가능. `get_supabase_client()`는 이미 service key를 사용하므로 그대로 사용:

```python
# 초대 이메일 발송
result = supabase.auth.admin.invite_user_by_email(
    email,
    options={"data": {"role": role}}  # user_metadata에 역할 힌트 저장
)
invited_user_id = result.user.id

# user_profiles에 역할 미리 저장 (upsert)
supabase.table("user_profiles").upsert({
    "id": invited_user_id,
    "role": role,
    "display_name": None
}).execute()
```

```python
# 계정 비활성화 (banned_until 방식)
supabase.auth.admin.update_user_by_id(
    user_id,
    {"banned_until": "2099-12-31T23:59:59Z"}
)
```

**중요:** `inviteUserByEmail`은 동일 이메일로 재초대 시 기존 초대를 갱신. 이미 가입된 이메일은 오류 발생 가능 — 오류 발생 시 `{"error": "USER_ALREADY_EXISTS", "status_code": 409}` 반환 처리 필요.

### 에러 코드 표준 (architecture.md)

```json
{
  "error": "INSUFFICIENT_PERMISSION",
  "message": "관리자 권한이 필요합니다.",
  "status_code": 403
}
```

`INSUFFICIENT_PERMISSION`은 architecture.md에 이미 정의된 에러 코드.

### 새 Pydantic 스키마 (`backend/app/models/schemas.py`)

```python
class InviteUserRequest(BaseModel):
    email: str
    role: InviteRoleType  # "builder" | "live_viewer" | "read_only" (admin 초대는 불가)

class UpdateRoleRequest(BaseModel):
    role: UserRoleType
```

`UserRoleType`과 `UserProfile`은 Story 2.2에서 이미 정의됨.

### 테스트 패턴 (Story 2.2 기준)

Admin/일반 사용자 구분을 위한 mock 패턴:

```python
def _mock_admin():
    user = MagicMock()
    user.id = "admin-user-id"
    return user

def _mock_builder():
    user = MagicMock()
    user.id = "builder-user-id"
    return user

@pytest.fixture
def admin_client():
    from app.core.auth import get_current_user
    from app.main import app
    app.dependency_overrides[get_current_user] = _mock_admin
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def builder_client():
    from app.core.auth import get_current_user
    from app.main import app
    app.dependency_overrides[get_current_user] = _mock_builder
    yield TestClient(app)
    app.dependency_overrides.clear()
```

Supabase Admin API 호출 mock:

```python
# require_admin 체크용 user_profiles mock
mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
    {"role": "admin"}
]

# invite_user_by_email mock
mock_invited_user = MagicMock()
mock_invited_user.user.id = "new-user-id"
mock_supabase.auth.admin.invite_user_by_email.return_value = mock_invited_user
```

### Frontend API 함수 (`frontend/src/lib/api.ts`)

```typescript
export interface InviteUserRequest {
  email: string
  role: 'builder' | 'live_viewer' | 'read_only'
}

export async function inviteUser(data: InviteUserRequest): Promise<void> {
  return apiPost('/api/v1/users/invite', data)
}

export async function updateUserRole(userId: string, role: string): Promise<UserProfile> {
  return apiPatch<UserProfile>(`/api/v1/users/${userId}/role`, { role })
}

export async function deactivateUser(userId: string): Promise<void> {
  return apiPost(`/api/v1/users/${userId}/deactivate`, {})
}

export async function listUsers(): Promise<UserProfile[]> {
  return apiGet<UserProfile[]>('/api/v1/users')
}
```

### Project Structure Notes

- 신규 파일: `backend/tests/test_user_management.py`
- 신규 파일: `frontend/src/components/layout/InviteTeamDialog.tsx`
- 신규 파일: `frontend/src/app/(auth)/dashboard/team/page.tsx`
- 신규 파일: `frontend/src/hooks/use-team-management.ts`
- 수정 파일: `backend/app/api/v1/users.py` (엔드포인트 4개 추가: list, invite, update_role, deactivate)
- 수정 파일: `backend/app/core/auth.py` (`require_admin` 헬퍼 추가)
- 수정 파일: `backend/app/models/schemas.py` (`InviteUserRequest`, `UpdateRoleRequest`, `InviteRoleType` 추가)
- 수정 파일: `frontend/src/lib/api.ts` (`apiPatch` + 4개 함수 추가)
- 수정 파일: `frontend/src/app/(auth)/layout.tsx` (Admin 전용 팀 관리 네비게이션 추가)
- 수정 파일: `backend/tests/test_rls_endpoints.py` (4개 401 테스트 추가)

**아키텍처 규칙 준수:**
- FastAPI Admin API는 `get_supabase_client()` 사용 (service key 포함) — 프론트 절대 미노출
- 에러 응답: `{"error": "INSUFFICIENT_PERMISSION", "message": "...", "status_code": 403}` 표준 형식
- 프론트 API 호출은 모두 `lib/api.ts` 경유

### References

- [Source: architecture.md - Authentication & Security] — JWT 검증, Supabase Admin API, service key 격리
- [Source: architecture.md - API & Communication Patterns] — 에러 코드 목록 (`INSUFFICIENT_PERMISSION`)
- [Source: architecture.md - Enforcement Guidelines] — FastAPI 호출 경유 규칙
- [Source: epics.md - Story 2.3] — AC1~AC4 원본
- [Source: 2-2-supabase-rls-role-based-access.md] — `UserProfile`, `UserRoleType`, `get_current_user` 패턴

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

없음 — 모든 테스트 1회 pass, 빌드 성공.

### Completion Notes List

- Task 1~5: `backend/app/api/v1/users.py` 재작성. `require_admin()` 헬퍼를 `auth.py`에 추가하여 모든 Admin 전용 엔드포인트에서 재사용.
- `InviteRoleType` = builder/live_viewer/read_only (admin 직접 초대 불가, 422 반환).
- 계정 비활성화: `banned_until='2099-12-31T23:59:59Z'` 방식으로 기존 JWT 포함 차단 구현.
- AppSidebar 미존재로 `(auth)/layout.tsx`에 Admin 전용 네비게이션 바 추가.
- pytest 57/57 passed, Next.js build success (`/dashboard/team` 경로 생성됨).

### File List

- backend/app/api/v1/users.py (수정 — 엔드포인트 4개 추가)
- backend/app/core/auth.py (수정 — require_admin 추가)
- backend/app/models/schemas.py (수정 — InviteUserRequest, UpdateRoleRequest, InviteRoleType 추가)
- backend/tests/test_user_management.py (신규 — 7개 테스트)
- backend/tests/test_rls_endpoints.py (수정 — 4개 401 테스트 추가)
- frontend/src/lib/api.ts (수정 — apiPatch + 4개 함수)
- frontend/src/components/layout/InviteTeamDialog.tsx (신규)
- frontend/src/app/(auth)/dashboard/team/page.tsx (신규)
- frontend/src/hooks/use-team-management.ts (신규)
- frontend/src/app/(auth)/layout.tsx (수정 — Admin 네비게이션)
