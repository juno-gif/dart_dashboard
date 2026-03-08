'use client'
import { useQuery } from '@tanstack/react-query'
import { getFinancials } from '@/lib/api'
import type { FinancialStatement } from '@/types'

export function useFinancialData(
  corpCode: string | null,
  years = 10,
  type = 'pl',
  fsDivParam = 'ALL'
) {
  return useQuery<FinancialStatement[]>({
    queryKey: ['financials', corpCode, { years, type, fsDivParam }],
    queryFn: () => getFinancials(corpCode!, years, type, fsDivParam),
    enabled: !!corpCode,
    staleTime: 5 * 60_000, // 5분 캐시
  })
}
