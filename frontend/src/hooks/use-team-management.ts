'use client'

export function useTeamManagement() {
  return {
    users: [],
    isLoading: false,
    error: null,
    updateRole: { mutate: () => {}, isPending: false },
    deactivate: { mutate: () => {}, isPending: false },
  }
}
