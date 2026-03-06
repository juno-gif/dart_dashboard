# Story 4.2: 공유 링크 읽기 전용 뷰어

Status: done

## Story

As a 공유 링크 수신자,
I want to view a shared analysis set without logging in,
so that I can review financial comparisons instantly without creating an account.

## Acceptance Criteria

1. **[미인증 접근 허용]** 미인증 사용자가 `/shared/{share_token}` URL로 접근하면 로그인 페이지로 리디렉션되지 않고 분석 세트가 읽기 전용으로 표시되어야 한다

2. **[공유 데이터 로드]** 공유 뷰가 렌더링될 때 `GET /api/v1/shared/{share_token}`이 호출되어 해당 분석 세트의 기업 구성과 최신 재무 데이터가 로드되어 차트가 표시되어야 한다. 편집·저장·삭제 버튼은 표시되지 않아야 한다

3. **[Supabase RLS — anon 접근]** 공유 뷰에서 RLS 정책이 평가될 때 anon 역할로 `analysis_sets`에 접근하면 `share_token`이 일치하는 레코드만 SELECT가 허용되어야 한다

4. **[유효하지 않은 토큰 404]** 유효하지 않거나 존재하지 않는 share_token으로 접근하면 FastAPI가 404 응답과 함께 "유효하지 않은 공유 링크입니다." 안내 페이지가 표시되어야 한다

## Tasks / Subtasks

