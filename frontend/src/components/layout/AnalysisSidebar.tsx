'use client'

import { useState } from 'react'
import { Trash2, Loader2, Pencil, ChevronRight, ChevronDown, FolderPlus, Folder, FolderOpen } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'
import { useAnalysisGroups } from '@/hooks/use-analysis-groups'
import { exportAnalysisSetPpt, updateAnalysisSet } from '@/lib/api'
import { ShareDialog } from '@/components/layout/ShareDialog'
import type { AnalysisSetData, AnalysisGroupData } from '@/lib/api'

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
  const { analysisSets, isLoading: setsLoading, saveSet, updateSet } = useAnalysisSets()
  const { groups, createGroup, renameGroup, deleteGroup } = useAnalysisGroups()

  const [saveOpen, setSaveOpen] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saveGroupId, setSaveGroupId] = useState<string>('__none__')
  const [saveError, setSaveError] = useState<string | null>(null)

  const [newGroupOpen, setNewGroupOpen] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')

  // 그룹 접기/펼치기 상태 (기본: 모두 펼침)
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())

  function toggleGroup(groupId: string) {
    setCollapsedGroups(prev => {
      const next = new Set(prev)
      if (next.has(groupId)) next.delete(groupId)
      else next.add(groupId)
      return next
    })
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaveError(null)
    try {
      await saveSet.mutateAsync({
        name: saveName,
        companyCodes,
        groupId: saveGroupId === '__none__' ? null : saveGroupId,
      })
      setSaveOpen(false)
      setSaveName('')
      setSaveGroupId('__none__')
    } catch (err: unknown) {
      const apiErr = err as { error?: string; message?: string }
      if (apiErr?.error === 'NAME_ALREADY_EXISTS') {
        setSaveError('이미 사용 중인 이름입니다.')
      } else {
        setSaveError(apiErr?.message || '저장에 실패했습니다.')
      }
    }
  }

  async function handleCreateGroup(e: React.FormEvent) {
    e.preventDefault()
    if (!newGroupName.trim()) return
    await createGroup.mutateAsync(newGroupName.trim())
    setNewGroupOpen(false)
    setNewGroupName('')
  }

  // 세트를 그룹으로 이동
  async function handleMoveSet(setId: string, groupId: string | null) {
    try {
      await updateSet.mutateAsync({ id: setId, groupId })
    } catch {
      toast.error('이동에 실패했습니다.')
    }
  }

  const isLoading = setsLoading

  // 그룹별로 세트 분류
  const groupedSets = new Map<string, AnalysisSetData[]>()
  const ungroupedSets: AnalysisSetData[] = []

  if (analysisSets) {
    for (const set of analysisSets) {
      if (set.group_id) {
        const arr = groupedSets.get(set.group_id) ?? []
        arr.push(set)
        groupedSets.set(set.group_id, arr)
      } else {
        ungroupedSets.push(set)
      }
    }
  }

  return (
    <aside className="w-[240px] border-r flex flex-col shrink-0 overflow-hidden bg-background">
      {/* 헤더 */}
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
          분석 세트
        </p>
        <button
          onClick={() => setNewGroupOpen(true)}
          className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          title="새 그룹 만들기"
        >
          <FolderPlus size={14} />
        </button>
      </div>

      {/* 목록 */}
      <div className="flex-1 overflow-y-auto py-2">
        {isLoading ? (
          <div className="flex items-center gap-2 px-4 py-2 text-xs text-muted-foreground">
            <Loader2 size={12} className="animate-spin" />
            불러오는 중...
          </div>
        ) : (
          <>
            {/* 그룹별 섹션 */}
            {groups?.map((group) => {
              const sets = groupedSets.get(group.id) ?? []
              const collapsed = collapsedGroups.has(group.id)
              return (
                <GroupSection
                  key={group.id}
                  group={group}
                  sets={sets}
                  collapsed={collapsed}
                  activeSetId={activeSetId}
                  allGroups={groups}
                  onToggle={() => toggleGroup(group.id)}
                  onLoad={onLoad}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onMoveSet={handleMoveSet}
                  onRenameGroup={(name) => renameGroup.mutate({ id: group.id, name })}
                  onDeleteGroup={() => {
                    if (window.confirm(`'${group.name}' 그룹을 삭제하시겠습니까?\n그룹 내 세트는 미분류로 이동됩니다.`)) {
                      deleteGroup.mutate(group.id)
                    }
                  }}
                />
              )
            })}

            {/* 미분류 세트 */}
            {ungroupedSets.length > 0 && (
              <div className="mt-1">
                {groups && groups.length > 0 && (
                  <p className="text-[10px] text-muted-foreground px-4 pb-1 pt-2 uppercase tracking-wider">
                    미분류
                  </p>
                )}
                <ul className="space-y-0.5 px-2">
                  {ungroupedSets.map((set) => (
                    <SidebarItem
                      key={set.id}
                      set={set}
                      isActive={set.id === activeSetId}
                      allGroups={groups ?? []}
                      onLoad={onLoad}
                      onEdit={onEdit}
                      onDelete={onDelete}
                      onMoveSet={handleMoveSet}
                    />
                  ))}
                </ul>
              </div>
            )}

            {(!analysisSets || analysisSets.length === 0) && (!groups || groups.length === 0) && (
              <p className="px-4 py-2 text-xs text-muted-foreground">
                저장된 분석 세트가 없습니다.
              </p>
            )}
          </>
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
      <Dialog open={saveOpen} onOpenChange={(o) => { setSaveOpen(o); if (!o) { setSaveName(''); setSaveGroupId('__none__'); setSaveError(null) } }}>
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
            {groups && groups.length > 0 && (
              <div className="space-y-1">
                <label className="text-sm font-medium">그룹 (선택)</label>
                <select
                  value={saveGroupId}
                  onChange={(e) => setSaveGroupId(e.target.value)}
                  disabled={saveSet.isPending}
                  className="w-full text-sm border rounded-md px-3 py-2 bg-background focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="__none__">그룹 없음</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
              </div>
            )}
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

      {/* 새 그룹 다이얼로그 */}
      <Dialog open={newGroupOpen} onOpenChange={(o) => { setNewGroupOpen(o); if (!o) setNewGroupName('') }}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>새 그룹 만들기</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateGroup} className="space-y-4">
            <Input
              placeholder="그룹 이름"
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              required
              disabled={createGroup.isPending}
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setNewGroupOpen(false)} disabled={createGroup.isPending}>취소</Button>
              <Button type="submit" disabled={createGroup.isPending || !newGroupName.trim()}>
                {createGroup.isPending ? '만드는 중...' : '만들기'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </aside>
  )
}

