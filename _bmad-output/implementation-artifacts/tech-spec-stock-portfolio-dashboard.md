---
title: '주식 포트폴리오 대시보드'
slug: 'stock-portfolio-dashboard'
created: '2026-02-26'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack:
  - Next.js 15 (App Router)
  - TypeScript
  - TailwindCSS 3.x
  - shadcn/ui
  - Recharts
  - papaparse (CSV 파싱)
  - Naver Finance polling API (국내 현재가)
  - Yahoo Finance API v8 (미국 주식/ETF)
  - open.er-api.com (환율, 무료/키 불필요)
files_to_modify:
  - portfolio-dashboard/app/page.tsx
  - portfolio-dashboard/app/api/price/route.ts
  - portfolio-dashboard/app/api/price-us/route.ts
  - portfolio-dashboard/app/api/exchange-rate/route.ts
  - portfolio-dashboard/components/HeroSection.tsx
  - portfolio-dashboard/components/AccountCards.tsx
  - portfolio-dashboard/components/SectorChart.tsx
  - portfolio-dashboard/components/StockList.tsx
  - portfolio-dashboard/components/StockDetailDrawer.tsx
  - portfolio-dashboard/components/CsvUpload.tsx
  - portfolio-dashboard/lib/csv-parser.ts
  - portfolio-dashboard/lib/sector-tagger.ts
  - portfolio-dashboard/lib/price-fetcher.ts
  - portfolio-dashboard/lib/portfolio-calculator.ts
  - portfolio-dashboard/types/portfolio.ts
code_patterns:
  - Next.js App Router (app/ 디렉토리 구조)
  - TypeScript strict mode
  - React hooks (useState, useEffect, useMemo) - 전역 상태 불필요
  - 순수 함수로 비즈니스 로직 분리 (lib/)
  - 서버사이드 API Routes로 외부 API 프록시 (CORS 방지)
  - shadcn/ui 컴포넌트 시스템
test_patterns:
  - 개인용 도구이므로 핵심 비즈니스 로직만 테스트
  - sector-tagger.ts 유닛 테스트 (Jest/Vitest)
  - portfolio-calculator.ts 유닛 테스트
---

# Tech-Spec: 주식 포트폴리오 대시보드

**Created:** 2026-02-26

## Overview

### Problem Statement

미래에셋증권의 5개 계좌(ISA, 연금저축A, 연금저축B, CMA, IRP)가 분산되어 있어, 통합 섹터 비중과 전체 포트폴리오 현황을 한눈에 확인하기 어렵다. 특히 동일한 ETF 상품이 여러 계좌에 흩어져 있어 실제 섹터 노출 비중을 파악하기 위해 계좌마다 수동으로 합산해야 하는 불편함이 있다.

### Solution

CSV 파일 업로드 기반의 개인용 Next.js 웹 대시보드를 구축한다. 사용자가 보유종목 정보를 CSV로 업로드하면, ETF 이름 키워드 기반으로 섹터를 자동 태깅하고, 네이버 금융 / Yahoo Finance API로 현재가를 조회하며, 당일 환율 API로 USD 자산을 KRW로 환산하여 통합 포트폴리오 현황을 제공한다. 하루 2~3회 빠르게 확인하는 패턴에 맞게, 열자마자 오늘 손익이 가장 먼저 눈에 들어오는 레이아웃으로 설계한다.

### Scope

**In Scope:**
- CSV 파일 업로드 (컬럼: 계좌, 종목명, 종목번호, 수량, 평균단가, 단위)
- 오늘 손익 표시 — 전체 합산 및 계좌별 (금액 + %, 최우선 표시)
- 총 평가금액 표시 (USD 자산은 당일 환율 기준 KRW 환산, 달러 병기)
- 섹터 비중 파이차트 (ETF 이름 키워드 자동 태깅, 계좌 통합)
- 종목별 수익률 리스트 (동일 종목코드 기준 계좌 통합, 드릴다운으로 계좌별 분포 표시)
- 전체기간 수익 표시 (하단 배치)
- 당일 환율 헤더 표시 (USD/KRW)
- 로컬 환경 실행 (localhost)

