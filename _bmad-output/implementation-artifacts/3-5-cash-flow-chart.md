# Story 3.5: 현금흐름 핵심 항목 차트

Status: done

## Story

As a Builder,
I want to view Cash Flow key metrics (operating, investing, financing activities) as a chart,
so that I can assess a company's cash generation and usage alongside P&L and B/S trends.

## Acceptance Criteria

1. **[CF 탭 전환 → API 호출]** Builder가 기업을 선택한 상태에서 "현금흐름" 탭 버튼을 클릭하면 `GET /api/v1/companies/{corp_code}/financials?years=5&type=cf`가 호출되고 영업활동·투자활동·재무활동 현금흐름 데이터가 FinancialChart에 표시됨

2. **[formatKRW 규칙 + 5년치 표시]** CF 차트 렌더링 시 모든 금액은 `formatKRW()`를 통해 변환 (컴포넌트 내 직접 변환 금지), 최근 5개 사업연도 데이터 표시

3. **[Skeleton 로딩 — 레이아웃 쉬프트 없음]** CF API 응답 대기 중 `h-80` 동일한 높이의 Skeleton 표시

4. **[CF 데이터 없음 안내]** 해당 기업의 CF 데이터가 DB에 미존재할 때 "현금흐름 데이터를 제공하지 않는 기업입니다. P&L 또는 B/S 데이터를 이용해 주세요." 안내 메시지 표시

## Tasks / Subtasks

