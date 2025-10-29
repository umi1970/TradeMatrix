'use client'

import { useEffect, useRef, useState } from 'react'
import {
  createChart,
  ColorType,
  CrosshairMode,
  LineStyle,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  type IChartApi,
  type CandlestickData,
  type HistogramData,
  type LineData,
} from 'lightweight-charts'
import { Card, CardContent } from '@/components/ui/card'

interface OHLCVData {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface TradingChartProps {
  symbol: string
  timeframe: string
  data: OHLCVData[]
  showEMA20?: boolean
  showEMA50?: boolean
  showEMA200?: boolean
  height?: number
}

export function TradingChart({
  symbol,
  timeframe,
  data,
  showEMA20 = true,
  showEMA50 = true,
  showEMA200 = true,
  height = 600,
}: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<any>(null)
  const volumeSeriesRef = useRef<any>(null)
  const ema20SeriesRef = useRef<any>(null)
  const ema50SeriesRef = useRef<any>(null)
  const ema200SeriesRef = useRef<any>(null)

  const [isLoading, setIsLoading] = useState(true)

  // Calculate EMA
  const calculateEMA = (data: OHLCVData[], period: number): LineData[] => {
    const ema: LineData[] = []
    const multiplier = 2 / (period + 1)
    let emaValue = data.slice(0, period).reduce((sum, d) => sum + d.close, 0) / period

    for (let i = period - 1; i < data.length; i++) {
      if (i === period - 1) {
        ema.push({ time: data[i].time as any, value: emaValue })
      } else {
        emaValue = (data[i].close - emaValue) * multiplier + emaValue
        ema.push({ time: data[i].time as any, value: emaValue })
      }
    }

    return ema
  }

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return

    setIsLoading(true)

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#888',
      },
      grid: {
        vertLines: { color: 'rgba(197, 203, 206, 0.1)' },
        horzLines: { color: 'rgba(197, 203, 206, 0.1)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: '#758696',
          width: 1,
          style: LineStyle.Dashed,
        },
        horzLine: {
          color: '#758696',
          width: 1,
          style: LineStyle.Dashed,
        },
      },
      rightPriceScale: {
        borderColor: 'rgba(197, 203, 206, 0.2)',
      },
      timeScale: {
        borderColor: 'rgba(197, 203, 206, 0.2)',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    chartRef.current = chart

    // Add candlestick series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    candlestickSeriesRef.current = candlestickSeries

    // Convert data to candlestick format
    const candlestickData: CandlestickData[] = data.map((d) => ({
      time: d.time as any,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }))

    candlestickSeries.setData(candlestickData)

    // Add volume series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    })

    volumeSeriesRef.current = volumeSeries

    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    // Convert data to volume format
    const volumeData: HistogramData[] = data.map((d) => ({
      time: d.time as any,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)',
    }))

    volumeSeries.setData(volumeData)

    // Add EMA indicators
    if (showEMA20 && data.length >= 20) {
      const ema20Series = chart.addSeries(LineSeries, {
        color: '#3b82f6',
        lineWidth: 1,
        title: 'EMA 20',
      })
      ema20SeriesRef.current = ema20Series
      ema20Series.setData(calculateEMA(data, 20))
    }

    if (showEMA50 && data.length >= 50) {
      const ema50Series = chart.addSeries(LineSeries, {
        color: '#f59e0b',
        lineWidth: 1,
        title: 'EMA 50',
      })
      ema50SeriesRef.current = ema50Series
      ema50Series.setData(calculateEMA(data, 50))
    }

    if (showEMA200 && data.length >= 200) {
      const ema200Series = chart.addSeries(LineSeries, {
        color: '#ef4444',
        lineWidth: 2,
        title: 'EMA 200',
      })
      ema200SeriesRef.current = ema200Series
      ema200Series.setData(calculateEMA(data, 200))
    }

    // Fit content
    chart.timeScale().fitContent()

    setIsLoading(false)

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
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
      }
    }
  }, [data, height, showEMA20, showEMA50, showEMA200])

  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">
            {symbol} - {timeframe}
          </h3>
          <div className="flex gap-2 mt-2 text-xs text-muted-foreground">
            {showEMA20 && <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-blue-500"></span>EMA 20
            </span>}
            {showEMA50 && <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-amber-500"></span>EMA 50
            </span>}
            {showEMA200 && <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-red-500"></span>EMA 200
            </span>}
          </div>
        </div>

        <div className="relative">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
              <div className="text-muted-foreground">Loading chart...</div>
            </div>
          )}
          <div ref={chartContainerRef} className="w-full" />
        </div>

        <div className="mt-4 text-xs text-muted-foreground">
          <p>Use mouse wheel to zoom, drag to pan. Click and drag on price scale to zoom vertically.</p>
        </div>
      </CardContent>
    </Card>
  )
}

export default TradingChart
