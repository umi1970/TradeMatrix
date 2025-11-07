'use client'

import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { TimeframeSelector } from './TimeframeSelector'
import { IndicatorSelector } from './IndicatorSelector'
import { ChartPreview } from './ChartPreview'
import { createBrowserClient } from '@/lib/supabase/client'
import { useToast } from '@/hooks/use-toast'
import type { ChartConfig } from '@/types/chart'

// TradingView symbol mapping
const SYMBOL_MAPPING: Record<string, string> = {
  '^GDAXI': 'XETR:DAX',
  '^NDX': 'NASDAQ:NDX',
  '^DJI': 'DJCFD:DJI',
  'EURUSD=X': 'OANDA:EURUSD',
  'EURGBP=X': 'OANDA:EURGBP',
  'GBPUSD=X': 'OANDA:GBPUSD',
}

interface ChartConfigModalProps {
  symbol: {
    id: string
    symbol: string
    name: string
    chart_config?: ChartConfig | null
  }
  isOpen: boolean
  onClose: () => void
  onSave?: (config: ChartConfig) => void
}

export function ChartConfigModal({
  symbol,
  isOpen,
  onClose,
  onSave,
}: ChartConfigModalProps) {
  const { toast } = useToast()
  const supabase = createBrowserClient()

  const [config, setConfig] = useState<ChartConfig>({
    timeframes: ['15m', '1h', '1d'],
    indicators: [],
    default_timeframe: '1h',
    theme: 'dark',
  })

  const [tvSymbol, setTvSymbol] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [width, setWidth] = useState(1200)
  const [height, setHeight] = useState(800)
  const [showVolume, setShowVolume] = useState(true)
  const [showLegend, setShowLegend] = useState(true)

  // Initialize form with symbol data
  useEffect(() => {
    if (symbol) {
      setTvSymbol(SYMBOL_MAPPING[symbol.symbol] || symbol.symbol)

      if (symbol.chart_config) {
        setConfig(symbol.chart_config)
      } else {
        // Set defaults
        setConfig({
          timeframes: ['15m', '1h', '1d'],
          indicators: [],
          default_timeframe: '1h',
          theme: 'dark',
        })
      }
    }
  }, [symbol])

  const handleSave = async () => {
    // Validation
    if (config.timeframes.length === 0) {
      toast({
        title: 'Validation Error',
        description: 'Please select at least one timeframe',
        variant: 'destructive',
      })
      return
    }

    if (!config.default_timeframe) {
      toast({
        title: 'Validation Error',
        description: 'Please select a default timeframe',
        variant: 'destructive',
      })
      return
    }

    if (!config.timeframes.includes(config.default_timeframe)) {
      toast({
        title: 'Validation Error',
        description: 'Default timeframe must be one of the selected timeframes',
        variant: 'destructive',
      })
      return
    }

    setIsSaving(true)

    try {
      // Update chart_config in Supabase
      // @ts-ignore - market_symbols not in generated types yet
      const { error } = await supabase
        .from('market_symbols')
        .update({ chart_config: config })
        .eq('id', symbol.id)

      if (error) throw error

      toast({
        title: 'Success',
        description: 'Chart configuration saved successfully',
      })

      onSave?.(config)
      onClose()
    } catch (error) {
      console.error('Error saving chart config:', error)
      toast({
        title: 'Error',
        description: 'Failed to save chart configuration',
        variant: 'destructive',
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Chart Configuration - {symbol.name} ({symbol.symbol})
          </DialogTitle>
          <DialogDescription>
            Configure chart generation settings for this symbol
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="basic" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">Basic</TabsTrigger>
            <TabsTrigger value="indicators">Indicators</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-4">
            {/* TradingView Symbol */}
            <div className="space-y-2">
              <Label htmlFor="tv_symbol">TradingView Symbol</Label>
              <Input
                id="tv_symbol"
                value={tvSymbol}
                onChange={(e) => setTvSymbol(e.target.value)}
                placeholder="XETR:DAX"
              />
              <p className="text-xs text-muted-foreground">
                Format: EXCHANGE:SYMBOL (e.g., XETR:DAX, NASDAQ:NDX)
              </p>
            </div>

            {/* Timeframes */}
            <TimeframeSelector
              selected={config.timeframes}
              onChange={(timeframes) => setConfig({ ...config, timeframes })}
            />

            {/* Default Timeframe */}
            <div className="space-y-2">
              <Label htmlFor="default-tf">Default Timeframe</Label>
              <Select
                value={config.default_timeframe}
                onValueChange={(value) =>
                  setConfig({ ...config, default_timeframe: value })
                }
              >
                <SelectTrigger id="default-tf">
                  <SelectValue placeholder="Select default timeframe" />
                </SelectTrigger>
                <SelectContent>
                  {config.timeframes.map((tf) => (
                    <SelectItem key={tf} value={tf}>
                      {tf.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Theme */}
            <div className="space-y-2">
              <Label htmlFor="theme">Chart Theme</Label>
              <Select
                value={config.theme}
                onValueChange={(value: 'dark' | 'light') =>
                  setConfig({ ...config, theme: value })
                }
              >
                <SelectTrigger id="theme">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="light">Light</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Dimensions */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="width">Width (px)</Label>
                <Input
                  id="width"
                  type="number"
                  value={width}
                  onChange={(e) => setWidth(parseInt(e.target.value))}
                  min={800}
                  max={1920}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="height">Height (px)</Label>
                <Input
                  id="height"
                  type="number"
                  value={height}
                  onChange={(e) => setHeight(parseInt(e.target.value))}
                  min={600}
                  max={1600}
                />
              </div>
            </div>

            {/* Switches */}
            <div className="flex items-center justify-between">
              <Label htmlFor="show_volume">Show Volume</Label>
              <Switch
                id="show_volume"
                checked={showVolume}
                onCheckedChange={setShowVolume}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="show_legend">Show Legend</Label>
              <Switch
                id="show_legend"
                checked={showLegend}
                onCheckedChange={setShowLegend}
              />
            </div>
          </TabsContent>

          <TabsContent value="indicators" className="space-y-4">
            <IndicatorSelector
              selected={config.indicators}
              onChange={(indicators) => setConfig({ ...config, indicators })}
            />
          </TabsContent>

          <TabsContent value="preview" className="space-y-4">
            <ChartPreview
              config={{
                ...config,
                tv_symbol: tvSymbol,
                width,
                height,
                show_volume: showVolume,
                show_legend: showLegend,
              }}
            />
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Configuration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
