---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
---

# my-bmad-project - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for my-bmad-project, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**카테고리 1: 기업 데이터 수집 (Company Data Acquisition)**
- FR1: 시스템은 DART OpenAPI를 통해 상장사의 P&L·B/S 재무 데이터를 자동 수집할 수 있다 _(Phase 1)_
- FR2: 시스템은 수집된 DART 데이터를 내부 DB에 캐싱하여 반복 API 호출을 최소화할 수 있다 _(Phase 1)_
- FR3: 시스템은 매일 정해진 시각에 DART 최신 데이터를 자동으로 갱신할 수 있다 _(Phase 2)_
- FR4: Builder는 DART 미등록 비상장사의 재무 데이터(기업명·사업연도·매출·영업이익·순이익)를 수기로 입력할 수 있다 _(Phase 3)_
- FR5: 시스템은 수기 입력된 비상장사 데이터를 팀 DB에 저장하여 이후 재사용할 수 있다 _(Phase 3)_

**카테고리 2: 기업 검색 및 조회 (Company Search & Discovery)**
- FR6: Builder는 한국어 기업명 또는 종목코드로 상장사를 검색할 수 있다 _(Phase 1)_
- FR7: 시스템은 검색어 입력 시 corp_code를 자동 매핑하여 DART 데이터를 즉시 로드할 수 있다 _(Phase 1)_
- FR8: Builder는 검색 즉시 해당 기업의 최근 5년치 P&L 데이터를 조회할 수 있다 _(Phase 1)_
- FR9: 시스템은 DART에 존재하지 않는 기업 검색 시 "수기 입력으로 추가" 안내를 표시할 수 있다 _(Phase 3)_
- FR10: Builder는 이전에 입력된 비상장사 데이터를 검색으로 조회할 수 있다 _(Phase 3)_

**카테고리 3: 재무 데이터 시각화 (Financial Data Visualization)**
- FR11: Builder는 단일 기업의 5년치 P&L 핵심 항목(매출·영업이익·순이익) 트렌드를 차트로 볼 수 있다 _(Phase 1)_
- FR12: Builder는 3~5개 기업의 P&L 트렌드를 한 화면에서 동시에 비교할 수 있다 _(Phase 1)_
- FR13: Builder는 B/S 핵심 항목(자산·부채·자본·현금성 자산)을 차트로 볼 수 있다 _(Phase 2)_
- FR14: Builder는 상장사와 비상장사 데이터를 동일한 비교 차트 뷰에서 나란히 볼 수 있다 _(Phase 3)_
- FR15: 시스템은 자동 업데이트로 새 분기 데이터가 추가됐을 때 시각적 알림 표시(●)를 제공할 수 있다 _(Phase 2)_
- FR36: Builder는 현금흐름 핵심 항목(영업활동·투자활동·재무활동 현금흐름)을 차트로 볼 수 있다 _(Phase 2)_

**카테고리 4: 분석 세트 관리 (Analysis Set Management)**
- FR16: Builder는 복수의 기업과 항목 설정을 이름 붙인 분석 세트로 저장할 수 있다 _(Phase 2)_
- FR17: Builder는 저장된 분석 세트를 조회하고 최신 데이터로 즉시 불러올 수 있다 _(Phase 2)_
- FR18: Builder는 자신이 생성한 분석 세트를 수정(기업 추가·삭제, 이름 변경)할 수 있다 _(Phase 2)_
- FR19: Admin은 모든 팀원의 분석 세트를 조회하고 수정할 수 있다 _(Phase 2)_
- FR20: Live Viewer는 공유된 분석 세트를 읽기 전용으로 조회할 수 있다 _(Phase 2)_
- FR21: 시스템은 자동 업데이트 후 분석 세트의 데이터를 최신 분기 기준으로 유지할 수 있다 _(Phase 2)_

**카테고리 5: 사용자 관리 및 접근 제어 (User Management & Access Control)**
- FR22: Admin은 이메일로 팀원을 초대하며 역할(Builder/LiveViewer/ReadOnly)을 지정할 수 있다 _(Phase 2)_
- FR23: Admin은 기존 팀원의 역할을 변경하거나 계정을 비활성화할 수 있다 _(Phase 2)_
- FR24: 사용자는 이메일로 로그인하고 역할 정보가 포함된 JWT 토큰을 발급받을 수 있다 _(Phase 2)_
- FR25: 시스템은 역할(Admin/Builder/LiveViewer/ReadOnly)에 따라 DB 행 단위 접근을 제어할 수 있다 _(Phase 2)_
- FR26: Builder는 자신이 생성한 분석 세트만 수정할 수 있고 타인의 세트는 조회만 가능하다 _(Phase 2)_

**카테고리 6: 공유 및 내보내기 (Sharing & Export)**
- FR27: 사용자는 현재 차트 화면을 이미지 파일로 다운로드할 수 있다 _(Phase 1)_
- FR28: Builder는 특정 분석 세트의 공유 링크를 생성하여 협업 도구(두레이 등)에서 배포할 수 있다 _(Phase 2)_
- FR29: 공유 링크를 통해 접근한 사용자는 분석 세트를 읽기 전용으로 볼 수 있다 _(Phase 2)_
- FR30: Builder는 분석 세트 결과를 PPT 형식으로 내보낼 수 있다 _(Phase 3)_
- FR31: LLM 기반 AI는 재무 데이터에 대한 자연어 질의에 응답하고 요약을 생성할 수 있다 _(Phase 3)_

**카테고리 7: 시스템 및 데이터 무결성 (System & Data Integrity)**
- FR32: 시스템은 DART API 장애 시 DB 캐시 데이터를 제공하고 장애 상태 배너를 표시할 수 있다 _(Phase 1)_
- FR33: Admin은 DART의 비표준 계정과목명을 표준화 키와 매핑하는 테이블을 관리할 수 있다 _(Phase 1)_
- FR34: 시스템은 매핑되지 않은 계정과목명을 원본 그대로 표시하고 Admin에게 알림을 제공할 수 있다 _(Phase 1)_
- FR35: 시스템은 DART API 일일 호출 한도(20,000건)를 초과하지 않도록 DB 캐싱 우선 정책을 적용할 수 있다 _(Phase 1)_

