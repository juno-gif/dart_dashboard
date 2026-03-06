# Story 1.6: 차트 이미지 다운로드 및 시스템 안정성

Status: review

## Story

As a Builder,
I want to download charts as image files and see clear status messages when data is unavailable,
So that I can use charts in presentations and always understand the reliability of the data shown.

## Acceptance Criteria

1. **[차트 PNG 다운로드]** 차트가 렌더링된 상태에서 이미지 다운로드 버튼을 클릭하면, 현재 차트 영역이 PNG 파일로 다운로드되어야 한다. 파일명은 `{기업명}_{YYYY-MM-DD}.png` 형식이어야 한다

2. **[DART 장애 배너]** DART API가 장애 상태일 때 기업 데이터를 조회하면, FastAPI가 DB 캐시 데이터를 제공하면서 503 응답과 `DART_API_UNAVAILABLE` 에러 코드를 반환해야 한다. 프론트엔드 상단에 Yellow-100 배경 배너 "일부 데이터가 오래되었습니다 — 마지막 업데이트: N일 전"이 표시되어야 한다

3. **[미매핑 계정 로그]** account_mappings에 매핑이 없는 계정과목이 DART에서 수신될 때, 미매핑 계정과목은 DART 원본명 그대로 표시되고 FastAPI 서버 로그에 경고가 기록되어야 한다

4. **[네트워크 오류 Toast]** API 호출이 네트워크 오류로 실패할 때, TanStack Query 자동 재시도 3회 모두 실패하면 하단 우측에 Toast "잠시 후 재시도해 주세요"가 표시되어야 한다 (수동 닫기)

## Tasks / Subtasks

