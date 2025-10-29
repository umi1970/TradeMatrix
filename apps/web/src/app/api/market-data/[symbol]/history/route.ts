/**
 * API Route: GET /api/market-data/[symbol]/history
 *
 * Fetch historical OHLCV data for a specific symbol.
 *
 * Query Parameters:
 * - interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d) - default: 1h
 * - limit: Number of candles to return - default: 500
 * - start_date: Start date (ISO format) - optional
 * - end_date: End date (ISO format) - optional
 */

import { createServerClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

interface RouteParams {
  params: {
    symbol: string
  }
}

export async function GET(
  request: Request,
  { params }: RouteParams
) {
  try {
    const { symbol } = params
    const { searchParams } = new URL(request.url)

    // Parse query parameters
    const interval = searchParams.get('interval') || '1h'
    const limit = parseInt(searchParams.get('limit') || '500')
    const startDate = searchParams.get('start_date')
    const endDate = searchParams.get('end_date')

    // Validate interval
    const validIntervals = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
    if (!validIntervals.includes(interval)) {
      return NextResponse.json(
        { error: `Invalid interval. Must be one of: ${validIntervals.join(', ')}` },
        { status: 400 }
      )
    }

    // Validate limit
    if (limit < 1 || limit > 5000) {
      return NextResponse.json(
        { error: 'Limit must be between 1 and 5000' },
        { status: 400 }
      )
    }

    const supabase = await createServerClient()

    // First, get the symbol_id from market_symbols table
    const { data: symbolData, error: symbolError } = await supabase
      .from('market_symbols')
      .select('id, alias')
      .eq('symbol', symbol.toUpperCase())
      .eq('active', true)
      .single()

    if (symbolError || !symbolData) {
      return NextResponse.json(
        { error: `Symbol not found: ${symbol}` },
        { status: 404 }
      )
    }

    // Build query for OHLC data
    let query = supabase
      .from('ohlc')
      .select('*')
      .eq('symbol_id', symbolData.id)
      .eq('timeframe', interval)
      .order('ts', { ascending: false })
      .limit(limit)

    // Add date filters if provided
    if (startDate) {
      query = query.gte('ts', startDate)
    }
    if (endDate) {
      query = query.lte('ts', endDate)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching OHLC data:', error)
      return NextResponse.json(
        { error: 'Failed to fetch historical data', details: error.message },
        { status: 500 }
      )
    }

    // Transform data to TradingView Lightweight Charts format
    const chartData = data?.map((candle: any) => ({
      time: Math.floor(new Date(candle.ts).getTime() / 1000), // Unix timestamp in seconds
      open: parseFloat(candle.open),
      high: parseFloat(candle.high),
      low: parseFloat(candle.low),
      close: parseFloat(candle.close),
      volume: candle.volume || 0
    })).reverse() || [] // Reverse to get chronological order

    return NextResponse.json({
      symbol: symbol.toUpperCase(),
      symbolName: symbolData.alias || symbol,
      interval,
      data: chartData,
      count: chartData.length,
      timestamp: new Date().toISOString()
    })

  } catch (error: any) {
    console.error('Unexpected error in /api/market-data/[symbol]/history:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    )
  }
}
