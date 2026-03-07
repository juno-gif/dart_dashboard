'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CompanySearchInput } from '@/components/search/CompanySearchInput'
import { FinancialChart } from '@/components/charts/FinancialChart'
import { KPICard } from '@/components/charts/KPICard'
import { CompareChart, COMPANY_COLORS } from '@/components/charts/CompareChart'
import { useFinancialData } from '@/hooks/use-financial-data'
import { useCompareFinancials } from '@/hooks/use-compare-financials'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'
import { DartWarningBanner } from '@/components/layout/DartWarningBanner'
import { SaveAnalysisSetDialog } from '@/components/layout/SaveAnalysisSetDialog'
import { AnalysisSetPanel } from '@/components/layout/AnalysisSetItem'
import { UpdateAnalysisSetDialog } from '@/components/layout/UpdateAnalysisSetDialog'
import { checkHealth, getNewDataStatus } from '@/lib/api'
import type { AnalysisSetData } from '@/lib/api'
import type { Company, FinancialType } from '@/types'
import { ManualEntryDialog } from '@/components/search/ManualEntryDialog'
import { FinancialTable } from '@/components/charts/FinancialTable'

const MAX_COMPANIES = 5

export default function DashboardPage() {
  const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([])
  const [editingSet, setEditingSet] = useState<AnalysisSetData | null>(null)
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false)
  const [editingCorpCode, setEditingCorpCode] = useState<string | null>(null)

  // 서버 웨이크업 체크 (Render 무료 플랜은 슬립 후 첫 요청에 30~60초 소요)
  const { isSuccess: serverReady, isLoading: serverWaking } = useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    retry: 10,
    retryDelay: 5000,
    staleTime: Infinity,
  })

  const { analysisSets, isLoading: setsLoading, loadSet, deleteSet } = useAnalysisSets()

  const companyCodes = selectedCompanies.map((c) => c.corp_code)
  const { data: newDataStatus } = useQuery({
    queryKey: ['new-data-status', companyCodes],
    queryFn: () => getNewDataStatus(companyCodes),
    enabled: companyCodes.length > 0,
  })
  const newDataCodes = new Set(newDataStatus?.new_data_codes ?? [])

  const [chartType, setChartType] = useState<FinancialType>('pl')

  const isCompareMode = selectedCompanies.length >= 2
  const isAtMax = selectedCompanies.length >= MAX_COMPANIES
  const primaryCompany = selectedCompanies[0] ?? null

  const { data: financials = [], isLoading: singleLoading, error: singleError } = useFinancialData(
    !isCompareMode ? (primaryCompany?.corp_code ?? null) : null,
    5,
    chartType
  )

  const { data: compareData = [], isLoading: compareLoading, error: compareError } =
    useCompareFinancials(
      isCompareMode ? selectedCompanies.map((c) => c.corp_code) : []
    )

  const activeError = isCompareMode ? compareError : singleError
  const activeData = isCompareMode ? compareData : financials
  const hasDartError =
    (activeError as { error?: string } | null)?.error === 'DART_API_UNAVAILABLE'

  const handleSelect = (company: Company) => {
    if (isAtMax) return
    if (!selectedCompanies.find((c) => c.corp_code === company.corp_code)) {
      setSelectedCompanies((prev) => [...prev, company])
    }
  }

  const handleRemove = (corp_code: string) => {
    setSelectedCompanies((prev) =>
      prev.filter((c) => c.corp_code !== corp_code)
    )
  }

  const handleLoadAnalysisSet = async (setId: string) => {
    const data = await loadSet.mutateAsync(setId)
    const restored: Company[] = data.company_codes.slice(0, MAX_COMPANIES).map((code) => ({
      corp_code: code,
      company_name: code,
      stock_code: null,
      is_listed: true,
      created_at: '',
    }))
    setSelectedCompanies(restored)
  }

  const handleEditAnalysisSet = (set: AnalysisSetData) => {
    setEditingSet(set)
    setUpdateDialogOpen(true)
  }

  const handleDeleteAnalysisSet = (setId: string) => {
    deleteSet.mutate(setId)
  }

  if (serverWaking && !serverReady) {
    return (
      <main className="p-6 max-w-5xl mx-auto flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium">서버를 준비하는 중입니다...</p>
        <p className="text-xs text-muted-foreground">무료 플랜 서버는 첫 접속 시 최대 60초가 걸릴 수 있습니다.</p>
      </main>
    )
  }

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold">재무 분석 대시보드</h1>

      {/* 분석 세트 목록 패널 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-muted-foreground">저장된 분석 세트</h2>
          <SaveAnalysisSetDialog companyCodes={selectedCompanies.map((c) => c.corp_code)} />
        </div>
        <AnalysisSetPanel
          analysisSets={analysisSets}
          isLoading={setsLoading}
          onLoad={handleLoadAnalysisSet}
          onEdit={handleEditAnalysisSet}
          onDelete={handleDeleteAnalysisSet}
        />
      </div>

      {/* 수정 다이얼로그 */}
      <UpdateAnalysisSetDialog
        set={editingSet}
        open={updateDialogOpen}
        onOpenChange={setUpdateDialogOpen}
        currentCompanyCodes={selectedCompanies.map((c) => c.corp_code)}
      />

      {/* 기업 검색 (5개 도달 시 비활성화) */}
      <div className="space-y-1">
        <CompanySearchInput onSelect={handleSelect} disabled={isAtMax} />
        {isAtMax && (
          <p className="text-xs text-muted-foreground px-1">
            최대 5개 기업까지 비교 가능
          </p>
        )}
      </div>

      {/* CompanyTag 목록 */}
      <div className="flex flex-wrap gap-2">
        {selectedCompanies.map((c, idx) => (
          <div
            key={c.corp_code}
            className="flex items-center gap-1 px-3 py-1 rounded-full text-sm border"
            style={{
              backgroundColor: `${COMPANY_COLORS[idx % COMPANY_COLORS.length]}18`,
              borderColor: COMPANY_COLORS[idx % COMPANY_COLORS.length],
            }}
          >
            {newDataCodes.has(c.corp_code) && (
              <span className="text-green-500 text-xs" title="신규 데이터 있음">●</span>
            )}
            <span>{c.company_name}</span>
            {!c.is_listed && (
              <span className="text-xs text-muted-foreground">(비상장)</span>
            )}
            {c.stock_code && (
              <span className="text-xs text-gray-500 ml-1">{c.stock_code}</span>
            )}
            {!c.is_listed && (
              <button
                onClick={() => setEditingCorpCode(c.corp_code)}
                className="ml-1 text-xs text-blue-500 hover:text-blue-700"
                aria-label={`${c.company_name} 재무 데이터 수정`}
              >
                편집
              </button>
            )}
            <button
              onClick={() => handleRemove(c.corp_code)}
              className="ml-1 text-gray-400 hover:text-gray-600"
              aria-label={`${c.company_name} 제거`}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      {/* DART 경고 배너 */}
      {(activeData.length > 0 || hasDartError) && (
        <DartWarningBanner data={activeData} hasDartError={hasDartError} />
      )}

      {/* 뷰 전환: 비교 / 단일 / 빈 상태 */}
      {isCompareMode ? (
        <>
          <CompareChart
            data={compareData}
            companies={selectedCompanies}
            isLoading={compareLoading}
          />
          <FinancialTable data={compareData} chartType="pl" companies={selectedCompanies} />
        </>
      ) : primaryCompany ? (
        <>
          <div className="flex gap-2">
            {(['pl', 'bs', 'cf'] as FinancialType[]).map((t) => (
              <button
                key={t}
                onClick={() => setChartType(t)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  chartType === t
                    ? 'bg-primary text-primary-foreground'
                    : 'border text-muted-foreground hover:bg-muted'
                }`}
              >
                {t === 'pl' ? '손익계산서' : t === 'bs' ? '재무상태표' : '현금흐름'}
              </button>
            ))}
          </div>
          <KPICard data={financials} isLoading={singleLoading} />
          <FinancialChart data={financials} isLoading={singleLoading} companyName={primaryCompany.company_name} type={chartType} />
          <FinancialTable data={financials} chartType={chartType} />
        </>
      ) : (
        <p className="text-gray-400 text-center text-sm mt-16">
          기업을 검색하여 추가하세요.
        </p>
      )}

      {/* 비상장사 재무 데이터 편집 다이얼로그 */}
      <ManualEntryDialog
        open={!!editingCorpCode}
        onOpenChange={(o) => { if (!o) setEditingCorpCode(null) }}
        onSelect={() => { setEditingCorpCode(null) }}
        mode="edit"
        corpCode={editingCorpCode ?? undefined}
      />
    </main>
  )
}