**Out of Scope:**
- 미래에셋증권 직접 API 연동
- 매매 기록, 거래 내역
- 알림 / 푸시 기능
- 목표 비중 설정
- 과거 수익률 차트 / 히스토리
- 다중 사용자 / 외부 배포

## Context for Development

### Codebase Patterns

**Confirmed Clean Slate** — 기존 코드 없음. 아래 패턴으로 신규 구축:

- **앱 위치**: `portfolio-dashboard/` (프로젝트 루트 하위 서브디렉토리)
- **라우팅**: Next.js 15 App Router (`app/` 디렉토리 구조)
- **언어**: TypeScript strict mode 전체 적용
- **UI**: shadcn/ui 컴포넌트 + TailwindCSS 유틸리티 클래스
- **상태관리**: React hooks (`useState`, `useEffect`, `useMemo`) — 전역 상태 라이브러리 불필요 (개인용 단일 페이지)
- **비즈니스 로직**: `lib/` 디렉토리에 순수 함수로 완전 분리 (테스트 용이)
- **외부 API**: 모두 `app/api/` Next.js Route Handler를 통한 서버사이드 프록시 처리 (브라우저 CORS 방지)
- **데이터 흐름**: CSV 업로드 → 파싱 → 섹터 태깅 → 현재가 조회 → 계산 → 렌더링

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `portfolio-dashboard/app/page.tsx` | 메인 대시보드 페이지, 데이터 흐름 오케스트레이션 |
| `portfolio-dashboard/app/api/price/route.ts` | 국내 현재가 프록시 (네이버 금융 polling API) |
| `portfolio-dashboard/app/api/price-us/route.ts` | 미국 현재가 프록시 (Yahoo Finance API v8) |
| `portfolio-dashboard/app/api/exchange-rate/route.ts` | USD/KRW 환율 프록시 (open.er-api.com) |
| `portfolio-dashboard/components/HeroSection.tsx` | 오늘 손익 히어로 섹션 |
| `portfolio-dashboard/components/AccountCards.tsx` | 계좌별 요약 카드 5개 |
| `portfolio-dashboard/components/SectorChart.tsx` | 섹터 비중 파이차트 (Recharts) |
| `portfolio-dashboard/components/StockList.tsx` | 종목별 수익률 리스트 |
| `portfolio-dashboard/components/StockDetailDrawer.tsx` | 종목 드릴다운 (계좌별 분포) |
| `portfolio-dashboard/components/CsvUpload.tsx` | CSV 드래그&드롭 업로드 |
| `portfolio-dashboard/lib/csv-parser.ts` | papaparse 기반 CSV 파싱 및 유효성 검사 |
| `portfolio-dashboard/lib/sector-tagger.ts` | ETF 이름 키워드 → 섹터 자동 매핑 |
| `portfolio-dashboard/lib/price-fetcher.ts` | 국내/미국 현재가 일괄 조회 |
| `portfolio-dashboard/lib/portfolio-calculator.ts` | 평가금액, 손익, 수익률, 섹터 비중 계산 |
| `portfolio-dashboard/types/portfolio.ts` | 전체 TypeScript 타입 정의 |

### Technical Decisions

1. **CSV 구조**: 단일 파일에 모든 계좌 데이터 포함. 컬럼: `계좌,종목명,종목번호,수량,평균단가,단위`

2. **현재가 API**:
   - 국내 (KRW): `https://polling.finance.naver.com/api/realtime/domestic/stock/{code}` — JSON 응답, 별도 파싱 불필요
   - 미국 (USD): `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d` — `meta.regularMarketPrice` 필드 사용

3. **환율 API**: `https://open.er-api.com/v6/latest/USD` — 무료, API 키 불필요, 당일 1회 조회 후 메모리 캐싱

4. **섹터 자동 태깅 우선순위**:
   - 1순위: 종목명 키워드 매칭 (아래 기준표)
   - 2순위: 단위가 `USD`인 종목 → 미국주식/ETF
   - 3순위: 미매칭 → `기타`

