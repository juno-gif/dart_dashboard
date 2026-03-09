/**
 * 공유 링크 읽기 전용 뷰어 — Story 4.2
 * Server Component: 인증 없이 직접 fetch → 미들웨어 제외 (middleware.ts matcher)
 * [Source: architecture.md - Frontend Architecture - Server Components]
 */
import { notFound } from 'next/navigation'
import { CompareChart, COMPANY_COLORS } from '@/components/charts/CompareChart'
import { FinancialChart } from '@/components/charts/FinancialChart'
import { FinancialTable } from '@/components/charts/FinancialTable'
import type { Company, FinancialStatement } from '@/types'

interface SharedFinancial {
  corp_code: string
  bsns_year: string
  reprt_code: string
  fs_div: string
  account_key: string
  account_nm: string | null
  amount: number | null
}

interface SharedData {
  id: string
  name: string
  company_codes: string[]
  financials: SharedFinancial[]
}

async function getSharedData(token: string): Promise<SharedData | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const res = await fetch(`${apiUrl}/api/v1/shared/${token}`, {
    cache: 'no-store',
  })
  if (res.status === 404) return null
  if (!res.ok) throw new Error('Failed to fetch shared data')
  return res.json()
}

async function getCompaniesByCodes(codes: string[], apiUrl: string): Promise<Company[]> {
  if (codes.length === 0) return []
  try {
    const res = await fetch(
      `${apiUrl}/api/v1/companies/by-codes?codes=${encodeURIComponent(codes.join(','))}`,
      { cache: 'no-store' }
    )
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

const PL_KEYS = ['revenue', 'operating_profit', 'net_income']

export default async function SharedPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const data = await getSharedData(token)

  if (!data) {
    notFound()
  }

  const isCompareMode = data.company_codes.length >= 2

  const fetchedCompanies = await getCompaniesByCodes(data.company_codes, apiUrl)
  const companyNameMap = new Map(fetchedCompanies.map((c) => [c.corp_code, c.company_name]))

  const companies: Company[] = data.company_codes.map((code) => ({
    corp_code: code,
    company_name: companyNameMap.get(code) ?? code,
    stock_code: null,
    is_listed: true,
    created_at: '',
  }))

  const financials = data.financials as unknown as FinancialStatement[]
  const plFinancials = financials.filter((f) => PL_KEYS.includes(f.account_key))

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-6">
      {/* 헤더: 이름 + 읽기 전용 배지 */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{data.name}</h1>
        <span className="text-xs text-muted-foreground border rounded-full px-3 py-1">
          읽기 전용
        </span>
      </div>

      {/* 기업 태그 */}
      <div className="flex flex-wrap gap-2">
        {companies.map((company, idx) => (
          <div
            key={company.corp_code}
            className="flex items-center gap-1 px-3 py-1 rounded-full text-sm border"
            style={{
              backgroundColor: `${COMPANY_COLORS[idx % COMPANY_COLORS.length]}18`,
              borderColor: COMPANY_COLORS[idx % COMPANY_COLORS.length],
            }}
          >
            <span>{company.company_name}</span>
          </div>
        ))}
      </div>

      {/* 차트 (편집·저장·삭제 버튼 없음) */}
      {isCompareMode ? (
        <CompareChart
          data={financials}
          companies={companies}
          isLoading={false}
        />
      ) : (
        <FinancialChart
          data={plFinancials}
          isLoading={false}
          type="pl"
        />
      )}

      {/* 데이터 테이블 */}
      <FinancialTable
        data={plFinancials}
        chartType="pl"
        companies={isCompareMode ? companies : undefined}
      />
    </main>
  )
}
