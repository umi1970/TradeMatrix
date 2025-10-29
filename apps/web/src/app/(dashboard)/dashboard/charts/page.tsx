'use client'

import { useState, useEffect } from 'react'
import { TradingChart } from '@/components/dashboard/trading-chart'
import { ChartControls, type ChartSettings } from '@/components/dashboard/chart-controls'
import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'

interface OHLCVData {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export default function ChartsPage() {
  const [settings, setSettings] = useState<ChartSettings>({
    symbol: 'DAX',
    timeframe: '1h',
    showEMA20: true,
    showEMA50: true,
    showEMA200: true,
    showRSI: false,
    showMACD: false,
  })

  const [chartData, setChartData] = useState<OHLCVData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Generate sample data (in production, fetch from Supabase)
  const generateSampleData = (symbol: string, timeframe: string): OHLCVData[] => {
    const data: OHLCVData[] = []
    const now = Date.now()
    const timeframeMs = {
      '1m': 60 * 1000,
      '5m': 5 * 60 * 1000,
      '15m': 15 * 60 * 1000,
      '30m': 30 * 60 * 1000,
      '1h': 60 * 60 * 1000,
      '4h': 4 * 60 * 60 * 1000,
      '1d': 24 * 60 * 60 * 1000,
      '1w': 7 * 24 * 60 * 60 * 1000,
    }[timeframe] || 60 * 60 * 1000

    const numCandles = 300
    let basePrice = symbol === 'DAX' ? 18000 : symbol === 'NASDAQ' ? 16000 : symbol === 'EURUSD' ? 1.08 : 34000

    for (let i = numCandles; i >= 0; i--) {
      const time = Math.floor((now - i * timeframeMs) / 1000)
      const volatility = basePrice * 0.002 // 0.2% volatility
      const trend = Math.sin(i / 20) * volatility * 2 // Add trend

      const open = basePrice + (Math.random() - 0.5) * volatility
      const close = open + trend + (Math.random() - 0.5) * volatility
      const high = Math.max(open, close) + Math.random() * volatility
      const low = Math.min(open, close) - Math.random() * volatility
      const volume = Math.random() * 1000000 + 500000

      data.push({
        time,
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume: Math.floor(volume),
      })

      basePrice = close
    }

    return data
  }

  // Fetch chart data when settings change
  useEffect(() => {
    let cancelled = false

    const fetchChartData = async () => {
      setIsLoading(true)
      setError(null)

      try {
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 800))

        if (cancelled) return

        // In production, fetch from Supabase:
        // const { data, error } = await supabase
        //   .from('market_data')
        //   .select('*')
        //   .eq('symbol', settings.symbol)
        //   .eq('timeframe', settings.timeframe)
        //   .order('time', { ascending: true })
        //   .limit(500)

        const data = generateSampleData(settings.symbol, settings.timeframe)
        if (!cancelled) {
          setChartData(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load chart data')
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    fetchChartData()

    return () => {
      cancelled = true
    }
  }, [settings.symbol, settings.timeframe])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Charts</h1>
        <p className="text-muted-foreground mt-1">
          Analyze market trends with advanced charting tools
        </p>
      </div>

      {/* Chart Controls */}
      <ChartControls settings={settings} onSettingsChange={setSettings} />

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Loading chart data for {settings.symbol} ({settings.timeframe})...
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Trading Chart */}
      {!isLoading && !error && chartData.length > 0 && (
        <TradingChart
          symbol={settings.symbol}
          timeframe={settings.timeframe}
          data={chartData}
          showEMA20={settings.showEMA20}
          showEMA50={settings.showEMA50}
          showEMA200={settings.showEMA200}
          height={600}
        />
      )}

      {/* Empty State */}
      {!isLoading && !error && chartData.length === 0 && (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <p className="text-muted-foreground">
                No chart data available for {settings.symbol} ({settings.timeframe})
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Try selecting a different symbol or timeframe
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card>
        <CardContent className="p-4">
          <div className="text-sm text-muted-foreground space-y-2">
            <p className="font-medium text-foreground">Chart Information:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Currently displaying sample data for demonstration purposes</li>
              <li>Production version will fetch real-time data from Supabase database</li>
              <li>EMA indicators are calculated client-side for performance</li>
              <li>RSI and MACD indicators coming soon</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
