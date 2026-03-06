# Story 1.3: 기업 검색 기능

Status: review

## Story

As a Builder,
I want to search for a company by name or stock code and select it from suggestions,
So that I can find the right company instantly without knowing its DART corp_code.

## Acceptance Criteria

1. **[검색 API 호출]** Builder가 검색창에 "카카오"를 입력하면 (300ms 디바운스 후), `GET /api/v1/companies/search?q=카카오&limit=8`이 호출되고 자동완성 드롭다운에 최대 8개 결과가 표시되어야 한다. 각 결과에 기업명, 종목코드가 표시되어야 한다

2. **[기업 선택]** Builder가 기업을 클릭하거나 Enter로 선택하면, corp_code가 자동 매핑되고 CompanyTag가 생성되어야 한다. 검색 입력창이 초기화되어야 한다

3. **[검색 결과 없음]** 검색어에 해당하는 기업이 없을 때 드롭다운에 "검색 결과 없음" 메시지와 "종목코드로 검색해보세요" 힌트가 표시되어야 한다

4. **[키보드 접근성]** CompanySearchInput에서 방향키로 드롭다운 항목이 이동하고 Enter로 선택되어야 한다. `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded` ARIA 속성이 적용되어야 한다

## Tasks / Subtasks

- [x] Task 1: Backend — `GET /api/v1/companies/search` 엔드포인트 구현 (AC: #1)
  - [x] 1.1 `backend/app/api/v1/companies.py` 구현: `GET /api/v1/companies/search?q={query}&limit=8`
  - [x] 1.2 DB-First 검색 로직: `companies` 테이블에서 `company_name ILIKE` 또는 `stock_code =` 조회
  - [x] 1.3 DB 결과 없을 시 `dart_client.search_companies()` 호출 후 `companies` 테이블에 UPSERT
  - [x] 1.4 `main.py`에 companies 라우터 등록
  - [x] 1.5 `backend/tests/test_companies.py` 작성 및 pytest 통과 (5/5)

- [x] Task 2: Frontend — `api.ts`에 `searchCompanies` 함수 추가 (AC: #1)
  - [x] 2.1 `frontend/src/lib/api.ts`에 `searchCompanies(q: string)` 함수 추가
  - [x] 2.2 반환 타입: `Company[]` (corp_code, company_name, stock_code)
  - [x] 2.3 `frontend/src/types/index.ts`에 `Company` 타입 이미 존재

- [x] Task 3: Frontend — `useCompanySearch` 훅 구현 (AC: #1)
  - [x] 3.1 `frontend/src/hooks/use-company-search.ts` 생성
  - [x] 3.2 300ms 디바운스 로직 구현
  - [x] 3.3 TanStack Query `useQuery` 사용 (enabled: query.length >= 1)
  - [x] 3.4 로딩/에러/결과 상태 반환

- [x] Task 4: Frontend — `CompanySearchInput` 컴포넌트 구현 (AC: #1~#4)
  - [x] 4.1 `frontend/src/components/search/CompanySearchInput.tsx` 생성
  - [x] 4.2 shadcn `Command` 컴포넌트 기반 구현 (이미 설치됨)
  - [x] 4.3 검색결과 드롭다운: 기업명 + 종목코드 표시
  - [x] 4.4 "검색 결과 없음" + "종목코드로 검색해보세요" 힌트 표시
  - [x] 4.5 기업 선택 시 `onSelect(company: Company)` 콜백 호출 + 입력창 초기화
  - [x] 4.6 ARIA: `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded`
  - [x] 4.7 키보드 탐색 (방향키, Enter) — Command 컴포넌트가 기본 처리

- [x] Task 5: Frontend — 대시보드 페이지에 검색 컴포넌트 연동 (AC: #2)
  - [x] 5.1 `frontend/src/app/(auth)/dashboard/page.tsx` 업데이트
  - [x] 5.2 `CompanySearchInput` 렌더링 및 선택된 기업 상태 관리
  - [x] 5.3 선택된 기업 `CompanyTag` 표시 (이름 + 삭제 버튼)
  - [x] 5.4 Next.js 빌드 통과 확인

## Dev Notes

### Backend: companies.py 구현 패턴

```python
# backend/app/api/v1/companies.py
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.core.database import get_supabase_client
from app.services.dart_client import search_companies as dart_search_companies
from app.models.schemas import Company

router = APIRouter()

@router.get("/companies/search", response_model=list[Company])
async def search_companies(
    q: str = Query(..., min_length=1, description="기업명 또는 종목코드"),
    limit: int = Query(8, ge=1, le=20),
):
    """DB-First 기업 검색: DB 조회 → 없으면 DART API → DB UPSERT"""
    supabase = get_supabase_client()

    # 1. DB에서 먼저 검색 (빠름, DART API 한도 절약)
    res = supabase.table("companies").select("*").or_(
        f"company_name.ilike.%{q}%,stock_code.eq.{q}"
    ).limit(limit).execute()

    if res.data:
        return res.data

    # 2. DB에 없으면 DART API 검색
    dart_results = dart_search_companies(q)
    if not dart_results:
        return []

    # 3. DART 결과를 companies 테이블에 UPSERT
    upsert_data = [
        {
            "corp_code": r["corp_code"],
            "company_name": r["corp_name"],
            "stock_code": r.get("stock_code") or None,
            "is_listed": bool(r.get("stock_code")),
        }
        for r in dart_results
    ]
    supabase.table("companies").upsert(upsert_data, on_conflict="corp_code").execute()

    return upsert_data[:limit]
```

> ⚠️ Python 3.9 환경 — `list[Company]`는 런타임 오류 없음 (FastAPI가 처리). 타입힌트 내 `str | None`은 `Optional[str]`로 작성

### Backend: main.py 라우터 추가

```python
# 기존 코드에 추가
from app.api.v1 import health, sync, companies
app.include_router(companies.router, prefix="/api/v1")
```

### Frontend: Company 타입 (types/index.ts)

```typescript
// frontend/src/types/index.ts에 추가
export interface Company {
  corp_code: string
  company_name: string
  stock_code: string | null
  is_listed?: boolean
}
```

### Frontend: searchCompanies (api.ts)

```typescript
// frontend/src/lib/api.ts에 추가
export async function searchCompanies(q: string): Promise<Company[]> {
  return apiGet<Company[]>(`/api/v1/companies/search?q=${encodeURIComponent(q)}&limit=8`)
}
```

> ⚠️ `Company` 타입은 `types/index.ts`에서 import 필요

### Frontend: useCompanySearch 훅

```typescript
// frontend/src/hooks/use-company-search.ts
'use client'
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchCompanies } from '@/lib/api'
import type { Company } from '@/types'

export function useCompanySearch() {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  // 300ms 디바운스
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(timer)
  }, [query])

  const { data: results = [], isLoading, isError } = useQuery({
    queryKey: ['company-search', debouncedQuery],
    queryFn: () => searchCompanies(debouncedQuery),
    enabled: debouncedQuery.length >= 1,
    staleTime: 60_000,
  })

  return { query, setQuery, results, isLoading, isError }
}
```

### Frontend: CompanySearchInput 컴포넌트

```tsx
// frontend/src/components/search/CompanySearchInput.tsx
'use client'
import { Command, CommandInput, CommandList, CommandItem, CommandEmpty } from '@/components/ui/command'
import { useCompanySearch } from '@/hooks/use-company-search'
import type { Company } from '@/types'

interface Props {
  onSelect: (company: Company) => void
}

export function CompanySearchInput({ onSelect }: Props) {
  const { query, setQuery, results, isLoading } = useCompanySearch()

  const handleSelect = (company: Company) => {
    onSelect(company)
    setQuery('')  // 선택 후 입력창 초기화
  }

  return (
    <Command
      role="combobox"
      aria-autocomplete="list"
      aria-expanded={results.length > 0}
    >
      <CommandInput
        placeholder="기업명 입력 (예: 삼성전자, 카카오)"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {isLoading && query.length >= 1 && (
          <div className="py-2 px-3 text-sm text-gray-500">검색 중...</div>
        )}
        {!isLoading && query.length >= 1 && (
          <CommandEmpty>
            <div>'{query}'에 대한 결과 없음</div>
            <div className="text-xs text-gray-400 mt-1">종목코드로 검색해보세요</div>
          </CommandEmpty>
        )}
        {results.map((company) => (
          <CommandItem
            key={company.corp_code}
            onSelect={() => handleSelect(company)}
          >
            <span>{company.company_name}</span>
            {company.stock_code && (
              <span className="ml-2 text-xs text-gray-400">{company.stock_code}</span>
            )}
          </CommandItem>
        ))}
      </CommandList>
    </Command>
  )
}
```

### Frontend: 대시보드 페이지 CompanyTag 패턴

```tsx
// frontend/src/app/(auth)/dashboard/page.tsx 업데이트 예시
'use client'
import { useState } from 'react'
import { CompanySearchInput } from '@/components/search/CompanySearchInput'
import type { Company } from '@/types'

export default function DashboardPage() {
  const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([])

  const handleSelect = (company: Company) => {
    if (!selectedCompanies.find(c => c.corp_code === company.corp_code)) {
      setSelectedCompanies(prev => [...prev, company])
    }
  }

  const handleRemove = (corp_code: string) => {
    setSelectedCompanies(prev => prev.filter(c => c.corp_code !== corp_code))
  }

  return (
    <main className="p-6">
      <CompanySearchInput onSelect={handleSelect} />
      <div className="flex flex-wrap gap-2 mt-4">
        {selectedCompanies.map(c => (
          <div key={c.corp_code} className="flex items-center gap-1 px-3 py-1 bg-blue-100 rounded-full text-sm">
            <span>{c.company_name}</span>
            <button onClick={() => handleRemove(c.corp_code)} className="ml-1 text-gray-400 hover:text-gray-600">×</button>
          </div>
        ))}
      </div>
      {selectedCompanies.length === 0 && (
        <p className="text-gray-400 mt-8 text-center">대시보드 준비 중입니다. (Story 1.3에서 구현)</p>
      )}
    </main>
  )
}
```

### 아키텍처 준수 사항

- **DB-First 원칙**: `companies` 테이블 먼저 조회 → 없을 때만 DART API 호출. DART API 일일 20,000건 한도 보존
- **dart_client 격리**: `companies.py`에서 직접 `OpenDartReader` import 금지 — `dart_client.search_companies()` 경유
- **snake_case**: 모든 API 응답은 snake_case (`corp_code`, `company_name` — `corpCode` 금지)
- **api.ts 경유**: 프론트엔드에서 `fetch` 직접 호출 금지 — `lib/api.ts`의 `apiGet()` 사용
- **Python 3.9**: `str | None` 대신 `Optional[str]`, `list[dict]` 타입힌트는 런타임 OK

### Story 1-2에서 이어받는 사항

- `dart_client.search_companies(keyword)` — Story 1.2에서 완전 구현됨, 재사용
- `get_supabase_client()` — Story 1.2에서 구현됨
- `Company` Pydantic 스키마 — Story 1.2에서 `schemas.py`에 추가됨
- shadcn `Command` 컴포넌트 — Story 1.1에서 미리 설치됨 (`frontend/src/components/ui/command.tsx`)
- `api.ts` `apiGet()` 함수 — Story 1.1에서 구현됨, 확장만 필요

### Project Structure Notes

**이번 스토리에서 신규 생성:**
- `backend/app/api/v1/companies.py`
- `backend/tests/test_companies.py`
- `frontend/src/hooks/use-company-search.ts`
- `frontend/src/components/search/CompanySearchInput.tsx`

**이번 스토리에서 수정:**
- `backend/app/main.py` — companies 라우터 등록
- `frontend/src/lib/api.ts` — `searchCompanies` 함수 추가
- `frontend/src/types/index.ts` — `Company` 타입 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — 검색 컴포넌트 연동

**의도적으로 이번 스토리에서 미구현:**
- 재무 데이터 조회 API → Story 1.4
- P&L 차트 렌더링 → Story 1.4
- 최대 5개 기업 제한 UI → Story 1.5에서 멀티 비교 시 처리

### References

- API 설계: [architecture.md - API & Communication Patterns](../planning-artifacts/architecture.md#api--communication-patterns)
- DB-First 캐싱: [architecture.md - Data Architecture](../planning-artifacts/architecture.md#data-architecture)
- UX 패턴: [ux-design-specification.md - CompanySearchInput](../planning-artifacts/ux-design-specification.md)
- Story AC 출처: [epics.md - Story 1.3](../planning-artifacts/epics.md#story-13-기업-검색-기능)
- dart_client: [1-2 Story](./1-2-dart-data-collection-and-db-schema.md)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List

- `backend/app/api/v1/companies.py` — 신규 생성
- `backend/tests/test_companies.py` — 신규 생성 (5 tests passed)
- `backend/app/main.py` — companies 라우터 등록
- `frontend/src/lib/api.ts` — searchCompanies 추가
- `frontend/src/hooks/use-company-search.ts` — 신규 생성
- `frontend/src/components/search/CompanySearchInput.tsx` — 신규 생성
- `frontend/src/app/(auth)/dashboard/page.tsx` — 검색 컴포넌트 연동
