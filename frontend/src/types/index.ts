/**
 * 전역 타입 정의
 * JSON 필드명 규칙: snake_case 통일 (camelCase 변환 금지)
 * [Source: architecture.md - JSON 필드 네이밍]
 */

// ── 기업 (Company) ─────────────────────────────────────
export interface Company {
  corp_code: string
  company_name: string
  stock_code: string | null
  is_listed: boolean
  created_at: string
}

export interface CompanySearchResult {
  corp_code: string
  company_name: string
  stock_code: string | null
  is_listed: boolean
}

// ── 재무 데이터 (Financial Statement) ──────────────────
export interface FinancialStatement {
  id: string
  corp_code: string
  bsns_year: string
  reprt_code: string
  fs_div: string
  account_key: string
  account_nm: string | null
  amount: number // 원 단위 BIGINT — formatKRW()로만 변환
  synced_at: string
  is_fallback?: boolean // CFS 요청 시 해당 연도 CFS 없어 OFS로 폴백된 경우 true
}

export type FinancialType = 'pl' | 'bs' | 'cf'

// ── 분석 세트 (Analysis Set) ───────────────────────────
export interface AnalysisSet {
  id: string
  name: string
  owner_id: string
  company_codes: string[]
  config: Record<string, unknown> | null
  share_token: string | null
  updated_at: string
  created_at: string
}

// ── 사용자 (User Profile) ──────────────────────────────
export type UserRole = 'admin' | 'builder' | 'live_viewer' | 'read_only'

export interface UserProfile {
  id: string
  role: UserRole
  display_name: string | null
}

// ── API 에러 응답 ──────────────────────────────────────
export interface ApiError {
  error: string
  message: string
  status_code: number
  cached_at?: string
}
