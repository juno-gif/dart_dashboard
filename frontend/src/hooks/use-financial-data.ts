'use client'
import { useQuery } from '@tanstack/react-query'
import { getFinancials } from '@/lib/api'
import type { FinancialStatement } from '@/types'

const QUICK_YEARS = 3

export function useFinancialData(
  corpCode: string | null,
  years = 10,
  type = 'pl',
  fsDivParam = 'ALL'
) {
  const needsTwoStage = years > QUICK_YEARS

  // Stage 1: 최근 3년 빠른 로딩
  const quickQuery = useQuery<FinancialStatement[]>({
    queryKey: ['financials', corpCode, { years: QUICK_YEARS, type, fsDivParam }],
    queryFn: () => getFinancials(corpCode!, QUICK_YEARS, type, fsDivParam),
    enabled: !!corpCode && needsTwoStage,
    staleTime: 30 * 60_000,
    gcTime: 60 * 60_000,
  })

  // Stage 2: 전체 데이터 (Stage 1 성공 후 실행 — 캐시 히트 시 즉시)
  const fullQuery = useQuery<FinancialStatement[]>({
    queryKey: ['financials', corpCode, { years, type, fsDivParam }],
    queryFn: () => getFinancials(corpCode!, years, type, fsDivParam),
    enabled: !!corpCode && (!needsTwoStage || quickQuery.isSuccess),
    staleTime: 30 * 60_000,
    gcTime: 60 * 60_000,
  })

  if (!needsTwoStage) {
    // 단일 쿼리 경로 (years ≤ 3)
    return {
      data: fullQuery.data ?? [],
      isLoading: fullQuery.isPending,
      isLoadingMore: false,
      error: fullQuery.error,
    }
  }

  // 두 단계 경로
  const isLoading = quickQuery.isPending                          // 첫 데이터 아직 없음
  const isLoadingMore = quickQuery.isSuccess && fullQuery.isPending  // 최근 3년은 표시 중, 전체 로딩 중
  const data = fullQuery.data ?? quickQuery.data ?? []
  const error = quickQuery.error ?? fullQuery.error

  return { data, isLoading, isLoadingMore, error }
}