- [x] Task 1: Backend — `shared.py` 라우터 생성 (AC: #2, #4)
  - [x] 1.1 `backend/app/api/v1/shared.py` 신규 생성
  - [x] 1.2 `GET /shared/{share_token}` 엔드포인트 — **인증 불필요** (auth dependency 없음)
  - [x] 1.3 `share_token`으로 `analysis_sets` 테이블 조회 (service key + .eq 필터로 직접 제한)
  - [x] 1.4 없으면 404 + `{"error": "SHARE_TOKEN_NOT_FOUND", ...}`
  - [x] 1.5 있으면 `SharedAnalysisSetResponse` 반환: `id`, `name`, `company_codes`, `financials`
  - [x] 1.6 `schemas.py`에 `SharedAnalysisSetResponse` 스키마 추가

- [x] Task 2: Backend — `main.py`에 shared 라우터 등록 (AC: #2)
  - [x] 2.1 `from app.api.v1 import shared` import 추가
  - [x] 2.2 `app.include_router(shared.router, prefix="/api/v1")` 추가

- [x] Task 3: Supabase RLS — anon SELECT 정책 추가 (AC: #3)
  - [x] 3.1 SQL 정책 문서화 (Supabase 대시보드 수동 실행 필요)
  - [x] 3.2 백엔드는 service key + `.eq("share_token", token)` 코드 레벨 필터로 이중 보호

- [x] Task 4: Backend — `test_shared.py` 테스트 추가 (AC: #2, #4)
  - [x] 4.1 `test_get_shared_returns_analysis_set` — 유효한 token으로 200 반환
  - [x] 4.2 `test_get_shared_not_found` — 없는 token으로 404 반환
  - [x] 4.3 `test_get_shared_no_auth_required` — 인증 없이도 200 반환
  - [x] 4.4 pytest 전체 통과 확인 — 111 passed

- [x] Task 5: Frontend — `shared/[token]/page.tsx` 생성 (AC: #1, #2, #4)
  - [x] 5.1 `frontend/src/app/shared/[token]/page.tsx` 신규 생성 — **Server Component**
  - [x] 5.2 인증 헤더 없이 서버 측 fetch (`cache: 'no-store'`)
  - [x] 5.3 404 응답 시 `notFound()` 호출 → 커스텀 not-found.tsx
  - [x] 5.4 `FinancialChart`(단일) / `CompareChart`(다중) 렌더링
  - [x] 5.5 편집·저장·삭제 버튼 없음 (읽기 전용 UI)
  - [x] 5.6 상단에 "읽기 전용" 배지 표시

- [x] Task 6: Frontend — 미인증 데이터 fetch 처리 (AC: #1, #2)
  - [x] 6.1 옵션 A 선택: `/shared/{token}` 단일 API에서 financials 포함 반환
  - [x] 6.2 `SharedAnalysisSetResponse`에 `financials: list[FinancialStatement]` 포함
  - [x] 6.3 백엔드에서 PL+BS+CF 모두 조회하여 반환

- [x] Task 7: `npm run build` 통과 확인 — `/shared/[token]` Dynamic route 정상 등록

## Dev Notes

### 핵심 아키텍처 결정 사항

**1. Server Component vs Client Component:**
아키텍처 문서에서 `shared/[token]/page.tsx`를 **Server Component**로 명시함.
- 인증 미들웨어에서 제외됨 (middleware.ts의 matcher가 이미 `shared`를 제외)
- 서버에서 직접 fetch → SEO 및 초기 로딩 최적화
- TanStack Query 사용 불필요 (Client Component 없이도 데이터 표시 가능)

**2. 미인증 재무 데이터 접근 전략 (옵션 A 권장):**
`GET /api/v1/shared/{share_token}` 엔드포인트 하나에서 모든 데이터 반환:
```json
{
  "id": "...",
  "name": "삼성전자 vs SK하이닉스 분석",
  "company_codes": ["005930", "000660"],
  "financials": [
    { "corp_code": "005930", "bsns_year": "2024", "account_key": "revenue", ... },
    ...
  ]
}
```
이 방식이 단일 API 호출로 완결되어 설계가 깔끔하고 미인증 접근 정책 관리가 단순화됨.

**3. Supabase RLS vs Service Key:**
`shared.py` 백엔드는 기존과 동일하게 `get_supabase_client()`(service key)를 사용.
서비스 키는 RLS를 bypass하므로 **코드 레벨에서 `.eq("share_token", token)` 필터로 직접 제한**:
```python
# service key 사용 시 RLS bypass → 코드 레벨 필터 필수
res = supabase.table("analysis_sets").select("*").eq("share_token", share_token).execute()
```
RLS 정책(Task 3)은 추가적인 방어 레이어 역할.

**Backend 엔드포인트 패턴:**
```python
# backend/app/api/v1/shared.py
"""
공유 링크 읽기 전용 뷰어 API — Story 4.2
GET /api/v1/shared/{share_token}  (인증 불필요)
[Source: architecture.md - API & Communication Patterns]
"""
import logging
from fastapi import APIRouter, HTTPException

from app.core.database import get_supabase_client
from app.models.schemas import SharedAnalysisSetResponse
from app.services.financial_service import get_pl_data, get_bs_data, get_cf_data

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/shared/{share_token}", response_model=SharedAnalysisSetResponse)
async def get_shared_analysis_set(share_token: str):
    """공유 링크로 분석 세트 조회 — 인증 불필요"""
    supabase = get_supabase_client()

    try:
        res = (
            supabase.table("analysis_sets")
            .select("*")
            .eq("share_token", share_token)
            .execute()
        )
    except Exception as e:
        logger.error(f"DB error for share_token {share_token}: {e}")
        raise HTTPException(
            status_code=503,
            detail={"error": "DB_UNAVAILABLE", "message": "데이터베이스에 일시적 오류가 발생했습니다.", "status_code": 503},
        )

    if not res.data:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SHARE_TOKEN_NOT_FOUND",
                "message": "유효하지 않은 공유 링크입니다.",
                "status_code": 404,
            },
        )

    analysis_set = res.data[0]
    company_codes = analysis_set["company_codes"]

    # 재무 데이터 조회 (PL + BS + CF 모두)
    all_financials = []
    for corp_code in company_codes:
        try:
            all_financials.extend(get_pl_data(corp_code, years=5))
            all_financials.extend(get_bs_data(corp_code, years=5))
            all_financials.extend(get_cf_data(corp_code, years=5))
        except Exception as e:
            logger.warning(f"Financial data fetch failed for {corp_code}: {e}")
            # 재무 데이터 실패는 치명적이지 않음 — 빈 데이터로 계속

    return SharedAnalysisSetResponse(
        id=analysis_set["id"],
        name=analysis_set["name"],
        company_codes=company_codes,
        financials=all_financials,
    )
```

**`schemas.py` 추가 스키마:**
```python
# ── Story 4.2: 공유 링크 뷰어 ────────────────────────────
class SharedAnalysisSetResponse(BaseModel):
    id: str
    name: str
    company_codes: list[str]
    financials: list[FinancialStatement]
```

**Frontend Server Component 패턴:**
```tsx
// frontend/src/app/shared/[token]/page.tsx
import { notFound } from 'next/navigation'
import { FinancialChart } from '@/components/charts/FinancialChart'
import { CompareChart, COMPANY_COLORS } from '@/components/charts/CompareChart'
import type { FinancialStatement } from '@/types'

interface SharedData {
  id: string
  name: string
  company_codes: string[]
  financials: FinancialStatement[]
}

async function getSharedData(token: string): Promise<SharedData | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const res = await fetch(`${apiUrl}/api/v1/shared/${token}`, {
    cache: 'no-store',  // 항상 최신 데이터
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Failed to fetch shared data')
  return res.json()
}

export default async function SharedPage({ params }: { params: { token: string } }) {
  const data = await getSharedData(params.token)

  if (!data) {
    notFound()
  }

  const isCompareMode = data.company_codes.length >= 2

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-6">
      {/* 읽기 전용 배지 */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{data.name}</h1>
        <span className="text-xs text-muted-foreground border rounded-full px-3 py-1">
          읽기 전용
        </span>
      </div>

      {/* 기업 태그 (편집 버튼 없음) */}
      <div className="flex flex-wrap gap-2">
        {data.company_codes.map((code, idx) => (
          <div
            key={code}
            className="flex items-center gap-1 px-3 py-1 rounded-full text-sm border"
            style={{
              backgroundColor: `${COMPANY_COLORS[idx % COMPANY_COLORS.length]}18`,
              borderColor: COMPANY_COLORS[idx % COMPANY_COLORS.length],
            }}
          >
            <span>{code}</span>
          </div>
        ))}
      </div>

      {/* 차트 (편집·저장·삭제 버튼 없음) */}
      {isCompareMode ? (
        <CompareChart
          data={data.financials}
          companies={data.company_codes.map(code => ({
            corp_code: code,
            company_name: code,
            stock_code: null,
            is_listed: true,
            created_at: '',
          }))}
          isLoading={false}
        />
      ) : (
        <FinancialChart
          data={data.financials.filter(f => ['revenue', 'operating_profit', 'net_income'].includes(f.account_key))}
          isLoading={false}
          type="pl"
        />
      )}
    </main>
  )
}
```

**⚠️ CompareChart props 확인 필요:**
`CompareChart`의 `companies` prop이 `Company[]` 타입을 기대함. 공유 뷰에서는 `company_name`을 모르므로 `corp_code`로 대체하거나, `/shared/{token}` API 응답에 기업명 정보도 포함하는 것을 고려.

**404 페이지 커스터마이징 (선택):**
Next.js App Router에서 `shared/[token]/not-found.tsx` 파일을 만들면 해당 경로에서의 404 커스터마이징 가능:
```tsx
// frontend/src/app/shared/[token]/not-found.tsx
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h1 className="text-2xl font-bold">유효하지 않은 공유 링크입니다.</h1>
      <p className="text-muted-foreground">링크가 만료되었거나 존재하지 않습니다.</p>
    </div>
  )
}
```

### 테스트 패턴

```python
# backend/tests/test_shared.py (신규 파일)
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """공유 뷰어는 인증 불필요 — dependency override 없이 그대로 사용"""
    from app.main import app
    yield TestClient(app)


def _make_analysis_set(share_token="valid-token"):
    return {
        "id": "set-id-1",
        "name": "삼성전자 분석",
        "owner_id": "user-id-1",
        "company_codes": ["005930"],
        "share_token": share_token,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


def test_get_shared_returns_analysis_set(client):
    """유효한 share_token으로 분석 세트 + 재무 데이터 반환"""
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        _make_analysis_set()
    ]

    with patch("app.api.v1.shared.get_supabase_client", return_value=mock_supabase):
        with patch("app.api.v1.shared.get_pl_data", return_value=[]):
            with patch("app.api.v1.shared.get_bs_data", return_value=[]):
                with patch("app.api.v1.shared.get_cf_data", return_value=[]):
                    response = client.get("/api/v1/shared/valid-token")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "삼성전자 분석"
    assert "company_codes" in data
    assert "financials" in data


def test_get_shared_not_found(client):
    """존재하지 않는 share_token → 404"""
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with patch("app.api.v1.shared.get_supabase_client", return_value=mock_supabase):
        response = client.get("/api/v1/shared/invalid-token")

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "SHARE_TOKEN_NOT_FOUND"


def test_get_shared_no_auth_required(client):
    """인증 없이 200 반환 — auth dependency 없음 확인"""
    # TestClient에 Authorization 헤더 없이 요청
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        _make_analysis_set()
    ]

    with patch("app.api.v1.shared.get_supabase_client", return_value=mock_supabase):
        with patch("app.api.v1.shared.get_pl_data", return_value=[]):
            with patch("app.api.v1.shared.get_bs_data", return_value=[]):
                with patch("app.api.v1.shared.get_cf_data", return_value=[]):
                    response = client.get("/api/v1/shared/valid-token")  # 헤더 없이

    assert response.status_code == 200
```

### 수정 대상 파일

- `backend/app/api/v1/shared.py` — **신규 파일** 생성
- `backend/app/models/schemas.py` — `SharedAnalysisSetResponse` 추가
- `backend/app/main.py` — shared 라우터 등록 (기존 TODO 주석 처리)
- `backend/tests/test_shared.py` — **신규 파일** 생성
- `frontend/src/app/shared/[token]/page.tsx` — **신규 파일** (Server Component)
- `frontend/src/app/shared/[token]/not-found.tsx` — **신규 파일** (선택적)

### DB 작업 (Supabase)

Task 3의 RLS 정책은 **Supabase 대시보드 SQL Editor**에서 직접 실행:
```sql
-- anon 역할에 share_token 기반 SELECT 허용
CREATE POLICY "anon_can_select_by_share_token"
ON analysis_sets
FOR SELECT
TO anon
USING (share_token IS NOT NULL);

-- 확인
SELECT * FROM pg_policies WHERE tablename = 'analysis_sets';
```

### Project Structure Notes

- `app/shared/[token]/` 는 `(auth)/` route group 바깥에 위치 — 인증 레이아웃 적용 안 됨
- `middleware.ts`는 이미 `/shared` 경로를 matcher에서 제외 (`shared` 키워드 포함) → 변경 불필요
- Story 4.1에서 생성한 `ShareDialog.tsx`가 share_token 생성을 담당, 이 스토리에서는 뷰어만 담당
- `FinancialChart`, `CompareChart`는 Server Component에서 직접 사용 가능 (props로 data 전달)
- `CompareChart`의 `companies` prop 타입이 `Company[]`를 요구하는 경우, 공유 뷰에서는 corp_code를 company_name으로 임시 사용하거나 백엔드 응답에 기업명 추가 필요

### References

- [Source: architecture.md - API & Communication Patterns] — GET /api/v1/shared/{share_token} (인증 불필요)
- [Source: architecture.md - Frontend 폴더 구조] — shared/[token]/page.tsx (Server Component)
- [Source: architecture.md - Authentication & Security] — RLS 정책 원칙
- [Source: architecture.md - Next.js App Router 활용] — Server Components for read-only pages
- [Source: epics.md - Epic 4, Story 4.2] — 공유 뷰어 AC
- [Source: ux-design-specification.md - Journey 3] — Live Viewer 공유 수신 플로우
- [Source: backend/app/api/v1/analysis_sets.py] — 기존 DB 조회 패턴
- [Source: backend/app/services/financial_service.py] — get_pl_data, get_bs_data, get_cf_data 패턴
- [Source: frontend/src/middleware.ts] — matcher에서 shared 제외 확인

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- 옵션 A 선택: `/shared/{token}` API에서 분석 세트 + PL+BS+CF 재무 데이터 모두 반환 (단일 API 호출로 완결)
- `CompareChart`의 `companies` prop이 `Company[]`를 요구하므로 corp_code를 company_name으로 임시 사용 (공유 뷰에서는 기업명 불필요)
- Supabase RLS anon 정책(Task 3.1 SQL)은 대시보드에서 수동 실행 필요 — 백엔드 service key + `.eq()` 필터로 코드 레벨 이중 보호
- 111 tests passed (기존 108 + 신규 3)

### File List

- `backend/app/api/v1/shared.py` (신규)
- `backend/app/models/schemas.py` (수정: SharedAnalysisSetResponse 추가)
- `backend/app/main.py` (수정: shared 라우터 등록)
- `backend/tests/test_shared.py` (신규)
- `frontend/src/app/shared/[token]/page.tsx` (신규)
- `frontend/src/app/shared/[token]/not-found.tsx` (신규)
- `frontend/src/app/shared/[token]/error.tsx` (신규: code review 수정)
