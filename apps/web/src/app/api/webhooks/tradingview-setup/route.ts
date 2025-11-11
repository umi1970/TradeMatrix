import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

/**
 * TradingView Setup Creation Webhook
 *
 * Receives TradingView alert with OHLC data, sends to AI for analysis,
 * creates setup in database, and generates Pine Script for monitoring.
 *
 * Expected payload from TradingView Pine Script:
 * {
 *   "ticker": "DAX",
 *   "exchange": "XETR",
 *   "interval": "60",
 *   "bars": [
 *     {"time": "1699704000000", "open": 19480, "high": 19520, "low": 19450, "close": 19500, "volume": 12500},
 *     ...
 *   ]
 * }
 */

interface OHLCBar {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

interface TradingViewPayload {
  ticker: string
  exchange?: string
  interval: string
  bars: OHLCBar[]
}

interface AIAnalysisResponse {
  side: 'long' | 'short'
  entry_price: number
  stop_loss: number
  take_profit: number
  confidence: number
  reasoning: string
  patterns_detected?: string[]
  support_levels?: number[]
  resistance_levels?: number[]
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    console.log('📥 TradingView Setup Webhook received:', body.substring(0, 200))

    let payload: TradingViewPayload

    try {
      payload = JSON.parse(body)
    } catch (e) {
      console.error('❌ Invalid JSON:', e)
      return NextResponse.json(
        { error: 'Invalid JSON payload' },
        { status: 400 }
      )
    }

    // Validate required fields
    const { ticker, interval, bars } = payload

    if (!ticker || !interval || !bars || !Array.isArray(bars) || bars.length === 0) {
      console.error('❌ Missing required fields:', { ticker, interval, barsLength: bars?.length })
      return NextResponse.json(
        { error: 'Missing required fields: ticker, interval, bars' },
        { status: 400 }
      )
    }

    console.log(`🎯 Processing TradingView alert: ${ticker} ${interval} (${bars.length} bars)`)

    // Step 1: Find symbol in database
    const { data: symbolData, error: symbolError } = await supabase
      .from('market_symbols')
      .select('id, symbol, alias, vendor, active')
      .or(`symbol.eq.${ticker},alias.eq.${ticker}`)
      .eq('active', true)
      .single()

    if (symbolError || !symbolData) {
      console.error(`❌ Symbol ${ticker} not found:`, symbolError)
      return NextResponse.json(
        { error: `Symbol ${ticker} not found in database. Please add it first.` },
        { status: 404 }
      )
    }

    console.log(`✅ Symbol found: ${symbolData.symbol} (${symbolData.alias})`)

    // Step 2: Call FastAPI AI Analysis Service
    const fastApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const analysisUrl = `${fastApiUrl}/api/analyze-ohlc`

    console.log(`🤖 Calling AI Analysis: ${analysisUrl}`)

    const analysisResponse = await fetch(analysisUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ticker: ticker,
        interval: interval,
        bars: bars,
      }),
    })

    if (!analysisResponse.ok) {
      const errorText = await analysisResponse.text()
      console.error('❌ AI Analysis failed:', errorText)
      return NextResponse.json(
        { error: 'AI Analysis failed', details: errorText },
        { status: 500 }
      )
    }

    const analysis: AIAnalysisResponse = await analysisResponse.json()

    console.log(`✅ AI Analysis complete: ${analysis.side} @ ${analysis.entry_price} (confidence: ${analysis.confidence})`)

    // Step 3: Check confidence threshold (0.60 minimum)
    const minConfidence = 0.60

    if (analysis.confidence < minConfidence) {
      console.log(`⚠️ Low confidence (${analysis.confidence}), rejecting setup`)
      return NextResponse.json({
        success: false,
        reason: 'confidence_too_low',
        confidence: analysis.confidence,
        min_confidence: minConfidence,
        message: `Setup rejected: Confidence ${analysis.confidence} is below threshold ${minConfidence}`,
      })
    }

    // Step 4: Create setup in database
    const now = new Date().toISOString()

    const setupData = {
      user_id: null, // System-generated setup (no specific user)
      symbol_id: symbolData.id,
      module: 'tradingview',
      strategy: 'tv_alert',
      side: analysis.side,
      entry_price: analysis.entry_price,
      stop_loss: analysis.stop_loss,
      take_profit: analysis.take_profit,
      confidence: analysis.confidence,
      status: 'pending',
      payload: {
        ticker: ticker,
        interval: interval,
        bars: bars,
        analysis: {
          reasoning: analysis.reasoning,
          patterns_detected: analysis.patterns_detected || [],
          support_levels: analysis.support_levels || [],
          resistance_levels: analysis.resistance_levels || [],
        },
        created_via: 'tradingview_webhook',
        created_at: now,
      },
      created_at: now,
      updated_at: now,
    }

    const { data: setup, error: setupError } = await supabase
      .from('setups')
      .insert(setupData)
      .select()
      .single()

    if (setupError || !setup) {
      console.error('❌ Failed to create setup:', setupError)
      return NextResponse.json(
        { error: 'Failed to create setup', details: setupError },
        { status: 500 }
      )
    }

    console.log(`✅ Setup created: ${setup.id}`)

    // Step 5: Generate Pine Script for monitoring
    const pineScriptResponse = await fetch(`${fastApiUrl}/api/generate-pine-script`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        setup_id: setup.id,
        ticker: ticker,
        side: analysis.side,
        entry_price: analysis.entry_price,
        stop_loss: analysis.stop_loss,
        take_profit: analysis.take_profit,
      }),
    })

    let pineScript = null

    if (pineScriptResponse.ok) {
      const pineData = await pineScriptResponse.json()
      pineScript = pineData.pine_script

      // Update setup with Pine Script
      await supabase
        .from('setups')
        .update({
          pine_script: pineScript,
          pine_script_active: true,
          updated_at: new Date().toISOString(),
        })
        .eq('id', setup.id)

      console.log(`✅ Pine Script generated for setup ${setup.id}`)
    } else {
      console.warn('⚠️ Pine Script generation failed, but setup created')
    }

    // Step 6: Send success response
    return NextResponse.json({
      success: true,
      setup_id: setup.id,
      ticker: ticker,
      side: analysis.side,
      entry_price: analysis.entry_price,
      stop_loss: analysis.stop_loss,
      take_profit: analysis.take_profit,
      confidence: analysis.confidence,
      reasoning: analysis.reasoning,
      pine_script: pineScript,
      webhook_url: `${process.env.NEXT_PUBLIC_APP_URL}/api/webhooks/tradingview-monitor`,
    })

  } catch (error) {
    console.error('❌ Webhook processing error:', error)
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

// Allow GET for testing/documentation
export async function GET() {
  return NextResponse.json({
    message: 'TradingView Setup Creation Webhook',
    url: `${process.env.NEXT_PUBLIC_APP_URL}/api/webhooks/tradingview-setup`,
    method: 'POST',
    expected_payload: {
      ticker: 'DAX',
      exchange: 'XETR',
      interval: '60',
      bars: [
        {
          time: '1699704000000',
          open: 19480,
          high: 19520,
          low: 19450,
          close: 19500,
          volume: 12500,
        },
        '... (up to 100 bars)',
      ],
    },
    response: {
      success: true,
      setup_id: 'uuid',
      ticker: 'DAX',
      side: 'long',
      entry_price: 19500,
      stop_loss: 19450,
      take_profit: 19600,
      confidence: 0.85,
      reasoning: 'Bullish trend with strong support...',
      pine_script: '//@version=5...',
      webhook_url: '/api/webhooks/tradingview-monitor',
    },
  })
}
