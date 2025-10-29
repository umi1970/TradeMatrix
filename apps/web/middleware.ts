import { updateSession } from '@/lib/supabase/middleware'
import type { NextRequest } from 'next/server'

/**
 * Middleware for authentication and session management
 * Runs on every request to update the session and protect routes
 *
 * Protected routes: /dashboard, /account
 * Public routes: /, /login, /signup, /auth/callback
 */
export async function middleware(request: NextRequest) {
  return await updateSession(request)
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
