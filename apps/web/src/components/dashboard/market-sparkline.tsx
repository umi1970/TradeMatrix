'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'

interface MarketSparklineProps {
  symbol: string
  symbolId?: string
  trend?: 'up' | 'down' | 'neutral'
}

export function MarketSparkline({ symbol, symbolId, trend = 'neutral' }: MarketSparklineProps) {
  const [points, setPoints] = useState<number[]>([])
  const supabase = createBrowserClient()

  useEffect(() => {
    async function loadHistoricalData() {
      if (!symbolId) return

      // Fetch last 20 days of EOD close prices
      const { data, error } = await supabase
        .from('eod_data' as any)
        .select('close')
        .eq('symbol_id', symbolId)
        .order('trade_date', { ascending: false })
        .limit(20)

      if (!error && data && data.length > 0) {
        // Reverse to get chronological order
        const closePrices = data.reverse().map((d: any) => parseFloat(d.close))
        setPoints(closePrices)
      }
    }

    loadHistoricalData()
  }, [symbolId, supabase])

  // Loading state
  if (points.length === 0) {
    return <div className="w-20 h-10" />
  }

  // Calculate SVG path
  const width = 80
  const height = 40
  const padding = 2

  const max = Math.max(...points)
  const min = Math.min(...points)
  const range = max - min || 1

  const pathPoints = points.map((value, index) => {
    const x = padding + (index / (points.length - 1)) * (width - 2 * padding)
    const y = padding + ((max - value) / range) * (height - 2 * padding)
    return `${x},${y}`
  })

  const pathD = `M ${pathPoints.join(' L ')}`

  // Determine color based on trend (first vs last price)
  const priceChange = points[points.length - 1] - points[0]
  const strokeColor = priceChange > 0 ? '#22c55e' : priceChange < 0 ? '#ef4444' : '#6b7280'

  return (
    <svg
      width={width}
      height={height}
      className="flex-shrink-0"
    >
      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
