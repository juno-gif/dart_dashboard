# Story 3.1: 분석 세트 저장 및 불러오기

Status: done

## Story

As a Builder,
I want to save the current company selection as a named analysis set and reload it instantly,
So that I can resume complex multi-company analyses without rebuilding them from scratch.

## Acceptance Criteria

1. **[분석 세트 저장]** Builder가 1개 이상의 기업을 선택한 상태에서 "분석 세트 저장" 버튼을 클릭하고 이름을 입력해 제출하면, `POST /api/v1/analysis-sets` 요청으로 DB에 즉시 저장되고 저장 목록에 표시되어야 한다. 성공 Toast "분석 세트가 저장되었습니다"가 3초 후 자동 소멸되어야 한다.

2. **[분석 세트 불러오기]** 저장된 분석 세트를 클릭하면 `GET /api/v1/analysis-sets/{id}`로 구성이 불러와지고, CompanyTag가 복원되며 각 기업의 최신 재무 데이터가 자동으로 로드되어 차트가 렌더링되어야 한다.

3. **[빈 상태]** 저장된 분석 세트가 없을 때 목록을 열면 "저장된 분석 세트가 없습니다. 기업을 선택한 후 저장해 보세요." 빈 상태 메시지가 표시되어야 한다.

4. **[중복 이름 방지]** 분석 세트 이름이 이미 존재할 때 동일한 이름으로 저장하면 "이미 사용 중인 이름입니다. 다른 이름을 입력하세요." 인라인 오류가 표시되어야 한다.

5. **[목록 조회]** `GET /api/v1/analysis-sets`는 로그인 사용자가 접근 가능한 세트 목록을 반환해야 한다 (자신이 저장한 세트).

## Tasks / Subtasks

