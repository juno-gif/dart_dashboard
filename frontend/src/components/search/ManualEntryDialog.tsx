'use client'

/**
 * 비상장사 수기 입력/편집 다이얼로그 — Story 5.1 / 5.2
 * POST /api/v1/companies/manual → 신규 생성 (create 모드)
 * PUT  /api/v1/companies/{corp_code}/manual → 기존 수정 (edit 모드)
 * [Source: architecture.md - Frontend Architecture, shadcn/ui Dialog 패턴]
 */
import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { createManualCompany, getManualCompanyFinancials, updateManualCompany } from '@/lib/api'
import type { Company } from '@/types'

interface FinancialRow {
  bsns_year: string
  revenue: string
  operating_profit: string
  net_income: string
}

interface FinancialRowError {
  bsns_year?: string
  revenue?: string
  operating_profit?: string
  net_income?: string
}

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  initialCompanyName?: string
  onSelect: (company: Company) => void
  /** 편집 모드: 'edit' 시 corpCode 필수 */
  mode?: 'create' | 'edit'
  corpCode?: string
}

const EMPTY_ROW: FinancialRow = { bsns_year: '', revenue: '', operating_profit: '', net_income: '' }

function isValidNumber(val: string) {
  return val === '' || /^-?\d+$/.test(val.trim())
}

