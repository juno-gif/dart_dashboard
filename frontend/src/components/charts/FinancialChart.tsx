'use client'
import { useRef } from 'react'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import { formatKRW, formatYearLabel } from '@/lib/format'
import { DownloadButton } from '@/components/charts/DownloadButton'
import type { FinancialStatement, FinancialType } from '@/types'

const PL_KEYS = ['revenue', 'operating_profit', 'net_income'] as const
const BS_KEYS = ['total_assets', 'total_liabilities', 'total_equity', 'cash_and_equivalents'] as const
const CF_KEYS = ['operating_cf', 'investing_cf', 'financing_cf'] as const

const PL_LABELS: Record<string, string> = {
  revenue: '매출',
  operating_profit: '영업이익',
  net_income: '순이익',
}
const BS_LABELS: Record<string, string> = {
  total_assets: '총자산',
  total_liabilities: '총부채',
  total_equity: '자본총계',
  cash_and_equivalents: '현금및현금성자산',
}
const CF_LABELS: Record<string, string> = {
  operating_cf: '영업활동현금흐름',
  investing_cf: '투자활동현금흐름',
  financing_cf: '재무활동현금흐름',
}

interface Props {
  data: FinancialStatement[]
  isLoading: boolean
  companyName?: string
  type?: FinancialType
}

export function FinancialChart({ data, isLoading, companyName, type = 'pl' }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)
  const today = new Date().toISOString().slice(0, 10)
  const filename = `${companyName ?? '차트'}_${today}`

  if (isLoading) {
    return <Skeleton className="h-80 w-full rounded-xl" />
  }

  const isBs = type === 'bs'
  const isCf = type === 'cf'
  const keys = isBs ? BS_KEYS : isCf ? CF_KEYS : PL_KEYS
  const labels = isBs ? BS_LABELS : isCf ? CF_LABELS : PL_LABELS

  const years = [...new Set(data.map((d) => d.bsns_year))].sort()

  // 연도별 reprt_code 맵 (부분연도 레이블용)
  const yearReprtMap = new Map<string, string>()
  for (const d of data) {
    if (!yearReprtMap.has(d.bsns_year)) yearReprtMap.set(d.bsns_year, d.reprt_code)
  }

  // CFS 없어 OFS로 폴백된 연도 집합
  const fallbackYears = new Set(data.filter((d) => d.is_fallback).map((d) => d.bsns_year))

  if (years.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center text-sm text-muted-foreground">
        {isCf
          ? '현금흐름 데이터를 제공하지 않는 기업입니다. P&L 또는 B/S 데이터를 이용해 주세요.'
          : isBs
          ? '재무상태표 데이터가 없습니다.'
          : '손익계산서 데이터가 없습니다.'}
      </div>
    )
  }

  const chartData = years.map((year) => {
    const get = (key: string) =>
      data.find((d) => d.bsns_year === year && d.account_key === key)?.amount ?? 0
    const row: Record<string, string | number> = { year }
    for (const k of keys) row[k] = get(k)
    return row
  })

  return (
    <div>
      <div className="flex justify-end mb-1">
        <DownloadButton chartRef={chartRef} filename={filename} />
      </div>
      <div ref={chartRef} className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 8, right: 80, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="year"
              tick={{ fontSize: 12 }}
              tickFormatter={(y: string) => {
                const base = formatYearLabel(y, yearReprtMap.get(y) ?? '')
                return fallbackYears.has(y) ? `${base}(별도)` : base
              }}
            />
            <YAxis
              yAxisId="left"
              tickFormatter={(v: number) => formatKRW(v)}
              width={80}
              tick={{ fontSize: 11 }}
            />
            {!isBs && !isCf && (
              <YAxis
                yAxisId="right"
                orientation="right"
                tickFormatter={(v: number) => formatKRW(v)}
                width={80}
                tick={{ fontSize: 11 }}
              />
            )}
            <Tooltip
              formatter={(value: number | undefined, name: string | undefined) => [
                value != null ? formatKRW(value) : '-',
                name ? (labels[name] ?? name) : name,
              ]}
            />
            <Legend formatter={(value: string) => labels[value] ?? value} />
            {isCf ? (
              <>
                <Bar yAxisId="left" dataKey="operating_cf" name="operating_cf" fill="#16a34a" opacity={0.8} />
                <Bar yAxisId="left" dataKey="investing_cf" name="investing_cf" fill="#ef4444" opacity={0.8} />
                <Bar yAxisId="left" dataKey="financing_cf" name="financing_cf" fill="#f59e0b" opacity={0.8} />
              </>
            ) : isBs ? (
              <>
                <Bar yAxisId="left" dataKey="total_assets" name="total_assets" fill="#2563eb" opacity={0.7} />
                <Line yAxisId="left" dataKey="total_liabilities" name="total_liabilities" stroke="#ef4444" strokeWidth={2} dot />
                <Line yAxisId="left" dataKey="total_equity" name="total_equity" stroke="#16a34a" strokeWidth={2} dot />
                <Line yAxisId="left" dataKey="cash_and_equivalents" name="cash_and_equivalents" stroke="#f59e0b" strokeWidth={2} dot />
              </>
            ) : (
              <>
                <Bar yAxisId="left" dataKey="revenue" name="revenue" fill="#2563eb" opacity={0.7} />
                <Line yAxisId="right" dataKey="operating_profit" name="operating_profit" stroke="#16a34a" strokeWidth={2} dot />
                <Line yAxisId="right" dataKey="net_income" name="net_income" stroke="#9333ea" strokeWidth={2} dot />
              </>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