5. **섹터 분류 기준표**:
   | 섹터 | 키워드 |
   |------|--------|
   | 🌎 미국지수 | 미국, S&P, 나스닥, NASDAQ, QQQ, DIA, SPY, 다우, 1Q, RISE AI |
   | 🇰🇷 국내지수 | 코스피, 코스닥, KOSPI, TIGER 200, KODEX 200, 코스피50, KRX(금 제외) |
   | 🥇 금 | 금현물, KRX금, GOLD |
   | 🛡️ 방산/테마 | 방산, 조선, 2차전지, 반도체 |
   | 📜 채권/혼합 | 채권, 국채, 혼합, 금채 |
   | 🌍 해외기타 | 유로, 유럽, 신흥국 |
   | 🏦 개별주 | 미매칭 국내 KRW 종목 |

6. **동일 종목 통합**: 종목번호(코드) 기준 그룹핑, 수량 합산 후 가중평균 단가 계산

7. **USD→KRW 표시**: 원화 메인 표기, 달러 괄호 병기 — 예: `₩2,823K ($2,056)`

8. **환경**: 로컬 전용 (`npm run dev`), 인증/로그인 불필요

## Implementation Plan

### Tasks

- [x] Task 1: Next.js 프로젝트 초기화 및 의존성 설치
  - File: `portfolio-dashboard/` (신규 디렉토리)
  - Action: `npx create-next-app@latest portfolio-dashboard --typescript --tailwind --app --no-src-dir --import-alias "@/*"` 실행 후 추가 패키지 설치: `npm install recharts papaparse @types/papaparse shadcn/ui`
  - Notes: shadcn/ui 초기화 `npx shadcn@latest init` — 기본 테마(neutral) 선택. `next.config.ts`에 외부 이미지 도메인 설정 불필요.

- [x] Task 2: TypeScript 타입 정의
  - File: `portfolio-dashboard/types/portfolio.ts`
  - Action: 아래 인터페이스 정의
    ```ts
    export interface RawHolding {
      계좌: string;        // ISA | 연금저축A | 연금저축B | CMA | IRP
      종목명: string;
      종목번호: string;    // 국내: 6자리 코드, 미국: 티커
      수량: number;
      평균단가: number;
      단위: 'KRW' | 'USD';
    }
    export type SectorKey = '미국지수' | '국내지수' | '금' | '방산/테마' | '채권/혼합' | '해외기타' | '개별주' | '기타';
    export interface HoldingWithMeta extends RawHolding {
      sector: SectorKey;
      currentPrice: number;      // 현재가 (원화 또는 달러, 단위 기준)
      currentPriceKRW: number;   // KRW 환산 현재가
      evalAmount: number;        // 평가금액 KRW
      gainAmount: number;        // 평가손익 KRW
      gainRate: number;          // 수익률 %
      todayGainAmount: number;   // 오늘 손익 KRW (전일종가 대비)
      todayGainRate: number;     // 오늘 수익률 %
      prevClose: number;         // 전일종가 (단위 기준)
    }
    export interface ConsolidatedHolding {
      종목번호: string;
      종목명: string;
      단위: 'KRW' | 'USD';
      sector: SectorKey;
      totalQty: number;
      avgCost: number;           // 가중평균 단가 KRW
      currentPrice: number;
      evalAmount: number;        // KRW
      gainAmount: number;        // KRW
      gainRate: number;          // %
      todayGainAmount: number;   // KRW
      todayGainRate: number;     // %
      byAccount: {
        account: string;
        qty: number;
        evalAmount: number;
        ratio: number;           // 이 종목 내 계좌 비중 %
      }[];
    }
    export interface AccountSummary {
      account: string;
      evalAmount: number;        // KRW
      todayGainAmount: number;   // KRW
      todayGainRate: number;     // %
    }
    export interface SectorAllocation {
      sector: SectorKey;
      amount: number;            // KRW
      ratio: number;             // %
      color: string;             // 파이차트 색상
    }
    export interface PortfolioSummary {
      totalEval: number;         // 총 평가금액 KRW
      totalCost: number;         // 총 투자원금 KRW
      totalGainAmount: number;   // 전체기간 손익 KRW
      totalGainRate: number;     // 전체기간 수익률 %
      todayGainAmount: number;   // 오늘 손익 KRW
      todayGainRate: number;     // 오늘 수익률 %
      exchangeRate: number;      // 당일 USD/KRW
      updatedAt: string;         // 업데이트 시각
    }
    ```
  - Notes: `RawHolding`은 CSV 파싱 직후 타입. `HoldingWithMeta`는 현재가 조회 후 계산된 타입.

