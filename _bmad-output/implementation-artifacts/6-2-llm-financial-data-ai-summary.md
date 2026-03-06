# Story 6.2: LLM 기반 재무 데이터 자연어 요약

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Builder,
I want to ask natural language questions about financial data and receive AI-generated summaries,
so that I can quickly derive insights without manually analyzing raw numbers.

## Acceptance Criteria

1. **AI 인사이트 패널 열기 (AC1):** Builder가 분석 세트 목록에서 "AI 요약" 버튼을 클릭하면 AI 인사이트 패널이 열리고 `POST /api/v1/analysis-sets/{id}/ai-summary` (question 없이)가 호출되어야 한다.

2. **재무 트렌드 요약 표시 (AC2):** API 요청에 현재 분석 세트의 재무 데이터(P&L)가 포함되면 LLM이 재무 트렌드 요약(성장률, 주요 변화 등)을 자연어 텍스트로 AI 패널에 표시해야 한다. LLM API Key는 서버 환경변수(`ANTHROPIC_API_KEY`)에만 보관되어 클라이언트에 노출되지 않아야 한다.

3. **자연어 질의 응답 (AC3):** Builder가 AI 패널에서 자연어로 질의를 입력하고 제출하면 LLM이 해당 분석 세트의 재무 데이터를 컨텍스트로 사용해 답변을 생성하고 패널에 표시해야 한다.

4. **LLM 오류 처리 (AC4):** LLM API 호출이 실패하거나 타임아웃이 발생하면 "AI 요약을 불러올 수 없습니다. 잠시 후 재시도해 주세요" 메시지가 표시되어야 하며 재시도 버튼이 제공되어야 한다.

## Tasks / Subtasks

- [x] Task 1: Backend — AI 서비스 생성 (AC: 2)
  - [x] `backend/requirements.txt`에 `anthropic>=0.40.0` 추가
  - [x] `backend/app/services/ai_service.py` 생성
    - [x] `generate_financial_summary(set_name, company_codes, financials_by_corp) -> str` — 초기 트렌드 요약 생성
    - [x] `answer_financial_question(question, set_name, company_codes, financials_by_corp) -> str` — Q&A 답변 생성
    - [x] `_build_financial_context(set_name, company_codes, financials_by_corp) -> str` — 재무 데이터를 LLM 컨텍스트 텍스트로 변환 (억 단위)
    - [x] `anthropic.Anthropic()` 클라이언트 초기화 (`ANTHROPIC_API_KEY` env var)
    - [x] `claude-haiku-4-5-20251001` 모델 사용 (비용 효율)
    - [x] LLM 예외 시 `LLMAIError` 커스텀 예외 raise

- [x] Task 2: Backend — API 엔드포인트 추가 (AC: 1, 2, 3, 4)
  - [x] `backend/app/api/v1/analysis_sets.py`에 `POST /analysis-sets/{set_id}/ai-summary` 엔드포인트 추가
  - [x] Pydantic request body: `class AiSummaryRequest(BaseModel): question: Optional[str] = None`
  - [x] Pydantic response: `class AiSummaryResponse(BaseModel): type: str; content: str`
  - [x] 인증 확인: `get_current_user` 의존성
  - [x] DB 조회: `analysis_sets` 테이블에서 set_id 검증 → 404 처리
  - [x] 권한 확인: `owner_id == user.id` 또는 `role == admin` → 403 처리
  - [x] 각 company_code별 `get_pl_data(corp_code, years=5)` 수집 (오류 시 빈 리스트)
  - [x] `question` 없으면 `generate_financial_summary()`, 있으면 `answer_financial_question()` 호출
  - [x] `LLMAIError` 캐치 → 503 `{"detail": {"error": "LLM_API_UNAVAILABLE", "message": "..."}}`
  - [x] `generate_financial_summary` / `answer_financial_question` import 추가

- [x] Task 3: Backend — 테스트 작성 (AC: 1, 2, 3, 4)
  - [x] `backend/tests/test_ai_summary.py` 생성
  - [x] `_mock_supabase_with_set(owner_is_current, role)` 헬퍼 (6-1 패턴 재사용)
  - [x] `test_ai_summary_success` — Builder 본인 세트, question 없음 → 200, type="summary", content 있음
  - [x] `test_ai_summary_with_question` — question 포함 → 200, type="answer", content 있음
  - [x] `test_ai_summary_forbidden` — 타인 세트 → 403 + INSUFFICIENT_PERMISSION
  - [x] `test_ai_summary_not_found` — 없는 set_id → 404 + ANALYSIS_SET_NOT_FOUND
  - [x] `test_ai_summary_admin_can_access_others` — Admin 타인 세트 → 200
  - [x] `test_ai_summary_llm_failure` — `generate_financial_summary` side_effect=LLMAIError → 503 + LLM_API_UNAVAILABLE
  - [x] Mock: `generate_financial_summary`, `answer_financial_question`, `get_supabase_client`, `get_pl_data`