- [x] Task 1: Backend — `AnalysisSet` Pydantic 스키마 추가 (AC: #1, #2, #5)
  - [x] 1.1 `backend/app/models/schemas.py`에 `AnalysisSet` 모델 추가
  - [x] 1.2 `AnalysisSetCreate` 요청 스키마: `name: str`, `company_codes: list[str]`
  - [x] 1.3 `AnalysisSet` 응답 스키마: `id, name, owner_id, company_codes, created_at, updated_at`

- [x] Task 2: Backend — `analysis_sets.py` 라우터 신규 생성 (AC: #1, #2, #3, #4, #5)
  - [x] 2.1 `backend/app/api/v1/analysis_sets.py` 신규 생성
  - [x] 2.2 `POST /api/v1/analysis-sets`: 분석 세트 저장 (auth guard, 중복 이름 체크)
  - [x] 2.3 `GET /api/v1/analysis-sets`: 현재 사용자 세트 목록 조회 (auth guard)
  - [x] 2.4 `GET /api/v1/analysis-sets/{set_id}`: 단일 세트 조회 (auth guard)
  - [x] 2.5 중복 이름 시 `NAME_ALREADY_EXISTS` 에러코드 + 409 반환

- [x] Task 3: Backend — `main.py`에 라우터 등록 (AC: #1)
  - [x] 3.1 `backend/app/main.py`에 `analysis_sets` 라우터 import + 등록

- [x] Task 4: Backend — 분석 세트 테스트 작성 (AC: #1, #2, #3, #4, #5)
  - [x] 4.1 `backend/tests/test_analysis_sets.py` 신규 작성
  - [x] 4.2 Builder가 세트 저장 → 201 + AnalysisSet 반환 테스트
  - [x] 4.3 중복 이름 저장 → 409 `NAME_ALREADY_EXISTS` 테스트
  - [x] 4.4 세트 목록 조회 → 200 + 리스트 테스트
  - [x] 4.5 단일 세트 조회 → 200 + AnalysisSet 테스트
  - [x] 4.6 토큰 없이 접근 → 401 테스트 (test_rls_endpoints.py에 추가)
  - [x] 4.7 pytest 전체 통과 확인 (67/67)

- [x] Task 5: Frontend — `api.ts`에 분석 세트 함수 추가 (AC: #1, #2, #5)
  - [x] 5.1 `frontend/src/lib/api.ts`에 `createAnalysisSet`, `listAnalysisSets`, `getAnalysisSet` 추가
  - [x] 5.2 `AnalysisSetData` 인터페이스 정의 (id, name, owner_id, company_codes, created_at, updated_at)

- [x] Task 6: Frontend — `use-analysis-sets.ts` 훅 생성 (AC: #1, #2, #5)
  - [x] 6.1 `frontend/src/hooks/use-analysis-sets.ts` 신규 생성
  - [x] 6.2 `useQuery(['analysis-sets'])` — 목록 조회
  - [x] 6.3 `useMutation` — 세트 저장 + `invalidateQueries(['analysis-sets'])`
  - [x] 6.4 성공 시 sonner `toast.success("분석 세트가 저장되었습니다")` 호출

- [x] Task 7: Frontend — `SaveAnalysisSetDialog.tsx` 컴포넌트 생성 (AC: #1, #4)
  - [x] 7.1 `frontend/src/components/layout/SaveAnalysisSetDialog.tsx` 신규 생성
  - [x] 7.2 Dialog 트리거: "분석 세트 저장" 버튼 (선택된 기업이 없으면 비활성화)
  - [x] 7.3 이름 입력 Input + 저장 버튼
  - [x] 7.4 중복 이름 오류 시 인라인 에러 표시 (`NAME_ALREADY_EXISTS` 감지)

- [x] Task 8: Frontend — `AnalysisSetItem.tsx` + 목록 패널 구현 (AC: #2, #3)
  - [x] 8.1 `frontend/src/components/layout/AnalysisSetItem.tsx` 신규 생성
  - [x] 8.2 세트 이름 + 기업 수 표시, 클릭 시 세트 불러오기
  - [x] 8.3 빈 상태 메시지: "저장된 분석 세트가 없습니다. 기업을 선택한 후 저장해 보세요."
  - [x] 8.4 대시보드 페이지에 분석 세트 목록 패널 통합

- [x] Task 9: Next.js 빌드 통과 확인 (AC: 전체)
  - [x] 9.1 `npm run build` TypeScript 에러 없이 통과

## Dev Notes

### Critical: 아키텍처 강제 규칙

**절대 금지 사항 (위반 시 PR 거부):**
- 컴포넌트에서 `fetch()` 직접 호출 금지 → 반드시 `lib/api.ts` 경유
- `use-analysis-sets.ts` 이외 파일에서 `analysis-sets` 쿼리 키 직접 사용 금지
- `shadcn/ui` 컴포넌트 직접 수정 금지 (`frontend/src/components/ui/` 폴더)
- `dart_client.py` 이외에서 OpenDartReader import 금지

**기존 패턴 재사용 필수:**
- `lib/api.ts`의 `apiGet`, `apiPost` 함수 재사용 (새로 fetch 래퍼 작성 금지)
- `hooks/use-team-management.ts` 패턴을 `use-analysis-sets.ts`에 그대로 적용
- `components/layout/InviteTeamDialog.tsx` 패턴을 `SaveAnalysisSetDialog.tsx`에 적용
- Toast는 `sonner` 라이브러리 (`import { toast } from 'sonner'`) — 이미 설치됨

### Backend 구현 패턴

**분석 세트 저장 (POST):**
```python
# backend/app/api/v1/analysis_sets.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import get_current_user
from app.core.database import get_supabase_client
from app.models.schemas import AnalysisSet, AnalysisSetCreate

router = APIRouter()

@router.post("/analysis-sets", status_code=status.HTTP_201_CREATED, response_model=AnalysisSet)
async def create_analysis_set(body: AnalysisSetCreate, user=Depends(get_current_user)):
    supabase = get_supabase_client()

    # 중복 이름 체크 (owner_id 기준)
    dup = supabase.table("analysis_sets").select("id").eq("owner_id", user.id).eq("name", body.name).execute()
    if dup.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "NAME_ALREADY_EXISTS", "message": "이미 사용 중인 이름입니다. 다른 이름을 입력하세요.", "status_code": 409},
        )

    res = supabase.table("analysis_sets").insert({
        "name": body.name,
        "owner_id": user.id,
        "company_codes": body.company_codes,
    }).execute()
    return res.data[0]
```

**스키마 패턴:**
```python
# backend/app/models/schemas.py 에 추가
class AnalysisSetCreate(BaseModel):
    name: str
    company_codes: list[str]

class AnalysisSet(BaseModel):
    id: str
    name: str
    owner_id: str
    company_codes: list[str]
    created_at: str
    updated_at: str
```

**주의: `company_codes`는 Supabase JSONB 컬럼** — Python에서 `list[str]`로 읽고 쓰면 자동 직렬화됨.

**라우터 등록 (`main.py`):**
```python
from app.api.v1 import companies, financials, health, sync, users, analysis_sets
app.include_router(analysis_sets.router, prefix="/api/v1")
```

### Frontend 구현 패턴

**TanStack Query 쿼리 키 (architecture.md 명시):**
```typescript
['analysis-sets']           // 목록
['analysis-sets', id]       // 단일 세트
```

**use-analysis-sets.ts 훅 패턴:**
```typescript
// hooks/use-analysis-sets.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { createAnalysisSet, listAnalysisSets } from '@/lib/api'

export function useAnalysisSets() {
  const queryClient = useQueryClient()

  const { data: analysisSets, isLoading } = useQuery({
    queryKey: ['analysis-sets'],
    queryFn: listAnalysisSets,
  })

  const saveSet = useMutation({
    mutationFn: ({ name, companyCodes }: { name: string; companyCodes: string[] }) =>
      createAnalysisSet({ name, company_codes: companyCodes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
      toast.success('분석 세트가 저장되었습니다', { duration: 3000 })
    },
  })

  return { analysisSets, isLoading, saveSet }
}
```

**분석 세트 불러오기 패턴:**
```typescript
// 세트 클릭 시: company_codes 배열을 기반으로 CompanyTag 복원
// 각 corp_code에 대해 기존 getFinancials() 호출로 차트 자동 렌더링
// → 대시보드의 기존 selectedCompanies 상태에 set.company_codes를 설정
```

**SaveAnalysisSetDialog 에러 처리:**
```typescript
// NAME_ALREADY_EXISTS 에러 감지 패턴 (InviteTeamDialog와 동일)
const apiErr = err as { error?: string; message?: string }
if (apiErr?.error === 'NAME_ALREADY_EXISTS') {
  setError('이미 사용 중인 이름입니다. 다른 이름을 입력하세요.')
}
```

### 기존 테스트 파일 패턴

**`dependency_overrides` 패턴 필수 적용 (Epic 2에서 확립):**
```python
# test_analysis_sets.py
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

def _mock_user():
    user = MagicMock()
    user.id = "test-user-id"
    return user

@pytest.fixture
def client():
    from app.core.auth import get_current_user
    from app.main import app
    app.dependency_overrides[get_current_user] = _mock_user
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### 아키텍처 준수 사항

- **에러 코드**: `NAME_ALREADY_EXISTS` (409), `ANALYSIS_SET_NOT_FOUND` (404)
- **snake_case 통일**: API 응답 필드명 snake_case (`company_codes`, `owner_id`, `created_at`)
- **Toast 라이브러리**: `sonner` (이미 설치됨) — `import { toast } from 'sonner'`
- **RLS**: 백엔드 service_role 키는 RLS 우회 — `owner_id` 필터링은 백엔드 코드에서 직접 구현
- **인증 가드**: 모든 `/api/v1/analysis-sets*` 엔드포인트에 `get_current_user` Dependency 필수

### 환경변수

추가 환경변수 불필요 — 기존 `SUPABASE_SERVICE_KEY`로 analysis_sets 테이블 접근 가능

### 의도적으로 이번 스토리에서 미구현

- `PATCH /api/v1/analysis-sets/{id}` (수정) → Story 3.2
- `DELETE /api/v1/analysis-sets/{id}` (삭제) → Story 3.2
- `share_token` 기반 공유 링크 → Epic 4
- `POST /api/v1/analysis-sets/{id}/share` → Epic 4
- LiveViewer 읽기 전용 뷰 → Story 3.2
- APScheduler 자동 갱신 → Story 3.3
- `config` JSONB 필드 활용 → Story 3.2

### Project Structure Notes

**신규 생성:**
- `backend/app/api/v1/analysis_sets.py`
- `backend/tests/test_analysis_sets.py`
- `frontend/src/hooks/use-analysis-sets.ts`
- `frontend/src/components/layout/SaveAnalysisSetDialog.tsx`
- `frontend/src/components/layout/AnalysisSetItem.tsx`

**수정:**
- `backend/app/models/schemas.py` — AnalysisSet, AnalysisSetCreate 추가
- `backend/app/main.py` — analysis_sets 라우터 등록
- `frontend/src/lib/api.ts` — createAnalysisSet, listAnalysisSets, getAnalysisSet 추가
- `backend/tests/test_rls_endpoints.py` — analysis-sets 401 테스트 추가

### References

- AC 출처: [epics.md - Story 3.1 분석 세트 저장 및 불러오기]
- DB 스키마: [architecture.md - Core Architectural Decisions > Data Architecture > analysis_sets]
- API 패턴: [architecture.md - API & Communication Patterns]
- TanStack Query 키: [architecture.md - Frontend Architecture > TanStack Query 쿼리 키 규칙]
- 에러 코드: [architecture.md - API & Communication Patterns > 에러 코드 목록]
- 컴포넌트 구조: [architecture.md - Frontend Architecture > 컴포넌트 구조]
- Toast 패턴: [architecture.md - Error Handling Patterns]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- middleware.ts 빌드 오류: `request.cookies.set(name, value, options)` → Next.js 16에서 options 미지원 → `request.cookies.set(name, value)` 로 수정 (response cookies에만 options 전달)
- dashboard/page.tsx 타입 오류: `Company` 타입에 `created_at` 필드 필수 → handleLoadAnalysisSet에서 `created_at: ''` 추가

### Completion Notes List

- ✅ Task 1: `AnalysisSetCreate`, `AnalysisSet` Pydantic 스키마 schemas.py에 추가
- ✅ Task 2: analysis_sets.py 라우터 생성 — POST/GET 3개 엔드포인트, NAME_ALREADY_EXISTS(409)/ANALYSIS_SET_NOT_FOUND(404) 에러 처리
- ✅ Task 3: main.py에 analysis_sets 라우터 등록
- ✅ Task 4: test_analysis_sets.py (10개 테스트), test_rls_endpoints.py 401 테스트 3개 추가 — 67/67 전체 통과
- ✅ Task 5: api.ts에 createAnalysisSet, listAnalysisSets, getAnalysisSet + AnalysisSetData 인터페이스 추가
- ✅ Task 6: use-analysis-sets.ts 훅 생성 — useQuery/useMutation, sonner toast 성공 알림
- ✅ Task 7: SaveAnalysisSetDialog.tsx — 기업 없을 때 비활성화, NAME_ALREADY_EXISTS 인라인 에러
- ✅ Task 8: AnalysisSetItem.tsx/AnalysisSetPanel + 대시보드 통합, 빈 상태 메시지 구현
- ✅ Task 9: npm run build TypeScript 에러 없이 통과

### File List

**신규 생성:**
- `backend/app/api/v1/analysis_sets.py`
- `backend/tests/test_analysis_sets.py`
- `frontend/src/hooks/use-analysis-sets.ts`
- `frontend/src/components/layout/SaveAnalysisSetDialog.tsx`
- `frontend/src/components/layout/AnalysisSetItem.tsx`

**수정:**
- `backend/app/models/schemas.py` — AnalysisSetCreate, AnalysisSet 스키마 추가
- `backend/app/main.py` — analysis_sets 라우터 등록
- `frontend/src/lib/api.ts` — createAnalysisSet, listAnalysisSets, getAnalysisSet, AnalysisSetData 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — 분석 세트 패널 + SaveAnalysisSetDialog 통합
- `backend/tests/test_rls_endpoints.py` — analysis-sets 401 테스트 3개 추가
- `frontend/src/middleware.ts` — request.cookies.set options 제거 (빌드 오류 수정)

### Change Log

- 2026-03-06: Story 3-1 구현 완료 — 분석 세트 저장/불러오기 백엔드 API + 프론트엔드 UI 전체 구현
- 2026-03-06: Code review 수정 — H1(DB 예외 처리 503), H2(name max_length=100/min=1, company_codes min=1), M1(AC#2 GET /api/v1/analysis-sets/{id} 호출 적용), M2(빈 배열 백엔드 검증) — 73/73 통과
