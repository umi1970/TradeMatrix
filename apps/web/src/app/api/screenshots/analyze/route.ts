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
      temperature: 0.2,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: `You are a professional day trader and technical analyst.
You are analyzing a trading chart screenshot to extract structured data and trading insights.

EXTRACT and ANALYZE the following:

## 1. BASIC DATA
- symbol: Trading symbol or instrument (e.g. "DAX", "EUR/USD")
- timeframe: Chart timeframe (e.g. "5m", "15m", "1h", "4h", "1D")
- current_price: Latest visible price (numeric)
- open: Opening price of current candle
- high: Highest price visible on chart
- low: Lowest price visible on chart
- close: Closing price (usually same as current_price)
- timestamp: When the chart snapshot was taken (ISO 8601 if visible)

## 2. TECHNICAL INDICATORS
Extract clearly visible indicator values:
- ema20, ema50, ema200
- rsi
- pivot_points: [R3, R2, R1, PP, S1, S2, S3] (only if shown)
- other_indicators: list of any additional indicators visible (MACD, VWAP, etc.)

## 3. SUPPORT / RESISTANCE LEVELS
Identify visible horizontal key levels based on:
- Horizontal lines drawn on chart
- Recent swing highs/lows
- Consolidation or reaction zones
Return as arrays:
- support_levels[]
- resistance_levels[]

## 4. TREND ANALYSIS
- trend: "bullish", "bearish", or "sideways"
- trend_strength: "strong", "moderate", or "weak"
- price_vs_emas: "above_all", "below_all", or "mixed"
- momentum_bias: short textual summary (e.g. "bullish momentum slowing near resistance")

## 5. PRICE ACTION & PATTERNS
- patterns_detected: Array of visible patterns (e.g. "double_top", "breakout", "rejection", "range")
- key_events: 2–3 short bullet points describing the most relevant recent price actions
- market_structure: "higher_highs", "lower_lows", "range_bound", or "mixed"

## 6. TRADING SETUP (recommended action)
- setup_type: "long", "short", or "no_trade"
- entry_price: Suggested entry level
- stop_loss: Suggested stop loss
- take_profit: Suggested take profit
- risk_reward: Ratio (TP distance ÷ SL distance)
- reasoning: 2–3 sentences summarizing logic (trend, levels, confirmation)
- timeframe_validity: "intraday", "swing", or "midterm"

## 7. CONFIDENCE & QUALITY
- confidence_score: 0.0–1.0 (based on clarity of trend, levels & confluence)
- chart_quality: "excellent", "good", "fair", or "poor"
- key_factors: list 2–3 factors influencing confidence (e.g. "clear EMA confluence", "low volume", "strong rejection")

RULES:
✅ Extract only what is visually identifiable.
✅ Never hallucinate numbers — if not visible, return null.
✅ Be precise with price values and levels.
✅ Focus on actionable, realistic setups.
✅ Always output a complete JSON object with all fields, even if some are null.

Return your answer **only** as valid JSON (no markdown, no extra text).`,
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

    // Backup heuristic: If confidence is 0.0 but we have data, set minimum confidence
    if (analysis.confidence_score === 0.0 && (analysis.trend || analysis.support_levels?.length > 0 || analysis.resistance_levels?.length > 0)) {
      console.log('⚠️ Confidence was 0.0, applying backup heuristic (0.4)')
      analysis.confidence_score = 0.4
    }

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
      trend_strength: analysis.trend_strength,
      price_vs_emas: analysis.price_vs_emas,
      momentum_bias: analysis.momentum_bias,
      confidence_score: analysis.confidence_score,
      chart_quality: analysis.chart_quality,
      key_factors: analysis.key_factors,
      setup_type: analysis.setup_type,
      entry_price: analysis.entry_price,
      stop_loss: analysis.stop_loss,
      take_profit: analysis.take_profit,
      risk_reward: analysis.risk_reward,
      reasoning: analysis.reasoning,
      timeframe_validity: analysis.timeframe_validity,
      patterns_detected: analysis.patterns_detected,
      support_levels: analysis.support_levels,
      resistance_levels: analysis.resistance_levels,
    })

  } catch (error) {
    console.error('❌ Screenshot analysis error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze screenshot' },
      { status: 500 }
    )
  }
}
