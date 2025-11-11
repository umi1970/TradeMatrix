import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const symbol = formData.get('symbol') as string | null

    if (!file) {
      return NextResponse.json(
        { error: 'Missing file' },
        { status: 400 }
      )
    }

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      return NextResponse.json(
        { error: 'File must be a CSV' },
        { status: 400 }
      )
    }

    console.log(`📥 Received CSV upload: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`)

    // Extract broker from filename (e.g., "CAPITALCOM_US30, 15.csv" -> "CAPITALCOM")
    let broker: string | null = null
    const fileNameWithoutExt = file.name.replace('.csv', '')
    const symbolPart = fileNameWithoutExt.split(',')[0]?.trim()

    if (symbolPart && (symbolPart.includes('_') || symbolPart.includes(':'))) {
      const separator = symbolPart.includes('_') ? '_' : ':'
      const parts = symbolPart.split(separator)
      if (parts.length === 2) {
        broker = parts[0].toUpperCase()
      }
    }

    console.log(`📊 Extracted broker: ${broker || 'none'}`)

    // Upload CSV to Supabase Storage
    const timestamp = Date.now()
    const fileName = `${timestamp}_${file.name}`
    const filePath = `charts/${fileName}`

    const { data: uploadData, error: uploadError } = await supabase
      .storage
      .from('charts')
      .upload(filePath, file, {
        contentType: 'text/csv',
        cacheControl: '3600',
      })

    if (uploadError) {
      console.error('❌ Failed to upload CSV:', uploadError)
      return NextResponse.json(
        { error: 'Failed to upload CSV' },
        { status: 500 }
      )
    }

    // Get public URL
    const { data: urlData } = supabase
      .storage
      .from('charts')
      .getPublicUrl(filePath)

    const csvUrl = urlData.publicUrl
    console.log(`✅ CSV uploaded: ${csvUrl}`)

    // Call FastAPI to parse CSV
    const fastApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://135.181.195.241:8000'
    const parseUrl = `${fastApiUrl}/api/parse-csv`

    console.log(`🤖 Calling FastAPI: ${parseUrl}`)

    // Create FormData for FastAPI
    const fastApiFormData = new FormData()
    fastApiFormData.append('file', file)
    if (symbol) {
      fastApiFormData.append('symbol', symbol)
    }

    const parseResponse = await fetch(parseUrl, {
      method: 'POST',
      body: fastApiFormData,
    })

    if (!parseResponse.ok) {
      const errorText = await parseResponse.text()
      console.error('❌ FastAPI parsing failed:', errorText)
      return NextResponse.json(
        { error: 'Failed to parse CSV', details: errorText },
        { status: 500 }
      )
    }

    const analysis = await parseResponse.json()

    console.log(`✅ CSV parsed: ${analysis.symbol} ${analysis.timeframe} - ${analysis.trend} trend`)

    // Get or create symbol in market_symbols table
    const normalizedSymbol = analysis.symbol

    let { data: symbolData, error: symbolError } = await supabase
      .from('market_symbols')
      .select('id, symbol')
      .eq('symbol', normalizedSymbol)
      .limit(1)
      .maybeSingle()

    if (symbolError || !symbolData) {
      console.log(`⚠️ Symbol "${normalizedSymbol}" not found, auto-creating...`)

      // Use broker as vendor if available, otherwise 'tradingview'
      const vendor = broker ? broker.toLowerCase() : 'tradingview'

      const { data: newSymbol, error: insertError } = await supabase
        .from('market_symbols')
        .insert({
          vendor: vendor,
          symbol: normalizedSymbol,
          alias: broker ? `${broker}:${normalizedSymbol}` : normalizedSymbol,
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

      console.log(`✅ Created new symbol: ${normalizedSymbol} (vendor: ${vendor}, broker: ${broker || 'none'})`)
      symbolData = newSymbol
    }

    // Write to chart_analyses table
    const { data: insertedAnalysis, error: insertError } = await supabase
      .from('chart_analyses')
      .insert({
        symbol_id: symbolData.id,
        timeframe: analysis.timeframe || '15m',
        chart_url: csvUrl, // CSV URL in Supabase Storage
        patterns_detected: [],
        trend: analysis.trend || 'unknown',
        support_levels: analysis.data.support_1 ? [analysis.data.support_1, analysis.data.support_2] : [],
        resistance_levels: analysis.data.resistance_1 ? [analysis.data.resistance_1, analysis.data.resistance_2] : [],
        confidence_score: analysis.confidence_score,
        analysis_summary: analysis.reasoning || '',
        payload: analysis.data, // Store complete analysis as JSON
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

    console.log(`✅ Saved analysis for ${normalizedSymbol} (${analysis.timeframe})`)

    return NextResponse.json({
      analysis_id: insertedAnalysis.id,
      symbol: normalizedSymbol,
      timeframe: analysis.timeframe,
      current_price: analysis.current_price,
      trend: analysis.trend,
      trend_strength: analysis.trend_strength,
      confidence_score: analysis.confidence_score,
      setup_type: analysis.setup_type,
      entry_price: analysis.entry_price,
      stop_loss: analysis.stop_loss,
      take_profit: analysis.take_profit,
      risk_reward: analysis.risk_reward,
      reasoning: analysis.reasoning,
      csv_url: csvUrl,
    })

  } catch (error) {
    console.error('❌ CSV upload error:', error)
    return NextResponse.json(
      { error: 'Failed to process CSV', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
