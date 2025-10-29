'use client'

import { MarketOverviewCard } from '@/components/dashboard/market-overview-card'
import { TradeSummaryCard } from '@/components/dashboard/trade-summary-card'
import { AgentStatusCard } from '@/components/dashboard/agent-status-card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, RefreshCw } from 'lucide-react'

// Mock data - will be replaced with real Supabase data
const mockMarketData = [
  {
    symbol: 'DAX',
    name: 'DAX 40',
    price: 17542.75,
    change: 142.5,
    changePercent: 0.82,
    trend: 'up' as const,
  },
  {
    symbol: 'NDX',
    name: 'NASDAQ 100',
    price: 16234.88,
    change: -87.32,
    changePercent: -0.54,
    trend: 'down' as const,
  },
  {
    symbol: 'EURUSD',
    name: 'EUR/USD',
    price: 1.0847,
    change: 0.0012,
    changePercent: 0.11,
    trend: 'up' as const,
  },
]

const mockTradeSummary = {
  totalTrades: 45,
  winningTrades: 28,
  losingTrades: 17,
  winRate: 62.2,
  totalProfitLoss: 3250.75,
  averageWin: 245.5,
  averageLoss: 132.8,
}

const mockAgents = [
  {
    name: 'ChartWatcher',
    status: 'active' as const,
    lastRun: '5 minutes ago',
    description: 'Monitors charts and extracts market values',
    icon: 'chart' as const,
  },
  {
    name: 'SignalBot',
    status: 'idle' as const,
    lastRun: '1 hour ago',
    description: 'Evaluates market structure for entry signals',
    icon: 'signal' as const,
  },
  {
    name: 'RiskManager',
    status: 'active' as const,
    lastRun: '2 minutes ago',
    description: 'Calculates position sizes and stop losses',
    icon: 'risk' as const,
  },
  {
    name: 'JournalBot',
    status: 'idle' as const,
    lastRun: '3 hours ago',
    description: 'Creates automated trading reports',
    icon: 'journal' as const,
  },
]

export default function DashboardPage() {
  // Using mock data - remove 'use client' if you want to fetch from Supabase server-side
  // Or use client-side data fetching with useEffect + createBrowserClient()

  // Fetch recent trades (will be implemented with real data)
  let recentTrades: any[] = []
  try {
    const { data } = await supabase
      .from('trades')
      .select('*')
      .eq('user_id', user?.id || '')
      .order('created_at', { ascending: false })
      .limit(5)
    recentTrades = data || []
  } catch (error) {
    console.log('Trades table not yet available')
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your trading performance and AI agents
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Trade
          </Button>
        </div>
      </div>

      {/* Market Overview */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {mockMarketData.map((market) => (
            <MarketOverviewCard key={market.symbol} market={market} />
          ))}
        </div>
      </section>

      {/* Trade Summary & Quick Stats */}
      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TradeSummaryCard summary={mockTradeSummary} />
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" className="w-full justify-start">
              View All Trades
            </Button>
            <Button variant="outline" className="w-full justify-start">
              Generate Report
            </Button>
            <Button variant="outline" className="w-full justify-start">
              Analyze Charts
            </Button>
          </CardContent>
        </Card>
      </section>

      {/* AI Agents Status */}
      <section>
        <h2 className="text-xl font-semibold mb-4">AI Agents</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {mockAgents.map((agent) => (
            <AgentStatusCard
              key={agent.name}
              agent={agent}
              onAction={() => console.log(`Running ${agent.name}`)}
            />
          ))}
        </div>
      </section>

      {/* Recent Activity */}
      <section>
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {recentTrades.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">
                  No recent trades. Start trading to see your activity here.
                </p>
                <Button className="mt-4" variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Create First Trade
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {recentTrades.map((trade: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between border-b pb-3 last:border-0"
                  >
                    <div>
                      <p className="font-medium">{trade.symbol}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(trade.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p
                        className={`font-semibold ${
                          trade.profit_loss >= 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {trade.profit_loss >= 0 ? '+' : ''}$
                        {trade.profit_loss?.toFixed(2)}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {trade.status}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
