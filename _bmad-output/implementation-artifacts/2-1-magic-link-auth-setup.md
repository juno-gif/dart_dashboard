# Story 2.1: 이메일 Magic Link 인증 설정

Status: done

## Story

As a 팀원,
I want to log in with just my email via a magic link (no password required),
So that I can access the dashboard securely without managing credentials.

## Acceptance Criteria

1. **[미인증 리디렉션]** 비인증 사용자가 `/dashboard`에 접근하면, Next.js `middleware.ts`가 실행되어 `/login`으로 리디렉션해야 한다

2. **[Magic Link 발송]** 로그인 페이지에서 이메일만 입력하고 전송하면 Supabase Auth Magic Link가 해당 이메일로 발송되고, 페이지에 "이메일을 확인하세요 — 로그인 링크가 발송되었습니다" 메시지가 표시되어야 한다. 비밀번호 입력 필드는 없어야 한다

3. **[JWT role 클레임]** Magic Link를 클릭하면 Supabase Auth가 토큰을 처리하고, `role` 클레임이 포함된 JWT를 발급하여 `/dashboard`로 리디렉션해야 한다

4. **[FastAPI 토큰 검증]** 인증된 사용자의 FastAPI 요청에 `Authorization: Bearer {token}` 헤더가 포함되면, `core/auth.py`의 `supabase.auth.get_user(token)`으로 검증하고, 실패 시 401 Unauthorized를 반환해야 한다

5. **[API fetch 래퍼 토큰 첨부]** 인증된 사용자의 API 요청 시, `lib/api.ts`의 fetch 래퍼가 자동으로 Authorization 헤더를 첨부해야 한다. 컴포넌트에서 직접 헤더 설정 금지

## Tasks / Subtasks

