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

    // Fetch current prices with symbol information
    const { data, error } = await supabase
      .from('current_prices_with_symbols')
      .select('*')
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
      symbol: item.symbol,
      name: item.symbol_name || item.symbol,
      price: parseFloat(item.price),
      open: item.open ? parseFloat(item.open) : null,
      high: item.high ? parseFloat(item.high) : null,
      low: item.low ? parseFloat(item.low) : null,
      change: item.change ? parseFloat(item.change) : null,
      changePercent: item.change_percent ? parseFloat(item.change_percent) : null,
      volume: item.volume,
      exchange: item.exchange,
      currency: item.currency,
      isMarketOpen: item.is_market_open,
      priceTimestamp: item.price_timestamp,
      updatedAt: item.updated_at,
      // Calculate trend for UI
      trend: item.change_percent
        ? (parseFloat(item.change_percent) >= 0 ? 'up' : 'down')
        : 'neutral'
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
