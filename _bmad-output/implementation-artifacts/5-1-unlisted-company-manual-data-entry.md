# Story 5.1: 비상장사 재무 데이터 수기 입력 및 저장

Status: done

## Story

As a Builder,
I want to manually enter financial data for companies not registered in DART,
so that I can include them in analyses alongside listed companies.

## Acceptance Criteria

1. **[검색 결과 없음 → 수기 입력 유도]** Builder가 CompanySearchInput에서 기업명을 검색했으나 DART에 등록되지 않아 결과가 없을 때, "검색 결과 없음" 드롭다운에 "DART에 등록되지 않은 기업입니다. 수기로 재무 데이터를 입력하시겠습니까?" 안내와 "수기 입력으로 추가" 버튼이 함께 표시되어야 한다

2. **[수기 입력 폼]** Builder가 "수기 입력으로 추가" 버튼을 클릭하면 수기 입력 Dialog가 열리고, 기업명, 사업연도(년도), 매출, 영업이익, 순이익 입력 필드가 표시되어야 한다. 최소 1개 사업연도 데이터를 입력할 수 있으며, "연도 추가" 버튼으로 최대 5개 연도까지 행을 추가할 수 있어야 한다

3. **[POST /api/v1/companies/manual]** Builder가 수기 입력 폼을 제출하면 `POST /api/v1/companies/manual`이 호출되어 `companies` 테이블에 `is_listed=false`로 저장되고, 입력된 연도별 데이터가 `financial_statements`에 각각 저장되어야 한다

4. **[성공 피드백 및 CompanyTag 추가]** 저장 성공 시 Toast "비상장사 데이터가 저장되었습니다"가 3초 후 자동 소멸되고, 해당 기업이 CompanyTag로 즉시 추가되어야 한다 (Dialog 닫힘)

5. **[클라이언트 유효성 검사]** 기업명 또는 사업연도가 비어있거나, 금액 필드에 숫자 이외 값이 있으면 "필수 항목입니다" 또는 "숫자만 입력하세요" 인라인 오류가 표시되어야 한다. 오류 상태에서 서버 요청은 전송되지 않아야 한다

## Tasks / Subtasks