- [x] Task 1: Backend — DART 장애 graceful 처리 + 미매핑 계정 경고 로그 (AC: #2, #3)
  - [x] 1.1 `backend/app/services/financial_service.py` 수정: sync 실패 시 DB 캐시 데이터로 폴백 (`try/except`), DB도 비어 있으면 `DART_API_UNAVAILABLE` 503 raise
  - [x] 1.2 `backend/app/api/v1/financials.py` 수정: DART 장애 시 503 에러 응답에 `{"error": "DART_API_UNAVAILABLE", "message": "...", "cached_at": "<synced_at>", "status_code": 503}` 포함
  - [x] 1.3 `backend/app/services/dart_client.py` 수정: `sync_company_financials()` 내 미매핑 계정 감지 시 `logging.warning(f"Unmapped account: {account_nm} for {corp_code}/{bsns_year}")`
  - [x] 1.4 `backend/tests/test_dart_failure.py` 작성 및 pytest 통과 (5/5, 전체 36/36)

- [x] Task 2: Frontend — Toaster 설정 + 전역 에러 핸들러 (AC: #4)
  - [x] 2.1 `frontend/src/app/layout.tsx`에 `<Toaster />` 추가 (`@/components/ui/sonner`에서 import, `sonner` 패키지 이미 설치됨)
  - [x] 2.2 `frontend/src/app/providers.tsx` 수정: `QueryCache`에 전역 `onError` 추가 → `DART_API_UNAVAILABLE` 제외한 모든 에러에 `toast.error("잠시 후 재시도해 주세요", { duration: Infinity, dismissible: true })`

- [x] Task 3: Frontend — `DartWarningBanner` 컴포넌트 (AC: #2)
  - [x] 3.1 `frontend/src/components/layout/DartWarningBanner.tsx` 생성
  - [x] 3.2 `synced_at` 기준으로 "마지막 업데이트: N일 전" 계산 및 표시
  - [x] 3.3 에러가 `DART_API_UNAVAILABLE`일 때 OR `synced_at`이 7일 이상 지났을 때 표시
  - [x] 3.4 Yellow-100 배경 (`bg-yellow-100`), 상단 고정 배너 형태
  - [x] 3.5 `frontend/src/app/(auth)/dashboard/page.tsx`에 DartWarningBanner 통합

- [x] Task 4: Frontend — 차트 이미지 다운로드 (AC: #1)
  - [x] 4.1 `html2canvas` 패키지 설치 확인 (`npm install html2canvas`) — 설치 완료 (v1.4.1, 타입 내장)
  - [x] 4.2 `frontend/src/components/charts/DownloadButton.tsx` 생성: `ref`로 차트 영역 지정, `html2canvas`로 캡처 후 PNG 다운로드
  - [x] 4.3 파일명: `{기업명}_{YYYY-MM-DD}.png` (기업 1개: 기업명, 비교: 첫 기업명 기준)
  - [x] 4.4 `FinancialChart.tsx` 및 `CompareChart.tsx`에 `DownloadButton` 통합 (차트 우측 상단 버튼)
  - [x] 4.5 Next.js 빌드 통과 확인

## Dev Notes

### Backend Task 1: DART 장애 처리 패턴

**현재 구조 (`financial_service.py`):**
```python
def get_pl_data(corp_code: str, years: int = 5) -> list:
    rows = _query_pl(supabase, corp_code, years)
    if not rows:
        sync_company_financials(corp_code, years=years)  # ← 여기서 예외 발생 시 503
        rows = _query_pl(supabase, corp_code, years)
    return _prefer_cfs(rows, years)
```

**수정 후:**
```python
import logging
logger = logging.getLogger(__name__)

def get_pl_data(corp_code: str, years: int = 5) -> list:
    supabase = get_supabase_client()
    rows = _query_pl(supabase, corp_code, years)

    if not rows:
        try:
            sync_company_financials(corp_code, years=years)
            rows = _query_pl(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            # DB도 비어 있음 → 503 raise (caller에서 처리)
            raise  # 빈 rows + 예외 → 호출부에서 DART_API_UNAVAILABLE 처리

    return _prefer_cfs(rows, years)
```

**router 수정 (`financials.py`):**
```python
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@router.get("/companies/{corp_code}/financials", response_model=list[FinancialStatement])
async def get_financials(corp_code: str, years: int = 5, type: str = "pl"):
    if type != "pl":
        raise HTTPException(status_code=400, ...)
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, ...)
    try:
        data = get_pl_data(corp_code, years=years)
    except Exception as e:
        logger.error(f"DART API unavailable for {corp_code}: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DART_API_UNAVAILABLE",
                "message": "DART API에 일시적 오류가 발생했습니다. 나중에 다시 시도해 주세요.",
                "cached_at": None,
                "status_code": 503,
            },
        )
    return data
```

⚠️ compare 엔드포인트도 동일 패턴 적용 필요.

### Backend Task 1.3: 미매핑 계정 경고 (`dart_client.py`)

현재 코드:
```python
account_key = mappings.get(account_nm, account_nm)  # 미매핑 시 원본명 fallback
```

수정 후:
```python
import logging
logger = logging.getLogger(__name__)

account_key = mappings.get(account_nm)
if account_key is None:
    account_key = account_nm  # 원본명 그대로
    logger.warning(f"Unmapped account: '{account_nm}' for {corp_code}/{bsns_year}")
```

### Backend Task 1.4: test_dart_failure.py 패턴

```python
def test_dart_sync_failure_returns_503_when_db_empty(client):
    """DART 장애 + DB 빈 경우 503 + DART_API_UNAVAILABLE 반환"""
    mock_supabase = MagicMock()
    # DB 항상 빈 결과
    execute_mock = mock_supabase.table.return_value....execute
    execute_mock.return_value = MagicMock(data=[])

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials", side_effect=Exception("DART down")):
            response = client.get("/api/v1/companies/005930/financials?type=pl")

    assert response.status_code == 503
    body = response.json()
    assert body["detail"]["error"] == "DART_API_UNAVAILABLE"

def test_dart_sync_failure_returns_cached_when_db_has_data(client):
    """DART 장애여도 DB에 데이터 있으면 정상 반환 (sync 호출 안 됨)"""
    rows = _make_fin_rows(years=2)
    mock_supabase = _make_supabase_mock(rows)

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials") as mock_sync:
            response = client.get("/api/v1/companies/005930/financials?type=pl")

    assert response.status_code == 200
    mock_sync.assert_not_called()  # DB에 데이터 있으면 sync 안 함
```

### Frontend Task 2: Providers + Toaster 설정

**`layout.tsx` 수정:**
```tsx
import { Toaster } from '@/components/ui/sonner'
// ...
<Providers>
  {children}
  <Toaster position="bottom-right" />
</Providers>
```

**`providers.tsx` 수정 — QueryCache 전역 에러 핸들러:**
```tsx
import { QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { toast } from 'sonner'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error: unknown) => {
            const apiError = error as { error?: string; message?: string }
            // DART 장애는 배너로 처리 → Toast 제외
            if (apiError?.error === 'DART_API_UNAVAILABLE') return
            // 그 외 모든 에러 → Toast
            toast.error('잠시 후 재시도해 주세요', {
              duration: Infinity,
              dismissible: true,
            })
          },
        }),
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 3,
          },
        },
      })
  )
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
```

⚠️ `QueryCache`는 `@tanstack/react-query`에서 import. `toast`는 `sonner`에서 직접 import (훅 없이 사용 가능).

### Frontend Task 3: DartWarningBanner

```tsx
// frontend/src/components/layout/DartWarningBanner.tsx
'use client'
import type { FinancialStatement } from '@/types'

interface Props {
  data: FinancialStatement[]
  hasDartError: boolean
}

function getDaysAgo(dateStr: string): number {
  const diff = Date.now() - new Date(dateStr).getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24))
}

export function DartWarningBanner({ data, hasDartError }: Props) {
  // synced_at 기준으로 가장 최근 업데이트 날짜 계산
  const latestSyncedAt = data
    .map((d) => d.synced_at)
    .filter(Boolean)
    .sort()
    .reverse()[0]

  const daysAgo = latestSyncedAt ? getDaysAgo(latestSyncedAt) : null
  const isStale = hasDartError || (daysAgo !== null && daysAgo >= 7)

  if (!isStale) return null

  return (
    <div className="w-full bg-yellow-100 border border-yellow-300 px-4 py-2 text-sm text-yellow-800 rounded-lg">
      ⚠️ 일부 데이터가 오래되었습니다
      {daysAgo !== null && ` — 마지막 업데이트: ${daysAgo}일 전`}
    </div>
  )
}
```

**dashboard/page.tsx에서 hasDartError 전달:**
```tsx
const { data: financials = [], isLoading, error } = useFinancialData(...)
const hasDartError = (error as { error?: string })?.error === 'DART_API_UNAVAILABLE'

// JSX에서:
{(financials.length > 0 || hasDartError) && (
  <DartWarningBanner data={financials} hasDartError={hasDartError} />
)}
```

### Frontend Task 4: 차트 이미지 다운로드

**⚠️ 신규 패키지 필요:**
```bash
npm install html2canvas
npm install --save-dev @types/html2canvas
```
dev-story 시작 시 승인 후 설치.

**`DownloadButton.tsx` 패턴:**
```tsx
// frontend/src/components/charts/DownloadButton.tsx
'use client'
import { useState } from 'react'

interface Props {
  chartRef: React.RefObject<HTMLDivElement | null>
  filename: string  // 예: "삼성전자_2026-03-05"
}

export function DownloadButton({ chartRef, filename }: Props) {
  const [isCapturing, setIsCapturing] = useState(false)

  const handleDownload = async () => {
    if (!chartRef.current) return
    setIsCapturing(true)
    try {
      const html2canvas = (await import('html2canvas')).default
      const canvas = await html2canvas(chartRef.current, { backgroundColor: '#ffffff' })
      const link = document.createElement('a')
      link.download = `${filename}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    } finally {
      setIsCapturing(false)
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={isCapturing}
      className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded border border-gray-200 hover:border-gray-400 disabled:opacity-50"
      aria-label="차트 이미지 다운로드"
    >
      {isCapturing ? '캡처 중...' : '↓ PNG'}
    </button>
  )
}
```

**`FinancialChart.tsx` 수정 — ref + DownloadButton 통합:**
```tsx
interface Props {
  data: FinancialStatement[]
  isLoading: boolean
  companyName?: string  // 파일명용
}

export function FinancialChart({ data, isLoading, companyName }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)
  const today = new Date().toISOString().slice(0, 10)
  const filename = `${companyName ?? '차트'}_${today}`

  // ...
  return (
    <div>
      <div className="flex justify-end mb-1">
        <DownloadButton chartRef={chartRef} filename={filename} />
      </div>
      <div ref={chartRef} className="h-80 w-full">
        {/* 기존 차트 */}
      </div>
    </div>
  )
}
```

**`CompareChart.tsx` 수정 — 동일 패턴, `companies[0].company_name` 기준.**

### 아키텍처 준수 사항

- **Toast 규칙**: 오류 수동 닫기 (`duration: Infinity, dismissible: true`), 성공 3초 자동 소멸
- **에러 계층**: 503 DART → 배너, 그 외 API 오류 → Toast, 4xx → Inline (이번 스토리: 배너 + Toast)
- **formatKRW 단일 출처**: 이번 스토리에서 금액 표시 없음 (다운로드는 기존 차트 캡처)
- **snake_case**: API 에러 응답도 snake_case 필드명 유지
- **DART 격리**: 미매핑 로그는 `dart_client.py` 내에서만 추가 (다른 모듈 금지)
- **html2canvas**: dynamic import (`await import('html2canvas')`) — Next.js SSR 호환

### 기존 Story 1.4/1.5에서 재사용

- `FinancialChart.tsx`, `CompareChart.tsx` — ref + DownloadButton 추가
- `financial_service.py` — try/except 추가
- `providers.tsx` — QueryCache onError 추가
- `sonner` 패키지: 이미 설치됨 (`package.json` 확인 완료)
- `components/ui/sonner.tsx`: 이미 존재 (`<Toaster>` 컴포넌트)
- `Providers`에 QueryCache 추가 시 기존 `retry: 3` 설정 유지 필수

### 주의사항

- `useFinancialData`와 `useCompareFinancials` 훅의 `error` 타입은 `unknown` — 타입 캐스팅 필요
- `html2canvas`는 SSR에서 실행 불가 → `await import('html2canvas')` dynamic import 필수
- `@types/html2canvas`는 html2canvas 최신 버전에서 패키지 자체에 포함될 수 있음 — 설치 시 확인

### Project Structure Notes

**이번 스토리에서 신규 생성:**
- `backend/tests/test_dart_failure.py`
- `frontend/src/components/layout/DartWarningBanner.tsx`
- `frontend/src/components/charts/DownloadButton.tsx`

**이번 스토리에서 수정:**
- `backend/app/services/financial_service.py` — DART 장애 graceful 처리
- `backend/app/api/v1/financials.py` — DART_API_UNAVAILABLE 에러 응답 형식
- `backend/app/services/dart_client.py` — 미매핑 계정 경고 로그
- `frontend/src/app/layout.tsx` — Toaster 추가
- `frontend/src/app/providers.tsx` — QueryCache onError 추가
- `frontend/src/components/charts/FinancialChart.tsx` — ref + DownloadButton
- `frontend/src/components/charts/CompareChart.tsx` — ref + DownloadButton
- `frontend/src/app/(auth)/dashboard/page.tsx` — DartWarningBanner 통합

**의도적으로 이번 스토리에서 미구현:**
- Phase 3 PPT 다운로드 → Story 6.1
- 분석 세트 자동 갱신 스케줄 → Story 3.3

### References

- AC 출처: [epics.md - Story 1.6 차트 이미지 다운로드 및 시스템 안정성]
- 에러 처리 계층: [architecture.md - Error Handling Patterns]
- Toast 규칙: [architecture.md - Toast 피드백]
- DART 에러 형식: [architecture.md - 표준 에러 응답 형식]
- html2canvas: MVP 권장 [architecture.md - 이미지 다운로드 (FR27)]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- 백엔드 테스트 5/5, 전체 36/36 통과
- html2canvas 1.4.1 설치 (타입 내장, @types/html2canvas 별도 불필요)
- Next.js 빌드 TypeScript 에러 없이 통과

### File List

- backend/app/services/financial_service.py (수정)
- backend/app/api/v1/financials.py (수정)
- backend/app/services/dart_client.py (수정)
- backend/tests/test_dart_failure.py (신규)
- frontend/src/app/layout.tsx (수정)
- frontend/src/app/providers.tsx (수정)
- frontend/src/components/layout/DartWarningBanner.tsx (신규)
- frontend/src/components/charts/DownloadButton.tsx (신규)
- frontend/src/components/charts/FinancialChart.tsx (수정)
- frontend/src/components/charts/CompareChart.tsx (수정)
- frontend/src/app/(auth)/dashboard/page.tsx (수정)
