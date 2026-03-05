# my-bmad-project

내부 DART OpenAPI 기반 재무 분석 대시보드 — B2B PE/M&A 팀용

## 프로젝트 구조

```
my-bmad-project/
├── frontend/     # Next.js 16 (TypeScript + Tailwind + shadcn/ui)
├── backend/      # FastAPI 0.135.1 (Python)
└── _bmad-output/ # BMAD 기획 산출물 (구현 대상 아님)
```

## 로컬 개발 실행

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs (Swagger UI)

# Frontend (별도 터미널)
cd frontend && npm run dev
# → http://localhost:3000
```

## 배포

- **Frontend**: Vercel (Root Directory: `frontend/`)
- **Backend**: Render (Root Directory: `backend/`, Start: `uvicorn app.main:app --host 0.0.0.0`)

## 기술 스택

| Layer | 기술 |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query v5, Recharts |
| Backend | FastAPI 0.135.1, Python 3.12, Pydantic v2, APScheduler |
| Database | Supabase (PostgreSQL + Auth + RLS) |
| External API | DART OpenAPI (금융감독원) |
| Deploy | Vercel (FE) + Render (BE) |