### NonFunctional Requirements

**성능 (Performance)**
- NFR-P1: 대시보드 초기 로딩(Vercel CDN 기준) 3초 이내
- NFR-P2: 기업 1개 P&L 조회 — DB 캐시 히트 시 1초 이내, DART API 신규 호출 시 30초 이내
- NFR-P3: 3~5개 기업 비교 차트 전환 5초 이내
- NFR-P4: DART 일일 자동 업데이트 작업 완료 시간 30분 이내

**보안 (Security)**
- NFR-S1: DART API Key는 서버 환경변수에만 보관, 클라이언트에 절대 노출 불가
- NFR-S2: Supabase Service Role Key는 FastAPI 서버에서만 사용
- NFR-S3: 모든 클라이언트-서버 통신 HTTPS 필수
- NFR-S4: JWT 토큰에 사용자 역할(role) 클레임 포함, FastAPI 미들웨어에서 매 요청 검증
- NFR-S5: Supabase RLS 정책으로 DB 행 단위 접근 제어

**안정성 (Reliability)**
- NFR-R1: DART 자동 업데이트(APScheduler 매일 07:00) 성공률 95% 이상
- NFR-R2: DART API 장애 시 DB 캐시 데이터 즉시 제공, 사용자에게 캐시 기준 날짜 표시
- NFR-R3: Render Free 인스턴스 슬립 방지를 위한 pg_cron 06:58 ping 메커니즘 유지
- NFR-R4: 업무 시간(평일 09:00~18:00 KST) 중 서비스 가용성 99% 이상 유지

**통합 (Integration)**
- NFR-I1: DART OpenAPI 일일 호출 건수 20,000건 미초과
- NFR-I2: Supabase Free Tier DB 사용량 500MB 미만 유지
- NFR-I3: FastAPI CORS 허용 도메인을 Vercel 배포 도메인으로만 제한
- NFR-I4: DART API 스펙 변경 시 `dart_client.py` 단일 모듈만 수정하여 영향 범위 격리 가능

**유지보수성 (Maintainability)**
- NFR-M1: 비코더 1인이 AI 개발 도구로 독립적으로 유지보수 가능한 코드 구조 유지
- NFR-M2: GitHub main 브랜치 push 시 Vercel + Render 자동 배포 적용
- NFR-M3: 개발/프로덕션 환경변수 분리 (.env.local / Vercel·Render 환경변수)
- NFR-M4: `account_mappings` 테이블을 통해 DART 계정과목 변경 시 코드 수정 없이 Admin이 직접 대응 가능

### Additional Requirements

**아키텍처에서 추출한 기술 요구사항:**
- **[중요] 프로젝트 초기화 (Epic 1 Story 1 필수):** Next.js 16 + FastAPI 0.135.1 공식 CLI 조합으로 monorepo 초기화
  ```bash
  npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"
  npx shadcn@latest init
  mkdir backend && python -m venv venv && pip install "fastapi[standard]" supabase ...
  ```
- **DB 스키마 생성:** 5개 테이블(companies, financial_statements, account_mappings, analysis_sets, user_profiles) Supabase Dashboard에서 수동 적용
- **DART API 격리 모듈:** `dart_client.py` 단일 진입점으로 구현 필수 (다른 모듈에서 OpenDartReader 직접 import 금지)
- **환경변수 구조:** frontend/.env.local + backend/.env 분리, NEXT_PUBLIC_ 접두사 규칙 준수
- **CI/CD 설정:** Vercel + Render GitHub main 브랜치 자동 배포 연동
- **Render 슬립 방지:** FastAPI `/health` 엔드포인트 + Supabase pg_cron 06:58 ping 구현

**UX에서 추출한 구현 요구사항:**
- **Desktop-First 반응형:** 1440px+ 완전 지원, 1024px 최소 지원, 767px 이하 접속 불가 안내 페이지
- **WCAG 2.1 AA 접근성:** 모든 인터랙티브 컴포넌트 키보드 탐색, ARIA 레이블, 색상 대비 4.5:1 이상
- **스켈레톤 로딩:** 실제 컨텐츠와 동일한 높이/너비 유지 (레이아웃 쉬프트 방지)
- **CompanySearchInput:** 300ms 디바운스, Command 컴포넌트 기반, 최대 8개 자동완성 결과
- **formatKRW 유틸:** `억` / `백만` / `조` 단위 변환, 모든 금액 표시에 적용
- **Toast 피드백:** 성공 3초 자동 소멸, 오류 수동 닫기 + 재시도 버튼
- **공유 Dialog:** 최대 480px 너비, backdrop-blur 오버레이

### FR Coverage Map

