import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type')
  const next = searchParams.get('next') ?? '/dashboard'

  if (code || (token_hash && type)) {
    const cookieStore = await cookies()
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return cookieStore.getAll()
          },
          setAll(cookiesToSet) {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          },
        },
      }
    )

    let error = null

    if (code) {
      // PKCE flow (OAuth, SSO)
      ;({ error } = await supabase.auth.exchangeCodeForSession(code))
    } else if (token_hash && type) {
      // Magic Link / OTP flow
      ;({ error } = await supabase.auth.verifyOtp({
        token_hash,
        type: type as Parameters<typeof supabase.auth.verifyOtp>[0]['type'],
      }))
    }

    if (!error) {
      return NextResponse.redirect(`${origin}${next}`)
    }
  }

  // 실패 시 로그인 페이지로
  return NextResponse.redirect(`${origin}/login`)
}
