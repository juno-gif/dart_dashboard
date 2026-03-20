'use client'
import { useQuery } from '@tanstack/react-query'
import { getValuation } from '@/lib/api'
import type { ValuationData } from '@/lib/api'

export function useValuation(corpCode: string | null) {
  return useQuery<ValuationData>({
    queryKey: ['valuation', corpCode],
    queryFn: () => getValuation(corpCode!),
    enabled: !!corpCode,
    staleTime: 60 * 60_000, // 1시간 캐시
  })
}
