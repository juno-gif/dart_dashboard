'use client'

/**
 * 분석 세트 수정 다이얼로그
 * Story 3.2: 이름 수정 및 현재 선택된 기업 코드로 업데이트
 * [Source: architecture.md - Frontend Architecture]
 */
import { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'
import type { AnalysisSetData } from '@/lib/api'

interface UpdateAnalysisSetDialogProps {
  set: AnalysisSetData | null
  open: boolean
  onOpenChange: (open: boolean) => void
  currentCompanyCodes: string[]
}

export function UpdateAnalysisSetDialog({
  set,
  open,
  onOpenChange,
  currentCompanyCodes,
}: UpdateAnalysisSetDialogProps) {
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const { updateSet } = useAnalysisSets()

  useEffect(() => {
    if (set) setName(set.name)
  }, [set])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!set) return
    setError(null)

    try {
      await updateSet.mutateAsync({
        id: set.id,
        name: name.trim(),
        companyCodes: currentCompanyCodes,
      })
      onOpenChange(false)
    } catch (err: unknown) {
      const apiErr = err as { error?: string; message?: string }
      if (apiErr?.error === 'NAME_ALREADY_EXISTS') {
        setError('이미 사용 중인 이름입니다. 다른 이름을 입력하세요.')
      } else {
        setError(apiErr?.message || '수정에 실패했습니다. 다시 시도해주세요.')
      }
    }
  }

  function handleOpenChange(next: boolean) {
    onOpenChange(next)
    if (!next) {
      setError(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>분석 세트 수정</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium">분석 세트 이름</label>
            <Input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={updateSet.isPending}
            />
            <p className="text-xs text-muted-foreground">
              현재 선택된 기업 {currentCompanyCodes.length}개로 업데이트됩니다.
            </p>
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={updateSet.isPending}
            >
              취소
            </Button>
            <Button type="submit" disabled={updateSet.isPending || !name.trim() || currentCompanyCodes.length === 0}>
              {updateSet.isPending ? '저장 중...' : '저장'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