- [x] Task 4: Frontend — API 함수 추가 (AC: 1, 3)
  - [x] `frontend/src/lib/api.ts`에 `requestAiSummary(setId, question?) -> Promise<AiSummaryResult>` 추가
    - [x] `interface AiSummaryResult { type: 'summary' | 'answer'; content: string }`
    - [x] `apiPost` 패턴 사용 (JSON POST, Authorization 헤더)
    - [x] 오류 시 throw (기존 패턴 유지)

- [x] Task 5: Frontend — AiInsightPanel 컴포넌트 생성 (AC: 1, 2, 3, 4)
  - [x] `frontend/src/components/layout/AiInsightPanel.tsx` 생성 (`'use client'`)
  - [x] Props: `interface AiInsightPanelProps { setId: string; setName: string; isOpen: boolean; onClose: () => void }`
  - [x] 패널 열릴 때(`isOpen=true`) 자동으로 초기 요약 요청 (`useEffect`)
  - [x] 상태: `hasError` (bool), `question` (string), `messages` (array)
  - [x] 초기 요약: `useMutation` — `isPending` → 스피너, 성공 → summary 텍스트 표시
  - [x] Q&A 입력: 텍스트 input + 제출 버튼 → `useMutation` → messages 배열에 추가
  - [x] 오류 상태: "AI 요약을 불러올 수 없습니다. 잠시 후 재시도해 주세요" + "재시도" 버튼
  - [x] 패널 레이아웃: 사이드 오버레이 패널 (fixed, right-0, z-50, shadow-xl)
  - [x] 닫기 버튼 (X) + `onClose` 콜백
  - [x] `Loader2` (lucide-react) 로딩 스피너, overflow-y-auto로 스크롤

- [x] Task 6: Frontend — AnalysisSetItem에 "AI 요약" 버튼 추가 (AC: 1)
  - [x] `frontend/src/components/layout/AnalysisSetItem.tsx`에 `AiInsightPanel` import
  - [x] `isAiPanelOpen` state (useState, 기본 false)
  - [x] `canEdit` 블록 내 ShareDialog 다음에 "AI" 버튼 추가
  - [x] 버튼 클릭 → `setIsAiPanelOpen(true)`
  - [x] `<AiInsightPanel setId={set.id} setName={set.name} isOpen={isAiPanelOpen} onClose={() => setIsAiPanelOpen(false)} />` 렌더링

- [x] Task 7: 빌드 및 테스트 검증
  - [x] `venv/bin/pip install anthropic` — 설치 완료
  - [x] `venv/bin/pytest tests/test_ai_summary.py -v` — 6/6 통과
  - [x] `npm run build` — 빌드 오류 없음

## Dev Notes

### Key Design Decisions

- **LLM 선택:** Anthropic Claude `claude-haiku-4-5-20251001` — 비용 효율적, 빠른 응답. API Key는 `ANTHROPIC_API_KEY` 서버 환경변수로만 관리.
- **엔드포인트 단일화:** `POST /ai-summary` 하나로 초기 요약(`question=None`)과 Q&A(`question=str`) 모두 처리. `type` 필드로 응답 종류 구분.
- **재무 컨텍스트 구성:** `get_pl_data` (기존 함수) 활용, 억 단위 변환 후 텍스트로 직렬화하여 LLM system prompt에 포함.
- **타임아웃:** anthropic SDK 기본 timeout 활용 (600s). LLM 호출 실패 시 503 반환.
- **프론트엔드 패널:** 모달이 아닌 사이드 오버레이 패널로 구현, 기존 차트 화면을 가리지 않도록.

### Architecture Patterns

- **Service Layer:** `ai_service.py`는 `ppt_service.py` 구조와 동일하게 순수 함수 형태. 라우터에서만 import. [Source: architecture.md - Service Layer Patterns]
- **API 에러 형식:** `{"detail": {"error": "LLM_API_UNAVAILABLE", "message": "..."}}` — 기존 에러 코드 패턴 준수. [Source: architecture.md - API & Communication Patterns]
- **Frontend API:** `lib/api.ts`에만 fetch 로직. 컴포넌트에서 직접 fetch 금지. [Source: architecture.md - Frontend Architecture]
- **useMutation 패턴:** `isPending` → 버튼 disabled + 스피너, `onError` → toast.error (duration: undefined). [Source: 6-1-analysis-set-ppt-export.md]
- **권한 확인 패턴:** `get_user_role(user.id)` 조회 후 `owner_id == user.id or role == admin`. [Source: analysis_sets.py export_analysis_set_ppt]

### Project Structure Notes

