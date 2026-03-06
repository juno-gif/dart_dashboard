'use client'

/**
 * Story 5.1: CommandEmpty에 "수기 입력으로 추가" 버튼 추가
 * DART 검색 결과 없을 때 ManualEntryDialog 열기
 */
import { useState } from 'react'
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { Button } from '@/components/ui/button'
import { useCompanySearch } from '@/hooks/use-company-search'
import { ManualEntryDialog } from '@/components/search/ManualEntryDialog'
import type { Company } from '@/types'

interface Props {
  onSelect: (company: Company) => void
  disabled?: boolean
}

export function CompanySearchInput({ onSelect, disabled }: Props) {
  const { query, setQuery, results, isLoading } = useCompanySearch()
  const [manualDialogOpen, setManualDialogOpen] = useState(false)

  const handleSelect = (company: Company) => {
    if (disabled) return
    onSelect(company)
    setQuery('')
  }

  const handleManualSelect = (company: Company) => {
    setQuery('')
    onSelect(company)
  }

  return (
    <>
      <Command
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={!disabled && results.length > 0}
      >
        <CommandInput
          placeholder="기업명 입력 (예: 삼성전자, 카카오)"
          value={query}
          onValueChange={disabled ? undefined : setQuery}
          disabled={disabled}
          className={disabled ? 'cursor-not-allowed opacity-50' : ''}
        />
        {!disabled && <CommandList>
          {isLoading && query.length >= 1 && (
            <div className="py-2 px-3 text-sm text-gray-500">검색 중...</div>
          )}
          {!isLoading && query.length >= 1 && (
            <CommandEmpty>
              <div>&apos;{query}&apos;에 대한 결과 없음</div>
              <div className="text-xs text-gray-400 mt-1">종목코드로 검색해보세요</div>
              <div className="mt-3 text-xs text-gray-500 px-1">
                DART에 등록되지 않은 기업입니다. 수기로 재무 데이터를 입력하시겠습니까?
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={() => setManualDialogOpen(true)}
              >
                수기 입력으로 추가
              </Button>
            </CommandEmpty>
          )}
          {results.map((company) => (
            <CommandItem
              key={company.corp_code}
              onSelect={() => handleSelect(company)}
            >
              <span>{company.company_name}</span>
              {company.stock_code && (
                <span className="ml-2 text-xs text-gray-400">{company.stock_code}</span>
              )}
              {!company.is_listed && (
                <span className="ml-2 text-xs text-muted-foreground">(비상장)</span>
              )}
            </CommandItem>
          ))}
        </CommandList>}
      </Command>

      <ManualEntryDialog
        open={manualDialogOpen}
        onOpenChange={setManualDialogOpen}
        initialCompanyName={query}
        onSelect={handleManualSelect}
      />
    </>
  )
}
