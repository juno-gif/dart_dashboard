---
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish]
inputDocuments:
  - product-brief-my-bmad-project-2026-03-03.md
  - technical-dart-dashboard-research-2026-03-03.md
workflowType: 'prd'
classification:
  projectType: saas_b2b
  domain: fintech-adjacent (business intelligence, no regulation)
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - my-bmad-project

**Author:** juno
**Date:** 2026-03-03

## Executive Summary

전략기획팀 5명이 사용하는 내부 전용 기업 실적 분석 대시보드. DART OpenAPI로 상장사 재무 데이터를 자동 수집하고, 비상장사는 수기 입력으로 보완한다. 기업 검색 즉시 5년치 P&L·B/S 핵심 항목을 조회하고, 3~5개 기업을 한 화면에서 동시 비교하며, 분석 세트(기업 묶음 + 항목 설정)를 저장·재사용·분기마다 자동 최신화하는 "팀의 기업 분석 라이브러리"다. 결과물은 두레이 공유 링크 및 PPT export로 추가 가공 없이 즉시 배포 가능하다.

현재 팀 워크플로우: DART·증권사 앱·유료 서비스를 개별 방문 → 엑셀 수작업 복붙 → 차트 수동 구성 → 팀 공유 가공. 이 제품은 수집부터 공유까지 전 과정을 자동화하고, 완성된 분석을 영구 보존·재활용 가능하게 만든다.

### What Makes This Special

기존 서비스(네이버 금융, FnGuide, NICE Bizline)는 통합 비교 뷰 없음, 분석 저장·재사용 불가, 팀 협업 기능 없음, 또는 고비용 구독이라는 한계를 가진다. 이 제품의 핵심 차별점:

- **분석 세트 영속성** — 한 번 구성한 기업 묶음이 분기마다 자동 최신화. 반복 조립 불필요
- **비상장사 DB 축적** — 수기 입력 데이터가 쌓일수록 강해지는 팀 고유 자산
- **사내 업무 플로우 통합** — 두레이 공유 링크·PPT export, 추가 가공 단계 없음
- **명확한 역할 분담** — 전략기획팀(P&L + B/S 핵심 항목) / 재무팀(EBITDA·현금흐름 심화 분석 자체 툴)

핵심 통찰: 전략기획팀의 진짜 병목은 데이터를 찾는 것이 아니라 **매번 처음부터 조립하는 것**이다.

## Success Criteria

### User Success

- 기업 1개 P&L 트렌드 데이터 조회: **30초 이내** (DART API → 차트 렌더링)
- 3~5개 기업 비교 차트 즉시 생성 — 수작업 복붙 0
- 한 번 구성한 분석 세트가 다음 분기에도 클릭 한 번으로 재사용 가능
- 팀원이 서로의 분석 세트를 권한 내에서 조회·활용 가능
- 비상장사 수기 입력 데이터를 상장사와 동일한 비교 뷰에서 나란히 표시

### Business Success

- MVP 배포 후 **2주 이내** 팀원 5명 전원 사용 시작
- 기업 분석 반복 작업 시간 **70% 이상 단축** (기업 1개 분석 구성 ~30분 → ~5분 목표)
- 분기 실적 발표 시즌 분석 세트 재활용률 **> 80%**
- 인프라 비용 MVP **$0/월** 유지, 안정화 후 **$25/월** 이내

### Technical Success

- 대시보드 첫 로딩 **< 3초** (Vercel CDN 기준)
- DART 자동 업데이트 성공률 **> 95%** (APScheduler 매일 07:00)
- DART API 일일 호출 한도(20,000건) 초과 없음 (DB 캐싱 전략 유지)
- Supabase Free 500MB DB 범위 내 운영

### Measurable Outcomes