export function ManualEntryDialog({ open, onOpenChange, initialCompanyName = '', onSelect, mode = 'create', corpCode }: Props) {
  const queryClient = useQueryClient()
  const [companyName, setCompanyName] = useState(initialCompanyName)
  const [companyNameError, setCompanyNameError] = useState('')
  const [rows, setRows] = useState<FinancialRow[]>([{ ...EMPTY_ROW }])
  const [rowErrors, setRowErrors] = useState<FinancialRowError[]>([{}])

  // 편집 모드: 기존 재무 데이터 로드
  const { data: existingData } = useQuery({
    queryKey: ['manual-company-financials', corpCode],
    queryFn: () => getManualCompanyFinancials(corpCode!),
    enabled: mode === 'edit' && open && !!corpCode,
  })

  // 기존 데이터 로드 시 폼 prefill (원 → 억 단위 변환)
  useEffect(() => {
    if (mode === 'edit' && existingData) {
      setCompanyName(existingData.company_name)
      const prefilled = existingData.financials.map((f) => ({
        bsns_year: f.bsns_year,
        revenue: f.revenue != null ? String(Math.round(f.revenue / 100_000_000)) : '',
        operating_profit: f.operating_profit != null ? String(Math.round(f.operating_profit / 100_000_000)) : '',
        net_income: f.net_income != null ? String(Math.round(f.net_income / 100_000_000)) : '',
      }))
      setRows(prefilled.length > 0 ? prefilled : [{ ...EMPTY_ROW }])
      setRowErrors(new Array(prefilled.length || 1).fill({}))
    }
  }, [mode, existingData])

  const mutation = useMutation({
    mutationFn: createManualCompany,
    onSuccess: (company) => {
      toast.success('비상장사 데이터가 저장되었습니다', { duration: 3000 })
      onSelect(company)
      onOpenChange(false)
      // reset
      setCompanyName('')
      setRows([{ ...EMPTY_ROW }])
      setRowErrors([{}])
    },
    onError: () => {
      toast.error('저장에 실패했습니다. 다시 시도해 주세요.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Parameters<typeof updateManualCompany>[1]) =>
      updateManualCompany(corpCode!, data),
    onSuccess: (company) => {
      toast.success('재무 데이터가 수정되었습니다', { duration: 3000 })
      // 차트 데이터 캐시 무효화 — 수정된 재무 데이터가 즉시 반영되도록
      queryClient.invalidateQueries({ queryKey: ['financials', corpCode] })
      queryClient.invalidateQueries({ queryKey: ['compare'] })
      queryClient.invalidateQueries({ queryKey: ['manual-company-financials', corpCode] })
      onSelect(company)
      onOpenChange(false)
    },
    onError: () => {
      toast.error('수정에 실패했습니다. 다시 시도해 주세요.')
    },
  })

  const validate = (): boolean => {
    let valid = true
    if (!companyName.trim()) {
      setCompanyNameError('필수 항목입니다')
      valid = false
    } else {
      setCompanyNameError('')
    }

    const newRowErrors: FinancialRowError[] = rows.map((row) => {
      const err: FinancialRowError = {}
      if (!row.bsns_year.trim()) {
        err.bsns_year = '필수 항목입니다'
        valid = false
      } else if (!/^\d{4}$/.test(row.bsns_year.trim())) {
        err.bsns_year = '4자리 연도를 입력하세요'
        valid = false
      }
      if (row.revenue && !isValidNumber(row.revenue)) {
        err.revenue = '숫자만 입력하세요'
        valid = false
      }
      if (row.operating_profit && !isValidNumber(row.operating_profit)) {
        err.operating_profit = '숫자만 입력하세요'
        valid = false
      }
      if (row.net_income && !isValidNumber(row.net_income)) {
        err.net_income = '숫자만 입력하세요'
        valid = false
      }
      return err
    })
    setRowErrors(newRowErrors)
    return valid
  }

  const handleSubmit = () => {
    if (!validate()) return

    const payload = {
      company_name: companyName.trim(),
      financials: rows.map((row) => ({
        bsns_year: row.bsns_year.trim(),
        // 억 단위 → 원 단위 변환 (빈 값은 null)
        revenue: row.revenue ? parseInt(row.revenue, 10) * 100_000_000 : null,
        operating_profit: row.operating_profit ? parseInt(row.operating_profit, 10) * 100_000_000 : null,
        net_income: row.net_income ? parseInt(row.net_income, 10) * 100_000_000 : null,
      })),
    }

    if (mode === 'edit') {
      updateMutation.mutate(payload)
    } else {
      mutation.mutate(payload)
    }
  }

  const addRow = () => {
    if (rows.length >= 5) return
    setRows([...rows, { ...EMPTY_ROW }])
    setRowErrors([...rowErrors, {}])
  }

  const updateRow = (idx: number, field: keyof FinancialRow, value: string) => {
    setRows(rows.map((r, i) => (i === idx ? { ...r, [field]: value } : r)))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[600px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === 'edit' ? '비상장사 재무 데이터 수정' : '비상장사 재무 데이터 수기 입력'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* 기업명 */}
          <div>
            <label className="text-sm font-medium">기업명 *</label>
            <Input
              className="mt-1"
              placeholder="기업명 입력"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
            />
            {companyNameError && (
              <p className="text-xs text-destructive mt-1">{companyNameError}</p>
            )}
          </div>

          {/* 연도별 입력 */}
          <div className="space-y-3">
            <p className="text-sm font-medium">재무 데이터 (억 단위 입력)</p>
            {rows.map((row, idx) => (
              <div key={idx} className="border rounded p-3 space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-muted-foreground">사업연도 *</label>
                    <Input
                      placeholder="예: 2024"
                      value={row.bsns_year}
                      onChange={(e) => updateRow(idx, 'bsns_year', e.target.value)}
                    />
                    {rowErrors[idx]?.bsns_year && (
                      <p className="text-xs text-destructive mt-1">{rowErrors[idx].bsns_year}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">매출 (억)</label>
                    <Input
                      placeholder="예: 5000"
                      value={row.revenue}
                      onChange={(e) => updateRow(idx, 'revenue', e.target.value)}
                    />
                    {rowErrors[idx]?.revenue && (
                      <p className="text-xs text-destructive mt-1">{rowErrors[idx].revenue}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">영업이익 (억)</label>
                    <Input
                      placeholder="예: 500"
                      value={row.operating_profit}
                      onChange={(e) => updateRow(idx, 'operating_profit', e.target.value)}
                    />
                    {rowErrors[idx]?.operating_profit && (
                      <p className="text-xs text-destructive mt-1">{rowErrors[idx].operating_profit}</p>
                    )}
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">순이익 (억)</label>
                    <Input
                      placeholder="예: 350"
                      value={row.net_income}
                      onChange={(e) => updateRow(idx, 'net_income', e.target.value)}
                    />
                    {rowErrors[idx]?.net_income && (
                      <p className="text-xs text-destructive mt-1">{rowErrors[idx].net_income}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addRow}
              disabled={rows.length >= 5}
            >
              + 연도 추가 ({rows.length}/5)
            </Button>
          </div>

          {/* 제출 버튼 */}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              취소
            </Button>
            <Button onClick={handleSubmit} disabled={mutation.isPending || updateMutation.isPending}>
              {(mutation.isPending || updateMutation.isPending)
                ? '저장 중...'
                : mode === 'edit' ? '수정' : '저장'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
