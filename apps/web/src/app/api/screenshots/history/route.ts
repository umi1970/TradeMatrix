import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const limit = parseInt(searchParams.get('limit') || '50')

    // Get analyses that have screenshot URLs (not 'screenshot' dummy value)
    const { data, error } = await supabase
      .from('chart_analyses')
      .select(`
        id,
        symbol_id,
        timeframe,
        chart_url,
        patterns_detected,
        trend,
        support_levels,
        resistance_levels,
        confidence_score,
        analysis_summary,
        payload,
        created_at,
        market_symbols (
          symbol
        )
      `)
      .not('chart_url', 'eq', 'screenshot')
      .like('chart_url', 'http%')
      .order('created_at', { ascending: false })
      .limit(limit)

    if (error) {
      console.error('Failed to fetch analyses:', error)
      return NextResponse.json(
        { error: 'Failed to fetch analyses' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      analyses: data || [],
      count: data?.length || 0,
    })

  } catch (error) {
    console.error('History API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch history' },
      { status: 500 }
    )
  }
}
