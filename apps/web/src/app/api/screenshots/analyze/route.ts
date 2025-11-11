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
    const files = formData.getAll('files') as File[]
    const symbol = formData.get('symbol') as string

    if (!files || files.length === 0 || !symbol) {
      return NextResponse.json(
        { error: 'Missing files or symbol' },
        { status: 400 }
      )
    }

    console.log(`📸 Received ${files.length} file(s) for multi-timeframe analysis`)

    // Separate image files from CSV files
    const imageFiles = files.filter(f => f.type.startsWith('image/'))
    const csvFiles = files.filter(f => f.name.endsWith('.csv') || f.type === 'text/csv')

    console.log(`   📷 ${imageFiles.length} screenshot(s), 📊 ${csvFiles.length} CSV file(s)`)

    // Upload all screenshots to Supabase Storage and convert to base64
    const screenshotUrls: string[] = []
    const imageContents: Array<{ type: 'image_url', image_url: { url: string } }> = []

    for (const file of imageFiles) {
      // Upload to Supabase Storage
      const timestamp = Date.now()
      const fileName = `${timestamp}_${file.name}`
      const filePath = `screenshots/${fileName}`

      const { data: uploadData, error: uploadError } = await supabase
        .storage
        .from('charts')
        .upload(filePath, file, {
          contentType: file.type,
          cacheControl: '3600',
        })

      if (uploadError) {
        console.error('❌ Failed to upload screenshot:', uploadError)
        return NextResponse.json(
          { error: 'Failed to upload screenshot' },
          { status: 500 }
        )
      }

      // Get public URL
      const { data: urlData } = supabase
        .storage
        .from('charts')
        .getPublicUrl(filePath)

      screenshotUrls.push(urlData.publicUrl)

      // Convert file to base64 for OpenAI
      const bytes = await file.arrayBuffer()
      const buffer = Buffer.from(bytes)
      const base64 = buffer.toString('base64')
      const mimeType = file.type

      imageContents.push({
        type: 'image_url',
        image_url: {
          url: `data:${mimeType};base64,${base64}`
        }
      })
    }

    console.log(`✅ All screenshots uploaded: ${screenshotUrls.join(', ')}`)

    // Parse CSV files and prepare as text context
    let csvContext = ''
    if (csvFiles.length > 0) {
      console.log(`📊 Processing ${csvFiles.length} CSV file(s)...`)
      for (const csvFile of csvFiles) {
        const csvText = await csvFile.text()
        const lines = csvText.split('\n')

        // Take header + first 100 rows (enough context, not too many tokens)
        const sampleLines = lines.slice(0, Math.min(101, lines.length))

        csvContext += `\n\n📊 CSV DATA from "${csvFile.name}":\n`
        csvContext += sampleLines.join('\n')
        csvContext += `\n... (${lines.length} total rows)\n`
      }
      console.log(`✅ CSV context prepared (${csvContext.length} characters)`)
    }

    // Call OpenAI Vision API with ALL images + CSV data in ONE request
    console.log(`🔍 Analyzing ${imageFiles.length} screenshot(s) ${csvFiles.length > 0 ? `+ ${csvFiles.length} CSV file(s)` : ''} for ${symbol}...`)

    const response = await openai.chat.completions.create({
      model: 'gpt-4o',
      temperature: 0.2,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: `You are a professional day trader analyzing ${imageFiles.length > 1 ? `${imageFiles.length} trading chart screenshots of the SAME SYMBOL at DIFFERENT TIMEFRAMES` : 'a trading chart screenshot'}${csvFiles.length > 0 ? ` with ${csvFiles.length} corresponding CSV file(s) containing EXACT OHLCV and indicator data` : ''}.

Your task is to EXTRACT and SUMMARIZE the technical and price information visible in the image.

⚠️ OUTPUT REQUIREMENTS:
- Respond **only** in valid JSON (no markdown or explanations).
- Use EXACTLY these root keys:
  ["symbol", "timeframe", "analyzed_timeframes", "current_price", "open", "high", "low", "close", "timestamp", "ema_20", "ema_50", "ema_200", "rsi_14", "atr_14", "macd_line", "macd_signal", "macd_histogram", "bb_upper", "bb_middle", "bb_lower", "pivot_point", "resistance_1", "support_1", "resistance_2", "support_2", "adx_14", "di_plus", "di_minus", "volume", "volatility_pct", "price_vs_ema20_pct", "price_vs_ema50_pct", "price_vs_ema200_pct", "support_levels", "resistance_levels", "trend", "trend_strength", "momentum_bias", "patterns_detected", "key_events", "market_structure", "setup_type", "entry_price", "stop_loss", "take_profit", "risk_reward", "reasoning", "detailed_analysis", "timeframe_validity", "confidence_score", "chart_quality", "key_factors"]

---

### 1️⃣ BASIC_DATA
Extract visible basic info:
- symbol: The trading symbol (e.g., EURUSD, GBPUSD, DAX)
- timeframe: The PRIMARY timeframe for entry (use trading format: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w - NOT '5 Minuten' or '1 hour')
- analyzed_timeframes: ${files.length > 1 ? `REQUIRED - Array of ALL ${files.length} timeframes you are analyzing (e.g., ["5m", "1h", "1d"]). MUST identify each chart's timeframe from labels/axes.` : 'null (single chart only)'}
- current_price, open, high, low, close, timestamp: From the primary/lowest timeframe chart.

### 2️⃣ TECHNICAL_INDICATORS
Extract if visible (return null if not visible):

**Moving Averages:**
- ema_20: EMA 20 value
- ema_50: EMA 50 value
- ema_200: EMA 200 value

**Momentum Indicators:**
- rsi_14: RSI(14) value (0-100)
- atr_14: ATR(14) value
- macd_line: MACD line value
- macd_signal: MACD signal line value
- macd_histogram: MACD histogram value

**Bollinger Bands:**
- bb_upper: Upper Bollinger Band
- bb_middle: Middle Bollinger Band (SMA 20)
- bb_lower: Lower Bollinger Band

**Pivot Points:**
- pivot_point: Daily pivot point
- resistance_1: R1 level
- support_1: S1 level
- resistance_2: R2 level
- support_2: S2 level

**Trend Indicators:**
- adx_14: ADX(14) value (0-100)
- di_plus: DI+ value
- di_minus: DI- value

**Volume & Volatility:**
- volume: Current bar volume
- volatility_pct: Volatility as percentage (ATR/Close * 100)

**Calculated Metrics:**
- price_vs_ema20_pct: (Current Price - EMA20) / EMA20 * 100
- price_vs_ema50_pct: (Current Price - EMA50) / EMA50 * 100
- price_vs_ema200_pct: (Current Price - EMA200) / EMA200 * 100

### 3️⃣ SUPPORT_RESISTANCE_LEVELS
support_levels[], resistance_levels[] from visible lines, pivots, or price zones.

### 4️⃣ TREND_ANALYSIS
trend ("bullish" | "bearish" | "sideways"),
trend_strength ("strong" | "moderate" | "weak") - use ADX and EMA alignment to determine strength,
momentum_bias (short comment like "bullish momentum slowing near resistance" - consider RSI, MACD, DI+/DI-).

### 5️⃣ PRICE_ACTION_PATTERNS
patterns_detected[],
key_events (2–3 short points),
market_structure ("higher_highs" | "lower_lows" | "range_bound" | "mixed").

### 6️⃣ TRADING_SETUP
setup_type ("long" | "short" | "no_trade"),
entry_price (current price or nearest support/resistance for optimal entry),
stop_loss (place below support for longs, above resistance for shorts - not arbitrary fixed distances),
take_profit (target nearest resistance for longs, support for shorts - use chart levels, not fixed ratios),
risk_reward (as decimal number, calculate dynamically based on trend strength and confidence:
  - Strong trend + high confidence (>0.75): 2.0–3.0
  - Moderate trend or medium confidence (0.5-0.75): 1.5–2.0
  - Weak trend or low confidence (<0.5): 1.0–1.5
  Example: 2.5 for strong bullish trend with 0.85 confidence),
reasoning (2–3 sentences explaining WHY this setup makes sense given the current market structure),
detailed_analysis (300-500 words comprehensive analysis structured as follows:
  📊 **Timeframe Breakdown** - Analyze each timeframe separately (if multiple provided):
     - Higher TF (e.g., 1d): Overall trend direction, key levels, trend strength
     - Middle TF (e.g., 1h): Current structure, support/resistance, MACD/RSI state
     - Lower TF (e.g., 5m): Entry timing, precise levels, immediate action
  🎯 **Indicator Confluence** - Cross-reference ALL indicators across timeframes:
     - Which indicators agree? (e.g., "RSI above 50 on all TFs, MACD positive on 1h+1d")
     - Which indicators conflict? (e.g., "5m RSI overbought but 1h still neutral")
     - Overall confluence score and impact on confidence
  💰 **Trade Rationale** - Explain exact entry/SL/TP placement:
     - WHY this entry price? (e.g., "5m EMA20 + previous support at 1.1590")
     - WHY this stop loss? (e.g., "Below 1h structure and 5m swing low at 1.1556")
     - WHY this take profit? (e.g., "1h resistance zone at 1.1620, aligns with 1d pivot")
  ⚠️ **Risk Factors** - What could invalidate this setup:
     - Key levels to watch (e.g., "If price closes below 1h EMA50, trend weakens")
     - Alternative scenarios (e.g., "If 1d resistance holds, expect pullback")
     - Time constraints (e.g., "Setup valid for next 4-6 hours on 5m entry")
  Use professional trading language. Be specific with levels and indicator values.),
timeframe_validity ("intraday" | "swing" | "midterm").

### 7️⃣ CONFIDENCE_QUALITY
confidence_score (0.0–1.0, calibrate realistically based on ALL visible indicators:
  - 0.85+: Clear trend, strong ADX (>40), EMA alignment, RSI confirming, MACD aligned, multiple indicators agree
  - 0.70–0.84: Good setup but with 1-2 conflicting signals (e.g., bullish EMAs but RSI overbought)
  - 0.50–0.69: Mixed signals (e.g., sideways EMAs, weak ADX <25, MACD divergence)
  - <0.50: Low probability, unclear structure, conflicting indicators),
chart_quality ("excellent" | "good" | "fair" | "poor") - based on chart clarity and indicator visibility,
key_factors (list 2–4 specific indicators/factors affecting confidence, e.g., "ADX 45 shows strong trend", "RSI 75 overbought", "MACD histogram declining", "Price above all EMAs").

---

RULES:
✅ Use only what is clearly visible in the chart.
✅ If an indicator value is uncertain or not visible, return null.
✅ Ensure numeric precision (trading requires accuracy).
✅ Focus on actionable insights, not generic explanations.
✅ Consider ALL 23 indicators when calculating confidence_score and trend_strength.
✅ Use ADX, RSI, MACD, EMAs alignment to determine trend strength.
✅ Calculate risk_reward dynamically based on trend_strength and confidence_score.
✅ If you analyze multiple timeframes of the same symbol, mention confluence in reasoning.
✅ Reasoning must explain WHY the setup works given market structure and indicator alignment.
✅ key_factors MUST reference specific indicator values (e.g., "ADX 45", "RSI 75", not just "strong trend").
✅ Output must be valid JSON with the exact 45 keys listed above (all indicators + analysis fields + analyzed_timeframes + detailed_analysis).

${csvFiles.length > 0 ? `
📊 CSV DATA AVAILABLE:
✅ You have access to CSV files with EXACT OHLCV and indicator values.
✅ CSV data is MORE ACCURATE than reading from chart images (no pixel estimation).
✅ PREFER CSV values over visual chart reading when available.
✅ Use CSV for precise entry_price, stop_loss, take_profit calculations.
✅ CSV columns typically include: timestamp, open, high, low, close, volume, ema_20, ema_50, ema_200, rsi_14, macd_line, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, adx_14, di_plus, di_minus, atr_14, pivot_point, support_1, resistance_1, support_2, resistance_2, and more.
✅ Use the MOST RECENT row (last row) for current_price and latest indicator values.
✅ Look back a few rows to understand trend direction and momentum changes.
` : ''}

${imageFiles.length > 1 ? `
🎯 MULTI-TIMEFRAME ANALYSIS RULES (${imageFiles.length} CHARTS PROVIDED):
✅ STEP 1: IDENTIFY - Read the timeframe label from EACH of the ${imageFiles.length} charts you received (look at chart title, x-axis labels). Fill "analyzed_timeframes" array with ALL ${imageFiles.length} timeframes.

✅ STEP 2: ANALYZE EACH TIMEFRAME:
   - Higher timeframe (e.g., 1d): What is the TREND direction? (bullish/bearish/sideways)
   - Middle timeframe (e.g., 1h): Does it confirm or conflict with higher TF trend?
   - Lower timeframe (e.g., 5m): Is there a clear ENTRY opportunity?

✅ STEP 3: CONFLUENCE CHECK:
   - DO ALL timeframes point in the SAME direction? → INCREASE confidence_score (+0.10 to +0.15)
   - Is higher TF bullish but lower TF bearish? → DECREASE confidence_score (-0.15 to -0.20)
   - Example: 1d bullish + 1h bullish + 5m bullish entry = 0.85+ confidence
   - Example: 1d bearish + 1h sideways + 5m bullish = 0.50-0.60 confidence (conflict!)

✅ STEP 4: REASONING - MUST mention ALL ${imageFiles.length} timeframes explicitly:
   Example: "1d timeframe shows strong bullish trend above all EMAs. 1h confirms with bullish MACD. 5m provides optimal entry near support at 1.1590 with tight stop loss."

✅ STEP 5: PRIMARY TIMEFRAME:
   - Use the LOWEST timeframe (where entry would occur) in "timeframe" field
   - But base confidence on ALL timeframes combined
` : ''}`,
            },
            // Add CSV data as text block (if available)
            ...(csvContext ? [{
              type: 'text' as const,
              text: csvContext
            }] : []),
            // Add all images
            ...imageContents,
          ],
        },
      ],
      max_tokens: 3000, // Increased for detailed_analysis (300-500 words)
      response_format: { type: 'json_object' },
    })

    const content = response.choices[0]?.message?.content
    if (!content) {
      return NextResponse.json(
        { error: 'No response from Vision API' },
        { status: 500 }
      )
    }

    let analysis = JSON.parse(content)

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

    // Normalize only obvious duplicates (keep it minimal!)
    const aliasMap: Record<string, string> = {
      'Silber': 'XAG/USD',
      'Silver': 'XAG/USD',
      'Gold': 'XAU/USD',
      'XAUUSD': 'XAU/USD',
      'Dow Jones': 'DJI',
      'NASDAQ 100': 'NDX',
      'S&P 500': 'SPX',
    }

    const detectedSymbol = analysis.symbol || symbol
    const normalizedSymbol = aliasMap[detectedSymbol] || detectedSymbol

    console.log(`📊 Symbol: "${detectedSymbol}" → "${normalizedSymbol}", Timeframe: ${analysis.timeframe}`)

    // Get or create symbol in market_symbols table
    // Try to find existing symbol (any vendor)
    let { data: symbolData, error: symbolError } = await supabase
      .from('market_symbols')
      .select('id, symbol')
      .eq('symbol', normalizedSymbol)
      .limit(1)
      .maybeSingle()

    if (symbolError || !symbolData) {
      console.log(`⚠️ Symbol "${normalizedSymbol}" not found, auto-creating...`)

      // Auto-create symbol with vendor='vision'
      const { data: newSymbol, error: insertError } = await supabase
        .from('market_symbols')
        .insert({
          vendor: 'vision', // Mark as Vision-detected symbol
          symbol: normalizedSymbol,
          alias: detectedSymbol, // Keep original name from Vision as alias
          active: true,
        })
        .select('id, symbol')
        .single()

      if (insertError || !newSymbol) {
        console.error('❌ Failed to create symbol:', insertError)
        return NextResponse.json(
          { error: `Failed to create symbol ${normalizedSymbol}` },
          { status: 500 }
        )
      }

      console.log(`✅ Created new symbol: ${normalizedSymbol} (vendor: vision)`)
      symbolData = newSymbol
    }

    // Write to chart_analyses table
    const { data: insertedAnalysis, error: insertError } = await supabase
      .from('chart_analyses')
      .insert({
        symbol_id: symbolData.id,
        timeframe: analysis.timeframe || '5m',
        chart_url: screenshotUrls[0], // Primary screenshot URL from Supabase Storage
        patterns_detected: analysis.patterns_detected || [],
        trend: analysis.trend || 'unknown',
        support_levels: analysis.support_levels || [],
        resistance_levels: analysis.resistance_levels || [],
        confidence_score: analysis.confidence_score,
        analysis_summary: analysis.reasoning || analysis.key_events || '',
        payload: {
          ...analysis,
          screenshot_urls: screenshotUrls, // Store all screenshot URLs in payload
          num_timeframes: files.length,
        }, // Store complete analysis as JSON
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

    console.log(`✅ Saved multi-timeframe analysis for ${normalizedSymbol} (${files.length} timeframe${files.length > 1 ? 's' : ''}: ${analysis.timeframe})`)

    return NextResponse.json({
      analysis_id: insertedAnalysis.id,
      symbol: normalizedSymbol,
      timeframe: analysis.timeframe,
      current_price: analysis.current_price,

      // Technical Indicators (23 total)
      ema_20: analysis.ema_20,
      ema_50: analysis.ema_50,
      ema_200: analysis.ema_200,
      rsi_14: analysis.rsi_14,
      atr_14: analysis.atr_14,
      macd_line: analysis.macd_line,
      macd_signal: analysis.macd_signal,
      macd_histogram: analysis.macd_histogram,
      bb_upper: analysis.bb_upper,
      bb_middle: analysis.bb_middle,
      bb_lower: analysis.bb_lower,
      pivot_point: analysis.pivot_point,
      resistance_1: analysis.resistance_1,
      support_1: analysis.support_1,
      resistance_2: analysis.resistance_2,
      support_2: analysis.support_2,
      adx_14: analysis.adx_14,
      di_plus: analysis.di_plus,
      di_minus: analysis.di_minus,
      volume: analysis.volume,
      volatility_pct: analysis.volatility_pct,
      price_vs_ema20_pct: analysis.price_vs_ema20_pct,
      price_vs_ema50_pct: analysis.price_vs_ema50_pct,
      price_vs_ema200_pct: analysis.price_vs_ema200_pct,

      // Trend Analysis
      trend: analysis.trend,
      trend_strength: analysis.trend_strength,
      momentum_bias: analysis.momentum_bias,

      // Support/Resistance
      support_levels: analysis.support_levels,
      resistance_levels: analysis.resistance_levels,

      // Patterns & Events
      patterns_detected: analysis.patterns_detected,
      market_structure: analysis.market_structure,
      key_events: analysis.key_events,

      // Trading Setup
      setup_type: analysis.setup_type,
      entry_price: analysis.entry_price,
      stop_loss: analysis.stop_loss,
      take_profit: analysis.take_profit,
      risk_reward: analysis.risk_reward,
      reasoning: analysis.reasoning,
      detailed_analysis: analysis.detailed_analysis,
      timeframe_validity: analysis.timeframe_validity,

      // Quality & Confidence
      confidence_score: analysis.confidence_score,
      chart_quality: analysis.chart_quality,
      key_factors: analysis.key_factors,

      screenshot_urls: screenshotUrls, // All screenshot URLs
      num_timeframes: files.length,
    })

  } catch (error) {
    console.error('❌ Screenshot analysis error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze screenshot' },
      { status: 500 }
    )
  }
}
