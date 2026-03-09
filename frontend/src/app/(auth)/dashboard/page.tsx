'use client'
import { useState, useEffect } from 'react'
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
import { checkHealth, getNewDataStatus, getCompaniesByCodes } from '@/lib/api'
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
  // 같은 탭 세션 내 새로고침 시 헬스체크 스피너 재표시 방지
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

  const { analysisSets, isLoading: setsLoading, loadSet, deleteSet } = useAnalysisSets()

  const companyCodes = selectedCompanies.map((c) => c.corp_code)
  const { data: newDataStatus } = useQuery({
    queryKey: ['new-data-status', companyCodes],
    queryFn: () => getNewDataStatus(companyCodes),
    enabled: companyCodes.length > 0,
  })
  const newDataCodes = new Set(newDataStatus?.new_data_codes ?? [])

  const [chartType, setChartType] = useState<FinancialType>('pl')
  const [fsDivFilter, setFsDivFilter] = useState<'CFS' | 'OFS'>('CFS')
  // 비교 모드에서 특정 기업 상세 드릴다운
  const [focusedCorpCode, setFocusedCorpCode] = useState<string | null>(null)

  const isCompareMode = selectedCompanies.length >= 2
  const isAtMax = selectedCompanies.length >= MAX_COMPANIES
  const primaryCompany = selectedCompanies[0] ?? null

  // 비교 모드 해제 시 포커스 초기화
  useEffect(() => {
    if (!isCompareMode) setFocusedCorpCode(null)
  }, [isCompareMode])

  // 단일 기업 상세 조회 대상: 단일 모드면 primaryCompany, 비교 모드면 focusedCorpCode
  const detailCorpCode = !isCompareMode ? (primaryCompany?.corp_code ?? null) : focusedCorpCode
  const detailCompany = detailCorpCode ? (selectedCompanies.find((c) => c.corp_code === detailCorpCode) ?? null) : null

  // 기업(상세 대상) 변경 시 연결/별도 필터 초기화
  useEffect(() => {
    setFsDivFilter('CFS')
  }, [detailCorpCode])

  // 단일/포커스 기업: CFS+OFS 전체 조회 후 클라이언트 필터링
  const { data: allFinancials = [], isLoading: singleLoading, error: singleError } = useFinancialData(
    detailCorpCode,
    10,
    chartType
    // fsDivParam 기본값 'ALL' — 훅에서 지정됨
  )

  // 사용 가능한 fs_div 목록 도출
  const availableFsDivs = new Set(allFinancials.map((d) => d.fs_div))
  const showFsDivTabs = availableFsDivs.has('CFS') && availableFsDivs.has('OFS')
  // CFS 없으면 OFS로 자동 전환
  const activeFsDiv = availableFsDivs.has(fsDivFilter) ? fsDivFilter : (availableFsDivs.has('CFS') ? 'CFS' : 'OFS')
  const financials = allFinancials.filter((d) => d.fs_div === activeFsDiv)

  const { data: compareData = [], isLoading: compareLoading, error: compareError } =
    useCompareFinancials(
      isCompareMode ? selectedCompanies.map((c) => c.corp_code) : []
    )

  const isDetailView = !isCompareMode || !!focusedCorpCode
  const activeError = isDetailView ? singleError : compareError
  const activeData = isDetailView ? financials : compareData
  const hasDartError =
    (activeError as { error?: string } | null)?.error === 'DART_API_UNAVAILABLE'

  const handleSelect = (company: Company) => {
    if (isAtMax) return
    if (!selectedCompanies.find((c) => c.corp_code === company.corp_code)) {
      setSelectedCompanies((prev) => [...prev, company])
    }
  }

  const handleRemove = (corp_code: string) => {
    setSelectedCompanies((prev) => prev.filter((c) => c.corp_code !== corp_code))
    if (focusedCorpCode === corp_code) setFocusedCorpCode(null)
  }

  const handleLoadAnalysisSet = async (setId: string) => {
    const data = await loadSet.mutateAsync(setId)
    const codes = data.company_codes.slice(0, MAX_COMPANIES)
    const companies = await getCompaniesByCodes(codes)
    const nameMap = new Map(companies.map((c) => [c.corp_code, c]))
    const restored: Company[] = codes.map((code) => {
      const found = nameMap.get(code)
      return found ?? {
        corp_code: code,
        company_name: code,
        stock_code: null,
        is_listed: true,
        created_at: '',
      }
    })
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
        <div className="flex gap-2">
          <div className="flex-1 min-w-0">
            <CompanySearchInput onSelect={handleSelect} disabled={isAtMax} />
          </div>
          {selectedCompanies.length > 0 && (
            <button
              onClick={() => setSelectedCompanies([])}
              className="shrink-0 px-3 py-1.5 text-sm border rounded-md text-muted-foreground hover:bg-muted transition-colors"
            >
              초기화
            </button>
          )}
        </div>
        {isAtMax && (
          <p className="text-xs text-muted-foreground px-1">
            최대 5개 기업까지 비교 가능
          </p>
        )}
      </div>

      {/* CompanyTag 목록 */}
      {isCompareMode && (
        <p className="text-xs text-muted-foreground">기업 태그를 클릭하면 상세 실적을 확인할 수 있습니다.</p>
      )}
      <div className="flex flex-wrap gap-2">
        {selectedCompanies.map((c, idx) => {
          const isFocused = focusedCorpCode === c.corp_code
          const color = COMPANY_COLORS[idx % COMPANY_COLORS.length]
          return (
            <div
              key={c.corp_code}
              onClick={isCompareMode ? () => setFocusedCorpCode(isFocused ? null : c.corp_code) : undefined}
              className={`flex items-center gap-1 px-3 py-1 rounded-full text-sm border transition-all ${
                isCompareMode ? 'cursor-pointer hover:opacity-80' : ''
              } ${isFocused ? 'ring-2 ring-offset-1 ring-current' : ''}`}
              style={{
                backgroundColor: `${color}${isFocused ? '30' : '18'}`,
                borderColor: color,
                color: isFocused ? color : undefined,
              }}
            >
              {newDataCodes.has(c.corp_code) && (
                <span className="text-green-500 text-xs" title="신규 데이터 있음">●</span>
              )}
              <span>{c.company_name}</span>
              {!c.is_listed && (
                <span className="text-xs opacity-60">(비상장)</span>
              )}
              {c.stock_code && (
                <span className="text-xs opacity-50 ml-1">{c.stock_code}</span>
              )}
              {!c.is_listed && (
                <button
                  onClick={(e) => { e.stopPropagation(); setEditingCorpCode(c.corp_code) }}
                  className="ml-1 text-xs text-blue-500 hover:text-blue-700"
                  aria-label={`${c.company_name} 재무 데이터 수정`}
                >
                  편집
                </button>
              )}
              <button
                onClick={(e) => { e.stopPropagation(); handleRemove(c.corp_code) }}
                className="ml-1 opacity-40 hover:opacity-80"
                aria-label={`${c.company_name} 제거`}
              >
                ×
              </button>
            </div>
          )
        })}
      </div>

      {/* DART 경고 배너 */}
      {(activeData.length > 0 || hasDartError) && (
        <DartWarningBanner data={activeData} hasDartError={hasDartError} />
      )}

      {/* 뷰 전환: 비교 / 드릴다운 / 단일 / 빈 상태 */}
      {isCompareMode && !focusedCorpCode ? (
        <>
          <CompareChart
            data={compareData}
            companies={selectedCompanies}
            isLoading={compareLoading}
          />
          <FinancialTable data={compareData} chartType="pl" companies={selectedCompanies} />
        </>
      ) : detailCompany ? (
        <>
          {/* 비교 모드 드릴다운 시 돌아가기 링크 */}
          {isCompareMode && (
            <button
              onClick={() => setFocusedCorpCode(null)}
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 -mb-2"
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
          </div>
          <KPICard data={financials} isLoading={singleLoading} chartType={chartType} />
          <FinancialChart data={financials} isLoading={singleLoading} companyName={detailCompany.company_name} type={chartType} />
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