| 시점 | 지표 |
|-----|------|
| MVP 배포 후 2주 | 팀원 5명 전원 최소 1회 분석 세트 생성 |
| 3개월 | 팀원 1인당 주 1회 이상 활성 사용 |
| 6개월 | 비상장사 수기 입력 누적 20개사 이상 |
| 첫 분기 실적 발표 시즌 | 엑셀 수작업 없이 DART 자동 수집 데이터로 팀 공유 완료 |

## User Journeys

### Journey 1: Builder — 경쟁사 분석 세트 첫 생성 (Happy Path)

**페르소나:** 이지수, 전략기획팀 3년차. 매 분기 경쟁사 3개(카카오, 네이버, 크래프톤)의 P&L을 비교하는 보고서를 만든다. 현재는 각 기업 DART 페이지를 개별 방문해 수치를 엑셀에 옮기는 데만 2시간이 걸린다.

**Opening Scene:** 분기 실적 발표 다음 날 아침. 팀장이 "오늘 오후까지 3사 비교 보고서 부탁해"라고 메시지를 보낸다. 지수는 대시보드를 연다.

**Rising Action:**
1. 검색창에 "카카오" 입력 → corp_code 자동 매핑, 5년치 P&L 차트 즉시 렌더링
2. "+ 기업 추가" → 네이버, 크래프톤 순서대로 추가
3. 비교 차트 뷰에서 3개 기업 영업이익률 트렌드를 한 화면으로 확인
4. "분석 세트로 저장" → "경쟁사 3사 P&L" 이름으로 저장

**Climax:** 전체 작업 시간 8분. 이전엔 2시간이었다.

**Resolution:** 저장된 분석 세트가 다음 분기에도 살아있다. 다음 실적 발표 때는 클릭 한 번으로 최신 데이터가 로드된다.

**요구 기능:** 기업 검색, DART 자동 수집, 다중 기업 비교 차트, 분석 세트 저장

---

### Journey 2: Builder — DART 미등록 비상장 스타트업 추가 (Edge Case)

**페르소나:** 박민준, 전략기획팀 2년차. 투자 검토 중인 비상장 스타트업 A사의 재무 데이터를 분석 세트에 넣고 싶다.

**Opening Scene:** A사는 DART 제출 대상이 아니라 API 조회가 불가능하다. 기존엔 수동 수집 데이터를 별도 엑셀에 관리했다.

**Rising Action:**
1. 기업 검색 → "검색 결과 없음 — 수기 입력으로 추가" 안내
2. 기업명, 사업연도, 매출·영업이익·순이익 직접 입력
3. 상장사와 동일한 비교 뷰에 자동 합류

**Climax:** 비상장사가 상장사와 나란히 같은 차트에 표시된다. 데이터는 팀 DB에 축적되어 다음번엔 검색으로 바로 나온다.

**Resolution:** 팀만 보유한 비상장사 DB가 분기마다 쌓인다. 1년 후엔 20개 비상장사 데이터가 즉시 조회 가능해진다.

**요구 기능:** 수기 입력 UI, 비상장사 DB 저장·재활용, 상장/비상장 통합 비교 뷰

---

### Journey 3: Admin — 새 팀원 초대 및 권한 부여

**페르소나:** 김영호, 전략기획팀장. 신입 팀원이 합류했다. 기존 분석 세트는 조회만, 새 분석 세트는 본인이 직접 만들 수 있도록 설정하고 싶다.

**Opening Scene:** 신입 팀원의 이메일 주소를 갖고 있다. 대시보드 설정 페이지를 연다.

**Rising Action:**
1. "팀원 초대" → 이메일 입력, 역할 선택 (Builder)
2. 초대 이메일 발송 → 팀원 가입 후 즉시 접근 가능

**Climax:** 팀원이 기존 분석 세트를 조회하고 새 세트를 직접 만들기 시작한다.

**Resolution:** 팀장은 Builder 팀원들의 분석 세트를 모두 볼 수 있다. Live Viewer로 초대된 실장은 조회만 가능하다.

