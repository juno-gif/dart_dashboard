'use client'
import { useRef } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import { formatKRW, formatYearLabel } from '@/lib/format'
import { DownloadButton } from '@/components/charts/DownloadButton'
import type { Company, FinancialStatement } from '@/types'

export const COMPANY_COLORS = [
  '#18181b',
  '#3b82f6',
  '#71717a',
  '#f59e0b',
  '#10b981',
  '#a1a1aa',
  '#ef4444',
  '#8b5cf6',
  '#06b6d4',
  '#f97316',
]

interface Props {
  data: FinancialStatement[]
  companies: Company[]
  isLoading: boolean
}

function pivotByCompany(
  data: FinancialStatement[],
  accountKey: string,
  codes: string[]
) {
  const years = [...new Set(data.map((d) => d.bsns_year))].sort()
  return years.map((year) => {
    const row: Record<string, string | number> = { year }
    for (const code of codes) {
      row[code] =
        data.find(
          (d) =>
            d.bsns_year === year &&
            d.corp_code === code &&
            d.account_key === accountKey
        )?.amount ?? 0
    }
    return row
  })
}

const METRICS = [
  { key: 'revenue', label: '매출 비교' },
  { key: 'operating_profit', label: '영업이익 비교' },
  { key: 'net_income', label: '순이익 비교' },
]

export function CompareChart({ data, companies, isLoading }: Props) {
  const chartRef = useRef<HTMLDivElement>(null)
  const today = new Date().toISOString().slice(0, 10)
  const firstName = companies[0]?.company_name ?? '비교차트'
  const filename = `${firstName}_${today}`

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-60 w-full rounded-xl" />
        ))}
      </div>
    )
  }

  const codes = companies.map((c) => c.corp_code)

  // 연도별 reprt_code 맵 (부분연도 레이블용)
  const yearReprtMap = new Map<string, string>()
  for (const d of data) {
    if (!yearReprtMap.has(d.bsns_year)) yearReprtMap.set(d.bsns_year, d.reprt_code)
  }

  return (
    <div>
      <div className="flex justify-end mb-1">
        <DownloadButton chartRef={chartRef} filename={filename} />
      </div>
      <div ref={chartRef} className="space-y-8">
        {METRICS.map(({ key, label }) => {
          const chartData = pivotByCompany(data, key, codes)
          return (
            <div key={key}>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">
                {label}
              </h3>
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartData}
                    margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                    <XAxis
                      dataKey="year"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(y: string) => formatYearLabel(y, yearReprtMap.get(y) ?? '')}
                    />
                    <YAxis
                      tickFormatter={(v: number) => formatKRW(v)}
                      width={80}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip
                      formatter={(
                        value: number | undefined,
                        name: string | undefined
                      ) => [
                        value != null ? formatKRW(value) : '-',
                        companies.find((c) => c.corp_code === name)
                          ?.company_name ?? name,
                      ]}
                    />
                    <Legend
                      formatter={(value: string) =>
                        companies.find((c) => c.corp_code === value)
                          ?.company_name ?? value
                      }
                    />
                    {codes.map((code, idx) => (
                      <Line
                        key={code}
                        dataKey={code}
                        stroke={COMPANY_COLORS[idx % COMPANY_COLORS.length]}
                        strokeWidth={2}
                        dot
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
