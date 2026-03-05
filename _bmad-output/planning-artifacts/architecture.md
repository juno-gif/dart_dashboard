---
stepsCompleted: [step-01-init, step-02-context, step-03-starter, step-04-decisions, step-05-patterns, step-06-structure, step-07-validation, step-08-complete]
lastStep: 8
status: 'complete'
completedAt: '2026-03-04'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/research/technical-dart-dashboard-research-2026-03-03.md
  - _bmad-output/planning-artifacts/product-brief-my-bmad-project-2026-03-03.md
workflowType: 'architecture'
project_name: 'my-bmad-project'
user_name: 'juno'
date: '2026-03-04'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
35개 FR, 7개 카테고리:
1. 기업 데이터 수집 (FR1-5): DART API 연동, DB 캐싱, 수기 입력
2. 기업 검색·조회 (FR6-10): 종목명/코드 검색, corp_code 자동 매핑
3. 재무 데이터 시각화 (FR11-15): P&L 5년 트렌드, 3~6개 기업 비교 차트
4. 분석 세트 관리 (FR16-21): 저장·재사용·자동 최신화
5. 사용자 관리·접근 제어 (FR22-26): RBAC 4개 역할, Supabase RLS
6. 공유·내보내기 (FR27-31): 이미지 다운로드, 공유 링크, PPT
7. 시스템·데이터 무결성 (FR32-35): 캐시 폴백, 계정과목 매핑 관리

**Non-Functional Requirements:**
- 성능: 초기 로딩 <3초, DB 캐시 히트 <1초, API 호출 <30초, 비교 차트 <5초
- 보안: DART API Key 서버 전용, Supabase Service Key 서버 전용, HTTPS 전구간, JWT 역할 클레임
- 안정성: DART 자동 업데이트 성공률 95%+, 장애 시 캐시 폴백, 업무시간 99% 가용성
- 통합: DART 일일 20,000건 한도, Supabase Free 500MB 이내
- 유지보수성: AI 친화 모듈형 모놀리스, GitHub push 자동 배포

**Scale & Complexity:**
- PRD 분류: 복잡도 medium, greenfield
- 사용자 규모: 5명 (단일 팀), 싱글 테넌트
- 외부 API 의존성: DART OpenAPI 1개 (핵심)
- Phase 구분: 3단계 (MVP → Growth → Vision)
- 예상 구현 컴포넌트: 15~20개 아키텍처 요소

### Technical Constraints & Dependencies

**확정된 기술 스택:**
- Frontend: Next.js 14 App Router + TypeScript + shadcn/ui + Tailwind CSS + Recharts
- Backend: FastAPI (Python) + OpenDartReader + Pydantic + APScheduler
- Database: Supabase (PostgreSQL + Auth + RLS)
- Deployment: Vercel (프론트) + Render (백엔드)

**주요 제약:**
- DART API Key: 환경변수 전용, 프론트엔드 절대 미노출
- Render Free 슬립: pg_cron ping으로 방지 (06:58 KST)
- Supabase Free: DB 500MB, 월 대역폭 5GB 한계
- 비코더 1인 개발: AI 친화 코드 구조 최우선, 복잡한 패턴 지양

### Cross-Cutting Concerns Identified

1. **인증·권한 관리** — JWT 클레임 → FastAPI 미들웨어 검증 → Supabase RLS 3단계. 모든 데이터 접근에 관통
2. **DART API 레이트 리밋·장애 대응** — 데이터 수집, 캐싱, 화면 렌더링 전 레이어에 걸침
3. **계정과목 표준화** — DART 비표준 `account_nm` → `account_mappings` 매핑. 데이터 수집~시각화 전 경로
4. **에러 처리·폴백 전략** — API 장애, 캐시 미스, 데이터 없음 상태를 일관된 패턴으로 처리
5. **금액 단위 변환** — DB는 원 단위 BIGINT, 화면은 억/조 단위 표시. 프론트 유틸 레이어 필요

---

## Starter Template Evaluation

### Primary Technology Domain

Full-Stack Web Application — 프론트엔드(Next.js)와 백엔드(FastAPI)를 분리한
모노레포 구조. Vercel(프론트) + Render(백엔드) 독립 배포.

### Project Repository Structure

단일 GitHub 레포지토리 내 monorepo 구조 채택:

```
my-bmad-project/          (GitHub repo root)
├── frontend/             (Next.js 16 App Router)
├── backend/              (FastAPI 0.135.1)
├── .github/              (워크플로우 — 선택)
└── README.md
```

**근거:** 비코더 1인 AI 개발 환경에서 단일 레포가 컨텍스트 관리, AI 도구(Cursor)
활용, 배포 설정 모두 단순화됨.

### Starter Options Considered

**Option A: 통합 Next.js + FastAPI 템플릿** (nextfastapi.com 등)
- 장점: 미리 연결된 설정
- 단점: 특정 설정에 고정, 업데이트 지연, 커스터마이즈 어려움