**요구 기능:** 이메일 초대, 역할별 접근 제어(Admin/Builder/LiveViewer/ReadOnly), Supabase RLS

---

### Journey 4: Live Viewer — 경영진에게 분석 결과 공유

**페르소나:** 최부장, 전략기획팀 실장. 직접 데이터를 만들지 않고 팀원들이 작성한 분석 세트를 보고받는다.

**Opening Scene:** 팀원 지수가 "경쟁사 3사 P&L" 분석 세트의 공유 링크를 두레이 채널에 올렸다.

**Rising Action:**
1. 링크 클릭 → Live Viewer 계정으로 바로 대시보드 뷰 접근
2. 최신 분기 데이터가 자동 반영된 차트 확인
3. 차트 이미지 다운로드 → PPT에 붙여넣기

**Climax:** 보고 자료 준비 시간이 사라진다. 링크 하나로 항상 최신 데이터를 볼 수 있다.

**Resolution:** 두레이 채널에 고정된 링크가 다음 분기에도 살아있다.

**요구 기능:** 공유 링크(두레이 연동), 읽기 전용 뷰, 차트 이미지 다운로드

---

### Journey Requirements Summary

| 저니 | 핵심 요구 기능 |
|-----|-------------|
| Builder — Happy Path | 기업 검색, DART 자동 수집, 다중 비교 차트, 분석 세트 저장 |
| Builder — Edge Case | 수기 입력, 비상장사 DB 축적, 상장/비상장 통합 비교 뷰 |
| Admin | 이메일 초대, 역할별 권한(RLS), 팀 관리 |
| Live Viewer | 공유 링크, 읽기 전용 뷰, 이미지 다운로드 |

## Domain-Specific Requirements

### Compliance & Regulatory

- **DART OpenAPI 이용약관 준수**
  - 일일 호출 한도 20,000건 미초과 (DB 캐싱으로 관리)
  - 수집 데이터 내부 분석 전용 사용 — 외부 재배포·상업적 판매 금지
  - DART API Key 1인 발급, 서버 환경변수에만 보관 (프론트 노출 금지)
- **데이터 성격:** DART 공시 데이터는 공개 정보 — 개인정보보호법(PIPA) 적용 대상 아님. 단, 사용자 계정 정보(이메일)는 Supabase Auth 내에서 관리

### Technical Constraints

- **보안**
  - DART API Key: `.env` → Render 환경변수 (프론트엔드 절대 미노출)
  - Supabase RLS: 역할별 행 단위 접근 제어 (Admin/Builder/LiveViewer/ReadOnly)
  - HTTPS 전구간 적용 (Vercel + Render 기본 제공)
  - Supabase Service Key: FastAPI 백엔드에서만 사용
- **데이터 무결성**
  - DART `account_nm` 비표준화 → `account_mappings` 테이블로 표준화 키 매핑
  - 미매핑 계정과목: 원본명 그대로 표시 + Admin 알림
  - 금액 단위: `BIGINT` (원 단위) → 프론트에서 억/조 변환 처리
- **외부 API 의존성 관리**
  - DART API 장애 시: DB 캐시 데이터 제공 + 장애 배너 표시
  - API 스펙 변경 시: `dart_client.py` 격리 모듈만 수정 (영향 최소화)
  - API 한도 초과 시: 이미 수집된 DB 데이터 제공, 다음 날 갱신

### Integration Requirements

- **DART OpenAPI** (핵심): `fnlttSinglAcntAll.json` 전체 재무제표, `fnlttMultiAcnt.json` 다중회사 일괄 조회
- **Supabase Auth**: 이메일 로그인, JWT 역할 클레임, RLS 정책 연동
- **APScheduler → Render**: 매일 07:00 DART 동기화. Render 슬립 방지: Supabase pg_cron 06:58 ping
- **Vercel ↔ Render**: CORS 허용 도메인 설정 (`CORSMiddleware`), JWT 검증

