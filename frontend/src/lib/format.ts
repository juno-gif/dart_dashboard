/**
 * 금액·퍼센트 포맷 유틸리티
 * DB는 원 단위 BIGINT, 화면은 억/조 단위 표시
 * formatKRW()는 모든 금액 표시에 사용 — 컴포넌트 내 직접 변환 금지
 * [Source: architecture.md - 금액 단위 변환 유틸]
 */

export function formatKRW(amount: number): string {
  const abs = Math.abs(amount)
  const sign = amount < 0 ? '-' : ''

  if (abs >= 1_000_000_000_000) {
    return `${sign}₩${(abs / 1e12).toFixed(1)}조`
  }
  if (abs >= 100_000_000) {
    return `${sign}₩${(abs / 1e8).toFixed(0)}억`
  }
  if (abs >= 1_000_000) {
    return `${sign}₩${(abs / 1e6).toFixed(1)}백만`
  }
  return `${sign}₩${abs.toLocaleString()}원`
}

export function formatPercent(value: number, digits = 1): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}%`
}

const REPRT_SUFFIX: Record<string, string> = {
  '11012': '(~2Q)',
  '11013': '(~1Q)',
  '11014': '(~3Q)',
}

/** bsns_year + reprt_code → "2025" 또는 "2025(~3Q)" 형태 레이블 */
export function formatYearLabel(year: string, reprtCode: string): string {
  const suffix = REPRT_SUFFIX[reprtCode] ?? ''
  return suffix ? `${year}${suffix}` : year
}

export function formatDate(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}
