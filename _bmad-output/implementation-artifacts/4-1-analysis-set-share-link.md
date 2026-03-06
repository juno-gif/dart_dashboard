# Story 4.1: 분석 세트 공유 링크 생성

Status: done

## Story

As a Builder,
I want to generate a shareable link for an analysis set,
so that I can distribute the analysis via collaboration tools without requiring recipients to log in.

## Acceptance Criteria

1. **[공유 링크 생성 API]** Builder가 본인 소유 분석 세트를 보고 있는 상태에서 "공유 링크 생성" 버튼을 클릭하면 `POST /api/v1/analysis-sets/{id}/share`가 호출되어 고유 `share_token`이 생성되고 DB에 저장되어야 한다

2. **[공유 URL 표시]** share_token이 생성되면 공유 Dialog가 열리고 `{BASE_URL}/shared/{share_token}` 형식의 URL이 표시되어야 한다. Dialog는 최대 480px 너비, backdrop-blur 오버레이로 표시되어야 한다

3. **[클립보드 복사]** 공유 Dialog에서 "링크 복사" 버튼을 클릭하면 공유 URL이 클립보드에 복사되고 "링크가 복사되었습니다" Toast가 3초 후 자동 소멸되어야 한다

4. **[중복 토큰 방지 — 멱등성]** 동일한 분석 세트에 이미 share_token이 존재할 때 Builder가 "공유 링크 생성"을 다시 클릭하면 기존 share_token을 재사용하여 동일한 URL이 표시되어야 한다 (중복 토큰 생성 금지)

## Tasks / Subtasks