**Option B: 개별 공식 CLI 조합** (선택)
- Next.js: `create-next-app@latest`
- FastAPI: 공식 문서 구조 기반 수동 설정
- shadcn/ui: `npx shadcn@latest init`
- 장점: 최신 버전 보장, 완전한 제어권, AI 생성 코드 품질 최고

### Selected Approach: 공식 CLI 조합 (Option B)

**근거:**
- create-next-app은 Vercel이 직접 관리하는 공식 도구 → 최신 모범 사례 반영
- FastAPI 수동 구조화는 이 프로젝트 특성(DART API 격리, APScheduler 통합)에 맞게 레이어를 직접 설계 가능
- AI 코딩 도구가 공식 구조를 가장 잘 이해함

### Initialization Commands

**Step 1: Frontend (Next.js 16)**

```bash
cd my-bmad-project
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*"
```

**Step 2: shadcn/ui 초기화**

```bash
cd frontend
npx shadcn@latest init
# 선택: zinc base color, CSS variables 사용
```

**Step 3: Recharts 설치**

```bash
npm install recharts
```

**Step 4: Backend (FastAPI 0.135.1)**

```bash
cd ../
mkdir backend && cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install "fastapi[standard]" \
  supabase \
  python-jose \
  python-dotenv \
  apscheduler \
  OpenDartReader \
  pandas
pip freeze > requirements.txt
```

### Architectural Decisions Provided by Starter

**Language & Runtime:**
- TypeScript (strict mode) — Next.js 16 기본 포함
- Python 3.12+ — FastAPI 권장 버전

**Styling Solution:**
- Tailwind CSS v4 — create-next-app에서 자동 구성
- shadcn/ui CSS Variables 방식 — zinc base color

**Build Tooling:**
- Turbopack (Next.js 16 기본 dev bundler)
- Vercel 배포: GitHub 자동 연동

**Code Organization:**
- Next.js: `/src/app` (App Router), `/src/components`, `/src/lib`
- FastAPI: `/app/api`, `/app/services`, `/app/models`, `/app/core`

**Development Experience:**
- TypeScript 타입 안전성 → AI 생성 코드 오류 조기 감지
- ESLint + Prettier — Next.js 기본 포함
- FastAPI 자동 `/docs` (Swagger UI) — API 테스트 즉시 가능

**Note:** 프로젝트 초기화는 첫 번째 구현 스토리로 문서화됩니다.

---

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (구현 시작 전 필수):**
- 데이터 캐싱 전략: 영구 저장 방식 (TTL 없음)
- 상태 관리: TanStack Query v5
- JWT 검증: Supabase SDK 방식
- API 에러 응답 표준 형식 확정

**Important Decisions (아키텍처에 큰 영향):**
- 핵심 DB 스키마 5개 테이블 구조
- REST 엔드포인트 구조
- 환경 변수 분리 전략

**Deferred Decisions (Post-MVP):**
- PPT Export 라이브러리 선택 (Phase 3)
- LLM API 연동 방식 (Phase 3)
- 로깅·모니터링 도구 (MVP 안정화 후)

### Data Architecture

**캐싱 전략: 영구 저장 (DB-First)**
- 결정: DART API 응답을 `financial_statements` 테이블에 즉시 영구 저장
- 근거: 재무 데이터는 분기별 업데이트 — TTL 기반 만료 불필요. APScheduler 매일 07:00 갱신으로 충분
- 효과: DART API 일일 20,000건 한도 자연 준수 (DB 히트율 극대화)

**핵심 DB 스키마:**

```sql
-- 기업 기본 정보
companies (
  corp_code     VARCHAR(8) PRIMARY KEY,  -- DART 고유 코드
  company_name  VARCHAR(100) NOT NULL,
  stock_code    VARCHAR(6),              -- 종목코드 (비상장 NULL)
  is_listed     BOOLEAN DEFAULT true,
  created_at    TIMESTAMPTZ DEFAULT now()
)

-- DART 수집 재무 데이터 (캐시)
financial_statements (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  corp_code     VARCHAR(8) REFERENCES companies(corp_code),
  bsns_year     VARCHAR(4) NOT NULL,     -- 사업연도
  reprt_code    VARCHAR(5) NOT NULL,     -- 보고서 구분
  fs_div        VARCHAR(3) NOT NULL,     -- CFS/OFS
  account_key   VARCHAR(50) NOT NULL,    -- 표준화된 계정과목 키
  account_nm    VARCHAR(100),            -- DART 원본 계정과목명
  amount        BIGINT,                  -- 금액 (원 단위)
  synced_at     TIMESTAMPTZ DEFAULT now(),
  UNIQUE(corp_code, bsns_year, reprt_code, fs_div, account_key)
)

-- 계정과목 표준화 매핑
account_mappings (
  account_nm    VARCHAR(100) PRIMARY KEY, -- DART 원본명
  account_key   VARCHAR(50) NOT NULL,     -- 표준 키 (revenue, operating_profit 등)
  display_name  VARCHAR(100),             -- 화면 표시명 (한국어)
  category      VARCHAR(20)               -- pl / bs / cf
)

-- 분석 세트
analysis_sets (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR(100) NOT NULL,
  owner_id      UUID REFERENCES auth.users(id),
  company_codes JSONB NOT NULL,           -- ["005930", "035720"]
  config        JSONB,                    -- 선택 항목 설정
  share_token   VARCHAR(64) UNIQUE,       -- 공유 링크 토큰
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at    TIMESTAMPTZ DEFAULT now()
)

-- 사용자 프로필 (Supabase Auth 확장)
user_profiles (
  id            UUID PRIMARY KEY REFERENCES auth.users(id),
  role          VARCHAR(20) DEFAULT 'builder', -- admin/builder/live_viewer/read_only
  display_name  VARCHAR(50)
)
```

