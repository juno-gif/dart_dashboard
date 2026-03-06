'use client'

/**
 * 분석 세트 저장 다이얼로그 (Builder 전용)
 * Story 3.1: 현재 선택된 기업들을 이름을 지정해 분석 세트로 저장
 * [Source: architecture.md - Frontend Architecture]
 */
import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'

interface SaveAnalysisSetDialogProps {
  companyCodes: string[]
}

export function SaveAnalysisSetDialog({ companyCodes }: SaveAnalysisSetDialogProps) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const { saveSet } = useAnalysisSets()
  const isDisabled = companyCodes.length === 0

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    try {
      await saveSet.mutateAsync({ name, companyCodes })
      setOpen(false)
      setName('')
    } catch (err: unknown) {
      const apiErr = err as { error?: string; message?: string }
      if (apiErr?.error === 'NAME_ALREADY_EXISTS') {
        setError('이미 사용 중인 이름입니다. 다른 이름을 입력하세요.')
      } else {
        setError(apiErr?.message || '저장에 실패했습니다. 다시 시도해주세요.')
      }
    }
  }

  function handleOpenChange(next: boolean) {
    setOpen(next)
    if (!next) {
      setName('')
      setError(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline" disabled={isDisabled}>
          분석 세트 저장
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>분석 세트 저장</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium">분석 세트 이름</label>
            <Input
              type="text"
              placeholder="예: 반도체 기업 비교"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={saveSet.isPending}
            />
            <p className="text-xs text-muted-foreground">
              선택된 기업 {companyCodes.length}개가 저장됩니다.
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
              disabled={saveSet.isPending}
            >
              취소
            </Button>
            <Button type="submit" disabled={saveSet.isPending || !name.trim()}>
              {saveSet.isPending ? '저장 중...' : '저장'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