- FR1: Epic 1 — DART OpenAPI 수집 모듈 구현
- FR2: Epic 1 — DB 캐싱 전략 (financial_statements 테이블)
- FR6: Epic 1 — 기업명/종목코드 검색 UI (CompanySearchInput)
- FR7: Epic 1 — corp_code 자동 매핑 → DART 데이터 즉시 로드
- FR8: Epic 1 — 5년치 P&L 데이터 조회 API + 차트 렌더링
- FR11: Epic 1 — 단일 기업 P&L 트렌드 차트 (FinancialChart)
- FR12: Epic 1 — 3~5개 기업 P&L 비교 차트
- FR27: Epic 1 — 차트 이미지 다운로드
- FR32: Epic 1 — DART 장애 시 캐시 폴백 + 장애 배너
- FR33: Epic 1 — 계정과목 표준화 매핑 테이블 관리
- FR34: Epic 1 — 미매핑 계정과목명 원본 표시 + Admin 알림
- FR35: Epic 1 — DB 캐싱 우선 정책 (DART API 호출 한도 준수)
- FR22: Epic 2 — Admin 이메일 팀원 초대 + 역할 지정
- FR23: Epic 2 — Admin 팀원 역할 변경·계정 비활성화
- FR24: Epic 2 — 이메일 로그인 + JWT 역할 클레임 발급
- FR25: Epic 2 — Supabase RLS 역할별 DB 행 단위 접근 제어
- FR26: Epic 2 — Builder 본인 분석 세트만 수정 가능
- FR3: Epic 3 — APScheduler 매일 07:00 DART 자동 갱신
- FR13: Epic 3 — B/S 핵심 항목 차트
- FR36: Epic 3 — 현금흐름 핵심 항목 차트
- FR15: Epic 3 — 자동 업데이트 시각적 알림 표시(●)
- FR16: Epic 3 — 분석 세트 저장
- FR17: Epic 3 — 저장된 분석 세트 최신 데이터로 불러오기
- FR18: Epic 3 — 분석 세트 수정(기업 추가·삭제, 이름 변경)
- FR19: Epic 3 — Admin 전체 분석 세트 조회·수정
- FR20: Epic 3 — Live Viewer 읽기 전용 분석 세트 조회
- FR21: Epic 3 — 자동 업데이트 후 분석 세트 최신 분기 유지
- FR28: Epic 4 — 분석 세트 공유 링크 생성
- FR29: Epic 4 — 공유 링크 읽기 전용 접근 (인증 불필요)
- FR4: Epic 5 — 비상장사 재무 데이터 수기 입력 UI
- FR5: Epic 5 — 수기 입력 비상장사 데이터 DB 저장·재사용
- FR9: Epic 5 — DART 미등록 기업 검색 시 "수기 입력으로 추가" 안내
- FR10: Epic 5 — 이전 입력 비상장사 데이터 검색으로 조회
- FR14: Epic 5 — 상장사·비상장사 통합 비교 차트 뷰
- FR30: Epic 6 — 분석 세트 PPT 내보내기
- FR31: Epic 6 — LLM 기반 재무 데이터 자연어 요약

## Epic List

### Epic 1: 기반 구축 및 P&L 데이터 탐색
팀원이 기업명을 검색해 5년치 P&L·비교 차트를 즉시 확인하고 이미지로 저장할 수 있는 기본 대시보드가 배포된다. (Phase 1 MVP)
**FRs covered:** FR1, FR2, FR6, FR7, FR8, FR11, FR12, FR27, FR32, FR33, FR34, FR35

### Epic 2: 사용자 인증 및 팀 접근 제어
팀원이 이메일 Magic Link로 비밀번호 없이 로그인하고, Admin이 역할을 지정하며, Supabase RLS가 역할별 DB 접근을 자동으로 제어한다. (Phase 2)
**FRs covered:** FR22, FR23, FR24, FR25, FR26

### Epic 3: 분석 세트 저장·재사용·자동 갱신
기업 묶음을 이름 붙인 분석 세트로 저장하고, 분기마다 자동으로 최신 데이터가 반영되며, B/S 지표도 함께 확인할 수 있다. (Phase 2)
**FRs covered:** FR3, FR13, FR36, FR15, FR16, FR17, FR18, FR19, FR20, FR21

### Epic 4: 공유 및 협업
Builder가 분석 세트의 공유 링크를 생성해 팀원 및 경영진이 인증 없이 읽기 전용으로 조회할 수 있다. (Phase 2)
**FRs covered:** FR28, FR29

### Epic 5: 비상장사 데이터 입력
DART 미등록 비상장사의 재무 데이터를 Builder가 직접 입력하고, 상장사와 동일한 비교 차트에서 나란히 볼 수 있다. (Phase 3)
**FRs covered:** FR4, FR5, FR9, FR10, FR14

### Epic 6: 고급 내보내기 및 AI 인사이트
분석 결과를 PPT 형식으로 내보내고, LLM 기반 AI가 재무 데이터에 대한 자연어 요약을 생성한다. (Phase 3)
**FRs covered:** FR30, FR31

---

## Epic 1: 기반 구축 및 P&L 데이터 탐색

팀원이 기업명을 검색해 5년치 P&L·비교 차트를 즉시 확인하고 이미지로 저장할 수 있는 기본 대시보드가 배포된다. (Phase 1 MVP)

### Story 1.1: 프로젝트 초기화 및 배포 파이프라인 구성

As a 개발자(팀),
I want to initialize the monorepo with Next.js 16 and FastAPI and configure automatic deployments,
So that the team has a live deployed URL to build upon and can access the dashboard immediately.

**Acceptance Criteria:**

**Given** 빈 GitHub 레포지토리가 준비된 상태에서
**When** 프로젝트 초기화 명령을 실행하면
**Then** `frontend/`(Next.js 16, TypeScript, Tailwind, shadcn/ui)와 `backend/`(FastAPI 0.135.1, Python 3.12) 디렉토리 구조가 아키텍처 문서의 프로젝트 트리와 일치해야 한다
**And** `frontend/.env.example`과 `backend/.env.example`에 모든 필수 환경변수가 문서화되어야 한다

**Given** GitHub main 브랜치에 코드가 push될 때
**When** 자동 배포가 실행되면
**Then** Vercel이 `frontend/`를 빌드해 HTTPS 배포 URL을 생성해야 한다
**And** Render가 `backend/`를 빌드해 `GET /health`가 200 OK `{"status": "ok"}`를 반환해야 한다

**Given** Render Free 인스턴스가 슬립 상태일 수 있을 때
**When** Supabase pg_cron이 매일 06:58 KST에 `GET {RENDER_URL}/health`를 호출하면
**Then** Render 인스턴스가 깨어나 업무 시간 내 요청에 즉시 응답해야 한다

---

### Story 1.2: DART 데이터 수집 및 DB 스키마 구축

As a 시스템,
I want to connect to DART OpenAPI and store financial data in a structured database,
So that company financial data can be served instantly without repeated API calls.

**Acceptance Criteria:**

