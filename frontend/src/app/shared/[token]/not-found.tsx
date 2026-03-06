/**
 * 공유 링크 404 커스텀 페이지 — Story 4.2
 * notFound() 호출 시 표시
 */
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h1 className="text-2xl font-bold">유효하지 않은 공유 링크입니다.</h1>
      <p className="text-muted-foreground">링크가 만료되었거나 존재하지 않습니다.</p>
    </div>
  )
}