// ── 그룹 섹션 ────────────────────────────────────────────────────────────────

interface GroupSectionProps {
  group: AnalysisGroupData
  sets: AnalysisSetData[]
  collapsed: boolean
  activeSetId: string | null
  allGroups: AnalysisGroupData[]
  onToggle: () => void
  onLoad: (setId: string) => void
  onEdit: (set: AnalysisSetData) => void
  onDelete: (setId: string) => void
  onMoveSet: (setId: string, groupId: string | null) => void
  onRenameGroup: (name: string) => void
  onDeleteGroup: () => void
}

function GroupSection({
  group, sets, collapsed, activeSetId, allGroups,
  onToggle, onLoad, onEdit, onDelete, onMoveSet, onRenameGroup, onDeleteGroup,
}: GroupSectionProps) {
  const [renaming, setRenaming] = useState(false)
  const [renameName, setRenameName] = useState(group.name)

  function submitRename(e: React.FormEvent) {
    e.preventDefault()
    if (renameName.trim() && renameName.trim() !== group.name) {
      onRenameGroup(renameName.trim())
    }
    setRenaming(false)
  }

  return (
    <div className="mb-1">
      {/* 그룹 헤더 */}
      <div className="group/gh flex items-center gap-1 px-2 py-1 rounded-md hover:bg-accent/50 cursor-pointer select-none"
        onClick={() => !renaming && onToggle()}
      >
        <span className="text-muted-foreground shrink-0">
          {collapsed
            ? <ChevronRight size={12} />
            : <ChevronDown size={12} />}
        </span>
        <span className="text-muted-foreground shrink-0">
          {collapsed ? <Folder size={13} /> : <FolderOpen size={13} />}
        </span>

        {renaming ? (
          <form onSubmit={submitRename} onClick={(e) => e.stopPropagation()} className="flex-1 flex gap-1">
            <input
              autoFocus
              className="flex-1 text-xs bg-background border rounded px-1 py-0.5 outline-none focus:ring-1 ring-primary min-w-0"
              value={renameName}
              onChange={(e) => setRenameName(e.target.value)}
              onBlur={submitRename}
              onKeyDown={(e) => { if (e.key === 'Escape') { setRenaming(false); setRenameName(group.name) } }}
            />
          </form>
        ) : (
          <span className="text-xs font-medium flex-1 truncate">{group.name}</span>
        )}

        {/* 그룹 액션 (호버 시) */}
        {!renaming && (
          <div className="hidden group-hover/gh:flex items-center gap-0.5 shrink-0" onClick={(e) => e.stopPropagation()}>
            <button
              className="p-0.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
              title="이름 변경"
              onClick={() => { setRenaming(true); setRenameName(group.name) }}
            >
              <Pencil size={11} />
            </button>
            <button
              className="p-0.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
              title="그룹 삭제"
              onClick={onDeleteGroup}
            >
              <Trash2 size={11} />
            </button>
          </div>
        )}
      </div>

      {/* 그룹 내 세트 */}
      {!collapsed && (
        <ul className="space-y-0.5 pl-5 pr-2">
          {sets.length === 0 ? (
            <li className="text-[11px] text-muted-foreground px-2 py-1 italic">비어 있음</li>
          ) : (
            sets.map((set) => (
              <SidebarItem
                key={set.id}
                set={set}
                isActive={set.id === activeSetId}
                allGroups={allGroups}
                currentGroupId={group.id}
                onLoad={onLoad}
                onEdit={onEdit}
                onDelete={onDelete}
                onMoveSet={onMoveSet}
              />
            ))
          )}
        </ul>
      )}
    </div>
  )
}

