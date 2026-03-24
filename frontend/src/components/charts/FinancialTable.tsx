'use client'

import { formatYearLabel, getRevenueLabel } from '@/lib/format'
import type { ValuationData } from '@/lib/api'
import type { FinancialStatement, FinancialType } from '@/types'

const ACCOUNT_LABELS: Record<string, string> = {
  // PL
  revenue: '매출',
  operating_profit: '영업이익',
  net_income: '순이익',
  // BS
  total_assets: '자산총계',
  total_liabilities: '부채총계',
  total_equity: '자본총계',
  cash_and_equivalents: '현금성자산',
  // CF
  operating_cf: '영업활동CF',
  investing_cf: '투자활동CF',
  financing_cf: '재무활동CF',
}

const ACCOUNT_ORDER: Record<FinancialType, string[]> = {
  pl: ['revenue', 'operating_profit', 'net_income'],
  bs: ['total_assets', 'total_liabilities', 'total_equity', 'cash_and_equivalents'],
  cf: ['operating_cf', 'investing_cf', 'financing_cf'],
}

function formatBillion(amount: number): string {
  const billion = amount / 100_000_000
  return billion.toLocaleString('ko-KR', { maximumFractionDigits: 1 })
}

interface Props {
  data: FinancialStatement[]
  chartType: FinancialType
  companies?: { corp_code: string; company_name: string }[]
  valuationData?: ValuationData | null
}

export function FinancialTable({ data, chartType, companies, valuationData }: Props) {
  if (!data.length) return null

  const accountKeys = ACCOUNT_ORDER[chartType]
  const isCompare = companies && companies.length >= 2

  // 연도 목록 (오름차순 — 좌: 과거, 우: 최신)
  const years = [...new Set(data.map((d) => d.bsns_year))].sort((a, b) =>
    a.localeCompare(b)
  )

  // 연도별 reprt_code 맵 (부분연도 레이블용)
  const yearReprtMap = new Map<string, string>()
  for (const d of data) {
    if (!yearReprtMap.has(d.bsns_year)) yearReprtMap.set(d.bsns_year, d.reprt_code)
  }

  // CFS 없어 OFS로 폴백된 연도 집합
  const fallbackYears = new Set(data.filter((d) => d.is_fallback).map((d) => d.bsns_year))

  if (isCompare) {
    // 비교 모드: 기업별 그룹 → 행: 계정, 열: 연도
    return (
      <div className="mt-6 space-y-4">
        <h3 className="text-sm font-medium text-muted-foreground">데이터 테이블 (억원)</h3>
        {companies.map((company) => {
          const companyData = data.filter((d) => d.corp_code === company.corp_code)
          if (!companyData.length) return null
          const companyFallbackYears = new Set(companyData.filter((d) => d.is_fallback).map((d) => d.bsns_year))
          const revenueLabel = getRevenueLabel(companyData.find((d) => d.account_key === 'revenue')?.account_nm)
          return (
            <div key={company.corp_code}>
              <p className="text-xs font-semibold mb-1">{company.company_name}</p>
              <TableGrid data={companyData} accountKeys={accountKeys} years={years} yearReprtMap={yearReprtMap} fallbackYears={companyFallbackYears} revenueLabel={revenueLabel} />
            </div>
          )
        })}
      </div>
    )
  }

  // 단일 기업
  const valByYear = chartType === 'bs' && valuationData
    ? new Map(valuationData.yearly.map((v) => [v.year, v]))
    : null
  const revenueLabel = getRevenueLabel(data.find((d) => d.account_key === 'revenue')?.account_nm)

  return (
    <div className="mt-6">
      <h3 className="text-sm font-medium text-muted-foreground mb-2">데이터 테이블 (억원)</h3>
      <TableGrid
        data={data}
        accountKeys={accountKeys}
        years={years}
        yearReprtMap={yearReprtMap}
        revenueLabel={revenueLabel}
        fallbackYears={fallbackYears}
        valByYear={valByYear}
        currentPbr={chartType === 'bs' ? (valuationData?.current_pbr ?? null) : null}
        currentPer={chartType === 'bs' ? (valuationData?.current_per ?? null) : null}
      />
    </div>
  )
}

function TableGrid({
  data,
  accountKeys,
  years,
  yearReprtMap,
  fallbackYears,
  revenueLabel = '매출',
  valByYear = null,
  currentPbr = null,
  currentPer = null,
}: {
  data: FinancialStatement[]
  accountKeys: string[]
  years: string[]
  yearReprtMap: Map<string, string>
  fallbackYears: Set<string>
  revenueLabel?: string
  valByYear?: Map<string, { pbr: number; per: number | null }> | null
  currentPbr?: number | null
  currentPer?: number | null
}) {
  // (account_key, bsns_year) → amount 맵
  const map = new Map<string, number>()
  for (const row of data) {
    map.set(`${row.account_key}__${row.bsns_year}`, row.amount)
  }

  return (
    <div className="overflow-x-auto rounded-md border text-sm">
      <table className="w-full">
        <thead>
          <tr className="bg-muted/50">
            <th className="text-left px-3 py-2 font-medium text-muted-foreground w-28">구분</th>
            {years.map((y) => (
              <th key={y} className="text-right px-3 py-2 font-medium text-muted-foreground">
                {formatYearLabel(y, yearReprtMap.get(y) ?? '')}
                {fallbackYears.has(y) && (
                  <span className="ml-1 text-xs text-amber-500 font-normal">(별도)</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {accountKeys.map((key, i) => (
            <tr key={key} className={i % 2 === 0 ? '' : 'bg-muted/20'}>
              <td className="px-3 py-2 text-muted-foreground">{key === 'revenue' ? revenueLabel : (ACCOUNT_LABELS[key] ?? key)}</td>
              {years.map((y) => {
                const amount = map.get(`${key}__${y}`)
                return (
                  <td key={y} className="px-3 py-2 text-right tabular-nums">
                    {amount !== undefined ? formatBillion(amount) : '-'}
                  </td>
                )
              })}
            </tr>
          ))}
          {valByYear && (
            <>
              <tr className="border-t">
                <td className="px-3 py-2 text-muted-foreground">PBR</td>
                {years.map((y) => {
                  const val = valByYear.get(y)
                  const isLatest = y === years[years.length - 1]
                  const pbr = isLatest && currentPbr != null ? currentPbr : val?.pbr
                  return (
                    <td key={y} className="px-3 py-2 text-right tabular-nums">
                      {pbr != null ? `${pbr.toFixed(2)}x` : '-'}
                    </td>
                  )
                })}
              </tr>
              <tr className="bg-muted/20">
                <td className="px-3 py-2 text-muted-foreground">PER</td>
                {years.map((y) => {
                  const val = valByYear.get(y)
                  const isLatest = y === years[years.length - 1]
                  const per = isLatest && currentPer != null ? currentPer : val?.per
                  return (
                    <td key={y} className="px-3 py-2 text-right tabular-nums">
                      {per != null ? `${per.toFixed(1)}x` : '-'}
                    </td>
                  )
                })}
              </tr>
            </>
          )}
        </tbody>
      </table>
    </div>
  )
}
