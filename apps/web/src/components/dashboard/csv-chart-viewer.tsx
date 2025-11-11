'use client'

import { useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { createChart, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts'

interface CSVChartData {
  symbol: string
  timeframe: string
  current_price: number
  trend: string
  confidence_score: number
  // Raw CSV data (array of OHLCV bars)
  csv_data?: Array<{
    time: string
    open: number
    high: number
    low: number
    close: number
    volume?: number
  }>
}

interface CSVChartViewerProps {
  data: CSVChartData | null
}

export function CSVChartViewer({ data }: CSVChartViewerProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current || !data?.csv_data) return

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2a2a2a',
      },
      timeScale: {
        borderColor: '#2a2a2a',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    chartRef.current = chart

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    candleSeriesRef.current = candleSeries

    // Convert CSV data to chart format
    const chartData: CandlestickData[] = data.csv_data.map((bar) => ({
      time: Math.floor(new Date(bar.time).getTime() / 1000) as any,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }))

    // Sort by time
    chartData.sort((a, b) => (a.time as number) - (b.time as number))

    candleSeries.setData(chartData)

    // Fit content
    chart.timeScale().fitContent()

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data])

  if (!data) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center text-muted-foreground">
            <p>No CSV data to display</p>
            <p className="text-sm mt-2">Upload a CSV on the CSV Upload tab to see the chart</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {data.symbol}
              <Badge variant="outline">{data.timeframe}</Badge>
            </CardTitle>
            <CardDescription>
              Current: ${data.current_price.toFixed(2)} •{' '}
              Trend:{' '}
              <span
                className={
                  data.trend === 'bullish'
                    ? 'text-green-500'
                    : data.trend === 'bearish'
                    ? 'text-red-500'
                    : 'text-gray-500'
                }
              >
                {data.trend.toUpperCase()}
              </span>{' '}
              • Confidence: {(data.confidence_score * 100).toFixed(0)}%
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div ref={chartContainerRef} className="w-full" />
      </CardContent>
    </Card>
  )
}
