'use client'

export default function SharedError() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold">오류가 발생했습니다</h1>
        <p className="text-muted-foreground">잠시 후 다시 시도해 주세요.</p>
      </div>
    </div>
  )
}
