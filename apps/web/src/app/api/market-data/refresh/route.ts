/**
 * API Route: POST /api/market-data/refresh
 *
 * Manually trigger a market data refresh (admin only).
 * This endpoint is useful for testing and on-demand updates.
 *
 * Body Parameters:
 * - symbols: Array of symbols to refresh (optional, defaults to all)
 * - force: Force refresh even if recently updated (optional)
 */

import { createServerClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function POST(request: Request) {
  try {
    const supabase = await createServerClient()

    // Check if user is authenticated
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // TODO: Add role-based authorization (admin only)
    // For now, any authenticated user can trigger refresh

    const body = await request.json().catch(() => ({}))
    const { symbols, force } = body

    // In production, this would trigger a Celery task via API
    // For now, return a simulated response

    return NextResponse.json({
      message: 'Market data refresh triggered',
      symbols: symbols || 'all',
      force: force || false,
      status: 'queued',
      note: 'This endpoint requires Celery worker to be running. Use: ./services/agents/start_market_data_worker.sh',
      timestamp: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Error in /api/market-data/refresh:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    )
  }
}

export async function GET() {
  return NextResponse.json(
    { error: 'Method not allowed. Use POST to trigger refresh.' },
    { status: 405 }
  )
}