**데이터 검증:** Pydantic v2 모델로 FastAPI 레이어에서 타입 검증. DB 레이어 중복 검증 최소화.

**마이그레이션:** Supabase Dashboard SQL Editor로 수동 적용 (MVP). 규모 성장 시 Alembic 도입 검토.

### Authentication & Security

**인증 흐름 (확정):**
```
사용자 로그인 (Supabase Auth)
  → JWT 발급 (role 클레임 포함)
  → Next.js 클라이언트 토큰 저장 (메모리/쿠키)
  → FastAPI 요청 헤더 Authorization: Bearer {token}
  → FastAPI 미들웨어: Supabase SDK get_user(token) 검증
  → Supabase RLS: user_id + role 기반 행 단위 권한 적용
```

**JWT 검증 방식: Supabase Python SDK**
- 결정: `supabase.auth.get_user(token)` 서버 검증
- 근거: python-jose 직접 구현보다 코드 단순화, Supabase 키 관리 통합, 비코더 유지보수 용이
- 주의: Supabase Service Key는 FastAPI 서버 환경변수에만 보관, 절대 프론트 미전달

**RLS 정책 원칙:**
- `analysis_sets`: owner_id = auth.uid() (Builder 본인 수정), live_viewer는 전체 조회 가능
- `financial_statements`: 인증된 모든 사용자 조회 가능 (회사 데이터는 공개 정보)
- `user_profiles`: 본인만 조회/수정, Admin은 전체 조회

### API & Communication Patterns

**REST API 설계 (FastAPI):**

```
# 기업 검색
GET  /api/v1/companies/search?q={query}&limit=8

# 재무 데이터 조회
GET  /api/v1/companies/{corp_code}/financials?years=5&type=pl

# 다중 기업 비교 데이터
GET  /api/v1/companies/compare?codes=005930,035720&type=pl

# 분석 세트 CRUD
POST /api/v1/analysis-sets
GET  /api/v1/analysis-sets
GET  /api/v1/analysis-sets/{id}
PUT  /api/v1/analysis-sets/{id}
DELETE /api/v1/analysis-sets/{id}

# 공유 링크
POST /api/v1/analysis-sets/{id}/share
GET  /api/v1/shared/{share_token}          (인증 불필요)

# DART 동기화 (관리용)
POST /api/v1/sync/company/{corp_code}
```

**표준 에러 응답 형식:**
```json
{
  "error": "DART_API_UNAVAILABLE",
  "message": "DART API에 일시적 오류가 발생했습니다. 캐시 데이터를 표시합니다.",
  "cached_at": "2026-03-01T07:00:00Z",
  "status_code": 503
}
```

**에러 코드 목록:**
- `DART_API_UNAVAILABLE` — DART API 장애, 캐시 폴백
- `DART_RATE_LIMIT` — 일일 한도 초과
- `COMPANY_NOT_FOUND` — 기업 코드 없음
- `INSUFFICIENT_PERMISSION` — 권한 부족
- `ANALYSIS_SET_NOT_FOUND` — 세트 없음

**CORS 설정:** Vercel 배포 도메인만 허용 (`ALLOWED_ORIGINS` 환경변수)

### Frontend Architecture

**상태 관리: TanStack Query v5 (React Query)**
- 결정: 서버 상태 전용. 클라이언트 UI 상태는 React `useState`/`useReducer`
- 근거: FastAPI REST API 연동 표준, 자동 캐싱·재시도·스켈레톤 상태 내장
- 설치: `npm install @tanstack/react-query`

**데이터 흐름:**
```
Next.js Client Component
  → useQuery / useMutation (TanStack Query)
  → fetch('/api/...' ) → FastAPI REST
  → Supabase PostgreSQL
```

**Next.js App Router 활용:**
- `app/` 디렉토리: 페이지 라우팅
- Client Components (`'use client'`): 차트, 검색, 인터랙티브 UI
- Server Components: 공유 링크 페이지 (read-only, 인증 불필요)
- Middleware: 인증 미들웨어 (로그인 리디렉션)

