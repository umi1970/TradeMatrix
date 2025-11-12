import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function POST(request: NextRequest) {
  try {
    const { analysis_id } = await request.json()

    if (!analysis_id) {
      return NextResponse.json(
        { error: 'Missing analysis_id' },
        { status: 400 }
      )
    }

    // Get chart analysis
    const { data: analysis, error: analysisError } = await supabase
      .from('chart_analyses')
      .select(`
        id,
        symbol_id,
        timeframe,
        payload,
        trend,
        confidence_score,
        market_symbols (
          symbol
        )
      `)
      .eq('id', analysis_id)
      .single()

    if (analysisError || !analysis) {
      console.error('Failed to fetch analysis:', analysisError)
      return NextResponse.json(
        { error: 'Analysis not found' },
        { status: 404 }
      )
    }

    const payload = analysis.payload || {}

    // Validate setup_type first
    if (!payload.setup_type || payload.setup_type === 'no_trade') {
      return NextResponse.json(
        { error: 'Cannot create setup: Analysis indicates no valid trade setup (setup_type is "no_trade" or missing)' },
        { status: 400 }
      )
    }

    if (payload.setup_type !== 'long' && payload.setup_type !== 'short') {
      return NextResponse.json(
        { error: `Invalid setup_type: "${payload.setup_type}". Must be "long" or "short"` },
        { status: 400 }
      )
    }

    // Validate required trading levels
    if (!payload.entry_price || !payload.stop_loss || !payload.take_profit) {
      return NextResponse.json(
        { error: 'Analysis missing required trading levels (entry/stop/target)' },
        { status: 400 }
      )
    }

    // Get user from authorization header (if exists)
    const authHeader = request.headers.get('authorization')
    let user_id = null

    if (authHeader) {
      const token = authHeader.replace('Bearer ', '')
      const { data: { user } } = await supabase.auth.getUser(token)
      user_id = user?.id || null
    }

    // Create setup in setups table
    const { data: setup, error: setupError } = await supabase
      .from('setups')
      .insert({
        user_id,
        module: 'vision_screenshot', // Mark as screenshot-based setup
        symbol_id: analysis.symbol_id,
        strategy: 'vision_analysis', // Distinct strategy name
        side: payload.setup_type === 'long' ? 'long' : 'short',
        entry_price: payload.entry_price,
        stop_loss: payload.stop_loss,
        take_profit: payload.take_profit,
        confidence: analysis.confidence_score || 0.5,
        status: 'pending',
        payload: {
          ...payload,
          analysis_id: analysis_id,
          timeframe: analysis.timeframe,
          symbol: (analysis.market_symbols as any)?.symbol,
          source: 'vision_screenshot',
        },
      })
      .select()
      .single()

    if (setupError) {
      console.error('Failed to create setup:', setupError)
      return NextResponse.json(
        { error: 'Failed to create setup' },
        { status: 500 }
      )
    }

    console.log(`✅ Created setup ${setup.id} from analysis ${analysis_id}`)

    return NextResponse.json({
      setup_id: setup.id,
      symbol: (analysis.market_symbols as any)?.symbol,
      side: setup.side,
      entry_price: setup.entry_price,
      stop_loss: setup.stop_loss,
      take_profit: setup.take_profit,
    })

  } catch (error) {
    console.error('❌ Create setup error:', error)
    return NextResponse.json(
      { error: 'Failed to create setup' },
      { status: 500 }
    )
  }
}