- [x] Task 3: 섹터 자동 태깅 로직
  - File: `portfolio-dashboard/lib/sector-tagger.ts`
  - Action: `tagSector(holding: RawHolding): SectorKey` 순수 함수 구현
    - 우선순위 1: 종목명 키워드 매칭 (아래 규칙, 대소문자 무시)
      - `미국지수`: "미국", "S&P", "나스닥", "NASDAQ", "QQQ", "DIA", "SPY", "다우", "1Q ", "RISE 미국"
      - `국내지수`: "코스피", "코스닥", "KOSPI", " 200", "코스피50", "코스닥150" — 단, "금현물" 포함 시 제외
      - `금`: "금현물", "KRX금", "GOLD"
      - `방산/테마`: "방산", "조선", "2차전지", "반도체", "K방산"
      - `채권/혼합`: "채권", "국채", "혼합", "금채"
      - `해외기타`: "유로", "유럽", "신흥국"
    - 우선순위 2: `단위 === 'USD'` → `미국지수`
    - 우선순위 3: 미매칭 → `개별주` (KRW) / `기타` (USD)
  - Notes: 금현물(0072R0)은 "KRX" 키워드 포함이지만 "금현물" 키워드가 먼저 매칭되어 `금`으로 분류됨. 키워드 체크 순서 중요.

- [x] Task 4: CSV 파서
  - File: `portfolio-dashboard/lib/csv-parser.ts`
  - Action: `parsePortfolioCSV(file: File): Promise<RawHolding[]>` 구현
    - papaparse `Papa.parse(file, { header: true, dynamicTyping: true })` 사용
    - 필수 컬럼 유효성 검사: `['계좌', '종목명', '종목번호', '수량', '평균단가', '단위']`
    - 누락 컬럼 시 `Error('유효하지 않은 CSV 형식: 필수 컬럼 누락 - {컬럼명}')` throw
    - 단위 값이 `KRW` 또는 `USD`가 아닐 경우 해당 행 스킵 후 콘솔 경고
    - 반환: `RawHolding[]` (섹터 태깅 전)
  - Notes: `dynamicTyping: true`로 수량/평균단가 자동 숫자 변환.

- [x] Task 5: 포트폴리오 계산기
  - File: `portfolio-dashboard/lib/portfolio-calculator.ts`
  - Action: 아래 순수 함수들 구현
    - `consolidateHoldings(holdings: HoldingWithMeta[]): ConsolidatedHolding[]`
      - 종목번호 기준 그룹핑
      - 가중평균 단가: `Σ(수량×평균단가KRW) / 총수량`
      - byAccount 배열 생성 및 ratio 계산
    - `calcAccountSummaries(holdings: HoldingWithMeta[]): AccountSummary[]`
      - 계좌별 evalAmount, todayGainAmount, todayGainRate 집계
    - `calcSectorAllocations(holdings: HoldingWithMeta[]): SectorAllocation[]`
      - 섹터별 evalAmount 합산, 전체 대비 ratio 계산
      - 색상 매핑: 미국지수 `#3B82F6`, 국내지수 `#10B981`, 금 `#F59E0B`, 방산/테마 `#EF4444`, 채권/혼합 `#8B5CF6`, 해외기타 `#06B6D4`, 개별주 `#F97316`, 기타 `#6B7280`
    - `calcPortfolioSummary(holdings: HoldingWithMeta[], exchangeRate: number): PortfolioSummary`
      - 전체 합산 지표 계산
  - Notes: 모든 금액 계산은 KRW 기준. USD 종목은 `evalAmount = currentPriceKRW × qty`.

- [x] Task 6: 환율 API Route
  - File: `portfolio-dashboard/app/api/exchange-rate/route.ts`
  - Action: GET handler 구현
    - `https://open.er-api.com/v6/latest/USD` 호출
    - `rates.KRW` 값 추출하여 반환: `{ rate: number, timestamp: string }`
    - 에러 시 fallback: `{ rate: 1370, timestamp: '...' }` (하드코딩 기본값)
    - `next: { revalidate: 3600 }` 옵션으로 1시간 캐싱
  - Notes: Next.js Route Handler의 `fetch` 캐싱 기능 활용.

