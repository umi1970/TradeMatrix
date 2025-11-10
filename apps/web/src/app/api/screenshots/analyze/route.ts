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
              text: `You are analyzing a screenshot of market data for ${symbol}.

Extract the following information:
1. Current Price (the most recent/current price shown)
2. Timestamp (when the data was captured - look for date/time on the chart)

IMPORTANT RULES:
- Only extract VISIBLE data from the screenshot
- Current price must be a valid number (no text, no symbols except decimal point)
- If you cannot find the data with high confidence, return null
- Be precise - trading depends on accurate price data

Respond in JSON format:
{
  "price": <number>,
  "timestamp": "<ISO 8601 string>",
  "confidence": <0.0 to 1.0>
}`,
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
      max_tokens: 500,
      response_format: { type: 'json_object' },
    })

    const content = response.choices[0]?.message?.content
    if (!content) {
      return NextResponse.json(
        { error: 'No response from Vision API' },
        { status: 500 }
      )
    }

    const extracted = JSON.parse(content)

    console.log(`✅ Extracted data for ${symbol}:`, extracted)

    // Validate extracted data
    if (!extracted.price || extracted.confidence < 0.7) {
      return NextResponse.json(
        { error: 'Low confidence extraction or missing data' },
        { status: 400 }
      )
    }

    // Get symbol_id from market_symbols table
    const { data: symbolData, error: symbolError } = await supabase
      .from('market_symbols')
      .select('id')
      .eq('symbol', symbol)
      .single()

    if (symbolError || !symbolData) {
      return NextResponse.json(
        { error: `Symbol ${symbol} not found in database` },
        { status: 404 }
      )
    }

    // Write to current_prices table
    const { error: upsertError } = await supabase
      .from('current_prices')
      .upsert({
        symbol_id: symbolData.id,
        price: extracted.price,
        open: extracted.price, // We don't have open from screenshot
        high: extracted.price,
        low: extracted.price,
        volume: 0,
        price_timestamp: extracted.timestamp || new Date().toISOString(),
      }, {
        onConflict: 'symbol_id'
      })

    if (upsertError) {
      console.error('❌ Failed to write to database:', upsertError)
      return NextResponse.json(
        { error: 'Failed to save price data' },
        { status: 500 }
      )
    }

    console.log(`✅ Saved price for ${symbol}: ${extracted.price}`)

    return NextResponse.json({
      price: extracted.price,
      timestamp: extracted.timestamp,
      confidence: extracted.confidence,
    })

  } catch (error) {
    console.error('❌ Screenshot analysis error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze screenshot' },
      { status: 500 }
    )
  }
}
