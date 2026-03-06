'use client'

/**
 * 팀원 관리 훅 (Admin 전용)
 * Story 2.3: 팀원 목록 조회, 역할 변경, 비활성화
 * [Source: architecture.md - Frontend Architecture - TanStack Query]
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { deactivateUser, listUsers, updateUserRole } from '@/lib/api'

export function useTeamManagement() {
  const queryClient = useQueryClient()

  const { data: users, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  })

  const updateRole = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      updateUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const deactivate = useMutation({
    mutationFn: (userId: string) => deactivateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  return {
    users,
    isLoading,
    error,
    updateRole,
    deactivate,
  }
}
