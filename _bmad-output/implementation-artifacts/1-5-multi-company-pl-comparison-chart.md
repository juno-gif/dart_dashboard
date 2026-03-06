# Story 1.5: 다중 기업 P&L 비교 차트

Status: review

## Story

As a Builder,
I want to add multiple companies and compare their P&L trends in a single view,
So that I can analyze competitive dynamics without switching between screens or manual data assembly.

## Acceptance Criteria

1. **[비교 차트 렌더링]** 기업 1개가 선택된 상태에서 추가 기업을 검색해 선택하면, CompanyTag가 추가되고 `GET /api/v1/companies/compare?codes=005930,035720&type=pl`이 호출되어 `CompareChart`가 렌더링되어야 한다

2. **[최대 5개 제한]** 기업이 5개 선택된 상태에서 추가 기업을 검색하려 하면 `CompanySearchInput`이 비활성화되고 "최대 5개 기업까지 비교 가능" 안내가 표시되어야 한다

3. **[실시간 업데이트]** CompanyTag의 X 버튼을 클릭하면 기업이 제거되고 비교 차트가 즉시 업데이트되어야 한다. 기업이 1개만 남으면 단일 기업 뷰(`KPICard` + `FinancialChart`)로 자동 전환되어야 한다

4. **[고유 색상 + 툴팁]** `CompareChart`에서 각 기업에 고유 색상이 할당되고, 호버 시 기업별 해당 연도 수치가 `formatKRW()` 형식으로 툴팁에 표시되어야 한다

## Tasks / Subtasks

