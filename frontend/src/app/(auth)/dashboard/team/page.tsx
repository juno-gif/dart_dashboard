'use client'

/**
 * 팀원 관리 페이지 (Admin 전용)
 * Story 2.3: 팀원 목록, 역할 변경, 계정 비활성화, 팀원 초대
 * [Source: architecture.md - Frontend Architecture]
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getUserProfile } from '@/lib/api'
import { useTeamManagement } from '@/hooks/use-team-management'
import { InviteTeamDialog } from '@/components/layout/InviteTeamDialog'

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  builder: 'Builder',
  live_viewer: 'Live Viewer',
  read_only: 'Read Only',
}

const ROLE_OPTIONS = ['admin', 'builder', 'live_viewer', 'read_only'] as const

export default function TeamPage() {
  const queryClient = useQueryClient()
  const { data: myProfile } = useQuery({
    queryKey: ['user-profile'],
    queryFn: getUserProfile,
  })

  const { users, isLoading, updateRole, deactivate } = useTeamManagement()

  const isAdmin = myProfile?.role === 'admin'

  if (!isAdmin) {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">팀 관리 페이지는 Admin만 접근할 수 있습니다.</p>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">팀 관리</h1>
        <InviteTeamDialog onSuccess={() => queryClient.invalidateQueries({ queryKey: ['users'] })} />
      </div>

      {isLoading && (
        <div className="text-sm text-muted-foreground">팀원 목록을 불러오는 중...</div>
      )}

      {users && users.length === 0 && (
        <div className="text-sm text-muted-foreground">등록된 팀원이 없습니다.</div>
      )}

      {users && users.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left px-4 py-3 font-medium">사용자 ID</th>
                <th className="text-left px-4 py-3 font-medium">표시 이름</th>
                <th className="text-left px-4 py-3 font-medium">역할</th>
                <th className="text-left px-4 py-3 font-medium">작업</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {users.map((member) => (
                <tr key={member.id} className="hover:bg-muted/20">
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {member.id.slice(0, 8)}...
                  </td>
                  <td className="px-4 py-3">
                    {member.display_name || <span className="text-muted-foreground">-</span>}
                  </td>
                  <td className="px-4 py-3">
                    {member.id === myProfile?.id ? (
                      <span className="text-muted-foreground">{ROLE_LABELS[member.role]}</span>
                    ) : (
                      <select
                        value={member.role}
                        onChange={(e) =>
                          updateRole.mutate({ userId: member.id, role: e.target.value })
                        }
                        disabled={updateRole.isPending}
                        className="rounded border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                      >
                        {ROLE_OPTIONS.map((r) => (
                          <option key={r} value={r}>
                            {ROLE_LABELS[r]}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {member.id !== myProfile?.id && (
                      <button
                        onClick={() => {
                          if (confirm(`${member.display_name || member.id.slice(0, 8)} 계정을 비활성화하시겠습니까?`)) {
                            deactivate.mutate(member.id)
                          }
                        }}
                        disabled={deactivate.isPending}
                        className="text-destructive hover:underline text-xs disabled:opacity-50"
                      >
                        비활성화
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
