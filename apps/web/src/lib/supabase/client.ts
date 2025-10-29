/**
 * Supabase Client for Client Components
 *
 * Usage in Client Components:
 * ```typescript
 * 'use client'
 *
 * import { createBrowserClient } from '@/lib/supabase/client'
 * import { useEffect, useState } from 'react'
 *
 * export default function Component() {
 *   const supabase = createBrowserClient()
 *   const [user, setUser] = useState(null)
 *
 *   useEffect(() => {
 *     supabase.auth.getUser().then(({ data: { user } }) => {
 *       setUser(user)
 *     })
 *   }, [])
 *
 *   return <div>User: {user?.email}</div>
 * }
 * ```
 */

import { createBrowserClient as createClient } from '@supabase/ssr'
import type { Database } from './types'

export function createBrowserClient() {
  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
