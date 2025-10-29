import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'

interface TradeSummary {
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  totalProfitLoss: number
  averageWin: number
  averageLoss: number
}

interface TradeSummaryCardProps {
  summary: TradeSummary
}

export function TradeSummaryCard({ summary }: TradeSummaryCardProps) {
  const isProfitable = summary.totalProfitLoss >= 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Trade Summary</CardTitle>
        <Activity className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Total P&L */}
          <div>
            <div
              className={`text-2xl font-bold ${
                isProfitable ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {isProfitable ? '+' : ''}${summary.totalProfitLoss.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Total Profit/Loss
            </p>
          </div>

          {/* Win/Loss Stats */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <span className="text-muted-foreground">Wins:</span>
              <span className="font-semibold">{summary.winningTrades}</span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-red-600" />
              <span className="text-muted-foreground">Losses:</span>
              <span className="font-semibold">{summary.losingTrades}</span>
            </div>
          </div>

          {/* Win Rate */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Win Rate</span>
            <Badge
              variant={summary.winRate >= 50 ? 'default' : 'secondary'}
              className="font-semibold"
            >
              {summary.winRate.toFixed(1)}%
            </Badge>
          </div>

          {/* Average Win/Loss */}
          <div className="grid grid-cols-2 gap-4 pt-2 border-t">
            <div>
              <p className="text-xs text-muted-foreground">Avg Win</p>
              <p className="text-sm font-semibold text-green-600">
                +${summary.averageWin.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Avg Loss</p>
              <p className="text-sm font-semibold text-red-600">
                -${Math.abs(summary.averageLoss).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Default export for easy async loading
export default TradeSummaryCard