- `backend/app/services/ai_service.py` — 신규 생성 (ppt_service.py 옆)
- `backend/app/api/v1/analysis_sets.py` — 엔드포인트 추가 (기존 파일)
- `backend/tests/test_ai_summary.py` — 신규 생성
- `frontend/src/lib/api.ts` — 함수 추가
- `frontend/src/components/layout/AiInsightPanel.tsx` — 신규 생성
- `frontend/src/components/layout/AnalysisSetItem.tsx` — 버튼 추가

### Financial Context Format for LLM

`_build_financial_context()` 출력 예시:
```
분석 세트: 테크기업비교
포함 기업: CORP001, CORP002

[CORP001 P&L (억원)]
2022: 매출=1200, 영업이익=150, 순이익=120
2023: 매출=1500, 영업이익=200, 순이익=160
2024: 매출=1800, 영업이익=250, 순이익=200

[CORP002 P&L (억원)]
2022: 매출=800, 영업이익=80, 순이익=60
...
```

### LLM Prompt Strategy

- **초기 요약 system prompt:** "당신은 재무 분석 전문가입니다. 아래 재무 데이터를 바탕으로 핵심 트렌드(매출 성장률, 영업이익률 변화, 주요 인사이트)를 3-5문단으로 한국어로 요약하세요."
- **Q&A system prompt:** "당신은 재무 분석 전문가입니다. 아래 재무 데이터를 참고하여 사용자의 질문에 한국어로 답변하세요."
- `max_tokens=1024` (요약), `1500` (Q&A)

### Testing Strategy

- 6-1 테스트 파일(`test_ppt_export.py`)의 mock 패턴 완전 재사용
- `generate_financial_summary`, `answer_financial_question`을 `patch`로 대체해 실제 LLM 호출 없이 테스트
- `LLMAIError` 테스트: `side_effect=LLMAIError("timeout")` 패턴

### References

- [Source: docs/epics.md - Epic 6, Story 6.2]
- [Source: architecture.md - API & Communication Patterns]
- [Source: architecture.md - Service Layer Patterns]
- [Source: architecture.md - Frontend Architecture]
- [Source: implementation-artifacts/6-1-analysis-set-ppt-export.md]
- [Source: backend/app/api/v1/analysis_sets.py - export_analysis_set_ppt 패턴]
- [Source: backend/app/services/ppt_service.py - 서비스 구조]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Task 1: `ai_service.py` 생성. `generate_financial_summary`, `answer_financial_question`, `_build_financial_context`, `_call_llm` 함수 구현. `LLMAIError` 커스텀 예외, `anthropic` SDK, `claude-haiku-4-5-20251001` 모델 사용.
- Task 2: `analysis_sets.py`에 `POST /analysis-sets/{set_id}/ai-summary` 추가. `AiSummaryRequest`, `AiSummaryResponse` Pydantic 모델, 권한 체크(owner/admin), `LLMAIError` → 503 매핑.
- Task 3: `test_ai_summary.py` 6개 테스트 (success, with_question, forbidden, not_found, admin, llm_failure) — 6/6 통과.
- Task 4: `api.ts`에 `AiSummaryResult` 인터페이스, `requestAiSummary(setId, question?)` 함수 추가.
- Task 5: `AiInsightPanel.tsx` 생성. 사이드 오버레이 패널, 초기 요약 자동 로드, 대화형 Q&A, 오류 상태 + 재시도 버튼.
- Task 6: `AnalysisSetItem.tsx`에 `isAiPanelOpen` state, "AI" 버튼, `AiInsightPanel` 렌더링 추가.
- Task 7: pytest 6/6 통과, npm build 성공.
- Code Review H1 fix: Q&A 실패 시 `lastFailedQuestion` state 추가, `questionMutation.onError`에서 변수 캡처 후 재시도 버튼 표시. AC4 완전 구현.
- Code Review M1 fix: `AiSummaryRequest.question`에 `Field(max_length=2000)` 추가 + `test_ai_summary_question_too_long` 테스트 추가 (422 검증). pytest 7/7 통과.
- Code Review M2 fix: `useEffect` 두 개 → 하나로 통합. `isOpen` 변경 시에만 실행, 의도적 eslint-disable 주석 추가.
- Code Review M3 fix: `anthropic.Anthropic` 모듈 레벨 지연 싱글턴(`_anthropic_client`, `_get_client()`)으로 변경. Python 3.9 호환을 위해 `Optional` 타입 사용.

### File List

- backend/requirements.txt
- backend/app/services/ai_service.py (신규)
- backend/app/api/v1/analysis_sets.py
- backend/tests/test_ai_summary.py (신규)
- frontend/src/lib/api.ts
- frontend/src/components/layout/AiInsightPanel.tsx (신규)
- frontend/src/components/layout/AnalysisSetItem.tsx
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/implementation-artifacts/6-2-llm-financial-data-ai-summary.md
