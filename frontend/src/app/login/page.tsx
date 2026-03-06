'use client'

import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/dashboard`,
      },
    })

    if (error) {
      setError(error.message)
    } else {
      setSent(true)
    }
    setIsLoading(false)
  }

  if (sent) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="w-full max-w-sm rounded-lg bg-white p-8 shadow text-center">
          <h1 className="mb-2 text-xl font-semibold">이메일을 확인하세요</h1>
          <p className="text-gray-600 text-sm">로그인 링크가 발송되었습니다</p>
        </div>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-lg bg-white p-8 shadow">
        <h1 className="mb-6 text-xl font-semibold text-center">로그인</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="email"
            placeholder="이메일 입력"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
          />
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? '전송 중...' : '매직 링크 전송'}
          </Button>
        </form>
      </div>
    </main>
  )
}
