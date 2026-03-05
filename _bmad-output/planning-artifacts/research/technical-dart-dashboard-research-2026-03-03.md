---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'DART 기반 기업 실적 분석 대시보드 기술 스택'
research_goals: '1) DART OpenAPI 데이터 범위 파악, 2) 비코더 친화적 기술 스택 선택, 3) 금융 데이터 시각화 라이브러리 비교'
user_name: 'juno'
date: '2026-03-03'
web_research_enabled: true
source_verification: true
---

# Research Report: Technical

**Date:** 2026-03-03
**Author:** juno
**Research Type:** technical

---

## Research Overview

이 기술 리서치는 DART(Data Analysis, Retrieval and Transfer) 기반 기업 실적 분석 대시보드 구축을 위한 최적 기술 스택을 탐색한 종합 기술 리포트다. 금융감독원 전자공시 API(DART OpenAPI)를 활용해 상장사 및 주요 비상장사의 재무제표 데이터를 자동 수집·시각화하는 내부 팀 대시보드를 목표로, 세 가지 핵심 리서치 목표 — ① DART OpenAPI 데이터 범위와 API 스펙 파악, ② 코딩 경험이 없는 비개발자도 AI 도구(Cursor + Claude Code)로 구축·운영 가능한 기술 스택 선택, ③ 금융 데이터 시각화에 최적화된 React 차트 라이브러리 비교 — 를 중심으로 진행되었다.

리서치는 5단계 체계적 방법론으로 수행되었다: 기술 스택 분석(Step 2), 통합 패턴 분석(Step 3), 아키텍처 패턴 분석(Step 4), 구현 전략 분석(Step 5). 각 단계에서 DART OpenAPI 공식 문서, FastAPI/Next.js 공식 문서, OpenDartReader GitHub, 기술 블로그, AI 코딩 도구 비교 리뷰 등 다수의 현행 소스를 기반으로 실제 구현 가능성을 교차 검증하였다. 비코더 AI 개발 방법론과 무료 인프라 옵션(Render Free + Vercel Hobby + Supabase Free = $0/월)을 포함하는 실용적 관점에서 작성되었다.

핵심 발견사항 요약: DART OpenAPI는 2015년 이후 5종 재무제표(IS·BS·CF·CIS·SCE) 전체를 무료로 제공하며, OpenDartReader Python 라이브러리로 쉽게 연동 가능하다. Next.js 14 + FastAPI + Supabase 스택은 AI 코딩 환경에 최적화되어 있으며 팀 5명 규모 내부 툴에 충분하다. Recharts는 React 통합성과 AI 코드 생성 품질이 가장 높아 차트 라이브러리 1순위로 선정되었다. 전체 종합 분석은 아래 Technical Research Synthesis 섹션을 참조.

---

## Technical Research Scope Confirmation

**Research Topic:** DART 기반 기업 실적 분석 대시보드 기술 스택
**Research Goals:** 1) DART OpenAPI 데이터 범위 파악, 2) 비코더 친화적 기술 스택 선택, 3) 금융 데이터 시각화 라이브러리 비교

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-03-03

---

## Technology Stack Analysis

### DART OpenAPI 데이터 범위 및 API 엔드포인트

DART(Data Analysis, Retrieval and Transfer) OpenAPI는 금융감독원이 운영하는 전자공시 시스템의 공개 API 서비스다. 2020년 1월 21일 공식 서비스를 시작하였으며, 상장법인(유가증권시장, 코스닥) 및 주요 비상장법인(사업보고서 제출 대상 & IFRS 적용 기업)의 정기보고서 데이터를 API로 제공한다.

**핵심 재무제표 API 엔드포인트:**

| API 명 | 엔드포인트 | 설명 |
|--------|-----------|------|
| 단일회사 주요계정 | `fnlttSinglAcnt.json` | 매출액·영업이익·당기순이익 등 주요 재무지표 |
| 단일회사 전체 재무제표 | `fnlttSinglAcntAll.json` | XBRL 재무제표 전 계정과목 (상세 비용 항목 포함) |
| 다중회사 주요계정 | `fnlttMultiAcnt.json` | 복수 기업 주요계정 일괄 조회 |
| 공시검색 | `list.json` | 기업별 공시 목록 조회 |
| 기업개황 | `company.json` | 기업 기본 정보 조회 |

**주요 요청 파라미터:**
- `crtfc_key`: DART 발급 인증키 (회원가입 후 무료 발급)
- `corp_code`: 기업 고유번호 8자리 (DART 내부 코드, 종목코드와 다름)
- `bsns_year`: 사업연도 4자리 (2015년 이후 데이터 제공)
- `reprt_code`: 보고서 구분 (11011=사업보고서, 11012=반기, 11013=1분기, 11014=3분기)
- `fs_div`: 재무제표 구분 (CFS=연결재무제표, OFS=별도재무제표)

**제공 재무제표 종류:**
- IS (Income Statement) - 손익계산서: 매출액, 영업이익, 당기순이익
- CIS (Comprehensive Income Statement) - 포괄손익계산서
- BS (Balance Sheet) - 재무상태표: 자산총계, 부채총계, 자본총계
- CF (Cash Flow) - 현금흐름표
- SCE (Statement of Changes in Equity) - 자본변동표

**주의사항 및 제약:**
- 비상장법인 중 사업보고서 미제출 기업은 데이터 없음 → 수기 입력 필요
- 금융업 제외 상장법인이 주요 데이터 대상
- 일부 기업은 계정과목 명칭이 표준화되지 않아 전처리 필요
- API 호출 한도: 무료 키 기준 하루 20,000건

