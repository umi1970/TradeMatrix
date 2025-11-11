import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = parseInt(searchParams.get('limit') || '20')
    const offset = parseInt(searchParams.get('offset') || '0')

    // Fetch analyses with symbol info, ordered by newest first
    const { data: analyses, error, count } = await supabase
      .from('chart_analyses')
      .select(`
        id,
        symbol_id,
        timeframe,
        chart_url,
        trend,
        confidence_score,
        created_at,
        market_symbols (
          symbol,
          vendor,
          alias
        )
      `, { count: 'exact' })
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (error) {
      console.error('❌ Failed to fetch analyses:', error)
      return NextResponse.json(
        { error: 'Failed to fetch analyses' },
        { status: 500 }
      )
    }

    // Transform data for frontend
    const transformedAnalyses = analyses?.map((analysis: any) => ({
      id: analysis.id,
      symbol: analysis.market_symbols?.symbol || 'UNKNOWN',
      vendor: analysis.market_symbols?.vendor || 'unknown',
      alias: analysis.market_symbols?.alias,
      timeframe: analysis.timeframe,
      trend: analysis.trend,
      confidence_score: analysis.confidence_score,
      chart_url: analysis.chart_url,
      created_at: analysis.created_at,
    })) || []

    return NextResponse.json({
      analyses: transformedAnalyses,
      total: count || 0,
      limit,
      offset,
      hasMore: count ? (offset + limit) < count : false,
    })

  } catch (error) {
    console.error('❌ Analyses fetch error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch analyses' },
      { status: 500 }
    )
  }
}
