'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'

interface Trade {
  id: string
  symbol: string
  side: 'long' | 'short'
  entry_price: number
  exit_price: number | null
  position_size: number
  stop_loss: number | null
  take_profit: number | null
  status: 'open' | 'closed' | 'cancelled'
  pnl: number | null
  pnl_percentage: number | null
  entry_time: string
  exit_time: string | null
  created_at: string
}

interface PerformanceStats {
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  totalProfitLoss: number
  averageWin: number
  averageLoss: number
}

export function TradePerformanceCard() {
  const [stats, setStats] = useState<PerformanceStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchTradePerformance() {
      try {
        const supabase = createBrowserClient()

        // Get current user
        const { data: { user }, error: userError } = await supabase.auth.getUser()
        if (userError || !user) {
          setError('Authentication required')
          setLoading(false)
          return
        }

        // Fetch all closed trades
        const { data: trades, error: tradesError } = await supabase
          .from('trades')
          .select('*')
          .eq('user_id', user.id)
          .eq('status', 'closed')
          .order('created_at', { ascending: false })

        if (tradesError) {
          throw tradesError
        }

        if (!trades || trades.length === 0) {
          setStats({
            totalTrades: 0,
            winningTrades: 0,
            losingTrades: 0,
            winRate: 0,
            totalProfitLoss: 0,
            averageWin: 0,
            averageLoss: 0,
          })
          setLoading(false)
          return
        }

        // Calculate statistics
        const totalTrades = trades.length
        const winningTrades = trades.filter(t => (t.pnl ?? 0) > 0).length
        const losingTrades = trades.filter(t => (t.pnl ?? 0) < 0).length
        const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0

        const totalProfitLoss = trades.reduce((sum, trade) => sum + (trade.pnl ?? 0), 0)

        const wins = trades.filter(t => (t.pnl ?? 0) > 0)
        const losses = trades.filter(t => (t.pnl ?? 0) < 0)

        const averageWin = wins.length > 0
          ? wins.reduce((sum, t) => sum + (t.pnl ?? 0), 0) / wins.length
          : 0

        const averageLoss = losses.length > 0
          ? losses.reduce((sum, t) => sum + (t.pnl ?? 0), 0) / losses.length
          : 0

        setStats({
          totalTrades,
          winningTrades,
          losingTrades,
          winRate,
          totalProfitLoss,
          averageWin,
          averageLoss,
        })
      } catch (err) {
        console.error('Error fetching trade performance:', err)
        setError('Failed to load performance data')
      } finally {
        setLoading(false)
      }
    }

    fetchTradePerformance()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trade Performance</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trade Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    )
  }

  if (stats?.totalTrades === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trade Performance</CardTitle>
          <CardDescription>Your trading statistics will appear here</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-sm text-muted-foreground">
              No trades yet. Create your first trade!
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade Performance</CardTitle>
        <CardDescription>Overall trading statistics</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Total P/L */}
        <div className="flex items-center justify-between pb-4 border-b">
          <span className="text-sm font-medium">Total P/L</span>
          <span
            className={`text-2xl font-bold ${
              stats!.totalProfitLoss >= 0 ? 'text-green-500' : 'text-red-500'
            }`}
          >
            {stats!.totalProfitLoss >= 0 ? '+' : ''}
            ${stats!.totalProfitLoss.toFixed(2)}
          </span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Total Trades</p>
            <p className="text-2xl font-bold">{stats!.totalTrades}</p>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Win Rate</p>
            <p className="text-2xl font-bold">{stats!.winRate.toFixed(1)}%</p>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Wins</p>
            <p className="text-xl font-semibold text-green-500">
              {stats!.winningTrades}
            </p>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Losses</p>
            <p className="text-xl font-semibold text-red-500">
              {stats!.losingTrades}
            </p>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Avg Win</p>
            <p className="text-lg font-semibold text-green-500">
              +${stats!.averageWin.toFixed(2)}
            </p>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Avg Loss</p>
            <p className="text-lg font-semibold text-red-500">
              ${stats!.averageLoss.toFixed(2)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
