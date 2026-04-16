'use client'
import { useState, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { CompanySearchInput } from '@/components/search/CompanySearchInput'
import { FinancialChart } from '@/components/charts/FinancialChart'
import { KPICard } from '@/components/charts/KPICard'
import { CompareChart, COMPANY_COLORS } from '@/components/charts/CompareChart'
import { useFinancialData } from '@/hooks/use-financial-data'
import { useCompareFinancials } from '@/hooks/use-compare-financials'
import { useAnalysisSets } from '@/hooks/use-analysis-sets'
import { useValuation } from '@/hooks/use-valuation'
import { DartWarningBanner } from '@/components/layout/DartWarningBanner'
import { AnalysisSidebar } from '@/components/layout/AnalysisSidebar'
import { UpdateAnalysisSetDialog } from '@/components/layout/UpdateAnalysisSetDialog'
import { ShareDialog } from '@/components/layout/ShareDialog'
import { checkHealth, getNewDataStatus, getCompaniesByCodes, syncCompany } from '@/lib/api'
import type { AnalysisSetData } from '@/lib/api'
import type { Company, FinancialStatement, FinancialType } from '@/types'
import { toast } from 'sonner'
import { ManualEntryDialog } from '@/components/search/ManualEntryDialog'
import { FinancialTable } from '@/components/charts/FinancialTable'
import { PBRTrendChart } from '@/components/charts/PBRTrendChart'
import { ErrorReportButton } from '@/components/layout/ErrorReportButton'

const MAX_COMPANIES = 10

function applyFsDivWithFallback(allData: FinancialStatement[], preferredFsDiv: string): FinancialStatement[] {
  const map = new Map<string, FinancialStatement>()
  for (const row of allData) {
    const key = `${row.bsns_year}__${row.account_key}`
    const existing = map.get(key)
    const isPreferred = row.fs_div === preferredFsDiv
    if (!existing) {
      map.set(key, { ...row, is_fallback: !isPreferred })
    } else if (isPreferred && existing.is_fallback) {
      map.set(key, { ...row, is_fallback: false })
    }
  }
  return Array.from(map.values())
}

export default function DashboardPage() {
  const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([])
  const [activeSetId, setActiveSetId] = useState<string | null>(null)
  const [editingSet, setEditingSet] = useState<AnalysisSetData | null>(null)
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false)
  const [editingCorpCode, setEditingCorpCode] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const queryClient = useQueryClient()
  const chartContainerRef = useRef<HTMLDivElement>(null)

  const [skipHealthCheck] = useState(() => {
    if (typeof window === 'undefined') return false
    return sessionStorage.getItem('server_healthy') === '1'
  })

  const { isSuccess: serverReady, isLoading: serverWaking } = useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    retry: 10,
    retryDelay: 5000,
    staleTime: Infinity,
    enabled: !skipHealthCheck,
  })

  useEffect(() => {
    if (serverReady) sessionStorage.setItem('server_healthy', '1')
  }, [serverReady])

  const { loadSet, deleteSet } = useAnalysisSets()

  const companyCodes = selectedCompanies.map((c) => c.corp_code)
  const { data: newDataStatus } = useQuery({
    queryKey: ['new-data-status', companyCodes],
    queryFn: () => getNewDataStatus(companyCodes),
    enabled: companyCodes.length > 0,
  })
  const newDataCodes = new Set(newDataStatus?.new_data_codes ?? [])

  const [chartType, setChartType] = useState<FinancialType>('pl')
  const [fsDivFilter, setFsDivFilter] = useState<'CFS' | 'OFS'>('CFS')
  const [focusedCorpCode, setFocusedCorpCode] = useState<string | null>(null)

  const isCompareMode = selectedCompanies.length >= 2
  const isAtMax = selectedCompanies.length >= MAX_COMPANIES
  const primaryCompany = selectedCompanies[0] ?? null

  useEffect(() => {
    if (!isCompareMode) setFocusedCorpCode(null)
  }, [isCompareMode])

  const detailCorpCode = !isCompareMode ? (primaryCompany?.corp_code ?? null) : focusedCorpCode
  const detailCompany = detailCorpCode ? (selectedCompanies.find((c) => c.corp_code === detailCorpCode) ?? null) : null

  useEffect(() => {
    setFsDivFilter('CFS')
  }, [detailCorpCode])

  const { data: allFinancials = [], isLoading: singleLoading, isLoadingMore: singleLoadingMore, error: singleError } = useFinancialData(
    detailCorpCode,
    10,
    chartType
  )

  const availableFsDivs = new Set(allFinancials.map((d) => d.fs_div))
  const showFsDivTabs = availableFsDivs.has('CFS') && availableFsDivs.has('OFS')
  const activeFsDiv = availableFsDivs.has(fsDivFilter) ? fsDivFilter : (availableFsDivs.has('CFS') ? 'CFS' : 'OFS')
  const financials = applyFsDivWithFallback(allFinancials, activeFsDiv)

  const { data: compareData = [], isLoading: compareLoading, error: compareError } =
    useCompareFinancials(isCompareMode ? selectedCompanies.map((c) => c.corp_code) : [])

  const { data: valuationData, isLoading: valuationLoading } = useValuation(
    detailCompany?.stock_code?.trim() ? detailCorpCode : null
  )

  const isDetailView = !isCompareMode || !!focusedCorpCode
  const activeError = isDetailView ? singleError : compareError
  const activeData = isDetailView ? financials : compareData
  const hasDartError = (activeError as { error?: string } | null)?.error === 'DART_API_UNAVAILABLE'

  const handleSelect = (company: Company) => {
    if (isAtMax) return
    if (!selectedCompanies.find((c) => c.corp_code === company.corp_code)) {
      setSelectedCompanies((prev) => [...prev, company])
      setActiveSetId(null) // 직접 수정 시 active set 해제
    }
  }

  const handleRemove = (corp_code: string) => {
    setSelectedCompanies((prev) => prev.filter((c) => c.corp_code !== corp_code))
    if (focusedCorpCode === corp_code) setFocusedCorpCode(null)
    setActiveSetId(null)
  }

  const handleLoadAnalysisSet = async (setId: string) => {
    const data = await loadSet.mutateAsync(setId)
    const codes = data.company_codes.slice(0, MAX_COMPANIES)
    const companies = await getCompaniesByCodes(codes)
    const nameMap = new Map(companies.map((c) => [c.corp_code, c]))
    const restored: Company[] = codes.map((code) => {
      const found = nameMap.get(code)
      return found ?? { corp_code: code, company_name: code, stock_code: null, is_listed: true, created_at: '' }
    })
    setSelectedCompanies(restored)
    setActiveSetId(setId)
  }

  const handleEditAnalysisSet = (set: AnalysisSetData) => {
    setEditingSet(set)
    setUpdateDialogOpen(true)
  }

  const handleDeleteAnalysisSet = (setId: string) => {
    deleteSet.mutate(setId)
    if (activeSetId === setId) setActiveSetId(null)
  }

  const handleSync = async () => {
    if (!detailCorpCode || syncing) return
    setSyncing(true)
    try {
      await syncCompany(detailCorpCode, 10)
      toast.success('데이터 수집을 시작했습니다. 1~2분 후 자동으로 새로고침됩니다.')
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['financials', detailCorpCode] })
        setSyncing(false)
      }, 90000)
    } catch {
      toast.error('재수집 요청에 실패했습니다.')
      setSyncing(false)
    }
  }

  // 서버 웨이크업 중
  if (serverWaking && !serverReady) {
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-4">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium">서버를 준비하는 중입니다...</p>
        <p className="text-xs text-muted-foreground">무료 플랜 서버는 첫 접속 시 최대 60초가 걸릴 수 있습니다.</p>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* ── 상단 바 ── */}
      <header className="border-b shrink-0 bg-background">
        {/* Row 1: 로고 + 검색 */}
        <div className="h-[52px] flex items-center gap-3 px-4">
          <div className="w-[240px] shrink-0 text-sm font-bold tracking-tight text-foreground">
            DART·대시
          </div>
          <div className="flex-1 max-w-sm">
            <CompanySearchInput onSelect={handleSelect} disabled={isAtMax} />
          </div>
        </div>

        {/* Row 2: 선택된 기업 chips (기업 있을 때만) */}
        {selectedCompanies.length > 0 && (
          <div className="flex items-center gap-2 px-4 pb-2.5 overflow-x-auto">
            {isCompareMode && (
              <span className="text-xs text-muted-foreground shrink-0">클릭하면 상세 확인</span>
            )}
            {selectedCompanies.map((c, idx) => {
              const isFocused = focusedCorpCode === c.corp_code
              const color = COMPANY_COLORS[idx % COMPANY_COLORS.length]
              return (
                <div
                  key={c.corp_code}
                  onClick={isCompareMode ? () => setFocusedCorpCode(isFocused ? null : c.corp_code) : undefined}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs border shrink-0 transition-all ${
                    isCompareMode ? 'cursor-pointer hover:opacity-80' : ''
                  } ${isFocused ? 'ring-2 ring-offset-1 ring-current' : ''}`}
                  style={{
                    backgroundColor: `${color}${isFocused ? '30' : '18'}`,
                    borderColor: color,
                    color: isFocused ? color : undefined,
                  }}
                >
                  {newDataCodes.has(c.corp_code) && (
                    <span className="text-green-500 text-[10px]">●</span>
                  )}
                  <span>{c.company_name}</span>
                  {c.stock_code && <span className="opacity-50">{c.stock_code}</span>}
                  {!c.is_listed && (
                    <button
                      onClick={(e) => { e.stopPropagation(); setEditingCorpCode(c.corp_code) }}
                      className="text-blue-500 hover:text-blue-700"
                    >편집</button>
                  )}
                  <button
                    onClick={(e) => { e.stopPropagation(); handleRemove(c.corp_code) }}
                    className="opacity-40 hover:opacity-80 ml-0.5"
                  >×</button>
                </div>
              )
            })}
            <button
              onClick={() => { setSelectedCompanies([]); setActiveSetId(null) }}
              className="shrink-0 px-2.5 py-1 text-xs border rounded-md text-muted-foreground hover:bg-muted transition-colors"
            >
              선택 취소
            </button>
            {activeSetId && (
              <div className="shrink-0">
                <ShareDialog setId={activeSetId} />
              </div>
            )}
          </div>
        )}
      </header>

      {/* ── 바디 ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* 사이드바 */}
        <AnalysisSidebar
          activeSetId={activeSetId}
          companyCodes={companyCodes}
          onLoad={handleLoadAnalysisSet}
          onEdit={handleEditAnalysisSet}
          onDelete={handleDeleteAnalysisSet}
        />

        {/* 메인 콘텐츠 */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6 max-w-4xl space-y-5">
            {/* DART 경고 배너 */}
            {(activeData.length > 0 || hasDartError) && (
              <DartWarningBanner data={activeData} hasDartError={hasDartError} />
            )}

            {/* 비교 / 드릴다운 / 단일 / 빈 상태 */}
            {isCompareMode && !focusedCorpCode ? (
              <>
                <CompareChart data={compareData} companies={selectedCompanies} isLoading={compareLoading} />
                <FinancialTable data={compareData} chartType="pl" companies={selectedCompanies} />
              </>
            ) : detailCompany ? (
              <>
                {isCompareMode && (
                  <button
                    onClick={() => setFocusedCorpCode(null)}
                    className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
                  >
                    ← 전체 비교로 돌아가기
                  </button>
                )}
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
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
                  {showFsDivTabs && (
                    <div className="flex gap-1">
                      {(['CFS', 'OFS'] as const).map((fsDiv) => (
                        <button
                          key={fsDiv}
                          onClick={() => setFsDivFilter(fsDiv)}
                          className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                            activeFsDiv === fsDiv
                              ? 'bg-secondary text-secondary-foreground'
                              : 'border text-muted-foreground hover:bg-muted'
                          }`}
                        >
                          {fsDiv === 'CFS' ? '연결' : '별도'}
                        </button>
                      ))}
                    </div>
                  )}
                  <div className="ml-auto flex items-center gap-2">
                    {detailCompany.is_listed && (
                      <button
                        onClick={handleSync}
                        disabled={syncing}
                        className="px-3 py-1 text-xs border rounded-md text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
                      >
                        {syncing ? '수집 중...' : '데이터 재수집'}
                      </button>
                    )}
                    <ErrorReportButton
                      companyName={detailCompany.company_name}
                      chartContainerRef={chartContainerRef}
                      chartType={chartType}
                      setChartType={setChartType}
                    />
                  </div>
                </div>
                {/* 과거 데이터 로딩 중 배너 */}
                {singleLoadingMore && (
                  <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-muted/50 border text-xs text-muted-foreground">
                    <div className="w-3 h-3 border-2 border-muted-foreground/40 border-t-muted-foreground rounded-full animate-spin shrink-0" />
                    최근 3년 데이터를 먼저 표시합니다. 과거 데이터를 불러오는 중...
                  </div>
                )}

                {/* 데이터 없음 (로딩 완전히 끝난 후에만 표시) */}
                {!singleLoading && !singleLoadingMore && financials.length === 0 && (
                  <div className="rounded-lg border bg-muted/40 p-6 text-center space-y-3">
                    <p className="text-sm text-muted-foreground">수집된 재무 데이터가 없습니다.</p>
                    <button
                      onClick={() => setEditingCorpCode(detailCorpCode)}
                      className="px-4 py-2 text-sm border rounded-md hover:bg-muted transition-colors"
                    >
                      실적 수기 입력
                    </button>
                  </div>
                )}
                <div ref={chartContainerRef}>
                  <KPICard
                    data={financials}
                    isLoading={singleLoading}
                    chartType={chartType}
                    valuationData={chartType === 'pl' ? valuationData : undefined}
                  />
                  <FinancialChart data={financials} isLoading={singleLoading} companyName={detailCompany.company_name} type={chartType} />
                  {chartType === 'bs' && (
                    <PBRTrendChart data={valuationData} isLoading={valuationLoading} />
                  )}
                  <FinancialTable
                    data={financials}
                    chartType={chartType}
                    valuationData={chartType === 'bs' ? valuationData : undefined}
                  />
                </div>
              </>
            ) : (
              <div className="mt-12 rounded-lg border bg-muted/40 p-5 space-y-2 text-sm text-muted-foreground">
                <p className="font-medium text-foreground">💡 사용 Tip</p>
                <ul className="space-y-1.5 list-disc list-inside">
                  <li>좌측 분석 세트를 클릭하거나, 상단 검색창에서 기업을 검색해 시작하세요.</li>
                  <li>DART Open API 및 감사보고서 파싱을 통해 수집된 데이터입니다.</li>
                  <li>처음 검색된 기업은 데이터 수집에 다소 시간이 소요됩니다. (1분 내외)</li>
                  <li>PBR/PER은 상장기업에 한해 제공됩니다.</li>
                </ul>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* 수정 다이얼로그 */}
      <UpdateAnalysisSetDialog
        set={editingSet}
        open={updateDialogOpen}
        onOpenChange={setUpdateDialogOpen}
        currentCompanyCodes={companyCodes}
      />

      {/* 비상장사 수기 입력 다이얼로그 */}
      <ManualEntryDialog
        open={!!editingCorpCode}
        onOpenChange={(o) => { if (!o) setEditingCorpCode(null) }}
        onSelect={() => setEditingCorpCode(null)}
        mode="edit"
        corpCode={editingCorpCode ?? undefined}
        initialCompanyName={selectedCompanies.find(c => c.corp_code === editingCorpCode)?.company_name ?? ''}
      />
    </div>
  )
}