**금액 단위 변환 유틸:**
```typescript
// src/lib/format.ts
export function formatKRW(amount: number): string {
  if (Math.abs(amount) >= 1_000_000_000_000) return `₩${(amount/1e12).toFixed(1)}조`
  if (Math.abs(amount) >= 100_000_000) return `₩${(amount/1e8).toFixed(0)}억`
  return `₩${(amount/1e6).toFixed(1)}백만`
}
```

### Infrastructure & Deployment

**환경 변수 구조:**

```bash
# frontend/.env.local (개발)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

# backend/.env (개발)
DART_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
DATABASE_URL=postgresql://...
ALLOWED_ORIGINS=http://localhost:3000
```

**Vercel 프로덕션 환경변수:**
- `NEXT_PUBLIC_API_URL` = Render 배포 URL
- Supabase 키 동일 설정

**Render 프로덕션 환경변수:**
- `DART_API_KEY`, `SUPABASE_SERVICE_KEY` 등 서버 전용 키
- `ALLOWED_ORIGINS` = Vercel 배포 도메인

**CI/CD:**
- Vercel: GitHub `main` 브랜치 push → 자동 배포 (루트 디렉토리: `frontend/`)
- Render: GitHub `main` 브랜치 push → 자동 배포 (루트 디렉토리: `backend/`)
- 별도 CI 파이프라인 미도입 (5인 팀, 단순성 우선)

**슬립 방지 (Render Free):**
- Supabase `pg_cron`: 매일 06:58 KST → `GET {RENDER_URL}/health` ping
- FastAPI `GET /health` 엔드포인트 제공

### Decision Impact Analysis

**구현 순서 (의존성 기반):**
1. 프로젝트 초기화 (레포, 프론트/백엔드 기본 구조)
2. DB 스키마 생성 (Supabase)
3. FastAPI 기본 구조 + CORS + Health endpoint
4. DART API 연동 (`dart_client.py` 격리 모듈)
5. 기업 검색 + 재무 데이터 조회 API
6. Next.js 프론트엔드 기본 레이아웃 (사이드바)
7. TanStack Query 연동 + 차트 렌더링
8. Supabase Auth + RLS (Phase 2)
9. 분석 세트 저장/조회 (Phase 2)

**컴포넌트 간 의존성:**
- `account_mappings` 테이블 → `financial_statements` 데이터 표시에 선행 필요
- Supabase Auth → RLS 정책 → 분석 세트 CRUD 순서
- DART 캐시 데이터 → 차트 렌더링 (캐시 없으면 로딩 상태)

---

## Implementation Patterns & Consistency Rules

### Critical Conflict Points: 12개 영역

AI 에이전트가 서로 다른 선택을 할 수 있는 지점을 모두 사전 확정함.

### Naming Patterns

**Database 네이밍 (PostgreSQL / Supabase)**
- 테이블: `snake_case` 복수형 → `companies`, `financial_statements`, `analysis_sets`
- 컬럼: `snake_case` → `corp_code`, `bsns_year`, `created_at`
- 외래키: `{참조테이블_단수}_id` 또는 자연키 → `corp_code`, `owner_id`
- 인덱스: `idx_{테이블}_{컬럼}` → `idx_financial_statements_corp_code`
- 기본키: `id` (UUID) 또는 자연키 (`corp_code`) — 테이블별 명시

**API 엔드포인트 네이밍 (FastAPI)**
- 리소스: 복수형 소문자 → `/api/v1/companies`, `/api/v1/analysis-sets`
- 복합명사: 하이픈 분리 → `/analysis-sets` (언더스코어 금지)
- 동사 액션: `/{id}/share`, `/{id}/sync` (명사형 REST 불가 시에만)
- 쿼리 파라미터: `snake_case` → `?corp_code=005930&bsns_year=2023`

**JSON 필드 네이밍 (전 레이어 통일)**
- **`snake_case` 통일** — FastAPI, Supabase, TypeScript 모두 동일
- 근거: DART API·Supabase 모두 snake_case 반환 → 변환 레이어 불필요
- TypeScript에서 `corp_code`, `bsns_year` 그대로 사용 (camelCase 변환 금지)

**TypeScript 코드 네이밍 (Frontend)**
- 컴포넌트: `PascalCase` → `FinancialChart`, `CompanySearchInput`
- 파일명: `PascalCase.tsx` → `FinancialChart.tsx`
- 함수/변수: `camelCase` → `formatKRW`, `analysisSetId`
- DB 필드 사용 시: `snake_case` 유지 → `corp_code`, `bsns_year`
- 커스텀 훅: `use` 접두사 → `useFinancialData`, `useAnalysisSet`
- 타입/인터페이스: `PascalCase` → `FinancialStatement`, `AnalysisSet`

