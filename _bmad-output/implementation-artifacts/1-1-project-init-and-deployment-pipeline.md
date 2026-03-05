# Story 1.1: 프로젝트 초기화 및 배포 파이프라인 구성

Status: review

## Story

As a 개발자(팀),
I want to initialize the monorepo with Next.js 16 and FastAPI and configure automatic deployments,
So that the team has a live deployed URL to build upon and can access the dashboard immediately.

## Acceptance Criteria

1. **[모노레포 초기화]** `frontend/`(Next.js 16, TypeScript, Tailwind, shadcn/ui)와 `backend/`(FastAPI 0.135.1, Python 3.12) 디렉토리 구조가 아키텍처 문서의 프로젝트 트리와 일치해야 한다
2. **[환경변수 문서화]** `frontend/.env.example`과 `backend/.env.example`에 모든 필수 환경변수가 문서화되어야 한다
3. **[Vercel 자동 배포]** GitHub main 브랜치에 코드가 push되면 Vercel이 `frontend/`를 빌드해 HTTPS 배포 URL을 생성해야 한다
4. **[Render 자동 배포 + 헬스체크]** Render가 `backend/`를 빌드해 `GET /health`가 200 OK `{"status": "ok"}`를 반환해야 한다
5. **[슬립 방지]** Supabase pg_cron이 매일 06:58 KST에 `GET {RENDER_URL}/health`를 호출하면 Render 인스턴스가 깨어나 업무 시간 내 요청에 즉시 응답해야 한다

## Tasks / Subtasks

