'use client'
import { Skeleton } from '@/components/ui/skeleton'
import { formatKRW, formatPercent } from '@/lib/format'
import type { FinancialStatement } from '@/types'

interface Props {
  data: FinancialStatement[]
  isLoading: boolean
}

function calcYoY(current: number | null, prev: number | null): number | null {
  if (current == null || prev == null || prev === 0) return null
  return ((current - prev) / Math.abs(prev)) * 100
}

export function KPICard({ data, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
    )
  }

  const years = [...new Set(data.map((d) => d.bsns_year))].sort().reverse()
  const latestYear = years[0]
  const prevYear = years[1]

  const get = (year: string | undefined, key: string): number | null => {
    if (!year) return null
    return data.find((d) => d.bsns_year === year && d.account_key === key)?.amount ?? null
  }

  const revenue = get(latestYear, 'revenue')
  const opProfit = get(latestYear, 'operating_profit')
  const netIncome = get(latestYear, 'net_income')
  const opMargin = revenue && opProfit ? (opProfit / revenue) * 100 : null

  const prevRevenue = get(prevYear, 'revenue')
  const prevOpProfit = get(prevYear, 'operating_profit')
  const prevNetIncome = get(prevYear, 'net_income')

  const cards = [
    {
      label: '매출',
      value: revenue != null ? formatKRW(revenue) : '-',
      yoy: calcYoY(revenue, prevRevenue),
    },
    {
      label: '영업이익',
      value: opProfit != null ? formatKRW(opProfit) : '-',
      yoy: calcYoY(opProfit, prevOpProfit),
    },
    {
      label: '순이익',
      value: netIncome != null ? formatKRW(netIncome) : '-',
      yoy: calcYoY(netIncome, prevNetIncome),
    },
    {
      label: '영업이익률',
      value: opMargin != null ? `${opMargin.toFixed(1)}%` : '-',
      yoy: null,
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-xl border bg-card p-4 shadow-sm"
        >
          <p className="text-sm text-muted-foreground">{card.label}</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{card.value}</p>
          {card.yoy != null && (
            <p
              className={`mt-1 text-xs ${
                card.yoy >= 0 ? 'text-green-600' : 'text-red-500'
              }`}
            >
              {card.yoy >= 0 ? '▲' : '▼'}{' '}
              {formatPercent(Math.abs(card.yoy))} 전년 대비
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
