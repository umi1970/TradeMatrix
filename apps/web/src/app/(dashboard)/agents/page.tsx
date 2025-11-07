import { Suspense } from 'react'
import { createServerClient } from '@/lib/supabase/server'
import { AgentFilter } from '@/components/agents/agent-filter'
import { SetupStats } from '@/components/agents/setup-stats'
import { TradingSetupCard } from '@/components/agents/trading-setup-card'
import { AgentControlPanel } from '@/components/agents/agent-control-panel'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Loader2, Clock, Play } from 'lucide-react'

interface SearchParams {
  agents?: string
}

interface TradingSetup {
  id: string
  symbol_id: string
  symbol: string
  timeframe: string
  agent_name: string
  analysis: string
  chart_url: string
  chart_snapshot_id: string | null
  confidence_score: number
  created_at: string
  metadata: {
    setup_type?: string
    entry?: number
    sl?: number
    tp?: number
    patterns?: Array<{
      name: string
      type: string
      confidence: number
    }>
    trend?: string
    support_levels?: number[]
    resistance_levels?: number[]
  }
}

async function getSetups(agentFilter?: string[]): Promise<TradingSetup[]> {
  const supabase = await createServerClient()

  // Get user session
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    return []
  }

  try {
    // Parallel fetch: chart_analyses (ChartWatcher) + setups (MorningPlanner, JournalBot)
    const [chartAnalysesResult, tradingSetupsResult] = await Promise.all([
      // 1. Chart Analyses (ChartWatcher pattern detection)
      (supabase as any)
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
          created_at,
          payload,
          market_symbols!inner(symbol)
        `)
        .order('created_at', { ascending: false })
        .limit(25),

      // 2. Trading Setups (MorningPlanner with Entry/SL/TP)
      (supabase as any)
        .from('setups')
        .select(`
          id,
          symbol_id,
          strategy,
          side,
          entry_price,
          stop_loss,
          take_profit,
          confidence,
          status,
          created_at,
          payload,
          market_symbols!inner(symbol)
        `)
        .order('created_at', { ascending: false })
        .limit(25),
    ])

    const allSetups: TradingSetup[] = []

    // Transform chart_analyses
    if (chartAnalysesResult.data && chartAnalysesResult.data.length > 0) {
      const analysisSetups = chartAnalysesResult.data.map((analysis: any) => ({
        id: analysis.id,
        symbol_id: analysis.symbol_id,
        symbol: analysis.market_symbols?.symbol || 'Unknown',
        timeframe: analysis.timeframe,
        agent_name: 'ChartWatcher',
        analysis: analysis.analysis_summary || 'Pattern detection completed',
        chart_url: analysis.chart_url,
        chart_snapshot_id: analysis.payload?.chart_snapshot_id || null,
        confidence_score: parseFloat(analysis.confidence_score) || 0,
        created_at: analysis.created_at,
        metadata: {
          patterns: analysis.patterns_detected || [],
          trend: analysis.trend,
          support_levels: analysis.support_levels || [],
          resistance_levels: analysis.resistance_levels || [],
        },
      }))
      allSetups.push(...analysisSetups)
    }

    // Transform setups (MorningPlanner + AI-generated)
    if (tradingSetupsResult.data && tradingSetupsResult.data.length > 0) {
      const tradingSetups = tradingSetupsResult.data.map((setup: any) => {
        // Use AI reasoning if available, otherwise generic message
        const analysis = setup.payload?.reasoning
          ? setup.payload.reasoning
          : `${setup.strategy.replace(/_/g, ' ')} setup detected. ${setup.side.toUpperCase()} signal with ${(setup.confidence * 100).toFixed(0)}% confidence.`

        // Determine agent name
        let agentName = 'Unknown'
        if (setup.strategy === 'asia_sweep' || setup.strategy === 'y_low_rebound') {
          agentName = 'MorningPlanner'
        } else if (setup.strategy === 'pattern_based' || setup.module === 'ai_generated') {
          agentName = 'AI Setup Generator'
        }

        return {
          id: setup.id,
          symbol_id: setup.symbol_id,
          symbol: setup.market_symbols?.symbol || 'Unknown',
          timeframe: setup.payload?.timeframe || '1h',
          agent_name: agentName,
          analysis,
          chart_url: setup.payload?.chart_url_1h || setup.payload?.chart_url_15m || setup.payload?.chart_url || '',
          chart_snapshot_id: setup.payload?.chart_snapshot_id || null,
          confidence_score: parseFloat(setup.confidence) || 0,
          created_at: setup.created_at,
          metadata: {
            setup_type: setup.strategy,
            entry: parseFloat(setup.entry_price),
            sl: parseFloat(setup.stop_loss),
            tp: parseFloat(setup.take_profit),
            trend: setup.side === 'long' ? 'bullish' : 'bearish',
            support_levels: [],
            resistance_levels: [],
            patterns: setup.payload?.patterns || [],
          },
        }
      })
      allSetups.push(...tradingSetups)
    }

    // Sort all setups by created_at (newest first)
    allSetups.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    // Filter by selected agents if provided
    if (agentFilter && agentFilter.length > 0) {
      return allSetups.filter((setup) => agentFilter.includes(setup.agent_name))
    }

    return allSetups
  } catch (error) {
    console.error('Error in getSetups:', error)
    return []
  }
}

export default async function AgentsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>
}) {
  // Parse agent filter from URL params (Next.js 15: searchParams is now a Promise)
  const params = await searchParams
  const agentFilter = params.agents?.split(',').filter(Boolean)

  const setups = await getSetups(agentFilter)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Trading Agents</h1>
          <p className="text-muted-foreground mt-1">
            AI-generated trading setups with pattern detection and analysis
          </p>
        </div>
      </div>

      {/* Agent Control Panel */}
      <AgentControlPanel />

      {/* Stats Section */}
      <SetupStats setups={setups} />

      {/* Filters Section */}
      <AgentFilter currentFilter={agentFilter} />

      {/* Setups Grid - Grouped by Agent */}
      <section>
        {setups.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="text-center">
                <p className="text-muted-foreground mb-2">
                  No trading setups found
                </p>
                <p className="text-sm text-muted-foreground">
                  AI agents will generate setups automatically when market conditions are favorable
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-8">
            {/* Group setups by agent_name */}
            {Object.entries(
              setups.reduce((groups, setup) => {
                const agent = setup.agent_name
                if (!groups[agent]) groups[agent] = []
                groups[agent].push(setup)
                return groups
              }, {} as Record<string, typeof setups>)
            ).map(([agentName, agentSetups]) => (
              <div key={agentName}>
                <div className="flex items-center gap-3 mb-4 pb-2 border-b">
                  <h3 className="text-xl font-bold">{agentName}</h3>
                  <Badge variant="secondary" className="text-xs">{agentSetups.length}</Badge>
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {agentSetups.map((setup) => (
                    <TradingSetupCard key={setup.id} setup={setup} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
