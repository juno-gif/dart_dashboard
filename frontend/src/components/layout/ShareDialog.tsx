'use client'

/**
 * 분석 세트 공유 링크 생성 다이얼로그 — Story 4.1
 * POST /api/v1/analysis-sets/{id}/share → 공유 URL 클립보드 복사
 * [Source: architecture.md - API & Communication Patterns]
 * [Source: ux-design-specification.md - ShareButton Component, Modal & Overlay Patterns]
 */
import { useState } from 'react'
import { Share2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'

interface ShareDialogProps {
  setId: string
}

export function ShareDialog({ setId }: ShareDialogProps) {
  const [open, setOpen] = useState(false)
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const { shareSet } = useAnalysisSets()

  const handleOpenChange = async (next: boolean) => {
    setOpen(next)
    if (next && !shareUrl) {
      try {
        const result = await shareSet.mutateAsync(setId)
        setShareUrl(result.share_url)
      } catch {
        toast.error('공유 링크 생성에 실패했습니다.')
        setOpen(false)
      }
    }
  }

  const handleCopy = async () => {
    if (!shareUrl) return
    await navigator.clipboard.writeText(shareUrl)
    toast.success('링크가 복사되었습니다', { duration: 3000 })
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <button
          className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity"
          title="공유"
          aria-label="분석 세트 공유"
        >
          <Share2 size={14} />
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-[480px]">
        <DialogHeader>
          <DialogTitle>분석 세트 공유</DialogTitle>
        </DialogHeader>
        {shareSet.isPending ? (
          <div className="flex justify-center py-4">
            <span className="text-sm text-muted-foreground">링크 생성 중...</span>
          </div>
        ) : shareUrl ? (
          <div className="flex gap-2">
            <Input value={shareUrl} readOnly className="flex-1 text-xs" />
            <Button onClick={handleCopy} size="sm">
              링크 복사
            </Button>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
