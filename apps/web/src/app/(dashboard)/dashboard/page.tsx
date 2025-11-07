'use client'

import { useState, useEffect } from 'react'
import { TradingViewWidget } from '@/components/dashboard/tradingview-widget'
import { SymbolPickerModal } from '@/components/dashboard/symbol-picker-modal'
import { AgentStatusCard } from '@/components/dashboard/agent-status-card'
import { TradePerformanceCard } from '@/components/dashboard/trade-performance-card'
import { MarketSentimentCard } from '@/components/dashboard/market-sentiment-card'
import { TopPerformersCard } from '@/components/dashboard/top-performers-card'
import { TradingStreakCard } from '@/components/dashboard/trading-streak-card'
import { RiskMetricsCard } from '@/components/dashboard/risk-metrics-card'
import { RecentTradesCard } from '@/components/dashboard/recent-trades-card'
import { AlertSettingsCard } from '@/components/dashboard/alert-settings-card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Plus, RefreshCw, Loader2, Settings } from 'lucide-react'
import { createBrowserClient } from '@/lib/supabase/client'

interface WatchlistItem {
  id: string
  position: number
  market_symbols: {
    id: string
    symbol: string
    alias: string | null
    tv_symbol: string | null
    vendor: string
    active: boolean
  }
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
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [showSymbolPicker, setShowSymbolPicker] = useState(false)
  const [userId, setUserId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Fetch user's watchlist with symbol details
  const fetchWatchlist = async () => {
    try {
      setError(null)
      const supabase = createBrowserClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        setError('Please sign in to view your watchlist')
        setIsLoading(false)
        return
      }

      setUserId(session.user.id)

      const { data, error: watchlistError } = await supabase
        .from('user_watchlist')
        .select('id, position, market_symbols(*)')
        .eq('user_id', session.user.id)
        .order('position')

      if (watchlistError) throw watchlistError

      setWatchlist(data || [])
    } catch (err: unknown) {
      console.error('Error fetching watchlist:', err)
      setError(err instanceof Error ? err.message : 'Failed to load watchlist')
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  // Initial fetch on mount
  useEffect(() => {
    fetchWatchlist()
  }, [])

  // Manual refresh handler
  const handleRefresh = () => {
    setIsRefreshing(true)
    fetchWatchlist()
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
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Market Overview</h2>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSymbolPicker(true)}
            disabled={!userId}
          >
            <Settings className="h-4 w-4 mr-2" />
            Edit Watchlist
          </Button>
        </div>

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
        ) : watchlist.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {watchlist
              .filter((item) => item.market_symbols.tv_symbol)
              .map((item) => (
                <TradingViewWidget
                  key={item.id}
                  symbol={item.market_symbols.tv_symbol!}
                  height={200}
                />
              ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <div className="text-center">
                <p className="text-muted-foreground mb-4">
                  No symbols in your watchlist
                </p>
                <Button onClick={() => setShowSymbolPicker(true)} disabled={!userId}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Symbols
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </section>

      {/* Symbol Picker Modal */}
      {userId && (
        <SymbolPickerModal
          open={showSymbolPicker}
          onOpenChange={setShowSymbolPicker}
          userId={userId}
          onSaved={fetchWatchlist}
        />
      )}

      {/* Performance Cards Row */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Performance Metrics</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <TradePerformanceCard />
          <MarketSentimentCard />
          <TopPerformersCard />
        </div>
      </section>

      {/* Stats & Quick Actions Row */}
      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <TradingStreakCard />
        <RiskMetricsCard />
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

      {/* Recent Trades */}
      <section>
        <RecentTradesCard />
      </section>

      {/* Alert Settings */}
      <section>
        <AlertSettingsCard />
      </section>

    </div>
  )
}