_Source: [DART OpenAPI 공식 가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019016), [OpenDartReader GitHub](https://github.com/FinanceData/OpenDartReader)_

---

### Programming Languages

**Python (추천 - 백엔드 및 데이터 처리)**

Python은 DART API 연동 및 금융 데이터 처리에 사실상 표준으로 자리잡고 있다. 생태계 내 주요 라이브러리가 모두 Python으로 작성되어 있으며, AI 코딩 도구와의 궁합도 가장 뛰어나다.

- **OpenDartReader**: DART API 래퍼 라이브러리. 기업명/종목코드로 직접 재무제표 조회 가능. `finstate()`, `finstate_all()` 메서드로 P&L, B/S 데이터 DataFrame 반환
- **pandas**: 재무 데이터 처리 및 변환 표준 라이브러리
- **비코더 친화도**: AI(Claude, GPT)가 Python 코드 생성 품질이 가장 높음. 에러 메시지도 해석 쉬움

**TypeScript/JavaScript (프론트엔드)**

React/Next.js 프론트엔드 구성 시 TypeScript 사용이 2025년 표준이다. 타입 안전성으로 AI가 생성한 코드의 오류를 빠르게 잡을 수 있다.

_Source: [OpenDartReader Docs](https://github.com/FinanceData/OpenDartReader), [Next.js FastAPI Template](https://nextfastapi.com/)_

---

### Development Frameworks and Libraries

**Option A: Next.js + FastAPI (추천 풀스택)**

2025년 내부 대시보드 툴의 주류 스택. 프론트엔드(Next.js)와 백엔드(FastAPI)를 분리하여 각 영역을 최적화한다.

| 구성요소 | 역할 |
|---------|------|
| **Next.js 14+** | React 기반 프론트엔드. 서버사이드 렌더링, 파일 기반 라우팅 |
| **FastAPI (Python)** | 비동기 API 서버. DART API 호출, 데이터 처리, 스케줄링 |
| **Tailwind CSS** | 유틸리티 CSS 프레임워크. AI 코드 생성 품질 높음 |
| **shadcn/ui** | Tailwind 기반 React 컴포넌트 라이브러리. 대시보드 UI 빠르게 구성 |
| **Pydantic** | FastAPI 데이터 검증. 재무 데이터 스키마 정의 |

**Option B: Streamlit (빠른 프로토타입 / 단순 내부 툴)**

코딩 경험이 거의 없는 경우 가장 진입장벽이 낮은 옵션. Python 파일 하나로 웹 앱을 구동할 수 있다.

- 장점: 코드 최소화, 즉시 실행, 재무 데이터 시각화 예제 풍부
- 단점: UI 커스터마이징 제한적, 복잡한 권한 구조 구현 어려움, 팀 공유/인증 기능 추가 시 복잡도 증가
- 결론: **MVP 초기 검증(PoC)에는 적합하나, 팀 단위 내부 툴 운영에는 Next.js+FastAPI 권장**

_Source: [Streamlit Official](https://streamlit.io/), [Next.js FastAPI Template](https://www.vintasoftware.com/blog/next-js-fastapi-template), [Realtime Dashboard 튜토리얼](https://jaehyeon.me/blog/2025-03-04-realtime-dashboard-3/)_

---

### Database and Storage Technologies

**PostgreSQL (추천)**

- 관계형 DB 중 오픈소스 표준. 재무 데이터(회사별·연도별 시계열)에 최적
- 분석 세트(기업 묶음 + 항목 설정), 사용자 권한, 캐싱된 DART 데이터 모두 단일 DB에서 관리 가능
- Supabase(PostgreSQL 호스팅 서비스)를 활용하면 Auth, Real-time, REST API를 무료로 즉시 사용 가능

**SQLite (로컬 개발/소규모)**

- 파일 기반 DB. 설치 불필요, 초기 개발 단계에서 빠르게 시작 가능
- 팀 공유 서버 운영 시에는 PostgreSQL로 마이그레이션 필요

**Redis (옵션 - 캐싱)**

- DART API 응답 캐싱으로 호출 한도 절약 및 응답 속도 개선
- 초기 MVP에서는 생략 가능. 사용량 증가 시 추가

_Source: [Next.js FastAPI 스택 가이드](https://www.augustinfotech.com/blogs/building-an-interactive-dashboard-with-next-js-and-python/)_

---

### Development Tools and Platforms (비코더 AI 코딩 환경)

코딩 경험 0인 비개발자가 Claude/AI의 도움으로 개발하는 2025년 접근법:

**Cursor (강력 추천)**

- VS Code 기반 AI 코드 에디터. 프로젝트 전체 컨텍스트를 파악한 상태로 코드 생성
- "DART API로 매출 데이터를 가져오는 엔드포인트를 FastAPI로 만들어줘"와 같은 자연어 명령으로 코드 생성
- 여러 파일을 동시에 수정하는 복잡한 작업도 처리 가능
- 비코더에게 가장 실용적인 도구로 2025년 평가 (→ Cursor + Claude 조합)

**Claude Code (본 프로젝트 도구)**

- 코드 이해, 리팩토링, 문서화에 강점
- 긴 컨텍스트 윈도우로 프로젝트 전체 구조 파악
- 자율 실행 가능 (~30시간 지속 작업)

**Replit Agent (빠른 프로토타이핑)**

- 아이디어를 설명하면 전체 앱을 자동으로 생성·테스트·디버깅
- 코딩 경험 없는 비개발자에게 진입장벽 최소화
- 단, 복잡한 커스텀 비즈니스 로직에서는 Cursor 대비 제한적

**추천 조합:** Cursor + Claude Code → 실질적인 개발 도구로 가장 적합

_Source: [AI Coding Tools 2025 비교](https://technologyrivers.com/blog/cursor-vs-replit-vs-claude-code-which-ai-coding-tool-should-you-choose-in-2026/), [Ironhack 개발자 AI 툴킷](https://www.ironhack.com/us/blog/the-web-developer-s-ai-toolkit-in-2025-cursor-claude-replit)_

---

### Cloud Infrastructure and Deployment

**Vercel (프론트엔드 배포 - 추천)**

- Next.js와 공식 통합. GitHub 연동 시 push만으로 자동 배포
- 무료 티어로 내부 팀 규모에서 충분히 운영 가능
- HTTPS 자동, CDN 글로벌 포함

**Railway / Render (백엔드 FastAPI 배포 - 추천)**

- Python FastAPI 서버를 코드 없이 배포 가능한 PaaS
- PostgreSQL 호스팅도 함께 제공
- 월 $5~20 수준으로 소규모 내부 팀 운영 적합

**Supabase (DB + Auth 통합 - 추천)**

- PostgreSQL 기반 BaaS(Backend as a Service)
- 인증(이메일/소셜 로그인), 실시간 구독, Row Level Security(RLS) 권한 제어 내장
- 분석 세트 공유·권한(빌더/Admin/뷰어) 구현에 적합

_Source: [Next.js Vercel 배포 가이드](https://www.vintasoftware.com/blog/next-js-fastapi-template)_

---

### Financial Data Visualization Chart Libraries 비교

재무 대시보드를 위한 차트 라이브러리 심층 비교 (React 기준):

| 라이브러리 | 주간 다운로드 | 렌더링 | 난이도 | 금융 대시보드 적합성 |
|-----------|------------|--------|--------|------------------|
| **Recharts** | 100만+ | SVG | ⭐ 쉬움 | ✅ 매우 적합 |
| **ApexCharts** | 급성장 중 | SVG | ⭐ 쉬움 | ✅ 적합 |
| **Chart.js** | 최다 | Canvas | ⭐ 쉬움 | ✅ 적합 |
| **Apache ECharts** | 기업용 | Canvas+WebGL | ⭐⭐ 중간 | △ 복잡한 기능에 유리 |
| **D3.js** | 커스텀 극강 | SVG | ⭐⭐⭐ 어려움 | △ 비코더에 비적합 |

**Recharts (최우선 추천)**

- React 생태계와 완벽 통합. JSX 문법으로 AI가 코드 생성 시 오류 최소화
- 약 10년 된 안정적 라이브러리. 방대한 예제와 커뮤니티
- 연도별 트렌드(꺾은선), 항목별 비교(막대), 비율(파이/도넛) 모두 지원
- **비코더 AI 코딩 프로젝트에 가장 검증된 선택**

**ApexCharts (차순위 추천)**

- 인터랙티브 기능(줌, 팬, 스크롤) 기본 내장
- 모든 차트 반응형 기본 지원
- 데이터 포인트 수천 건 수준이면 성능 이슈 없음 (금융 실적 데이터는 연도별이므로 데이터 포인트 수 적음 → 문제없음)

**Apache ECharts (참고)**

- 수만 건 이상 대규모 데이터 처리에 강점 (금융 실적 집계 데이터에는 과스펙)
- 커스터마이징 자유도 높지만 학습 곡선 존재
- 한국어 레이블, 원화(₩) 단위 포맷 커스터마이징 용이

**결론: Recharts를 기본으로 선택, 추가 인터랙티브 기능 필요 시 ApexCharts로 전환 검토**

_Source: [Best React Chart Libraries 2025 - LogRocket](https://blog.logrocket.com/best-react-chart-libraries-2025/), [8 Best React Chart Libraries - Embeddable](https://embeddable.com/blog/react-chart-libraries), [ECharts vs Recharts - StackShare](https://stackshare.io/stackups/echarts-vs-recharts)_

---

### Technology Adoption Trends

**2025년 비코더 개발 트렌드:**

1. **AI-First 개발 접근법 주류화**: 코딩 경험 없이 Cursor+Claude 조합으로 풀스택 앱 구현이 현실화됨. "No-Code"에서 "AI-Assisted Code"로 패러다임 이동
2. **Python 백엔드 + Next.js 프론트엔드**: 내부 대시보드 툴의 2025년 표준 스택. FastAPI의 Python 친화성과 Next.js의 UI 생산성이 시너지
3. **BaaS 활용 급증**: Supabase, Firebase 등 DB+Auth+API를 패키지로 제공하는 서비스로 백엔드 구성 시간 단축
4. **차트 라이브러리 성숙**: Recharts, ApexCharts가 금융 대시보드 표준으로 자리잡음. D3.js 직접 사용은 감소 추세

_Source: [Dashboard Builder Guide 2026 - WeWeb](https://www.weweb.io/blog/dashboard-builder-guide-no-code-ai-best-practices), [10 Best Low-Code Platforms 2025](https://www.dipolediamond.com/10-best-low-code-platforms-for-financial-services-in-2025/)_

## Integration Patterns Analysis

### API Design Patterns (DART 대시보드 맥락)

**핵심 통합 구조: DART API → FastAPI 백엔드 → Next.js 프론트엔드**

이 대시보드의 통합 구조는 외부 API(DART) 데이터를 내부 REST API로 래핑하는 단순한 레이어드 아키텍처가 적합하다. 마이크로서비스나 이벤트 드리븐 같은 복잡한 패턴은 팀 5명 내부 툴에 과스펙이다.

**RESTful API 설계 원칙 (FastAPI 기준):**

| 엔드포인트 예시 | 역할 |
|--------------|------|
| `GET /api/companies` | 등록 기업 목록 조회 |
| `GET /api/companies/{corp_code}/financials` | 특정 기업 재무 데이터 조회 |
| `POST /api/analysis-sets` | 분석 세트 생성 |
| `GET /api/analysis-sets/{id}` | 분석 세트 조회 (기업 묶음 + 데이터) |
| `POST /api/dart/sync/{corp_code}` | 특정 기업 DART 데이터 강제 동기화 |
| `GET /api/dashboard/{set_id}` | 대시보드 차트 데이터 (집계) 반환 |

**FastAPI 레이어드 아키텍처:**
```
Route Layer    → HTTP 요청/응답 처리
Service Layer  → 비즈니스 로직 (DART 데이터 수집, 분석 세트 관리)
Repository Layer → DB 쿼리 (PostgreSQL/Supabase)
External Layer  → DART OpenAPI 호출 (OpenDartReader)
```

_Source: [FastAPI Best Practices](https://medium.com/@lautisuarez081/fastapi-best-practices-and-design-patterns-building-quality-python-apis-31774ff3c28a), [FastAPI Official](https://fastapi.tiangolo.com/)_

---

### Communication Protocols

**HTTP/REST (프론트엔드 ↔ 백엔드)**

- Next.js → FastAPI 통신: HTTP/HTTPS REST API (JSON 응답)
- 인증 토큰: JWT Bearer Token (`Authorization: Bearer <token>`)
- CORS 설정: FastAPI `CORSMiddleware`로 Next.js 도메인만 허용

**DART OpenAPI 통신 (백엔드 → 외부 API)**

- 프로토콜: HTTPS REST
- 응답 포맷: JSON (`fnlttSinglAcnt.json`) 또는 XML
- 인증: API Key (`crtfc_key` 쿼리 파라미터)
- 호출 한도: 20,000건/일 → 응답 캐싱 필수

**실시간 통신 (선택 사항)**

- DART 업데이트 알림(빨간 점 표시)은 실시간 웹소켓 불필요
- 페이지 로드 시 최신 상태 조회(polling) 방식으로 충분
- Supabase Realtime 구독으로 업데이트 알림 구현 가능 (구현 단순화)

_Source: [FastAPI CORS Guide](https://fastapi.tiangolo.com/), [DART OpenAPI 가이드](https://opendart.fss.or.kr/)_

---

### Data Formats and Standards

**재무 데이터 처리 파이프라인:**

```
DART API 응답 (JSON/XBRL)
    ↓ OpenDartReader / 직접 파싱
Python pandas DataFrame
    ↓ 표준화 (계정과목 정규화)
PostgreSQL 저장 (기업별·연도별 테이블)
    ↓ FastAPI 직렬화 (Pydantic)
JSON 응답
    ↓ Next.js → Recharts 데이터 형식 변환
차트 렌더링
```

**DART 응답 데이터 포맷 예시:**
```json
{
  "status": "000",
  "message": "정상",
  "list": [
    {
      "rcept_no": "20240329001234",
      "bsns_year": "2023",
      "corp_code": "00126380",
      "sj_div": "IS",
      "account_id": "ifrs-full_Revenue",
      "account_nm": "매출액",
      "thstrm_amount": "260904148860000"
    }
  ]
}
```

**주의**: 기업마다 `account_nm`(계정과목명)이 다를 수 있음 → 표준 매핑 테이블 관리 필요

_Source: [DART OpenAPI 개발가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019016)_

---

### 자동 업데이트 스케줄링 패턴 (매일 오전 7시)

**APScheduler + FastAPI 조합 (강력 추천)**

APScheduler는 FastAPI 내에서 BackgroundScheduler와 CronTrigger를 통해 정해진 시간에 작업을 자동 실행한다. DART 업데이트 체크(매일 7시)에 최적이다.

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()
scheduler.add_job(
    check_dart_updates,      # DART 공시 체크 함수
    trigger=CronTrigger(hour=7, minute=0),  # 매일 오전 7시
    id="daily_dart_sync"
)

# FastAPI lifespan으로 앱 시작/종료 시 스케줄러 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()
```

**업데이트 워크플로우:**
1. 매일 07:00 → `check_dart_updates()` 실행
2. 등록된 기업 목록 순회
3. 전날 이후 신규 공시(사업보고서) 확인
4. 신규 공시 발견 시 → 재무 데이터 갱신
5. DB에 `last_updated`, `has_new_data` 플래그 업데이트
6. 프론트엔드 분석 세트 리스트에서 빨간 점(●) 표시

_Source: [APScheduler + FastAPI 구현 가이드](https://rajansahu713.medium.com/implementing-background-job-scheduling-in-fastapi-with-apscheduler-6f5fdabf3186), [APScheduler 공식 문서](https://apscheduler.readthedocs.io/en/3.x/userguide.html)_

---

### 인증 및 권한 관리 패턴

**Supabase Auth + Row Level Security (RLS)**

팀 5명 규모 내부 툴에서 권한 4단계(빌더/Admin/라이브뷰어/읽기전용)를 구현하는 데 Supabase RLS가 가장 효율적이다.

**권한 구조 설계:**

| 역할 | 이메일 기반 초대 | 분석 세트 생성 | 수정/삭제 | 조회 |
|------|--------------|------------|---------|-----|
| Admin (팀장) | ✅ | ✅ | 전체 | ✅ |
| Builder (팀원) | - | ✅ | 본인 생성분 | ✅ |
| Live Viewer (실장) | - | ❌ | ❌ | ✅ (라이브) |
| Read-only (경영진) | - | ❌ | ❌ | ✅ |

**RLS 정책 예시:**
```sql
-- 분석 세트 수정: 생성자 또는 Admin만 가능
CREATE POLICY "analysis_sets_update" ON analysis_sets
  FOR UPDATE USING (
    auth.uid() = created_by OR
    auth.jwt() ->> 'role' = 'admin'
  );
```

**JWT 기반 역할 전달:**
- Supabase JWT에 `role` 클레임 포함
- FastAPI 미들웨어에서 JWT 검증 + 역할 확인
- Next.js 클라이언트에서 역할별 UI 분기 처리

_Source: [Supabase RLS 공식 문서](https://supabase.com/docs/guides/database/postgres/row-level-security), [Supabase RBAC 가이드](https://supabase.com/docs/guides/database/postgres/custom-claims-and-role-based-access-control-rbac)_

---

### System Interoperability 및 보안 패턴

**API 보안:**
- DART API Key: 환경변수로 관리 (`.env`), 절대 프론트엔드 노출 금지
- Supabase Anon Key: 공개 가능 (RLS로 보호), Service Key는 백엔드만 사용
- HTTPS 전구간 적용 (Vercel + Railway 기본 제공)

**에러 처리 패턴:**
- DART API 호출 실패 → 재시도 로직 (최대 3회, exponential backoff)
- API 한도 초과 → 캐싱 우선 응답, 다음 날 갱신
- 계정과목 미매핑 → 원본 계정명 그대로 표시 + 관리자 알림

**DART 데이터 캐싱 전략:**
- 이미 수집된 연도 데이터: DB 캐시 사용 (재호출 불필요)
- 최신 연도 데이터: 공시 여부 확인 후 갱신 여부 판단
- 강제 갱신: Admin이 수동 동기화 트리거 가능

_Source: [FastAPI 보안 가이드](https://fastapi.tiangolo.com/tutorial/security/), [Supabase 보안 가이드](https://supabase.com/docs/guides/api/securing-your-api)_

## Architectural Patterns and Design

### System Architecture Patterns (DART 대시보드 권장 구조)

**모듈형 모놀리스(Modular Monolith) + 레이어드 아키텍처 (강력 추천)**

팀 5명 내부 툴 규모에서는 마이크로서비스가 아닌 잘 구조화된 모놀리식 애플리케이션이 최적이다. 모놀리스는 초기 배포가 단순하고, 유지보수가 쉬우며, 소규모 팀에서 운영 오버헤드가 적다.

```
┌─────────────────────────────────────────────────┐
│                   클라이언트                       │
│           Next.js (Vercel 배포)                   │
│   [분석 세트 목록] [대시보드 뷰] [기업 관리]          │
└─────────────────┬───────────────────────────────┘
                  │ HTTPS REST API (JSON)
┌─────────────────▼───────────────────────────────┐
│              FastAPI 백엔드                        │
│           (Railway/Render 배포)                   │
│  ┌──────────┐ ┌──────────┐ ┌─────────────────┐  │
│  │ 기업 모듈 │ │분석세트  │ │ DART 동기화 모듈 │  │
│  │ /company │ │/analysis │ │ APScheduler     │  │
│  └──────────┘ └──────────┘ └─────────────────┘  │
│              공통: 인증/권한 미들웨어                │
└─────────────────┬───────────────────────────────┘
        ┌─────────┴──────────┐
        ▼                    ▼
┌──────────────┐    ┌─────────────────┐
│  Supabase    │    │  DART OpenAPI   │
│ (PostgreSQL) │    │  (외부 API)     │
│  Auth + RLS  │    │  opendart.fss   │
└──────────────┘    └─────────────────┘
```

**FastAPI 모듈 구조 (기능별 분리):**
```
backend/
├── main.py                 # FastAPI 앱 + lifespan
├── core/
│   ├── config.py          # 환경 변수 설정
│   ├── database.py        # DB 연결
│   └── auth.py            # JWT 검증
├── modules/
│   ├── company/
│   │   ├── router.py      # GET /api/companies
│   │   ├── service.py     # 비즈니스 로직
│   │   └── schemas.py     # Pydantic 모델
│   ├── financials/
│   │   ├── router.py      # GET /api/financials
│   │   ├── service.py     # DART 데이터 처리
│   │   └── dart_client.py # OpenDartReader 래핑
│   ├── analysis_sets/
│   │   └── ...
│   └── scheduler/
│       └── dart_sync.py   # APScheduler 작업
```

_Source: [FastAPI Best Practices - GitHub](https://github.com/zhanymkanov/fastapi-best-practices), [Modular Monolith FastAPI](https://github.com/arctikant/fastapi-modular-monolith-starter-kit)_

---

### Design Principles and Best Practices

**DART 대시보드 설계 원칙:**

1. **외부 의존성 격리**: DART OpenAPI 클라이언트를 별도 모듈(`dart_client.py`)로 격리 → 향후 API 스펙 변경 시 수정 최소화
2. **데이터 캐싱 우선**: DART에서 수집한 재무 데이터는 DB에 저장 후 재활용 → API 호출 최소화
3. **비동기 처리**: FastAPI의 `async/await` 활용으로 DART API 병렬 호출 (다수 기업 동시 조회)
4. **Pydantic 스키마 검증**: 재무 데이터 입출력 타입을 명확히 정의 → AI 생성 코드 오류 조기 감지

**Next.js 프론트엔드 패턴:**

- **Server Components (RSC)**: 대시보드 초기 렌더링은 서버에서 데이터 prefetch → 빠른 초기 로딩
- **SWR 또는 React Query**: 실시간성이 필요한 업데이트 알림(빨간 점)은 클라이언트 사이드 polling
- **Server Actions**: 분석 세트 생성/수정 폼 → 별도 API 없이 직접 DB 조작 가능 (Next.js 14+ 기능)

_Source: [FastAPI Best Practices PyCon 2025](https://cfp.in.pycon.org/2025/talk/LHLX8U/), [Next.js Data Fetching 공식](https://nextjs.org/docs/app/getting-started/fetching-data)_

---

### Data Architecture Patterns (DB 스키마 설계)

**핵심 테이블 구조:**

```sql
-- 기업 정보
companies (
  id, corp_code, corp_name, stock_code,
  sector, is_listed, created_at
)

-- 재무 데이터 (P&L + B/S 통합)
financial_data (
  id, corp_code, bsns_year, reprt_code,
  fs_div,           -- CFS/OFS
  account_type,     -- IS/BS/CF
  account_key,      -- 표준화 계정 키 (revenue, op_profit...)
  account_nm,       -- 원본 계정명
  amount,           -- 금액 (BIGINT, 원 단위)
  dart_updated_at,  -- DART 공시 일시
  synced_at
)

-- 분석 세트
analysis_sets (
  id, name, created_by, created_at,
  has_new_data      -- 신규 DART 업데이트 여부
)

-- 분석 세트 ↔ 기업 매핑 (N:M)
analysis_set_companies (
  set_id, corp_code, display_order
)

-- 계정과목 표준 매핑
account_mappings (
  raw_account_nm,   -- DART 원본 계정명
  standard_key,     -- 표준화 키 (revenue, op_profit...)
  display_nm_ko     -- 한글 표시명
)
```

**재무 금액 처리:**
- `BIGINT` 타입 사용 (원 단위, 삼성전자 매출 260조 → 260,904,148,860,000)
- 표시 시 프론트엔드에서 억/조 단위 변환 처리
- `NUMERIC(20, 0)` 또는 `BIGINT` 모두 적합 (PostgreSQL 정수 정밀도 충분)

_Source: [Financial Statement Database 설계 - Analyzing Alpha](https://analyzingalpha.com/financial-statement-database), [PostgreSQL Financial Data - Medium](https://medium.com/the-handbook-of-coding-in-finance/building-financial-data-storage-with-postgresql-in-python-b981e38826fe)_

---

### Scalability and Performance Patterns

**현 규모에서 최적화 우선순위:**

팀 5명 내부 툴이므로 수백 기업, 수천 데이터 포인트 수준 → 성능 최적화보다 **개발 속도와 유지보수성**이 우선.

| 최적화 항목 | MVP 적용 여부 | 설명 |
|-----------|------------|------|
| DB 인덱스 | ✅ 필수 | `corp_code + bsns_year` 복합 인덱스 |
| DART 응답 캐싱 | ✅ 필수 | 수집된 데이터 DB 저장, 재호출 없음 |
| 병렬 API 호출 | ✅ 적용 | `asyncio.gather()`로 다수 기업 동시 조회 |
| Redis 캐싱 | ❌ MVP 제외 | 추후 요청 증가 시 추가 |
| TimescaleDB | ❌ MVP 제외 | 일반 PostgreSQL로 충분한 규모 |
| CDN | ✅ 자동 | Vercel 배포 시 자동 적용 |

_Source: [PostgreSQL Time-Series Best Practices - Alibaba Cloud](https://www.alibabacloud.com/blog/postgresql-time-series-best-practices-stock-exchange-system-database_594815)_

---

### Deployment and Operations Architecture

**GitHub → 자동 배포 파이프라인:**

```
개발자 로컬 (Cursor + Claude Code)
    ↓ git push
GitHub Repository
    ├── Vercel (자동 감지) → 프론트엔드 배포
    └── Railway (자동 감지) → 백엔드 배포
         └── APScheduler 실행 중 (매일 07:00 DART 동기화)

환경 변수:
  .env.local      → Next.js 로컬
  Vercel Env      → Next.js 프로덕션
  Railway Env     → FastAPI 프로덕션 (DART_API_KEY, DATABASE_URL 등)
```

**개발 환경 설정 (비코더 친화):**
```bash
# 백엔드 실행
uvicorn main:app --reload  # FastAPI 개발 서버

# 프론트엔드 실행
npm run dev               # Next.js 개발 서버
```

_Source: [Next.js FastAPI Template - Vintasoftware](https://www.vintasoftware.com/blog/next-js-fastapi-template)_

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategy (비코더 단계별 접근)

**추천 개발 접근법: "AI-First 단계적 구축"**

코딩 경험 0인 개발자가 Claude Code/Cursor를 활용해 실제 프로덕션 내부 툴을 구축한 사례가 2025년 기준 검증되어 있다. 핵심은 **한 번에 모든 것을 구축하지 않고 동작하는 최소 단위부터 확장**하는 것이다.

**단계별 기술 도입 순서:**

| 단계 | 목표 | 도구 도입 | 검증 기준 |
|------|-----|---------|---------|
| 0단계: 환경 셋업 | 개발 환경 구성 | Cursor, Python, Node.js, Git | 로컬에서 "Hello World" 실행 |
| 1단계: DART 연동 PoC | API 데이터 수신 확인 | Python + OpenDartReader | 삼성전자 매출 데이터 출력 |
| 2단계: 백엔드 MVP | FastAPI REST API | FastAPI + Supabase | /api/companies 응답 |
| 3단계: 프론트엔드 MVP | 차트 대시보드 | Next.js + Recharts | 차트 1개 렌더링 |
| 4단계: 인증/권한 | 팀 접근 제어 | Supabase Auth + RLS | 로그인 후 역할별 뷰 |
| 5단계: 자동화 | 스케줄 업데이트 | APScheduler | 매일 7시 자동 갱신 확인 |

_Source: [Claude Code GitHub Integration 가이드](https://www.eesel.ai/blog/claude-code-github-integration), [Claude Code 활용 팁](https://www.builder.io/blog/claude-code)_

---

### Development Workflows and Tooling

**비코더 AI 개발 워크플로우 (일상적 개발 사이클):**

```
1. Cursor에서 자연어로 요청
   "DART API로 삼성전자의 2023년 매출액을 가져오는
    FastAPI 엔드포인트를 만들어줘"

2. Cursor/Claude Code가 코드 생성 + 파일 편집

3. 로컬에서 실행 테스트
   uvicorn main:app --reload

4. 에러 발생 시 에러 메시지를 Cursor에 붙여넣기
   "이런 에러가 났어: [에러 메시지]"

5. Cursor가 수정 제안 → 반복

6. 동작 확인 후 Git commit + push
   → Vercel/Railway 자동 배포
```

**Git/GitHub 비코더 운영 방법:**
- Cursor 내에서 Git 커밋/푸시 가능 (UI 제공)
- Claude Code로 `git add, commit, push` 자연어 명령 가능
- GitHub Desktop 앱 활용 (GUI 기반 Git, 터미널 불필요)

**프로젝트 구조 관리 팁:**
- `.claude/commands/` 폴더에 자주 쓰는 프롬프트 저장
- `CLAUDE.md` 파일에 프로젝트 컨텍스트 정의 → AI가 항상 참조

_Source: [AI Coding Tool 비교 2025](https://vladimirsiedykh.com/blog/ai-coding-assistant-comparison-claude-code-github-copilot-cursor-feature-analysis-2025), [Claude Code Git 워크플로우](https://www.eesel.ai/blog/git-workflows-claude-code)_

---

### Testing and Quality Assurance (MVP 최소 테스트 전략)

비코더 MVP 단계에서는 복잡한 테스트 커버리지보다 **핵심 경로 동작 검증**에 집중한다.

**FastAPI 필수 테스트 (pytest + TestClient):**

```python
# 핵심 API 엔드포인트 smoke test
def test_get_companies(client):
    response = client.get("/api/companies")
    assert response.status_code == 200

def test_get_financials(client):
    response = client.get("/api/companies/00126380/financials?year=2023")
    assert response.status_code == 200
    data = response.json()
    assert "revenue" in data  # 매출 데이터 존재 확인
```

**MVP 단계 테스트 우선순위:**
1. DART API 연동 함수 (가장 중요 - 외부 의존성)
2. 핵심 REST 엔드포인트 응답 코드
3. 인증/권한 거부 케이스
4. 차트 데이터 포맷 검증 (프론트엔드 렌더링 오류 방지)

**Next.js 최소 테스트 (Vitest):**
- MVP에서는 E2E 테스트보다 수동 QA 우선
- 차트 컴포넌트 렌더링 확인 정도로 시작

_Source: [FastAPI Testing 공식 문서](https://fastapi.tiangolo.com/tutorial/testing/), [Next.js Vitest 가이드](https://nextjs.org/docs/app/guides/testing/vitest)_

---

### Cost Optimization and Resource Management

**예상 인프라 비용 (월 기준):**

| 서비스 | 플랜 | 월 비용 | 제한 |
|--------|-----|--------|-----|
| **Vercel** | Hobby (Free) | $0 | 개인 프로젝트, 상업용 제한 |
| **Vercel** | Pro | $20 | 팀 공유, 상업용 내부 툴 ✅ |
| **Railway** | Hobby | $5 | FastAPI 백엔드, $5 크레딧 포함 |
| **Supabase** | Free | $0 | 500MB DB, 50MB 파일, 2GB 대역폭 |
| **Supabase** | Pro | $25 | 8GB DB, 무제한 인증 |

**MVP 권장 플랜 (무료 시작):**

| 서비스 | 플랜 | 월 비용 | 용도 |
|--------|-----|--------|-----|
| **Vercel** | Hobby (Free) | $0 | Next.js 프론트엔드 배포 |
| **Render** | Free | $0 | FastAPI 백엔드 (Python 유지) |
| **Supabase** | Free | $0 | PostgreSQL + Auth + pg_cron |
| **합계** | | **$0** | MVP 전체 무료 운영 |

**Render Free 슬립 이슈 해결책:**
- Render Free는 15분 비활성 시 슬립 → 첫 요청 약 30초 지연
- 팀이 매일 사용하는 내부 툴이므로 실제 슬립 빈도 낮음
- Supabase `pg_cron`으로 매일 06:58에 Render ping → 슬립 없이 07:00 자동 업데이트 실행

**향후 업그레이드 경로:**
- 운영 안정화 후 Railway Hobby $5 추가로 슬립 이슈 완전 해소

**DART API 비용:**
- OpenDart API Key: **무료** (금융감독원 회원가입 후 발급)
- 호출 한도: 20,000건/일 → 300개 기업 × 5년 데이터 = 1,500건 (한도 내 충분)

_Source: [Render FastAPI 배포 가이드](https://render.com/articles/fastapi-deployment-options), [Render vs Railway 비교](https://www.freetiers.com/blog/render-vs-railway-comparison), [Supabase pg_cron](https://supabase.com/docs/guides/database/extensions/pg_cron)_

---

### Risk Assessment and Mitigation

**주요 리스크 및 대응 전략:**

| 리스크 | 발생 가능성 | 영향도 | 대응 방안 |
|--------|----------|--------|---------|
| DART API 스펙 변경 | 중간 | 높음 | 외부 의존성 격리(`dart_client.py`), 변경 감지 모니터링 |
| 계정과목명 비표준화 | 높음 | 중간 | `account_mappings` 테이블 + 미매핑 시 원본명 표시 |
| 비코더 개발 지연 | 중간 | 중간 | 단계적 Phase 분리, MVP 최소화 |
| DART API 서비스 장애 | 낮음 | 중간 | DB 캐시로 최근 데이터 제공, 장애 배너 표시 |
| API 호출 한도 초과 | 낮음 | 낮음 | 수집된 데이터 DB 재활용, 일별 호출 모니터링 |
| 비상장사 데이터 없음 | 확실 | 낮음 | Phase 3 수기 입력으로 처리(이미 계획됨) |
| 보안: API Key 노출 | 낮음 | 높음 | 환경변수 엄수, 프론트 미노출 규칙 |

---

## Technical Research Recommendations

### Implementation Roadmap (권장 구현 순서)

**Phase 1 (MVP) - 핵심 기능:**
1. 개발 환경 셋업 (Cursor + Python + Node.js + GitHub)
2. Supabase 프로젝트 생성 + 스키마 마이그레이션
3. FastAPI 백엔드: DART API 연동 + `/companies`, `/financials` 엔드포인트
4. Next.js 프론트엔드: 기업 검색 + P&L 트렌드 차트 (Recharts)
5. 경쟁사 비교 차트
6. 차트 이미지 다운로드 기능
7. Vercel + Railway 배포

**Phase 2:**
1. Supabase Auth 연동 + 역할별 권한 (RLS)
2. B/S 데이터 (자산/부채/자본/현금성자산) 차트 추가
3. 분석 세트 저장/조회 기능
4. APScheduler 매일 7시 자동 업데이트
5. 빨간 점(●) 알림 UI

**Phase 3:**
1. 수기 입력 (비상장사)
2. Dooray 링크 공유
3. PPT Export

### Technology Stack Recommendations (최종 권장 스택)

```
Frontend:   Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
Charts:     Recharts (기본) → ApexCharts (인터랙티브 필요시)
Backend:    Python FastAPI + OpenDartReader + APScheduler
Database:   Supabase (PostgreSQL + Auth + RLS + pg_cron)
Deploy:     Vercel Hobby (FE, Free) + Render Free (BE)
Dev Tools:  Cursor + Claude Code
Version:    GitHub
Cost:       MVP $0 → 안정화 후 $5/월 (Render 슬립 해소 시)
```

### Skill Development Requirements

**비코더 학습 권장 사항 (우선순위 순):**
1. **Git 기초** (30분): add, commit, push 3개 명령어만 이해
2. **Python 환경** (1시간): `pip install`, 가상환경(`venv`) 개념
3. **환경변수 개념** (30분): `.env` 파일, Vercel/Railway 환경 설정
4. **REST API 개념** (1시간): GET/POST, JSON 응답 이해
5. **터미널 기초** (1시간): 파일 탐색, 명령 실행

→ 대부분의 실제 코딩은 Cursor + Claude Code가 대신하므로, 위 5가지만 이해해도 충분

### Success Metrics and KPIs

| 지표 | MVP 목표 | Phase 2 목표 |
|-----|---------|------------|
| 데이터 수집 시간 | DART 기업 1개 P&L: < 30초 | 분석 세트 10개 기업: < 2분 |
| 대시보드 로딩 시간 | < 3초 | < 2초 |
| 자동 업데이트 성공률 | - | > 95% |
| 월 인프라 비용 | < $25 | < $50 |
| 팀 채택률 | 팀원 5명 모두 사용 | 경영진 공유 활성화 |

<!-- Content will be appended sequentially through research workflow steps -->

---

## Technical Research Synthesis

# DART 기반 기업 실적 분석 대시보드: 종합 기술 리서치 보고서

## Executive Summary

DART(Data Analysis, Retrieval and Transfer) OpenAPI를 활용한 기업 실적 분석 대시보드는 금융감독원이 무료로 제공하는 전자공시 API를 기반으로, 팀 내부에서 기업 재무 데이터를 자동 수집·시각화하는 내부 툴이다. 본 종합 기술 리서치는 5단계에 걸쳐 DART API 스펙, 기술 스택, 통합 패턴, 아키텍처, 구현 전략을 체계적으로 분석한 결과를 담고 있다.

**핵심 기술 발견사항:**

- DART OpenAPI는 `fnlttSinglAcnt.json`, `fnlttSinglAcntAll.json`, `fnlttMultiAcnt.json` 엔드포인트를 통해 IS·BS·CF·CIS·SCE 5종 재무제표를 무료 API로 제공한다 (일일 20,000건 한도, 2015년 이후 데이터)
- Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui (FE) + Python FastAPI + OpenDartReader + APScheduler (BE) + Supabase PostgreSQL + Auth + RLS (DB) 조합이 비코더 AI 개발 환경에 최적화된 스택임을 확인
- Recharts가 React 생태계 완전 통합 + AI 코드 생성 품질에서 가장 우수하며, ApexCharts가 인터랙티브 기능 필요 시 차선책
- Vercel Hobby + Render Free + Supabase Free 조합으로 MVP 단계 $0 인프라 운영 가능
- 모듈형 모놀리스 + 레이어드 아키텍처(Route/Service/Repository/External Layer)가 팀 5명 내부 툴 규모에 최적

**기술 권장사항:**

- Next.js 14 + FastAPI + Supabase 풀스택 스택 채택 (비코더 AI 개발 최적)
- Cursor + Claude Code 조합으로 AI-First 단계적 개발 접근
- Phase 1 (MVP): DART API 연동 + 기본 P&L 차트 → Phase 2: 인증/권한 + 자동 업데이트 → Phase 3: 고급 기능
- `account_mappings` 테이블로 DART 계정과목 비표준화 문제 선제 해결
- Supabase pg_cron으로 Render Free 슬립 이슈 우회 (무료 운영 유지)

## Table of Contents

1. Technical Research Introduction and Methodology
2. DART 기반 기업 실적 분석 대시보드 기술 현황 및 아키텍처 분석
3. Implementation Approaches and Best Practices
4. Technology Stack Evolution and Current Trends
5. Integration and Interoperability Patterns
6. Performance and Scalability Analysis
7. Security and Compliance Considerations
8. Strategic Technical Recommendations
9. Implementation Roadmap and Risk Assessment
10. Future Technical Outlook and Innovation Opportunities
11. Technical Research Methodology and Source Verification
12. Technical Appendices and Reference Materials

---

## 1. Technical Research Introduction and Methodology

### Technical Research Significance

DART 기반 재무 대시보드는 국내 금융 분야에서 독특한 기회를 제공한다. 금융감독원의 DART 시스템은 2020년 OpenAPI 서비스를 개시하여 코스피·코스닥 전 상장사와 주요 비상장사의 재무제표 데이터를 무료로 API 형태로 공개하고 있다. 이 인프라를 활용하면 팀이 전문 금융 데이터 서비스(Bloomberg, Refinitiv 등)의 고비용 구독 없이도 내부 실적 분석 대시보드를 구축할 수 있다.

_Technical Importance: DART OpenAPI는 2020년 공식 서비스 개시 이후 개발자 커뮤니티에서 국내 재무 데이터 표준 소스로 자리잡았다._
_Business Impact: 팀 5명이 공유하는 내부 분석 툴을 통해 기업 실적 분석 효율 대폭 향상, 외부 데이터 서비스 구독 비용 절감_
_Source: [DART OpenAPI 공식](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019016)_

### Technical Research Methodology

- **Technical Scope**: DART API 스펙, 기술 스택(언어·프레임워크·DB·차트·배포), 통합 패턴, 아키텍처 설계, 구현 전략, 비용 최적화 전 영역 커버
- **Data Sources**: DART OpenAPI 공식 가이드, FastAPI/Next.js 공식 문서, OpenDartReader GitHub, 기술 블로그, AI 코딩 도구 비교 리뷰, Supabase/Render/Vercel 공식 가이드 등 다중 권위 소스 교차 검증
- **Analysis Framework**: 5단계 기술 리서치 워크플로우 (기술 스택 → 통합 패턴 → 아키텍처 → 구현 전략 → 종합)
- **Time Period**: 2025~2026년 기준 현행 기술 데이터 중심
- **Technical Depth**: 실제 코드 예제, DB 스키마, 시스템 다이어그램 포함 실무 구현 수준

### Technical Research Goals and Objectives

**Original Technical Goals:** 1) DART OpenAPI 데이터 범위 파악, 2) 비코더 친화적 기술 스택 선택, 3) 금융 데이터 시각화 라이브러리 비교

**Achieved Technical Objectives:**

- **Goal 1 달성**: DART API 엔드포인트 5종(단일/다중/전체 재무제표, 공시목록, 기업개황), 재무제표 5종(IS/BS/CF/CIS/SCE), 파라미터 스펙(corp_code, bsns_year, reprt_code, fs_div), 일일 호출 한도 20,000건 등 완전히 파악. OpenDartReader 라이브러리로 Python 연동 단순화 확인
- **Goal 2 달성**: Next.js 14 + FastAPI + Supabase 스택이 비코더 + AI 코딩 도구(Cursor + Claude Code) 환경에 최적임 확인. 5단계 학습 최소화 요구사항 정의 (Git 기초, Python 환경, 환경변수, REST API 개념, 터미널 기초)
- **Goal 3 달성**: 5개 주요 React 차트 라이브러리 비교(Recharts, ApexCharts, Chart.js, ECharts, D3.js) 완료. Recharts 1순위 선정 근거 명확화 (100만+/주 다운로드, React JSX 완전 통합, AI 코드 생성 품질 최고)
- **추가 발견**: 인프라 $0 시작 가능 옵션 발견, Render Free 슬립 이슈 pg_cron 해결책 검증, DART 계정과목 비표준화 문제 및 해결 전략 수립

---

## 2. DART 기반 기업 실적 분석 대시보드: 기술 현황 및 아키텍처 분석

### Current Technical Architecture Patterns

DART 대시보드에 가장 적합한 아키텍처는 **모듈형 모놀리스(Modular Monolith) + 레이어드 아키텍처**다. 팀 5명 내부 툴 규모에서 마이크로서비스 아키텍처는 운영 복잡도 대비 효용이 낮다. 단일 FastAPI 앱 내에서 기능 도메인별 모듈을 분리하는 방식이 유지보수성과 개발 속도를 동시에 확보한다.

_Dominant Patterns: 모듈형 모놀리스 + 레이어드 아키텍처(Route/Service/Repository/External 4계층)_
_Architectural Evolution: 소규모 내부 툴은 2025년에도 모놀리스가 주류. 마이크로서비스는 대규모 엔터프라이즈 대상_
_Architectural Trade-offs: 모놀리스 → 빠른 개발·간단한 배포·낮은 운영 오버헤드 vs 마이크로서비스 → 독립 확장·기술 다양성·높은 복잡도_
_Source: [FastAPI Best Practices - GitHub](https://github.com/zhanymkanov/fastapi-best-practices), [Modular Monolith FastAPI](https://github.com/arctikant/fastapi-modular-monolith-starter-kit)_

### System Design Principles and Best Practices

DART 대시보드 설계 4대 원칙:

1. **외부 의존성 격리**: DART API 클라이언트를 `dart_client.py` 모듈로 격리하여 향후 API 스펙 변경 영향 최소화
2. **데이터 캐싱 우선**: 수집된 재무 데이터는 PostgreSQL에 저장, 재API 호출 없이 재활용
3. **비동기 처리**: `asyncio.gather()`로 다수 기업 DART 데이터 병렬 수집
4. **Pydantic 스키마 검증**: 재무 데이터 타입 안전성 확보, AI 생성 코드 오류 조기 감지

_Design Principles: 단일 책임 원칙, 의존성 역전 원칙(FastAPI DI 활용), 관심사 분리_
_Best Practice Patterns: 레이어드 아키텍처, Repository 패턴, 환경변수 기반 설정 관리_
_Architectural Quality Attributes: 비코더 유지보수성 > 성능 최적화 > 확장성 (우선순위 순)_
_Source: [FastAPI Best Practices PyCon 2025](https://cfp.in.pycon.org/2025/talk/LHLX8U/), [Next.js Data Fetching 공식](https://nextjs.org/docs/app/getting-started/fetching-data)_

---

## 3. Implementation Approaches and Best Practices

### Current Implementation Methodologies

비코더 AI-First 개발 방법론은 "동작하는 최소 단위부터 점진적 확장"이 핵심이다. 코딩 경험 0에서 시작하여 Cursor + Claude Code를 활용해 실제 프로덕션 내부 툴을 구축한 사례가 2025년 기준 검증되어 있다.

_Development Approaches: AI-First 점진적 개발, 단계별 Phase 분리 (MVP → 기능 확장 → 고급 기능)_
_Code Organization Patterns: FastAPI 기능별 모듈 분리 (`modules/company`, `modules/financials`, `modules/analysis_sets`, `modules/scheduler`)_
_Quality Assurance Practices: pytest smoke test (핵심 API 엔드포인트 응답 코드 검증), 수동 QA 우선_
_Deployment Strategies: GitHub push → Vercel/Render 자동 배포 (별도 CI/CD 구성 불필요)_
_Source: [Claude Code vs Cursor 2026 - Builder.io](https://www.builder.io/blog/cursor-vs-claude-code), [Next.js FastAPI Template](https://nextfastapi.com/)_

### Implementation Framework and Tooling

| 도구 | 역할 | 비코더 친화도 |
|-----|------|------------|
| Cursor | AI 코드 에디터 (프로젝트 전체 컨텍스트 파악) | ⭐⭐⭐ |
| Claude Code | 자율 코딩 에이전트 (긴 컨텍스트) | ⭐⭐⭐ |
| FastAPI | Python REST API 프레임워크 (자동 문서화) | ⭐⭐ |
| Next.js 14 | React 풀스택 프레임워크 (파일 기반 라우팅) | ⭐⭐ |
| Supabase | DB + Auth + RLS 통합 BaaS | ⭐⭐⭐ |
| Render | Python 앱 배포 PaaS (Docker 불필요) | ⭐⭐⭐ |
| Vercel | Next.js 배포 (GitHub 연동 자동) | ⭐⭐⭐ |

_Development Frameworks: FastAPI 0.100+ (async native, Pydantic v2), Next.js 14 (App Router, Server Components, Server Actions)_
_Tool Ecosystem: OpenDartReader 0.7+ (DART API Python 래퍼), APScheduler 3.x (백그라운드 스케줄링)_
_Build and Deployment Systems: GitHub + Vercel + Render (코드 없는 자동 CI/CD)_
_Source: [FastAPI Official](https://fastapi.tiangolo.com/), [Realtime Dashboard FastAPI + Next.js](https://jaehyeon.me/blog/2025-03-04-realtime-dashboard-3/)_

---

## 4. Technology Stack Evolution and Current Trends

### Current Technology Stack Landscape

2025년 내부 분석 대시보드 트렌드는 Python 백엔드 + JavaScript 프론트엔드 + BaaS DB의 명확한 삼원 구조로 수렴하고 있다. 이 스택은 AI 코딩 도구가 가장 잘 지원하는 조합이기도 하다.

_Programming Languages: Python (백엔드/데이터 처리), TypeScript (프론트엔드). 이 조합이 2025년 AI 코드 생성 품질 최고_
_Frameworks and Libraries: FastAPI (Python 비동기 API), Next.js 14 App Router (React SSR), shadcn/ui (Tailwind 기반 UI 컴포넌트), Recharts (차트)_
_Database and Storage Technologies: Supabase PostgreSQL (관계형), Auth 내장, RLS 권한 제어, pg_cron 스케줄링_
_API and Communication Technologies: REST/JSON (FE ↔ BE), DART OpenAPI HTTPS REST (BE ↔ 외부)_
_Source: [Tech Stack Guide 2025 - DEV Community](https://dev.to/dimeloper/choosing-tech-stack-in-2025-a-practical-guide-4gll), [Deploying Next.js FastAPI PostgreSQL 2025 - Medium](https://medium.com/@zafarobad/ultimate-guide-to-deploying-next-js-d57ab72f6ba6)_

### Technology Adoption Patterns

_Adoption Trends: BaaS(Supabase) 활용 급증으로 DB+Auth 직접 구축 시간 대폭 단축. AI 코딩 도구(Cursor, Claude Code)로 비코더의 실제 앱 구축이 현실화_
_Migration Patterns: Streamlit(빠른 PoC) → Next.js+FastAPI(팀 운영 수준) 마이그레이션이 내부 툴 표준 경로_
_Emerging Technologies: Next.js Server Actions(별도 API 없는 DB 직접 조작), Supabase Realtime(WebSocket 없는 실시간 구독)_
_Source: [Claude Code vs Cursor Complete Comparison 2026 - Northflank](https://northflank.com/blog/claude-code-vs-cursor-comparison), [Best AI Coding Tools - IEEE Spectrum](https://spectrum.ieee.org/best-ai-coding-tools)_

---

## 5. Integration and Interoperability Patterns

### Current Integration Approaches

DART 대시보드의 통합 아키텍처는 3계층 통합 구조다: 외부 DART API → 내부 FastAPI 백엔드 → Next.js 프론트엔드. 이 단방향 데이터 흐름에서 FastAPI가 외부 API 의존성을 캡슐화하는 Adapter 역할을 한다.

_API Design Patterns: RESTful JSON API (`/api/companies`, `/api/financials`, `/api/analysis-sets`, `/api/dart/sync`)_
_Service Integration: 단일 FastAPI 서비스 내 모듈 통합 (마이크로서비스 없음, 운영 단순화)_
_Data Integration: DART JSON → pandas DataFrame → PostgreSQL → Pydantic → JSON 응답의 선형 데이터 파이프라인_
_Source: [FastAPI Best Practices](https://medium.com/@lautisuarez081/fastapi-best-practices-and-design-patterns-building-quality-python-apis-31774ff3c28a)_

### Interoperability Standards and Protocols

_Standards Compliance: OpenAPI 3.0 (FastAPI 자동 생성), JWT Bearer Token (RFC 7519), HTTPS/TLS 전구간_
_Protocol Selection: HTTP/HTTPS REST (FE ↔ BE, 단순성 우선), HTTPS REST (BE ↔ DART API, 외부 강제)_
_Integration Challenges: DART 계정과목 비표준화(account_nm 다양성) → `account_mappings` 테이블로 해결, CORS 설정 필요(FastAPI CORSMiddleware)_
_Source: [DART OpenAPI 개발가이드](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019016)_

---

## 6. Performance and Scalability Analysis

### Performance Characteristics and Optimization

팀 5명 내부 툴의 데이터 규모(수백 기업 × 5년 = 수천 레코드)에서 PostgreSQL 표준 쿼리 성능은 충분하다. MVP 단계에서는 성능보다 개발 속도가 우선이며, 필수 최적화만 적용한다.

_Performance Benchmarks: 대시보드 로딩 목표 < 3초 (Vercel CDN + Supabase 조합으로 달성 가능)_
_Optimization Strategies: `corp_code + bsns_year` 복합 인덱스, asyncio.gather() 병렬 API 호출, 수집 데이터 DB 캐싱_
_Monitoring and Measurement: Vercel Analytics (무료), Render 로그 모니터링_
_Source: [PostgreSQL Financial Data Best Practices](https://medium.com/the-handbook-of-coding-in-finance/building-financial-data-storage-with-postgresql-in-python-b981e38826fe)_

### Scalability Patterns and Approaches

_Scalability Patterns: 수직 확장 우선 (Render/Railway 플랜 업그레이드). 현 규모에서 수평 확장 불필요_
_Capacity Planning: Supabase Free(500MB DB) → 300개 기업 × 20년 × 50 계정 = ~300,000 레코드 → 약 50MB. Free 티어로 수년간 충분_
_Elasticity and Auto-scaling: Vercel는 자동 CDN 스케일링 내장. 백엔드는 수동 업그레이드로 충분_
_Source: [Supabase 공식 가이드](https://supabase.com/docs/guides/database)_

---

## 7. Security and Compliance Considerations

### Security Best Practices and Frameworks

DART 대시보드의 보안 핵심은 **API Key 관리**와 **Supabase RLS 권한 제어**다. 외부 공개가 아닌 내부 팀 툴이므로 복잡한 보안 인프라보다 기본 보안 원칙 철저 준수가 우선이다.

_Security Frameworks: JWT Bearer Token 인증 (Supabase Auth), Row Level Security (RLS) 권한 제어, HTTPS 전구간_
_Threat Landscape: DART API Key 노출(환경변수 엄수로 방지), 미인가 접근(RLS로 방지), 내부 데이터 유출(역할별 접근 제어)_
_Secure Development Practices: `.env` 파일 Git 제외 (`.gitignore`), Vercel/Render 환경변수 대시보드 사용, Supabase Service Key 백엔드만 사용_
_Source: [FastAPI 보안 가이드](https://fastapi.tiangolo.com/tutorial/security/), [Supabase RLS 공식](https://supabase.com/docs/guides/database/postgres/row-level-security)_

### Compliance and Regulatory Considerations

_Industry Standards: DART OpenAPI 이용약관 준수 (일일 호출 한도 20,000건, 상업적 재배포 금지)_
_Regulatory Compliance: 내부 분석 목적 DART 데이터 활용은 이용약관 내 허용. 외부 공개 시 금감원 허가 필요_
_Audit and Governance: `synced_at` 타임스탬프로 데이터 수집 이력 관리, `dart_updated_at`으로 원본 공시 시점 추적_
_Source: [DART OpenAPI 이용약관](https://opendart.fss.or.kr/intro/main.do)_

---

## 8. Strategic Technical Recommendations

### Technical Strategy and Decision Framework

5단계 리서치 결과 도출된 전략적 권장사항:

| 결정 영역 | 권장사항 | 근거 |
|---------|---------|-----|
| 아키텍처 패턴 | 모듈형 모놀리스 + 레이어드 아키텍처 | 팀 5명 규모, 운영 단순성 우선 |
| 언어 선택 | Python (BE) + TypeScript (FE) | AI 코드 생성 품질 최고, DART 에코시스템 |
| DB 선택 | Supabase PostgreSQL | Auth+RLS 내장, Free 티어 충분 |
| 차트 라이브러리 | Recharts (기본) | React 완전 통합, AI 코드 생성 최적 |
| 배포 전략 | Vercel Hobby + Render Free | MVP $0 인프라 |
| 개발 도구 | Cursor + Claude Code | 비코더 AI-First 개발 최적 조합 |

_Architecture Recommendations: 단일 FastAPI 앱 내 도메인별 모듈 분리. `dart_client.py` 격리로 외부 API 변경 영향 최소화_
_Technology Selection: Next.js 14 App Router (SSR + Server Components + Server Actions 활용), Pydantic v2 (데이터 검증 성능 향상)_
_Implementation Strategy: 6단계 점진적 구현 (0: 환경셋업 → 1: DART PoC → 2: 백엔드 MVP → 3: 프론트엔드 MVP → 4: 인증/권한 → 5: 자동화)_
_Source: [Complete AI Coding Course 2025 - Udemy](https://www.udemy.com/course/the-complete-ai-coding-course-2025-cursor-ai-v0-vercel/), [Next.js FastAPI Template - Vintasoftware](https://www.vintasoftware.com/blog/next-js-fastapi-template)_

### Competitive Technical Advantage

_Technology Differentiation: DART OpenAPI 무료 활용으로 Bloomberg/Refinitiv 대비 비용 절감. 내부 분석 특화 UX로 범용 툴 대비 효율 향상_
_Innovation Opportunities: AI 요약 기능 추가(LLM API 연동), 산업군별 벤치마킹, 수기 입력 비상장사 데이터 통합_
_Strategic Technology Investments: Cursor Pro 구독($20/월)이 개발 속도 대비 가장 높은 ROI_
_Source: [Dashboard Builder Guide 2026 - WeWeb](https://www.weweb.io/blog/dashboard-builder-guide-no-code-ai-best-practices)_

---

## 9. Implementation Roadmap and Risk Assessment

### Technical Implementation Framework

3단계 구현 프레임워크:

**Phase 1 (MVP, 2-4주):**
- 개발 환경 셋업 (Cursor + Python 3.11+ + Node.js 20+ + GitHub 레포 생성)
- Supabase 프로젝트 + 스키마 마이그레이션 (`companies`, `financial_data`, `account_mappings`)
- FastAPI DART 연동 + REST 엔드포인트 (`/companies`, `/financials`)
- Next.js P&L 트렌드 차트 (Recharts), 경쟁사 비교 차트
- Vercel Hobby + Render Free 배포

**Phase 2 (인증·권한·자동화, 2-3주):**
- Supabase Auth 연동 + RLS 4단계 권한 (Admin/Builder/LiveViewer/ReadOnly)
- B/S 데이터 차트 (자산·부채·자본·현금성자산)
- 분석 세트 저장/조회 기능
- APScheduler 매일 07:00 DART 자동 업데이트
- 빨간 점(●) 신규 데이터 알림 UI
- Supabase pg_cron으로 06:58 Render ping (슬립 이슈 해결)

**Phase 3 (고급 기능, 3-4주):**
- 비상장사 수기 입력 기능
- Dooray 링크 공유
- PPT Export

_Implementation Phases: Phase 1 (MVP 핵심) → Phase 2 (팀 운영) → Phase 3 (완성도)_
_Technology Migration Strategy: 로컬 SQLite 개발 → Supabase PostgreSQL 프로덕션 (migration 스크립트)_
_Resource Planning: 비코더 1인 + AI 도구. Cursor Pro($20/월) 투자 권장_
_Source: [FastAPI Testing 공식](https://fastapi.tiangolo.com/tutorial/testing/), [Supabase pg_cron](https://supabase.com/docs/guides/database/extensions/pg_cron)_

### Technical Risk Management

| 리스크 | 확률 | 영향 | 대응 |
|--------|-----|------|-----|
| DART API 스펙 변경 | 중간 | 높음 | `dart_client.py` 격리 모듈화 |
| 계정과목 비표준화 | 높음 | 중간 | `account_mappings` 테이블 선제 구축 |
| Render Free 슬립 | 확실 | 낮음 | pg_cron ping(06:58) + 매일 사용 패턴 |
| 비코더 개발 지연 | 중간 | 중간 | Phase 분리 + AI 도구 최대 활용 |
| API 호출 한도 초과 | 낮음 | 낮음 | DB 캐싱 우선, 수집 데이터 재활용 |
| 비상장사 데이터 공백 | 확실 | 낮음 | Phase 3 수기 입력으로 처리 |
| Vercel 상업적 이용 | 낮음 | 중간 | 내부 전용 툴·매출 없음 (회색지대 수용) |

_Technical Risks: DART API 의존성(격리 패턴으로 완화), 비코더 복잡도 증가(Phase 분리로 완화)_
_Implementation Risks: Render 슬립 자동화(pg_cron ping 해결), 환경변수 관리 실수(체크리스트로 방지)_
_Business Impact Risks: 인프라 비용 증가 시 Railway $5 단계적 전환으로 통제 가능_
_Source: [Render FastAPI 배포 가이드](https://render.com/articles/fastapi-deployment-options), [Render vs Railway 비교](https://www.freetiers.com/blog/render-vs-railway-comparison)_

---

## 10. Future Technical Outlook and Innovation Opportunities

### Emerging Technology Trends

_Near-term Technical Evolution (1-2년): LLM API(GPT-4o, Claude)를 활용한 재무 데이터 AI 요약 기능. Supabase AI/Vector 기능으로 자연어 쿼리 지원. Next.js 15+ Server Actions 확대_
_Medium-term Technology Trends (3-5년): 실시간 DART 공시 WebSocket 수신 (현재 DART는 polling만 지원). XBRL 구조화 데이터 직접 파싱으로 계정과목 표준화 자동화_
_Long-term Technical Vision (5년+): DART API 자체 AI 요약 기능 추가 예상. 오픈소스 한국 금융 데이터 표준화 이니셔티브_
_Source: [AI Coding Tools 2025 - IEEE Spectrum](https://spectrum.ieee.org/best-ai-coding-tools), [Dashboard Builder Guide 2026](https://www.weweb.io/blog/dashboard-builder-guide-no-code-ai-best-practices)_

### Innovation and Research Opportunities

_Research Opportunities: DART 계정과목 자동 표준화(LLM 기반 매핑 제안), 재무 이상치 탐지 알고리즘, 산업군별 벤치마크 자동화_
_Emerging Technology Adoption: LangChain + DART 데이터로 "삼성전자 2023년 영업이익 추이는?" 자연어 질의 지원_
_Innovation Framework: Phase 3 완료 후 AI 기능 레이어 추가. 기존 REST API 위에 LLM 레이어만 추가하면 기존 기능 유지하면서 확장 가능_
_Source: [OpenDartReader GitHub](https://github.com/FinanceData/OpenDartReader)_

---

## 11. Technical Research Methodology and Source Verification

### Comprehensive Technical Source Documentation

**Primary Technical Sources:**
- DART OpenAPI 공식 가이드: https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019016
- OpenDartReader GitHub: https://github.com/FinanceData/OpenDartReader
- FastAPI 공식 문서: https://fastapi.tiangolo.com/
- Next.js 공식 문서: https://nextjs.org/docs/
- Supabase 공식 문서: https://supabase.com/docs/
- APScheduler 공식 문서: https://apscheduler.readthedocs.io/

**Secondary Technical Sources:**
- Next.js FastAPI Template: https://nextfastapi.com/
- Vintasoftware Next.js FastAPI 가이드: https://www.vintasoftware.com/blog/next-js-fastapi-template
- LogRocket 2025 React 차트 라이브러리 비교: https://blog.logrocket.com/best-react-chart-libraries-2025/
- Render FastAPI 배포: https://render.com/articles/fastapi-deployment-options
- Supabase pg_cron: https://supabase.com/docs/guides/database/extensions/pg_cron
- Claude Code vs Cursor 2026: https://www.builder.io/blog/cursor-vs-claude-code
- Realtime Dashboard FastAPI + Next.js: https://jaehyeon.me/blog/2025-03-04-realtime-dashboard-3/

**Technical Web Search Queries Used:**
- "DART OpenAPI financial dashboard FastAPI Next.js"
- "non-coder AI development Cursor Claude Code 2025 internal tool"
- "APScheduler FastAPI background scheduler"
- "Supabase RLS row level security role-based access"
- "Recharts vs ApexCharts React chart library 2025"
- "Render Free tier Python FastAPI deployment sleep"
- "Vercel Hobby plan commercial use policy"
- "Supabase pg_cron scheduled jobs"

### Technical Research Quality Assurance

_Technical Source Verification: 모든 핵심 기술 주장(DART API 한도, Supabase Free 티어 제한, Render 슬립 정책)은 공식 문서 또는 다수 블로그 교차 검증_
_Technical Confidence Levels: DART API 스펙(높음-공식 문서), Render 슬립 이슈(높음-다수 블로그), AI 코딩 도구 비교(중간-빠르게 변화하는 영역)_
_Technical Limitations: Vercel Hobby 상업적 이용 경계 불명확(회색지대), DART API 안정성 SLA 미공개, Render 무료 티어 정책 변경 가능_
_Methodology Transparency: 5단계 순차 리서치 + 각 단계 웹 검색 기반 현행 데이터 검증_

---

## 12. Technical Appendices and Reference Materials

### Detailed Technical Data Tables

**차트 라이브러리 상세 비교:**

| 라이브러리 | 주간 다운로드 | 렌더링 방식 | AI 코드 생성 품질 | 금융 대시보드 적합성 | 라이선스 |
|-----------|------------|-----------|----------------|------------------|--------|
| Recharts | 100만+ | SVG | ⭐⭐⭐ 최고 | ✅ 매우 적합 | MIT |
| ApexCharts | 급성장 | SVG | ⭐⭐ 좋음 | ✅ 적합 | MIT |
| Chart.js | 최다 | Canvas | ⭐⭐ 좋음 | ✅ 적합 | MIT |
| Apache ECharts | 기업용 | Canvas+WebGL | ⭐ 중간 | △ 과스펙 | Apache 2.0 |
| D3.js | 커스텀 극강 | SVG | ⭐ 어려움 | ❌ 비코더 비적합 | ISC |

**인프라 비용 비교:**

| 조합 | 월 비용 | 특징 | 권장 시점 |
|-----|--------|------|---------|
| Vercel Hobby + Render Free + Supabase Free | $0 | 슬립 이슈 (pg_cron으로 해결) | MVP 시작 |
| Vercel Hobby + Railway Hobby + Supabase Free | $5 | 슬립 없음, 안정적 | 안정화 후 |
| Vercel Pro + Railway + Supabase Pro | $50+ | 완전 프로덕션 | 팀 규모 확대 시 |

**DART API 엔드포인트 상세:**

| 엔드포인트 | 기능 | 주요 파라미터 | 반환 재무제표 |
|-----------|-----|-------------|------------|
| `fnlttSinglAcnt.json` | 단일회사 주요계정 | corp_code, bsns_year, reprt_code, fs_div | IS·BS 주요 항목 |
| `fnlttSinglAcntAll.json` | 단일회사 전체 재무 | 동일 | IS·BS·CF·CIS·SCE 전체 |
| `fnlttMultiAcnt.json` | 다중회사 일괄 | corp_code(복수), bsns_year | IS·BS 주요 항목 |
| `list.json` | 공시 목록 | corp_code, bgn_de, end_de | - |
| `company.json` | 기업 기본정보 | corp_code | - |

### Technical Resources and References

_Technical Standards: DART OpenAPI 이용약관, JWT RFC 7519, OpenAPI 3.0 Specification_
_Open Source Projects: OpenDartReader (https://github.com/FinanceData/OpenDartReader), FastAPI (https://github.com/tiangolo/fastapi), Recharts (https://github.com/recharts/recharts), shadcn/ui (https://github.com/shadcn-ui/ui)_
_Research Papers and Publications: FinanceData 블로그 (DART API 활용 가이드), Supabase 공식 블로그 (RLS 구현 패턴)_
_Technical Communities: FastAPI 디스코드, Next.js GitHub Discussions, Supabase 커뮤니티, 국내 DART API 활용 GitHub 레포지토리_

---

## Technical Research Conclusion

### Summary of Key Technical Findings

5단계 체계적 기술 리서치를 통해 DART 기반 기업 실적 분석 대시보드 구축을 위한 최적 기술 스택과 구현 전략을 확정하였다.

**3대 핵심 발견:**

1. **DART OpenAPI는 완전한 재무 데이터 플랫폼**: IS·BS·CF·CIS·SCE 5종 재무제표를 2015년 이후 무료로 제공. OpenDartReader Python 라이브러리로 연동 단순화. 일일 20,000건 한도는 내부 팀 용도로 충분
2. **Next.js + FastAPI + Supabase 스택이 비코더 AI 개발에 최적**: AI 코딩 도구(Cursor + Claude Code)가 가장 잘 지원하는 조합. 비코더도 5가지 기초 개념(Git, Python 환경, 환경변수, REST API, 터미널)만 이해하면 AI의 도움으로 프로덕션 내부 툴 구축 가능
3. **MVP를 $0으로 시작 가능**: Vercel Hobby + Render Free + Supabase Free 조합. Render 슬립 이슈는 pg_cron ping으로 해결. 안정화 후 Railway Hobby $5로 단계적 업그레이드

### Strategic Technical Impact Assessment

이 리서치 결과는 팀이 외부 금융 데이터 서비스에 의존하지 않고 DART 공공 API를 활용해 자체 분석 인프라를 구축할 수 있음을 기술적으로 검증했다. 비코더 AI-First 개발 방법론의 현실 가능성도 최신 도구(Cursor + Claude Code)와 함께 확인되었다. 특히 인프라 비용 $0 시작이 가능함을 확인하여 초기 리스크를 최소화하고 가치 검증 후 비용을 점진적으로 투입하는 전략이 실현 가능하다.

### Next Steps Technical Recommendations

1. **즉시 착수**: 개발 환경 셋업 (Cursor + Python 3.11+ + Node.js 20+ + GitHub 레포 생성)
2. **DART PoC**: OpenDartReader로 삼성전자 2023년 P&L 데이터 수신 확인 (1-2시간)
3. **Supabase 설정**: 프로젝트 생성 + DB 스키마 마이그레이션 (이 리서치의 SQL 스키마 활용)
4. **PRD 작성**: 이 기술 리서치를 기반으로 제품 요구사항 문서 작성
5. **아키텍처 문서**: FastAPI 모듈 구조, DB 스키마, API 명세 공식화

---

**Technical Research Completion Date:** 2026-03-03
**Research Period:** 2025~2026년 현행 기술 데이터 기준
**Document Length:** 종합 기술 리서치 (단계별 심층 분석 포함)
**Source Verification:** 모든 핵심 기술 사실 공식 문서 및 다중 소스 검증
**Technical Confidence Level:** 높음 - 다수 권위 있는 기술 소스 기반

_이 종합 기술 리서치 보고서는 DART 기반 기업 실적 분석 대시보드의 기술 스택 선택과 구현 전략에 관한 권위 있는 기술 참조 문서로, PRD 작성 및 실제 개발 착수의 기반이 된다._
