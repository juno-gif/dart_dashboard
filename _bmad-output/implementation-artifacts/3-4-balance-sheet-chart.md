# Story 3.4: B/S 핵심 항목 차트

Status: done

## Story

As a Builder,
I want to view Balance Sheet key metrics (assets, liabilities, equity, cash) as a chart,
So that I can assess a company's financial position alongside P&L trends.

## Acceptance Criteria

1. **[B/S 탭 전환 → API 호출]** Builder가 기업을 선택한 상태에서 "B/S" 탭 버튼을 클릭하면 `GET /api/v1/companies/{corp_code}/financials?years=5&type=bs`가 호출되고 자산·부채·자본·현금성자산 데이터가 FinancialChart에 표시되어야 한다.

2. **[formatKRW 규칙 + 5년치 표시]** B/S 차트가 렌더링될 때 모든 금액은 `formatKRW()`를 통해 변환되어야 한다 (컴포넌트 내 직접 변환 금지). 최근 5개 사업연도 데이터가 표시되어야 한다.

3. **[Skeleton 로딩 — 레이아웃 쉬프트 없음]** B/S API 응답을 기다리는 동안 FinancialChart와 동일한 높이(`h-80`)의 Skeleton이 표시되어야 한다.

4. **[B/S 데이터 없음 안내]** 해당 기업의 B/S 데이터가 DB에 존재하지 않을 때 "B/S 데이터를 제공하지 않는 기업입니다. P&L 데이터만 이용 가능합니다." 안내 메시지가 표시되어야 한다.

## Tasks / Subtasks

