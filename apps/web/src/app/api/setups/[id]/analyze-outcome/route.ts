import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import OpenAI from 'openai'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

interface AnalyzeParams {
  params: Promise<{
    id: string
  }>
}

export async function POST(request: NextRequest, context: AnalyzeParams) {
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  })

  try {
    const { id: setupId } = await context.params

    // Get setup from database
    const { data: setup, error: setupError } = await supabase
      .from('setups')
      .select(`
        *,
        market_symbols (
          symbol,
          alias
        )
      `)
      .eq('id', setupId)
      .single()

    if (setupError || !setup) {
      return NextResponse.json(
        { error: 'Setup not found' },
        { status: 404 }
      )
    }

    // Check if setup has an outcome
    if (!setup.outcome) {
      return NextResponse.json(
        { error: 'Cannot analyze: Setup has no outcome yet. Wait for SL/TP hit.' },
        { status: 400 }
      )
    }

    // Check if lesson already exists
    const { data: existingLesson } = await supabase
      .from('trade_lessons')
      .select('*')
      .eq('setup_id', setupId)
      .maybeSingle()

    if (existingLesson) {
      return NextResponse.json({
        message: 'Lesson already exists for this setup',
        lesson: existingLesson,
      })
    }

    // Extract setup data
    const symbol = (setup.market_symbols as any)?.symbol || 'Unknown'
    const entryPrice = setup.entry_price
    const stopLoss = setup.stop_loss
    const takeProfit = setup.take_profit
    const side = setup.side
    const confidence = setup.confidence_score || setup.confidence || 0
    const outcome = setup.outcome
    const pnlPercent = setup.pnl_percent
    const entryHitAt = setup.entry_hit_at
    const slHitAt = setup.sl_hit_at
    const tpHitAt = setup.tp_hit_at
    const closedAt = setup.closed_at

    // Extract original reasoning from payload
    const payload = setup.payload || {}
    const originalReasoning = payload.reasoning || payload.detailed_analysis || setup.analysis || 'No reasoning provided'

    // Calculate trade duration
    let tradeDurationHours = 0
    if (closedAt && entryHitAt) {
      const closedTime = new Date(closedAt).getTime()
      const entryTime = new Date(entryHitAt).getTime()
      tradeDurationHours = (closedTime - entryTime) / (1000 * 60 * 60)
    }

    // Build OpenAI Prompt
    const outcomeType = outcome === 'win' ? 'succeeded' : 'failed'
    const hitLevel = outcome === 'win' ? 'Take Profit' : 'Stop Loss'

    const prompt = `Analyze why this ${side.toUpperCase()} trade ${outcomeType}:

ORIGINAL SETUP:
- Symbol: ${symbol}
- Side: ${side.toUpperCase()}
- Entry: ${entryPrice}
- Stop Loss: ${stopLoss}
- Take Profit: ${takeProfit}
- Risk/Reward: ${payload.risk_reward || 'Unknown'}
- Original Reasoning: ${originalReasoning}
- Confidence Score: ${(confidence * 100).toFixed(0)}%
- Timeframe: ${payload.timeframe || 'Unknown'}

ACTUAL OUTCOME:
- Outcome: ${outcome.toUpperCase()} (${hitLevel} Hit)
- P&L: ${pnlPercent?.toFixed(2)}%
- Entry Hit At: ${entryHitAt ? new Date(entryHitAt).toISOString() : 'N/A'}
- ${outcome === 'win' ? 'TP' : 'SL'} Hit At: ${(tpHitAt || slHitAt) ? new Date(tpHitAt || slHitAt!).toISOString() : 'N/A'}
- Trade Duration: ${tradeDurationHours.toFixed(1)} hours

${outcome === 'loss' ? 'ANALYSIS FOCUS: Why did the trade fail?' : 'ANALYSIS FOCUS: Why did the trade succeed?'}

Provide a structured analysis in the following format:

1. ROOT CAUSE:
   - What was the primary reason for ${outcome === 'win' ? 'success' : 'failure'}?
   - Was the original analysis correct or flawed?

2. INDICATOR ANALYSIS:
   - Which technical indicators ${outcome === 'win' ? 'correctly predicted' : 'failed to predict'} the outcome?
   - List 2-3 specific indicators that were ${outcome === 'win' ? 'accurate' : 'misleading'}

3. LESSON LEARNED:
   - What is the key takeaway from this trade?
   - How can we ${outcome === 'win' ? 'replicate this success' : 'avoid this mistake'} in the future?

4. IMPROVED STRATEGY:
   - ${outcome === 'win' ? 'What made this setup strong?' : 'How should the strategy be adjusted?'}
   - Specific actionable improvements (e.g., "Require RSI confirmation below 30", "Wait for EMA crossover")

Keep the response concise but actionable. Focus on practical improvements.`

    console.log(`📊 Analyzing outcome for setup ${setupId} (${outcome})...`)

    // Call OpenAI
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are an expert trading analyst specializing in post-trade analysis and strategy improvement. Provide concise, actionable insights.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 1000,
    })

    const analysisText = completion.choices[0]?.message?.content || ''

    if (!analysisText) {
      throw new Error('OpenAI returned empty analysis')
    }

    // Parse analysis sections (simple regex extraction)
    const rootCauseMatch = analysisText.match(/1\.\s*ROOT CAUSE:\s*([\s\S]*?)(?=2\.|$)/i)
    const indicatorMatch = analysisText.match(/2\.\s*INDICATOR ANALYSIS:\s*([\s\S]*?)(?=3\.|$)/i)
    const lessonMatch = analysisText.match(/3\.\s*LESSON LEARNED:\s*([\s\S]*?)(?=4\.|$)/i)
    const strategyMatch = analysisText.match(/4\.\s*IMPROVED STRATEGY:\s*([\s\S]*?)$/i)

    const rootCause = rootCauseMatch?.[1]?.trim() || null
    const indicatorAnalysis = indicatorMatch?.[1]?.trim() || null
    const lessonLearned = lessonMatch?.[1]?.trim() || analysisText.substring(0, 500) // Fallback
    const improvedStrategy = strategyMatch?.[1]?.trim() || null

    // Extract failed indicators (parse from indicator analysis)
    const failedIndicators: string[] = []
    if (indicatorAnalysis && outcome === 'loss') {
      // Simple extraction: Look for indicator names (RSI, MACD, EMA, etc.)
      const commonIndicators = ['RSI', 'MACD', 'EMA', 'SMA', 'Bollinger', 'Stochastic', 'ADX', 'ATR', 'Volume', 'Support', 'Resistance']
      commonIndicators.forEach(indicator => {
        if (indicatorAnalysis.toLowerCase().includes(indicator.toLowerCase())) {
          failedIndicators.push(indicator)
        }
      })
    }

    // Save to trade_lessons table
    const { data: lesson, error: lessonError } = await supabase
      .from('trade_lessons')
      .insert({
        setup_id: setupId,
        outcome: outcome,
        root_cause: rootCause,
        failed_indicators: failedIndicators.length > 0 ? failedIndicators : null,
        lesson_learned: lessonLearned,
        improved_strategy: improvedStrategy,
        analysis_payload: {
          full_analysis: analysisText,
          prompt_used: prompt,
          model: 'gpt-4o-mini',
          analyzed_at: new Date().toISOString(),
        },
      })
      .select()
      .single()

    if (lessonError) {
      console.error('Failed to save lesson:', lessonError)
      return NextResponse.json(
        { error: 'Failed to save analysis' },
        { status: 500 }
      )
    }

    // Update setup with outcome_analysis
    await supabase
      .from('setups')
      .update({
        outcome_analysis: lessonLearned,
        updated_at: new Date().toISOString(),
      })
      .eq('id', setupId)

    console.log(`✅ Created trade lesson ${lesson.id} for setup ${setupId}`)

    return NextResponse.json({
      message: `Trade outcome analyzed successfully (${outcome})`,
      lesson: {
        id: lesson.id,
        root_cause: rootCause,
        failed_indicators: failedIndicators,
        lesson_learned: lessonLearned,
        improved_strategy: improvedStrategy,
      },
      full_analysis: analysisText,
    })

  } catch (error) {
    console.error('❌ Analyze outcome error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze outcome' },
      { status: 500 }
    )
  }
}
