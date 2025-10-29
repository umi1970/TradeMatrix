/**
 * Auth Callback Route
 *
 * This route handles the OAuth callback from Supabase Auth.
 * After successful OAuth login (Google, GitHub, etc.), users are redirected here.
 *
 * The route exchanges the auth code for a session and redirects to the app.
 */

import { createServerClient as createClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import type { NextRequest } from 'next/server'
import type { Database } from '@/lib/supabase/types'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const next = requestUrl.searchParams.get('next') ?? '/dashboard'

  if (code) {
    try {
      const cookieStore = await cookies()

      // Create Supabase client with proper cookie handling for Route Handlers
      const supabase = createClient<Database>(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
          cookies: {
            getAll() {
              return cookieStore.getAll()
            },
            setAll(cookiesToSet) {
              cookiesToSet.forEach(({ name, value, options }) => {
                cookieStore.set(name, value, options)
              })
            },
          },
        }
      )

      // Exchange the code for a session
      const { data, error } = await supabase.auth.exchangeCodeForSession(code)

      if (error) {
        console.error('Error exchanging code for session:', error)
        // Redirect to login with error
        return NextResponse.redirect(new URL('/login?error=auth_callback_error', requestUrl.origin))
      }

      if (!data.session) {
        console.error('No session returned after exchanging code')
        return NextResponse.redirect(new URL('/login?error=no_session', requestUrl.origin))
      }

      console.log('✅ Google OAuth successful, session created for:', data.user?.email)

      // Redirect to dashboard after successful auth
      return NextResponse.redirect(new URL(next, requestUrl.origin))
    } catch (error) {
      console.error('Unexpected error in auth callback:', error)
      return NextResponse.redirect(new URL('/login?error=unexpected_error', requestUrl.origin))
    }
  }

  // No code provided, redirect to login
  console.error('No code parameter in callback URL')
  return NextResponse.redirect(new URL('/login?error=no_code', requestUrl.origin))
}
