'use client'

import { QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { toast } from 'sonner'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error: unknown) => {
            const apiError = error as { error?: string }
            // DART 장애는 배너로 처리 → Toast 제외
            if (apiError?.error === 'DART_API_UNAVAILABLE') return
            // 동시에 여러 쿼리 실패해도 토스트 1개만 표시
            toast.error('잠시 후 재시도해 주세요', {
              id: 'query-error',
              duration: 5000,
            })
          },
        }),
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1분
            retry: 3,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}
