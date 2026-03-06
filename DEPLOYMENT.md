# 배포 가이드

**스택:** Supabase (DB + Auth) → Render (Backend) → Vercel (Frontend)

---

## 1단계 — Supabase DB 스키마 적용

### 1-1. 테이블 생성

Supabase Dashboard → **SQL Editor** → New Query에서 아래 SQL 실행:

```sql
-- ① 기업 기본 정보
CREATE TABLE IF NOT EXISTS companies (
  corp_code     VARCHAR(8) PRIMARY KEY,
  company_name  VARCHAR(100) NOT NULL,
  stock_code    VARCHAR(6),
  is_listed     BOOLEAN DEFAULT true,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- ② DART 재무 데이터 캐시
CREATE TABLE IF NOT EXISTS financial_statements (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  corp_code   VARCHAR(8) REFERENCES companies(corp_code),
  bsns_year   VARCHAR(4) NOT NULL,
  reprt_code  VARCHAR(5) NOT NULL,
  fs_div      VARCHAR(3) NOT NULL,
  account_key VARCHAR(50) NOT NULL,
  account_nm  VARCHAR(100),
  amount      BIGINT,
  synced_at   TIMESTAMPTZ DEFAULT now(),
  UNIQUE(corp_code, bsns_year, reprt_code, fs_div, account_key)
);

-- ③ 계정과목 표준화 매핑
CREATE TABLE IF NOT EXISTS account_mappings (
  account_nm   VARCHAR(100) PRIMARY KEY,
  account_key  VARCHAR(50) NOT NULL,
  display_name VARCHAR(100),
  category     VARCHAR(20)
);

-- ④ 분석 세트
CREATE TABLE IF NOT EXISTS analysis_sets (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR(100) NOT NULL,
  owner_id      UUID REFERENCES auth.users(id),
  company_codes JSONB NOT NULL,
  config        JSONB,
  share_token   VARCHAR(64) UNIQUE,
  updated_at    TIMESTAMPTZ DEFAULT now(),
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- ⑤ 사용자 프로필 (Supabase Auth 확장)
CREATE TABLE IF NOT EXISTS user_profiles (
  id           UUID PRIMARY KEY REFERENCES auth.users(id),
  role         VARCHAR(20) DEFAULT 'builder',
  display_name VARCHAR(50)
);
```

### 1-2. RLS(Row Level Security) 활성화

```sql
-- analysis_sets: 소유자 본인만 읽기·쓰기, admin은 모두 접근 (FastAPI에서 role 체크)
ALTER TABLE analysis_sets ENABLE ROW LEVEL SECURITY;

-- user_profiles: 본인만 읽기
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 공개 테이블 (인증 없이 읽기 가능)
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_mappings ENABLE ROW LEVEL SECURITY;

-- 기본 정책: Service Role Key (백엔드)는 RLS 우회 → 별도 정책 불필요
-- 읽기 전용 공개 접근이 필요하다면 아래 추가:
CREATE POLICY "companies_public_read" ON companies FOR SELECT USING (true);
CREATE POLICY "financial_statements_public_read" ON financial_statements FOR SELECT USING (true);
CREATE POLICY "account_mappings_public_read" ON account_mappings FOR SELECT USING (true);
```

### 1-3. Supabase Auth 설정

Dashboard → **Authentication** → **Email** 섹션:
- ✅ Enable Email provider
- ✅ Enable Magic Link (passwordless)
- Confirm email: 팀 내부용이면 OFF 권장

Dashboard → **Authentication** → **URL Configuration**:
- Site URL: `https://your-app.vercel.app` (Vercel 배포 후 입력)
- Redirect URLs에 추가: `https://your-app.vercel.app/auth/callback`

### 1-4. 키 수집

Dashboard → **Settings** → **API**에서 복사:
- `Project URL` → `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`
- `anon public` → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `service_role` → `SUPABASE_SERVICE_KEY` (**절대 프론트에 넣지 말 것**)

