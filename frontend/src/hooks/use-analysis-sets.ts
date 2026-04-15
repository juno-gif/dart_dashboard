'use client'

/**
 * 분석 세트 훅 (Builder 전용)
 * Story 3.1: 분석 세트 목록 조회, 저장, 불러오기
 * Story 3.2: 분석 세트 수정, 삭제
 * Story 4.1: 공유 링크 생성
 * [Source: architecture.md - Frontend Architecture - TanStack Query]
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { createAnalysisSet, deleteAnalysisSet, getAnalysisSet, listAnalysisSets, shareAnalysisSet, updateAnalysisSet } from '@/lib/api'
import type { AnalysisSetData } from '@/lib/api'

export function useAnalysisSets() {
  const queryClient = useQueryClient()

  const { data: analysisSets, isLoading } = useQuery({
    queryKey: ['analysis-sets'],
    queryFn: listAnalysisSets,
  })

  const saveSet = useMutation({
    mutationFn: ({ name, companyCodes, groupId }: { name: string; companyCodes: string[]; groupId?: string | null }) =>
      createAnalysisSet({ name, company_codes: companyCodes, group_id: groupId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
      toast.success('분석 세트가 저장되었습니다', { duration: 3000 })
    },
  })

  const loadSet = useMutation({
    mutationFn: (id: string) => getAnalysisSet(id),
  })

  const updateSet = useMutation({
    mutationFn: ({ id, name, companyCodes, groupId }: { id: string; name?: string; companyCodes?: string[]; groupId?: string | null }) =>
      updateAnalysisSet(id, { name, company_codes: companyCodes, group_id: groupId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
      toast.success('변경 사항이 저장되었습니다', { duration: 3000 })
    },
  })

  const deleteSet = useMutation({
    mutationFn: (id: string) => deleteAnalysisSet(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
      toast.success('분석 세트가 삭제되었습니다', { duration: 3000 })
    },
  })

  const shareSet = useMutation({
    mutationFn: (id: string) => shareAnalysisSet(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
    },
  })

  return { analysisSets, isLoading, saveSet, loadSet, updateSet, deleteSet, shareSet }
}

export type { AnalysisSetData }
