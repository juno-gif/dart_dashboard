/**
 * Supabase 클라이언트 (anon key — 공개 사용 가능)
 * [Source: architecture.md - Authentication & Security]
 * 빌드 타임 env vars 미설정 시 placeholder 사용 (실제 기능 비작동)
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl =
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? 'https://placeholder.supabase.co'
const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? 'placeholder-anon-key'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

/** 현재 세션(JWT)을 반환하는 헬퍼 */
export async function getSession() {
  const { data } = await supabase.auth.getSession()
  return data.session
}
