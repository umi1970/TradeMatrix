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

    // Try to fetch from price_cache first (real-time prices)
    const { data: cacheData, error: cacheError } = await (supabase as any)
      .from('price_cache')
      .select(`
        *,
        symbols!inner(
          symbol,
          name,
          id
        )
      `)
      .order('updated_at', { ascending: false })

    // If price_cache is empty or error, fallback to last EOD close prices
    let marketData: any[] = []

    if (cacheData && cacheData.length > 0) {
      // Use real-time prices from cache
      marketData = cacheData.map((item: any) => {
        const price = item.price ? parseFloat(item.price) : null
        return {
          symbol: item.symbols.symbol,
          name: item.symbols.name || item.symbols.symbol,
          price: price,
          open: null,
          high: null,
          low: null,
          change: null,
          changePercent: null,
          volume: null,
          exchange: null,
          currency: 'USD',
          isMarketOpen: true,
          priceTimestamp: item.updated_at,
          updatedAt: item.updated_at,
          trend: 'neutral'
        }
      })
    } else {
      // Fallback to last EOD close prices
      console.log('Price cache empty, falling back to EOD data')

      const { data: eodData, error: eodError } = await (supabase as any)
        .from('eod_data')
        .select(`
          *,
          symbols!inner(
            symbol,
            name
          )
        `)
        .order('date', { ascending: false })
        .limit(50) // Get recent data for all symbols

      if (eodError) {
        console.error('Error fetching EOD data:', eodError)
        return NextResponse.json(
          { error: 'Failed to fetch market data', details: eodError.message },
          { status: 500 }
        )
      }

      // Group by symbol and get most recent close price for each
      const symbolMap = new Map()
      eodData?.forEach((item: any) => {
        const symbol = item.symbols.symbol
        if (!symbolMap.has(symbol)) {
          symbolMap.set(symbol, {
            symbol: symbol,
            name: item.symbols.name || symbol,
            price: item.close ? parseFloat(item.close) : null,
            open: item.open ? parseFloat(item.open) : null,
            high: item.high ? parseFloat(item.high) : null,
            low: item.low ? parseFloat(item.low) : null,
            change: item.close && item.open ? parseFloat(item.close) - parseFloat(item.open) : null,
            changePercent: item.close && item.open ? ((parseFloat(item.close) - parseFloat(item.open)) / parseFloat(item.open) * 100) : null,
            volume: item.volume,
            exchange: null,
            currency: 'USD',
            isMarketOpen: false, // Markets are closed (using EOD data)
            priceTimestamp: item.date,
            updatedAt: item.date,
            trend: item.close && item.open ? (parseFloat(item.close) >= parseFloat(item.open) ? 'up' : 'down') : 'neutral'
          })
        }
      })

      marketData = Array.from(symbolMap.values())
    }

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