### Risk Mitigations

| 리스크 | 완화 방안 |
|--------|---------|
| DART API 스펙 변경 | `dart_client.py` 격리, 공시 모니터링 |
| 계정과목 비표준화 | `account_mappings` 선제 구축 |
| Render Free 슬립 | pg_cron 06:58 ping + 매일 사용 패턴 |
| API Key 노출 | 환경변수 엄수, 프론트 미전달 규칙 |
| 비상장사 데이터 공백 | Phase 3 수기 입력으로 처리 (계획됨) |

## SaaS B2B Specific Requirements

### Project-Type Overview

단일 조직(팀) 전용 내부 대시보드. 외부 고객에게 판매하는 SaaS가 아닌 팀 내부 툴이므로 멀티테넌트·구독 과금 구조는 해당 없음. 단일 테넌트 + 역할 기반 접근 제어(RBAC)가 핵심 구조.

### Tenant Model

- **싱글 테넌트** — 조직 1개(전략기획팀), 테넌트 격리 불필요
- 단일 Supabase 프로젝트 내 모든 데이터 관리
- Admin이 팀원을 직접 초대·관리 (셀프서비스 가입 없음)

### RBAC Matrix

| 역할 | 분석 세트 생성 | 분석 세트 수정 | 분석 세트 조회 | 기업 등록 | 팀원 초대 |
|------|-------------|-------------|-------------|---------|---------|
| **Admin** | ✅ | ✅ 전체 | ✅ 전체 | ✅ | ✅ |
| **Builder** | ✅ | ✅ 본인 생성분 | ✅ 전체 | ✅ | ❌ |
| **Live Viewer** | ❌ | ❌ | ✅ 전체 | ❌ | ❌ |
| **Read-only** | ❌ | ❌ | ✅ 본인에게 공유된 것 | ❌ | ❌ |

Supabase RLS 정책으로 DB 행 단위 권한 제어. JWT 클레임에 `role` 포함.

### Subscription Tiers

해당 없음 — 내부 툴, 과금 구조 없음. 인프라 비용만 관리 ($0 → $5 → $25 단계적).

### Integration List

| 통합 대상 | 유형 | 우선순위 |
|---------|------|--------|
| DART OpenAPI (opendart.fss.or.kr) | 외부 데이터 API | MVP 필수 |
| Supabase (PostgreSQL + Auth + RLS) | DB + 인증 | MVP 필수 |
| Render (FastAPI 백엔드 호스팅) | 배포 인프라 | MVP 필수 |
| Vercel (Next.js 프론트엔드 호스팅) | 배포 인프라 | MVP 필수 |
| 두레이 (링크 공유) | 협업 툴 연동 | Growth |
| PPT Export | 문서 생성 | Vision |

### Technical Architecture Considerations

- **백엔드:** FastAPI (Python) — 모듈형 모놀리스, 레이어드 아키텍처
- **프론트엔드:** Next.js 14 App Router — Server Components, Server Actions
- **인증 흐름:** Supabase Auth → JWT → FastAPI 미들웨어 검증 → RLS 적용
- **데이터 흐름:** DART API → OpenDartReader → PostgreSQL 캐시 → FastAPI → Next.js → Recharts

### Implementation Considerations

- AI-First 개발 (Cursor + Claude Code) — 비코더 1인 구축
- 각 Phase 완료 후 배포·검증 후 다음 Phase 진행
- `.env` 파일 관리 철저, Vercel/Render 자동 배포 (GitHub push 트리거)

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP 접근법:** Problem-Solving MVP — "이것만 동작하면 팀이 당장 쓸 수 있다"

MVP 검증 기준: "기존에 2시간 걸리던 경쟁사 3사 P&L 비교가 10분 안에 완료되는가?"

**리소스:** 비코더 1인 + AI (Cursor + Claude Code). MVP는 외부 배포·인증·권한 없이도 팀 내부에서 검증 가능.

