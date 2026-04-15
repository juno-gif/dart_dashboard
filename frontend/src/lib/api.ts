/**
 * FastAPI 호출 함수 모음 (모든 API 호출은 이 파일 경유 필수)
 * 컴포넌트 내 직접 fetch 금지 — architecture.md Enforcement Guidelines #2
 */
import type { Company, FinancialStatement } from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

// FastAPI는 에러를 { "detail": { "error": "...", "message": "..." } } 형태로 래핑
// detail이 객체인 경우 언래핑해서 컴포넌트에서 바로 error/message 접근 가능하게 함
async function parseApiError(res: Response): Promise<never> {
  const fallback = { error: 'UNKNOWN_ERROR', message: 'Unknown error occurred', status_code: res.status }
  const json = await res.json().catch(() => fallback)
  const detail = json?.detail
  throw (detail && typeof detail === 'object' && !Array.isArray(detail)) ? detail : json
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: JSON_HEADERS })
  if (!res.ok) return parseApiError(res)
  return res.json()
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  })
  if (!res.ok) return parseApiError(res)
  return res.json()
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'PUT',
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  })
  if (!res.ok) return parseApiError(res)
  return res.json()
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'PATCH',
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  })
  if (!res.ok) return parseApiError(res)
  return res.json()
}

export async function apiDelete(path: string): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'DELETE',
    headers: JSON_HEADERS,
  })
  if (!res.ok) return parseApiError(res)
}

export async function apiPostBlob(path: string): Promise<Blob> {
  const res = await fetch(`${API_URL}${path}`, { method: 'POST' })
  if (!res.ok) return parseApiError(res)
  return res.blob()
}

// ── 서버 헬스체크 ───────────────────────────────────────
export async function checkHealth(): Promise<boolean> {
  const res = await fetch(`${API_URL}/api/v1/health`)
  return res.ok
}

// ── 기업 검색 ──────────────────────────────────────────
export async function searchCompanies(q: string): Promise<Company[]> {
  return apiGet<Company[]>(`/api/v1/companies/search?q=${encodeURIComponent(q)}&limit=8`)
}

// ── 재무 데이터 조회 ────────────────────────────────────
export async function getFinancials(
  corpCode: string,
  years = 10,
  type = 'pl',
  fsDivParam?: string
): Promise<FinancialStatement[]> {
  const params = new URLSearchParams({ years: String(years), type })
  if (fsDivParam) params.set('fs_div', fsDivParam)
  return apiGet<FinancialStatement[]>(
    `/api/v1/companies/${corpCode}/financials?${params}`
  )
}

// ── 다중 기업 비교 ──────────────────────────────────────
export async function getCompareFinancials(
  codes: string[],
  years = 5,
  type = 'pl'
): Promise<FinancialStatement[]> {
  const sortedCodes = [...codes].sort().join(',')
  return apiGet<FinancialStatement[]>(
    `/api/v1/companies/compare?codes=${encodeURIComponent(sortedCodes)}&years=${years}&type=${type}`
  )
}

// ── 기업 배치 조회 ──────────────────────────────────────
export async function getCompaniesByCodes(codes: string[]): Promise<Company[]> {
  if (codes.length === 0) return []
  return apiGet<Company[]>(`/api/v1/companies/by-codes?codes=${encodeURIComponent(codes.join(','))}`)
}

// ── 분석 그룹 ───────────────────────────────────────────
export interface AnalysisGroupData {
  id: string
  name: string
  display_order: number
  created_at: string
  updated_at: string
}

export async function listAnalysisGroups(): Promise<AnalysisGroupData[]> {
  return apiGet<AnalysisGroupData[]>('/api/v1/analysis-groups')
}

export async function createAnalysisGroup(name: string): Promise<AnalysisGroupData> {
  return apiPost<AnalysisGroupData>('/api/v1/analysis-groups', { name })
}

export async function updateAnalysisGroup(id: string, data: { name?: string; display_order?: number }): Promise<AnalysisGroupData> {
  return apiPatch<AnalysisGroupData>(`/api/v1/analysis-groups/${id}`, data)
}

export async function deleteAnalysisGroup(id: string): Promise<void> {
  return apiDelete(`/api/v1/analysis-groups/${id}`)
}