- [x] Task 7: 국내 현재가 API Route
  - File: `portfolio-dashboard/app/api/price/route.ts`
  - Action: GET handler 구현, 쿼리 파라미터: `?codes=102110,069500,...`
    - 종목코드 배열을 받아 네이버 금융 polling API 병렬 호출
    - URL: `https://polling.finance.naver.com/api/realtime/domestic/stock/{code}`
    - **⚠️ 선행 조건**: 구현 전 반드시 실제 API 응답 구조 확인 필요. `curl "https://polling.finance.naver.com/api/realtime/domestic/stock/102110"` 로 실제 응답 필드명 검증할 것. 아래 필드명은 확인 후 수정:
    - 응답에서 현재가 필드 (예: `datas[0].closePrice`), 전일종가 필드 (예: `datas[0].closePrice - datas[0].compareToPreviousClosePrice`) 추출
    - 반환: `{ [code: string]: { currentPrice: number, prevClose: number } | null }`
    - 개별 종목 조회 실패 시 해당 종목만 `null` 처리 (전체 실패 방지), null 종목은 현재가를 평균단가로 fallback
  - Notes: `Promise.allSettled` 사용하여 일부 실패 허용. 비공식 API이므로 응답 구조 변경 가능성 염두에 둘 것.

- [x] Task 8: 미국 현재가 API Route
  - File: `portfolio-dashboard/app/api/price-us/route.ts`
  - Action: GET handler 구현, 쿼리 파라미터: `?tickers=AAPL,GOOGL,...`
    - Yahoo Finance API 병렬 호출
    - URL: `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d`
    - `meta.regularMarketPrice` (현재가), `meta.previousClose` (전일종가) 추출
    - 반환: `{ [ticker: string]: { currentPrice: number, prevClose: number } }`
    - 개별 종목 실패 시 null 처리
  - Notes: Yahoo Finance는 비공식 API이므로 User-Agent 헤더 설정 권장: `'Mozilla/5.0'`.

- [x] Task 9: 현재가 패처 오케스트레이터
  - File: `portfolio-dashboard/lib/price-fetcher.ts`
  - Action: `fetchPrices(holdings: RawHolding[]): Promise<Record<string, { currentPrice: number, prevClose: number } | null>>` 구현
    - **역할 분리 원칙**: 이 함수는 가격 조회만 담당. 금액 계산은 Task 5의 `portfolio-calculator.ts`에서 처리.
    - KRW 종목 코드 추출 → `/api/price?codes=...` 호출
    - USD 종목 티커 추출 → `/api/price-us?tickers=...` 호출
    - 두 호출 `Promise.all`로 병렬 처리
    - 반환: `{ [종목번호: string]: { currentPrice: number, prevClose: number } | null }` (종목번호 → 가격 맵)
    - null인 종목(조회 실패)은 호출자(`portfolio-calculator`)에서 평균단가를 현재가 fallback으로 처리
  - Notes: 계산 로직(KRW 환산, 손익 계산 등)은 이 파일에 포함하지 말 것. `portfolio-calculator.ts`의 `enrichHoldings(holdings, priceMap, exchangeRate): HoldingWithMeta[]` 함수가 최종 계산 담당.

- [x] Task 10: CSV 업로드 컴포넌트
  - File: `portfolio-dashboard/components/CsvUpload.tsx`
  - Action: `CsvUpload({ onUpload }: { onUpload: (holdings: RawHolding[]) => void })` 구현
    - shadcn/ui `Card` 컴포넌트 사용
    - 드래그&드롭 영역 (`onDragOver`, `onDrop` 핸들러)
    - 클릭으로 파일 선택 (`<input type="file" accept=".csv" hidden>`)
    - 업로드 상태: idle / loading / error
    - 에러 시 에러 메시지 표시 (shadcn/ui `Alert` 컴포넌트)
    - 성공 시 `onUpload(parsedHoldings)` 콜백 호출
    - 마지막 업로드 시각 표시: `마지막 업로드: HH:MM`
  - Notes: `parsePortfolioCSV` 함수 호출하여 파싱.

