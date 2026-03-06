'use client'
import type { FinancialStatement } from '@/types'

interface Props {
  data: FinancialStatement[]
  hasDartError: boolean
}

function getDaysAgo(dateStr: string): number {
  const diff = Date.now() - new Date(dateStr).getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24))
}

export function DartWarningBanner({ data, hasDartError }: Props) {
  const latestSyncedAt = data
    .map((d) => d.synced_at)
    .filter(Boolean)
    .sort()
    .reverse()[0]

  const daysAgo = latestSyncedAt ? getDaysAgo(latestSyncedAt) : null
  const isStale = hasDartError || (daysAgo !== null && daysAgo >= 7)

  if (!isStale) return null

  return (
    <div className="w-full bg-yellow-100 border border-yellow-300 px-4 py-2 text-sm text-yellow-800 rounded-lg">
      ⚠️ 일부 데이터가 오래되었습니다
      {daysAgo !== null && ` — 마지막 업데이트: ${daysAgo}일 전`}
    </div>
  )
}