**Given** Supabase Dashboard SQL Editor에서 스키마 SQL이 실행되면
**When** 아키텍처 문서의 DB 스키마가 적용되면
**Then** `companies`, `financial_statements`, `account_mappings` 테이블이 올바른 컬럼·타입·제약조건으로 생성되어야 한다

**Given** DART API Key가 `backend/.env`에 설정된 상태에서
**When** `dart_client.py`의 함수가 호출되면
**Then** DART OpenAPI에서 재무 데이터를 조회하고 `financial_statements` 테이블에 영구 저장해야 한다
**And** OpenDartReader는 오직 `dart_client.py`에서만 import 되어야 한다 (다른 모듈 직접 import 금지)

**Given** 동일한 기업·연도 데이터를 두 번 수집할 때
**When** `financial_statements` INSERT가 실행되면
**Then** UNIQUE(corp_code, bsns_year, reprt_code, fs_div, account_key) 제약으로 중복 없이 UPSERT 처리되어야 한다

**Given** FastAPI 서버가 실행 중일 때
**When** API 응답이 클라이언트에 전달되면
**Then** DART API Key와 Supabase Service Key가 응답 헤더·본문·프론트엔드 번들에 절대 노출되지 않아야 한다

---

### Story 1.3: 기업 검색 기능

As a Builder,
I want to search for a company by name or stock code and select it from suggestions,
So that I can find the right company instantly without knowing its DART corp_code.

**Acceptance Criteria:**

**Given** 대시보드가 로드된 상태에서
**When** Builder가 검색창에 "카카오"를 입력하면 (300ms 디바운스 후)
**Then** `GET /api/v1/companies/search?q=카카오&limit=8`이 호출되고 자동완성 드롭다운에 최대 8개 결과가 표시되어야 한다
**And** 각 결과에 기업명, 종목코드가 표시되어야 한다

**Given** 검색 결과가 표시된 상태에서
**When** Builder가 기업을 클릭하거나 Enter로 선택하면
**Then** corp_code가 자동 매핑되고 CompanyTag가 생성되어야 한다
**And** 검색 입력창이 초기화되어야 한다

**Given** 검색어에 해당하는 기업이 없을 때
**When** 드롭다운이 표시되면
**Then** "검색 결과 없음" 메시지와 "종목코드로 검색해보세요" 힌트가 표시되어야 한다

**Given** CompanySearchInput에서 키보드로 탐색할 때
**When** 방향키를 누르면
**Then** 드롭다운 항목이 이동하고 Enter로 선택되어야 한다
**And** `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded` ARIA 속성이 적용되어야 한다

---

### Story 1.4: 단일 기업 P&L 차트 및 KPI 카드

As a Builder,
I want to see a 5-year P&L trend chart and key financial KPI cards after selecting a company,
So that I can immediately understand financial performance without manual data assembly.

**Acceptance Criteria:**

**Given** Builder가 CompanySearchInput에서 기업을 선택하면
**When** 대시보드 메인 영역이 렌더링되면
**Then** 해당 기업의 최근 5년치 매출·영업이익·순이익 데이터가 FinancialChart에 표시되어야 한다
**And** KPICard 4개(매출·영업이익·순이익·영업이익률)가 최신 연도 기준으로 표시되어야 한다

**Given** 재무 데이터가 DB에 캐싱된 상태에서
**When** `GET /api/v1/companies/{corp_code}/financials?years=5&type=pl`이 호출되면
**Then** DB에서 1초 이내에 snake_case JSON으로 응답해야 한다
**And** 금액은 원 단위 BIGINT로 응답하고 프론트엔드에서 `formatKRW()`로만 변환되어야 한다 (컴포넌트 내 직접 변환 금지)

**Given** 데이터 로딩 중일 때
**When** API 응답을 기다리는 동안
**Then** KPICard와 FinancialChart에 실제 컴포넌트와 동일한 높이의 Skeleton이 표시되어야 한다 (레이아웃 쉬프트 없음)

**Given** KPICard에 전년 대비 증감률이 표시될 때
**When** 수치가 양수이면 ▲ Green-600, 음수이면 ▼ Red-500으로 표시되어야 한다

---

### Story 1.5: 다중 기업 P&L 비교 차트

As a Builder,
I want to add multiple companies and compare their P&L trends in a single view,
So that I can analyze competitive dynamics without switching between screens or manual data assembly.

**Acceptance Criteria:**

**Given** 기업 1개가 선택된 상태에서
**When** Builder가 추가 기업을 검색해 선택하면
**Then** CompanyTag가 추가되고 `GET /api/v1/companies/compare?codes=005930,035720&type=pl`이 호출되어 비교 차트가 렌더링되어야 한다

**Given** 기업이 5개 선택된 상태에서
**When** Builder가 추가 기업을 검색하려 하면
**Then** CompanySearchInput이 비활성화되고 Tooltip "최대 5개 기업까지 비교 가능"이 표시되어야 한다

**Given** CompanyTag의 X 버튼을 클릭하면
**When** 기업이 목록에서 제거되면
**Then** 비교 차트가 즉시 업데이트되어야 한다
**And** 기업이 1개만 남으면 단일 기업 뷰로 전환되어야 한다

**Given** 비교 차트가 렌더링될 때
**When** Recharts가 데이터를 표시하면
**Then** 각 기업에 고유 색상이 할당되고 범례·툴팁이 정확히 표시되어야 한다
**And** 호버 시 기업별 해당 연도 수치가 `formatKRW()` 형식으로 툴팁에 표시되어야 한다

---

### Story 1.6: 차트 이미지 다운로드 및 시스템 안정성

As a Builder,
I want to download charts as image files and see clear status messages when data is unavailable,
So that I can use charts in presentations and always understand the reliability of the data shown.

**Acceptance Criteria:**

**Given** 차트가 렌더링된 상태에서
**When** Builder가 이미지 다운로드 버튼을 클릭하면
**Then** 현재 차트 영역이 PNG 파일로 다운로드되어야 한다
**And** 파일명은 `{기업명}_{YYYY-MM-DD}.png` 형식이어야 한다

