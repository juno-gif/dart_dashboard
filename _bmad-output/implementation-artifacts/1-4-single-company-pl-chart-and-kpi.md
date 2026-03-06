# Story 1.4: 단일 기업 P&L 차트 및 KPI 카드

Status: review

## Story

As a Builder,
I want to see a 5-year P&L trend chart and key financial KPI cards after selecting a company,
So that I can immediately understand financial performance without manual data assembly.

## Acceptance Criteria

1. **[P&L 차트 렌더링]** Builder가 CompanySearchInput에서 기업을 선택하면, 대시보드 메인 영역에 해당 기업의 최근 5년치 매출·영업이익·순이익 데이터가 `FinancialChart`에 표시되어야 한다. KPICard 4개(매출·영업이익·순이익·영업이익률)가 최신 연도 기준으로 표시되어야 한다

2. **[API 응답 1초 이내]** `GET /api/v1/companies/{corp_code}/financials?years=5&type=pl` 호출 시 DB에서 1초 이내에 snake_case JSON으로 응답해야 한다. 금액은 원 단위 BIGINT로 응답하고 프론트엔드에서 `formatKRW()`로만 변환되어야 한다 (컴포넌트 내 직접 변환 금지)

3. **[스켈레톤 로딩]** 데이터 로딩 중일 때 KPICard와 FinancialChart에 실제 컴포넌트와 동일한 높이의 Skeleton이 표시되어야 한다 (레이아웃 쉬프트 없음)

4. **[증감률 색상]** KPICard에 전년 대비 증감률이 표시될 때, 양수이면 `▲ text-green-600`, 음수이면 `▼ text-red-500`으로 표시되어야 한다

## Tasks / Subtasks

