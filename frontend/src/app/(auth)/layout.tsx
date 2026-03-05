// (auth) route group — 인증이 필요한 페이지들의 공통 레이아웃
// Story 2.1에서 사이드바 + 헤더 추가 예정
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <div className="min-h-screen">{children}</div>
}
