# Story 3.3: APScheduler DART 자동 갱신 및 신규 데이터 알림

Status: done

## Story

As a 시스템,
I want to automatically sync DART data daily and notify users when new quarter data arrives,
So that analysis sets always reflect the latest financial information without manual intervention.

## Acceptance Criteria

1. **[APScheduler 자동 갱신 - 매일 07:00 KST]** FastAPI 서버가 실행 중이고 APScheduler가 설정된 상태에서 매일 07:00 KST에 스케줄이 트리거되면, `dart_client.py`를 통해 `companies` 테이블에 등록된 모든 기업의 최신 재무 데이터를 조회하고 `financial_statements`에 UPSERT해야 한다. 갱신 완료 후 서버 로그에 `[DART_SYNC] 완료: {n}개 기업, {m}개 레코드 갱신` 형식으로 기록되어야 한다.

2. **[신규 분기 데이터 알림 - ● 인디케이터]** 자동 갱신 후 기존에 없던 신규 분기 데이터가 추가되면, Builder가 해당 기업이 포함된 분석 세트를 불러올 때 기업명 옆에 "●" 신규 데이터 알림 인디케이터가 표시되어야 한다. 차트는 최신 분기 데이터를 자동으로 포함해야 한다 (FR21 — DB-First 캐싱으로 자동 충족).

3. **[DART 오류 - 데이터 보존 및 로그]** DART 자동 갱신 중 API 오류가 발생하면, 기존 DB 데이터는 손상되지 않고 유지되어야 한다. 서버 로그에 `[DART_SYNC] 실패: {corp_code} - {error}` 오류가 기록되어야 한다. 오류가 발생한 기업은 건너뛰고 나머지 기업은 계속 갱신되어야 한다.

4. **[API 한도 초과 방지]** 일일 API 호출 누적이 18,000건을 초과하면 남은 기업 갱신을 중단하고 `[DART_SYNC] 한도 초과 방지: 조기 종료` 로그를 남겨야 한다 (NFR-I1: DART 20,000건/일).

## Tasks / Subtasks

- [ ] Task 1: DB Migration — `companies` 테이블 `last_new_data_at` 컬럼 추가
  - [ ] 1.1 Supabase Dashboard SQL Editor에서 실행:
    ```sql
    ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_new_data_at TIMESTAMPTZ NULL;
    ```
  - [ ] 1.2 마이그레이션 적용 확인 (테이블 컬럼 목록 확인)

