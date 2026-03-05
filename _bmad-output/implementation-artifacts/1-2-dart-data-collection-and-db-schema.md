# Story 1.2: DART 데이터 수집 및 DB 스키마 구축

Status: review

## Story

As a 시스템,
I want to connect to DART OpenAPI and store financial data in a structured database,
So that company financial data can be served instantly without repeated API calls.

## Acceptance Criteria

1. **[DB 스키마 생성]** Supabase Dashboard SQL Editor에서 스키마 SQL이 실행되면, `companies`, `financial_statements`, `account_mappings` 테이블이 올바른 컬럼·타입·제약조건으로 생성되어야 한다

2. **[DART API 연동]** DART API Key가 `backend/.env`에 설정된 상태에서 `dart_client.py`의 함수가 호출되면, DART OpenAPI에서 재무 데이터를 조회하고 `financial_statements` 테이블에 영구 저장해야 한다. OpenDartReader는 오직 `dart_client.py`에서만 import 되어야 한다 (다른 모듈 직접 import 금지)

3. **[UPSERT 중복 방지]** 동일한 기업·연도 데이터를 두 번 수집할 때 INSERT가 실행되면, `UNIQUE(corp_code, bsns_year, reprt_code, fs_div, account_key)` 제약으로 중복 없이 UPSERT 처리되어야 한다

4. **[보안]** FastAPI 서버가 실행 중일 때 API 응답이 클라이언트에 전달되면, DART API Key와 Supabase Service Key가 응답 헤더·본문·프론트엔드 번들에 절대 노출되지 않아야 한다

## Tasks / Subtasks

