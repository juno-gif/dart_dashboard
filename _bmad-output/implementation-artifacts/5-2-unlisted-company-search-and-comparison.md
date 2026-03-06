# Story 5.2: 비상장사 검색 조회 및 상장사 통합 비교

Status: done

## Story

As a Builder,
I want to find previously entered unlisted companies via search and compare them with listed companies,
so that I can perform comprehensive competitive analysis across all company types in one view.

## Acceptance Criteria

1. **[검색 결과 통합 표시]** Builder가 CompanySearchInput에 기업명을 입력하면, DART 상장사와 이전에 수기 입력한 비상장사가 함께 결과 목록에 표시되어야 한다. 비상장사 항목에는 "(비상장)" 레이블이 표시되어 상장사와 구분되어야 한다

2. **[비상장사 CompanyTag 레이블]** 비상장사를 선택하면 CompanyTag에도 "(비상장)" 레이블이 표시되어야 한다

3. **[통합 비교 차트]** Builder가 상장사와 비상장사를 함께 선택한 상태에서 비교 차트가 렌더링되면, `GET /api/v1/companies/compare?codes=...`가 호출되고 상장사·비상장사 데이터가 동일한 FinancialChart에 나란히 표시되어야 한다

4. **[비상장사 자동 갱신 제외]** 분석 세트 자동 갱신(APScheduler) 시 비상장사(`is_listed=false`)는 DART 동기화 대상에서 제외되어야 한다. 비상장사 기업명 옆에 "●" 신규 데이터 알림 인디케이터가 표시되지 않아야 한다

5. **[Admin 수기 데이터 수정]** Admin이 비상장사 CompanyTag의 편집 버튼을 클릭하면, 기존 입력 데이터가 ManualEntryDialog 폼에 불러와져 수정하거나 연도를 추가할 수 있어야 한다

## Tasks / Subtasks

