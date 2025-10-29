/**
 * Supabase Server Client for Server Components
 *
 * Usage in Server Components:
 * ```typescript
 * import { createServerClient } from '@/lib/supabase/server'
 *
 * export default async function Page() {
 *   const supabase = await createServerClient()
 *   const { data: trades } = await supabase.from('trades').select('*')
 *   return <div>{JSON.stringify(trades)}</div>
 * }
 * ```
 */

import { createServerClient as createClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { Database } from './types'

export async function createServerClient() {
  const cookieStore = await cookies()

  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // The `setAll` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
      },
    }
  )
}

/**
 * Admin Client for Server-side operations that require service_role key
 * WARNING: Only use this in server-side code, NEVER expose service_role key to client!
 *
 * Usage:
 * ```typescript
 * import { createAdminClient } from '@/lib/supabase/server'
 *
 * const supabase = createAdminClient()
 * // Can bypass RLS policies
 * ```
 */
export async function createAdminClient() {
  const cookieStore = await cookies()

  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Ignore cookie errors in admin context
          }
        },
      },
    }
  )
}
