/**
 * FastAPI 호출 함수 모음 (모든 API 호출은 이 파일 경유 필수)
 * 컴포넌트 내 직접 fetch 금지 — architecture.md Enforcement Guidelines #2
 *
 * 완전 구현: Story 1.3 (기업 검색), Story 1.4 (재무 데이터 조회)
 * Story 2.1: 토큰 자동 첨부 추가
 * Story 2.2: getUserProfile 추가, 401 리디렉션 처리
 * Story 2.3: 팀원 초대/역할관리/비활성화/목록 함수 추가
 * Story 3.2: updateAnalysisSet, deleteAnalysisSet, apiDelete 추가
 * Story 4.1: shareAnalysisSet, ShareResponse 추가
 * Story 6.2: requestAiSummary, AiSummaryResult 추가
 */
import type { Company, FinancialStatement, UserProfile } from '@/types'
import { supabase } from '@/lib/supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getToken(): Promise<string | undefined> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token
}

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const resolvedToken = token ?? await getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (resolvedToken) headers['Authorization'] = `Bearer ${resolvedToken}`

  const res = await fetch(`${API_URL}${path}`, { headers })
  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.json()
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  token?: string
): Promise<T> {
  const resolvedToken = token ?? await getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (resolvedToken) headers['Authorization'] = `Bearer ${resolvedToken}`

  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.json()
}

// ── Story 1.3: 기업 검색 ──────────────────────────────
export async function searchCompanies(q: string): Promise<Company[]> {
  return apiGet<Company[]>(`/api/v1/companies/search?q=${encodeURIComponent(q)}&limit=8`)
}

// ── Story 1.4: 재무 데이터 조회 ───────────────────────
export async function getFinancials(
  corpCode: string,
  years = 5,
  type = 'pl'
): Promise<FinancialStatement[]> {
  return apiGet<FinancialStatement[]>(
    `/api/v1/companies/${corpCode}/financials?years=${years}&type=${type}`
  )
}

// ── Story 1.5: 다중 기업 비교 ─────────────────────────
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

export async function apiPut<T>(
  path: string,
  body: unknown,
  token?: string
): Promise<T> {
  const resolvedToken = token ?? await getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (resolvedToken) headers['Authorization'] = `Bearer ${resolvedToken}`

  const res = await fetch(`${API_URL}${path}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.json()
}

export async function apiPatch<T>(
  path: string,
  body: unknown,
  token?: string
): Promise<T> {
  const resolvedToken = token ?? await getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (resolvedToken) headers['Authorization'] = `Bearer ${resolvedToken}`

  const res = await fetch(`${API_URL}${path}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.json()
}

// ── Story 2.2: 사용자 프로필 조회 ─────────────────────
export async function getUserProfile(): Promise<UserProfile> {
  return apiGet<UserProfile>('/api/v1/users/me')
}

// ── Story 2.3: 팀원 초대 및 역할 관리 ─────────────────
export interface InviteUserRequest {
  email: string
  role: 'builder' | 'live_viewer' | 'read_only'
}

export async function listUsers(): Promise<UserProfile[]> {
  return apiGet<UserProfile[]>('/api/v1/users')
}

export async function inviteUser(data: InviteUserRequest): Promise<{ message: string; email: string; role: string }> {
  return apiPost('/api/v1/users/invite', data)
}

export async function updateUserRole(userId: string, role: string): Promise<UserProfile> {
  return apiPatch<UserProfile>(`/api/v1/users/${userId}/role`, { role })
}

export async function deactivateUser(userId: string): Promise<{ message: string; user_id: string }> {
  return apiPost(`/api/v1/users/${userId}/deactivate`, {})
}

// ── Story 3.1: 분석 세트 저장 및 불러오기 ─────────────
export interface AnalysisSetData {
  id: string
  name: string
  owner_id: string
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

// ── Story 3.2: 분석 세트 수정 및 삭제 ─────────────────
export async function apiDelete(path: string, token?: string): Promise<void> {
  const resolvedToken = token ?? await getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (resolvedToken) headers['Authorization'] = `Bearer ${resolvedToken}`

  const res = await fetch(`${API_URL}${path}`, { method: 'DELETE', headers })
  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
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

// ── Story 4.1: 공유 링크 생성 ─────────────────────────
export interface ShareResponse {
  share_token: string
  share_url: string
}

export async function shareAnalysisSet(id: string): Promise<ShareResponse> {
  return apiPost<ShareResponse>(`/api/v1/analysis-sets/${id}/share`, {})
}

// ── Story 3.3: 신규 데이터 상태 확인 ──────────────────
export async function getNewDataStatus(codes: string[]): Promise<{ new_data_codes: string[] }> {
  if (codes.length === 0) return { new_data_codes: [] }
  return apiGet<{ new_data_codes: string[] }>(
    `/api/v1/companies/new-data-status?codes=${encodeURIComponent(codes.join(','))}`
  )
}

// ── Story 5.1: 비상장사 수기 입력 ──────────────────────
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

export async function createManualCompany(data: ManualCompanyCreateRequest): Promise<import('@/types').Company> {
  return apiPost<import('@/types').Company>('/api/v1/companies/manual', data)
}

// ── Story 5.2: Admin 비상장사 재무 데이터 조회·수정 ──────
export interface ManualCompanyFinancialsResponse {
  corp_code: string
  company_name: string
  financials: ManualFinancialEntry[]
}

export async function getManualCompanyFinancials(corpCode: string): Promise<ManualCompanyFinancialsResponse> {
  return apiGet<ManualCompanyFinancialsResponse>(`/api/v1/companies/${corpCode}/manual`)
}

export async function updateManualCompany(corpCode: string, data: ManualCompanyCreateRequest): Promise<import('@/types').Company> {
  return apiPut<import('@/types').Company>(`/api/v1/companies/${corpCode}/manual`, data)
}

// ── Story 6.1: PPT 내보내기 ────────────────────────────
export async function apiPostBlob(path: string): Promise<Blob> {
  const token = await getToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers,
  })
  if (!res.ok) {
    if (res.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login'
      throw new Error('Unauthorized')
    }
    const error = await res.json().catch(() => ({
      error: 'UNKNOWN_ERROR',
      message: 'Unknown error occurred',
      status_code: res.status,
    }))
    throw error
  }
  return res.blob()
}

export async function exportAnalysisSetPpt(setId: string): Promise<Blob> {
  return apiPostBlob(`/api/v1/analysis-sets/${setId}/export/ppt`)
}

// ── Story 6.2: AI 재무 요약 ────────────────────────────
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
