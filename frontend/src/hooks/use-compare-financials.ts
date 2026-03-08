'use client'
import { useQuery } from '@tanstack/react-query'
import { getCompareFinancials } from '@/lib/api'
import type { FinancialStatement } from '@/types'

export function useCompareFinancials(
  codes: string[],
  years = 10,
  type = 'pl'
) {
  const sortedCodesStr = [...codes].sort().join(',')
  return useQuery<FinancialStatement[]>({
    queryKey: ['compare', sortedCodesStr, { years, type }],
    queryFn: () => getCompareFinancials(codes, years, type),
    enabled: codes.length >= 2,
    staleTime: 5 * 60_000,
  })
}
