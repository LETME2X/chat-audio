import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })
  
  // Refresh session if exists
  const { data: { session } } = await supabase.auth.getSession()
  
  // If we have a session, ensure temp_user_id is preserved
  if (session) {
    const tempUserId = req.cookies.get('temp_user_id')?.value
    if (tempUserId) {
      res.cookies.set('temp_user_id', tempUserId, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7 // 1 week
      })
    }
  }

  return res
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)']
}