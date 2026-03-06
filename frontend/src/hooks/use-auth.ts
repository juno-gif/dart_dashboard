'use client'

import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

export function useAuth() {
  const [session, setSession] = useState<Session | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // 초기 세션 조회
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setIsLoading(false)
    })

    // 세션 변경 구독 (로그인/로그아웃)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  return {
    session,
    isLoading,
    /** API 요청에 사용할 access_token */
    accessToken: session?.access_token ?? null,
  }
}
