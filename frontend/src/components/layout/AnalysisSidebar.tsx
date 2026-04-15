'use client'

import { useState } from 'react'
import { Trash2, Loader2, Pencil } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'
import { exportAnalysisSetPpt } from '@/lib/api'
import { ShareDialog } from '@/components/layout/ShareDialog'
import type { AnalysisSetData } from '@/lib/api'

interface AnalysisSidebarProps {
  activeSetId: string | null
  companyCodes: string[]
  onLoad: (setId: string) => void
  onEdit: (set: AnalysisSetData) => void
  onDelete: (setId: string) => void
}

export function AnalysisSidebar({
  activeSetId,
  companyCodes,
  onLoad,
  onEdit,
  onDelete,
}: AnalysisSidebarProps) {
  const { analysisSets, isLoading, saveSet } = useAnalysisSets()
  const [saveOpen, setSaveOpen] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saveError, setSaveError] = useState<string | null>(null)

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaveError(null)
    try {
      await saveSet.mutateAsync({ name: saveName, companyCodes })
      setSaveOpen(false)
      setSaveName('')
    } catch (err: unknown) {
      const apiErr = err as { error?: string; message?: string }
      if (apiErr?.error === 'NAME_ALREADY_EXISTS') {
        setSaveError('이미 사용 중인 이름입니다.')
      } else {
        setSaveError(apiErr?.message || '저장에 실패했습니다.')
      }
    }
  }

  return (
    <aside className="w-[240px] border-r flex flex-col shrink-0 overflow-hidden bg-background">
      {/* 분석 세트 목록 */}
      <div className="flex-1 overflow-y-auto py-3">
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider px-4 pb-2">
          내 분석 세트
        </p>

        {isLoading ? (
          <div className="flex items-center gap-2 px-4 py-2 text-xs text-muted-foreground">
            <Loader2 size={12} className="animate-spin" />
            불러오는 중...
          </div>
        ) : !analysisSets || analysisSets.length === 0 ? (
          <p className="px-4 py-2 text-xs text-muted-foreground">
            저장된 분석 세트가 없습니다.
          </p>
        ) : (
          <ul className="space-y-0.5 px-2">
            {analysisSets.map((set) => (
              <SidebarItem
                key={set.id}
                set={set}
                isActive={set.id === activeSetId}
                onLoad={onLoad}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </ul>
        )}
      </div>

      {/* 새 분석 세트 저장 버튼 */}
      <div className="border-t p-3 shrink-0">
        <button
          onClick={() => setSaveOpen(true)}
          disabled={companyCodes.length === 0}
          className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-xs border rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <span className="text-base leading-none">+</span>
          새 분석 세트
        </button>
      </div>

      {/* 저장 다이얼로그 */}
      <Dialog open={saveOpen} onOpenChange={(o) => { setSaveOpen(o); if (!o) { setSaveName(''); setSaveError(null) } }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>분석 세트 저장</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-1">
              <label className="text-sm font-medium">분석 세트 이름</label>
              <Input
                placeholder="예: 반도체 기업 비교"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                required
                disabled={saveSet.isPending}
              />
              <p className="text-xs text-muted-foreground">선택된 기업 {companyCodes.length}개가 저장됩니다.</p>
            </div>
            {saveError && <p className="text-sm text-destructive">{saveError}</p>}
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setSaveOpen(false)} disabled={saveSet.isPending}>취소</Button>
              <Button type="submit" disabled={saveSet.isPending || !saveName.trim()}>
                {saveSet.isPending ? '저장 중...' : '저장'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </aside>
  )
}

interface SidebarItemProps {
  set: AnalysisSetData
  isActive: boolean
  onLoad: (setId: string) => void
  onEdit: (set: AnalysisSetData) => void
  onDelete: (setId: string) => void
}

function SidebarItem({ set, isActive, onLoad, onEdit, onDelete }: SidebarItemProps) {
  const pptMutation = useMutation({
    mutationFn: () => exportAnalysisSetPpt(set.id),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${set.name}_${new Date().toISOString().slice(0, 10)}.pptx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('PPT 파일이 다운로드되었습니다')
    },
    onError: () => toast.error('내보내기에 실패했습니다.'),
  })

  return (
    <li className="group relative">
      <button
        onClick={() => onLoad(set.id)}
        className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
          isActive
            ? 'bg-primary/10 text-primary'
            : 'hover:bg-accent text-foreground'
        }`}
      >
        <div className="flex items-center gap-2 min-w-0">
          {isActive && <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />}
          <span className={`text-sm truncate flex-1 ${isActive ? 'font-medium' : ''}`}>
            {set.name}
          </span>
          <span className="text-[11px] text-muted-foreground shrink-0 group-hover:hidden">
            {set.company_codes.length}개
          </span>
        </div>
      </button>

      {/* 호버 액션 (우측 절대 위치) */}
      <div className="absolute right-1 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-0.5 bg-background/90 rounded">
        <ShareDialog setId={set.id} />
        <button
          onClick={() => pptMutation.mutate()}
          disabled={pptMutation.isPending}
          className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground text-[10px] disabled:opacity-50"
          title="PPT"
        >
          {pptMutation.isPending ? <Loader2 size={12} className="animate-spin" /> : 'PPT'}
        </button>
        <button
          onClick={() => onEdit(set)}
          className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
          title="수정"
        >
          <Pencil size={12} />
        </button>
        <button
          onClick={() => {
            if (window.confirm(`'${set.name}' 분석 세트를 삭제하시겠습니까?`)) onDelete(set.id)
          }}
          className="p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
          title="삭제"
        >
          <Trash2 size={12} />
        </button>
      </div>
    </li>
  )
}