### MVP Feature Set (Phase 1)

**지원하는 핵심 저니:** Builder — 경쟁사 분석 세트 첫 생성 (Happy Path)

**Must-Have 기능:**

| 기능 | 근거 |
|-----|-----|
| DART API 연동 + OpenDartReader | 없으면 제품 존재 불가 |
| 기업 검색 (종목명/코드) | 첫 번째 사용자 액션 |
| P&L 5년치 트렌드 차트 (Recharts) | 핵심 가치 전달 |
| 3~5개 기업 비교 차트 | 핵심 차별점 |
| 차트 이미지 다운로드 | 즉각적인 업무 활용 |
| Vercel + Render Free 배포 ($0) | 팀 접근 가능 상태 |

**MVP에서 의도적으로 제외:**
- 로그인/인증 (초기 팀 내부 URL 공유로 대체)
- 분석 세트 저장 (URL 북마크로 임시 대체)
- B/S 차트 (P&L 검증 후 추가)
- 자동 업데이트 (수동 새로고침으로 시작)

### Post-MVP Features

**Phase 2 (Growth) — 팀 운영 수준:**
1. Supabase Auth + RLS — Admin/Builder/LiveViewer/ReadOnly 권한
2. 분석 세트 저장·조회 (기업 묶음 영속성 핵심 기능)
3. B/S 차트 (자산·부채·자본·현금성 자산)
4. APScheduler 매일 07:00 자동 업데이트 + 빨간 점(●) 알림
5. 두레이 공유 링크

**Phase 3 (Vision) — 완성도:**
1. 비상장사 수기 입력
2. PPT Export
3. LLM 재무 데이터 AI 요약

### Risk Mitigation Strategy

**기술 리스크:** DART API 의존성 → `dart_client.py` 격리 모듈. MVP에서 수동 테스트로 먼저 검증 후 자동화

**시장 리스크:** 팀이 실제로 안 쓸 수 있음 → MVP를 인증 없이 최대한 빠르게 배포, 팀원 1인에게 먼저 테스트

**리소스 리스크:** 비코더 개발 지연 → Phase 1만 목표, 각 기능 단위로 AI와 구현·테스트·배포 반복. Phase 2는 Phase 1 실사용 후 결정

## Functional Requirements

> 이 섹션은 제품이 갖춰야 할 **기능 역량 계약서(Capability Contract)**다.
> UX 디자이너·아키텍트·PM은 이 목록의 기능만을 설계·구현한다.
> (Phase 1=MVP, Phase 2=Growth, Phase 3=Vision)

### 1. 기업 데이터 수집 (Company Data Acquisition)

- **FR1:** 시스템은 DART OpenAPI를 통해 상장사의 P&L·B/S 재무 데이터를 자동 수집할 수 있다 _(Phase 1)_
- **FR2:** 시스템은 수집된 DART 데이터를 내부 DB에 캐싱하여 반복 API 호출을 최소화할 수 있다 _(Phase 1)_
- **FR3:** 시스템은 매일 정해진 시각에 DART 최신 데이터를 자동으로 갱신할 수 있다 _(Phase 2)_
- **FR4:** Builder는 DART 미등록 비상장사의 재무 데이터(기업명·사업연도·매출·영업이익·순이익)를 수기로 입력할 수 있다 _(Phase 3)_
- **FR5:** 시스템은 수기 입력된 비상장사 데이터를 팀 DB에 저장하여 이후 재사용할 수 있다 _(Phase 3)_

### 2. 기업 검색 및 조회 (Company Search & Discovery)

