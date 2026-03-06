# Story 3.2: 분석 세트 수정 및 역할 기반 접근

Status: done

## Story

As a Builder,
I want to edit my own analysis sets and have Admin manage all team sets,
So that each team member operates within their permission boundary when collaborating.

## Acceptance Criteria

1. **[분석 세트 수정 - Builder 본인]** Builder가 본인 소유 분석 세트를 불러온 상태에서 기업을 추가·삭제하거나 세트 이름을 변경하고 저장하면, `PATCH /api/v1/analysis-sets/{id}`로 변경 사항이 DB에 반영되어야 한다. 성공 Toast "변경 사항이 저장되었습니다"가 표시되어야 한다.

2. **[권한 부족 - 타인 세트 수정 금지]** Builder가 타인 소유 분석 세트를 수정하려 하면, FastAPI 수정 엔드포인트가 `INSUFFICIENT_PERMISSION` 에러 코드와 403 응답을 반환해야 한다. 프론트엔드에서 타인 소유 세트의 편집·삭제 버튼이 비활성화(또는 미표시)되어야 한다.

3. **[Admin 전체 수정]** Admin이 팀원의 분석 세트를 수정하면, `PATCH /api/v1/analysis-sets/{id}`가 `owner_id`와 무관하게 변경을 허용해야 한다.

4. **[LiveViewer 읽기 전용]** LiveViewer가 분석 세트 목록을 조회하면, 편집·삭제 버튼이 표시되지 않고 읽기 전용 뷰만 제공되어야 한다.

## Tasks / Subtasks