**Given** DART API가 장애 상태일 때
**When** 기업 데이터를 조회하면
**Then** FastAPI가 DB 캐시 데이터를 제공하면서 503 응답과 `DART_API_UNAVAILABLE` 에러 코드를 반환해야 한다
**And** 프론트엔드 상단에 Yellow-100 배경 배너 "일부 데이터가 오래되었습니다 — 마지막 업데이트: N일 전"이 표시되어야 한다

**Given** account_mappings에 매핑이 없는 계정과목이 DART에서 수신될 때
**When** 재무 데이터가 차트에 표시되면
**Then** 미매핑 계정과목은 DART 원본명 그대로 표시되어야 한다
**And** FastAPI 서버 로그에 미매핑 계정과목 경고가 기록되어야 한다

**Given** API 호출이 네트워크 오류로 실패할 때
**When** TanStack Query 자동 재시도가 3회 모두 실패하면
**Then** 하단 우측에 Red-500 배경 Toast "잠시 후 재시도해 주세요"가 표시되어야 한다 (수동 닫기)

---

## Epic 2: 사용자 인증 및 팀 접근 제어

팀원이 이메일 Magic Link로 비밀번호 없이 로그인하고, Admin이 역할을 지정하며, Supabase RLS가 역할별 DB 접근을 자동으로 제어한다. (Phase 2)

### Story 2.1: 이메일 Magic Link 인증 설정 (비밀번호 없음)

As a 팀원,
I want to log in with just my email via a magic link (no password required),
So that I can access the dashboard securely without managing credentials.

**Acceptance Criteria:**

**Given** 인증되지 않은 사용자가 `/dashboard`에 접근하면
**When** Next.js `middleware.ts`가 실행되면
**Then** `/login` 페이지로 리디렉션되어야 한다

**Given** 로그인 페이지에서 이메일만 입력하고 제출하면
**When** Supabase Auth Magic Link가 이메일로 발송되면
**Then** 로그인 페이지에 "이메일을 확인하세요 — 로그인 링크가 발송되었습니다" 안내 메시지가 표시되어야 한다
**And** 비밀번호 입력 필드는 존재하지 않아야 한다

**Given** 팀원이 이메일 수신함에서 Magic Link를 클릭하면
**When** Supabase Auth가 토큰을 처리하면
**Then** `role` 클레임이 포함된 JWT 토큰이 발급되고 `/dashboard`로 리디렉션되어야 한다

**Given** 인증된 사용자가 FastAPI에 요청을 보낼 때
**When** `Authorization: Bearer {token}` 헤더가 포함되면
**Then** `core/auth.py`의 `supabase.auth.get_user(token)`으로 토큰이 검증되어야 한다
**And** 검증 실패 시 401 Unauthorized가 반환되어야 한다

**Given** 로그인 성공 후 API 요청을 보낼 때
**When** `lib/api.ts`의 fetch 래퍼 함수가 호출되면
**Then** Authorization 헤더가 자동으로 첨부되어야 한다 (컴포넌트에서 직접 헤더 설정 금지)

---

### Story 2.2: Supabase RLS 및 역할별 DB 접근 제어

As a 시스템,
I want database-level row access control based on user roles,
So that data security is enforced at the database layer regardless of application code.

**Acceptance Criteria:**

**Given** Supabase Dashboard에서 RLS 스키마가 적용되면
**When** `user_profiles` 테이블이 생성되면
**Then** `auth.users(id)` 참조, `role` 컬럼 기본값 `'builder'`로 생성되어야 한다

**Given** 인증된 Builder가 `financial_statements`를 조회하면
**When** RLS 정책이 평가되면
**Then** 인증된 모든 사용자에게 조회가 허용되어야 한다 (재무 데이터는 공개 정보)

**Given** Builder가 타인의 `analysis_sets`를 수정하려 하면
**When** UPDATE 쿼리가 실행되면
**Then** `owner_id = auth.uid()` 조건의 RLS 정책으로 차단되어야 한다

**Given** 인증되지 않은 요청으로 Supabase에 직접 쿼리를 보내면
**When** RLS가 적용되면
**Then** 데이터가 반환되지 않아야 한다 (anon key 직접 접근 차단, 단 공유 토큰 기반 접근은 Epic 4에서 별도 정책 추가)

**Given** Admin이 `user_profiles`를 조회하면
**When** RLS 정책이 평가되면
**Then** 전체 사용자 프로필을 조회할 수 있어야 한다
**And** 일반 사용자는 본인 프로필만 조회할 수 있어야 한다

---

### Story 2.3: Admin 팀원 초대 및 역할 관리

As an Admin,
I want to invite team members by email and assign their roles,
So that each team member can access the dashboard with the right permissions via a single email click.

**Acceptance Criteria:**

**Given** Admin이 팀원 초대 UI에서 이메일과 역할(Builder/LiveViewer/ReadOnly)을 입력하고 제출하면
**When** Supabase Auth invite API가 Magic Link 초대 이메일을 발송하면
**Then** `user_profiles`에 지정된 역할이 저장되어야 한다
**And** 초대받은 팀원이 이메일 Magic Link를 클릭하면 비밀번호 설정 없이 즉시 대시보드에 접근할 수 있어야 한다

**Given** Admin이 팀원의 역할을 변경하면
**When** `user_profiles.role`이 업데이트되면
**Then** 변경된 역할이 즉시 RLS 정책에 적용되어야 한다

**Given** Builder가 팀원 초대를 시도하면
**When** FastAPI 초대 엔드포인트가 호출되면
**Then** `INSUFFICIENT_PERMISSION` 에러 코드와 403 응답이 반환되어야 한다

**Given** Admin이 팀원 계정을 비활성화하면
**When** Supabase Auth에서 계정이 비활성화되면
**Then** 해당 사용자는 이후 Magic Link 요청이 거부되어야 한다
**And** 기존 발급된 JWT 토큰으로도 API 접근이 차단되어야 한다

---