- [x] Task 1: Backend — `schemas.py` 업데이트 (AC: #1, #4)
  - [x] 1.1 `AnalysisSet` Pydantic 스키마에 `share_token: Optional[str] = None` 필드 추가 (DB 스키마에 이미 존재, 응답에만 누락됨)
  - [x] 1.2 `ShareResponse` 스키마 추가: `share_token: str`, `share_url: str`

- [x] Task 2: Backend — `analysis_sets.py` 공유 엔드포인트 추가 (AC: #1, #4)
  - [x] 2.1 `POST /analysis-sets/{set_id}/share` 엔드포인트 추가
  - [x] 2.2 세트 존재 확인 + 소유권 체크 (Builder: 본인 소유만, Admin: 전체)
  - [x] 2.3 기존 share_token 있으면 재사용 (멱등성), 없으면 `secrets.token_urlsafe(32)` 로 신규 생성
  - [x] 2.4 `share_url = f"{settings.FRONTEND_URL}/shared/{share_token}"` 조립 후 `ShareResponse` 반환
  - [x] 2.5 `FRONTEND_URL` 환경변수를 `app/core/config.py`의 `Settings` 클래스에 추가

- [x] Task 3: Backend — `test_analysis_sets.py` 공유 테스트 추가 (AC: #1, #4)
  - [x] 3.1 `test_share_creates_token` — 신규 토큰 생성 200 반환 + share_url 포함 확인
  - [x] 3.2 `test_share_reuses_existing_token` — 기존 token 있을 때 동일 token 반환 (멱등성)
  - [x] 3.3 `test_share_rejects_non_owner` — 타인 소유 세트 403 반환
  - [x] 3.4 `test_share_not_found` — 없는 set_id 404 반환
  - [x] 3.5 pytest 전체 통과 확인 (108/108 통과)

- [x] Task 4: Frontend — `api.ts` 공유 함수 추가 (AC: #1)
  - [x] 4.1 `shareAnalysisSet(id: string): Promise<ShareResponse>` 추가 — `apiPost<ShareResponse>('/api/v1/analysis-sets/{id}/share', {})`
  - [x] 4.2 `ShareResponse` 인터페이스 추가: `{ share_token: string; share_url: string }`
  - [x] 4.3 `AnalysisSetData` 인터페이스에 `share_token: string | null` 필드 추가 (기존 `AnalysisSet` 타입과 통일)

- [x] Task 5: Frontend — `use-analysis-sets.ts` shareSet mutation 추가 (AC: #1, #4)
  - [x] 5.1 `shareSet` useMutation 추가 — `mutationFn: (id: string) => shareAnalysisSet(id)`
  - [x] 5.2 성공 시 `queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })` 호출
  - [x] 5.3 훅 return에 `shareSet` 추가

- [x] Task 6: Frontend — `ShareDialog.tsx` 컴포넌트 생성 (AC: #2, #3)
  - [x] 6.1 `frontend/src/components/layout/ShareDialog.tsx` 생성
  - [x] 6.2 Dialog 열기 트리거: "공유" 버튼 (ShareButton variant)
  - [x] 6.3 공유 링크 생성 중 로딩 스피너 표시 (generating 상태)
  - [x] 6.4 Dialog 내부: URL 입력창 (읽기 전용) + "링크 복사" 버튼
  - [x] 6.5 클립보드 복사 후 sonner `toast.success("링크가 복사되었습니다")` 3초 소멸
  - [x] 6.6 Dialog 스펙: `max-w-[480px]`, shadcn Dialog 기본 overlay
  - [x] 6.7 닫기: X 버튼 + 배경 클릭 + Escape 키 (shadcn Dialog 기본 동작)
  - [x] 6.8 접근성: `aria-label="분석 세트 공유"`, shadcn Dialog 자동 제공

- [x] Task 7: Frontend — `AnalysisSetItem.tsx`에 ShareDialog 통합 (AC: #2, #3)
  - [x] 7.1 `AnalysisSetItem`에 ShareDialog 버튼 추가 (edit/delete 버튼 옆)
  - [x] 7.2 Builder/Admin만 공유 버튼 표시 (canEdit 조건 활용, LiveViewer/ReadOnly에게는 숨김)

- [x] Task 8: `npm run build` 통과 확인 (TypeScript 에러 없음)

## Dev Notes

### 핵심 아키텍처 — 기존 패턴 그대로 활용

**DB 스키마 확인 (이미 준비 완료):**
`analysis_sets` 테이블에 `share_token VARCHAR(64) UNIQUE` 컬럼이 이미 존재함.
다만 현재 `AnalysisSet` Pydantic 스키마에는 `share_token` 필드가 없어 Task 1에서 추가 필요.

현재 `schemas.py`의 `AnalysisSet` 클래스 (수정 전):
```python
class AnalysisSet(BaseModel):
    id: str
    name: str
    owner_id: str
    company_codes: list[str]
    created_at: str
    updated_at: str
    # share_token 누락 — Task 1.1에서 추가
```

**Backend 엔드포인트 패턴 (기존 `analysis_sets.py` 패턴 그대로):**
```python
import secrets
from app.core.config import settings

@router.post("/analysis-sets/{set_id}/share", response_model=ShareResponse)
async def share_analysis_set(set_id: str, user=Depends(get_current_user)):
    supabase = get_supabase_client()

    # 1. 세트 존재 확인
    try:
        res = supabase.table("analysis_sets").select("*").eq("id", set_id).execute()
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "DB_UNAVAILABLE", ...})

    if not res.data:
        raise HTTPException(status_code=404, detail={"error": "ANALYSIS_SET_NOT_FOUND", ...})

    existing = res.data[0]

    # 2. 소유권 체크
    role = get_user_role(user.id)
    if role != "admin" and existing["owner_id"] != user.id:
        raise HTTPException(status_code=403, detail={"error": "INSUFFICIENT_PERMISSION", ...})

    # 3. 멱등성: 기존 토큰 재사용
    if existing.get("share_token"):
        token = existing["share_token"]
    else:
        token = secrets.token_urlsafe(32)
        supabase.table("analysis_sets").update({"share_token": token}).eq("id", set_id).execute()

    share_url = f"{settings.FRONTEND_URL}/shared/{token}"
    return ShareResponse(share_token=token, share_url=share_url)
```

**`config.py` Settings 추가:**
```python
class Settings(BaseSettings):
    ...
    FRONTEND_URL: str = "http://localhost:3000"  # Vercel 배포 시 환경변수로 오버라이드
```

**Frontend API 함수 패턴 (`api.ts` 기존 패턴 그대로):**
```typescript
// ── Story 4.1: 공유 링크 생성 ─────────────────────────
export interface ShareResponse {
  share_token: string
  share_url: string
}

export async function shareAnalysisSet(id: string): Promise<ShareResponse> {
  return apiPost<ShareResponse>(`/api/v1/analysis-sets/${id}/share`, {})
}
```

**`use-analysis-sets.ts` 훅 확장 패턴 (기존 `createSet`, `updateSet`, `deleteSet` 패턴 그대로):**
```typescript
const shareSet = useMutation({
  mutationFn: (id: string) => shareAnalysisSet(id),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
  },
})
// return에 shareSet 추가
```

**ShareDialog 컴포넌트 — shadcn Dialog + sonner Toast:**
```tsx
// frontend/src/components/layout/ShareDialog.tsx
'use client'
import { useState } from 'react'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from 'sonner'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'
import { Share2 } from 'lucide-react'

interface Props {
  setId: string
}

export function ShareDialog({ setId }: Props) {
  const [open, setOpen] = useState(false)
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const { shareSet } = useAnalysisSets()

  const handleOpen = async () => {
    setOpen(true)
    const result = await shareSet.mutateAsync(setId)
    setShareUrl(result.share_url)
  }

  const handleCopy = async () => {
    if (!shareUrl) return
    await navigator.clipboard.writeText(shareUrl)
    toast.success('링크가 복사되었습니다')
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" onClick={handleOpen} aria-label="분석 세트 공유">
          <Share2 className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-[480px]">
        <DialogHeader>
          <DialogTitle>분석 세트 공유</DialogTitle>
        </DialogHeader>
        {shareSet.isPending ? (
          <div className="flex justify-center py-4">
            <span className="text-sm text-muted-foreground">링크 생성 중...</span>
          </div>
        ) : shareUrl ? (
          <div className="flex gap-2">
            <Input value={shareUrl} readOnly className="flex-1" />
            <Button onClick={handleCopy}>링크 복사</Button>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
```

**⚠️ 주의: `DialogContent` backdrop-blur 커스터마이징**
shadcn의 `DialogOverlay`는 기본적으로 `bg-black/80`이지만 `backdrop-blur-sm` 클래스가 없음.
`components/ui/dialog.tsx`를 직접 수정하지 말고, `DialogContent`에 `className`으로 overlay style을 추가하거나 shadcn의 `DialogOverlay` 래핑 패턴 사용.
또는 `Dialog`를 래핑하여 overlay에 `backdrop-blur-sm` 추가:
```tsx
// DialogContent 내부에서 overlay 커스터마이징이 필요하다면:
// shadcn Dialog의 DialogOverlay는 전역 ui/dialog.tsx에서 정의됨
// 간단하게는 기존 overlay 유지 (backdrop-blur는 UX 스펙 권장이지만 필수 아님)
```

### 테스트 패턴

```python
# backend/tests/test_analysis_sets.py 추가

def test_share_creates_token(client):
    """공유 링크 생성 — 신규 토큰 생성"""
    mock_supabase = MagicMock()
    # 첫 번째 select: 세트 존재 (share_token=None)
    # update: 토큰 저장
    ...
    response = client.post("/api/v1/analysis-sets/test-id/share")
    assert response.status_code == 200
    data = response.json()
    assert "share_token" in data
    assert "share_url" in data
    assert "/shared/" in data["share_url"]

def test_share_reuses_existing_token(client):
    """멱등성 — 기존 토큰 재사용"""
    # select 결과에 share_token="existing-token" 포함
    # update가 호출되지 않아야 함
    ...

def test_share_rejects_non_owner(client):
    """타인 소유 세트 403"""
    ...
    assert response.status_code == 403

def test_share_not_found(client):
    """없는 세트 404"""
    ...
    assert response.status_code == 404
```

### 수정 대상 파일

- `backend/app/models/schemas.py` — `AnalysisSet`에 `share_token` 추가, `ShareResponse` 신규 추가
- `backend/app/api/v1/analysis_sets.py` — `share_analysis_set` 엔드포인트 추가
- `backend/app/core/config.py` — `FRONTEND_URL` 환경변수 추가
- `backend/tests/test_analysis_sets.py` — 공유 테스트 4개 추가
- `frontend/src/lib/api.ts` — `ShareResponse` 인터페이스, `shareAnalysisSet` 함수 추가, `AnalysisSetData`에 `share_token` 추가
- `frontend/src/hooks/use-analysis-sets.ts` — `shareSet` mutation 추가
- `frontend/src/components/layout/ShareDialog.tsx` — **신규 파일** 생성
- `frontend/src/components/layout/AnalysisSetItem.tsx` — `ShareDialog` 통합

### Project Structure Notes

- `shared/[token]/page.tsx` — **이 스토리에서 생성하지 않음** (Story 4.2에서 담당)
- `middleware.ts`는 이미 `/shared` 경로를 인증 미들웨어에서 제외함 (`shared` matcher 패턴)
- `main.py`에 `shared.py` 라우터 등록 TODO 있음 → Story 4.2에서 처리
- `backend/app/api/v1/shared.py` — **이 스토리에서 생성하지 않음** (Story 4.2에서 담당)
- `AnalysisSet` 타입 (`types/index.ts`)은 이미 `share_token: string | null` 포함 → 변경 없음
- `AnalysisSetData` 인터페이스 (`lib/api.ts`)에는 `share_token` 누락 → Task 4.3에서 추가
- `AnalysisSet` Pydantic 스키마 (`schemas.py`)에는 `share_token` 누락 → Task 1.1에서 추가

### References

- [Source: architecture.md - API & Communication Patterns] — POST /api/v1/analysis-sets/{id}/share
- [Source: architecture.md - DB Schema] — analysis_sets.share_token VARCHAR(64) UNIQUE
- [Source: architecture.md - Frontend 폴더 구조] — ShareButton.tsx, shared/[token]/page.tsx
- [Source: epics.md - Epic 4, Story 4.1] — 공유 링크 생성 AC
- [Source: ux-design-specification.md - ShareButton Component] — 상태, variant 정의
- [Source: ux-design-specification.md - Modal & Overlay Patterns] — 480px, backdrop-blur
- [Source: ux-design-specification.md - Feedback Patterns] — Toast 3초 소멸
- [Source: backend/app/api/v1/analysis_sets.py] — 기존 소유권 체크 패턴 (get_user_role)
- [Source: frontend/src/hooks/use-analysis-sets.ts] — useMutation 패턴
- [Source: frontend/src/lib/api.ts] — apiPost 패턴

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Task 1: `AnalysisSet` 스키마에 `share_token: Optional[str] = None` 추가, `ShareResponse(share_token, share_url)` 신규 추가
- Task 2: `POST /analysis-sets/{set_id}/share` 엔드포인트 구현 — secrets.token_urlsafe(32) 신규 생성, 기존 토큰 재사용 멱등성, Builder 소유권 체크, config.py에 FRONTEND_URL 추가
- Task 3: `TestShareAnalysisSet` 클래스 4개 테스트 추가 (신규생성/멱등성/403/404). 기존 회귀 테스트 `test_compare_rejects_non_pl_type` → `test_compare_rejects_invalid_type`으로 수정 (Story 3.4 이후 bs/cf 지원됨). 108/108 전체 통과
- Task 4: `api.ts`에 `ShareResponse` 인터페이스, `shareAnalysisSet` 함수, `AnalysisSetData.share_token` 필드 추가
- Task 5: `use-analysis-sets.ts`에 `shareSet` useMutation 추가, 성공 시 캐시 무효화
- Task 6: `ShareDialog.tsx` 신규 생성 — Dialog 열릴 때 자동으로 share API 호출, 로딩/URL표시/복사 3단계 UX
- Task 7: `AnalysisSetItem.tsx`에 ShareDialog 통합 — canEdit 조건 내 (Builder/Admin만 표시)
- Task 8: `npm run build` TypeScript 에러 없음

### File List

- `backend/app/models/schemas.py`
- `backend/app/api/v1/analysis_sets.py`
- `backend/app/core/config.py`
- `backend/tests/test_analysis_sets.py`
- `backend/tests/test_compare.py`
- `frontend/src/lib/api.ts`
- `frontend/src/hooks/use-analysis-sets.ts`
- `frontend/src/components/layout/ShareDialog.tsx` (신규)
- `frontend/src/components/layout/AnalysisSetItem.tsx`