// ── 분석 세트 ───────────────────────────────────────────
export interface AnalysisSetData {
  id: string
  name: string
  owner_id: string | null
  company_codes: string[]
  share_token: string | null
  group_id: string | null
  created_at: string
  updated_at: string
}

export async function createAnalysisSet(data: {
  name: string
  company_codes: string[]
  group_id?: string | null
}): Promise<AnalysisSetData> {
  return apiPost<AnalysisSetData>('/api/v1/analysis-sets', data)
}

export async function listAnalysisSets(): Promise<AnalysisSetData[]> {
  return apiGet<AnalysisSetData[]>('/api/v1/analysis-sets')
}

export async function getAnalysisSet(id: string): Promise<AnalysisSetData> {
  return apiGet<AnalysisSetData>(`/api/v1/analysis-sets/${id}`)
}

export async function updateAnalysisSet(
  id: string,
  data: { name?: string; company_codes?: string[]; group_id?: string | null }
): Promise<AnalysisSetData> {
  return apiPatch<AnalysisSetData>(`/api/v1/analysis-sets/${id}`, data)
}

export async function deleteAnalysisSet(id: string): Promise<void> {
  return apiDelete(`/api/v1/analysis-sets/${id}`)
}

// ── 공유 링크 ───────────────────────────────────────────
export interface ShareResponse {
  share_token: string
  share_url: string
}

export async function shareAnalysisSet(id: string): Promise<ShareResponse> {
  return apiPost<ShareResponse>(`/api/v1/analysis-sets/${id}/share`, {})
}

// ── 신규 데이터 상태 확인 ───────────────────────────────
export async function getNewDataStatus(codes: string[]): Promise<{ new_data_codes: string[] }> {
  if (codes.length === 0) return { new_data_codes: [] }
  return apiGet<{ new_data_codes: string[] }>(
    `/api/v1/companies/new-data-status?codes=${encodeURIComponent(codes.join(','))}`
  )
}

// ── 비상장사 수기 입력 ──────────────────────────────────
export interface ManualFinancialEntry {
  bsns_year: string
  revenue: number | null
  operating_profit: number | null
  net_income: number | null
}

export interface ManualCompanyCreateRequest {
  company_name: string
  financials: ManualFinancialEntry[]
}

export async function createManualCompany(data: ManualCompanyCreateRequest): Promise<Company> {
  return apiPost<Company>('/api/v1/companies/manual', data)
}

export interface ManualCompanyFinancialsResponse {
  corp_code: string
  company_name: string
  financials: ManualFinancialEntry[]
}

export async function getManualCompanyFinancials(corpCode: string): Promise<ManualCompanyFinancialsResponse> {
  return apiGet<ManualCompanyFinancialsResponse>(`/api/v1/companies/${corpCode}/manual`)
}

export async function updateManualCompany(corpCode: string, data: ManualCompanyCreateRequest): Promise<Company> {
  return apiPut<Company>(`/api/v1/companies/${corpCode}/manual`, data)
}

// ── PPT 내보내기 ────────────────────────────────────────
export async function exportAnalysisSetPpt(setId: string): Promise<Blob> {
  return apiPostBlob(`/api/v1/analysis-sets/${setId}/export/ppt`)
}

// ── Valuation (PBR/PER) ─────────────────────────────────
export interface ValuationData {
  current_pbr: number | null
  current_per: number | null
  yearly: { year: string; pbr: number; per: number | null }[]
}

export async function getValuation(corpCode: string, years = 10): Promise<ValuationData> {
  return apiGet<ValuationData>(`/api/v1/companies/${corpCode}/valuation?years=${years}`)
}

// ── 데이터 재수집 ────────────────────────────────────────
export async function syncCompany(corpCode: string, years = 10): Promise<void> {
  await apiPost(`/api/v1/sync/company/${corpCode}?years=${years}`, {})
}

// ── AI 재무 요약 ────────────────────────────────────────
export interface AiSummaryResult {
  type: 'summary' | 'answer'
  content: string
}

export async function requestAiSummary(
  setId: string,
  question?: string
): Promise<AiSummaryResult> {
  return apiPost<AiSummaryResult>(
    `/api/v1/analysis-sets/${setId}/ai-summary`,
    { question: question ?? null }
  )
}