- [x] Task 1: Backend — DART 자동 갱신 시 비상장사 필터링 검증 (AC: #4)
  - [x] 1.1 `backend/app/scheduler/tasks.py` 읽어서 sync 대상 쿼리 확인
  - [x] 1.2 sync 대상 쿼리에 `.eq("is_listed", True)` 필터 미적용 시 추가 — `dart_client.py:129` 적용
  - [x] 1.3 `GET /api/v1/companies/new-data-status` — `last_new_data_at` NULL로 비상장사 자연 제외 확인. 추가 변경 불필요

- [x] Task 2: Backend — Admin 수기 데이터 수정 엔드포인트 (AC: #5)
  - [x] 2.1 `GET /api/v1/companies/{corp_code}/manual` 구현 (`companies.py:180-245`)
  - [x] 2.2 `PUT /api/v1/companies/{corp_code}/manual` 구현 (`companies.py:248-321`). 전체 교체: DELETE → UPSERT
  - [x] 2.3 `ManualCompanyFinancialsResponse` 스키마 추가 (`schemas.py:122-126`)
  - [x] 2.4 PUT은 기존 `ManualCompanyCreate` 스키마 재사용

- [x] Task 3: Backend — 테스트 작성 (AC: #4, #5)
  - [x] 3.1 GET 200 테스트 — `test_get_manual_company_financials_success`
  - [x] 3.2 Admin PUT 200 테스트 — `test_put_manual_company_success`
  - [x] 3.3 Admin 아닌 사용자 PUT 403 — `test_put_manual_company_non_admin_forbidden`
  - [x] 3.4 존재하지 않는 corp_code PUT 404 — `test_put_manual_company_not_found`

- [x] Task 4: Frontend — 검색 결과·CompanyTag "(비상장)" 레이블 (AC: #1, #2)
  - [x] 4.1 `CompanySearchInput.tsx:84-86` — `CommandItem`에 `(비상장)` 레이블 추가
  - [x] 4.2 설계 변경: `CompanyTag.tsx` 독립 컴포넌트 없음 확인 → `dashboard/page.tsx` 인라인 구현으로 변경
  - [x] 4.3 `dashboard/page.tsx:154-156` — `!c.is_listed`이면 `(비상장)` 배지 표시

- [x] Task 5: Frontend — Admin 비상장사 편집 UI (AC: #5)
  - [x] 5.1 `ManualEntryDialog.tsx` — `mode?: 'create' | 'edit'`, `corpCode?: string` props 추가
  - [x] 5.2 `useQuery` + `useEffect` prefill 구현 (`ManualEntryDialog.tsx:60-78`)
  - [x] 5.3 `updateMutation` + 캐시 무효화 구현 (`ManualEntryDialog.tsx:97-113`)
  - [x] 5.4 `dashboard/page.tsx:160-168` — Admin 편집 버튼, `ManualEntryDialog` edit 모드 연결

- [x] Task 6: Frontend — `lib/api.ts` 업데이트 (AC: #5)
  - [x] 6.1 `getManualCompanyFinancials` 추가 (`api.ts:295-297`)
  - [x] 6.2 `updateManualCompany` 추가 (`api.ts:299-301`)
  - [x] 6.3 `ManualCompanyFinancialsResponse` 인터페이스 정의 (`api.ts:289-293`)

- [x] Task 7: `npm run build` ✓ / `pytest test_manual_company_edit.py` 6/6 ✓

## Dev Notes

### 핵심 구현 분석 (기존 코드 재사용 가능 범위)

**✅ 이미 동작하는 것 (추가 구현 불필요)**

1. **검색 API** — `GET /api/v1/companies/search`가 이미 `is_listed` 필드를 포함한 `Company` 스키마로 응답함. DB에서 `company_name.ilike` 검색 시 상장사·비상장사 구분 없이 모두 반환. **프론트 UI 레이블 추가만 필요.**

2. **비교 차트 API** — `GET /api/v1/companies/compare?codes=MAN_XXXX,005930&type=pl`가 `financial_statements` 테이블에서 corp_code 기준으로 조회하므로 MAN_ 코드도 동일하게 동작. **백엔드 변경 불필요.**

3. **신규 데이터 상태** — `GET /api/v1/companies/new-data-status`는 `last_new_data_at` 기준. 수기 입력 비상장사는 이 필드가 NULL이므로 자연적으로 결과에서 제외됨. **변경 불필요.**

4. **`Company` 타입** — `frontend/src/types/index.ts`의 `Company` 인터페이스에 `is_listed: boolean`이 이미 있음.

**⚠️ 확인 및 수정 필요**

5. **DART 자동 갱신 필터** — `backend/app/scheduler/tasks.py`에서 sync 대상 기업 쿼리 확인. `.eq("is_listed", True)` 필터가 없으면 추가해야 함. 없을 경우 MAN_ 코드로 DART API 호출 시 오류 발생 또는 빈 결과를 DB에 잘못 저장할 수 있음.

**🆕 신규 구현 필요**

6. **Admin 편집 엔드포인트** — 신규 추가
7. **프론트 "(비상장)" 레이블** — UI 변경
8. **ManualEntryDialog 편집 모드** — 기능 확장

### Backend — Admin 편집 엔드포인트 설계

```python
# backend/app/api/v1/companies.py 에 추가

# Response schema (schemas.py에 추가)
class ManualCompanyFinancialsResponse(BaseModel):
    corp_code: str
    company_name: str
    financials: list[ManualFinancialEntry]  # 기존 스키마 재사용

# GET — 기존 수기 입력 재무 데이터 조회 (Admin 전용)
@router.get("/companies/{corp_code}/manual", response_model=ManualCompanyFinancialsResponse)
async def get_manual_company_financials(corp_code: str, user=Depends(get_current_user)):
    require_admin(user)
    supabase = get_supabase_client()
    # companies 테이블에서 회사 정보 조회
    # financial_statements 테이블에서 PL 데이터 조회 (reprt_code="11011", fs_div="OFS")
    # ManualFinancialEntry 리스트로 변환해 반환

# PUT — 기존 수기 입력 재무 데이터 전체 교체 (Admin 전용)
@router.put("/companies/{corp_code}/manual", response_model=Company, status_code=200)
async def update_manual_company(corp_code: str, body: ManualCompanyCreate, user=Depends(get_current_user)):
    require_admin(user)
    supabase = get_supabase_client()
    # is_listed=False 기업인지 확인 (404 처리)
    # financial_statements UPSERT (기존 5-1 패턴 동일)
    # Company 반환
```

**주의:** `require_admin`은 `backend/app/core/auth.py`에 이미 구현됨. 사용법:
```python
from app.core.auth import get_current_user, require_admin

async def endpoint(user=Depends(get_current_user)):
    require_admin(user)
    ...
```

**GET 응답의 ManualFinancialEntry 변환 로직:**
```python
# financial_statements 조회 결과를 연도별로 그룹핑
from collections import defaultdict

rows = supabase.table("financial_statements")
    .select("bsns_year, account_key, amount")
    .eq("corp_code", corp_code)
    .eq("reprt_code", "11011")
    .eq("fs_div", "OFS")
    .execute().data

# 연도별 그룹핑
by_year = defaultdict(dict)
for row in rows:
    by_year[row["bsns_year"]][row["account_key"]] = row["amount"]

financials = [
    ManualFinancialEntry(
        bsns_year=year,
        revenue=data.get("revenue"),
        operating_profit=data.get("operating_profit"),
        net_income=data.get("net_income"),
    )
    for year, data in sorted(by_year.items())
]
```

### Frontend — "(비상장)" 레이블 추가 위치

**CompanySearchInput.tsx** — `CommandItem` 내부 (`frontend/src/components/search/CompanySearchInput.tsx:75-85`):
```tsx
<CommandItem key={company.corp_code} onSelect={() => handleSelect(company)}>
  <span>{company.company_name}</span>
  {company.stock_code && (
    <span className="ml-2 text-xs text-gray-400">{company.stock_code}</span>
  )}
  {!company.is_listed && (
    <span className="ml-2 text-xs text-muted-foreground">(비상장)</span>
  )}
</CommandItem>
```

**CompanyTag.tsx** — 구조 확인 후 `is_listed` 수신 prop 추가 또는 Company 객체 전체 수신 방식 채택.

### Frontend — ManualEntryDialog 편집 모드 설계

```tsx
interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialCompanyName?: string
  onSelect: (company: Company) => void
  // 편집 모드 props 추가
  mode?: 'create' | 'edit'
  corpCode?: string  // 편집 모드 시 필수
}

// 편집 모드에서 기존 데이터 로드
const { data: existingData } = useQuery({
  queryKey: ['manual-financials', corpCode],
  queryFn: () => getManualCompanyFinancials(corpCode!),
  enabled: mode === 'edit' && !!corpCode && open,
})

// existingData 로드 완료 시 rows/companyName 초기화
useEffect(() => {
  if (existingData && mode === 'edit') {
    setCompanyName(existingData.company_name)
    setRows(existingData.financials.map(f => ({
      bsns_year: f.bsns_year,
      revenue: f.revenue ? String(f.revenue / 100_000_000) : '',
      operating_profit: f.operating_profit ? String(f.operating_profit / 100_000_000) : '',
      net_income: f.net_income ? String(f.net_income / 100_000_000) : '',
    })))
  }
}, [existingData, mode])

// 제출 시 분기 처리
const handleSubmit = () => {
  if (!validate()) return
  if (mode === 'edit' && corpCode) {
    updateMutation.mutate({ corpCode, data: payload })
  } else {
    createMutation.mutate(payload)
  }
}
```

**금액 역변환 주의:** DB/API는 원 단위. 편집 모드에서 폼에 표시 시 억 단위로 역변환 필요:
- `amount / 100_000_000` → 폼 표시
- 제출 시 `* 100_000_000` → API 전송 (기존 5-1 로직 동일)

### Frontend — CompanyTag Admin 편집 버튼

```tsx
// CompanyTag.tsx
// userRole을 얻는 방법: hooks/use-auth.ts의 getUserProfile 또는 context
// 간단 구현: userRole을 prop으로 전달하거나 context에서 읽기

{!company.is_listed && userRole === 'admin' && (
  <button
    onClick={(e) => { e.stopPropagation(); onEdit?.(company) }}
    className="ml-1 p-0.5 rounded hover:bg-muted"
    aria-label="수기 데이터 편집"
  >
    <PencilIcon className="h-3 w-3" />
  </button>
)}
```

편집 버튼 클릭 시 부모에서 ManualEntryDialog를 `mode='edit'`으로 열기.

### 아키텍처 준수 사항 (필수)

- **모든 API 호출은 `lib/api.ts` 경유** — CompanyTag나 컴포넌트에서 직접 fetch 금지
- **`is_listed` 필드** — `Company` 타입에 이미 있음. API 응답에서 그대로 사용
- **`require_admin(user)`** — Admin 전용 엔드포인트에 반드시 적용 (`core/auth.py` 기존 함수)
- **`formatKRW()`** — 금액 표시는 반드시 이 유틸 사용 (컴포넌트 직접 변환 금지)
- **snake_case 통일** — API 요청/응답 필드명 camelCase 변환 금지
- **TanStack Query 키 규칙** — `['manual-financials', corp_code]`

### 5-1에서 배운 것 (재사용 패턴)

- `supabase.table(...).upsert(rows, on_conflict="corp_code,bsns_year,reprt_code,fs_div,account_key")` 패턴 그대로 사용
- 테스트 auth mock: `app.dependency_overrides[get_current_user] = lambda: MOCK_USER`
- Admin mock: `MOCK_ADMIN = type("User", (), {"id": "admin-123"})()` + `require_admin` mock 패치 필요
- `_mock_supabase_empty()` 헬퍼 패턴 참조: `backend/tests/test_manual_company.py`

### 수정 대상 파일

**Backend (수정):**
- `backend/app/api/v1/companies.py` — GET + PUT `/companies/{corp_code}/manual` 엔드포인트 추가
- `backend/app/models/schemas.py` — `ManualCompanyFinancialsResponse` 스키마 추가
- `backend/app/scheduler/tasks.py` — `is_listed=True` 필터 추가 (확인 후 필요 시)

**Backend (신규):**
- `backend/tests/test_manual_company_edit.py`

**Frontend (수정):**
- `frontend/src/components/search/CompanySearchInput.tsx` — "(비상장)" 레이블
- `frontend/src/components/search/CompanyTag.tsx` — "(비상장)" 배지 + Admin 편집 버튼
- `frontend/src/components/search/ManualEntryDialog.tsx` — 편집 모드 추가
- `frontend/src/lib/api.ts` — `getManualCompanyFinancials`, `updateManualCompany` 추가

### Project Structure Notes

- 모든 search 컴포넌트는 `frontend/src/components/search/` 유지 (아키텍처 강제 규칙)
- 신규 엔드포인트는 `backend/app/api/v1/companies.py` 하단에 추가 (별도 파일 불필요)
- `ManualCompanyFinancialsResponse` 스키마는 `backend/app/models/schemas.py`에 `# ── Story 5.2` 구분 주석으로 추가

### References

- [Source: architecture.md - API & Communication Patterns] — REST 패턴, 에러 응답 형식, require_admin 사용법
- [Source: architecture.md - Enforcement Guidelines] — lib/api.ts 경유, snake_case, formatKRW 규칙
- [Source: epics.md - Epic 5, Story 5.2] — AC 전체, BDD 시나리오
- [Source: backend/app/api/v1/companies.py:99-174] — POST /companies/manual 기존 패턴 (5.1 구현)
- [Source: backend/app/core/auth.py:77-104] — require_admin 사용법
- [Source: backend/tests/test_manual_company.py] — auth mock, supabase mock 패턴
- [Source: frontend/src/types/index.ts:8-14] — Company 인터페이스 (is_listed 확인)
- [Source: frontend/src/components/search/CompanySearchInput.tsx:75-85] — CommandItem 수정 위치
- [Source: frontend/src/components/search/ManualEntryDialog.tsx] — 편집 모드 확장 기반

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- **설계 변경 (Task 4.2/4.3/5.4)**: 스토리에서 `CompanyTag.tsx` 독립 컴포넌트 수정으로 설계됐으나, 해당 컴포넌트가 `dashboard/page.tsx` 인라인으로 구현되어 있어 `dashboard/page.tsx`에 직접 추가함
- **Code Review Fix (H1)**: `PUT /companies/{corp_code}/manual` — DELETE 후 UPSERT로 전체 교체 의미 보장. `companies.py:279-290`
- **Code Review Fix (M3)**: `updateMutation.onSuccess`에 `['financials', corpCode]`, `['compare']`, `['manual-company-financials', corpCode]` 쿼리 캐시 무효화 추가

### File List

- `backend/app/services/dart_client.py` — DART sync에 `is_listed=True` 필터 추가
- `backend/app/api/v1/companies.py` — GET/PUT `/companies/{corp_code}/manual` 엔드포인트 추가
- `backend/app/models/schemas.py` — `ManualCompanyFinancialsResponse` 스키마 추가
- `backend/tests/test_manual_company_edit.py` — 신규: 6개 테스트
- `frontend/src/components/search/CompanySearchInput.tsx` — `(비상장)` 레이블 추가
- `frontend/src/components/search/ManualEntryDialog.tsx` — 편집 모드 추가 (`mode`, `corpCode` props, `useQuery` prefill, `updateMutation`, 캐시 무효화)
- `frontend/src/lib/api.ts` — `apiPut`, `getManualCompanyFinancials`, `updateManualCompany`, `ManualCompanyFinancialsResponse` 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — `(비상장)` 배지, Admin 편집 버튼, `ManualEntryDialog` edit 모드 마운트