---

## 2단계 — Render 백엔드 배포

### 2-1. Render 서비스 생성

1. render.com → **New** → **Web Service**
2. GitHub 연결 → `my-bmad-project` 레포 선택
3. 설정:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free

### 2-2. 환경변수 설정

Render Dashboard → 서비스 → **Environment** → Add 환경변수:

| Key | Value |
|-----|-------|
| `DART_API_KEY` | DART OpenAPI 키 |
| `SUPABASE_URL` | Supabase Project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service_role 키 |
| `DATABASE_URL` | `postgresql://postgres:[pw]@db.[ref].supabase.co:5432/postgres` |
| `ANTHROPIC_API_KEY` | `sk-ant-...` (Anthropic Console에서 발급) |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` (Vercel URL, 배포 후 업데이트) |
| `FRONTEND_URL` | `https://your-app.vercel.app` |

### 2-3. 배포 확인

배포 완료 후 브라우저에서 확인:
```
GET https://your-backend.onrender.com/api/v1/health
→ {"status": "ok"}
```

---

## 3단계 — Vercel 프론트엔드 배포

### 3-1. Vercel 프로젝트 생성

1. vercel.com → **Add New Project**
2. GitHub 레포 import
3. **Root Directory:** `frontend` 로 변경 (중요!)
4. Framework: Next.js (자동 감지)

### 3-2. 환경변수 설정

Vercel → 프로젝트 → **Settings** → **Environment Variables**:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |

### 3-3. 배포 및 URL 확인

배포 완료 후 Vercel URL 확인 → **2단계**로 돌아가서:
- Render `ALLOWED_ORIGINS` → Vercel URL로 업데이트
- Render `FRONTEND_URL` → Vercel URL로 업데이트
- Supabase Auth Site URL → Vercel URL로 업데이트

---

## 4단계 — 배포 후 검증

### 체크리스트

```
[ ] GET /api/v1/health → {"status": "ok"}
[ ] 프론트엔드 로딩 (https://your-app.vercel.app)
[ ] Magic Link 로그인 이메일 수신 확인
[ ] 로그인 후 대시보드 접근
[ ] 기업 검색 (예: "삼성전자")
[ ] 재무 차트 로딩
[ ] 분석 세트 저장/로드
[ ] PPT 내보내기 다운로드
[ ] AI 요약 버튼 동작
```

### 첫 번째 Admin 계정 설정

1. Magic Link로 첫 로그인
2. Supabase Dashboard → SQL Editor 실행:
```sql
UPDATE user_profiles
SET role = 'admin'
WHERE id = (SELECT id FROM auth.users WHERE email = 'your@email.com');
```

---

## 5단계 — Render 슬립 방지 (선택)

Supabase Dashboard → **Database** → **Extensions** → `pg_cron` 활성화 후 SQL 실행:

```sql
SELECT cron.schedule(
  'render-wakeup',
  '58 21 * * *',  -- 매일 06:58 KST (UTC 21:58)
  $$SELECT net.http_get(url := 'https://your-backend.onrender.com/api/v1/health')$$
);
```
> `pg_net` extension도 필요: Dashboard → Extensions → `pg_net` 활성화

---

## 환경변수 요약

| 위치 | 변수 | 비고 |
|------|------|------|
| Render | `DART_API_KEY` | DART OpenAPI |
| Render | `SUPABASE_URL` | |
| Render | `SUPABASE_SERVICE_KEY` | ⚠️ 서버 전용 |
| Render | `DATABASE_URL` | Supabase postgres URL |
| Render | `ANTHROPIC_API_KEY` | AI 요약용 ⚠️ 서버 전용 |
| Render | `ALLOWED_ORIGINS` | Vercel URL |
| Render | `FRONTEND_URL` | Vercel URL |
| Vercel | `NEXT_PUBLIC_API_URL` | Render URL |
| Vercel | `NEXT_PUBLIC_SUPABASE_URL` | |
| Vercel | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | |
