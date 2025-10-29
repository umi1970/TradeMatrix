'use client'

import { useState, useEffect } from 'react'
import { MarketOverviewCard } from '@/components/dashboard/market-overview-card'
import { TradeSummaryCard } from '@/components/dashboard/trade-summary-card'
import { AgentStatusCard } from '@/components/dashboard/agent-status-card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Plus, RefreshCw, Loader2 } from 'lucide-react'

interface MarketData {
  symbol: string
  name: string
  price: number
  change: number | null
  changePercent: number | null
  trend: 'up' | 'down' | 'neutral'
  updatedAt: string
}

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
  const [marketData, setMarketData] = useState<MarketData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Mock recent trades - replace with real Supabase data later
  const recentTrades: any[] = []

  // Fetch market data from API
  const fetchMarketData = async () => {
    try {
      setError(null)
      const response = await fetch('/api/market-data/current')

      if (!response.ok) {
        throw new Error(`Failed to fetch market data: ${response.statusText}`)
      }

      const result = await response.json()
      setMarketData(result.data || [])
    } catch (err: any) {
      console.error('Error fetching market data:', err)
      setError(err.message || 'Failed to load market data')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  // Initial fetch on mount
  useEffect(() => {
    fetchMarketData()

    // Poll every 30 seconds for updates
    const interval = setInterval(fetchMarketData, 30000)

    return () => clearInterval(interval)
  }, [])

  // Manual refresh handler
  const handleRefresh = () => {
    setIsRefreshing(true)
    fetchMarketData()
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
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Trade
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>
            {error}
            <Button
              variant="link"
              size="sm"
              onClick={handleRefresh}
              className="ml-2"
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Market Overview */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardContent className="flex items-center justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : marketData.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {marketData.map((market) => (
              <MarketOverviewCard key={market.symbol} market={market} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <div className="text-center">
                <p className="text-muted-foreground">
                  No market data available
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Make sure the Celery worker is running to fetch live data
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  className="mt-4"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
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