- [x] Task 1: Backend — `AnalysisSetUpdate` 스키마 + `get_user_role()` 헬퍼 추가 (AC: #1, #2, #3)
  - [x] 1.1 `backend/app/models/schemas.py`에 `AnalysisSetUpdate` 추가: `name: Optional[str] = Field(None, min_length=1, max_length=100)`, `company_codes: Optional[list[str]] = Field(None, min_length=1)`
  - [x] 1.2 `backend/app/core/auth.py`에 `get_user_role(user_id: str) -> str` 헬퍼 추가 — `user_profiles` 테이블 조회, 없으면 `"builder"` 반환, DB 오류 시 503 raise

- [x] Task 2: Backend — `PATCH /api/v1/analysis-sets/{id}` 엔드포인트 구현 (AC: #1, #2, #3)
  - [x] 2.1 `backend/app/api/v1/analysis_sets.py`에 PATCH 라우터 추가
  - [x] 2.2 소유권 체크: `get_user_role(user.id)` 호출 → admin이면 허용, builder이면 `owner_id == user.id` 검증, 불일치 시 403 `INSUFFICIENT_PERMISSION`
  - [x] 2.3 세트 존재 여부 확인: 없으면 404 `ANALYSIS_SET_NOT_FOUND`
  - [x] 2.4 name 변경 시 중복 이름 체크 (owner 기준): 중복이면 409 `NAME_ALREADY_EXISTS`
  - [x] 2.5 변경 내용만 업데이트 (partial update): name이 None이면 기존 name 유지, company_codes가 None이면 기존 유지
  - [x] 2.6 업데이트된 `AnalysisSet` 반환 (200)
  - [x] 2.7 모든 DB 작업에 try/except → 503 `DB_UNAVAILABLE`

- [x] Task 3: Backend — `DELETE /api/v1/analysis-sets/{id}` 엔드포인트 구현 (AC: #2, #3)
  - [x] 3.1 `backend/app/api/v1/analysis_sets.py`에 DELETE 라우터 추가 (status 204)
  - [x] 3.2 소유권 체크: PATCH와 동일 패턴 (admin 허용, builder 본인만)
  - [x] 3.3 세트 존재 여부 확인: 없으면 404
  - [x] 3.4 DB에서 삭제 실행, 204 반환 (body 없음)
  - [x] 3.5 모든 DB 작업에 try/except → 503

- [x] Task 4: Backend — 테스트 작성 (AC: #1, #2, #3)
  - [x] 4.1 `backend/tests/test_analysis_sets.py`에 `TestPatchAnalysisSet` 클래스 추가
    - [x] 4.1.1 Builder가 본인 세트 이름 변경 → 200 + 새 이름 반환
    - [x] 4.1.2 Builder가 본인 세트 company_codes 변경 → 200 + 새 codes 반환
    - [x] 4.1.3 Builder가 타인 세트 수정 시도 → 403 `INSUFFICIENT_PERMISSION`
    - [x] 4.1.4 Admin이 타인 세트 수정 → 200 (admin mock 적용)
    - [x] 4.1.5 존재하지 않는 세트 수정 → 404 `ANALYSIS_SET_NOT_FOUND`
    - [x] 4.1.6 중복 이름으로 수정 → 409 `NAME_ALREADY_EXISTS`
    - [x] 4.1.7 빈 name → 422
    - [x] 4.1.8 빈 company_codes → 422
    - [x] 4.1.9 DB 오류 → 503 (TestDbErrors에서 커버)
  - [x] 4.2 `TestDeleteAnalysisSet` 클래스 추가
    - [x] 4.2.1 Builder가 본인 세트 삭제 → 204
    - [x] 4.2.2 Builder가 타인 세트 삭제 시도 → 403
    - [x] 4.2.3 Admin이 타인 세트 삭제 → 204
    - [x] 4.2.4 존재하지 않는 세트 삭제 → 404
  - [x] 4.3 `backend/tests/test_rls_endpoints.py`에 PATCH/DELETE 401 테스트 추가
  - [x] 4.4 pytest 39/39 통과 확인

- [x] Task 5: Frontend — `api.ts`에 updateAnalysisSet/deleteAnalysisSet 추가 (AC: #1, #3)
  - [x] 5.1 `updateAnalysisSet(id: string, data: { name?: string; company_codes?: string[] })` 추가 → `apiPatch<AnalysisSetData>(...)`
  - [x] 5.2 `deleteAnalysisSet(id: string)` 추가 → `apiDelete(...)` — `apiDelete` 헬퍼 신규 추가 (204 no-content 처리)

- [x] Task 6: Frontend — `use-analysis-sets.ts` 훅 확장 (AC: #1, #2, #3, #4)
  - [x] 6.1 `updateSet` useMutation 추가: toast.success("변경 사항이 저장되었습니다", { duration: 3000 })
  - [x] 6.2 `deleteSet` useMutation 추가: toast.success("분석 세트가 삭제되었습니다", { duration: 3000 })
  - [x] 6.3 훅에서 `updateSet`, `deleteSet` export

- [x] Task 7: Frontend — `AnalysisSetItem.tsx` 수정 — 역할 기반 편집/삭제 버튼 (AC: #2, #4)
  - [x] 7.1 `AnalysisSetItemProps`에 `currentUserId`, `currentUserRole` props 추가
  - [x] 7.2 `canEdit = (set.owner_id === currentUserId || currentUserRole === 'admin') && currentUserRole !== 'live_viewer'` 계산
  - [x] 7.3 `canEdit`일 때만 편집/삭제 버튼 표시 — 삭제 클릭 시 `window.confirm`으로 확인
  - [x] 7.4 `AnalysisSetPanel`에도 `currentUserId`, `currentUserRole` prop 전달

- [x] Task 8: Frontend — `UpdateAnalysisSetDialog.tsx` 신규 생성 (AC: #1)
  - [x] 8.1 `frontend/src/components/layout/UpdateAnalysisSetDialog.tsx` 생성
  - [x] 8.2 Props: `set: AnalysisSetData | null`, `open: boolean`, `onOpenChange`, `currentCompanyCodes: string[]`
  - [x] 8.3 UI: name Input (pre-filled via useEffect), 기업 수 표시, 저장 버튼
  - [x] 8.4 submit: `updateSet.mutateAsync({ id, name, companyCodes })`
  - [x] 8.5 중복 이름 오류 시 인라인 에러 (`NAME_ALREADY_EXISTS` 감지)
  - [x] 8.6 성공 시 Dialog 닫기

- [x] Task 9: Frontend — `dashboard/page.tsx` 수정 (AC: #1, #2, #3, #4)
  - [x] 9.1 `getUserProfile` useQuery 추가: `useQuery({ queryKey: ['users', 'me'], queryFn: getUserProfile })`
  - [x] 9.2 `editingSet: AnalysisSetData | null` + `updateDialogOpen: boolean` state 추가
  - [x] 9.3 `handleEditAnalysisSet` → `setEditingSet` + `setUpdateDialogOpen(true)`
  - [x] 9.4 `handleDeleteAnalysisSet` → `deleteSet.mutate(setId)`
  - [x] 9.5 `UpdateAnalysisSetDialog` 항상 렌더, editingSet 기반으로 열림
  - [x] 9.6 `AnalysisSetPanel`에 `currentUserId`, `currentUserRole` 전달

- [x] Task 10: Next.js 빌드 통과 확인 (AC: 전체)
  - [x] 10.1 `npm run build` TypeScript 에러 없이 통과

## Dev Notes

### Critical: 아키텍처 강제 규칙 (위반 시 PR 거부)

- 컴포넌트에서 `fetch()` 직접 호출 금지 → 반드시 `lib/api.ts` 경유
- `shadcn/ui` 컴포넌트 직접 수정 금지 (`frontend/src/components/ui/` 폴더)
- `dart_client.py` 이외에서 OpenDartReader import 금지
- `analysis-sets` 쿼리 키는 `use-analysis-sets.ts` 이외 파일에서 직접 사용 금지

### Backend 구현 패턴

#### `get_user_role()` 헬퍼 (auth.py에 추가)

```python
# backend/app/core/auth.py — require_admin() 바로 아래 추가
def get_user_role(user_id: str) -> str:
    """user_profiles에서 역할 조회. 없으면 'builder' 반환. DB 오류 시 503 raise."""
    from fastapi import HTTPException, status
    supabase = get_supabase_client()
    try:
        res = supabase.table("user_profiles").select("role").eq("id", user_id).execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "DB_UNAVAILABLE", "message": "권한 확인 중 오류가 발생했습니다.", "status_code": 503},
        )
    return res.data[0]["role"] if res.data else "builder"
```

#### `AnalysisSetUpdate` 스키마 (schemas.py에 추가)

```python
# Story 3.2: 분석 세트 수정 스키마
class AnalysisSetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    company_codes: Optional[list[str]] = Field(None, min_length=1)
```

`Optional` import: `from typing import Literal, Optional` (이미 있음)

#### PATCH 엔드포인트 패턴

```python
# backend/app/api/v1/analysis_sets.py
from app.core.auth import get_current_user, get_user_role
from app.models.schemas import AnalysisSet, AnalysisSetCreate, AnalysisSetUpdate

@router.patch("/analysis-sets/{set_id}", response_model=AnalysisSet)
async def update_analysis_set(set_id: str, body: AnalysisSetUpdate, user=Depends(get_current_user)):
    supabase = get_supabase_client()

    # 세트 존재 확인
    try:
        res = supabase.table("analysis_sets").select("*").eq("id", set_id).execute()
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "DB_UNAVAILABLE", ...})
    if not res.data:
        raise HTTPException(status_code=404, detail={"error": "ANALYSIS_SET_NOT_FOUND", ...})

    existing = res.data[0]

    # 소유권 체크
    role = get_user_role(user.id)
    if role != "admin" and existing["owner_id"] != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "INSUFFICIENT_PERMISSION", "message": "본인 소유의 분석 세트만 수정할 수 있습니다.", "status_code": 403},
        )

    # name 중복 체크 (name 변경 시에만, 본인의 다른 세트와 중복 확인)
    if body.name is not None and body.name != existing["name"]:
        owner_id = existing["owner_id"]  # admin이 타인 세트 수정 시에도 기존 owner 기준
        try:
            dup = supabase.table("analysis_sets").select("id").eq("owner_id", owner_id).eq("name", body.name).execute()
        except Exception:
            raise HTTPException(status_code=503, detail={"error": "DB_UNAVAILABLE", ...})
        if dup.data:
            raise HTTPException(status_code=409, detail={"error": "NAME_ALREADY_EXISTS", ...})

    # 변경 필드만 업데이트 (partial update)
    update_data = {}
    if body.name is not None:
        update_data["name"] = body.name
    if body.company_codes is not None:
        update_data["company_codes"] = body.company_codes

    if not update_data:
        return existing  # 변경 없음

    try:
        updated = supabase.table("analysis_sets").update(update_data).eq("id", set_id).execute()
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "DB_UNAVAILABLE", ...})
    return updated.data[0]
```

#### DELETE 엔드포인트 패턴

```python
from fastapi import Response

@router.delete("/analysis-sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_set(set_id: str, user=Depends(get_current_user)):
    supabase = get_supabase_client()

    # 세트 존재 확인
    try:
        res = supabase.table("analysis_sets").select("id", "owner_id").eq("id", set_id).execute()
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "DB_UNAVAILABLE", ...})
    if not res.data:
        raise HTTPException(status_code=404, detail={"error": "ANALYSIS_SET_NOT_FOUND", ...})

    # 소유권 체크
    role = get_user_role(user.id)
    if role != "admin" and res.data[0]["owner_id"] != user.id:
        raise HTTPException(status_code=403, detail={"error": "INSUFFICIENT_PERMISSION", ...})

    # 삭제
    try:
        supabase.table("analysis_sets").delete().eq("id", set_id).execute()
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "DB_UNAVAILABLE", ...})
    # 204 → FastAPI는 자동으로 body 없이 반환
```

**주의:** 204 No Content는 `response_model` 지정하지 않음. FastAPI가 자동으로 빈 응답 처리.

#### Admin mock 테스트 패턴 (새로운 방법)

Admin 테스트는 기존 `_mock_user()` 함수를 builder용으로 유지하고, 추가 fixture로 admin mock:

```python
# test_analysis_sets.py에 추가
ADMIN_USER_ID = "admin-user-id"

def _mock_admin_user():
    user = MagicMock()
    user.id = ADMIN_USER_ID
    return user

# Admin 테스트 시 get_user_role도 mock 필요!
# PATCH/DELETE에서 get_user_role()을 DB 쿼리로 조회하므로 supabase mock 체인에서 처리
# 또는: patch("app.api.v1.analysis_sets.get_user_role", return_value="admin")

with patch("app.api.v1.analysis_sets.get_user_role", return_value="admin"):
    with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
        res = admin_client.patch(...)
```

**중요:** `get_user_role`은 `auth.py`에 있지만 `analysis_sets.py`에서 import해서 사용하므로 patch target은 `app.api.v1.analysis_sets.get_user_role`.

#### PATCH mock DB 체인

```python
def test_update_own_set_returns_200(self, client):
    mock_sb = MagicMock()
    # 1) 세트 존재 확인 (GET)
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [SAMPLE_SET]
    # 2) 중복 이름 체크 (GET) — 중복 없음
    # 3) 업데이트 (UPDATE) → 반환값
    updated_set = {**SAMPLE_SET, "name": "새 이름"}
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [updated_set]

    with patch("app.api.v1.analysis_sets.get_user_role", return_value="builder"):
        with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_sb):
            res = client.patch(f"/api/v1/analysis-sets/{SAMPLE_SET['id']}", json={"name": "새 이름"})

    assert res.status_code == 200
    assert res.json()["name"] == "새 이름"
```

**주의:** Mock 체인이 복잡할 수 있음. `select.return_value.eq.return_value.execute` 체인이 첫 번째 DB 조회와 중복 체크에서 충돌할 수 있으므로, `MagicMock` autospec을 활용하거나 `side_effect` 리스트 활용:

```python
# execute side_effect: [세트 존재 확인 결과, 중복 이름 없음, ...]
mock_execute = mock_sb.table.return_value.select.return_value.eq.return_value.execute
mock_execute.side_effect = [
    MagicMock(data=[SAMPLE_SET]),  # 첫 번째 호출: 세트 존재 확인
    MagicMock(data=[]),            # 두 번째 호출: 중복 이름 없음
]
```

### Frontend 구현 패턴

#### `apiDelete` 헬퍼 (api.ts에 추가)

```typescript
export async function apiDelete(path: string, token?: string): Promise<void> {
  const resolvedToken = token ?? await getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (resolvedToken) headers['Authorization'] = `Bearer ${resolvedToken}`

  const res = await fetch(`${API_URL}${path}`, { method: 'DELETE', headers })
  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR', message: 'Unknown error occurred', status_code: res.status,
    }))
    throw error
  }
  // 204 No Content: no body to parse
}
```

#### `updateAnalysisSet`, `deleteAnalysisSet` (api.ts에 추가)

```typescript
// Story 3.2: 분석 세트 수정 및 삭제
export async function updateAnalysisSet(
  id: string,
  data: { name?: string; company_codes?: string[] }
): Promise<AnalysisSetData> {
  return apiPatch<AnalysisSetData>(`/api/v1/analysis-sets/${id}`, data)
}

export async function deleteAnalysisSet(id: string): Promise<void> {
  return apiDelete(`/api/v1/analysis-sets/${id}`)
}
```

#### `use-analysis-sets.ts` 확장

```typescript
import { createAnalysisSet, deleteAnalysisSet, getAnalysisSet, listAnalysisSets, updateAnalysisSet } from '@/lib/api'

export function useAnalysisSets() {
  const queryClient = useQueryClient()

  // ... (기존 useQuery, saveSet, loadSet 유지)

  const updateSet = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; company_codes?: string[] } }) =>
      updateAnalysisSet(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
      toast.success('변경 사항이 저장되었습니다', { duration: 3000 })
    },
  })

  const deleteSet = useMutation({
    mutationFn: (id: string) => deleteAnalysisSet(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
      toast.success('분석 세트가 삭제되었습니다', { duration: 3000 })
    },
  })

  return { analysisSets, isLoading, saveSet, loadSet, updateSet, deleteSet }
}
```

#### `UpdateAnalysisSetDialog.tsx` 패턴

```tsx
'use client'
import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'
import type { AnalysisSetData } from '@/lib/api'

interface UpdateAnalysisSetDialogProps {
  activeSet: AnalysisSetData
  currentCompanyCodes: string[]  // 현재 대시보드에 선택된 기업 codes
}

export function UpdateAnalysisSetDialog({ activeSet, currentCompanyCodes }: UpdateAnalysisSetDialogProps) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(activeSet.name)
  const [error, setError] = useState<string | null>(null)
  const { updateSet } = useAnalysisSets()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await updateSet.mutateAsync({
        id: activeSet.id,
        data: { name: name.trim(), company_codes: currentCompanyCodes },
      })
      setOpen(false)
    } catch (err: unknown) {
      const apiErr = err as { error?: string; message?: string }
      if (apiErr?.error === 'NAME_ALREADY_EXISTS') {
        setError('이미 사용 중인 이름입니다. 다른 이름을 입력하세요.')
      } else {
        setError(apiErr?.message || '저장에 실패했습니다. 다시 시도해주세요.')
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          &apos;{activeSet.name}&apos; 업데이트
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>분석 세트 업데이트</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium">분석 세트 이름</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} required disabled={updateSet.isPending} />
            <p className="text-xs text-muted-foreground">
              현재 선택된 기업 {currentCompanyCodes.length}개로 업데이트됩니다.
            </p>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)} disabled={updateSet.isPending}>취소</Button>
            <Button type="submit" disabled={updateSet.isPending || !name.trim()}>
              {updateSet.isPending ? '저장 중...' : '저장'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
```

#### `AnalysisSetItem.tsx` 수정 패턴

```tsx
import { Trash2 } from 'lucide-react'  // lucide-react는 이미 설치됨 (shadcn/ui 의존성)
import { useAnalysisSets } from '@/hooks/use-analysis-sets'

interface AnalysisSetItemProps {
  set: AnalysisSetData
  onLoad: (setId: string) => void
  currentUserId?: string
  currentUserRole?: string
}

export function AnalysisSetItem({ set, onLoad, currentUserId, currentUserRole }: AnalysisSetItemProps) {
  const { deleteSet } = useAnalysisSets()
  const canEdit = (set.owner_id === currentUserId || currentUserRole === 'admin')
                  && currentUserRole !== 'live_viewer'

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation()
    if (!window.confirm(`'${set.name}' 분석 세트를 삭제하시겠습니까?`)) return
    await deleteSet.mutateAsync(set.id)
  }

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => onLoad(set.id)}
        className="flex-1 text-left px-3 py-2 rounded-md hover:bg-accent transition-colors border border-border"
      >
        <p className="text-sm font-medium truncate">{set.name}</p>
        <p className="text-xs text-muted-foreground mt-0.5">기업 {set.company_codes.length}개</p>
      </button>
      {canEdit && (
        <button
          onClick={handleDelete}
          className="p-1.5 text-muted-foreground hover:text-destructive transition-colors"
          aria-label={`${set.name} 삭제`}
          disabled={deleteSet.isPending}
        >
          <Trash2 size={14} />
        </button>
      )}
    </div>
  )
}
```

#### `dashboard/page.tsx` 수정 포인트

```tsx
// 추가 import
import { getUserProfile } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import type { AnalysisSetData } from '@/lib/api'
import { UpdateAnalysisSetDialog } from '@/components/layout/UpdateAnalysisSetDialog'

// 추가 state 및 query
const { data: currentUser } = useQuery({ queryKey: ['users', 'me'], queryFn: getUserProfile })
const [activeSet, setActiveSet] = useState<AnalysisSetData | null>(null)

// handleLoadAnalysisSet 수정 (activeSet 추가 설정)
const handleLoadAnalysisSet = async (setId: string) => {
  const data = await loadSet.mutateAsync(setId)
  setActiveSet(data)  // ← 추가
  const restored: Company[] = data.company_codes.slice(0, MAX_COMPANIES).map((code) => ({
    corp_code: code, company_name: code, stock_code: null, is_listed: true, created_at: '',
  }))
  setSelectedCompanies(restored)
}

// canEditActiveSet 계산
const canEditActiveSet = activeSet && currentUser &&
  (activeSet.owner_id === currentUser.id || currentUser.role === 'admin') &&
  currentUser.role !== 'live_viewer'

// 기존 SaveAnalysisSetDialog 옆에 UpdateAnalysisSetDialog 추가 (activeSet && canEditActiveSet일 때)
<div className="flex items-center gap-2">
  <SaveAnalysisSetDialog companyCodes={selectedCompanies.map((c) => c.corp_code)} />
  {activeSet && canEditActiveSet && (
    <UpdateAnalysisSetDialog
      activeSet={activeSet}
      currentCompanyCodes={selectedCompanies.map((c) => c.corp_code)}
    />
  )}
</div>

// AnalysisSetPanel에 currentUser 전달
<AnalysisSetPanel
  analysisSets={analysisSets}
  isLoading={setsLoading}
  onLoad={handleLoadAnalysisSet}
  currentUserId={currentUser?.id}
  currentUserRole={currentUser?.role}
/>
```

### Story 3.1 학습 사항 (이번 스토리에 적용)

**middleware.ts 이슈:** `request.cookies.set(name, value)` — Next.js 16에서 options 미지원. response cookies에만 options 전달 가능 (이미 수정됨).

**타입 가드:** `Company` 타입에 `created_at: string` 필드 필수 — 빈 문자열로 채워야 함 (`created_at: ''`).

**DB mock 체인 주의:** `select().eq().execute()` 체인을 동일 mock으로 여러 번 호출하는 경우 `side_effect` 리스트 사용.

**에러 코드 추가:** `INSUFFICIENT_PERMISSION` — 이미 architecture.md에 정의됨, `ANALYSIS_SET_NOT_FOUND` — Story 3.1에서 이미 사용.

### 아키텍처 준수 사항

- **에러 코드**: `INSUFFICIENT_PERMISSION`(403), `ANALYSIS_SET_NOT_FOUND`(404), `NAME_ALREADY_EXISTS`(409), `DB_UNAVAILABLE`(503)
- **TanStack Query 키**: `['analysis-sets']` (목록), `['analysis-sets', id]` (단일), `['users', 'me']` (사용자 프로필)
- **Auth 패턴**: `get_user_role()` 헬퍼는 `auth.py`에 위치 — `require_admin()` 패턴과 동일
- **RLS 우회**: service_role 키는 RLS 우회 → 소유권 체크는 FastAPI 코드 레벨에서 직접 구현
- **204 No Content**: DELETE 엔드포인트는 `status_code=204`, `response_model` 없음
- **Toast**: `sonner` 라이브러리만 사용

### 환경변수

추가 환경변수 불필요.

### 의도적으로 이번 스토리에서 미구현

- APScheduler 자동 갱신 → Story 3.3
- B/S 차트 → Story 3.4
- 현금흐름 차트 → Story 3.5
- 공유 링크 → Epic 4
- `share_token` 생성 → Epic 4

### Project Structure Notes

**수정:**
- `backend/app/models/schemas.py` — `AnalysisSetUpdate` 추가
- `backend/app/core/auth.py` — `get_user_role()` 헬퍼 추가
- `backend/app/api/v1/analysis_sets.py` — PATCH, DELETE 엔드포인트 추가
- `backend/tests/test_analysis_sets.py` — TestPatchAnalysisSet, TestDeleteAnalysisSet 추가
- `backend/tests/test_rls_endpoints.py` — PATCH/DELETE 401 테스트 추가
- `frontend/src/lib/api.ts` — `apiDelete`, `updateAnalysisSet`, `deleteAnalysisSet` 추가
- `frontend/src/hooks/use-analysis-sets.ts` — `updateSet`, `deleteSet` 추가
- `frontend/src/components/layout/AnalysisSetItem.tsx` — 역할 기반 삭제 버튼 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — `activeSet`, `currentUser`, `UpdateAnalysisSetDialog` 통합

**신규 생성:**
- `frontend/src/components/layout/UpdateAnalysisSetDialog.tsx`

### References

- AC 출처: [epics.md - Story 3.2 분석 세트 수정 및 역할 기반 접근]
- DB 스키마: [architecture.md - Core Architectural Decisions > Data Architecture > analysis_sets]
- API 패턴: [architecture.md - API & Communication Patterns > REST API 설계]
- 에러 코드: [architecture.md - API & Communication Patterns > 에러 코드 목록]
- 역할 체크 패턴: [Story 2.3 구현 - require_admin() 패턴 in app/core/auth.py]
- RLS 정책: [architecture.md - Authentication & Security > RLS 정책 원칙]
- TanStack Query 키: [architecture.md - Frontend Architecture > TanStack Query 쿼리 키 규칙]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List

**수정:**
- `backend/app/models/schemas.py`
- `backend/app/core/auth.py`
- `backend/app/api/v1/analysis_sets.py`
- `backend/tests/test_analysis_sets.py`
- `backend/tests/test_rls_endpoints.py`
- `frontend/src/lib/api.ts`
- `frontend/src/hooks/use-analysis-sets.ts`
- `frontend/src/components/layout/AnalysisSetItem.tsx`
- `frontend/src/app/(auth)/dashboard/page.tsx`

**신규 생성:**
- `frontend/src/components/layout/UpdateAnalysisSetDialog.tsx`
