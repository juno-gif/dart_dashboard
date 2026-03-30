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

  const showList = !disabled && query.length >= 1

  return (
    <>
      <div className="relative">
        <Command
          shouldFilter={false}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={showList}
          className="overflow-visible"
        >
          <CommandInput
            placeholder="기업명 입력 (예: 삼성전자, SK하이닉스)"
            value={query}
            onValueChange={disabled ? undefined : setQuery}
            disabled={disabled}
            className={disabled ? 'cursor-not-allowed opacity-50' : ''}
          />
          {showList && (
            <CommandList className="absolute top-full left-0 right-0 z-50 mt-1 rounded-md border bg-popover shadow-md">
              {isLoading && (
                <div className="py-2 px-3 text-sm text-gray-500">검색 중...</div>
              )}
              {!isLoading && (
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
              {results.length > 0 && (
                <div className="border-t px-3 py-2">
                  <button
                    onMouseDown={(e) => { e.preventDefault(); setManualDialogOpen(true) }}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    + DART에 데이터가 없나요? 수기로 입력
                  </button>
                </div>
              )}
            </CommandList>
          )}
        </Command>
      </div>

      <ManualEntryDialog
        open={manualDialogOpen}
        onOpenChange={setManualDialogOpen}
        initialCompanyName={query}
        onSelect={handleManualSelect}
      />
    </>
  )
}
