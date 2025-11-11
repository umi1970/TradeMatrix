'use client'

import { useState, useEffect } from 'react'
import { TradingChart } from '@/components/dashboard/trading-chart'
import { ChartControls, type ChartSettings } from '@/components/dashboard/chart-controls'
import { CSVUploadZone } from '@/components/dashboard/csv-upload-zone'
import { AnalysesTable } from '@/components/dashboard/analyses-table'
import { CSVChartViewer } from '@/components/dashboard/csv-chart-viewer'
import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Loader2, Upload, LineChart } from 'lucide-react'

interface OHLCVData {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface CSVChartData {
  symbol: string
  timeframe: string
  current_price: number
  trend: string
  confidence_score: number
  csv_data?: Array<{
    time: string
    open: number
    high: number
    low: number
    close: number
    volume?: number
  }>
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
  const [csvChartData, setCSVChartData] = useState<CSVChartData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Handle CSV upload complete
  const handleCSVAnalysisComplete = (analysis: any) => {
    if (analysis.ohlcv_data) {
      setCSVChartData({
        symbol: analysis.symbol,
        timeframe: analysis.timeframe,
        current_price: analysis.current_price,
        trend: analysis.trend,
        confidence_score: analysis.confidence_score,
        csv_data: analysis.ohlcv_data,
      })
    }
  }

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
        // Fetch real data from API
        const response = await fetch(
          `/api/market-data/${settings.symbol}/history?interval=${settings.timeframe}&limit=500`
        )

        if (!response.ok) {
          throw new Error(`Failed to fetch chart data: ${response.statusText}`)
        }

        const result = await response.json()

        if (cancelled) return

        // Check if we have data
        if (result.data && result.data.length > 0) {
          setChartData(result.data)
        } else {
          // Fallback to sample data if no real data available
          console.warn('No real data available, using sample data')
          const sampleData = generateSampleData(settings.symbol, settings.timeframe)
          setChartData(sampleData)
        }

      } catch (err) {
        if (!cancelled) {
          console.error('Error fetching chart data:', err)
          setError(err instanceof Error ? err.message : 'Failed to load chart data')

          // Fallback to sample data on error
          const sampleData = generateSampleData(settings.symbol, settings.timeframe)
          setChartData(sampleData)
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

      {/* Tabs: CSV Upload vs Live Charts */}
      <Tabs defaultValue="csv-upload" className="space-y-4">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="csv-upload" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            CSV Upload
          </TabsTrigger>
          <TabsTrigger value="live-charts" className="flex items-center gap-2">
            <LineChart className="h-4 w-4" />
            Live Charts
          </TabsTrigger>
        </TabsList>

        {/* CSV Upload Tab */}
        <TabsContent value="csv-upload" className="space-y-4">
          <CSVUploadZone onAnalysisComplete={handleCSVAnalysisComplete} />
          <AnalysesTable />
        </TabsContent>

        {/* Live Charts Tab */}
        <TabsContent value="live-charts" className="space-y-4">
          {/* CSV Chart */}
          <CSVChartViewer data={csvChartData} />

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
                  <li>Fetching real-time data from Twelve Data API via Supabase</li>
                  <li>Data is updated every minute by background workers</li>
                  <li>EMA indicators are calculated client-side for performance</li>
                  <li>Falls back to sample data if real data is not available</li>
                  <li>
                    {chartData.length > 0 && (
                      <span className="font-medium text-foreground">
                        Current: {chartData.length} candles loaded
                      </span>
                    )}
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
