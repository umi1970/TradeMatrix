/**
 * API Route: GET /api/market-data/current
 *
 * Fetch current prices for all tracked symbols from the database.
 * Data is updated every minute by the Celery worker.
 */

import { createServerClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

interface CurrentPrice {
  id: string
  symbol: string
  symbol_name: string
  price: number
  open: number | null
  high: number | null
  low: number | null
  previous_close: number | null
  change: number | null
  change_percent: number | null
  volume: number | null
  exchange: string | null
  currency: string
  is_market_open: boolean
  price_timestamp: string | null
  updated_at: string
}

export async function GET(request: Request) {
  try {
    const supabase = await createServerClient()

    // Fetch current prices from price_cache (populated by liquidity alert system)
    const { data, error } = await (supabase as any)
      .from('price_cache')
      .select(`
        *,
        symbols!inner(
          symbol,
          name
        )
      `)
      .order('updated_at', { ascending: false })

    if (error) {
      console.error('Error fetching current prices:', error)
      return NextResponse.json(
        { error: 'Failed to fetch current prices', details: error.message },
        { status: 500 }
      )
    }

    // Transform data to frontend format
    const marketData = data?.map((item: any) => ({
      symbol: item.symbols.symbol,
      name: item.symbols.name || item.symbols.symbol,
      price: parseFloat(item.price),
      open: null, // price_cache doesn't store OHLC data
      high: null,
      low: null,
      change: null,
      changePercent: null,
      volume: null,
      exchange: null,
      currency: 'USD',
      isMarketOpen: true, // Assume market open if price is cached
      priceTimestamp: item.updated_at,
      updatedAt: item.updated_at,
      trend: 'neutral'
    })) || []

    return NextResponse.json({
      data: marketData,
      count: marketData.length,
      timestamp: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Unexpected error in /api/market-data/current:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    )
  }
}
