'use client'

// (auth) route group — 인증이 필요한 페이지들의 공통 레이아웃
// Story 2.1: 클라이언트 인증 가드 추가 (middleware와 이중 방어)
// Story 2.3: Admin 전용 팀 관리 메뉴 추가
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/hooks/use-auth'
import { useQuery } from '@tanstack/react-query'
import { getUserProfile } from '@/lib/api'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { session, isLoading } = useAuth()
  const router = useRouter()

  const { data: profile } = useQuery({
    queryKey: ['user-profile'],
    queryFn: getUserProfile,
    enabled: !!session,
  })

  useEffect(() => {
    if (!isLoading && !session) {
      router.replace('/login')
    }
  }, [isLoading, session, router])

  // 세션 로딩 중: null 반환 (레이아웃 쉬프트 방지)
  if (isLoading) return null

  // 세션 없음: 리디렉션 중 (렌더 방지)
  if (!session) return null

  return (
    <div className="min-h-screen">
      {/* Admin 전용 팀 관리 네비게이션 */}
      {profile?.role === 'admin' && (
        <nav className="border-b bg-background px-6 py-2 flex gap-4 text-sm">
          <Link href="/dashboard" className="hover:underline text-muted-foreground hover:text-foreground">
            대시보드
          </Link>
          <Link href="/dashboard/team" className="hover:underline text-muted-foreground hover:text-foreground">
            팀 관리
          </Link>
        </nav>
      )}
      {children}
    </div>
  )
}