**Python 코드 네이밍 (Backend)**
- 모든 식별자: `snake_case` → `get_financial_data`, `corp_code`
- 클래스: `PascalCase` → `FinancialService`, `DartClient`
- Pydantic 모델: `PascalCase` → `FinancialStatementResponse`
- 상수: `UPPER_SNAKE_CASE` → `DART_API_KEY`, `MAX_COMPANIES`

### Structure Patterns

**Frontend 디렉토리 구조 (절대 준수)**

```
frontend/src/
├── app/
│   ├── (auth)/
│   │   ├── dashboard/
│   │   └── layout.tsx
│   ├── shared/[token]/
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                 # shadcn/ui 자동 생성 (수정 금지)
│   ├── charts/             # FinancialChart, KPICard
│   ├── search/             # CompanySearchInput, CompanyTag
│   └── layout/             # Sidebar, Header, AnalysisSetItem
├── lib/
│   ├── api.ts              # FastAPI 호출 함수 (fetch 래퍼)
│   ├── format.ts           # formatKRW, formatPercent
│   ├── supabase.ts         # Supabase 클라이언트
│   └── utils.ts            # shadcn/ui cn() 등
├── hooks/
│   └── use-financial-data.ts
└── types/
    └── index.ts
```

**Backend 디렉토리 구조 (절대 준수)**

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py       # 환경변수 로딩
│   │   ├── auth.py         # JWT 검증 미들웨어
│   │   └── database.py     # Supabase 클라이언트
│   ├── api/v1/
│   │   ├── companies.py
│   │   ├── financials.py
│   │   ├── analysis_sets.py
│   │   └── sync.py
│   ├── services/
│   │   ├── dart_client.py  # DART API 격리 모듈
│   │   ├── financial_service.py
│   │   └── analysis_set_service.py
│   ├── models/
│   │   └── schemas.py
│   └── scheduler/
│       └── tasks.py
├── requirements.txt
└── .env
```

**테스트 파일 위치:**
- Frontend: `src/` 내 동일 디렉토리 co-located (`*.test.ts`, `*.test.tsx`)
- Backend: `tests/` 별도 디렉토리 (`test_companies.py`)

### Format Patterns

**API 응답 형식**

성공: 직접 반환 (래퍼 없음)
```json
[{ "corp_code": "005930", "bsns_year": "2023", "account_key": "revenue", "amount": 258935000000000 }]
```

에러: 표준 형식
```json
{ "error": "COMPANY_NOT_FOUND", "message": "기업을 찾을 수 없습니다.", "status_code": 404 }
```

**날짜/시간 형식:**
- DB 저장: `TIMESTAMPTZ` (UTC)
- API JSON: ISO 8601 → `"2026-03-04T07:00:00Z"`
- 화면 표시: `"3시간 전"` (상대적) 또는 `"2026-03-04"` (절대적)
- 금지: Unix timestamp 숫자형

**금액 단위:**
- DB: 원 단위 `BIGINT`
- API: 원 단위 그대로 전달 (변환 금지)
- 프론트: `formatKRW()` 유틸로만 변환 (컴포넌트 내 직접 변환 금지)

### Communication Patterns

**TanStack Query 쿼리 키 규칙:**
```typescript
['companies', 'search', { q: query }]
['financials', corp_code, { years: 5, type: 'pl' }]
['analysis-sets']
['analysis-sets', id]
```

**API 호출 레이어 (`lib/api.ts`):**
- 모든 FastAPI 호출은 `lib/api.ts` 함수를 통해서만 (컴포넌트 내 직접 fetch 금지)
- 인증 헤더 자동 첨부

**상태 업데이트 패턴:**
- 데이터 변경 후: `queryClient.invalidateQueries()` 캐시 무효화
- 낙관적 업데이트: 세트 이름 변경 등 즉각 피드백 필요 시에만 적용

### Process Patterns

**에러 처리 계층:**
- `4xx` 사용자 실수: Inline Error (입력 필드 아래)
- `503` DART 장애: Banner (캐시 데이터 + 상단 경고)
- `500` 서버 오류: Toast ("잠시 후 재시도")
- 네트워크 오류: TanStack Query 자동 재시도 3회 후 Toast

**로딩 상태 규칙:**
- `isLoading` 최초 로드: Skeleton 컴포넌트 (레이아웃 쉬프트 방지)
- `isFetching` 백그라운드 갱신: 표시 안 함
- `isPending` mutation: 버튼 내 스피너 + disabled

**DART API 호출 격리:**
- `dart_client.py`에서만 직접 호출 허용
- 다른 서비스/라우터에서 OpenDartReader 직접 import 금지
- DB 캐시 조회 우선 → 없을 때만 dart_client 호출

### Enforcement Guidelines

**모든 AI 에이전트 필수 준수:**

1. JSON 필드명 `snake_case` 통일 (camelCase 변환 레이어 도입 금지)
2. FastAPI 호출은 `frontend/src/lib/api.ts` 경유 (컴포넌트 내 직접 fetch 금지)
3. DART OpenAPI 호출은 `backend/app/services/dart_client.py`만 허용
4. DB 금액 저장은 원 단위 BIGINT, 화면 변환은 `formatKRW()` 유틸만 사용
5. 에러 응답은 표준 형식 `{ error, message, status_code }` 준수
6. 새 컴포넌트는 `frontend/src/components/` 하위 카테고리에 배치
7. 새 FastAPI 엔드포인트는 `backend/app/api/v1/` 하위 파일에 라우터 등록
8. 환경변수 `NEXT_PUBLIC_` 접두사 규칙 준수 (공개/비공개 구분)

**Anti-Patterns (금지):**
```typescript
// ❌ camelCase JSON
{ corpCode: "005930" }
// ✅ snake_case 통일
{ corp_code: "005930" }

