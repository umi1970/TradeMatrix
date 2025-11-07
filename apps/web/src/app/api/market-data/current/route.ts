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

    // Step 1: Get all active symbols (simpler, more dynamic)
    const { data: symbols, error: symbolsError } = await (supabase as any)
      .from('market_symbols')
      .select('id, symbol, name')
      .eq('active', true)

    console.log(`Symbols query result: ${symbols?.length || 0} records, error:`, symbolsError)

    if (!symbols || symbols.length === 0) {
      return NextResponse.json({
        data: [],
        count: 0,
        timestamp: new Date().toISOString()
      })
    }

    const symbolIds = symbols.map((s: any) => s.id)

    // Step 2: Get latest EOD levels for fallback
    const { data: eodLevels } = await (supabase as any)
      .from('eod_levels')
      .select('*')
      .in('symbol_id', symbolIds)
      .order('trade_date', { ascending: false })

    // Step 3: Get live prices from price_cache
    const { data: cacheData } = await (supabase as any)
      .from('price_cache')
      .select('*')
      .in('symbol_id', symbolIds)

    console.log(`Price cache query result: ${cacheData?.length || 0} records`)
    console.log(`EOD Levels query result: ${eodLevels?.length || 0} records`)

    // Step 4: Build EOD map (fallback data)
    const eodMap = new Map()
    eodLevels?.forEach((item: any) => {
      if (!eodMap.has(item.symbol_id)) {
        eodMap.set(item.symbol_id, {
          price: item.yesterday_close ? parseFloat(item.yesterday_close) : null,
          high: item.yesterday_high ? parseFloat(item.yesterday_high) : null,
          low: item.yesterday_low ? parseFloat(item.yesterday_low) : null,
          date: item.trade_date
        })
      }
    })

    // Step 5: Build cache map (live data)
    const cacheMap = new Map()
    cacheData?.forEach((item: any) => {
      cacheMap.set(item.symbol_id, {
        price: item.current_price ? parseFloat(item.current_price) : null,
        high: item.high_today ? parseFloat(item.high_today) : null,
        low: item.low_today ? parseFloat(item.low_today) : null,
        updated_at: item.updated_at
      })
    })

    // Step 6: Merge everything (symbols + live prices + EOD fallback)
    const marketData = symbols.map((symbol: any) => {
      const liveData = cacheMap.get(symbol.id)
      const eodData = eodMap.get(symbol.id)

      return {
        symbol: symbol.symbol,
        symbolId: symbol.id,
        name: symbol.name,
        price: liveData?.price || eodData?.price || 0,
        open: null,
        high: liveData?.high || eodData?.high || null,
        low: liveData?.low || eodData?.low || null,
        change: null,
        changePercent: null,
        volume: null,
        exchange: null,
        currency: 'USD',
        isMarketOpen: !!liveData?.price,
        priceTimestamp: liveData?.updated_at || eodData?.date || new Date().toISOString(),
        updatedAt: liveData?.updated_at || eodData?.date || new Date().toISOString(),
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