- [x] Task 1: Frontend — `@supabase/supabase-js` 설치 + Supabase 클라이언트 초기화 (AC: #2, #3, #5)
  - [x] 1.1 `npm install @supabase/supabase-js @supabase/ssr` 실행
  - [x] 1.2 `frontend/src/lib/supabase.ts` 구현: `createClient(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY)` — 기존 placeholder 교체
  - [x] 1.3 `frontend/src/lib/supabase.ts`에 `getSession()` 헬퍼 추가: Supabase 세션(JWT) 반환

- [x] Task 2: Frontend — `use-auth` 훅 생성 (AC: #3, #5)
  - [x] 2.1 `frontend/src/hooks/use-auth.ts` 생성
  - [x] 2.2 `useAuth()` 훅: `supabase.auth.getSession()` → session 반환, `onAuthStateChange` 구독
  - [x] 2.3 `session.access_token` 노출로 `lib/api.ts`에서 사용 가능하게 함

- [x] Task 3: Frontend — 로그인 페이지 구현 (AC: #2)
  - [x] 3.1 `frontend/src/app/login/page.tsx` 생성
  - [x] 3.2 이메일 입력 폼 + "매직 링크 전송" 버튼 (비밀번호 입력 없음)
  - [x] 3.3 `supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: '/dashboard' } })` 호출
  - [x] 3.4 성공 시: "이메일을 확인하세요 — 로그인 링크가 발송되었습니다" 표시 (폼 숨김)
  - [x] 3.5 에러 시: Inline error 메시지 표시 (4xx 패턴 준수)
  - [x] 3.6 shadcn/ui `Input`, `Button` 컴포넌트 사용

- [x] Task 4: Frontend — `middleware.ts` 생성 (AC: #1)
  - [x] 4.1 `frontend/src/middleware.ts` 생성
  - [x] 4.2 `@supabase/ssr` 설치 및 `createServerClient` 사용 (쿠키 기반 SSR 세션)
  - [x] 4.3 `/dashboard` 경로: 세션 없으면 `/login`으로 리디렉션
  - [x] 4.4 `/login` 경로: 이미 인증된 사용자면 `/dashboard`로 리디렉션
  - [x] 4.5 `matcher` 설정: `['/((?!_next/static|_next/image|favicon.ico|api|shared).*)']`

- [x] Task 5: Frontend — `lib/api.ts` 토큰 자동 첨부 업데이트 (AC: #5)
  - [x] 5.1 `frontend/src/lib/api.ts` 수정: `apiGet`, `apiPost` 함수가 `supabase.auth.getSession()` 호출하여 token 자동 첨부
  - [x] 5.2 기존 optional `token?: string` 파라미터 유지 (하위 호환) — 제공 시 우선 사용
  - [x] 5.3 인증 불필요 엔드포인트(공유 링크)는 token 없이도 작동해야 함

- [x] Task 6: Frontend — `(auth)/layout.tsx` 인증 가드 추가 (AC: #1)
  - [x] 6.1 `frontend/src/app/(auth)/layout.tsx` 수정: `useAuth` 훅으로 세션 확인
  - [x] 6.2 세션 없으면 `/login`으로 클라이언트 리디렉션 (middleware와 이중 방어)
  - [x] 6.3 세션 로딩 중: null 반환 (레이아웃 쉬프트 방지)

- [x] Task 7: Backend — `core/auth.py` 구현 (AC: #4)
  - [x] 7.1 `backend/app/core/auth.py` 구현 (TODO 주석 → 실제 구현)
  - [x] 7.2 `HTTPBearer` 스킴 + `get_current_user` FastAPI Dependency 구현
  - [x] 7.3 `supabase_client.auth.get_user(token)` 검증, 실패 시 `HTTPException(401)` raise
  - [x] 7.4 현재 라우터에는 미적용 — Story 2.2에서 RLS와 함께 적용 예정

- [x] Task 8: Backend — 인증 테스트 (AC: #4)
  - [x] 8.1 `backend/tests/test_auth.py` 작성 (4개 테스트)
  - [x] 8.2 유효한 토큰 → 사용자 반환 테스트 (mock)
  - [x] 8.3 유효하지 않은 토큰 → 401 반환 테스트
  - [x] 8.4 user=None 응답 → 401 반환 테스트
  - [x] 8.5 토큰 없음 → 401 반환 테스트
  - [x] 8.6 pytest 전체 40/40 통과

- [x] Task 9: Next.js 빌드 통과 확인 (AC: 전체)
  - [x] 9.1 `npm run build` TypeScript 에러 없이 통과

## Dev Notes

### Critical: 기존 코드 재사용 필수

**이미 존재하는 파일들 (수정 또는 구현):**
- `frontend/src/lib/supabase.ts` — placeholder → 실제 구현으로 교체 (절대 새 파일 생성 금지)
- `frontend/src/app/(auth)/layout.tsx` — 기존 파일 수정 (Story 2.1에서 추가 예정 명시됨)
- `backend/app/core/auth.py` — TODO 주석 구현으로 교체
- `frontend/src/lib/api.ts` — 기존 `apiGet`/`apiPost` 함수 수정 (새 함수 추가 금지)

**로그인 디렉토리:**
- `frontend/src/app/login/` 디렉토리 이미 존재, `page.tsx` 파일 없음 → 생성 필요

**미들웨어:**
- `frontend/src/middleware.ts` 아직 없음 → 새로 생성

### Backend 패키지 주의사항

```
# requirements.txt 현재 상태
supabase>=2.0.0  # 이미 설치됨

# backend/app/core/database.py에서 supabase client 생성 방식 확인 후 재사용
```

`backend/app/core/database.py`의 기존 `get_supabase_client()` 패턴 재사용:
- `auth.py`에서 `get_supabase_client()` 임포트하여 사용 (새 클라이언트 생성 금지)

### Frontend 패키지 의존성

**신규 설치 필요:**
```bash
npm install @supabase/supabase-js
# @supabase/ssr은 middleware에서 쿠키 기반 세션 필요 시 추가 고려
```

**이미 설치됨:**
- `@tanstack/react-query` ^5.90.21
- `sonner` ^2.0.7
- `lucide-react` ^0.577.0
- shadcn/ui 컴포넌트: `Button`, `Input`, `Skeleton` 등

### Task 4: Middleware 구현 패턴

**권장 구현 (쿠키 기반 세션 — SSR 호환):**

```typescript
// frontend/src/middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: { headers: request.headers },
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options)
          })
        },
      },
    }
  )

  const { data: { session } } = await supabase.auth.getSession()

  const isAuthPage = request.nextUrl.pathname.startsWith('/login')
  const isDashboard = request.nextUrl.pathname.startsWith('/dashboard')

  if (isDashboard && !session) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (isAuthPage && session) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api|shared).*)'],
}
```

⚠️ `@supabase/ssr` 설치 필요 (`npm install @supabase/ssr`). Task 4.2에서 확인 후 설치.

**단순화 대안 (쿠키 직접 확인):**
`@supabase/ssr` 없이도 `request.cookies.get('sb-xxx-auth-token')` 쿠키 존재 여부로 간단히 확인 가능. 단, 토큰 만료 처리가 안 되므로 `@supabase/ssr` 사용 권장.

### Task 3: 로그인 페이지 패턴

```tsx
// frontend/src/app/login/page.tsx
'use client'
import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/dashboard`,
      },
    })

    if (error) {
      setError(error.message)
    } else {
      setSent(true)
    }
    setIsLoading(false)
  }

  if (sent) {
    return (
      <main className="...">
        <p>이메일을 확인하세요 — 로그인 링크가 발송되었습니다</p>
      </main>
    )
  }

  return (
    <main className="...">
      <h1>로그인</h1>
      <form onSubmit={handleSubmit}>
        <Input
          type="email"
          placeholder="이메일 입력"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={isLoading}>
          {isLoading ? '전송 중...' : '매직 링크 전송'}
        </Button>
      </form>
    </main>
  )
}
```

### Task 7: Backend auth.py 구현 패턴

```python
# backend/app/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.database import get_supabase_client

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """FastAPI Dependency: JWT 검증 후 사용자 반환
    사용법: async def endpoint(user = Depends(get_current_user))
    """
    token = credentials.credentials
    supabase = get_supabase_client()
    try:
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise ValueError("No user")
        return user.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

⚠️ 현재 financials/companies 라우터에는 적용하지 않음. `get_current_user`만 준비 (Story 2.2 RLS 적용 시 사용).

### Task 5: api.ts 토큰 자동 첨부 수정 패턴

```typescript
// frontend/src/lib/api.ts 수정
import { supabase } from '@/lib/supabase'

async function getToken(): Promise<string | undefined> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token
}

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const resolvedToken = token ?? await getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (resolvedToken) headers['Authorization'] = `Bearer ${resolvedToken}`
  // ... 나머지 동일
}
```

⚠️ `supabase`가 null placeholder이면 `getToken()` 호출 시 에러 발생. Task 1(supabase.ts 구현) 완료 후 Task 5 진행 필수.

### Task 8: 테스트 패턴

```python
# backend/tests/test_auth.py
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_valid_token_returns_user(client):
    """유효한 토큰 → 사용자 반환"""
    mock_user = MagicMock()
    mock_user.user.id = "test-user-id"
    mock_supabase = MagicMock()
    mock_supabase.auth.get_user.return_value = mock_user

    with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        from app.core.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        import asyncio
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")
        user = asyncio.run(get_current_user(creds))
        assert user.id == "test-user-id"

def test_invalid_token_raises_401(client):
    """유효하지 않은 토큰 → 401"""
    mock_supabase = MagicMock()
    mock_supabase.auth.get_user.side_effect = Exception("Invalid JWT")

    with patch("app.core.auth.get_supabase_client", return_value=mock_supabase):
        response = client.get(
            "/api/v1/companies/search?q=test",
            headers={"Authorization": "Bearer invalid-token"},
        )
        # 현재 search 엔드포인트는 인증 불필요 → 200 반환
        # get_current_user Dependency를 직접 테스트하는 방식 권장
        assert response.status_code in [200, 401]
```

⚠️ 현재 라우터에 `get_current_user` Dependency 미적용으로 401 테스트는 독립 함수 테스트로 작성.

### 아키텍처 준수 사항

- **컴포넌트 내 직접 fetch 금지**: 반드시 `lib/api.ts` 경유
- **DART API 격리 유지**: `dart_client.py` 이외 모듈에서 OpenDartReader import 금지
- **Service Key 노출 금지**: `SUPABASE_SERVICE_KEY`는 백엔드 전용, 프론트 미전달
- **Supabase Anon Key**: `NEXT_PUBLIC_SUPABASE_ANON_KEY` — 프론트 공개 사용 가능
- **에러 계층 준수**: 4xx → Inline error, 네트워크 오류 → Toast (기존 QueryCache onError)
- **snake_case 통일**: API 응답 필드명 snake_case 유지

### 환경변수 체크리스트

**frontend/.env.local 필요 항목:**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

**backend/.env 이미 있어야 할 항목:**
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

⚠️ 실제 Supabase 프로젝트 URL/KEY 없으면 Magic Link 테스트 불가. Backend auth.py 및 supabase.ts는 mock으로 단위 테스트 가능.

### 신규 패키지 설치 필요 (승인 필요)

```bash
# Frontend
npm install @supabase/supabase-js   # Supabase 클라이언트
npm install @supabase/ssr           # middleware SSR 세션 처리

# Backend: 추가 불필요 (supabase>=2.0.0 이미 설치됨)
```

### Project Structure Notes

**이번 스토리에서 신규 생성:**
- `frontend/src/middleware.ts`
- `frontend/src/app/login/page.tsx`
- `frontend/src/hooks/use-auth.ts`
- `backend/tests/test_auth.py`

**이번 스토리에서 수정:**
- `frontend/src/lib/supabase.ts` — placeholder → 실제 구현
- `frontend/src/lib/api.ts` — 토큰 자동 첨부
- `frontend/src/app/(auth)/layout.tsx` — 인증 가드 추가
- `backend/app/core/auth.py` — TODO 구현

**의도적으로 이번 스토리에서 미구현:**
- Supabase RLS 정책 → Story 2.2
- 팀 초대/역할 관리 → Story 2.3
- 현재 financials/companies 라우터에 auth 가드 적용 → Story 2.2

### References

- AC 출처: [epics.md - Story 2.1 이메일 Magic Link 인증 설정]
- 인증 흐름: [architecture.md - Authentication & Security]
- JWT 검증 방식: [architecture.md - JWT 검증 방식: Supabase Python SDK]
- 에러 처리: [architecture.md - Error Handling Patterns]
- API 패턴: [architecture.md - API & Communication Patterns]
- 환경변수: [architecture.md - Environment Variables]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Next.js 빌드 시 `supabaseUrl is required` 에러: `createClient`가 module level에서 호출되어 빌드 타임에 env vars가 없을 경우 실패. placeholder fallback (`?? 'https://placeholder.supabase.co'`)으로 해결
- pytest `test_missing_token_raises_403`: FastAPI 최신 버전에서 HTTPBearer가 Authorization 헤더 없을 때 403 대신 401 반환. 테스트를 401로 수정
- Next.js 16.1.6: `middleware.ts`가 deprecated → `proxy.ts` 권장 경고. 현재는 작동하므로 유지 (추후 마이그레이션 필요)

### Completion Notes List

- 모든 9개 Task 완료: pytest 40/40, Next.js build 성공
- `@supabase/supabase-js` + `@supabase/ssr` 설치 완료
- middleware.ts는 Next.js 16에서 deprecated 경고가 있으나 기능 정상 동작
- 실제 Supabase 프로젝트 URL/KEY 없으면 Magic Link 기능 미작동 (env vars 설정 필요)
- Story 2.2에서 financials/companies 라우터에 `get_current_user` Dependency 적용 예정

### File List

- `frontend/src/lib/supabase.ts` (수정)
- `frontend/src/hooks/use-auth.ts` (신규)
- `frontend/src/app/login/page.tsx` (신규)
- `frontend/src/middleware.ts` (신규)
- `frontend/src/lib/api.ts` (수정)
- `frontend/src/app/(auth)/layout.tsx` (수정)
- `backend/app/core/auth.py` (수정)
- `backend/tests/test_auth.py` (신규)