// ❌ 컴포넌트 내 직접 fetch
const res = await fetch(`${API_URL}/api/v1/companies`)
// ✅ api.ts 경유
import { searchCompanies } from '@/lib/api'

// ❌ dart_client 격리 위반 (service에서 직접 import)
import OpenDartReader from 'opendartreader'
// ✅ dart_client 경유
from app.services.dart_client import get_financial_data
```

---

## Project Structure & Boundaries

### Complete Project Directory Structure

```
my-bmad-project/                        (GitHub repo root)
├── README.md
├── .gitignore
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── components.json                 # shadcn/ui 설정
│   ├── .env.local                      # gitignore
│   ├── .env.example
│   └── src/
│       ├── app/
│       │   ├── globals.css
│       │   ├── layout.tsx              # RootLayout, QueryClientProvider
│       │   ├── page.tsx                # → /dashboard 리디렉션
│       │   ├── middleware.ts           # 미인증 → /login
│       │   ├── login/
│       │   │   └── page.tsx
│       │   ├── (auth)/
│       │   │   ├── layout.tsx          # 사이드바 + 헤더
│       │   │   └── dashboard/
│       │   │       ├── page.tsx        # 메인 대시보드
│       │   │       └── [set_id]/
│       │   │           └── page.tsx    # 분석 세트 뷰
│       │   └── shared/
│       │       └── [token]/
│       │           └── page.tsx        # 공유 링크 (Server Component)
│       ├── components/
│       │   ├── ui/                     # shadcn/ui 자동 생성 (수정 금지)
│       │   │   ├── button.tsx
│       │   │   ├── card.tsx
│       │   │   ├── command.tsx
│       │   │   ├── dialog.tsx
│       │   │   ├── sidebar.tsx
│       │   │   ├── skeleton.tsx
│       │   │   ├── tabs.tsx
│       │   │   ├── toast.tsx
│       │   │   └── tooltip.tsx
│       │   ├── charts/
│       │   │   ├── FinancialChart.tsx  # FR11-12
│       │   │   └── KPICard.tsx         # FR11
│       │   ├── search/
│       │   │   ├── CompanySearchInput.tsx  # FR6-8
│       │   │   └── CompanyTag.tsx
│       │   └── layout/
│       │       ├── AppSidebar.tsx
│       │       ├── AppHeader.tsx
│       │       ├── AnalysisSetItem.tsx # FR17
│       │       └── ShareButton.tsx     # FR28
│       ├── lib/
│       │   ├── api.ts                  # 모든 FastAPI 호출 함수
│       │   ├── format.ts               # formatKRW, formatPercent, formatDate
│       │   ├── supabase.ts             # Supabase 클라이언트 (anon key)
│       │   └── utils.ts               # shadcn/ui cn() 등
│       ├── hooks/
│       │   ├── use-financial-data.ts  # FR8,11-12
│       │   ├── use-analysis-sets.ts   # FR16-21
│       │   └── use-auth.ts            # FR24
│       └── types/
│           └── index.ts               # FinancialStatement, AnalysisSet, User 등
│
└── backend/
    ├── requirements.txt
    ├── .env                            # gitignore
    ├── .env.example
    └── app/
        ├── main.py                     # FastAPI 앱, CORS, 라우터, lifespan
        ├── core/
        │   ├── config.py               # pydantic-settings 환경변수
        │   ├── auth.py                 # Supabase SDK JWT 검증 의존성
        │   └── database.py             # Supabase 클라이언트 (service key)
        ├── api/
        │   └── v1/
        │       ├── __init__.py
        │       ├── companies.py        # FR6-10
        │       ├── financials.py       # FR11-15
        │       ├── analysis_sets.py    # FR16-21
        │       ├── shared.py           # FR29 (인증 불필요)
        │       ├── sync.py             # FR1-3
        │       └── health.py           # Render 슬립 방지
        ├── services/
        │   ├── dart_client.py          # FR1-3: DART API 격리 모듈
        │   ├── financial_service.py    # FR8,11-15
        │   ├── company_service.py      # FR6-10
        │   └── analysis_set_service.py # FR16-21
        ├── models/
        │   └── schemas.py              # Pydantic 요청/응답 스키마
        └── scheduler/
            └── tasks.py                # FR3: APScheduler 07:00 동기화
