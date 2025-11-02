'use client'

import { useEffect, useRef, useState } from 'react'

interface MarketSparklineProps {
  symbol: string
  data?: Array<{ time: string; value: number }>
  trend?: 'up' | 'down' | 'neutral'
}

export function MarketSparkline({ symbol, data = [], trend = 'neutral' }: MarketSparklineProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<any>(null)
  const seriesRef = useRef<any>(null)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  useEffect(() => {
    if (!chartContainerRef.current || !isMounted) return

    // Dynamic import to avoid SSR issues
    import('lightweight-charts').then(({ createChart, ColorType }) => {
      if (!chartContainerRef.current) return

      const lineColor = trend === 'up' ? '#22c55e' : trend === 'down' ? '#ef4444' : '#6b7280'

      // Create chart
      const chart = createChart(chartContainerRef.current, {
        width: 80,
        height: 40,
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#6b7280',
        },
        grid: {
          vertLines: { visible: false },
          horzLines: { visible: false },
        },
        leftPriceScale: { visible: false },
        rightPriceScale: { visible: false },
        timeScale: { visible: false },
        handleScroll: false,
        handleScale: false,
        crosshair: { horzLine: { visible: false }, vertLine: { visible: false } },
      })

      chartRef.current = chart

      // Add line series
      const lineSeries = chart.addLineSeries({
        color: lineColor,
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      })

      seriesRef.current = lineSeries

      // If we have data, set it
      if (data && data.length > 0) {
        const chartData = data.map((item) => ({
          time: item.time,
          value: item.value,
        }))
        lineSeries.setData(chartData)
        chart.timeScale().fitContent()
      } else {
        // Generate dummy flat line if no data
        const now = Date.now() / 1000
        const dummyData = Array.from({ length: 10 }, (_, i) => ({
          time: (now - (10 - i) * 3600) as any,
          value: 100 + Math.random() * 2,
        }))
        lineSeries.setData(dummyData)
        chart.timeScale().fitContent()
      }
    }).catch(err => {
      console.error('Error loading chart:', err)
    })

    // Cleanup
    return () => {
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
        seriesRef.current = null
      }
    }
  }, [data, trend, isMounted])

  return (
    <div
      ref={chartContainerRef}
      className="flex-shrink-0"
      style={{ width: '80px', height: '40px' }}
    />
  )
}