- **FR6:** Builder는 한국어 기업명 또는 종목코드로 상장사를 검색할 수 있다 _(Phase 1)_
- **FR7:** 시스템은 검색어 입력 시 corp_code를 자동 매핑하여 DART 데이터를 즉시 로드할 수 있다 _(Phase 1)_
- **FR8:** Builder는 검색 즉시 해당 기업의 최근 5년치 P&L 데이터를 조회할 수 있다 _(Phase 1)_
- **FR9:** 시스템은 DART에 존재하지 않는 기업 검색 시 "수기 입력으로 추가" 안내를 표시할 수 있다 _(Phase 3)_
- **FR10:** Builder는 이전에 입력된 비상장사 데이터를 검색으로 조회할 수 있다 _(Phase 3)_

### 3. 재무 데이터 시각화 (Financial Data Visualization)

- **FR11:** Builder는 단일 기업의 5년치 P&L 핵심 항목(매출·영업이익·순이익) 트렌드를 차트로 볼 수 있다 _(Phase 1)_
- **FR12:** Builder는 3~5개 기업의 P&L 트렌드를 한 화면에서 동시에 비교할 수 있다 _(Phase 1)_
- **FR13:** Builder는 B/S 핵심 항목(자산·부채·자본·현금성 자산)을 차트로 볼 수 있다 _(Phase 2)_
- **FR14:** Builder는 상장사와 비상장사 데이터를 동일한 비교 차트 뷰에서 나란히 볼 수 있다 _(Phase 3)_
- **FR15:** 시스템은 자동 업데이트로 새 분기 데이터가 추가됐을 때 시각적 알림 표시(●)를 제공할 수 있다 _(Phase 2)_
- **FR36:** Builder는 현금흐름 핵심 항목(영업활동·투자활동·재무활동 현금흐름)을 차트로 볼 수 있다 _(Phase 2)_

### 4. 분석 세트 관리 (Analysis Set Management)

- **FR16:** Builder는 복수의 기업과 항목 설정을 이름 붙인 분석 세트로 저장할 수 있다 _(Phase 2)_
- **FR17:** Builder는 저장된 분석 세트를 조회하고 최신 데이터로 즉시 불러올 수 있다 _(Phase 2)_
- **FR18:** Builder는 자신이 생성한 분석 세트를 수정(기업 추가·삭제, 이름 변경)할 수 있다 _(Phase 2)_
- **FR19:** Admin은 모든 팀원의 분석 세트를 조회하고 수정할 수 있다 _(Phase 2)_
- **FR20:** Live Viewer는 공유된 분석 세트를 읽기 전용으로 조회할 수 있다 _(Phase 2)_
- **FR21:** 시스템은 자동 업데이트 후 분석 세트의 데이터를 최신 분기 기준으로 유지할 수 있다 _(Phase 2)_

### 5. 사용자 관리 및 접근 제어 (User Management & Access Control)

- **FR22:** Admin은 이메일로 팀원을 초대하며 역할(Builder/LiveViewer/ReadOnly)을 지정할 수 있다 _(Phase 2)_
- **FR23:** Admin은 기존 팀원의 역할을 변경하거나 계정을 비활성화할 수 있다 _(Phase 2)_
- **FR24:** 사용자는 이메일로 로그인하고 역할 정보가 포함된 JWT 토큰을 발급받을 수 있다 _(Phase 2)_
- **FR25:** 시스템은 역할(Admin/Builder/LiveViewer/ReadOnly)에 따라 DB 행 단위 접근을 제어할 수 있다 _(Phase 2)_
- **FR26:** Builder는 자신이 생성한 분석 세트만 수정할 수 있고 타인의 세트는 조회만 가능하다 _(Phase 2)_

### 6. 공유 및 내보내기 (Sharing & Export)

- **FR27:** 사용자는 현재 차트 화면을 이미지 파일로 다운로드할 수 있다 _(Phase 1)_
- **FR28:** Builder는 특정 분석 세트의 공유 링크를 생성하여 협업 도구(두레이 등)에서 배포할 수 있다 _(Phase 2)_
- **FR29:** 공유 링크를 통해 접근한 사용자는 분석 세트를 읽기 전용으로 볼 수 있다 _(Phase 2)_
- **FR30:** Builder는 분석 세트 결과를 PPT 형식으로 내보낼 수 있다 _(Phase 3)_
- **FR31:** LLM 기반 AI는 재무 데이터에 대한 자연어 질의에 응답하고 요약을 생성할 수 있다 _(Phase 3)_

