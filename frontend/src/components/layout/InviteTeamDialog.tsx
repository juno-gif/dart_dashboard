'use client'

/**
 * 팀원 초대 다이얼로그 (Admin 전용)
 * Story 2.3: Supabase Auth Magic Link 초대 + 역할 지정
 * [Source: architecture.md - Frontend Architecture]
 */
import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { inviteUser } from '@/lib/api'

interface InviteTeamDialogProps {
  onSuccess?: () => void
}

const ROLE_OPTIONS = [
  { value: 'builder', label: 'Builder — 분석 세트 생성·편집' },
  { value: 'live_viewer', label: 'Live Viewer — 실시간 조회' },
  { value: 'read_only', label: 'Read Only — 읽기 전용' },
] as const

export function InviteTeamDialog({ onSuccess }: InviteTeamDialogProps) {
  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'builder' | 'live_viewer' | 'read_only'>('builder')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      await inviteUser({ email, role })
      setSuccess(`초대 이메일이 발송되었습니다. (${email})`)
      setEmail('')
      setRole('builder')
      onSuccess?.()
    } catch (err: unknown) {
      const apiErr = err as { error?: string; message?: string }
      if (apiErr?.error === 'USER_ALREADY_EXISTS') {
        setError('이미 초대되었거나 가입된 이메일입니다.')
      } else if (apiErr?.error === 'INSUFFICIENT_PERMISSION') {
        setError('초대 권한이 없습니다.')
      } else {
        setError(apiErr?.message || '초대에 실패했습니다. 다시 시도해주세요.')
      }
    } finally {
      setLoading(false)
    }
  }

  function handleOpenChange(next: boolean) {
    setOpen(next)
    if (!next) {
      setEmail('')
      setRole('builder')
      setError(null)
      setSuccess(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm">팀원 초대</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>팀원 초대</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium">이메일</label>
            <Input
              type="email"
              placeholder="teammate@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">역할</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as typeof role)}
              disabled={loading}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            >
              {ROLE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
          {success && (
            <p className="text-sm text-green-600">{success}</p>
          )}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={loading}
            >
              취소
            </Button>
            <Button type="submit" disabled={loading || !email}>
              {loading ? '발송 중...' : '초대 이메일 발송'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