- [x] Task 11: 히어로 섹션 컴포넌트
  - File: `portfolio-dashboard/components/HeroSection.tsx`
  - Action: `HeroSection({ summary }: { summary: PortfolioSummary })` 구현
    - 2컬럼 그리드 레이아웃
    - 좌측: 오늘 손익 (금액 `text-4xl font-bold`, % `text-2xl`) — 양수 green, 음수 red
    - 우측: 총 평가금액 (`text-2xl`), 투자원금, 전체기간 수익률
    - 상단 헤더: `USD/KRW {exchangeRate}`, 마지막 업데이트 시각, 새로고침 버튼
  - Notes: 새로고침 버튼 클릭 시 부모 컴포넌트의 데이터 재조회 트리거.

- [x] Task 12: 계좌별 카드 컴포넌트
  - File: `portfolio-dashboard/components/AccountCards.tsx`
  - Action: `AccountCards({ accounts }: { accounts: AccountSummary[] })` 구현
    - shadcn/ui `Card` 5개를 `grid grid-cols-5` 레이아웃으로 배치
    - 각 카드: 계좌명, 평가금액 (억/만 단위 포맷), 오늘 손익 (금액+%)
    - 수익 색상: 양수 `text-green-600`, 음수 `text-red-500`
  - Notes: 금액 포맷 헬퍼: 1억 이상은 "1.2억", 1만 이상은 "1,234만".

- [x] Task 13: 섹터 파이차트 컴포넌트
  - File: `portfolio-dashboard/components/SectorChart.tsx`
  - Action: `SectorChart({ allocations }: { allocations: SectorAllocation[] })` 구현
    - Recharts `PieChart` + `Pie` + `Tooltip` + `Legend` 사용
    - 각 섹터 색상은 `SectorAllocation.color` 사용
    - 범례: 섹터명 + % 표시
    - 빈 데이터 시 "데이터 없음" 표시
  - Notes: `ResponsiveContainer width="100%" height={300}` 사용.

- [x] Task 14: 종목별 수익률 리스트 컴포넌트
  - File: `portfolio-dashboard/components/StockList.tsx`
  - Action: `StockList({ holdings, onSelect }: { holdings: ConsolidatedHolding[], onSelect: (h: ConsolidatedHolding) => void })` 구현
    - shadcn/ui `Table` 컴포넌트 사용
    - 컬럼: 종목명 / 섹터뱃지 / 오늘수익률 / 오늘손익 / 평가금액 / 전체수익률
    - 오늘수익률 기준 내림차순 정렬 (기본)
    - 행 클릭 시 `onSelect(holding)` 호출
    - USD 종목 평가금액: "₩2,823K ($2,056)" 형식
    - 수익률 색상: 양수 green, 음수 red, 0 gray
    - "더보기" 없이 전체 표시 (종목 수 ~18개로 적음)
  - Notes: 섹터 뱃지는 shadcn/ui `Badge` 컴포넌트 + 섹터별 색상 적용.

- [x] Task 15: 종목 드릴다운 드로어
  - File: `portfolio-dashboard/components/StockDetailDrawer.tsx`
  - Action: `StockDetailDrawer({ holding, open, onClose }: { holding: ConsolidatedHolding | null, open: boolean, onClose: () => void })` 구현
    - shadcn/ui `Sheet` (사이드 드로어) 컴포넌트 사용
    - 헤더: 종목명, 종목코드, 섹터뱃지
    - 요약: 총 보유수량, 가중평균단가, 총 평가금액, 오늘 수익률, 전체 수익률
    - 계좌별 분포 테이블: 계좌명 / 수량 / 평가금액 / 비중(진행바)
    - 비중 진행바: shadcn/ui `Progress` 컴포넌트
  - Notes: `holding`이 null일 때 렌더링 스킵.