## Epic 3: 분석 세트 저장·재사용·자동 갱신

기업 묶음을 이름 붙인 분석 세트로 저장하고, 분기마다 자동으로 최신 데이터가 반영되며, B/S 지표도 함께 확인할 수 있다. (Phase 2)

### Story 3.1: 분석 세트 저장 및 불러오기

As a Builder,
I want to save the current company selection as a named analysis set and reload it instantly,
So that I can resume complex multi-company analyses without rebuilding them from scratch.

**Acceptance Criteria:**

**Given** Builder가 1개 이상의 기업을 선택한 상태에서
**When** "분석 세트 저장" 버튼을 클릭하고 이름을 입력해 제출하면
**Then** `POST /api/v1/analysis-sets` 요청으로 DB에 저장되고 저장 목록에 즉시 표시되어야 한다
**And** 성공 Toast "분석 세트가 저장되었습니다"가 3초 후 자동 소멸되어야 한다

**Given** 저장된 분석 세트 목록이 표시된 상태에서
**When** Builder가 특정 분석 세트를 클릭하면
**Then** `GET /api/v1/analysis-sets/{id}`로 구성이 불러와지고 CompanyTag가 복원되어야 한다
**And** 각 기업의 최신 재무 데이터가 자동으로 로드되어 차트가 렌더링되어야 한다

**Given** 저장된 분석 세트가 없는 상태에서
**When** Builder가 분석 세트 목록을 열면
**Then** "저장된 분석 세트가 없습니다. 기업을 선택한 후 저장해 보세요." 빈 상태 메시지가 표시되어야 한다

**Given** 분석 세트 이름이 이미 존재할 때
**When** Builder가 동일한 이름으로 저장하려 하면
**Then** "이미 사용 중인 이름입니다. 다른 이름을 입력하세요." 인라인 오류가 표시되어야 한다

---

### Story 3.2: 분석 세트 수정 및 역할 기반 접근

As a Builder,
I want to edit my own analysis sets and have Admin manage all team sets,
So that each team member operates within their permission boundary when collaborating.

**Acceptance Criteria:**

**Given** Builder가 본인 소유 분석 세트를 불러온 상태에서
**When** 기업을 추가·삭제하거나 세트 이름을 변경하고 저장하면
**Then** `PATCH /api/v1/analysis-sets/{id}`로 변경 사항이 DB에 반영되어야 한다
**And** 성공 Toast "변경 사항이 저장되었습니다"가 표시되어야 한다

**Given** Builder가 타인 소유 분석 세트를 수정하려 하면
**When** FastAPI 수정 엔드포인트가 호출되면
**Then** `INSUFFICIENT_PERMISSION` 에러 코드와 403 응답이 반환되어야 한다
**And** 프론트엔드에서 타인 소유 세트의 편집 버튼이 비활성화되어야 한다

**Given** Admin이 팀원의 분석 세트를 수정하면
**When** `PATCH /api/v1/analysis-sets/{id}`가 호출되면
**Then** `owner_id`와 무관하게 변경이 허용되어야 한다

**Given** LiveViewer가 분석 세트 목록을 조회하면
**When** 리스트 UI가 렌더링되면
**Then** 편집·삭제 버튼이 표시되지 않고 읽기 전용 뷰만 제공되어야 한다

---

### Story 3.3: APScheduler DART 자동 갱신 및 신규 데이터 알림

As a 시스템,
I want to automatically sync DART data daily and notify users when new quarter data arrives,
So that analysis sets always reflect the latest financial information without manual intervention.

**Acceptance Criteria:**

**Given** FastAPI 서버가 실행 중이고 APScheduler가 설정된 상태에서
**When** 매일 07:00 KST에 스케줄이 트리거되면
**Then** `dart_client.py`를 통해 등록된 기업의 최신 재무 데이터를 조회하고 `financial_statements`에 UPSERT해야 한다
**And** 갱신 완료 후 서버 로그에 `[DART_SYNC] 완료: {n}개 기업, {m}개 레코드 갱신` 형식으로 기록되어야 한다

**Given** 자동 갱신 후 기존에 없던 신규 분기 데이터가 추가되면
**When** Builder가 해당 기업이 포함된 분석 세트를 조회하면
**Then** 기업명 옆에 "●" 신규 데이터 알림 인디케이터가 표시되어야 한다
**And** 분석 세트의 차트가 최신 분기 데이터를 자동으로 포함해야 한다 (FR21)

**Given** DART 자동 갱신 중 API 오류가 발생하면
**When** `dart_client.py`가 예외를 반환하면
**Then** 기존 DB 데이터는 손상되지 않고 유지되어야 한다
**And** 서버 로그에 `[DART_SYNC] 실패: {error}` 오류가 기록되어야 한다

**Given** 자동 갱신이 20,000건 API 한도에 근접할 때
**When** 일일 호출 누적이 18,000건을 초과하면
**Then** 남은 기업 갱신을 중단하고 `[DART_SYNC] 한도 초과 방지: 조기 종료` 로그를 남겨야 한다 (NFR-I1)

---

### Story 3.4: B/S 핵심 항목 차트

As a Builder,
I want to view Balance Sheet key metrics (assets, liabilities, equity, cash) as a chart,
So that I can assess a company's financial position alongside P&L trends.

**Acceptance Criteria:**

**Given** Builder가 기업을 선택한 상태에서
**When** "B/S" 탭 또는 지표 전환 버튼을 클릭하면
**Then** `GET /api/v1/companies/{corp_code}/financials?years=5&type=bs`가 호출되고 자산·부채·자본·현금성자산 데이터가 FinancialChart에 표시되어야 한다

**Given** B/S 차트가 렌더링될 때
**When** 금액이 표시되면
**Then** 모든 금액은 `formatKRW()`를 통해 변환되어야 한다 (컴포넌트 내 직접 변환 금지)
**And** 최근 5개 사업연도 데이터가 표시되어야 한다

