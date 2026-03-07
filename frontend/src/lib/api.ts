/**
 * FastAPI 호출 함수 모음 (모든 API 호출은 이 파일 경유 필수)
 * 컴포넌트 내 직접 fetch 금지 — architecture.md Enforcement Guidelines #2
 */
import type { Company, FinancialStatement } from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { headers: JSON_HEADERS })
  if (!res.ok) {
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.json()
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.json()
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'PUT',
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.json()
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'PATCH',
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.json()
}

export async function apiDelete(path: string): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'DELETE',
    headers: JSON_HEADERS,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
}

export async function apiPostBlob(path: string): Promise<Blob> {
  const res = await fetch(`${API_URL}${path}`, { method: 'POST' })
  if (!res.ok) {
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
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
  years = 5,
  type = 'pl'
): Promise<FinancialStatement[]> {
  return apiGet<FinancialStatement[]>(
    `/api/v1/companies/${corpCode}/financials?years=${years}&type=${type}`
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

// ── 분석 세트 ───────────────────────────────────────────
export interface AnalysisSetData {
  id: string
  name: string
  owner_id: string | null
  company_codes: string[]
  share_token: string | null
  created_at: string
  updated_at: string
}

export async function createAnalysisSet(data: {
  name: string
  company_codes: string[]
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
  data: { name?: string; company_codes?: string[] }
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
