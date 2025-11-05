'use client'

import { useState, useEffect } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { InfoIcon } from 'lucide-react'

interface ChartPreviewConfig {
  tv_symbol: string
  timeframes: string[]
  indicators: string[]
  theme: 'dark' | 'light'
  width: number
  height: number
  show_volume: boolean
  show_legend: boolean
}

interface ChartPreviewProps {
  config: ChartPreviewConfig
}

export function ChartPreview({ config }: ChartPreviewProps) {
  const [chartUrl, setChartUrl] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Build chart-img.com URL
    const buildChartUrl = () => {
      const params = new URLSearchParams({
        symbol: config.tv_symbol,
        interval: config.timeframes[0] || '1h', // Use first timeframe for preview
        theme: config.theme,
        width: config.width.toString(),
        height: config.height.toString(),
        hide_top_toolbar: 'false',
        hide_legend: (!config.show_legend).toString(),
        hide_side_toolbar: 'false',
      })

      if (config.indicators.length > 0) {
        params.append('studies', config.indicators.join(','))
      }

      if (!config.show_volume) {
        params.append('hide_volume', 'true')
      }

      return `https://api.chart-img.com/tradingview/advanced-chart?${params.toString()}`
    }

    const url = buildChartUrl()
    setChartUrl(url)
    setIsLoading(false)
  }, [config])

  if (isLoading) {
    return <Skeleton className="w-full h-[400px]" />
  }

  return (
    <div className="space-y-4">
      <Alert>
        <InfoIcon className="h-4 w-4" />
        <AlertDescription>
          This is a preview using the first selected timeframe ({config.timeframes[0] || 'H1'}).
          All configured timeframes will be available to AI agents.
        </AlertDescription>
      </Alert>

      <div className="border rounded-lg overflow-hidden bg-muted">
        <img
          src={chartUrl}
          alt={`Chart preview for ${config.tv_symbol}`}
          className="w-full h-auto"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              'https://via.placeholder.com/1200x800?text=Chart+Preview+Unavailable'
          }}
        />
      </div>

      <div className="text-xs text-muted-foreground break-all">
        <strong>Generated URL:</strong>
        <br />
        {chartUrl}
      </div>
    </div>
  )
}