- [x] Task 1: Backend — `GET /api/v1/companies/compare` 엔드포인트 구현 (AC: #1)
  - [x] 1.1 `backend/app/api/v1/financials.py`에 compare 라우터 추가: `GET /companies/compare?codes={codes}&years=5&type=pl`
  - [x] 1.2 `codes` 쿼리 파라미터: 콤마 구분 문자열 파싱 (예: `005930,035720`), 1~5개 코드 허용
  - [x] 1.3 각 corp_code에 대해 `get_pl_data()` 호출 → 결과 merge → `list[FinancialStatement]` 반환 (이미 corp_code 포함)
  - [x] 1.4 `backend/tests/test_compare.py` 작성 및 pytest 통과 (7/7, 전체 31/31)

- [x] Task 2: Frontend — `getCompareFinancials` API 함수 추가 (AC: #1)
  - [x] 2.1 `frontend/src/lib/api.ts`에 `getCompareFinancials(codes, years, type)` 함수 추가
  - [x] 2.2 querystring: `codes=005930,035720&years=5&type=pl` (codes는 sort → join(','))

- [x] Task 3: Frontend — `use-compare-financials.ts` 훅 생성 (AC: #1, #3)
  - [x] 3.1 `frontend/src/hooks/use-compare-financials.ts` 생성
  - [x] 3.2 TanStack Query `useQuery` 사용
  - [x] 3.3 queryKey: `['compare', sortedCodesStr, { years, type }]` — codes 정렬 후 join(',')로 일관성 보장
  - [x] 3.4 `enabled: codes.length >= 2` — 단일 기업 시 호출 안 함

- [x] Task 4: Frontend — `CompareChart.tsx` 컴포넌트 구현 (AC: #1, #4)
  - [x] 4.1 `frontend/src/components/charts/CompareChart.tsx` 생성
  - [x] 4.2 기업별 고유 색상 팔레트 (5색: `COMPANY_COLORS`): `['#2563eb', '#16a34a', '#9333ea', '#ea580c', '#0891b2']`
  - [x] 4.3 3개 LineChart 섹션 (매출·영업이익·순이익 각각): x=연도, 선=기업별, 고유 색상 할당
  - [x] 4.4 툴팁: 기업별 수치를 `formatKRW()` 형식으로, 범례: 기업명 표시
  - [x] 4.5 `isLoading` 시 shadcn `Skeleton` 3개 표시 (각 차트 동일 높이 `h-60`)
  - [x] 4.6 `formatKRW()` 경유 — 컴포넌트 내 직접 변환 금지

- [x] Task 5: Frontend — 대시보드 페이지 업데이트 (AC: #1, #2, #3)
  - [x] 5.1 `frontend/src/app/(auth)/dashboard/page.tsx` 업데이트
  - [x] 5.2 `selectedCompanies.length >= 2` → `CompareChart` 렌더링 (단일 뷰 숨김)
  - [x] 5.3 `selectedCompanies.length === 1` → 기존 `KPICard` + `FinancialChart` 유지
  - [x] 5.4 `selectedCompanies.length >= 5` → `CompanySearchInput`에 `disabled` prop 전달 + 안내 문구 표시
  - [x] 5.5 `CompanySearchInput`에 `disabled?: boolean` prop 추가 (Command 컴포넌트에 전달)
  - [x] 5.6 Next.js 빌드 통과 확인

## Dev Notes

### Backend: compare 엔드포인트 구현 패턴

기존 `financials.py`에 추가:

```python
# backend/app/api/v1/financials.py 에 추가
from typing import List

@router.get("/companies/compare", response_model=list[FinancialStatement])
async def compare_financials(
    codes: str,           # "005930,035720" — 콤마 구분
    years: int = 5,
    type: str = "pl",
):
    """다중 기업 P&L 비교 데이터 조회"""
    if type != "pl":
        raise HTTPException(status_code=400, detail="type=pl만 지원됩니다.")
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, detail="years는 1~10 사이여야 합니다.")

    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list or len(code_list) > 5:
        raise HTTPException(status_code=400, detail="codes는 1~5개여야 합니다.")

    all_data: list[dict] = []
    for corp_code in code_list:
        try:
            data = get_pl_data(corp_code, years=years)
            all_data.extend(data)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))
    return all_data
```

⚠️ **라우터 순서 주의**: FastAPI는 경로를 순서대로 매칭한다. `GET /companies/compare`는 `GET /companies/{corp_code}/financials`보다 먼저 등록되어야 한다 — `financials.py`에서 `/companies/compare` 라우터를 `/companies/{corp_code}/financials` **위에** 배치할 것.

### Backend: test_compare.py 패턴

```python
# backend/tests/test_compare.py
def test_compare_financials_returns_merged_data(client):
    """두 기업 codes로 요청 시 merge된 데이터 반환"""
    rows_a = _make_fin_rows("005930", years=2)
    rows_b = _make_fin_rows("035720", years=2)

    # 두 번 호출 대응 (각 기업별)
    mock_supabase = MagicMock()
    execute_mock = mock_supabase.table.return_value...execute
    execute_mock.side_effect = [
        MagicMock(data=rows_a),
        MagicMock(data=rows_b),
    ]
    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        response = client.get("/api/v1/companies/compare?codes=005930,035720&type=pl")
    assert response.status_code == 200
    assert len(response.json()) == len(rows_a) + len(rows_b)

def test_compare_rejects_more_than_5_codes(client):
    """6개 이상 codes 시 400 반환"""
    codes = ",".join(["000001"] * 6)
    response = client.get(f"/api/v1/companies/compare?codes={codes}&type=pl")
    assert response.status_code == 400

def test_compare_rejects_non_pl_type(client):
    response = client.get("/api/v1/companies/compare?codes=005930&type=bs")
    assert response.status_code == 400
```

### Frontend: api.ts 추가 함수

```typescript
// frontend/src/lib/api.ts 에 추가 (Story 1.5: 다중 기업 비교)
export async function getCompareFinancials(
  codes: string[],
  years = 5,
  type = 'pl'
): Promise<FinancialStatement[]> {
  const sortedCodes = [...codes].sort().join(',')
  return apiGet<FinancialStatement[]>(
    `/api/v1/companies/compare?codes=${encodeURIComponent(sortedCodes)}&years=${years}&type=${type}`
  )
}
```

### Frontend: use-compare-financials.ts 훅

```typescript
// frontend/src/hooks/use-compare-financials.ts
'use client'
import { useQuery } from '@tanstack/react-query'
import { getCompareFinancials } from '@/lib/api'
import type { FinancialStatement } from '@/types'

export function useCompareFinancials(
  codes: string[],
  years = 5,
  type = 'pl'
) {
  const sortedCodesStr = [...codes].sort().join(',')
  return useQuery<FinancialStatement[]>({
    queryKey: ['compare', sortedCodesStr, { years, type }],
    queryFn: () => getCompareFinancials(codes, years, type),
    enabled: codes.length >= 2,
    staleTime: 5 * 60_000,
  })
}
```

### Frontend: CompareChart.tsx 구조

```tsx
// frontend/src/components/charts/CompareChart.tsx
'use client'
import { Line, LineChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import { formatKRW } from '@/lib/format'
import type { Company, FinancialStatement } from '@/types'

const COMPANY_COLORS = ['#2563eb', '#16a34a', '#9333ea', '#ea580c', '#0891b2']

interface Props {
  data: FinancialStatement[]
  companies: Company[]
  isLoading: boolean
}

// 데이터 피벗: { year: '2024', '005930': 100억, '035720': 80억 }[]
function pivotByCompany(data: FinancialStatement[], accountKey: string, codes: string[]) {
  const years = [...new Set(data.map((d) => d.bsns_year))].sort()
  return years.map((year) => {
    const row: Record<string, string | number> = { year }
    for (const code of codes) {
      row[code] = data.find(
        (d) => d.bsns_year === year && d.corp_code === code && d.account_key === accountKey
      )?.amount ?? 0
    }
    return row
  })
}

export function CompareChart({ data, companies, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-60 w-full rounded-xl" />)}
      </div>
    )
  }

  const codes = companies.map((c) => c.corp_code)
  const metrics = [
    { key: 'revenue', label: '매출 비교' },
    { key: 'operating_profit', label: '영업이익 비교' },
    { key: 'net_income', label: '순이익 비교' },
  ]

  return (
    <div className="space-y-8">
      {metrics.map(({ key, label }) => {
        const chartData = pivotByCompany(data, key, codes)
        return (
          <div key={key}>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">{label}</h3>
            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                  <YAxis tickFormatter={(v: number) => formatKRW(v)} width={80} tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(value: number | undefined, name: string | undefined) => [
                      value != null ? formatKRW(value) : '-',
                      companies.find((c) => c.corp_code === name)?.company_name ?? name,
                    ]}
                  />
                  <Legend
                    formatter={(value: string) =>
                      companies.find((c) => c.corp_code === value)?.company_name ?? value
                    }
                  />
                  {codes.map((code, idx) => (
                    <Line
                      key={code}
                      dataKey={code}
                      stroke={COMPANY_COLORS[idx % COMPANY_COLORS.length]}
                      strokeWidth={2}
                      dot
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )
      })}
    </div>
  )
}
```

### Frontend: dashboard/page.tsx 업데이트 패턴

```tsx
'use client'
import { useState } from 'react'
import { CompanySearchInput } from '@/components/search/CompanySearchInput'
import { KPICard } from '@/components/charts/KPICard'
import { FinancialChart } from '@/components/charts/FinancialChart'
import { CompareChart } from '@/components/charts/CompareChart'
import { useFinancialData } from '@/hooks/use-financial-data'
import { useCompareFinancials } from '@/hooks/use-compare-financials'
import type { Company } from '@/types'

const MAX_COMPANIES = 5

export default function DashboardPage() {
  const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([])
  const isCompareMode = selectedCompanies.length >= 2
  const isAtMax = selectedCompanies.length >= MAX_COMPANIES
  const primaryCompany = selectedCompanies[0] ?? null

  // 단일 기업 훅
  const { data: financials = [], isLoading: singleLoading } = useFinancialData(
    !isCompareMode ? (primaryCompany?.corp_code ?? null) : null
  )

  // 비교 훅
  const { data: compareData = [], isLoading: compareLoading } = useCompareFinancials(
    isCompareMode ? selectedCompanies.map((c) => c.corp_code) : []
  )

  const handleSelect = (company: Company) => {
    if (isAtMax) return
    if (!selectedCompanies.find((c) => c.corp_code === company.corp_code)) {
      setSelectedCompanies((prev) => [...prev, company])
    }
  }

  const handleRemove = (corp_code: string) => {
    setSelectedCompanies((prev) => prev.filter((c) => c.corp_code !== corp_code))
  }

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold">재무 분석 대시보드</h1>

      {/* 검색 (5개 도달시 비활성화) */}
      <div className="space-y-1">
        <CompanySearchInput onSelect={handleSelect} disabled={isAtMax} />
        {isAtMax && (
          <p className="text-xs text-muted-foreground px-1">최대 5개 기업까지 비교 가능</p>
        )}
      </div>

      {/* CompanyTag 목록 */}
      <div className="flex flex-wrap gap-2">
        {selectedCompanies.map((c, idx) => (
          <div
            key={c.corp_code}
            className="flex items-center gap-1 px-3 py-1 rounded-full text-sm"
            style={{ backgroundColor: `${COMPANY_COLORS[idx % 5]}20`, borderColor: COMPANY_COLORS[idx % 5], borderWidth: 1 }}
          >
            <span>{c.company_name}</span>
            {c.stock_code && <span className="text-xs text-gray-500 ml-1">{c.stock_code}</span>}
            <button onClick={() => handleRemove(c.corp_code)} className="ml-1 text-gray-400 hover:text-gray-600" aria-label={`${c.company_name} 제거`}>×</button>
          </div>
        ))}
      </div>

      {/* 뷰 전환 */}
      {isCompareMode ? (
        <CompareChart data={compareData} companies={selectedCompanies} isLoading={compareLoading} />
      ) : primaryCompany ? (
        <>
          <KPICard data={financials} isLoading={singleLoading} />
          <FinancialChart data={financials} isLoading={singleLoading} />
        </>
      ) : (
        <p className="text-gray-400 text-center text-sm mt-16">기업을 검색하여 추가하세요.</p>
      )}
    </main>
  )
}
```

⚠️ `COMPANY_COLORS` 상수는 `CompareChart.tsx`와 `dashboard/page.tsx` 양쪽에서 사용한다. 중복 방지를 위해 `frontend/src/lib/constants.ts`에 추출하거나, CompareChart에서 import하는 방식을 선택할 것 (둘 중 하나 선택하여 일관성 유지, 추출 권장).

### Frontend: CompanySearchInput disabled prop 추가

```tsx
// frontend/src/components/search/CompanySearchInput.tsx 수정
interface Props {
  onSelect: (company: Company) => void
  disabled?: boolean  // ← 추가
}

export function CompanySearchInput({ onSelect, disabled }: Props) {
  // ...
  return (
    <Command role="combobox" aria-autocomplete="list" aria-expanded={results.length > 0}>
      <CommandInput
        placeholder="기업명 입력 (예: 삼성전자, 카카오)"
        value={query}
        onValueChange={disabled ? undefined : setQuery}  // disabled시 입력 차단
        disabled={disabled}
        className={disabled ? 'cursor-not-allowed opacity-50' : ''}
      />
      {!disabled && (
        <CommandList>
          {/* 기존 목록 */}
        </CommandList>
      )}
    </Command>
  )
}
```

### 아키텍처 준수 사항

- **라우터 순서**: `/companies/compare`를 `/companies/{corp_code}/financials` **위에** 배치 — FastAPI 경로 매칭 순서 의존
- **formatKRW 단일 출처**: CompareChart 내 직접 변환 금지 → `frontend/src/lib/format.ts`만 사용
- **API 호출 레이어**: 컴포넌트 내 직접 fetch 금지 → `lib/api.ts` 경유 필수
- **쿼리키 일관성**: codes는 항상 sort() 후 join(',') — 순서가 달라도 같은 캐시 사용
- **snake_case**: API 응답·TypeScript 타입 모두 snake_case (corp_code, bsns_year 등)
- **Python 3.9**: `Optional[str]` 사용, `list[dict]` 타입힌트는 런타임 OK
- **DART API 격리**: financial_service.py에서 직접 DART 호출 금지 — sync_company_financials() 경유

### 기존 Story 1.4에서 재사용

- `get_pl_data()` — financial_service.py (그대로 재사용)
- `_prefer_cfs()` — financial_service.py (그대로 재사용)
- `formatKRW()`, `formatPercent()` — lib/format.ts
- `FinancialStatement` TypeScript 타입 — types/index.ts (corp_code 필드 이미 포함 확인 필요)
- `useFinancialData` 훅 — 단일 기업 뷰에서 계속 사용
- `KPICard`, `FinancialChart` 컴포넌트 — 단일 기업 뷰에서 계속 사용

### TypeScript 타입 확인 필요

Story 1-5 구현 전 `frontend/src/types/index.ts`에서 `FinancialStatement` 타입의 `corp_code` 필드 존재 여부 확인:

```typescript
// 필요 시 추가
export interface FinancialStatement {
  id: string
  corp_code: string  // ← 비교 차트에서 필수
  bsns_year: string
  account_key: string
  account_nm: string
  amount: number
  fs_div: string
  reprt_code: string
  synced_at: string
}
```

### Project Structure Notes

**이번 스토리에서 신규 생성:**
- `backend/tests/test_compare.py`
- `frontend/src/hooks/use-compare-financials.ts`
- `frontend/src/components/charts/CompareChart.tsx`
- `frontend/src/lib/constants.ts` (COMPANY_COLORS 추출 시)

**이번 스토리에서 수정:**
- `backend/app/api/v1/financials.py` — compare 라우터 추가
- `frontend/src/lib/api.ts` — getCompareFinancials 추가
- `frontend/src/components/search/CompanySearchInput.tsx` — disabled prop 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — 비교 모드 통합

**의도적으로 이번 스토리에서 미구현:**
- 비교 KPI 카드 (기업 간 수치 나란히 비교 테이블) → 별도 기능으로 추가 가능
- 매출/영업이익/순이익 탭 전환 UI → 기본 3섹션 레이아웃으로 대체
- 차트 이미지 다운로드 → Story 1.6에서 구현

### References

- API 설계: [architecture.md - API & Communication Patterns] - `GET /api/v1/companies/compare?codes=...&type=pl`
- 컴포넌트 구조: [architecture.md - Frontend 디렉토리 구조]
- Story 1.4 패턴: [1-4-single-company-pl-chart-and-kpi.md] - get_pl_data, FinancialChart, formatKRW 패턴
- TanStack Query 키: [architecture.md - TanStack Query 쿼리 키 규칙]
- AC 출처: [epics.md - Story 1.5 다중 기업 P&L 비교 차트]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- `CompanySearchInput`에 `disabled` prop 추가 시 CommandList도 조건부 렌더링 필요 (`{!disabled && <CommandList>...</CommandList>}`)
- `COMPANY_COLORS`를 `CompareChart.tsx`에서 export하여 `dashboard/page.tsx`에서 CompanyTag 색상에 재사용 (constants.ts 별도 파일 불필요)
- Recharts `Tooltip formatter` 타입: `(value: number | undefined, name: string | undefined)` — Story 1.4에서 확인된 패턴 적용

### File List

- backend/app/api/v1/financials.py (modified — compare 라우터 추가)
- backend/tests/test_compare.py (new)
- frontend/src/lib/api.ts (modified — getCompareFinancials 추가)
- frontend/src/hooks/use-compare-financials.ts (new)
- frontend/src/components/charts/CompareChart.tsx (new)
- frontend/src/components/search/CompanySearchInput.tsx (modified — disabled prop 추가)
- frontend/src/app/(auth)/dashboard/page.tsx (modified — 비교 모드 통합)
