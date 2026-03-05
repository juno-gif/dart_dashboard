/**
 * FastAPI 호출 함수 모음 (모든 API 호출은 이 파일 경유 필수)
 * 컴포넌트 내 직접 fetch 금지 — architecture.md Enforcement Guidelines #2
 *
 * 완전 구현: Story 1.3 (기업 검색), Story 1.4 (재무 데이터 조회)
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, { headers })
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

export async function apiPost<T>(
  path: string,
  body: unknown,
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers,
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
