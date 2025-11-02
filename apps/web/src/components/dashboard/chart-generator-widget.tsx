'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Loader2, ExternalLink, Copy, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { TimeframeSelector } from './timeframe-selector'
import { useChartGeneration } from '@/hooks/useChartGeneration'
import { useLatestSnapshot } from '@/hooks/useChartSnapshots'
import { useToast } from '@/hooks/use-toast'
import type { MarketSymbol } from '@/types/chart'

interface ChartGeneratorWidgetProps {
  symbol: MarketSymbol
}

export function ChartGeneratorWidget({ symbol }: ChartGeneratorWidgetProps) {
  const { toast } = useToast()
  const { generate, isGenerating, data, error } = useChartGeneration()
  const [selectedTimeframe, setSelectedTimeframe] = useState(
    symbol.chart_config?.default_timeframe || '1h'
  )

  // Get latest snapshot for selected timeframe
  const latestSnapshot = useLatestSnapshot(symbol.id, selectedTimeframe)

  const chartUrl = data?.chart_url || latestSnapshot?.chart_url

  const handleGenerate = () => {
    generate({
      symbol_id: symbol.id,
      timeframe: selectedTimeframe,
    })
  }

  const handleCopyUrl = () => {
    if (chartUrl) {
      navigator.clipboard.writeText(chartUrl)
      toast({
        title: 'Copied',
        description: 'Chart URL copied to clipboard',
      })
    }
  }

  const handleOpenInNewTab = () => {
    if (chartUrl) {
      window.open(chartUrl, '_blank')
    }
  }

  if (!symbol.chart_enabled) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Chart Generator</CardTitle>
          <CardDescription>
            {symbol.name} ({symbol.symbol})
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertDescription>
              Chart generation is not enabled for this symbol. Please configure it in the settings.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  const availableTimeframes = symbol.chart_config?.timeframes || []

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Chart Generator</CardTitle>
            <CardDescription>
              {symbol.name} ({symbol.symbol})
            </CardDescription>
          </div>
          {chartUrl && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyUrl}
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy URL
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleOpenInNewTab}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Open
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Timeframe Selector */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Select Timeframe</label>
          <TimeframeSelector
            value={selectedTimeframe}
            onChange={setSelectedTimeframe}
            availableTimeframes={availableTimeframes}
          />
        </div>

        {/* Generate Button */}
        <Button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="w-full"
        >
          {isGenerating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating Chart...
            </>
          ) : (
            <>
              <RefreshCw className="mr-2 h-4 w-4" />
              Generate Chart
            </>
          )}
        </Button>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>
              {error.message || 'Failed to generate chart'}
            </AlertDescription>
          </Alert>
        )}

        {/* Chart Display */}
        {chartUrl && (
          <div className="space-y-2">
            <div className="relative aspect-video w-full overflow-hidden rounded-lg border bg-muted">
              <Image
                src={chartUrl}
                alt={`${symbol.symbol} ${selectedTimeframe} Chart`}
                fill
                className="object-contain"
                unoptimized
              />
            </div>

            {/* Chart Info */}
            {latestSnapshot && (
              <div className="text-xs text-muted-foreground space-y-1">
                <p>Generated: {new Date(latestSnapshot.generated_at).toLocaleString()}</p>
                <p>Expires: {new Date(latestSnapshot.expires_at).toLocaleString()}</p>
                <p className="capitalize">Trigger: {latestSnapshot.trigger_type}</p>
              </div>
            )}
          </div>
        )}

        {/* Placeholder when no chart */}
        {!chartUrl && !isGenerating && (
          <div className="flex items-center justify-center aspect-video w-full rounded-lg border border-dashed bg-muted/50">
            <div className="text-center text-muted-foreground">
              <p className="text-sm font-medium">No chart available</p>
              <p className="text-xs mt-1">Click Generate Chart to create one</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
