/**
 * Auth Callback Route
 *
 * This route handles the OAuth callback from Supabase Auth.
 * After successful OAuth login (Google, GitHub, etc.), users are redirected here.
 *
 * The route exchanges the auth code for a session and redirects to the app.
 */

import { createServerClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const origin = requestUrl.origin

  if (code) {
    const supabase = await createServerClient()

    // Exchange the code for a session
    await supabase.auth.exchangeCodeForSession(code)
  }

  // Redirect to dashboard after successful auth
  // You can customize this to redirect to a specific page
  return NextResponse.redirect(`${origin}/dashboard`)
}
