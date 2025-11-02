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

    // Step 1: Get all symbols from eod_levels (same as EOD widget)
    const { data: eodLevels, error: eodError } = await (supabase as any)
      .from('eod_levels')
      .select(`
        *,
        symbols!inner(
          symbol,
          name,
          is_active
        )
      `)
      .eq('symbols.is_active', true)
      .order('trade_date', { ascending: false })
      .limit(100)

    console.log(`EOD Levels query result: ${eodLevels?.length || 0} records, error:`, eodError)

    if (!eodLevels || eodLevels.length === 0) {
      return NextResponse.json({
        data: [],
        count: 0,
        timestamp: new Date().toISOString()
      })
    }

    // Step 2: Get latest EOD level for each symbol
    const symbolMap = new Map()
    eodLevels.forEach((item: any) => {
      const symbol = item.symbols.symbol
      if (!symbolMap.has(symbol)) {
        symbolMap.set(symbol, {
          symbol_id: item.symbol_id,
          symbol: symbol,
          name: item.symbols.name,
          eod_price: item.yesterday_close ? parseFloat(item.yesterday_close) : null,
          eod_high: item.yesterday_high ? parseFloat(item.yesterday_high) : null,
          eod_low: item.yesterday_low ? parseFloat(item.yesterday_low) : null,
          eod_date: item.trade_date
        })
      }
    })

    // Step 3: Try to get live prices from price_cache
    const { data: cacheData } = await (supabase as any)
      .from('price_cache')
      .select('*')
      .in('symbol_id', Array.from(symbolMap.values()).map(s => s.symbol_id))

    console.log(`Price cache query result: ${cacheData?.length || 0} records`)

    // Step 4: Build cache map by symbol_id
    const cacheMap = new Map()
    cacheData?.forEach((item: any) => {
      cacheMap.set(item.symbol_id, {
        price: item.price ? parseFloat(item.price) : null,
        updated_at: item.updated_at
      })
    })

    // Step 5: Merge live prices with EOD data
    const marketData = Array.from(symbolMap.values()).map((symbolData: any) => {
      const livePrice = cacheMap.get(symbolData.symbol_id)

      return {
        symbol: symbolData.symbol,
        symbolId: symbolData.symbol_id, // Add symbol_id for sparkline
        name: symbolData.name,
        price: livePrice?.price || symbolData.eod_price,
        open: null,
        high: symbolData.eod_high,
        low: symbolData.eod_low,
        change: null,
        changePercent: null,
        volume: null,
        exchange: null,
        currency: 'USD',
        isMarketOpen: !!livePrice?.price, // true if we have live price
        priceTimestamp: livePrice?.updated_at || symbolData.eod_date,
        updatedAt: livePrice?.updated_at || symbolData.eod_date,
        trend: 'neutral'
      }
    })

    console.log(`Returning ${marketData.length} market data records (${cacheMap.size} with live prices)`)

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