// ── 세트 아이템 ───────────────────────────────────────────────────────────────

interface SidebarItemProps {
  set: AnalysisSetData
  isActive: boolean
  allGroups: AnalysisGroupData[]
  currentGroupId?: string
  onLoad: (setId: string) => void
  onEdit: (set: AnalysisSetData) => void
  onDelete: (setId: string) => void
  onMoveSet: (setId: string, groupId: string | null) => void
}

function SidebarItem({ set, isActive, allGroups, currentGroupId, onLoad, onEdit, onDelete, onMoveSet }: SidebarItemProps) {
  const [showMoveMenu, setShowMoveMenu] = useState(false)

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

  // 이동 가능한 그룹 목록 (현재 그룹 제외)
  const moveTargets = allGroups.filter((g) => g.id !== currentGroupId)

  return (
    <li className="group relative">
      <button
        onClick={() => onLoad(set.id)}
        className={`w-full text-left px-3 py-1.5 rounded-md transition-colors ${
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

      {/* 호버 액션 */}
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

        {/* 그룹 이동 */}
        {(allGroups.length > 0) && (
          <div className="relative">
            <button
              onClick={(e) => { e.stopPropagation(); setShowMoveMenu((v) => !v) }}
              className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground text-[10px]"
              title="그룹으로 이동"
            >
              <Folder size={12} />
            </button>
            {showMoveMenu && (
              <div
                className="absolute right-0 top-full mt-1 z-50 bg-popover border rounded-md shadow-md py-1 min-w-[120px]"
                onMouseLeave={() => setShowMoveMenu(false)}
              >
                {currentGroupId && (
                  <button
                    className="w-full text-left px-3 py-1.5 text-xs hover:bg-accent"
                    onClick={() => { onMoveSet(set.id, null); setShowMoveMenu(false) }}
                  >
                    미분류로 이동
                  </button>
                )}
                {moveTargets.map((g) => (
                  <button
                    key={g.id}
                    className="w-full text-left px-3 py-1.5 text-xs hover:bg-accent"
                    onClick={() => { onMoveSet(set.id, g.id); setShowMoveMenu(false) }}
                  >
                    {g.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

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