- [x] Task 1: Backend — `GET /api/v1/companies/{corp_code}/financials` 엔드포인트 구현 (AC: #1, #2)
  - [x] 1.1 `backend/app/services/financial_service.py` 생성: DB에서 financial_statements 조회, 없으면 sync 후 재조회
  - [x] 1.2 `backend/app/api/v1/financials.py` 생성: `GET /api/v1/companies/{corp_code}/financials?years=5&type=pl`
  - [x] 1.3 `type=pl` 필터: account_key IN (`revenue`, `operating_profit`, `net_income`) 또는 account_nm category='pl'
  - [x] 1.4 `main.py`에 financials 라우터 등록
  - [x] 1.5 `backend/tests/test_financials.py` 작성 및 pytest 통과 (6/6)

- [x] Task 2: Frontend — `format.ts` 유틸 생성 (AC: #2)
  - [x] 2.1 `frontend/src/lib/format.ts` 생성
  - [x] 2.2 `formatKRW(amount: number): string` 구현 (조/억/백만 단위 변환)
  - [x] 2.3 `formatPercent(value: number): string` 구현 (소수점 1자리 %)

- [x] Task 3: Frontend — `getFinancials` 함수 및 훅 구현 (AC: #1, #3)
  - [x] 3.1 `frontend/src/lib/api.ts`에 `getFinancials(corpCode, years, type)` 함수 추가
  - [x] 3.2 `frontend/src/hooks/use-financial-data.ts` 생성
  - [x] 3.3 TanStack Query `useQuery` 사용, queryKey: `['financials', corpCode, { years, type }]`
  - [x] 3.4 `enabled: !!corpCode` — 기업 미선택 시 호출 안 함

- [x] Task 4: Frontend — `KPICard` 컴포넌트 구현 (AC: #1, #4)
  - [x] 4.1 `frontend/src/components/charts/KPICard.tsx` 생성
  - [x] 4.2 4개 카드: 매출·영업이익·순이익·영업이익률
  - [x] 4.3 전년 대비 증감률: ▲ `text-green-600`, ▼ `text-red-500`
  - [x] 4.4 `isLoading` 시 shadcn `Skeleton` 표시 (동일 높이 유지)
  - [x] 4.5 `formatKRW()` 경유 — 컴포넌트 내 직접 변환 금지

- [x] Task 5: Frontend — `FinancialChart` 컴포넌트 구현 (AC: #1, #3)
  - [x] 5.1 `frontend/src/components/charts/FinancialChart.tsx` 생성
  - [x] 5.2 Recharts `ComposedChart` 기반 — x축: 연도, y축: 금액
  - [x] 5.3 3개 계열: 매출(Bar), 영업이익(Line), 순이익(Line) — 고유 색상 할당
  - [x] 5.4 툴팁: 호버 시 `formatKRW()` 형식으로 수치 표시
  - [x] 5.5 `isLoading` 시 shadcn `Skeleton` 표시 (차트와 동일 높이)

- [x] Task 6: Frontend — 대시보드 페이지 통합 (AC: #1, #3)
  - [x] 6.1 `frontend/src/app/(auth)/dashboard/page.tsx` 업데이트
  - [x] 6.2 기업 선택 시 `KPICard` 4개 + `FinancialChart` 렌더링
  - [x] 6.3 기업 미선택 시 "기업을 검색하여 추가하세요" 빈 상태 유지
  - [x] 6.4 Next.js 빌드 통과 확인

## Dev Notes

### Backend: financial_service.py 구현 패턴

```python
# backend/app/services/financial_service.py
from typing import Optional
from app.core.database import get_supabase_client
from app.services.dart_client import sync_company_financials

PL_ACCOUNT_KEYS = {"revenue", "operating_profit", "net_income"}

def get_pl_data(corp_code: str, years: int = 5) -> list[dict]:
    """DB-First P&L 조회: DB 없으면 DART sync 후 재조회"""
    supabase = get_supabase_client()

    res = (
        supabase.table("financial_statements")
        .select("*")
        .eq("corp_code", corp_code)
        .in_("account_key", list(PL_ACCOUNT_KEYS))
        .order("bsns_year", desc=True)
        .limit(years * len(PL_ACCOUNT_KEYS) * 2)  # CFS/OFS 대비 버퍼
        .execute()
    )

    if not res.data:
        # DART에서 sync 후 재조회
        sync_company_financials(corp_code, years=years)
        res = (
            supabase.table("financial_statements")
            .select("*")
            .eq("corp_code", corp_code)
            .in_("account_key", list(PL_ACCOUNT_KEYS))
            .order("bsns_year", desc=True)
            .limit(years * len(PL_ACCOUNT_KEYS) * 2)
            .execute()
        )

    # CFS 우선, 없으면 OFS 선택
    rows = res.data or []
    return _prefer_cfs(rows, years)


def _prefer_cfs(rows: list[dict], years: int) -> list[dict]:
    """동일 연도+계정에 CFS/OFS 둘 다 있으면 CFS 선택"""
    from collections import defaultdict
    best: dict[tuple, dict] = {}
    for row in rows:
        key = (row["bsns_year"], row["account_key"])
        existing = best.get(key)
        if existing is None or (row["fs_div"] == "CFS" and existing["fs_div"] != "CFS"):
            best[key] = row
    result = sorted(best.values(), key=lambda r: r["bsns_year"], reverse=True)
    # 최근 N개 연도만 추출
    years_seen: set = set()
    filtered = []
    for row in result:
        years_seen.add(row["bsns_year"])
        if len(years_seen) <= years:
            filtered.append(row)
    return filtered
```

### Backend: financials.py 라우터

```python
# backend/app/api/v1/financials.py
from typing import Optional
from fastapi import APIRouter, HTTPException
from app.models.schemas import FinancialStatement
from app.services.financial_service import get_pl_data

router = APIRouter()

@router.get("/companies/{corp_code}/financials", response_model=list[FinancialStatement])
async def get_financials(
    corp_code: str,
    years: int = 5,
    type: str = "pl",
):
    """기업 재무 데이터 조회 (DB-First, type=pl만 지원 — bs/cf는 Story 3.4/3.5)"""
    if type != "pl":
        raise HTTPException(status_code=400, detail="type=pl만 지원됩니다 (bs/cf는 Epic 3에서 구현)")
    try:
        data = get_pl_data(corp_code, years=years)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    return data
```

### Backend: main.py 라우터 추가

```python
from app.api.v1 import companies, financials, health, sync
app.include_router(financials.router, prefix="/api/v1")
```

### Frontend: format.ts 구현

```typescript
// frontend/src/lib/format.ts
export function formatKRW(amount: number): string {
  const abs = Math.abs(amount)
  const sign = amount < 0 ? '-' : ''
  if (abs >= 1_000_000_000_000) return `${sign}₩${(abs / 1e12).toFixed(1)}조`
  if (abs >= 100_000_000) return `${sign}₩${(abs / 1e8).toFixed(0)}억`
  if (abs >= 1_000_000) return `${sign}₩${(abs / 1e6).toFixed(1)}백만`
  return `${sign}₩${abs.toLocaleString()}`
}

export function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}
```

### Frontend: api.ts 추가 함수

```typescript
// frontend/src/lib/api.ts 에 추가
import type { FinancialStatement } from '@/types'

export async function getFinancials(
  corpCode: string,
  years = 5,
  type = 'pl'
): Promise<FinancialStatement[]> {
  return apiGet<FinancialStatement[]>(
    `/api/v1/companies/${corpCode}/financials?years=${years}&type=${type}`
  )
}
```

### Frontend: use-financial-data.ts 훅

```typescript
// frontend/src/hooks/use-financial-data.ts
'use client'
import { useQuery } from '@tanstack/react-query'
import { getFinancials } from '@/lib/api'
import type { FinancialStatement } from '@/types'

export function useFinancialData(corpCode: string | null, years = 5, type = 'pl') {
  return useQuery<FinancialStatement[]>({
    queryKey: ['financials', corpCode, { years, type }],
    queryFn: () => getFinancials(corpCode!, years, type),
    enabled: !!corpCode,
    staleTime: 5 * 60_000, // 5분 캐시
  })
}
```

### Frontend: KPICard 컴포넌트

```tsx
// frontend/src/components/charts/KPICard.tsx
'use client'
import { Skeleton } from '@/components/ui/skeleton'
import { formatKRW, formatPercent } from '@/lib/format'
import type { FinancialStatement } from '@/types'

interface Props {
  data: FinancialStatement[]
  isLoading: boolean
}

function calcYoY(current?: number, prev?: number): number | null {
  if (current == null || prev == null || prev === 0) return null
  return ((current - prev) / Math.abs(prev)) * 100
}

export function KPICard({ data, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
    )
  }

  // 최신 2개 연도 추출
  const years = [...new Set(data.map((d) => d.bsns_year))].sort().reverse()
  const latestYear = years[0]
  const prevYear = years[1]

  const get = (year: string, key: string) =>
    data.find((d) => d.bsns_year === year && d.account_key === key)?.amount ?? null

  const revenue = get(latestYear, 'revenue')
  const opProfit = get(latestYear, 'operating_profit')
  const netIncome = get(latestYear, 'net_income')
  const opMargin = revenue && opProfit ? (opProfit / revenue) * 100 : null

  const prevRevenue = get(prevYear, 'revenue')
  const prevOpProfit = get(prevYear, 'operating_profit')
  const prevNetIncome = get(prevYear, 'net_income')

  const cards = [
    { label: '매출', value: revenue != null ? formatKRW(revenue) : '-', yoy: calcYoY(revenue, prevRevenue) },
    { label: '영업이익', value: opProfit != null ? formatKRW(opProfit) : '-', yoy: calcYoY(opProfit, prevOpProfit) },
    { label: '순이익', value: netIncome != null ? formatKRW(netIncome) : '-', yoy: calcYoY(netIncome, prevNetIncome) },
    { label: '영업이익률', value: opMargin != null ? `${opMargin.toFixed(1)}%` : '-', yoy: null },
  ]

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="rounded-xl border bg-card p-4 shadow-sm">
          <p className="text-sm text-muted-foreground">{card.label}</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{card.value}</p>
          {card.yoy != null && (
            <p className={`mt-1 text-xs ${card.yoy >= 0 ? 'text-green-600' : 'text-red-500'}`}>
              {card.yoy >= 0 ? '▲' : '▼'} {formatPercent(Math.abs(card.yoy))} 전년 대비
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
```

### Frontend: FinancialChart 컴포넌트

```tsx
// frontend/src/components/charts/FinancialChart.tsx
'use client'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import { formatKRW } from '@/lib/format'
import type { FinancialStatement } from '@/types'

interface Props {
  data: FinancialStatement[]
  isLoading: boolean
}

export function FinancialChart({ data, isLoading }: Props) {
  if (isLoading) {
    return <Skeleton className="h-80 w-full rounded-xl" />
  }

  // 연도별 피벗
  const years = [...new Set(data.map((d) => d.bsns_year))].sort()
  const chartData = years.map((year) => {
    const get = (key: string) =>
      data.find((d) => d.bsns_year === year && d.account_key === key)?.amount ?? 0
    return {
      year,
      revenue: get('revenue'),
      operating_profit: get('operating_profit'),
      net_income: get('net_income'),
    }
  })

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis tickFormatter={(v) => formatKRW(v)} width={80} />
          <Tooltip formatter={(value: number) => formatKRW(value)} />
          <Legend />
          <Bar dataKey="revenue" name="매출" fill="#2563eb" opacity={0.7} />
          <Line dataKey="operating_profit" name="영업이익" stroke="#16a34a" strokeWidth={2} dot />
          <Line dataKey="net_income" name="순이익" stroke="#9333ea" strokeWidth={2} dot />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
```

### Frontend: 대시보드 페이지 통합 패턴

```tsx
// frontend/src/app/(auth)/dashboard/page.tsx 업데이트
'use client'
import { useState } from 'react'
import { CompanySearchInput } from '@/components/search/CompanySearchInput'
import { KPICard } from '@/components/charts/KPICard'
import { FinancialChart } from '@/components/charts/FinancialChart'
import { useFinancialData } from '@/hooks/use-financial-data'
import type { Company } from '@/types'

export default function DashboardPage() {
  const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([])
  const primaryCompany = selectedCompanies[0] ?? null

  const { data: financials = [], isLoading } = useFinancialData(
    primaryCompany?.corp_code ?? null
  )

  const handleSelect = (company: Company) => {
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

      {/* 검색 + CompanyTag */}
      <CompanySearchInput onSelect={handleSelect} />
      <div className="flex flex-wrap gap-2">
        {selectedCompanies.map((c) => (
          <div key={c.corp_code} className="flex items-center gap-1 px-3 py-1 bg-blue-100 rounded-full text-sm">
            <span>{c.company_name}</span>
            {c.stock_code && <span className="text-xs text-gray-500 ml-1">{c.stock_code}</span>}
            <button onClick={() => handleRemove(c.corp_code)} className="ml-1 text-gray-400 hover:text-gray-600" aria-label={`${c.company_name} 제거`}>×</button>
          </div>
        ))}
      </div>

      {/* KPI + 차트 */}
      {primaryCompany ? (
        <>
          <KPICard data={financials} isLoading={isLoading} />
          <FinancialChart data={financials} isLoading={isLoading} />
        </>
      ) : (
        <p className="text-gray-400 text-center text-sm mt-16">기업을 검색하여 추가하세요.</p>
      )}
    </main>
  )
}
```

### 아키텍처 준수 사항

- **DB-First**: `financial_statements` 테이블 먼저 조회 → 없으면 `sync_company_financials()` 호출 후 재조회
- **CFS 우선**: 동일 연도+계정에 연결재무제표(CFS)와 개별재무제표(OFS)가 공존 시 CFS 선택
- **formatKRW 단일 출처**: 컴포넌트 내 직접 변환 절대 금지 → `frontend/src/lib/format.ts`만 사용
- **dart_client 격리**: `financial_service.py`에서 직접 OpenDartReader import 금지 — `sync_company_financials()` 경유
- **snake_case**: API 응답·타입 모두 `corp_code`, `bsns_year`, `account_key` (camelCase 금지)
- **Python 3.9**: `str | None` 대신 `Optional[str]`, 타입힌트 `list[dict]`는 런타임 OK
- **TanStack Query 키**: `['financials', corpCode, { years, type }]` — 아키텍처 문서 정의 준수

### P&L Account Key 필터 기준

DB에 저장된 `account_key`는 `account_mappings`를 통해 표준화됨:
- `revenue` — 매출액 (DART: 매출액, 수익(매출액) 등)
- `operating_profit` — 영업이익
- `net_income` — 당기순이익 (CFS 기준 지배기업 귀속 순이익)

⚠️ 미매핑 계정(`account_key = account_nm` 원본 그대로)은 P&L 필터에서 자연 제외됨 — 이는 의도된 동작

### Recharts 주의사항

현재 프로젝트에 Recharts가 설치되어 있는지 확인 필요:
```bash
# frontend 디렉토리에서
cat package.json | grep recharts
# 없으면: npm install recharts
```

shadcn/ui `Skeleton` 컴포넌트 설치 확인:
```bash
ls frontend/src/components/ui/skeleton.tsx
# 없으면: npx shadcn@latest add skeleton
```

### Project Structure Notes

**이번 스토리에서 신규 생성:**
- `backend/app/services/financial_service.py`
- `backend/app/api/v1/financials.py`
- `backend/tests/test_financials.py`
- `frontend/src/lib/format.ts`
- `frontend/src/hooks/use-financial-data.ts`
- `frontend/src/components/charts/KPICard.tsx`
- `frontend/src/components/charts/FinancialChart.tsx`

**이번 스토리에서 수정:**
- `backend/app/main.py` — financials 라우터 등록
- `frontend/src/lib/api.ts` — `getFinancials` 함수 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — KPICard + FinancialChart 통합

**의도적으로 이번 스토리에서 미구현:**
- `type=bs`, `type=cf` → Story 3.4, 3.5에서 구현
- 다중 기업 비교 → Story 1.5
- 차트 이미지 다운로드 → Story 1.6
- DART 장애 배너 → Story 1.6

### References

- API 설계: [architecture.md - API & Communication Patterns](../planning-artifacts/architecture.md#api--communication-patterns)
- DB 스키마: [architecture.md - Data Architecture](../planning-artifacts/architecture.md#data-architecture)
- formatKRW 스펙: [architecture.md - Frontend Architecture](../planning-artifacts/architecture.md#frontend-architecture)
- 컴포넌트 구조: [architecture.md - Structure Patterns](../planning-artifacts/architecture.md#structure-patterns)
- KPICard UX: [ux-design-specification.md](../planning-artifacts/ux-design-specification.md)
- Story 1.3 패턴: [1-3-company-search.md](./1-3-company-search.md)
- AC 출처: [epics.md - Story 1.4](../planning-artifacts/epics.md#story-14-단일-기업-pl-차트-및-kpi-카드)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Recharts Tooltip `formatter` prop requires `(value: number | undefined, name: string | undefined)` signature — type annotations must match Recharts' internal `Formatter<number, string>` type exactly
- `format.ts` was already implemented from a previous session; Task 2 was verified and marked complete without re-implementation

### File List

- backend/app/services/financial_service.py (new)
- backend/app/api/v1/financials.py (new)
- backend/tests/test_financials.py (new)
- backend/app/main.py (modified)
- frontend/src/lib/api.ts (modified)
- frontend/src/hooks/use-financial-data.ts (new)
- frontend/src/components/charts/KPICard.tsx (new)
- frontend/src/components/charts/FinancialChart.tsx (new)
- frontend/src/app/(auth)/dashboard/page.tsx (modified)
