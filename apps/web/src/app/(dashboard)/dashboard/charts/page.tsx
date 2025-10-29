import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export const metadata = {
  title: 'Charts - TradeMatrix.ai',
  description: 'View market charts and technical analysis',
}

export default function ChartsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Charts</h1>
        <p className="text-muted-foreground mt-1">
          Analyze market trends with advanced charting tools
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Market Charts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              Chart visualization coming soon. Integration with TradingView
              Lightweight Charts.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
