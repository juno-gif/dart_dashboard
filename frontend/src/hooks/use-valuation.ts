'use client'
import { useQuery } from '@tanstack/react-query'
import { getValuation } from '@/lib/api'
import type { ValuationData } from '@/lib/api'

export function useValuation(corpCode: string | null) {
  return useQuery<ValuationData>({
    queryKey: ['valuation', corpCode],
    queryFn: () => getValuation(corpCode!),
    enabled: !!corpCode,
    staleTime: 5 * 60_000, // 5분 캐시 (rate limit 후 재시도 대응)
  })
}