### 7. 시스템 및 데이터 무결성 (System & Data Integrity)

- **FR32:** 시스템은 DART API 장애 시 DB 캐시 데이터를 제공하고 장애 상태 배너를 표시할 수 있다 _(Phase 1)_
- **FR33:** Admin은 DART의 비표준 계정과목명을 표준화 키와 매핑하는 테이블을 관리할 수 있다 _(Phase 1)_
- **FR34:** 시스템은 매핑되지 않은 계정과목명을 원본 그대로 표시하고 Admin에게 알림을 제공할 수 있다 _(Phase 1)_
- **FR35:** 시스템은 DART API 일일 호출 한도(20,000건)를 초과하지 않도록 DB 캐싱 우선 정책을 적용할 수 있다 _(Phase 1)_

## Non-Functional Requirements

### Performance

- **NFR-P1:** 대시보드 초기 로딩(Vercel CDN 기준) 3초 이내
- **NFR-P2:** 기업 1개 P&L 조회 — DB 캐시 히트 시 1초 이내, DART API 신규 호출 시 30초 이내
- **NFR-P3:** 3~5개 기업 비교 차트 전환 5초 이내
- **NFR-P4:** DART 일일 자동 업데이트 작업 완료 시간 30분 이내

### Security

- **NFR-S1:** DART API Key는 서버 환경변수에만 보관, 클라이언트(프론트엔드)에 절대 노출 불가
- **NFR-S2:** Supabase Service Role Key는 FastAPI 서버에서만 사용, 프론트엔드 직접 접근 차단
- **NFR-S3:** 모든 클라이언트-서버 통신은 HTTPS 필수 적용
- **NFR-S4:** JWT 토큰에 사용자 역할(role) 클레임 포함, FastAPI 미들웨어에서 매 요청 검증
- **NFR-S5:** Supabase RLS 정책으로 DB 행 단위 접근 제어 — 역할 없이 직접 DB 쿼리 시 데이터 반환 불가

### Reliability

- **NFR-R1:** DART 자동 업데이트(APScheduler 매일 07:00) 성공률 95% 이상
- **NFR-R2:** DART API 장애 시 DB 캐시 데이터 즉시 제공, 사용자에게 캐시 기준 날짜 표시
- **NFR-R3:** Render Free 인스턴스 슬립 방지를 위한 pg_cron 06:58 ping 메커니즘 유지
- **NFR-R4:** 업무 시간(평일 09:00~18:00 KST) 중 서비스 가용성 99% 이상 유지

### Integration

- **NFR-I1:** DART OpenAPI 일일 호출 건수 20,000건 미초과 (DB 캐싱 우선 정책으로 관리)
- **NFR-I2:** Supabase Free Tier DB 사용량 500MB 미만 유지
- **NFR-I3:** FastAPI CORS 허용 도메인을 Vercel 배포 도메인으로만 제한
- **NFR-I4:** DART API 스펙 변경 시 `dart_client.py` 단일 모듈만 수정하여 영향 범위 격리 가능

### Maintainability

- **NFR-M1:** 비코더 1인이 AI 개발 도구로 독립적으로 유지보수 가능한 코드 구조 유지 (모듈형 모놀리스 + 레이어드 아키텍처)
- **NFR-M2:** GitHub main 브랜치 push 시 Vercel + Render 자동 배포 적용
- **NFR-M3:** 개발/프로덕션 환경변수 분리 (.env.local / Vercel·Render 환경변수)
- **NFR-M4:** `account_mappings` 테이블을 통해 DART 계정과목 변경 시 코드 수정 없이 Admin이 직접 대응 가능