**Given** 데이터 로딩 중일 때
**When** B/S API 응답을 기다리는 동안
**Then** FinancialChart와 동일한 높이의 Skeleton이 표시되어야 한다 (레이아웃 쉬프트 없음)

**Given** 해당 기업의 B/S 데이터가 DB에 존재하지 않을 때
**When** B/S 탭을 클릭하면
**Then** "B/S 데이터를 제공하지 않는 기업입니다. P&L 데이터만 이용 가능합니다." 안내 메시지가 표시되어야 한다

---

### Story 3.5: 현금흐름 핵심 항목 차트

As a Builder,
I want to view Cash Flow key metrics (operating, investing, financing activities) as a chart,
So that I can assess a company's cash generation and capital allocation alongside P&L and B/S.

**Acceptance Criteria:**

**Given** Builder가 기업을 선택한 상태에서
**When** "현금흐름" 탭을 클릭하면
**Then** `GET /api/v1/companies/{corp_code}/financials?years=5&type=cf`가 호출되고 영업활동·투자활동·재무활동 현금흐름 데이터가 FinancialChart에 표시되어야 한다

**Given** 현금흐름 차트가 렌더링될 때
**When** 금액이 표시되면
**Then** 모든 금액은 `formatKRW()`를 통해 변환되어야 한다 (컴포넌트 내 직접 변환 금지)
**And** 최근 5개 사업연도 데이터가 표시되어야 한다
**And** 영업활동(OperatingCF)·투자활동(InvestingCF)·재무활동(FinancingCF) 3개 항목이 구분되어 표시되어야 한다

**Given** 데이터 로딩 중일 때
**When** 현금흐름 API 응답을 기다리는 동안
**Then** FinancialChart와 동일한 높이의 Skeleton이 표시되어야 한다 (레이아웃 쉬프트 없음)

**Given** 해당 기업의 현금흐름 데이터가 DB에 존재하지 않을 때
**When** 현금흐름 탭을 클릭하면
**Then** "현금흐름 데이터를 제공하지 않는 기업입니다. P&L 또는 B/S 데이터를 이용해 주세요." 안내 메시지가 표시되어야 한다

---

## Epic 4: 공유 및 협업

Builder가 분석 세트의 공유 링크를 생성해 팀원 및 경영진이 인증 없이 읽기 전용으로 조회할 수 있다. (Phase 2)

### Story 4.1: 분석 세트 공유 링크 생성

As a Builder,
I want to generate a shareable link for an analysis set,
So that I can distribute the analysis via collaboration tools without requiring recipients to log in.

**Acceptance Criteria:**

**Given** Builder가 본인 소유 분석 세트를 보고 있는 상태에서
**When** "공유 링크 생성" 버튼을 클릭하면
**Then** `POST /api/v1/analysis-sets/{id}/share`가 호출되어 고유 `share_token`이 생성되고 DB에 저장되어야 한다

**Given** share_token이 생성되면
**When** 공유 Dialog가 열리면
**Then** `{BASE_URL}/shared/{share_token}` 형식의 URL이 표시되어야 한다
**And** Dialog는 최대 480px 너비, backdrop-blur 오버레이로 표시되어야 한다 (UX 스펙 준수)

**Given** 공유 Dialog에서 "링크 복사" 버튼을 클릭하면
**When** 클립보드 API가 호출되면
**Then** 공유 URL이 클립보드에 복사되고 "링크가 복사되었습니다" Toast가 3초 후 자동 소멸되어야 한다

**Given** 동일한 분석 세트에 이미 share_token이 존재할 때
**When** Builder가 "공유 링크 생성"을 다시 클릭하면
**Then** 기존 share_token을 재사용하여 동일한 URL이 표시되어야 한다 (중복 토큰 생성 금지)

---

### Story 4.2: 공유 링크 읽기 전용 뷰어

As a 공유 링크 수신자,
I want to view a shared analysis set without logging in,
So that I can review financial comparisons instantly without creating an account.

**Acceptance Criteria:**

**Given** 미인증 사용자가 `/shared/{share_token}` URL로 접근하면
**When** Next.js 라우트가 처리되면
**Then** 로그인 페이지로 리디렉션되지 않고 분석 세트가 읽기 전용으로 표시되어야 한다

**Given** 공유 뷰가 렌더링될 때
**When** `GET /api/v1/shared/{share_token}`이 호출되면
**Then** 해당 분석 세트의 기업 구성과 최신 재무 데이터가 로드되어 차트가 표시되어야 한다
**And** 편집·저장·삭제 버튼은 표시되지 않아야 한다

**Given** 공유 뷰에서 RLS 정책이 평가될 때
**When** anon 역할로 `analysis_sets`에 접근하면
**Then** `share_token`이 일치하는 레코드만 SELECT가 허용되어야 한다 (Epic 2의 RLS에 공유 토큰 정책 추가)

**Given** 유효하지 않거나 존재하지 않는 share_token으로 접근하면
**When** FastAPI가 요청을 처리하면
**Then** 404 응답과 함께 "유효하지 않은 공유 링크입니다." 안내 페이지가 표시되어야 한다

---

## Epic 5: 비상장사 데이터 입력

DART 미등록 비상장사의 재무 데이터를 Builder가 직접 입력하고, 상장사와 동일한 비교 차트에서 나란히 볼 수 있다. (Phase 3)

### Story 5.1: 비상장사 재무 데이터 수기 입력 및 저장

As a Builder,
I want to manually enter financial data for companies not registered in DART,
So that I can include them in analyses alongside listed companies.

**Acceptance Criteria:**

**Given** Builder가 CompanySearchInput에서 기업명을 검색했으나 DART에 등록되지 않아 결과가 없을 때
**When** "검색 결과 없음" 드롭다운이 표시되면
**Then** "DART에 등록되지 않은 기업입니다. 수기로 재무 데이터를 입력하시겠습니까?" 안내와 "수기 입력으로 추가" 버튼이 함께 표시되어야 한다

