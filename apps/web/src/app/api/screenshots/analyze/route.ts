import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'
import { createClient } from '@supabase/supabase-js'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const symbol = formData.get('symbol') as string

    if (!file || !symbol) {
      return NextResponse.json(
        { error: 'Missing file or symbol' },
        { status: 400 }
      )
    }

    // Convert file to base64
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    const base64 = buffer.toString('base64')
    const mimeType = file.type

    // Call OpenAI Vision API
    console.log(`🔍 Analyzing screenshot for ${symbol}...`)

    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: `You are a professional day trader analyzing a trading chart screenshot.

EXTRACT & ANALYZE the following:

## 1. BASIC DATA
- symbol: Trading symbol/instrument name
- timeframe: Chart timeframe (e.g., "5m", "15m", "1h", "4h", "1D")
- current_price: Most recent price (number only)
- open: Opening price of current candle
- high: Highest price visible
- low: Lowest price visible
- close: Closing price (same as current_price usually)
- timestamp: When screenshot was taken (ISO 8601)

## 2. TECHNICAL INDICATORS (extract visible values)
- ema20: EMA(20) value if visible
- ema50: EMA(50) value if visible
- ema200: EMA(200) value if visible
- rsi: RSI value if visible
- pivot_points: Array of pivot levels [R3, R2, R1, PP, S1, S2, S3] if visible
- other_indicators: Any other visible indicators

## 3. SUPPORT/RESISTANCE LEVELS
Identify key price levels from:
- Horizontal lines on chart
- Previous highs/lows
- Consolidation zones
- Pivot points
Return as arrays: support_levels[], resistance_levels[]

## 4. TREND ANALYSIS
- trend: "bullish", "bearish", or "sideways"
- trend_strength: "strong", "moderate", "weak"
- price_vs_emas: Position relative to EMAs (above/below)

## 5. PRICE ACTION & PATTERNS
- patterns_detected: Array of patterns (e.g., "breakout", "rejection", "consolidation", "reversal", "crash")
- key_events: Describe major price movements visible
- market_structure: Higher highs/lows, lower highs/lows, range-bound

## 6. TRADING SETUP (your recommendation)
- setup_type: "long", "short", or "no_trade"
- entry_price: Recommended entry (number)
- stop_loss: Recommended stop loss (number)
- take_profit: Recommended take profit (number)
- risk_reward: Ratio (number)
- reasoning: Why this setup? (2-3 sentences)

## 7. CONFIDENCE & QUALITY
- confidence_score: 0.0 to 1.0 (how confident are you in this analysis?)
- chart_quality: "excellent", "good", "fair", "poor"

RULES:
✅ Extract ONLY what you can SEE clearly
✅ Be precise with numbers (trading depends on accuracy!)
✅ If unsure about a value, use null
✅ Analyze like a professional day trader
✅ Focus on actionable insights

Respond in JSON format with ALL fields listed above.`,
            },
            {
              type: 'image_url',
              image_url: {
                url: `data:${mimeType};base64,${base64}`,
              },
            },
          ],
        },
      ],
      max_tokens: 2000,
      response_format: { type: 'json_object' },
    })

    const content = response.choices[0]?.message?.content
    if (!content) {
      return NextResponse.json(
        { error: 'No response from Vision API' },
        { status: 500 }
      )
    }

    const analysis = JSON.parse(content)

    console.log(`✅ Chart analysis complete:`, analysis)

    // Validate analysis data
    if (!analysis.current_price || !analysis.confidence_score || analysis.confidence_score < 0.6) {
      return NextResponse.json(
        { error: 'Low confidence analysis or missing critical data' },
        { status: 400 }
      )
    }

    // Get symbol_id from market_symbols table
    const { data: symbolData, error: symbolError } = await supabase
      .from('market_symbols')
      .select('id, symbol')
      .eq('symbol', analysis.symbol || symbol)
      .single()

    if (symbolError || !symbolData) {
      return NextResponse.json(
        { error: `Symbol ${analysis.symbol || symbol} not found in database` },
        { status: 404 }
      )
    }

    // Write to chart_analyses table
    const { data: insertedAnalysis, error: insertError } = await supabase
      .from('chart_analyses')
      .insert({
        symbol_id: symbolData.id,
        timeframe: analysis.timeframe || '5m',
        chart_url: 'screenshot', // Mark as screenshot-based analysis
        patterns_detected: analysis.patterns_detected || [],
        trend: analysis.trend || 'unknown',
        support_levels: analysis.support_levels || [],
        resistance_levels: analysis.resistance_levels || [],
        confidence_score: analysis.confidence_score,
        analysis_summary: analysis.reasoning || analysis.key_events || '',
        payload: analysis, // Store complete analysis as JSON
      })
      .select()
      .single()

    if (insertError) {
      console.error('❌ Failed to write to database:', insertError)
      return NextResponse.json(
        { error: 'Failed to save analysis' },
        { status: 500 }
      )
    }

    console.log(`✅ Saved analysis for ${symbolData.symbol} (${analysis.timeframe})`)

    return NextResponse.json({
      analysis_id: insertedAnalysis.id,
      symbol: analysis.symbol,
      timeframe: analysis.timeframe,
      current_price: analysis.current_price,
      trend: analysis.trend,
      confidence_score: analysis.confidence_score,
      setup_type: analysis.setup_type,
      entry_price: analysis.entry_price,
      stop_loss: analysis.stop_loss,
      take_profit: analysis.take_profit,
      reasoning: analysis.reasoning,
    })

  } catch (error) {
    console.error('❌ Screenshot analysis error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze screenshot' },
      { status: 500 }
    )
  }
}
