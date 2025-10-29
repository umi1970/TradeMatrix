/**
 * Supabase Client Exports
 *
 * Central export point for all Supabase utilities.
 * Import from here for cleaner imports throughout the app.
 *
 * Example:
 * ```typescript
 * import { createServerClient, createBrowserClient } from '@/lib/supabase'
 * ```
 */

export { createServerClient, createAdminClient } from './server'
export { createBrowserClient } from './client'
export { updateSession } from './middleware'
export type { Database, Json } from './types'