```

### Architectural Boundaries

**Frontend ↔ Backend 경계**
```
[Next.js Client]  →  lib/api.ts  →  FastAPI /api/v1/*
[Supabase Auth]   →  JWT 발급    →  FastAPI core/auth.py 검증
                                     ↓
                              Supabase PostgreSQL (RLS)
```

**DART API 격리 경계**
```
[FastAPI 모든 서비스]  →  dart_client.py만  →  DART OpenAPI
                         (직접 import 절대 금지)
```

**컴포넌트 경계**
```
components/ui/     → shadcn/ui 자동 생성, 수정 금지
components/charts/ → ui/ 위에서 구축, 비즈니스 로직 포함
app/(auth)/        → 컴포넌트 조합, 데이터는 hooks/에서만
```

### Requirements to Structure Mapping

| FR 카테고리 | Frontend 파일 | Backend 파일 |
|---|---|---|
| FR1-5 기업 데이터 수집 | — | `dart_client.py`, `scheduler/tasks.py` |
| FR6-10 기업 검색 | `CompanySearchInput.tsx`, `use-financial-data.ts` | `companies.py`, `company_service.py` |
| FR11-15 재무 시각화 | `FinancialChart.tsx`, `KPICard.tsx` | `financials.py`, `financial_service.py` |
| FR16-21 분석 세트 | `AnalysisSetItem.tsx`, `use-analysis-sets.ts` | `analysis_sets.py`, `analysis_set_service.py` |
| FR22-26 사용자 관리 | `use-auth.ts`, `middleware.ts` | `core/auth.py`, RLS 정책 |
| FR27-31 공유·내보내기 | `ShareButton.tsx`, `shared/[token]/page.tsx` | `shared.py`, `analysis_set_service.py` |
| FR32-35 시스템 무결성 | 에러 배너, Toast | `dart_client.py` 폴백, `account_mappings` DB |

**Cross-Cutting 위치:**
- 인증: `frontend/middleware.ts` + `hooks/use-auth.ts` + `backend/core/auth.py`
- 에러 처리: `frontend/lib/api.ts` (변환) + 각 컴포넌트 (표시)
- 금액 변환: `frontend/lib/format.ts` → `formatKRW()` 단일 출처
- 타입 정의: `frontend/src/types/index.ts` / `backend/app/models/schemas.py`

### Data Flow

```
DART OpenAPI
  → dart_client.py (수집)
  → financial_service.py (account_mappings 표준화)
  → Supabase financial_statements (BIGINT 원 단위)
  → FastAPI REST (snake_case JSON)
  → lib/api.ts → TanStack Query (캐싱)
  → FinancialChart.tsx (formatKRW 변환 후 렌더링)
```

### Development Workflow

```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# FastAPI 문서: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

**배포:**
- Vercel Root Directory: `frontend/`
- Render Root Directory: `backend/`, Start: `uvicorn app.main:app --host 0.0.0.0`

---

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
기술 스택 전 레이어(Next.js 16 + FastAPI 0.135.1 + Supabase)가 충돌 없이 호환됨.
TanStack Query v5는 Next.js Client Components와 완전 통합. Supabase SDK JWT 검증은
python-jose 대비 코드량 최소화 및 키 관리 일원화 효과 확인.

**Pattern Consistency:**
- snake_case JSON 통일 원칙이 DART API(원본 snake_case), Supabase(원본 snake_case),
  FastAPI Pydantic(기본 snake_case) 모두와 일관됨 — 변환 레이어 불필요 결정 유효
- DART 격리 패턴(dart_client.py)이 Step 4 결정 → Step 5 패턴 → Step 6 구조까지
  일관되게 반영됨
- formatKRW() 단일 출처 원칙이 format.ts 파일 위치까지 완전히 추적됨

**Structure Alignment:**
모노레포 구조(frontend/ + backend/)가 Vercel + Render 독립 배포 전략과 완전 정렬.
shadcn/ui 컴포넌트를 ui/ 하위에 격리하고 수정 금지 규칙을 명시해 의도하지 않은
오버라이드 방지.

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**
35개 FR 전체가 특정 파일 또는 DB 오브젝트에 매핑됨 (Project Structure FR→파일 매핑 테이블 참조).
7개 FR 카테고리 중 아키텍처 지원이 없는 항목 없음.

**Non-Functional Requirements Coverage:**
- 성능: DB-First 캐싱으로 DART 호출 최소화 → 반복 조회 <1초 목표 달성 가능
- 보안: 4중 보호 (서버 전용 키 + HTTPS + JWT + Supabase RLS)
- 안정성: DART 장애 → 캐시 폴백 + 503 표준 에러 응답 + Render 슬립 방지(pg_cron)
- 통합 한도: DART 20,000건/일 → DB 캐시 히트율 극대화로 자연 준수
- 유지보수: AI 친화 모듈형 구조 + 단일 레포 + 자동 배포

### Implementation Readiness Validation ✅

**Decision Completeness:**
- 모든 Critical 결정에 버전 명시: Next.js 16, FastAPI 0.135.1, TanStack Query v5
- DB 스키마: 5개 테이블 완전한 SQL DDL 포함
- API 엔드포인트: 전체 11개 URL 패턴 명시
- 환경변수: 개발/프로덕션 분리 완전 정의

**Structure Completeness:**
- 전체 파일 트리: frontend + backend 디렉토리의 모든 파일 명시
- FR→파일 매핑: 7개 카테고리 × Frontend/Backend 파일 완전 대응
- 경계 정의: Frontend↔Backend, DART 격리, 컴포넌트 계층 모두 명시

**Pattern Completeness:**
- 12개 충돌 영역 완전 해소
- 4개 언어/플랫폼(DB, API URL, TypeScript, Python) 네이밍 완전 정의
- 프로세스 패턴: 에러 처리 4계층, 로딩 3상태, DART 격리 규칙

### Gap Analysis Results

**Critical Gaps:** 없음 — 구현 시작을 막는 미결정 사항 없음

**Important Gaps (허용됨):**
- 이미지 다운로드(FR28): MVP에서 html2canvas 또는 브라우저 Print API로 충분.
  Phase 3 PPT는 Deferred로 명시됨
- 테스트 프레임워크: Vitest(프론트) + pytest(백엔드) 표준 조합으로 에이전트 추론 가능

**Nice-to-Have Gaps:**
- 로깅 전략: FastAPI 기본 로깅으로 MVP 진행, 안정화 후 구체화 (Deferred)

### Validation Issues Addressed

갭 분석 결과 Critical 이슈 없음. Important 갭 2건은 모두 MVP 범위 외이거나 에이전트가
표준 관행으로 추론 가능한 수준으로 구현 차단 없음.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] 프로젝트 컨텍스트 분석 (35 FR, 7 카테고리, 3 Phase)
- [x] 규모·복잡도 평가 (5인 팀, Medium 복잡도, Greenfield)
- [x] 기술 제약 식별 (DART API Key 격리, Render 슬립, Supabase 500MB)
- [x] Cross-Cutting Concerns 5개 매핑

**✅ Architectural Decisions**
- [x] Critical 결정 버전 포함 문서화
- [x] 기술 스택 전체 명시 (Next.js 16, FastAPI 0.135.1, Supabase, Vercel, Render)
- [x] 통합 패턴 정의 (REST API, JWT, RLS)
- [x] 성능 고려 (DB-First 캐싱, TanStack Query 캐싱)

**✅ Implementation Patterns**
- [x] 네이밍 규칙 (DB, API, TypeScript, Python)
- [x] 구조 패턴 (frontend/backend 디렉토리 규칙)
- [x] 통신 패턴 (TanStack Query 키, API 레이어)
- [x] 프로세스 패턴 (에러 처리, 로딩 상태)

**✅ Project Structure**
- [x] 완전한 디렉토리 구조 정의
- [x] 컴포넌트 경계 확립
- [x] 통합 포인트 매핑
- [x] FR→구조 매핑 완료

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION ✅

**Confidence Level:** HIGH

**Key Strengths:**
1. DART API 격리 설계 — dart_client.py 단일 진입점으로 레이트 리밋·장애 대응 집중화
2. snake_case 통일 — 변환 레이어 제거로 버그 표면 최소화
3. DB-First 영구 캐싱 — DART 한도 자연 준수 + 빠른 응답
4. 비코더 친화 설계 — AI 에이전트가 이해하기 쉬운 명확한 모듈 경계
5. 모든 FR에 파일 단위 매핑 — 에이전트 구현 시 혼란 없음

**Areas for Future Enhancement:**
- Phase 3: PPT 내보내기 라이브러리 결정 (python-pptx 또는 프론트 기반)
- Phase 3: LLM API 연동 방식 결정 (OpenAI SDK 또는 Anthropic SDK)
- MVP 안정화 후: 구조적 로깅 도입 (structlog 또는 FastAPI logging middleware)

### Implementation Handoff

**AI Agent Guidelines:**
- 모든 아키텍처 결정을 정확히 준수할 것
- Implementation Patterns의 8가지 강제 규칙 준수
- 새 파일 생성 시 Project Structure의 디렉토리 위치 참조
- 모든 질문은 이 문서를 먼저 참조

**First Implementation Priority:**

```bash
# Step 1: Frontend 초기화
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"

# Step 2: shadcn/ui 초기화
cd frontend && npx shadcn@latest init

# Step 3: Backend 초기화
mkdir backend && cd backend
python -m venv venv && source venv/bin/activate
pip install "fastapi[standard]" supabase python-dotenv apscheduler OpenDartReader pandas

# Step 4: Supabase DB 스키마 적용 (Dashboard SQL Editor)
# → Core Architectural Decisions > Data Architecture 섹션 SQL 사용
```
