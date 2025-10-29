import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'

interface MarketData {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  trend: 'up' | 'down' | 'neutral'
}

interface MarketOverviewCardProps {
  market: MarketData
}

export function MarketOverviewCard({ market }: MarketOverviewCardProps) {
  const getTrendIcon = () => {
    switch (market.trend) {
      case 'up':
        return <ArrowUpRight className="h-4 w-4" />
      case 'down':
        return <ArrowDownRight className="h-4 w-4" />
      default:
        return <Minus className="h-4 w-4" />
    }
  }

  const getTrendColor = () => {
    switch (market.trend) {
      case 'up':
        return 'text-green-600 bg-green-50 dark:bg-green-950 dark:text-green-400'
      case 'down':
        return 'text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400'
      default:
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950 dark:text-gray-400'
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{market.name}</CardTitle>
        <Badge variant="outline" className="text-xs">
          {market.symbol}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div>
            <div className="text-2xl font-bold">
              ${market.price.toLocaleString()}
            </div>
            <div className={`flex items-center gap-1 text-sm font-medium mt-1 ${getTrendColor()}`}>
              {getTrendIcon()}
              <span>
                {market.change >= 0 ? '+' : ''}
                {market.change.toFixed(2)}
              </span>
              <span className="text-xs">
                ({market.changePercent >= 0 ? '+' : ''}
                {market.changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Default export for easy async loading
export default MarketOverviewCard
