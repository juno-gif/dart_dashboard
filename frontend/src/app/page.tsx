import { redirect } from 'next/navigation'

// 루트(/) → /dashboard 리디렉션
// Story 2.1에서 인증 미들웨어(middleware.ts)가 /login으로 리디렉션 처리 예정
export default function RootPage() {
  redirect('/dashboard')
}
