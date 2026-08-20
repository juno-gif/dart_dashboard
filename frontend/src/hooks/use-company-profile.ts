'use client'
import { useQuery } from '@tanstack/react-query'
import { getCompanyProfile } from '@/lib/api'
import type { CompanyProfile } from '@/types'

export function useCompanyProfile(corpCode: string | null) {
  return useQuery<CompanyProfile>({
    queryKey: ['company-profile', corpCode],
    queryFn: () => getCompanyProfile(corpCode!),
    enabled: !!corpCode,
    staleTime: 30 * 60_000, // 30분 캐시 — 설립일/대표이사 등은 자주 안 바뀜
    gcTime: 60 * 60_000,
    retry: false,
  })
}
