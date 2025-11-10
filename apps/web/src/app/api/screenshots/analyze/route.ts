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
              text: `You are a professional day trader analyzing a trading chart screenshot.

Your task is to EXTRACT and SUMMARIZE the technical and price information visible in the image.

⚠️ OUTPUT REQUIREMENTS:
- Respond **only** in valid JSON (no markdown or explanations).
- Use EXACTLY these root keys:
  ["symbol", "timeframe", "current_price", "open", "high", "low", "close", "timestamp", "ema20", "ema50", "ema200", "rsi", "pivot_points", "other_indicators", "support_levels", "resistance_levels", "trend", "trend_strength", "price_vs_emas", "momentum_bias", "patterns_detected", "key_events", "market_structure", "setup_type", "entry_price", "stop_loss", "take_profit", "risk_reward", "reasoning", "timeframe_validity", "confidence_score", "chart_quality", "key_factors"]

---

### 1️⃣ BASIC_DATA
Extract visible basic info:
symbol, timeframe, current_price, open, high, low, close, timestamp.

### 2️⃣ TECHNICAL_INDICATORS
Extract if visible:
ema20, ema50, ema200, rsi, pivot_points, other_indicators.

### 3️⃣ SUPPORT_RESISTANCE_LEVELS
support_levels[], resistance_levels[] from visible lines, pivots, or price zones.

### 4️⃣ TREND_ANALYSIS
trend ("bullish" | "bearish" | "sideways"),
trend_strength ("strong" | "moderate" | "weak"),
price_vs_emas ("above_all" | "below_all" | "mixed"),
momentum_bias (short comment like "bullish momentum slowing near resistance").

### 5️⃣ PRICE_ACTION_PATTERNS
patterns_detected[],
key_events (2–3 short points),
market_structure ("higher_highs" | "lower_lows" | "range_bound" | "mixed").

### 6️⃣ TRADING_SETUP
setup_type ("long" | "short" | "no_trade"),
entry_price, stop_loss, take_profit, risk_reward,
reasoning (2–3 sentences),
timeframe_validity ("intraday" | "swing" | "midterm").

### 7️⃣ CONFIDENCE_QUALITY
confidence_score (0.0–1.0),
chart_quality ("excellent" | "good" | "fair" | "poor"),
key_factors (list 2–3 reasons affecting confidence).

---

RULES:
✅ Use only what is clearly visible in the chart.
✅ If a value is uncertain, return null.
✅ Ensure numeric precision (trading requires accuracy).
✅ Focus on actionable insights, not generic explanations.
✅ Output must be valid JSON with the exact keys above.`,
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

    // Flatten nested structure if needed (Vision sometimes returns numbered keys)
    if (analysis['1_BASIC_DATA']) {
      console.log('⚠️ Flattening nested JSON structure...')
      analysis = {
        ...analysis['1_BASIC_DATA'],
        ...analysis['2_TECHNICAL_INDICATORS'],
        ...analysis['3_SUPPORT_RESISTANCE_LEVELS'],
        ...analysis['4_TREND_ANALYSIS'],
        ...analysis['5_PRICE_ACTION_PATTERNS'],
        ...analysis['6_TRADING_SETUP'],
        ...analysis['7_CONFIDENCE_QUALITY'],
      }
    }

    // Validate analysis data
    if (!analysis.current_price || !analysis.confidence_score || analysis.confidence_score < 0.5) {
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