- [x] Task 1: Backend — `financial_service.py` CF 조회 함수 추가 (AC: #1, #2, #4)
  - [x] 1.1 `CF_ACCOUNT_KEYS = ["operating_cf", "investing_cf", "financing_cf"]` 상수 추가
  - [x] 1.2 `get_cf_data(corp_code: str, years: int = 5) -> list` 함수 추가 — `get_bs_data()` 패턴 그대로, `CF_ACCOUNT_KEYS` 사용
  - [x] 1.3 내부 `_query_cf(supabase, corp_code, years)` 헬퍼 함수 추가 (`.in_("account_key", CF_ACCOUNT_KEYS)` 사용)
  - [x] 1.4 기존 `_prefer_cfs()` 함수 변경 없이 재사용 (CF도 동일 CFS 우선 로직)

- [x] Task 2: Backend — `financials.py` `type=cf` 지원 추가 (AC: #1, #4)
  - [x] 2.1 `get_cf_data` import 추가
  - [x] 2.2 `get_financials` 엔드포인트: `chart_type not in ("pl", "bs")` → `chart_type not in ("pl", "bs", "cf")` 로 변경
  - [x] 2.3 `cf` 분기: `get_cf_data(corp_code, years=years)` 호출 (빈 결과 시 `[]` 반환 — 404 아님)
  - [x] 2.4 `compare_financials` 엔드포인트도 동일하게 `cf` 지원 추가
  - [x] 2.5 400 에러 메시지 갱신: `"type은 pl, bs, cf만 지원됩니다."`

- [x] Task 3: Backend — `test_financials.py` 수정 및 CF 테스트 추가 (AC: #1, #2, #4)
  - [x] 3.1 기존 `test_get_financials_rejects_cf_type` 테스트 삭제 (이제 cf도 지원)
  - [x] 3.2 `test_get_financials_cf_returns_db_data` 추가 — DB에 CF 데이터 있을 때 200 반환
  - [x] 3.3 `test_get_financials_rejects_invalid_type` 추가 — `type=invalid`는 400 반환
  - [x] 3.4 pytest 전체 통과 확인 (8/8 통과)

- [x] Task 4: Frontend — `dashboard/page.tsx` 현금흐름 탭 추가 (AC: #1, #3)
  - [x] 4.1 `chartType` state 타입을 `'pl' | 'bs'` → `FinancialType` (`'pl' | 'bs' | 'cf'`)으로 변경
  - [x] 4.2 기존 탭 버튼 영역에 "현금흐름" 버튼 추가 (P&L / B/S / 현금흐름)
  - [x] 4.3 `useFinancialData` 호출에 이미 `chartType` 전달 중 — 변경 없음

- [x] Task 5: Frontend — `FinancialChart.tsx` CF 렌더링 모드 추가 (AC: #2, #3, #4)
  - [x] 5.1 `CF_KEYS`, `CF_LABELS` 상수 추가
  - [x] 5.2 `isCf = type === 'cf'` 분기 추가
  - [x] 5.3 CF 차트 렌더링: 3개 Bar 차트 (영업·투자·재무 각기 다른 색상)
    - 영업활동: `#16a34a` (Bar)
    - 투자활동: `#ef4444` (Bar)
    - 재무활동: `#f59e0b` (Bar)
  - [x] 5.4 빈 데이터 상태: "현금흐름 데이터를 제공하지 않는 기업입니다. P&L 또는 B/S 데이터를 이용해 주세요."
  - [x] 5.5 `keys` / `labels` / 렌더링 분기 기존 `isBs` 패턴 그대로 확장

- [x] Task 6: `npm run build` 통과 확인 (TypeScript 에러 없음)

## Dev Notes

### 핵심 패턴 — Story 3.4에서 확립된 패턴 그대로 반복

Story 3.4(B/S)에서 다음 패턴이 완전히 확립됨. CF는 동일 패턴 반복:

**Backend `financial_service.py` 완성 패턴:**
```python
CF_ACCOUNT_KEYS = ["operating_cf", "investing_cf", "financing_cf"]

def get_cf_data(corp_code: str, years: int = 5) -> list:
    """DB-First CF 조회. DB에 데이터 없으면 DART sync 후 재조회."""
    supabase = get_supabase_client()
    rows = _query_cf(supabase, corp_code, years)
    if not rows:
        try:
            sync_company_financials(corp_code, years=years)
            rows = _query_cf(supabase, corp_code, years)
        except Exception as e:
            logger.warning(f"DART sync failed for {corp_code}: {e}")
            raise
    return _prefer_cfs(rows, years)

def _query_cf(supabase, corp_code: str, years: int) -> list:
    res = (
        supabase.table("financial_statements")
        .select("*")
        .eq("corp_code", corp_code)
        .in_("account_key", CF_ACCOUNT_KEYS)
        .order("bsns_year", desc=True)
        .limit(years * len(CF_ACCOUNT_KEYS) * 2)
        .execute()
    )
    return res.data or []
```

**Backend `financials.py` 변경 포인트:**
```python
# import 추가
from app.services.financial_service import get_bs_data, get_cf_data, get_pl_data

# get_financials 엔드포인트
if chart_type not in ("pl", "bs", "cf"):
    raise HTTPException(status_code=400, detail="type은 pl, bs, cf만 지원됩니다.")

# 분기 추가
if chart_type == "bs":
    data = get_bs_data(corp_code, years=years)
elif chart_type == "cf":
    data = get_cf_data(corp_code, years=years)
else:
    data = get_pl_data(corp_code, years=years)

# compare_financials 엔드포인트도 동일하게:
if chart_type == "bs":
    fetch = get_bs_data
elif chart_type == "cf":
    fetch = get_cf_data
else:
    fetch = get_pl_data
```

**Frontend `dashboard/page.tsx` 탭 추가:**

현재 상태 (Story 3.4 완료 후):
```tsx
const [chartType, setChartType] = useState<'pl' | 'bs'>('pl')
```

변경:
```tsx
const [chartType, setChartType] = useState<FinancialType>('pl')  // 'pl' | 'bs' | 'cf'
```

탭 버튼에 "현금흐름" 추가:
```tsx
<button onClick={() => setChartType('cf')}
  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
    chartType === 'cf' ? 'bg-primary text-primary-foreground' : 'border text-muted-foreground hover:bg-muted'
  }`}>
  현금흐름
</button>
```

**Frontend `FinancialChart.tsx` CF 분기 추가:**

현재 상태:
```tsx
const CF_KEYS = ['operating_cf', 'investing_cf', 'financing_cf'] as const
const CF_LABELS: Record<string, string> = {
  operating_cf: '영업활동현금흐름',
  investing_cf: '투자활동현금흐름',
  financing_cf: '재무활동현금흐름',
}

// isBs 분기 이후에 추가
const isCf = type === 'cf'
const keys = isBs ? BS_KEYS : isCf ? CF_KEYS : PL_KEYS
const labels = isBs ? BS_LABELS : isCf ? CF_LABELS : PL_LABELS
```

CF 렌더링 (3개 Bar):
```tsx
{isCf ? (
  <>
    <Bar dataKey="operating_cf" name="operating_cf" fill="#16a34a" opacity={0.8} />
    <Bar dataKey="investing_cf" name="investing_cf" fill="#ef4444" opacity={0.8} />
    <Bar dataKey="financing_cf" name="financing_cf" fill="#f59e0b" opacity={0.8} />
  </>
) : isBs ? (
  // 기존 BS 렌더링
) : (
  // 기존 PL 렌더링
)}
```

빈 상태 메시지 분기:
```tsx
{isCf ? '현금흐름 데이터를 제공하지 않는 기업입니다. P&L 또는 B/S 데이터를 이용해 주세요.'
  : isBs ? '재무상태표 데이터가 없습니다.'
  : '손익계산서 데이터가 없습니다.'}
```

### 테스트 패턴

```python
def test_get_financials_cf_returns_db_data(client):
    """type=cf 요청 시 CF 데이터 반환"""
    cf_keys = ["operating_cf", "investing_cf", "financing_cf"]
    rows = _make_fin_rows(years=2, account_keys=cf_keys)
    mock_supabase = _make_supabase_mock(rows)

    with patch("app.services.financial_service.get_supabase_client", return_value=mock_supabase):
        with patch("app.services.financial_service.sync_company_financials"):
            response = client.get("/api/v1/companies/005930/financials?years=3&type=cf")

    assert response.status_code == 200
    result = response.json()
    assert len(result) > 0
    assert all(r["account_key"] in cf_keys for r in result)


def test_get_financials_rejects_invalid_type(client):
    """type=invalid 요청 시 400 반환"""
    response = client.get("/api/v1/companies/005930/financials?type=invalid")
    assert response.status_code == 400
```

### DB 사전 확인 (Supabase)

CF 데이터는 `account_mappings` 테이블의 CF 항목이 있어야 함:
```sql
SELECT * FROM account_mappings WHERE category = 'cf';
```

없으면 수동으로 추가:
```sql
INSERT INTO account_mappings (account_nm, account_key, display_name, category) VALUES
  ('영업활동으로인한현금흐름', 'operating_cf', '영업활동현금흐름', 'cf'),
  ('투자활동으로인한현금흐름', 'investing_cf', '투자활동현금흐름', 'cf'),
  ('재무활동으로인한현금흐름', 'financing_cf', '재무활동현금흐름', 'cf')
ON CONFLICT (account_nm) DO NOTHING;
```

**⚠️ 주의:** DART API의 CF 계정과목명은 회사마다 다를 수 있음. `dart_client.py`의 `sync_company_financials`가 `account_mappings`를 참조해서 매핑하는 방식 확인 필요.

### 수정 대상 파일

- `backend/app/services/financial_service.py` — CF 상수 + `get_cf_data()` + `_query_cf()` 추가
- `backend/app/api/v1/financials.py` — `type=cf` 지원, `get_cf_data` import
- `backend/tests/test_financials.py` — `test_get_financials_rejects_cf_type` 삭제, CF 테스트 2개 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — `chartType` 타입을 `FinancialType`으로, 현금흐름 탭 추가
- `frontend/src/components/charts/FinancialChart.tsx` — CF_KEYS, CF_LABELS, CF 렌더링 분기 추가

### Project Structure Notes

- 모든 파일 경로는 Story 3.4와 동일
- `FinancialType = 'pl' | 'bs' | 'cf'` — `types/index.ts`에 이미 정의됨 (변경 없음)
- `useFinancialData(corpCode, years, type)` — 이미 `type` 파라미터 지원 (변경 없음)
- `chartType` state — Story 3.4에서 `'pl' | 'bs'`로 추가됨, 이번에 `FinancialType`으로 확장

### References

- [Source: architecture.md - DB-First Caching Strategy]
- [Source: architecture.md - API & Communication Patterns]
- [Source: architecture.md - Financial Data Service]
- [Source: epics.md - Epic 3, Story 3.5]
- [Source: backend/app/services/financial_service.py - BS 패턴 참조]
- [Source: frontend/src/components/charts/FinancialChart.tsx - type prop 패턴 참조]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Task 1: `CF_ACCOUNT_KEYS`, `get_cf_data()`, `_query_cf()` 추가 — BS 패턴 그대로 복사, `_prefer_cfs()` 재사용
- Task 2: `get_financials`, `compare_financials` 양쪽에 `type=cf` 지원 추가. if/elif/else로 3분기 처리
- Task 3: `test_get_financials_rejects_cf_type` 삭제 → `test_get_financials_cf_returns_db_data`, `test_get_financials_rejects_invalid_type` 추가. 8/8 통과
- Task 4: `chartType` 타입을 `FinancialType`으로 확장, 탭 버튼을 배열 map으로 리팩터링 (pl/bs/cf 3개)
- Task 5: `CF_KEYS`, `CF_LABELS` 상수 추가, `isCf` 분기로 3-Bar CF 차트 렌더링, 빈 상태 메시지 CF 분기 추가
- Task 6: `npm run build` TypeScript 에러 없음, 빌드 성공

### File List

- `backend/app/services/financial_service.py`
- `backend/app/api/v1/financials.py`
- `backend/tests/test_financials.py`
- `frontend/src/app/(auth)/dashboard/page.tsx`
- `frontend/src/components/charts/FinancialChart.tsx`