- [ ] Task 2: Backend — `sync_all_companies()` 함수 구현 (AC: #1, #2, #3, #4)
  - [ ] 2.1 `backend/app/services/dart_client.py`에 `sync_all_companies()` 함수 추가
  - [ ] 2.2 `companies` 테이블에서 모든 `corp_code` 목록 조회 (DB 오류 시 즉시 에러 로그 후 종료)
  - [ ] 2.3 각 기업마다: 동기화 전 기존 `bsns_year` 목록 조회 → `sync_company_financials()` 호출 → 동기화 후 `bsns_year` 목록 재조회 → 신규 연도 감지 시 `companies.last_new_data_at` 업데이트
  - [ ] 2.4 API 호출 카운터 추적: 기업당 `years=5` 호출로 추정 (+5씩 누적), 18,000건 초과 시 루프 중단 + `[DART_SYNC] 한도 초과 방지: 조기 종료` 로그
  - [ ] 2.5 기업별 예외 처리: `except Exception as e` → `logger.error(f"[DART_SYNC] 실패: {corp_code} - {e}")` → 다음 기업으로 계속 진행
  - [ ] 2.6 완료 로그: `logger.info(f"[DART_SYNC] 완료: {n}개 기업, {m}개 레코드 갱신")`
  - [ ] 2.7 반환값: `{"companies_synced": n, "records_synced": m}` dict

- [ ] Task 3: Backend — `scheduler/tasks.py` 구현 (AC: #1)
  - [ ] 3.1 `backend/app/scheduler/tasks.py` 구현:
    - `from apscheduler.schedulers.asyncio import AsyncIOScheduler`
    - `from app.services.dart_client import sync_all_companies`
  - [ ] 3.2 `start_scheduler()` 함수: `AsyncIOScheduler(timezone="Asia/Seoul")` 생성, `add_job(sync_all_companies, 'cron', hour=7, minute=0, misfire_grace_time=3600)`, `scheduler.start()`, scheduler 반환

- [ ] Task 4: Backend — `main.py` lifespan APScheduler 통합 (AC: #1)
  - [ ] 4.1 `main.py` lifespan에서 TODO 코드 활성화:
    - `from app.scheduler.tasks import start_scheduler`
    - 시작 시: `scheduler = start_scheduler()`
    - 종료 시: `scheduler.shutdown(wait=False)`

- [ ] Task 5: Backend — `companies.py` 신규 데이터 상태 엔드포인트 추가 (AC: #2)
  - [ ] 5.1 `GET /api/v1/companies/new-data-status?codes=005930,035720` 엔드포인트 추가
  - [ ] 5.2 `codes` 쿼리 파라미터로 `,` 구분된 corp_code 목록 수신
  - [ ] 5.3 `companies` 테이블에서 해당 기업들의 `last_new_data_at` 조회
  - [ ] 5.4 `last_new_data_at IS NOT NULL`이면서 최근 7일 이내인 corp_code 목록 반환
  - [ ] 5.5 응답: `{ "new_data_codes": ["005930"] }` (빈 배열도 허용)
  - [ ] 5.6 인증 필요 (`get_current_user` Depends)

- [ ] Task 6: Backend — 테스트 작성 (AC: #1, #2, #3, #4)
  - [ ] 6.1 `backend/tests/test_dart_client.py`에 `TestSyncAllCompanies` 클래스 추가
    - [ ] 6.1.1 `test_sync_all_companies_success` — 2개 기업 성공, 로그 형식 검증
    - [ ] 6.1.2 `test_sync_all_companies_partial_failure` — 1개 실패해도 나머지 계속, 에러 로그 검증
    - [ ] 6.1.3 `test_sync_all_companies_rate_limit` — 18,000건 초과 시 조기 종료 로그 검증
    - [ ] 6.1.4 `test_sync_all_companies_new_data_detected` — 신규 bsns_year 감지 시 `last_new_data_at` 업데이트 확인
    - [ ] 6.1.5 `test_sync_all_companies_no_companies` — companies 테이블 비어있으면 `완료: 0개 기업` 로그
  - [ ] 6.2 `backend/tests/test_companies.py`에 `TestNewDataStatus` 클래스 추가
    - [ ] 6.2.1 `test_new_data_status_returns_recent_companies` — 7일 내 new_data 있는 기업 반환
    - [ ] 6.2.2 `test_new_data_status_excludes_old_data` — 7일 이전 new_data는 제외
    - [ ] 6.2.3 `test_new_data_status_empty_when_no_new_data` — 신규 데이터 없으면 빈 배열
    - [ ] 6.2.4 `test_new_data_status_requires_auth_401` — 인증 없으면 401
  - [ ] 6.3 `backend/tests/test_scheduler.py` 신규 생성
    - [ ] 6.3.1 `test_start_scheduler_returns_running_scheduler`
    - [ ] 6.3.2 `test_scheduler_has_daily_cron_job`
  - [ ] 6.4 pytest 전체 통과 확인

- [ ] Task 7: Frontend — `api.ts` 신규 데이터 상태 조회 함수 추가 (AC: #2)
  - [ ] 7.1 `getNewDataStatus(codes: string[]): Promise<{ new_data_codes: string[] }>` 함수 추가 → `apiGet(...)` 경유

- [ ] Task 8: Frontend — Dashboard 신규 데이터 상태 연동 (AC: #2)
  - [ ] 8.1 `dashboard/page.tsx`에 `newDataCodes: string[]` state 추가 (기본값 `[]`)
  - [ ] 8.2 `handleLoadAnalysisSet` 내부에서 분석 세트 로드 후 `getNewDataStatus(company_codes)` 호출 → `setNewDataCodes(data.new_data_codes)`
  - [ ] 8.3 `handleRemove`로 기업 제거 시 `newDataCodes`에서도 해당 corp_code 제거

- [ ] Task 9: Frontend — CompanyTag "●" 인디케이터 표시 (AC: #2)
  - [ ] 9.1 `dashboard/page.tsx` CompanyTag 렌더링 부분에서 `newDataCodes`에 포함된 기업이면 기업명 옆에 `<span className="text-blue-500 text-xs ml-1" title="새로운 분기 데이터가 추가되었습니다">●</span>` 표시

- [ ] Task 10: Next.js 빌드 통과 확인
  - [ ] 10.1 `npm run build` TypeScript 에러 없이 통과

## Dev Notes

### Critical: 아키텍처 강제 규칙 (위반 시 PR 거부)

- 컴포넌트에서 `fetch()` 직접 호출 금지 → 반드시 `lib/api.ts` 경유
- DART API 호출은 `dart_client.py`에서만 허용 — 다른 모듈에서 OpenDartReader 직접 import 금지
- `shadcn/ui` 컴포넌트 직접 수정 금지 (`frontend/src/components/ui/` 폴더)

### DB Migration (선행 필수)

```sql
-- Supabase Dashboard SQL Editor에서 실행
ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_new_data_at TIMESTAMPTZ NULL;
```

**주의:** 이 컬럼이 없으면 Task 2, 5, 6이 모두 실패함. 반드시 Task 1부터 진행.

### Backend 구현 패턴

#### `sync_all_companies()` 전체 패턴

```python
# backend/app/services/dart_client.py 에 추가

DART_RATE_LIMIT_THRESHOLD = 18_000
YEARS_PER_COMPANY = 5  # sync_company_financials 기본 years=5

def sync_all_companies() -> dict:
    """모든 등록 기업의 DART 데이터 자동 갱신. APScheduler 07:00 KST에 호출.
    - 기업별 예외를 격리하여 일부 실패해도 전체 중단 방지
    - DART 일일 API 호출 한도(20,000건) 초과 방지: 18,000건에서 조기 종료
    """
    supabase = get_supabase_client()

    try:
        corp_res = supabase.table("companies").select("corp_code").execute()
        corp_codes = [row["corp_code"] for row in (corp_res.data or [])]
    except Exception as e:
        logger.error(f"[DART_SYNC] 기업 목록 조회 실패: {e}")
        return {"companies_synced": 0, "records_synced": 0}

    total_synced = 0
    records_synced = 0
    api_call_count = 0

    for corp_code in corp_codes:
        if api_call_count >= DART_RATE_LIMIT_THRESHOLD:
            logger.warning("[DART_SYNC] 한도 초과 방지: 조기 종료")
            break

        try:
            # 동기화 전 기존 bsns_year 목록 조회
            before_res = (
                supabase.table("financial_statements")
                .select("bsns_year")
                .eq("corp_code", corp_code)
                .execute()
            )
            existing_years = {row["bsns_year"] for row in (before_res.data or [])}

            # DART 동기화
            result = sync_company_financials(corp_code, years=YEARS_PER_COMPANY)
            records_synced += result["synced_rows"]
            api_call_count += YEARS_PER_COMPANY
            total_synced += 1

            # 신규 bsns_year 감지
            after_res = (
                supabase.table("financial_statements")
                .select("bsns_year")
                .eq("corp_code", corp_code)
                .execute()
            )
            new_years = {row["bsns_year"] for row in (after_res.data or [])} - existing_years

            if new_years:
                supabase.table("companies").update(
                    {"last_new_data_at": datetime.utcnow().isoformat()}
                ).eq("corp_code", corp_code).execute()

        except Exception as e:
            logger.error(f"[DART_SYNC] 실패: {corp_code} - {e}")
            # 기존 데이터 손상 없음 — UPSERT 방식이므로 실패 시 원본 유지
            api_call_count += YEARS_PER_COMPANY  # 실패해도 카운트 추정

    logger.info(f"[DART_SYNC] 완료: {total_synced}개 기업, {records_synced}개 레코드 갱신")
    return {"companies_synced": total_synced, "records_synced": records_synced}
```

**주의:** `datetime` import는 이미 파일 상단에 있음.

#### `start_scheduler()` 패턴

```python
# backend/app/scheduler/tasks.py 전체 교체

"""
APScheduler 태스크 — 완전 구현: Story 3.3
매일 07:00 KST DART 데이터 자동 갱신
[Source: architecture.md - Infrastructure & Deployment]
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.dart_client import sync_all_companies

logger = logging.getLogger(__name__)


def start_scheduler() -> AsyncIOScheduler:
    """APScheduler 초기화 및 시작. FastAPI lifespan에서 호출."""
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        sync_all_companies,
        "cron",
        hour=7,
        minute=0,
        misfire_grace_time=3600,  # 1시간 내 서버 재시작 시 자동 실행
        id="dart_daily_sync",
    )
    scheduler.start()
    logger.info("[SCHEDULER] APScheduler 시작: DART 일일 동기화 07:00 KST")
    return scheduler
```

#### `main.py` lifespan 수정 패턴

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.scheduler.tasks import start_scheduler
    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)
    logger.info("[SCHEDULER] APScheduler 종료")
```

**주의:** `import logging`과 `logger = logging.getLogger(__name__)` 추가 필요.

#### 신규 데이터 상태 엔드포인트 패턴 (`companies.py`에 추가)

```python
# 7일 이내 신규 데이터가 추가된 기업 조회
from datetime import datetime, timedelta

@router.get("/companies/new-data-status")
async def get_new_data_status(
    codes: str,  # "005930,035720" 형식
    user=Depends(get_current_user)
):
    """분석 세트의 기업 중 신규 데이터(7일 이내)가 있는 기업 코드 목록 반환"""
    supabase = get_supabase_client()
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return {"new_data_codes": []}

    threshold = (datetime.utcnow() - timedelta(days=7)).isoformat()
    try:
        res = (
            supabase.table("companies")
            .select("corp_code")
            .in_("corp_code", code_list)
            .gte("last_new_data_at", threshold)
            .execute()
        )
    except Exception:
        return {"new_data_codes": []}  # 에러 시 빈 배열 반환 (알림 실패는 치명적이지 않음)

    return {"new_data_codes": [row["corp_code"] for row in (res.data or [])]}
```

**주의:** 이 엔드포인트는 `/companies/search` 보다 먼저 라우터에 등록해야 함 (경로 충돌 방지를 위해 `/companies/{corp_code}` 보다 앞에 위치).

### Backend 테스트 패턴

#### `TestSyncAllCompanies` mock 전략

```python
# test_dart_client.py에 추가
import pytest
from unittest.mock import MagicMock, patch, call
from app.services.dart_client import sync_all_companies

class TestSyncAllCompanies:
    def test_sync_all_companies_success(self, caplog):
        mock_sb = MagicMock()
        # companies 목록 반환
        mock_sb.table.return_value.select.return_value.execute.return_value.data = [
            {"corp_code": "000001"},
            {"corp_code": "000002"},
        ]
        # before/after financial_statements (bsns_year 조회) — 신규 없음
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        with patch("app.services.dart_client.get_supabase_client", return_value=mock_sb):
            with patch("app.services.dart_client.sync_company_financials", return_value={"synced_rows": 10}):
                with caplog.at_level("INFO"):
                    result = sync_all_companies()

        assert result["companies_synced"] == 2
        assert "[DART_SYNC] 완료: 2개 기업" in caplog.text

    def test_sync_all_companies_partial_failure(self, caplog):
        """일부 기업 실패해도 계속 진행 + 에러 로그 기록"""
        ...

    def test_sync_all_companies_rate_limit(self, caplog):
        """18,000건 초과 시 조기 종료"""
        # 4,000개 기업 모킹 (5 calls/company × 3,600 = 18,000 → 3,601번째에서 멈춤)
        ...

    def test_sync_all_companies_new_data_detected(self):
        """신규 bsns_year 감지 시 last_new_data_at 업데이트"""
        mock_sb = MagicMock()
        # before: 2022, 2023만 있음
        # after: 2022, 2023, 2024 있음 → 신규
        before_result = MagicMock(data=[{"bsns_year": "2022"}, {"bsns_year": "2023"}])
        after_result = MagicMock(data=[{"bsns_year": "2022"}, {"bsns_year": "2023"}, {"bsns_year": "2024"}])
        # side_effect: companies 조회(1) → before(1) → after(1) 순으로 호출
        # update().eq().execute() 호출 확인
        ...
```

**주의:** `sync_all_companies`는 `get_supabase_client`와 `sync_company_financials` 둘 다 patch 필요.

#### `TestNewDataStatus` mock 패턴

```python
# test_companies.py의 TestNewDataStatus

class TestNewDataStatus:
    def test_new_data_status_returns_recent_companies(self, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.gte.return_value.execute.return_value.data = [
            {"corp_code": "005930"}
        ]
        with patch("app.api.v1.companies.get_supabase_client", return_value=mock_sb):
            res = client.get("/api/v1/companies/new-data-status?codes=005930,035720")
        assert res.status_code == 200
        assert res.json() == {"new_data_codes": ["005930"]}

    def test_new_data_status_requires_auth_401(self, client):
        # client fixture는 unauthenticated (no override)
        res = client.get("/api/v1/companies/new-data-status?codes=005930")
        assert res.status_code == 401
```

**주의:** `test_companies.py`의 기존 `client` fixture는 인증된 사용자 override를 사용하므로 인증 테스트엔 별도 unauthenticated client 필요 (기존 패턴 참조).

#### `test_scheduler.py` 패턴

```python
from app.scheduler.tasks import start_scheduler

class TestScheduler:
    def test_start_scheduler_returns_running_scheduler(self):
        with patch("app.scheduler.tasks.sync_all_companies"):
            scheduler = start_scheduler()
        assert scheduler.running is True
        scheduler.shutdown(wait=False)

    def test_scheduler_has_daily_cron_job(self):
        with patch("app.scheduler.tasks.sync_all_companies"):
            scheduler = start_scheduler()
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "dart_daily_sync"
        scheduler.shutdown(wait=False)
```

### Frontend 구현 패턴

#### `api.ts` 추가 함수

```typescript
// Story 3.3: 신규 데이터 상태 조회
export async function getNewDataStatus(codes: string[]): Promise<{ new_data_codes: string[] }> {
  if (codes.length === 0) return { new_data_codes: [] }
  return apiGet<{ new_data_codes: string[] }>(
    `/api/v1/companies/new-data-status?codes=${encodeURIComponent(codes.join(','))}`
  )
}
```

#### `dashboard/page.tsx` 수정 포인트

```tsx
// 추가 state
const [newDataCodes, setNewDataCodes] = useState<string[]>([])

// handleLoadAnalysisSet 수정
const handleLoadAnalysisSet = async (setId: string) => {
  const data = await loadSet.mutateAsync(setId)
  const restored: Company[] = data.company_codes.slice(0, MAX_COMPANIES).map((code) => ({
    corp_code: code,
    company_name: code,
    stock_code: null,
    is_listed: true,
    created_at: '',
  }))
  setSelectedCompanies(restored)

  // 신규 데이터 상태 조회 (실패해도 UI에 영향 없음)
  try {
    const status = await getNewDataStatus(data.company_codes)
    setNewDataCodes(status.new_data_codes)
  } catch {
    setNewDataCodes([])
  }
}

// handleRemove 수정: newDataCodes에서도 제거
const handleRemove = (corp_code: string) => {
  setSelectedCompanies((prev) => prev.filter((c) => c.corp_code !== corp_code))
  setNewDataCodes((prev) => prev.filter((code) => code !== corp_code))
}
```

#### CompanyTag "●" 인디케이터 (dashboard/page.tsx 렌더링 부분)

```tsx
{selectedCompanies.map((c, idx) => (
  <div
    key={c.corp_code}
    className="flex items-center gap-1 px-3 py-1 rounded-full text-sm border"
    style={{
      backgroundColor: `${COMPANY_COLORS[idx % COMPANY_COLORS.length]}18`,
      borderColor: COMPANY_COLORS[idx % COMPANY_COLORS.length],
    }}
  >
    <span>{c.company_name}</span>
    {newDataCodes.includes(c.corp_code) && (
      <span
        className="text-blue-500 text-xs ml-1"
        title="새로운 분기 데이터가 추가되었습니다"
      >
        ●
      </span>
    )}
    {c.stock_code && (
      <span className="text-xs text-gray-500 ml-1">{c.stock_code}</span>
    )}
    <button
      onClick={() => handleRemove(c.corp_code)}
      className="ml-1 text-gray-400 hover:text-gray-600"
      aria-label={`${c.company_name} 제거`}
    >
      ×
    </button>
  </div>
))}
```

### Story 3.2 학습 사항 (이번 스토리에 적용)

**기업별 예외 격리:** `sync_all_companies()`에서 각 기업 처리를 try/except로 감싸서 한 기업 실패가 전체 동기화를 중단시키지 않도록 함.

**APScheduler AsyncIOScheduler:** FastAPI 비동기 환경에서는 `BackgroundScheduler` 대신 `AsyncIOScheduler` 사용. lifespan에서 시작/종료 관리.

**DART API 호출 추정:** `sync_company_financials`는 `years` 파라미터만큼 DART API를 호출함. 정확한 카운트 대신 `years_per_company` 상수로 추정하여 한도 추적.

**신규 데이터 감지:** UPSERT는 기존 데이터를 덮어쓰므로 `bsns_year` 비교로 신규 연도 추가 여부 감지.

**에러 허용 설계:** `get_new_data_status` 엔드포인트 내부 DB 오류 시 빈 배열 반환 (알림 실패는 사용성에 영향 없음).

### 아키텍처 준수 사항

- **에러 코드**: 신규 추가 없음 (기존 로그 패턴만)
- **TanStack Query 키**: 새 query 없음 (getNewDataStatus는 mutation-like 동작이므로 직접 호출)
- **APScheduler**: `apscheduler`는 `requirements.txt`에 이미 포함 (`pip install apscheduler` 완료 가정)
- **DART 격리**: `sync_all_companies()`도 `dart_client.py`에 위치 (격리 규칙 준수)
- **오류 격리**: 기업별 예외 처리로 기존 데이터 안전 보장

### 환경변수

추가 환경변수 불필요. 기존 `DART_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`로 충분.

### 의도적으로 이번 스토리에서 미구현

- B/S 차트 → Story 3.4
- 현금흐름 차트 → Story 3.5
- 공유 링크 → Epic 4
- DART sync 수동 트리거 Admin UI → 범위 외

### Project Structure Notes

**수정:**
- `backend/app/services/dart_client.py` — `sync_all_companies()` 함수 추가
- `backend/app/scheduler/tasks.py` — `start_scheduler()` 완전 구현
- `backend/app/main.py` — lifespan APScheduler 코드 활성화
- `backend/app/api/v1/companies.py` — `GET /companies/new-data-status` 엔드포인트 추가
- `frontend/src/lib/api.ts` — `getNewDataStatus()` 함수 추가
- `frontend/src/app/(auth)/dashboard/page.tsx` — `newDataCodes` state + "●" 인디케이터

**신규 생성:**
- `backend/tests/test_scheduler.py`

**DB Migration (Supabase Dashboard에서 수동):**
- `companies` 테이블에 `last_new_data_at TIMESTAMPTZ NULL` 컬럼 추가

### References

- AC 출처: [epics.md - Story 3.3 APScheduler DART 자동 갱신 및 신규 데이터 알림]
- APScheduler 설정: [architecture.md - Infrastructure & Deployment - scheduler/tasks.py]
- DART 격리 원칙: [architecture.md - DART API 격리 경계]
- DB 스키마: [architecture.md - Core Architectural Decisions - companies 테이블]
- 기존 sync 패턴: [Story 1.2 구현 - dart_client.py sync_company_financials()]
- NFR-I1: DART 일일 20,000건 한도
- NFR-R1: DART 자동 업데이트 성공률 95%+

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
