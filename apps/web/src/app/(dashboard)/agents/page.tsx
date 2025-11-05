import { Suspense } from 'react'
import { createServerClient } from '@/lib/supabase/server'
import { AgentFilter } from '@/components/agents/agent-filter'
import { SetupStats } from '@/components/agents/setup-stats'
import { TradingSetupCard } from '@/components/agents/trading-setup-card'
import { Card, CardContent } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'

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
    // Query chart_analyses table for ChartWatcher and SignalBot setups
    // Note: Using 'as any' because chart_analyses table exists but is not in generated types yet
    const { data: chartAnalyses, error } = await (supabase as any)
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
      .limit(50)

    if (error) {
      console.error('Error fetching setups:', error)
      return []
    }

    if (!chartAnalyses || chartAnalyses.length === 0) {
      return []
    }

    // Transform data to unified format
    const setups: TradingSetup[] = chartAnalyses.map((analysis: any) => {
      // Determine agent name based on timeframe (from chart_watcher.py logic)
      let agent_name = 'ChartWatcher'
      if (analysis.timeframe === '15m' || analysis.timeframe === '1h') {
        agent_name = analysis.payload?.agent_name || 'ChartWatcher'
      }

      return {
        id: analysis.id,
        symbol_id: analysis.symbol_id,
        symbol: analysis.market_symbols?.symbol || 'Unknown',
        timeframe: analysis.timeframe,
        agent_name,
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
      }
    })

    // Filter by selected agents if provided
    if (agentFilter && agentFilter.length > 0) {
      return setups.filter((setup) => agentFilter.includes(setup.agent_name))
    }

    return setups
  } catch (error) {
    console.error('Error in getSetups:', error)
    return []
  }
}

export default async function AgentsPage({
  searchParams,
}: {
  searchParams: SearchParams
}) {
  // Parse agent filter from URL params
  const agentFilter = searchParams.agents?.split(',').filter(Boolean)

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

      {/* Stats Section */}
      <SetupStats setups={setups} />

      {/* Filters Section */}
      <AgentFilter currentFilter={agentFilter} />

      {/* Setups Grid */}
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
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {setups.map((setup) => (
              <TradingSetupCard key={setup.id} setup={setup} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
