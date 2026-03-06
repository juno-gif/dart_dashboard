'use client'
import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchCompanies } from '@/lib/api'
import type { Company } from '@/types'

export function useCompanySearch() {
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  // 300ms 디바운스
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(timer)
  }, [query])

  const { data: results = [], isLoading, isError } = useQuery<Company[]>({
    queryKey: ['company-search', debouncedQuery],
    queryFn: () => searchCompanies(debouncedQuery),
    enabled: debouncedQuery.length >= 1,
    staleTime: 60_000,
  })

  return { query, setQuery, results, isLoading, isError }
}
