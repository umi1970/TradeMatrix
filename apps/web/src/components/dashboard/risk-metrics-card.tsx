'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Loader2, Info } from 'lucide-react'

interface Trade {
  id: string
  pnl: number | null
  pnl_percentage: number | null
  status: 'open' | 'closed' | 'cancelled'
  created_at: string
}

interface RiskMetrics {
  maxDrawdown: number | null
  maxDrawdownPercentage: number | null
  sharpeRatio: number | null
  profitFactor: number | null
  hasEnoughData: boolean
}

export function RiskMetricsCard() {
  const [metrics, setMetrics] = useState<RiskMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function calculateRiskMetrics() {
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
          .select('id, pnl, pnl_percentage, status, created_at')
          .eq('user_id', user.id)
          .eq('status', 'closed')
          .not('pnl', 'is', null)
          .order('created_at', { ascending: true })

        if (tradesError) {
          throw tradesError
        }

        if (!trades || trades.length < 5) {
          setMetrics({
            maxDrawdown: null,
            maxDrawdownPercentage: null,
            sharpeRatio: null,
            profitFactor: null,
            hasEnoughData: false
          })
          setLoading(false)
          return
        }

        // Calculate Max Drawdown
        let peak = 0
        let maxDrawdown = 0
        let runningTotal = 0

        trades.forEach((trade) => {
          runningTotal += trade.pnl ?? 0
          if (runningTotal > peak) {
            peak = runningTotal
          }
          const drawdown = peak - runningTotal
          if (drawdown > maxDrawdown) {
            maxDrawdown = drawdown
          }
        })

        const maxDrawdownPercentage = peak > 0 ? (maxDrawdown / peak) * 100 : 0

        // Calculate Profit Factor
        const grossProfit = trades
          .filter(t => (t.pnl ?? 0) > 0)
          .reduce((sum, t) => sum + (t.pnl ?? 0), 0)

        const grossLoss = Math.abs(
          trades
            .filter(t => (t.pnl ?? 0) < 0)
            .reduce((sum, t) => sum + (t.pnl ?? 0), 0)
        )

        const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : null

        // Calculate Sharpe Ratio (simplified)
        // Using returns instead of P/L for more accurate calculation
        const returns = trades.map(t => t.pnl ?? 0)
        const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length

        const variance = returns.reduce((sum, r) => {
          return sum + Math.pow(r - avgReturn, 2)
        }, 0) / returns.length

        const stdDev = Math.sqrt(variance)
        const sharpeRatio = stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : null // Annualized

        setMetrics({
          maxDrawdown,
          maxDrawdownPercentage,
          sharpeRatio,
          profitFactor,
          hasEnoughData: true
        })
      } catch (err) {
        console.error('Error calculating risk metrics:', err)
        setError('Failed to calculate risk metrics')
      } finally {
        setLoading(false)
      }
    }

    calculateRiskMetrics()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk Metrics</CardTitle>
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
          <CardTitle>Risk Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    )
  }

  if (!metrics?.hasEnoughData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk Metrics</CardTitle>
          <CardDescription>Advanced trading statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center space-y-3">
            <Info className="h-12 w-12 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium mb-1">Insufficient Data</p>
              <p className="text-xs text-muted-foreground">
                Complete at least 5 trades to see risk metrics
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Metrics</CardTitle>
        <CardDescription>Advanced trading statistics</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Max Drawdown */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Max Drawdown</span>
              <button
                className="text-muted-foreground hover:text-foreground transition-colors"
                title="The largest peak-to-trough decline in your account"
              >
                <Info className="h-3 w-3" />
              </button>
            </div>
            <div className="text-right">
              <div className="text-xl font-bold text-red-500">
                -${metrics.maxDrawdown?.toFixed(2)}
              </div>
              {metrics.maxDrawdownPercentage !== null && (
                <div className="text-xs text-red-500/70">
                  -{metrics.maxDrawdownPercentage.toFixed(2)}%
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Profit Factor */}
        {metrics.profitFactor !== null && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">Profit Factor</span>
                <button
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  title="Ratio of gross profit to gross loss (>1 is profitable)"
                >
                  <Info className="h-3 w-3" />
                </button>
              </div>
              <div className={`text-xl font-bold ${
                metrics.profitFactor >= 1 ? 'text-green-500' : 'text-red-500'
              }`}>
                {metrics.profitFactor.toFixed(2)}
              </div>
            </div>
            <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  metrics.profitFactor >= 1 ? 'bg-green-500' : 'bg-red-500'
                }`}
                style={{
                  width: `${Math.min((metrics.profitFactor / 3) * 100, 100)}%`
                }}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              {metrics.profitFactor >= 2
                ? 'Excellent risk/reward ratio'
                : metrics.profitFactor >= 1
                ? 'Profitable trading system'
                : 'Needs improvement'}
            </p>
          </div>
        )}

        {/* Sharpe Ratio */}
        {metrics.sharpeRatio !== null && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">Sharpe Ratio</span>
                <button
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  title="Risk-adjusted return metric (>1 is good, >2 is excellent)"
                >
                  <Info className="h-3 w-3" />
                </button>
              </div>
              <div className={`text-xl font-bold ${
                metrics.sharpeRatio >= 1 ? 'text-green-500' :
                metrics.sharpeRatio >= 0 ? 'text-yellow-500' : 'text-red-500'
              }`}>
                {metrics.sharpeRatio.toFixed(2)}
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              {metrics.sharpeRatio >= 2
                ? 'Excellent risk-adjusted returns'
                : metrics.sharpeRatio >= 1
                ? 'Good risk-adjusted returns'
                : metrics.sharpeRatio >= 0
                ? 'Moderate risk-adjusted returns'
                : 'Poor risk-adjusted returns'}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