- [x] Task 1: Supabase DB 스키마 생성 (AC: #1)
  - [x] 1.1 Supabase Dashboard → SQL Editor에서 아래 스키마 SQL 실행
  - [x] 1.2 `companies` 테이블 생성 확인 (corp_code PK)
  - [x] 1.3 `financial_statements` 테이블 생성 및 UNIQUE 제약 확인
  - [x] 1.4 `account_mappings` 테이블 생성 확인
  - [x] 1.5 기본 `account_mappings` 데이터 시딩 (P&L 핵심 계정과목)

- [x] Task 2: `backend/app/core/database.py` 구현 (AC: #2, #4)
  - [x] 2.1 Supabase Python 클라이언트 초기화 (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY` 사용)
  - [x] 2.2 `get_supabase_client()` 함수 구현 (싱글턴 패턴)
  - [x] 2.3 Service Key 사용 확인 (RLS 우회, 서버 전용)

- [x] Task 3: `backend/app/services/dart_client.py` 구현 (AC: #2, #3, #4)
  - [x] 3.1 `OpenDartReader` import 및 초기화 (`DART_API_KEY` 사용)
  - [x] 3.2 `search_companies(keyword: str) -> list[dict]` 함수 구현 (기업 검색)
  - [x] 3.3 `get_financial_statements(corp_code: str, bsns_year: str, reprt_code: str) -> list[dict]` 함수 구현
  - [x] 3.4 `sync_company_financials(corp_code: str, years: int = 5)` 함수 구현 (DART → DB UPSERT)
  - [x] 3.5 UPSERT 로직: `financial_statements` 테이블에 `on_conflict` 처리

- [x] Task 4: `backend/app/models/schemas.py` Pydantic 모델 구현 (AC: #2)
  - [x] 4.1 `Company` 스키마 (corp_code, company_name, stock_code, is_listed)
  - [x] 4.2 `FinancialStatement` 스키마 (모든 필드, snake_case)
  - [x] 4.3 `AccountMapping` 스키마

- [x] Task 5: `backend/app/api/v1/sync.py` 동기화 엔드포인트 구현 (AC: #2)
  - [x] 5.1 `POST /api/v1/sync/company/{corp_code}` 엔드포인트 구현
  - [x] 5.2 `dart_client.sync_company_financials()` 호출
  - [x] 5.3 `main.py`에 sync 라우터 등록

- [x] Task 6: 테스트 작성 및 검증 (AC: #1~#4)
  - [x] 6.1 `backend/tests/test_dart_client.py` 작성 (mock DART API)
  - [x] 6.2 `backend/tests/test_database.py` 작성 (Supabase 클라이언트 초기화 테스트)
  - [x] 6.3 pytest 실행 통과 확인 (13/13 PASS)

## Dev Notes

### DB 스키마 SQL (Supabase SQL Editor에서 실행)

```sql
-- 1. 기업 기본 정보
CREATE TABLE IF NOT EXISTS companies (
  corp_code     VARCHAR(8) PRIMARY KEY,
  company_name  VARCHAR(100) NOT NULL,
  stock_code    VARCHAR(6),
  is_listed     BOOLEAN DEFAULT true,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- 2. DART 수집 재무 데이터 (캐시)
CREATE TABLE IF NOT EXISTS financial_statements (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  corp_code     VARCHAR(8) REFERENCES companies(corp_code),
  bsns_year     VARCHAR(4) NOT NULL,
  reprt_code    VARCHAR(5) NOT NULL,
  fs_div        VARCHAR(3) NOT NULL,
  account_key   VARCHAR(50) NOT NULL,
  account_nm    VARCHAR(100),
  amount        BIGINT,
  synced_at     TIMESTAMPTZ DEFAULT now(),
  UNIQUE(corp_code, bsns_year, reprt_code, fs_div, account_key)
);

-- 3. 계정과목 표준화 매핑
CREATE TABLE IF NOT EXISTS account_mappings (
  account_nm    VARCHAR(100) PRIMARY KEY,
  account_key   VARCHAR(50) NOT NULL,
  display_name  VARCHAR(100),
  category      VARCHAR(20)
);

-- 4. 기본 P&L 계정과목 시딩
INSERT INTO account_mappings (account_nm, account_key, display_name, category) VALUES
  ('매출액', 'revenue', '매출액', 'pl'),
  ('영업이익', 'operating_profit', '영업이익', 'pl'),
  ('당기순이익', 'net_income', '당기순이익', 'pl'),
  ('매출총이익', 'gross_profit', '매출총이익', 'pl'),
  ('매출원가', 'cost_of_sales', '매출원가', 'pl')
ON CONFLICT (account_nm) DO NOTHING;
```

> ⚠️ `analysis_sets`, `user_profiles` 테이블은 Story 2.1, 3.1에서 생성 — 이번 스토리에서 미포함

### database.py 구현 패턴

```python
# backend/app/core/database.py
from supabase import create_client, Client
from app.core.config import settings

_supabase_client: Client | None = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY  # ⚠️ Service Key 사용 (RLS 우회, 절대 프론트 노출 금지)
        )
    return _supabase_client
```

### dart_client.py 구현 패턴

```python
# backend/app/services/dart_client.py
import OpenDartReader  # ← 이 파일에서만 import 허용
from app.core.config import settings
from app.core.database import get_supabase_client

dart = OpenDartReader(settings.DART_API_KEY)

def search_companies(keyword: str) -> list[dict]:
    """기업명으로 DART 기업 검색"""
    result = dart.corp_codes  # pandas DataFrame
    filtered = result[result['corp_name'].str.contains(keyword, na=False)]
    return filtered.head(8).to_dict('records')

def get_financial_statements(corp_code: str, bsns_year: str, reprt_code: str = '11011') -> list[dict]:
    """DART에서 재무제표 조회 (11011=사업보고서, 11012=반기, 11013=1분기, 11014=3분기)"""
    df = dart.finstate(corp_code, bsns_year, reprt_code)
    if df is None or df.empty:
        return []
    return df.to_dict('records')

def sync_company_financials(corp_code: str, years: int = 5) -> dict:
    """기업 재무 데이터를 DART에서 수집해 DB에 UPSERT"""
    supabase = get_supabase_client()
    current_year = 2025  # 또는 datetime.now().year - 1
    synced_count = 0

    for year_offset in range(years):
        bsns_year = str(current_year - year_offset)
        rows = get_financial_statements(corp_code, bsns_year)
        if not rows:
            continue

        upsert_data = []
        for row in rows:
            account_nm = row.get('account_nm', '')
            # account_mappings에서 표준 키 조회
            mapping = supabase.table('account_mappings').select('account_key').eq('account_nm', account_nm).execute()
            account_key = mapping.data[0]['account_key'] if mapping.data else account_nm

            upsert_data.append({
                'corp_code': corp_code,
                'bsns_year': bsns_year,
                'reprt_code': row.get('reprt_code', '11011'),
                'fs_div': row.get('fs_div', 'CFS'),
                'account_key': account_key,
                'account_nm': account_nm,
                'amount': int(row.get('thstrm_amount', 0) or 0),
            })

        if upsert_data:
            supabase.table('financial_statements').upsert(
                upsert_data,
                on_conflict='corp_code,bsns_year,reprt_code,fs_div,account_key'
            ).execute()
            synced_count += len(upsert_data)

    return {'corp_code': corp_code, 'synced_rows': synced_count}
```

### sync.py 라우터 구현 패턴

```python
# backend/app/api/v1/sync.py
from fastapi import APIRouter, HTTPException
from app.services.dart_client import sync_company_financials

router = APIRouter()

@router.post("/sync/company/{corp_code}")
async def sync_company(corp_code: str):
    try:
        result = sync_company_financials(corp_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail={
            "error": "DART_API_UNAVAILABLE",
            "message": str(e)
        })
```

### main.py 라우터 등록 추가

```python
# backend/app/main.py에 추가
from app.api.v1 import health, sync  # sync 추가

app.include_router(health.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")  # 추가
```

### OpenDartReader 주요 API 참고

| 함수 | 설명 |
|------|------|
| `dart.corp_codes` | 전체 기업 목록 DataFrame |
| `dart.finstate(corp_code, bsns_year, reprt_code)` | 재무제표 조회 |
| `dart.company(corp_code)` | 기업 기본 정보 |

- `reprt_code`: `11011`=사업보고서, `11012`=반기, `11013`=1분기, `11014`=3분기
- `fs_div`: `CFS`=연결재무제표, `OFS`=별도재무제표
- 반환값은 pandas DataFrame (`.to_dict('records')`로 변환)

### 아키텍처 준수 사항

- **DART 격리 원칙**: `OpenDartReader`는 오직 `dart_client.py`에서만 import. 다른 파일에서 직접 import 시 아키텍처 위반
- **Service Key**: `database.py`에서 `SUPABASE_SERVICE_KEY` 사용 (RLS 우회). 절대 `NEXT_PUBLIC_` 환경변수로 노출 금지
- **snake_case**: 모든 JSON 응답은 snake_case 통일 (`corp_code` O, `corpCode` X)
- **금액 단위**: DB에는 BIGINT 원 단위 저장. 화면 표시는 Story 1.4의 `formatKRW()` 담당
- **DB-First 캐싱**: DB에 데이터 있으면 DART API 미호출. 없을 때만 `dart_client` 호출
- **config.py에 DATABASE_URL 추가**: `settings.DATABASE_URL` 이미 config.py에 선언됨 (빈 문자열 기본값)

### Story 1-1에서 이어받는 사항

- `backend/app/services/dart_client.py` — 스텁 파일 존재, 이번 스토리에서 완전 구현
- `backend/app/core/database.py` — 스텁 파일 존재, 이번 스토리에서 완전 구현
- `backend/app/models/schemas.py` — 스텁 파일 존재, Pydantic 모델 추가
- FastAPI 0.128.8 (0.135.1 미출시로 0.128.8 설치됨 — 기능 동일)
- Python 3.9.6 로컬 환경 (Render는 PYTHON_VERSION=3.12.0 설정됨)
- requirements.txt는 직접 의존성만 포함하도록 이미 정리됨

### Project Structure Notes

**이번 스토리에서 수정/구현하는 파일:**
- `backend/app/core/database.py` — Supabase 클라이언트 초기화 (완전 구현)
- `backend/app/services/dart_client.py` — DART API 격리 모듈 (완전 구현)
- `backend/app/models/schemas.py` — Pydantic 모델 추가
- `backend/app/api/v1/sync.py` — 동기화 엔드포인트 (완전 구현)
- `backend/app/main.py` — sync 라우터 등록
- `backend/tests/test_dart_client.py` — 신규 생성
- `backend/tests/test_database.py` — 신규 생성

**외부(Supabase Dashboard)에서 수동 실행:**
- DB 스키마 SQL (Task 1)

**의도적으로 이번 스토리에서 미구현:**
- 기업 검색 API (`/api/v1/companies/search`) → Story 1.3
- 재무 데이터 조회 API (`/api/v1/companies/{corp_code}/financials`) → Story 1.3~1.4
- `analysis_sets`, `user_profiles` 테이블 → Story 2.1, 3.1
- APScheduler 자동 갱신 → Story 3.3

### References

- DB 스키마: [architecture.md - Data Architecture](../planning-artifacts/architecture.md#data-architecture)
- DART 격리 원칙: [architecture.md - DART API 호출 격리](../planning-artifacts/architecture.md#implementation-patterns)
- 에러 코드: [architecture.md - API & Communication Patterns](../planning-artifacts/architecture.md#api--communication-patterns)
- Story AC 출처: [epics.md - Story 1.2](../planning-artifacts/epics.md#story-12-dart-데이터-수집-및-db-스키마-구축)
- 이전 스토리 완료 노트: [1-1 Dev Agent Record](./1-1-project-init-and-deployment-pipeline.md#dev-agent-record)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `import OpenDartReader` 시 클래스가 모듈 직접 노출됨 → `OpenDartReader(api_key)` 방식 사용 (`OpenDartReader.OpenDartReader()` 아님)
- Python 3.9 환경에서 `str | None` 문법 미지원 → `Optional[str]` 로 수정
- `dict[str, str]` 타입 힌트도 Python 3.9에서 지원되나 런타임 이슈 없음 확인

### Completion Notes List

- ✅ Task 1 완료: Supabase에 companies, financial_statements, account_mappings 테이블 생성 및 기본 account_mappings 시딩 (사용자 직접 실행)
- ✅ Task 2 완료: database.py — Supabase 클라이언트 싱글턴, SUPABASE_SERVICE_KEY 사용
- ✅ Task 3 완료: dart_client.py — search_companies, get_financial_statements, sync_company_financials 구현. OpenDartReader 격리 원칙 준수
- ✅ Task 4 완료: schemas.py — Company, FinancialStatement, AccountMapping, SyncResult Pydantic 모델 추가
- ✅ Task 5 완료: sync.py — POST /api/v1/sync/company/{corp_code} 엔드포인트. main.py에 라우터 등록
- ✅ Task 6 완료: 13/13 테스트 PASS (test_database: 3, test_dart_client: 7, test_health: 3)

### File List

**수정된 파일:**
- `backend/app/core/database.py`
- `backend/app/services/dart_client.py`
- `backend/app/models/schemas.py`
- `backend/app/main.py`

**신규 생성 파일:**
- `backend/app/api/v1/sync.py`
- `backend/tests/test_database.py`
- `backend/tests/test_dart_client.py`