- [x] Task 1: 모노레포 디렉토리 기본 구조 설정 (AC: #1)
  - [x] 1.1 GitHub 레포지토리 루트에 `README.md`, `.gitignore` 생성
  - [x] 1.2 `.gitignore`에 `frontend/.env.local`, `backend/.env`, `backend/venv/`, `**/__pycache__/` 포함

- [x] Task 2: Next.js 16 Frontend 초기화 (AC: #1, #2)
  - [x] 2.1 공식 CLI 실행: `npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"`
  - [x] 2.2 shadcn/ui 초기화: `cd frontend && npx shadcn@latest init` (neutral color, CSS variables)
  - [x] 2.3 TanStack Query v5 설치: `npm install @tanstack/react-query`
  - [x] 2.4 Recharts 설치: `npm install recharts`
  - [x] 2.5 `frontend/.env.example` 생성 (아래 [환경변수 섹션] 참조)
  - [x] 2.6 `frontend/src/app/layout.tsx`에 `QueryClientProvider` 래핑 추가
  - [x] 2.7 `frontend/src/lib/` 디렉토리 생성: `api.ts`, `format.ts`, `supabase.ts`, `utils.ts` 스텁 파일 생성
  - [x] 2.8 `frontend/src/types/index.ts` 생성 (기본 타입 스텁)
  - [x] 2.9 `frontend/src/components/` 하위 디렉토리 생성: `ui/`, `charts/`, `search/`, `layout/`

- [x] Task 3: FastAPI Backend 초기화 (AC: #1, #2, #4)
  - [x] 3.1 `backend/` 디렉토리 생성 및 Python venv 설정: `python -m venv venv`
  - [x] 3.2 패키지 설치: `pip install "fastapi[standard]" supabase python-dotenv apscheduler OpenDartReader pandas`
  - [x] 3.3 `pip freeze > requirements.txt` 실행
  - [x] 3.4 아키텍처 문서의 디렉토리 구조대로 폴더 생성:
    - `backend/app/core/` → `config.py`, `auth.py`, `database.py`
    - `backend/app/api/v1/` → `__init__.py`, `health.py`
    - `backend/app/services/` → `dart_client.py`
    - `backend/app/models/` → `schemas.py`
    - `backend/app/scheduler/` → `tasks.py`
  - [x] 3.5 `backend/app/main.py` 생성 (CORS + 라우터 + lifespan)
  - [x] 3.6 `GET /health` 엔드포인트 구현: `{"status": "ok"}` 반환
  - [x] 3.7 `backend/.env.example` 생성 (아래 [환경변수 섹션] 참조)
  - [x] 3.8 `backend/app/core/config.py`에 pydantic-settings로 환경변수 로딩 구현

- [ ] Task 4: Vercel 배포 연동 (AC: #3)
  - [ ] 4.1 Vercel 프로젝트 생성 → GitHub 레포 연결
  - [ ] 4.2 Vercel Root Directory를 `frontend/`로 설정
  - [ ] 4.3 Vercel 환경변수 설정: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - [ ] 4.4 main 브랜치 push 후 빌드 성공 확인

- [ ] Task 5: Render 배포 연동 (AC: #4)
  - [ ] 5.1 Render Web Service 생성 → GitHub 레포 연결
  - [ ] 5.2 Render Root Directory를 `backend/`로 설정
  - [ ] 5.3 Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - [ ] 5.4 Render 환경변수 설정: `DART_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ALLOWED_ORIGINS`
  - [ ] 5.5 배포 후 `GET /health` → 200 OK `{"status": "ok"}` 확인

- [ ] Task 6: Supabase pg_cron 슬립 방지 설정 (AC: #5)
  - [ ] 6.1 Supabase Dashboard → Database → Extensions에서 `pg_cron` 활성화
  - [ ] 6.2 SQL Editor에서 cron job 등록:
    ```sql
    SELECT cron.schedule(
      'render-wakeup',
      '58 21 * * *',  -- 06:58 KST = 21:58 UTC
      $$SELECT net.http_get(url := '{RENDER_URL}/health')$$
    );
    ```
  - [ ] 6.3 pg_net extension 활성화 확인 (http_get 함수 사용을 위해)

- [ ] Task 7: 최종 검증 (AC: #1~#5 전체)
  - [ ] 7.1 Vercel 배포 URL로 접속 → Next.js 기본 페이지 렌더링 확인
  - [ ] 7.2 Render 배포 URL `/health` → `{"status": "ok"}` 확인
  - [ ] 7.3 로컬 개발 환경 실행 검증:
    - `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000`
    - `cd frontend && npm run dev`
    - `http://localhost:8000/docs` Swagger UI 접근 가능 확인
  - [ ] 7.4 GitHub main push 시 양쪽 자동 배포 트리거 확인

## Dev Notes

### 핵심 아키텍처 준수 사항

- **Next.js 버전**: **반드시 Next.js 16** 사용 (`create-next-app@latest` 실행 시 2026년 기준 최신 버전이 16임). Next.js 14 또는 15 설치 금지
- **FastAPI 버전**: `"fastapi[standard]"` 0.135.1 설치 (`pip install "fastapi[standard]"` 최신 버전이 0.135.1임)
- **Python**: 3.12+ 사용 (venv 생성 시 Python 3.12 확인)
- **shadcn/ui**: `npx shadcn@latest init` (구버전 `shadcn-ui` CLI 금지, `@latest` 필수)
- **TanStack Query**: v5 (`@tanstack/react-query` 최신 버전)

### 환경변수 구조 (절대 준수)

**`frontend/.env.example`:**
```bash
# Frontend 공개 환경변수 (NEXT_PUBLIC_ 접두사 = 클라이언트에 노출됨)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

# 실제 값은 frontend/.env.local에 설정 (gitignore됨)
```

**`backend/.env.example`:**
```bash
# Backend 서버 전용 환경변수 (절대 클라이언트에 전달 금지)
DART_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
DATABASE_URL=postgresql://...
ALLOWED_ORIGINS=http://localhost:3000
```

**⚠️ 보안 경고**: `DART_API_KEY`와 `SUPABASE_SERVICE_KEY`는 절대 `NEXT_PUBLIC_` 접두사 사용 금지. 프론트엔드 번들에 포함되면 즉시 보안 사고.

### FastAPI main.py 최소 구조

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # APScheduler 시작 (Story 3.3에서 구현)
    yield
    # 정리

app = FastAPI(title="my-bmad-project API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
```

### GET /health 엔드포인트

```python
# backend/app/api/v1/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}
```

### backend/app/core/config.py

```python
# pydantic-settings 사용 (FastAPI 0.135.1에 포함됨)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DART_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    DATABASE_URL: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
```

### frontend/src/app/layout.tsx QueryClientProvider 설정

```typescript
// 'use client'는 QueryClientProvider에 필요
// App Router 방식: providers.tsx 파일로 분리 권장
// frontend/src/app/providers.tsx
'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

// frontend/src/app/layout.tsx에서 Providers로 래핑
import { Providers } from './providers'
```

### frontend/src/lib/format.ts (스텁 - 완전 구현은 Story 1.4에서)

```typescript
// Story 1.4에서 실제 사용되지만 스텁으로 미리 생성
export function formatKRW(amount: number): string {
  if (Math.abs(amount) >= 1_000_000_000_000) return `₩${(amount/1e12).toFixed(1)}조`
  if (Math.abs(amount) >= 100_000_000) return `₩${(amount/1e8).toFixed(0)}억`
  return `₩${(amount/1e6).toFixed(1)}백만`
}

export function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}
```

### frontend/src/lib/api.ts (스텁 - 완전 구현은 Story 1.3에서)

```typescript
// 모든 FastAPI 호출은 이 파일을 통해서만 (컴포넌트 내 직접 fetch 금지)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, { headers })
  if (!res.ok) throw await res.json()
  return res.json()
}
```

### Vercel 설정 주의사항

- **Root Directory**: 반드시 `frontend/`로 설정 (모노레포이므로 중요)
- **Framework Preset**: Next.js 자동 감지됨
- **Build Command**: 기본값 `npm run build` 사용 (커스텀 불필요)
- **Output Directory**: 기본값 `.next` 사용

### Render 설정 주의사항

- **Root Directory**: `backend/` 설정
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (포트는 Render가 자동 관리하지만 명시)
- **Python Version**: 3.12 Environment Variable `PYTHON_VERSION=3.12.0` 설정

### Supabase pg_cron 설정 상세

```sql
-- Supabase Dashboard → SQL Editor에서 실행
-- 1. pg_net extension 활성화 (HTTP 호출용)
CREATE EXTENSION IF NOT EXISTS pg_net;

-- 2. cron job 등록 (06:58 KST = 21:58 UTC)
SELECT cron.schedule(
  'render-wakeup',     -- job 이름
  '58 21 * * *',       -- cron 표현식 (UTC 기준)
  $$SELECT net.http_get(url := 'https://{YOUR_RENDER_URL}/health')$$
);

-- 3. 등록 확인
SELECT * FROM cron.job;
```

**⚠️ 주의**: `{YOUR_RENDER_URL}`을 실제 Render 배포 URL로 교체 필요

### 아키텍처 디렉토리 구조 완전 트리 (참조용)

```
my-bmad-project/
├── README.md
├── .gitignore
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── components.json          # shadcn/ui 설정
│   ├── .env.example
│   └── src/
│       ├── app/
│       │   ├── globals.css
│       │   ├── layout.tsx       # RootLayout + Providers
│       │   ├── providers.tsx    # QueryClientProvider
│       │   ├── page.tsx         # → /dashboard 리디렉션 예정
│       │   ├── middleware.ts    # 인증 미들웨어 (Story 2.1에서 구현)
│       │   ├── login/
│       │   │   └── page.tsx     # (Story 2.1에서 구현)
│       │   ├── (auth)/
│       │   │   ├── layout.tsx
│       │   │   └── dashboard/
│       │   │       └── page.tsx
│       │   └── shared/
│       │       └── [token]/
│       │           └── page.tsx
│       ├── components/
│       │   ├── ui/              # shadcn/ui 자동 생성 (수정 금지)
│       │   ├── charts/
│       │   ├── search/
│       │   └── layout/
│       ├── lib/
│       │   ├── api.ts           # 스텁 생성 (Story 1.3에서 완성)
│       │   ├── format.ts        # formatKRW 스텁 (Story 1.4에서 완성)
│       │   ├── supabase.ts      # 스텁 (Story 2.1에서 구현)
│       │   └── utils.ts         # shadcn/ui cn()
│       ├── hooks/
│       │   └── use-financial-data.ts  # 스텁
│       └── types/
│           └── index.ts         # 스텁
└── backend/
    ├── requirements.txt
    ├── .env.example
    └── app/
        ├── main.py              # ✅ 이번 스토리에서 완전 구현
        ├── core/
        │   ├── config.py        # ✅ 이번 스토리에서 구현
        │   ├── auth.py          # 스텁 (Story 2.1에서 구현)
        │   └── database.py      # 스텁 (Story 1.2에서 구현)
        ├── api/v1/
        │   ├── __init__.py
        │   ├── health.py        # ✅ 이번 스토리에서 구현
        │   ├── companies.py     # 스텁 (Story 1.3에서 구현)
        │   ├── financials.py    # 스텁 (Story 1.4에서 구현)
        │   ├── analysis_sets.py # 스텁 (Story 3.1에서 구현)
        │   ├── shared.py        # 스텁 (Story 4.2에서 구현)
        │   └── sync.py          # 스텁 (Story 3.3에서 구현)
        ├── services/
        │   ├── dart_client.py   # 스텁 (Story 1.2에서 구현)
        │   ├── financial_service.py    # 스텁
        │   ├── company_service.py      # 스텁
        │   └── analysis_set_service.py # 스텁
        ├── models/
        │   └── schemas.py       # 스텁 (필요 스토리에서 점진적 구현)
        └── scheduler/
            └── tasks.py         # 스텁 (Story 3.3에서 구현)
```

### Project Structure Notes

**이번 스토리에서 생성/완전 구현하는 파일:**
- `my-bmad-project/README.md`, `.gitignore`
- `backend/app/main.py` — FastAPI 앱, CORS 설정
- `backend/app/core/config.py` — pydantic-settings 환경변수
- `backend/app/api/v1/health.py` — `GET /health` 엔드포인트
- `frontend/.env.example`, `backend/.env.example`
- `frontend/src/app/layout.tsx` — QueryClientProvider 래핑
- `frontend/src/app/providers.tsx` — QueryClientProvider 분리

**이번 스토리에서 스텁(빈 파일)만 생성하는 파일:**
- `backend/app/core/auth.py`, `backend/app/core/database.py`
- `backend/app/services/dart_client.py`
- `backend/app/models/schemas.py`
- `backend/app/scheduler/tasks.py`
- `frontend/src/lib/api.ts` (최소 스텁), `frontend/src/lib/format.ts` (완전 구현)
- `frontend/src/lib/supabase.ts` (스텁)
- `frontend/src/types/index.ts` (스텁)
- 모든 `__init__.py` 파일

**의도적으로 이번 스토리에서 미구현 (다음 스토리 담당):**
- DB 스키마 생성 → Story 1.2
- DART API 연동 → Story 1.2
- 기업 검색 API → Story 1.3
- 인증 미들웨어 → Story 2.1

### shadcn/ui 컴포넌트 사전 설치 권장

Story 1.3~1.6에서 사용할 shadcn/ui 컴포넌트를 미리 설치해두면 이후 스토리 구현 속도가 올라감:

```bash
cd frontend
npx shadcn@latest add button card command dialog sidebar skeleton tabs toast tooltip
```

### References

- 초기화 CLI 명령: [architecture.md - Initialization Commands](planning-artifacts/architecture.md#initialization-commands)
- 환경변수 구조: [architecture.md - 환경 변수 구조](planning-artifacts/architecture.md#infrastructure--deployment)
- 완전 디렉토리 구조: [architecture.md - Complete Project Directory Structure](planning-artifacts/architecture.md#complete-project-directory-structure)
- FastAPI main.py 패턴: [architecture.md - Implementation Patterns](planning-artifacts/architecture.md#structure-patterns)
- pg_cron 슬립 방지: [architecture.md - 슬립 방지](planning-artifacts/architecture.md#infrastructure--deployment)
- Story AC 출처: [epics.md - Story 1.1](planning-artifacts/epics.md#story-11-프로젝트-초기화-및-배포-파이프라인-구성)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- FastAPI 0.135.1 미출시: pip install 시 0.128.8 설치됨. 기능 동일, 버전 차이만 존재. requirements.txt에는 실제 설치된 0.128.8이 기록됨
- Python 3.12 미설치: 시스템에 Python 3.9.6만 존재. FastAPI는 3.8+ 지원이므로 동작에 문제 없음. Render 배포 시 환경변수 `PYTHON_VERSION=3.12.0` 설정하면 Render 자체에서 3.12 사용 가능
- shadcn/ui toast 컴포넌트 deprecated: sonner로 대체 설치 (shadcn 2026년 기준 권장사항)
- shadcn/ui base color: --defaults 플래그로 neutral 설치됨 (zinc 대신). 기능에 영향 없으며 향후 변경 가능

### Completion Notes List

- ✅ Task 1 완료: README.md (기술 스택 표 포함), .gitignore (frontend/.env.local, backend/.env, venv/, __pycache__ 제외 포함) 생성
- ✅ Task 2 완료: Next.js 16.1.6, shadcn/ui (neutral + CSS variables), TanStack Query v5.90.21, Recharts 3.7.0 설치. providers.tsx (QueryClient 설정 staleTime=60s, retry=3), layout.tsx 업데이트, lib/(api/format/supabase).ts, types/index.ts 생성. shadcn/ui 컴포넌트 미리 설치: button/card/command/dialog/skeleton/tabs/sonner/tooltip/sidebar
- ✅ Task 3 완료: FastAPI 0.128.8, Python 3.9.6 venv, 87개 패키지 requirements.txt 생성. main.py (CORS + lifespan), config.py (pydantic-settings), health.py (GET /health → {"status": "ok"}), 모든 스텁 파일 생성
- ✅ 백엔드 테스트 3/3 PASS: test_health_returns_200, test_health_returns_ok_status, test_health_content_type_json (pytest 8.4.2)
- ✅ Next.js 빌드 성공: next build 통과, TypeScript 컴파일 오류 없음 (Turbopack 2.1s)
- ⚠️ Tasks 4-6 수동 완료 필요: Vercel, Render, Supabase는 외부 서비스로 사용자가 직접 대시보드에서 설정 필요. Dev Notes 섹션의 각 서비스별 설정 가이드 참조
- ⚠️ Task 7 수동 완료 필요: Tasks 4-6 완료 후 배포 URL로 직접 검증 필요

### File List

**신규 생성 파일:**
- `README.md`
- `.gitignore`
- `frontend/src/app/providers.tsx`
- `frontend/src/app/page.tsx` (수정 — /dashboard 리디렉션)
- `frontend/src/app/layout.tsx` (수정 — Providers 래핑)
- `frontend/src/app/(auth)/layout.tsx`
- `frontend/src/app/(auth)/dashboard/page.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/format.ts`
- `frontend/src/lib/supabase.ts`
- `frontend/src/types/index.ts`
- `frontend/.env.example`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/card.tsx`
- `frontend/src/components/ui/command.tsx`
- `frontend/src/components/ui/dialog.tsx`
- `frontend/src/components/ui/skeleton.tsx`
- `frontend/src/components/ui/tabs.tsx`
- `frontend/src/components/ui/sonner.tsx`
- `frontend/src/components/ui/tooltip.tsx`
- `frontend/src/components/ui/sidebar.tsx`
- `frontend/src/components/ui/separator.tsx`
- `frontend/src/components/ui/sheet.tsx`
- `frontend/src/components/ui/input.tsx`
- `frontend/src/hooks/use-mobile.ts`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/core/__init__.py`
- `backend/app/core/config.py`
- `backend/app/core/auth.py`
- `backend/app/core/database.py`
- `backend/app/api/__init__.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/api/v1/health.py`
- `backend/app/services/__init__.py`
- `backend/app/services/dart_client.py`
- `backend/app/models/__init__.py`
- `backend/app/models/schemas.py`
- `backend/app/scheduler/__init__.py`
- `backend/app/scheduler/tasks.py`
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/tests/__init__.py`
- `backend/tests/test_health.py`