- [ ] Task 1: Backend — `financial_service.py` B/S 조회 함수 추가 (AC: #1, #2, #4)
  - [ ] 1.1 `BS_ACCOUNT_KEYS = ["total_assets", "total_liabilities", "total_equity", "cash_and_equivalents"]` 상수 추가
  - [ ] 1.2 `get_bs_data(corp_code: str, years: int = 5) -> list` 함수 추가 — `get_pl_data()` 패턴 그대로 복사, `BS_ACCOUNT_KEYS` 사용
  - [ ] 1.3 내부 `_query_bs(supabase, corp_code, years)` 헬퍼 함수 추가 (`.in_("account_key", BS_ACCOUNT_KEYS)` 사용)
  - [ ] 1.4 기존 `_prefer_cfs()` 함수는 변경 없이 재사용 (B/S도 동일 CFS 우선 로직 적용)

- [ ] Task 2: Backend — `financials.py` `type=bs` 지원 추가 (AC: #1, #4)
  - [ ] 2.1 `get_financials` 엔드포인트에서 `type=bs` 처리 추가:
    - `get_bs_data(corp_code, years=years)` 호출
    - 빈 결과 시: `[]` 반환 (404 아님 — 프론트에서 빈 배열로 "데이터 없음" 안내 표시)
  - [ ] 2.2 `compare_financials` 엔드포인트에서 `type=bs` 처리 추가 (동일 패턴)
  - [ ] 2.3 기존 `"type=pl만 지원됩니다"` 400 에러 → `"pl/bs만 지원됩니다. cf는 Story 3.5에서 구현됩니다."` 로 메시지 변경 (`type=cf`는 여전히 400)
  - [ ] 2.4 `financial_service`에서 `get_bs_data` import 추가

- [ ] Task 3: Backend — `test_financials.py` 수정 및 B/S 테스트 추가 (AC: #1, #2, #4)
  - [ ] 3.1 기존 `test_get_financials_rejects_non_pl_type` 테스트 삭제 (이제 bs도 지원하므로 유효하지 않음)
  - [ ] 3.2 `test_get_financials_bs_type_returns_200` 추가 — DB에 BS 데이터 있을 때 200 반환
  - [ ] 3.3 `test_get_financials_bs_type_returns_empty_when_no_data` 추가 — DB에 BS 없을 때 빈 배열 + 200
  - [ ] 3.4 `test_get_financials_cf_type_returns_400` 추가 — `type=cf`는 여전히 400
  - [ ] 3.5 pytest 전체 통과 확인

- [ ] Task 4: Frontend — `dashboard/page.tsx` 차트 유형 탭 추가 (AC: #1, #3)
  - [ ] 4.1 `chartType: FinancialType` state 추가 (기본값 `'pl'`, import `FinancialType` from `@/types`)
  - [ ] 4.2 `useFinancialData(corpCode, 5, chartType)` — `chartType` 전달 (기존 `!isCompareMode` 분기 유지)
  - [ ] 4.3 CompanyTag 목록과 차트 사이에 탭 UI 추가: P&L / B/S 두 개 버튼, `!isCompareMode && primaryCompany` 조건에서만 표시
    - 탭 전환 시 `setChartType(...)` 호출
    - 선택된 탭: `bg-primary text-primary-foreground`, 미선택: `variant="outline"`
    - shadcn/ui `Button` 컴포넌트 사용 (Tabs 컴포넌트 불필요 — 단순 버튼 토글로 충분)
  - [ ] 4.4 기업 변경 시(`handleSelect`, `handleRemove`로 기업 목록 변경 시) `setChartType('pl')`로 리셋

- [ ] Task 5: Frontend — `FinancialChart.tsx` B/S 렌더링 모드 추가 (AC: #2, #3, #4)
  - [ ] 5.1 Props에 `type?: FinancialType` 추가 (기본값 `'pl'`)
  - [ ] 5.2 B/S용 `chartData` 빌드 로직 추가:
    ```tsx
    // type='bs' 일 때
    const chartData = years.map((year) => {
      const get = (key: string) =>
        data.find((d) => d.bsns_year === year && d.account_key === key)?.amount ?? 0
      return {
        year,
        total_assets: get('total_assets'),
        total_liabilities: get('total_liabilities'),
        total_equity: get('total_equity'),
        cash_and_equivalents: get('cash_and_equivalents'),
      }
    })
    ```
  - [ ] 5.3 B/S 차트 렌더링: 자산(Bar, `#2563eb`), 부채(Bar, `#ef4444`), 자본(Line, `#16a34a`), 현금성자산(Line, `#9333ea`)
    - Tooltip: `total_assets='자산'`, `total_liabilities='부채'`, `total_equity='자본'`, `cash_and_equivalents='현금성자산'`
    - Legend: 동일 한국어 레이블
  - [ ] 5.4 빈 데이터 상태 처리: `!isLoading && data.length === 0` 시:
    ```tsx
    <p className="text-sm text-muted-foreground text-center py-8">
      {type === 'bs'
        ? 'B/S 데이터를 제공하지 않는 기업입니다. P&L 데이터만 이용 가능합니다.'
        : '재무 데이터가 없습니다.'}
    </p>
    ```

- [ ] Task 6: `npm run build` 통과 확인 (TypeScript 에러 없음)
  - [ ] 6.1 `npm run build` 실행

## Dev Notes

### 아키텍처 강제 규칙 (위반 시 PR 거부)

- 컴포넌트 내 직접 `fetch()` 금지 → 반드시 `lib/api.ts` 경유 (이번 스토리는 api.ts 변경 없음 — 기존 `getFinancials` 재사용)
- 금액 표시는 `formatKRW()` 유틸만 사용, FinancialChart 내에서만 변환
- `shadcn/ui` 컴포넌트 직접 수정 금지 (`frontend/src/components/ui/` 폴더)
- DART OpenAPI 직접 import 금지 (dart_client.py만 허용)

### DB 사전 확인 (선행 필수)

B/S 데이터는 `account_mappings` 테이블의 BS 항목이 있어야 `financial_statements`에 표준 key로 저장됩니다.

**Supabase Dashboard에서 확인:**
```sql
SELECT * FROM account_mappings WHERE category = 'bs';
```

없으면 수동으로 추가:
```sql
INSERT INTO account_mappings (account_nm, account_key, display_name, category) VALUES
  ('자산총계',          'total_assets',         '자산총계',    'bs'),
  ('부채총계',          'total_liabilities',    '부채총계',    'bs'),
  ('자본총계',          'total_equity',         '자본총계',    'bs'),
  ('현금및현금성자산',  'cash_and_equivalents', '현금성자산',  'bs')
ON CONFLICT (account_nm) DO NOTHING;
```

**주의:** DART 계정과목명은 기업마다 다를 수 있습니다. 위 항목은 가장 일반적인 매핑입니다.

### Backend 구현 패턴

#### `financial_service.py` B/S 추가 패턴

```python
# 기존 파일 끝에 추가
BS_ACCOUNT_KEYS = ["total_assets", "total_liabilities", "total_equity", "cash_and_equivalents"]


def get_bs_data(corp_code: str, years: int = 5) -> list:
    """DB-First B/S 조회.
    DB에 데이터 없으면 DART sync 후 재조회.
    DART 장애 시: DB 캐시 있으면 반환, 없으면 예외 re-raise (→ 503).
    CFS(연결) 우선, 없으면 OFS(개별) 사용.
    """
    supabase = get_supabase_client()

    rows = _query_bs(supabase, corp_code, years)

    if not rows:
        try:
            sync_company_financials(corp_code, years=years)
            rows = _query_bs(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            raise

    return _prefer_cfs(rows, years)  # 기존 _prefer_cfs 재사용


def _query_bs(supabase, corp_code: str, years: int) -> list:
    res = (
        supabase.table("financial_statements")
        .select("*")
        .eq("corp_code", corp_code)
        .in_("account_key", BS_ACCOUNT_KEYS)
        .order("bsns_year", desc=True)
        .limit(years * len(BS_ACCOUNT_KEYS) * 2)  # CFS+OFS 대비 버퍼
        .execute()
    )
    return res.data or []
```

#### `financials.py` 엔드포인트 수정 패턴

```python
# import 추가
from app.services.financial_service import get_pl_data, get_bs_data

# get_financials 엔드포인트 수정
@router.get("/companies/{corp_code}/financials", response_model=list[FinancialStatement])
async def get_financials(
    corp_code: str,
    years: int = 5,
    chart_type: str = Query("pl", alias="type"),
    _: object = Depends(get_current_user),
):
    if chart_type not in ("pl", "bs"):
        raise HTTPException(
            status_code=400,
            detail="type은 pl 또는 bs만 지원됩니다. cf는 Story 3.5에서 구현됩니다.",
        )
    if years < 1 or years > 10:
        raise HTTPException(status_code=400, detail="years는 1~10 사이여야 합니다.")

    try:
        data = get_pl_data(corp_code, years=years) if chart_type == "pl" else get_bs_data(corp_code, years=years)
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

    return data  # 빈 배열 포함 정상 반환 (404 없음 — 프론트에서 빈 배열로 처리)
```

**주의:** `compare_financials`도 동일하게 `type=bs` 지원 추가 (`get_pl_data` → 분기 처리).

### Frontend 구현 패턴

#### `dashboard/page.tsx` chartType state + 탭

```tsx
// 상단 imports에 추가
import type { FinancialType } from '@/types'

// state 추가 (selectedCompanies 바로 아래)
const [chartType, setChartType] = useState<FinancialType>('pl')

// handleSelect 수정 — 기업 추가 시 P&L로 리셋
const handleSelect = (company: Company) => {
  if (isAtMax) return
  if (!selectedCompanies.find((c) => c.corp_code === company.corp_code)) {
    setSelectedCompanies((prev) => [...prev, company])
    setChartType('pl')  // 새 기업 추가 시 P&L로 초기화
  }
}

// handleRemove 수정 — 마지막 기업 제거 시 P&L로 리셋
const handleRemove = (corp_code: string) => {
  setSelectedCompanies((prev) => prev.filter((c) => c.corp_code !== corp_code))
  setNewDataCodes((prev) => prev.filter((code) => code !== corp_code))
  // 기업 목록이 비면 P&L로 리셋
  if (selectedCompanies.length <= 1) setChartType('pl')
}

// useFinancialData에 chartType 전달
const { data: financials = [], isLoading: singleLoading, error: singleError } = useFinancialData(
  !isCompareMode ? (primaryCompany?.corp_code ?? null) : null,
  5,
  chartType,  // 추가
)

// 탭 UI — CompanyTag 목록 아래, 차트 위 (단일 기업 모드에서만 표시)
{!isCompareMode && primaryCompany && (
  <div className="flex gap-2">
    <Button
      size="sm"
      variant={chartType === 'pl' ? 'default' : 'outline'}
      onClick={() => setChartType('pl')}
    >
      P&L
    </Button>
    <Button
      size="sm"
      variant={chartType === 'bs' ? 'default' : 'outline'}
      onClick={() => setChartType('bs')}
    >
      B/S
    </Button>
  </div>
)}
```

`Button` import 추가: `import { Button } from '@/components/ui/button'`

#### `FinancialChart.tsx` B/S 렌더링

기존 P&L 렌더링 분기와 B/S 렌더링 분기를 `type` prop으로 분리:

```tsx
interface Props {
  data: FinancialStatement[]
  isLoading: boolean
  companyName?: string
  type?: FinancialType  // 추가 (기본값 'pl')
}

export function FinancialChart({ data, isLoading, companyName, type = 'pl' }: Props) {
  // ... isLoading Skeleton 동일

  // 빈 데이터 처리 (isLoading 이후)
  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        {type === 'bs'
          ? 'B/S 데이터를 제공하지 않는 기업입니다. P&L 데이터만 이용 가능합니다.'
          : '재무 데이터가 없습니다.'}
      </p>
    )
  }

  const years = [...new Set(data.map((d) => d.bsns_year))].sort()

  // P&L chartData (기존 유지)
  // B/S chartData (신규)
  if (type === 'bs') {
    const bsChartData = years.map((year) => {
      const get = (key: string) =>
        data.find((d) => d.bsns_year === year && d.account_key === key)?.amount ?? 0
      return {
        year,
        total_assets: get('total_assets'),
        total_liabilities: get('total_liabilities'),
        total_equity: get('total_equity'),
        cash_and_equivalents: get('cash_and_equivalents'),
      }
    })
    // return ComposedChart with Bar(total_assets, #2563eb), Bar(total_liabilities, #ef4444),
    //   Line(total_equity, #16a34a), Line(cash_and_equivalents, #9333ea)
  }
  // P&L 렌더링 (기존 코드 유지)
}
```

`FinancialType` import 추가: `import type { FinancialType } from '@/types'`

### 테스트 패턴

#### 기존 `test_get_financials_rejects_non_pl_type` 수정

```python
# 기존 테스트는 삭제하고 아래로 교체:

def test_get_financials_bs_type_returns_200(client):
    """type=bs 요청 시 200 반환 (Story 3.4 구현 후)"""
    rows = _make_fin_rows(
        years=2,
        account_keys=["total_assets", "total_liabilities", "total_equity", "cash_and_equivalents"]
    )
    mock_supabase = _make_supabase_mock(rows)

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        response = client.get("/api/v1/companies/005930/financials?type=bs")

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_financials_bs_returns_empty_when_no_data(client):
    """type=bs, DB에 데이터 없을 때 빈 배열 + 200 반환"""
    mock_supabase = _make_supabase_mock([])
    # sync 후에도 빈 결과
    execute_mock = mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value.order.return_value.limit.return_value.execute
    execute_mock.side_effect = [MagicMock(data=[]), MagicMock(data=[])]

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials"):
            response = client.get("/api/v1/companies/005930/financials?type=bs")

    assert response.status_code == 200
    assert response.json() == []


def test_get_financials_cf_type_returns_400(client):
    """type=cf 요청 시 여전히 400 반환 (Story 3.5에서 구현 예정)"""
    response = client.get("/api/v1/companies/005930/financials?type=cf")
    assert response.status_code == 400
```

**주의:** `_make_supabase_mock`의 `.in_` 체인은 기존 mock과 동일하게 작동함 — `BS_ACCOUNT_KEYS`도 같은 체인으로 처리됨.

### Story 3.3 학습 사항 (이번 스토리에 적용)

- **서비스 함수 격리 패턴:** `get_bs_data()`는 `get_pl_data()` 와 완전히 동일한 패턴으로 구현. `_prefer_cfs()` 재사용.
- **빈 배열 반환 vs 에러:** B/S 데이터 없음은 오류가 아님 (일부 기업은 B/S를 제공하지 않음). 400/404 없이 `[]` 반환 후 프론트에서 안내 메시지 표시.
- **기존 훅 재사용:** `useFinancialData(corpCode, years, type)` — 이미 `type` 파라미터를 지원하므로 훅 수정 불필요. `api.ts`도 수정 불필요.
- **TanStack Query 키:** `['financials', corpCode, { years, type }]` — `type='bs'`로 변경 시 자동으로 새 쿼리 실행.

### 아키텍처 준수 사항

- **API 라우트 순서:** `compare`, `new-data-status`가 `{corp_code}` 앞에 위치하는 기존 순서 유지
- **formatKRW:** FinancialChart 내부에서만 변환, 컴포넌트 밖으로 노출 금지
- **에러 코드:** 신규 추가 없음 (`DART_API_UNAVAILABLE` 기존 코드 재사용)
- **FinancialType:** `types/index.ts`에 이미 정의됨 — 신규 타입 추가 불필요

### 환경변수

추가 환경변수 불필요.

### 의도적으로 이번 스토리에서 미구현

- 비교 모드(2개+ 기업) B/S 비교 차트 → CompareChart는 현재 P&L만 지원, B/S 비교는 Story 3.5 범위 외로 postpone 또는 Story 3.5 완료 후 별도 처리. 탭 UI는 단일 기업 모드에서만 표시.
- 현금흐름(CF) 차트 → Story 3.5
- DART sync 중 B/S account key 신규 매핑 자동화 → account_mappings 수동 관리 (FR33 범위)

### Project Structure Notes

**수정 파일:**
- `backend/app/services/financial_service.py` — `BS_ACCOUNT_KEYS`, `get_bs_data()`, `_query_bs()` 추가
- `backend/app/api/v1/financials.py` — `type=bs` 지원, `get_bs_data` import, 에러 메시지 업데이트
- `backend/tests/test_financials.py` — `test_get_financials_rejects_non_pl_type` 삭제, B/S 테스트 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — `chartType` state, 탭 UI, `useFinancialData` type 전달
- `frontend/src/components/charts/FinancialChart.tsx` — `type` prop, B/S 렌더링 분기, 빈 데이터 상태

**신규 파일:** 없음

**DB (Supabase Dashboard 확인/추가):**
- `account_mappings` 테이블에 BS 항목 존재 여부 확인, 없으면 수동 INSERT

### References

- AC 출처: [epics.md - Story 3.4 B/S 핵심 항목 차트]
- B/S account_key 표준: [architecture.md - Data Architecture - account_mappings 테이블]
- DB-First 패턴: [architecture.md - Data Architecture - 캐싱 전략]
- 금액 변환 규칙: [architecture.md - Format Patterns - 금액 단위]
- 기존 패턴: [Story 1.4 구현 - financial_service.py get_pl_data()]
- FR13: Builder는 B/S 핵심 항목(자산·부채·자본·현금성 자산)을 차트로 볼 수 있다

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