- [x] Task 16: 메인 페이지 오케스트레이션
  - File: `portfolio-dashboard/app/page.tsx`
  - Action: 전체 데이터 흐름 및 레이아웃 구현
    - 상태: `rawHoldings`, `holdingsWithMeta`, `exchangeRate`, `loading`, `error`, `selectedHolding`
    - CSV 업로드 → 파싱 → 섹터태깅 → 현재가조회 → 계산 순서로 처리
    - `useMemo`로 `consolidated`, `accountSummaries`, `sectorAllocations`, `portfolioSummary` 파생
    - 레이아웃 (CSV 미업로드 시): CsvUpload 컴포넌트 중앙 표시
    - 레이아웃 (업로드 후): HeroSection → AccountCards → 2컬럼(SectorChart | StockList) → 하단 전체기간 수익
    - 새로고침: 현재 `rawHoldings`로 현재가 재조회
    - StockDetailDrawer를 `selectedHolding` 상태로 제어
  - Notes: 로딩 중 shadcn/ui `Skeleton` 컴포넌트로 로딩 UI 처리.

- [x] Task 17: 샘플 CSV 파일 생성
  - File: `portfolio-dashboard/data/sample.csv`
  - Action: Notes의 샘플 데이터를 CSV 파일로 저장 (juno님 실제 보유종목 데이터 기반)
  - Notes: 개발/테스트용. 앱 내 "샘플 데이터 불러오기" 버튼으로 연결 가능.

### Acceptance Criteria

- [x] AC 1: Given 올바른 형식의 CSV 파일(컬럼: 계좌,종목명,종목번호,수량,평균단가,단위)을 업로드하면, 파싱된 보유종목 목록이 화면에 로드된다
- [x] AC 2: Given 필수 컬럼이 누락된 CSV를 업로드하면, "유효하지 않은 CSV 형식" 에러 메시지가 업로드 영역에 표시된다
- [x] AC 3: Given 보유종목이 로드되면, TIGER 200은 `국내지수`, KODEX 미국S&P500은 `미국지수`, TIGER KRX금현물은 `금`으로 자동 태깅된다
- [x] AC 4: Given 보유종목이 로드되면, 국내 KRW 종목의 현재가가 네이버 금융 API를 통해 조회되고 종목 리스트에 표시된다
- [x] AC 5: Given 보유종목이 로드되면, AAPL/GOOGL 등 USD 종목의 현재가가 Yahoo Finance API를 통해 조회된다
- [x] AC 6: Given 데이터가 로드되면, 헤더에 당일 USD/KRW 환율이 표시된다 (예: `USD/KRW 1,373`)
- [x] AC 7: Given 모든 데이터가 준비되면, 전체 오늘 손익(금액+%)이 최상단 히어로 섹션에 `text-4xl` 이상 크기로 표시되며, 양수는 초록색, 음수는 빨간색으로 표시된다
- [x] AC 8: Given 모든 데이터가 준비되면, ISA/연금저축A/연금저축B/CMA/IRP 5개 계좌 카드가 각각 오늘 손익과 평가금액을 표시한다
- [x] AC 9: Given 모든 데이터가 준비되면, 섹터별 비중 파이차트가 섹터명과 % 레전드와 함께 표시된다
- [x] AC 10: Given TIGER 200이 ISA/연금저축A/연금저축B/CMA/IRP 5개 계좌에 분산 보유된 경우, 종목 리스트에는 1개 통합 행으로 표시되고 수량 합계가 정확히 계산된다
- [x] AC 11: Given 종목 리스트에서 TIGER 200 행을 클릭하면, 계좌별 보유 수량과 비중을 보여주는 사이드 드로어가 열린다
- [x] AC 12: Given CMA 계좌의 AAPL 평가금액이 표시될 때, `₩2,823K ($2,056)` 형식으로 원화 메인 + 달러 괄호 병기로 표시된다
- [x] AC 13: Given 모든 데이터가 준비되면, 전체기간 총 수익금액과 수익률 %가 페이지 하단에 표시된다
- [x] AC 14: Given 특정 종목의 현재가 API 조회가 실패하면, 해당 종목의 현재가는 평균단가로 fallback 처리되고 종목 리스트에 `현재가 조회 실패` 표시가 나타나며 나머지 종목의 대시보드는 정상 표시된다

## Additional Context

### Dependencies

**npm 패키지:**
- `next@15.x` — 프레임워크
- `react@18.x`, `react-dom@18.x`
- `typescript`, `@types/react`, `@types/node`
- `tailwindcss@3.x`, `postcss`, `autoprefixer`
- `recharts` — 파이차트
- `papaparse`, `@types/papaparse` — CSV 파싱
- `shadcn/ui` 컴포넌트: Card, Badge, Table, Sheet, Progress, Skeleton, Alert

