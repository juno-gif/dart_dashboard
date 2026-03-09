'use client'

import { Loader2, Trash2 } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import type { AnalysisSetData } from '@/lib/api'
import { exportAnalysisSetPpt } from '@/lib/api'
import { ShareDialog } from '@/components/layout/ShareDialog'

interface AnalysisSetItemProps {
  set: AnalysisSetData
  onLoad: (setId: string) => void
  onDelete: (setId: string) => void
  onEdit: (set: AnalysisSetData) => void
}

export function AnalysisSetItem({
  set,
  onLoad,
  onDelete,
  onEdit,
}: AnalysisSetItemProps) {
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
      toast.success('PPT 파일이 다운로드되었습니다', { duration: 3000 })
    },
    onError: () => {
      toast.error('내보내기에 실패했습니다. 잠시 후 재시도해 주세요', { duration: undefined })
    },
  })

  return (
    <>
    <div className="flex items-center gap-1 group">
      <button
        onClick={() => onLoad(set.id)}
        className="flex-1 text-left px-3 py-2 rounded-md hover:bg-accent transition-colors border border-border"
      >
        <p className="text-sm font-medium truncate">{set.name}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          기업 {set.company_codes.length}개
        </p>
      </button>

      <>
        <ShareDialog setId={set.id} />
        <button
          onClick={() => pptMutation.mutate()}
          disabled={pptMutation.isPending}
          className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity text-xs disabled:opacity-50 disabled:cursor-not-allowed"
          title="PPT 내보내기"
        >
          {pptMutation.isPending ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            'PPT'
          )}
        </button>
        <button
          onClick={() => onEdit(set)}
          className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity text-xs"
          title="수정"
        >
          수정
        </button>
        <button
          onClick={() => {
            if (window.confirm(`'${set.name}' 분석 세트를 삭제하시겠습니까?`)) {
              onDelete(set.id)
            }
          }}
          className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
          title="삭제"
        >
          <Trash2 size={14} />
        </button>
      </>
    </div>
    </>
  )
}

interface AnalysisSetPanelProps {
  analysisSets: AnalysisSetData[] | undefined
  isLoading: boolean
  onLoad: (setId: string) => void
  onDelete: (setId: string) => void
  onEdit: (set: AnalysisSetData) => void
}

export function AnalysisSetPanel({
  analysisSets,
  isLoading,
  onLoad,
  onDelete,
  onEdit,
}: AnalysisSetPanelProps) {
  if (isLoading) {
    return (
      <p className="text-xs text-muted-foreground px-1">불러오는 중...</p>
    )
  }

  if (!analysisSets || analysisSets.length === 0) {
    return (
      <p className="text-xs text-muted-foreground px-1">
        저장된 분석 세트가 없습니다. 기업을 선택한 후 저장해 보세요.
      </p>
    )
  }

  return (
    <div className="space-y-1">
      {analysisSets.map((set) => (
        <AnalysisSetItem
          key={set.id}
          set={set}
          onLoad={onLoad}
          onDelete={onDelete}
          onEdit={onEdit}
        />
      ))}
    </div>
  )
}
