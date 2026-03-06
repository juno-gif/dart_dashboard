import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  // H2: env vars 미설정 시 placeholder fallback (런타임 TypeError 방지)
  const supabaseUrl =
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? 'https://placeholder.supabase.co'
  const supabaseAnonKey =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? 'placeholder-anon-key'

  let response = NextResponse.next({
    request: { headers: request.headers },
  })

  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll()
      },
      // H1: request와 response 모두 업데이트 (@supabase/ssr 공식 패턴)
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) =>
          request.cookies.set(name, value)
        )
        response = NextResponse.next({ request })
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options)
        )
      },
    },
  })

  // M1: getSession() 대신 getUser()로 서버 측 검증 수행
  const { data: { user } } = await supabase.auth.getUser()

  const isDashboard = request.nextUrl.pathname.startsWith('/dashboard')
  const isLoginPage = request.nextUrl.pathname.startsWith('/login')

  // 비인증 사용자 → /login 리디렉션
  if (isDashboard && !user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // 이미 인증된 사용자가 /login 접근 → /dashboard 리디렉션
  if (isLoginPage && user) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api|shared).*)'],
}