**Given** Builder가 "수기 입력으로 추가" 버튼을 클릭하면
**When** 수기 입력 폼이 열리면
**Then** 기업명, 사업연도(년도), 매출, 영업이익, 순이익 입력 필드가 표시되어야 한다
**And** 최소 1개 사업연도 데이터를 입력할 수 있으며, "연도 추가" 버튼으로 최대 5개 연도까지 행을 추가할 수 있어야 한다

**Given** Builder가 수기 입력 폼을 작성하고 제출하면
**When** `POST /api/v1/companies/manual`이 호출되면
**Then** `companies` 테이블에 `is_listed=false`로 저장되고 `financial_statements`에 입력된 연도별 데이터가 저장되어야 한다
**And** 성공 Toast "비상장사 데이터가 저장되었습니다"가 3초 후 자동 소멸되고 해당 기업이 CompanyTag로 즉시 추가되어야 한다

**Given** 필수 입력 필드가 비어있는 상태에서 Builder가 폼을 제출하면
**When** 클라이언트 유효성 검사가 실행되면
**Then** 누락된 필드에 "필수 항목입니다" 인라인 오류 메시지가 표시되어야 한다
**And** 서버 요청은 전송되지 않아야 한다

---

### Story 5.2: 비상장사 검색 조회 및 상장사 통합 비교

As a Builder,
I want to find previously entered unlisted companies via search and compare them with listed companies,
So that I can perform comprehensive competitive analysis across all company types in one view.

**Acceptance Criteria:**

**Given** Builder가 CompanySearchInput에 기업명을 입력하면
**When** 검색 결과 드롭다운이 표시되면
**Then** DART 상장사와 이전에 수기 입력한 비상장사가 함께 결과 목록에 표시되어야 한다
**And** 비상장사 항목에는 "(비상장)" 레이블이 표시되어 상장사와 구분되어야 한다

**Given** Builder가 상장사와 비상장사를 함께 선택한 상태에서
**When** 비교 차트가 렌더링되면
**Then** `GET /api/v1/companies/compare?codes=...`가 호출되고 상장사·비상장사 데이터가 동일한 FinancialChart에 나란히 표시되어야 한다
**And** 비상장사 CompanyTag에도 "(비상장)" 레이블이 표시되어야 한다

**Given** 비상장사는 DART 자동 갱신 대상이 아닐 때
**When** 분석 세트를 자동 갱신 후 불러오면
**Then** 비상장사 데이터는 수기 입력한 값 그대로 표시되어야 한다
**And** 비상장사 기업명 옆에 "●" 신규 데이터 알림 인디케이터가 표시되지 않아야 한다

**Given** Admin이 수기 입력된 비상장사 데이터를 수정하려 할 때
**When** 해당 기업의 재무 데이터 편집 UI에 접근하면
**Then** 기존 입력 데이터가 폼에 불러와져 수정하거나 연도를 추가할 수 있어야 한다

---

## Epic 6: 고급 내보내기 및 AI 인사이트

분석 결과를 PPT 형식으로 내보내고, LLM 기반 AI가 재무 데이터에 대한 자연어 요약을 생성한다. (Phase 3)

### Story 6.1: 분석 세트 PPT 내보내기

As a Builder,
I want to export an analysis set as a PowerPoint file,
So that I can use the financial comparison results directly in presentations without manual re-creation.

**Acceptance Criteria:**

**Given** Builder가 분석 세트를 조회 중인 상태에서
**When** "PPT 내보내기" 버튼을 클릭하면
**Then** `POST /api/v1/analysis-sets/{id}/export/ppt`가 호출되어 PPT 파일 생성이 시작되어야 한다
**And** 생성 중 Skeleton 또는 로딩 인디케이터가 표시되어야 한다

**Given** PPT 파일이 생성 완료되면
**When** 서버에서 파일이 반환되면
**Then** `{분석세트명}_{YYYY-MM-DD}.pptx` 형식으로 파일이 자동 다운로드되어야 한다
**And** 성공 Toast "PPT 파일이 다운로드되었습니다"가 3초 후 자동 소멸되어야 한다

**Given** PPT 파일에 포함되는 슬라이드 구성은
**When** 파일이 생성되면
**Then** 분석 세트 제목 슬라이드, 기업별 P&L 트렌드 차트, 비교 차트 슬라이드가 포함되어야 한다

**Given** PPT 생성 중 서버 오류가 발생하면
**When** API가 오류를 반환하면
**Then** Red-500 배경 Toast "내보내기에 실패했습니다. 잠시 후 재시도해 주세요"가 표시되어야 한다 (수동 닫기)

---

### Story 6.2: LLM 기반 재무 데이터 자연어 요약

As a Builder,
I want to ask natural language questions about financial data and receive AI-generated summaries,
So that I can quickly derive insights without manually analyzing raw numbers.

**Acceptance Criteria:**

**Given** Builder가 분석 세트를 조회 중인 상태에서
**When** "AI 요약" 버튼을 클릭하면
**Then** AI 인사이트 패널이 열리고 `POST /api/v1/analysis-sets/{id}/ai-summary`가 호출되어야 한다

**Given** API 요청에 현재 분석 세트의 재무 데이터가 포함되면
**When** LLM이 응답을 생성하면
**Then** 재무 트렌드 요약 (성장률, 주요 변화 등)이 자연어 텍스트로 AI 패널에 표시되어야 한다
**And** DART API Key와 동일하게 LLM API Key는 서버 환경변수에만 보관되어 클라이언트에 노출되지 않아야 한다

**Given** Builder가 AI 패널에서 자연어로 질의를 입력하면
**When** 질의가 제출되면
**Then** LLM이 해당 분석 세트의 재무 데이터를 컨텍스트로 사용해 답변을 생성하고 패널에 표시해야 한다

**Given** LLM API 호출이 실패하거나 타임아웃이 발생하면
**When** 오류가 반환되면
**Then** "AI 요약을 불러올 수 없습니다. 잠시 후 재시도해 주세요" 메시지가 표시되어야 한다
**And** 재시도 버튼이 제공되어야 한다
