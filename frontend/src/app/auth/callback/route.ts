import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const tempUserId = requestUrl.searchParams.get('temp_user_id')

  if (code) {
    const supabase = createRouteHandlerClient({ cookies })
    const { data: { session } } = await supabase.auth.exchangeCodeForSession(code)
    
    if (session && tempUserId) {
      // Merge anonymous session with authenticated session
      await supabase.rpc('merge_user_sessions', {
        p_temp_user_id: tempUserId,
        p_user_id: session.user.id
      })
    }
  }

  return NextResponse.redirect(requestUrl.origin)
}