**외부 서비스 (무료, 키 불필요):**
- 네이버 금융 polling API — 국내 현재가
- Yahoo Finance API v8 — 미국 현재가
- open.er-api.com — USD/KRW 환율

### Testing Strategy

**유닛 테스트 (Vitest):**
- `lib/sector-tagger.ts`: 각 섹터 키워드 매핑 케이스 (TIGER 200 → 국내지수, KODEX 미국S&P500 → 미국지수, TIGER KRX금현물 → 금 등)
- `lib/portfolio-calculator.ts`: 동일 종목 통합, 가중평균 단가 계산, 섹터 비중 계산

**수동 테스트:**
1. `data/sample.csv` 업로드 → 전체 플로우 동작 확인
2. 잘못된 CSV 업로드 → 에러 메시지 확인
3. TIGER 200 클릭 → 드릴다운 드로어 5개 계좌 표시 확인
4. 헤더 환율 표시 확인
5. USD 종목 원화/달러 병기 확인

### Notes

**보유종목 샘플 데이터 (CSV 형식):**
```
계좌,종목명,종목번호,수량,평균단가,단위
ISA,1Q 미국S&P500,0026S0,161,12032,KRW
ISA,하나금융지주,086790,13,85554,KRW
ISA,TIGER 200,102110,33,82006,KRW
ISA,TIGER 유로스탁스배당30,245350,150,17727,KRW
ISA,KODEX 미국S&P500,379800,286,20285,KRW
ISA,KODEX 미국나스닥100,379810,201,21334,KRW
ISA,RISE 미국AI테크액티브,495940,120,13246,KRW
연금저축A,TIGER KRX금현물,0072R0,299,13491,KRW
연금저축A,KODEX K방산TOP10,0080G0,423,11643,KRW
연금저축A,ACE 미국10년국채액티브,0085P0,258,10809,KRW
연금저축A,KODEX 200,069500,24,43778,KRW
연금저축A,TIGER 200,102110,166,71092,KRW
연금저축A,PLUS 코스피50,122090,251,39881,KRW
연금저축A,KODEX 미국S&P500,379800,199,20934,KRW
연금저축A,KODEX 미국나스닥100,379810,141,22827,KRW
연금저축A,TIGER 조선TOP10,494670,201,28105,KRW
연금저축B,TIGER KRX금현물,0072R0,83,16223,KRW
연금저축B,KODEX 방산TOP10,0080G0,9,13238,KRW
연금저축B,KODEX 200,069500,68,53112,KRW
연금저축B,TIGER 200,102110,141,69987,KRW
연금저축B,PLUS 코스피50,122090,104,42127,KRW
연금저축B,TIGER 다우존스30,245340,52,31411,KRW
연금저축B,KODEX 미국나스닥100,379810,70,21874,KRW
연금저축B,KODEX 방산TOP10,0080G0,50,12695,KRW
CMA,TIGER 200,102110,38,77581,KRW
CMA,PLUS 코스피50,122090,17,40400,KRW
CMA,AAPL,AAPL,8,257,USD
CMA,GOOGL,GOOGL,9,331,USD
CMA,QQQM,QQQM,39,250,USD
CMA,DIA,DIA,8,466,USD
CMA,SPYM,SPYM,114,79,USD
IRP,PLUS 금채권혼합,0138Y0,129,10549,KRW
IRP,KODEX 200,069500,30,43690,KRW
IRP,TIGER 200,102110,45,74669,KRW
IRP,PLUS 코스피50,122090,68,50436,KRW
IRP,TIGER 미국나스닥100,379810,13,142675,KRW
IRP,KODEX 200미국채혼합,284430,56,18610,KRW
IRP,TIGER 미국S&P500,560750,138,21800,KRW
IRP,KODEX 삼성전자채권혼합,448330,33,14430,KRW
```

**화면 레이아웃 우선순위:**
1. 오늘 손익 (금액 + %) — 히어로 섹션, 가장 크게
2. 총 평가금액 + 전체기간 수익
3. 계좌별 오늘 손익 카드 5개
4. 섹터 비중 파이차트 + 종목별 수익률 리스트 (좌우 분할)
5. 전체기간 수익 상세 (하단)
