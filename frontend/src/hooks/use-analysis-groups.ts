'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { createAnalysisGroup, deleteAnalysisGroup, listAnalysisGroups, updateAnalysisGroup } from '@/lib/api'

export function useAnalysisGroups() {
  const queryClient = useQueryClient()

  const { data: groups, isLoading } = useQuery({
    queryKey: ['analysis-groups'],
    queryFn: listAnalysisGroups,
  })

  const createGroup = useMutation({
    mutationFn: (name: string) => createAnalysisGroup(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-groups'] })
      toast.success('그룹이 생성되었습니다', { duration: 2000 })
    },
  })

  const renameGroup = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      updateAnalysisGroup(id, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-groups'] })
    },
  })

  const deleteGroup = useMutation({
    mutationFn: (id: string) => deleteAnalysisGroup(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-groups'] })
      queryClient.invalidateQueries({ queryKey: ['analysis-sets'] })
      toast.success('그룹이 삭제되었습니다', { duration: 2000 })
    },
  })

  return { groups, isLoading, createGroup, renameGroup, deleteGroup }
}