- [x] Task 1: Backend — `POST /api/v1/companies/manual` 엔드포인트 (AC: #3)
  - [x] 1.1 `backend/app/models/schemas.py`에 `ManualFinancialEntry`, `ManualCompanyCreate` 스키마 추가
  - [x] 1.2 `backend/app/api/v1/companies.py`에 `POST /companies/manual` 라우터 추가
  - [x] 1.3 corp_code 자동 생성: `"MAN_" + uuid4().hex[:8].upper()` (DART 코드와 충돌 방지)
  - [x] 1.4 `companies` 테이블 INSERT: `corp_code`, `company_name`, `is_listed=False`, `stock_code=None`
  - [x] 1.5 `financial_statements` 테이블 UPSERT: 연도별 PL 3계정 (revenue, operating_profit, net_income)
  - [x] 1.6 고정값: `reprt_code="11011"`, `fs_div="OFS"`, `account_nm=None`
  - [x] 1.7 이미 동일 `corp_code`+`company_name` 조합 존재 시 — 기존 회사 재사용 (409 아닌 200)

- [x] Task 2: Backend — `test_manual_company.py` 테스트 작성 (AC: #3)
  - [x] 2.1 `test_post_manual_company_success` — 201, companies + financial_statements 저장 확인
  - [x] 2.2 `test_post_manual_company_multiple_years` — 3개 연도, 9개 rows 저장
  - [x] 2.3 `test_post_manual_company_auth_required` — 인증 없이 401 반환
  - [x] 2.4 pytest 전체 통과 확인 — 115 passed

- [x] Task 3: Frontend — `ManualEntryDialog.tsx` 컴포넌트 생성 (AC: #2, #4, #5)
  - [x] 3.1 `frontend/src/components/search/ManualEntryDialog.tsx` 신규 생성
  - [x] 3.2 shadcn/ui `Dialog`으로 오버레이 구현
  - [x] 3.3 기업명 input + 연도별 행 (사업연도, 매출, 영업이익, 순이익)
  - [x] 3.4 "연도 추가" 버튼 — 최대 5행까지, 이후 비활성화
  - [x] 3.5 클라이언트 유효성 검사: 필수 필드, 숫자 형식 (인라인 에러 메시지)
  - [x] 3.6 `useMutation` 연동 → 성공 시 Toast + Dialog 닫기 + `onSelect(company)` 호출

- [x] Task 4: Frontend — `CompanySearchInput.tsx` 수정 (AC: #1, #4)
  - [x] 4.1 `CommandEmpty` 내 "수기 입력으로 추가" 버튼 추가
  - [x] 4.2 `ManualEntryDialog` open 상태 관리 (`useState<boolean>`)
  - [x] 4.3 Dialog에 `initialCompanyName={query}` 전달 (입력값 pre-fill)
  - [x] 4.4 Dialog 성공 시 `onSelect(company)` 호출로 CompanyTag 즉시 추가

- [x] Task 5: Frontend — `lib/api.ts` 업데이트 (AC: #3)
  - [x] 5.1 `createManualCompany(data: ManualCompanyCreateRequest)` 함수 추가
  - [x] 5.2 `POST /api/v1/companies/manual` 호출, 반환 타입 `Company`

- [x] Task 6: `npm run build` 통과 확인

## Dev Notes

### 핵심 구현 결정사항

**1. corp_code 자동 생성 전략**

DART corp_code는 8자리 숫자(예: `"00126380"`). 비상장 수기 입력 기업은 DART와 충돌하지 않도록 고유 식별자가 필요함:

```python
import uuid
corp_code = "MAN_" + uuid.uuid4().hex[:8].upper()
# 예: "MAN_A3F9C21E"
```

- `companies` 테이블 `corp_code` PK가 `VARCHAR(8)`로 정의된 경우 충돌 가능 — 스키마 확인 후 필요하면 `VARCHAR(20)`으로 마이그레이션 필요
- Supabase SQL Editor에서 변경: `ALTER TABLE companies ALTER COLUMN corp_code TYPE VARCHAR(20);`

**2. financial_statements 저장 형식**

PL 3계정 고정값:
```python
reprt_code = "11011"  # 사업보고서
fs_div = "OFS"        # 별도재무제표
account_nm = None     # 수기 입력 — 원본 없음

# 저장 예시 (1개 연도, 3개 rows):
[
  {"corp_code": "MAN_A3F9C21E", "bsns_year": "2024", "reprt_code": "11011",
   "fs_div": "OFS", "account_key": "revenue", "account_nm": None, "amount": 50000000000},
  {"corp_code": "MAN_A3F9C21E", "bsns_year": "2024", "reprt_code": "11011",
   "fs_div": "OFS", "account_key": "operating_profit", "account_nm": None, "amount": 5000000000},
  {"corp_code": "MAN_A3F9C21E", "bsns_year": "2024", "reprt_code": "11011",
   "fs_div": "OFS", "account_key": "net_income", "account_nm": None, "amount": 3500000000},
]
```

**3. Pydantic 스키마 설계**

```python
# backend/app/models/schemas.py 추가

class ManualFinancialEntry(BaseModel):
    bsns_year: str = Field(..., pattern=r'^\d{4}$')  # 4자리 연도
    revenue: Optional[int] = None                     # 매출 (원 단위)
    operating_profit: Optional[int] = None            # 영업이익
    net_income: Optional[int] = None                  # 순이익

class ManualCompanyCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=100)
    financials: list[ManualFinancialEntry] = Field(..., min_length=1, max_length=5)
```

**4. API 엔드포인트 위치 주의**

`companies.py`에 추가 시 기존 경로와 충돌 주의:
- 기존: `GET /companies/new-data-status` (등록 순서: 상단)
- 기존: `GET /companies/search`
- 신규: `POST /companies/manual`

POST 메서드이므로 경로 순서 충돌 없음. `companies.py` 하단에 추가 가능.

**5. Frontend — ManualEntryDialog 구조**

```tsx
// frontend/src/components/search/ManualEntryDialog.tsx
'use client'
import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { createManualCompany } from '@/lib/api'
import type { Company } from '@/types'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialCompanyName?: string
  onSelect: (company: Company) => void
}
```

연도별 행은 `useState<ManualFinancialEntry[]>` 배열로 관리:
```tsx
const [entries, setEntries] = useState([{ bsns_year: '', revenue: '', operating_profit: '', net_income: '' }])

const addEntry = () => {
  if (entries.length >= 5) return
  setEntries([...entries, { bsns_year: '', revenue: '', operating_profit: '', net_income: '' }])
}
```

**6. CompanySearchInput 수정 — CommandEmpty 확장**

```tsx
// 기존 CommandEmpty 내용 아래 추가
<CommandEmpty>
  <div>&apos;{query}&apos;에 대한 결과 없음</div>
  <div className="text-xs text-gray-400 mt-1">종목코드로 검색해보세요</div>
  <div className="mt-3 text-xs text-gray-500">
    DART에 등록되지 않은 기업입니다. 수기로 재무 데이터를 입력하시겠습니까?
  </div>
  <Button
    variant="outline"
    size="sm"
    className="mt-2"
    onClick={() => setManualDialogOpen(true)}
  >
    수기 입력으로 추가
  </Button>
</CommandEmpty>
```

**7. 금액 입력 처리**

사용자는 "5000억" 대신 원 단위 숫자를 입력하거나, 억 단위 입력 후 서버에서 변환하는 방식 중 선택:
- **권장: 억 단위 입력, 프론트에서 × 100_000_000 변환 후 전송**
  - UX 개선: "500000000000" 대신 "5000" (억 단위) 입력
  - 입력 placeholder: "억 단위 입력 (예: 5000 → 5,000억)"
  - 전송 시: `revenue * 100_000_000`

**8. Supabase RLS — companies 테이블 쓰기 권한**

기존 `companies` 테이블 RLS 정책 확인 필요. 현재 Builder가 DART 검색 후 UPSERT하는 패턴(`companies.py:88`)이 이미 있음 → service key 사용으로 RLS 무관. `companies/manual`도 동일하게 service key 경유 → 별도 RLS 정책 불필요.

### Backend 패턴 참조

```python
# backend/app/api/v1/companies.py 기존 패턴
@router.get("/companies/search", response_model=list[Company])
async def search_companies(..., _: object = Depends(get_current_user)):
    supabase = get_supabase_client()
    ...
    supabase.table("companies").upsert(upsert_data, on_conflict="corp_code").execute()
```

신규 엔드포인트도 동일하게:
```python
@router.post("/companies/manual", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_manual_company(body: ManualCompanyCreate, user=Depends(get_current_user)):
    supabase = get_supabase_client()
    ...
```

### 테스트 패턴 (test_manual_company.py)

기존 `tests/test_companies.py`의 auth mock 패턴 참조:

```python
# backend/tests/test_manual_company.py
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

MOCK_USER = type("User", (), {"id": "user-123"})()

@pytest.fixture
def client():
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### DB 마이그레이션 노트

`corp_code` 컬럼이 현재 `VARCHAR(8)`인 경우 `MAN_XXXXXXXX` (12자)를 저장할 수 없음. Supabase SQL Editor에서 실행:

```sql
-- corp_code 컬럼 타입 확장
ALTER TABLE companies ALTER COLUMN corp_code TYPE VARCHAR(20);
ALTER TABLE financial_statements ALTER COLUMN corp_code TYPE VARCHAR(20);

-- 확인
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name IN ('companies', 'financial_statements')
  AND column_name = 'corp_code';
```

### Project Structure Notes

- `ManualEntryDialog.tsx` 위치: `frontend/src/components/search/` (search 관련이므로 적합)
- `companies/manual` 엔드포인트: 기존 `companies.py`에 추가 (별도 파일 불필요)
- `lib/api.ts` 주석: `// ── Story 5.1: 비상장사 수기 입력 ──────────────────────────` 패턴 유지
- `ManualCompanyCreate`, `ManualFinancialEntry` 스키마: `schemas.py`에 `# ── Story 5.1` 구분 주석으로 추가

### 수정 대상 파일

- `backend/app/models/schemas.py` (수정: ManualFinancialEntry, ManualCompanyCreate 추가)
- `backend/app/api/v1/companies.py` (수정: POST /companies/manual 추가)
- `backend/tests/test_manual_company.py` (신규)
- `frontend/src/components/search/ManualEntryDialog.tsx` (신규)
- `frontend/src/components/search/CompanySearchInput.tsx` (수정: CommandEmpty 확장)
- `frontend/src/lib/api.ts` (수정: createManualCompany 함수 추가)

### References

- [Source: architecture.md - Data Architecture] — companies 테이블 스키마, financial_statements UNIQUE 제약
- [Source: architecture.md - API & Communication Patterns] — REST 엔드포인트 패턴, 에러 응답 형식
- [Source: architecture.md - Enforcement Guidelines] — lib/api.ts 경유 필수, service key 사용
- [Source: epics.md - Epic 5, Story 5.1] — AC, BDD 시나리오 전체
- [Source: backend/app/api/v1/companies.py:88] — service key + upsert 패턴
- [Source: frontend/src/components/search/CompanySearchInput.tsx] — CommandEmpty 수정 위치
- [Source: frontend/src/lib/api.ts] — apiPost 래퍼 패턴
- [Source: backend/app/models/schemas.py] — 기존 Company, FinancialStatement 스키마 구조

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- corp_code 자동 생성: `"MAN_" + uuid4().hex[:8].upper()` — DART 8자리 숫자와 충돌 없음
- 동일 company_name 비상장사 중복 방지: 기존 corp_code 재사용 로직 구현
- 금액 입력: 억 단위 입력 → 프론트에서 ×100_000_000 변환 후 전송
- 테스트 4개 추가: 201 성공, 3개 연도 9개 rows, 401 미인증, 기존 회사 재사용
- 115 tests passed (기존 111 + 신규 4)
- `npm run build` 성공

### File List

- `backend/app/models/schemas.py` (수정: ManualFinancialEntry, ManualCompanyCreate 추가)
- `backend/app/api/v1/companies.py` (수정: POST /companies/manual 엔드포인트 추가)
- `backend/tests/test_manual_company.py` (신규)
- `frontend/src/components/search/ManualEntryDialog.tsx` (신규)
- `frontend/src/components/search/CompanySearchInput.tsx` (수정: ManualEntryDialog 연동)
- `frontend/src/lib/api.ts` (수정: createManualCompany 함수 추가)
