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
import { Checkbox } from '@/components/ui/checkbox'
import { IndicatorMultiSelect } from './indicator-multi-select'
import { useUpdateSymbolConfig } from '@/hooks/useMarketSymbols'
import type { MarketSymbol, ChartConfig } from '@/types/chart'
import { TIMEFRAMES, CHART_THEMES } from '@/types/chart'

interface SymbolEditModalProps {
  symbol: MarketSymbol | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SymbolEditModal({
  symbol,
  open,
  onOpenChange,
}: SymbolEditModalProps) {
  const updateConfig = useUpdateSymbolConfig()

  // Form state
  const [tradingViewSymbol, setTradingViewSymbol] = useState('')
  const [chartEnabled, setChartEnabled] = useState(false)
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>([])
  const [defaultTimeframe, setDefaultTimeframe] = useState('')
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>([])
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')

  // Initialize form with symbol data
  useEffect(() => {
    if (symbol) {
      setTradingViewSymbol(symbol.chart_img_symbol || '')
      setChartEnabled(symbol.chart_enabled)

      if (symbol.chart_config) {
        setSelectedTimeframes(symbol.chart_config.timeframes || [])
        setDefaultTimeframe(symbol.chart_config.default_timeframe || '')
        setSelectedIndicators(symbol.chart_config.indicators || [])
        setTheme(symbol.chart_config.theme || 'dark')
      } else {
        // Set defaults
        setSelectedTimeframes(['1h', '4h', '1d'])
        setDefaultTimeframe('1h')
        setSelectedIndicators(['EMA_20', 'EMA_50', 'RSI', 'Volume'])
        setTheme('dark')
      }
    }
  }, [symbol])

  const handleSave = async () => {
    if (!symbol) return

    // Validation
    if (chartEnabled && !tradingViewSymbol) {
      alert('Please enter a TradingView symbol')
      return
    }

    if (chartEnabled && selectedTimeframes.length === 0) {
      alert('Please select at least one timeframe')
      return
    }

    if (chartEnabled && !defaultTimeframe) {
      alert('Please select a default timeframe')
      return
    }

    if (chartEnabled && !selectedTimeframes.includes(defaultTimeframe)) {
      alert('Default timeframe must be one of the selected timeframes')
      return
    }

    const chartConfig: ChartConfig = {
      timeframes: selectedTimeframes,
      indicators: selectedIndicators,
      default_timeframe: defaultTimeframe,
      theme,
    }

    await updateConfig.mutateAsync({
      symbolId: symbol.id,
      chart_img_symbol: tradingViewSymbol,
      chart_enabled: chartEnabled,
      chart_config: chartConfig,
    })

    onOpenChange(false)
  }

  const toggleTimeframe = (timeframe: string) => {
    if (selectedTimeframes.includes(timeframe)) {
      setSelectedTimeframes(selectedTimeframes.filter(tf => tf !== timeframe))
      // If removing default timeframe, clear it
      if (timeframe === defaultTimeframe) {
        setDefaultTimeframe('')
      }
    } else {
      setSelectedTimeframes([...selectedTimeframes, timeframe])
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Edit Chart Settings: {symbol?.symbol}
          </DialogTitle>
          <DialogDescription>
            Configure chart generation settings for {symbol?.alias || symbol?.symbol}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* TradingView Symbol */}
          <div className="space-y-2">
            <Label htmlFor="tv-symbol">TradingView Symbol</Label>
            <Input
              id="tv-symbol"
              placeholder="e.g., XETR:DAX or CAPITALCOM:DAX"
              value={tradingViewSymbol}
              onChange={(e) => setTradingViewSymbol(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Format: EXCHANGE:SYMBOL (e.g., XETR:DAX for DAX on Xetra)
            </p>
          </div>

          {/* Chart Enabled Toggle */}
          <div className="flex items-center space-x-2">
            <Switch
              id="chart-enabled"
              checked={chartEnabled}
              onCheckedChange={setChartEnabled}
            />
            <Label htmlFor="chart-enabled">
              Enable chart generation for this symbol
            </Label>
          </div>

          {chartEnabled && (
            <>
              {/* Timeframes */}
              <div className="space-y-2">
                <Label>Available Timeframes</Label>
                <div className="grid grid-cols-3 gap-2">
                  {TIMEFRAMES.map((tf) => (
                    <div key={tf.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={`tf-${tf.value}`}
                        checked={selectedTimeframes.includes(tf.value)}
                        onCheckedChange={() => toggleTimeframe(tf.value)}
                      />
                      <label
                        htmlFor={`tf-${tf.value}`}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        {tf.label}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Default Timeframe */}
              <div className="space-y-2">
                <Label htmlFor="default-tf">Default Timeframe</Label>
                <Select
                  value={defaultTimeframe}
                  onValueChange={setDefaultTimeframe}
                >
                  <SelectTrigger id="default-tf">
                    <SelectValue placeholder="Select default timeframe" />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedTimeframes.map((tf) => {
                      const timeframe = TIMEFRAMES.find(t => t.value === tf)
                      return (
                        <SelectItem key={tf} value={tf}>
                          {timeframe?.label || tf}
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>

              {/* Indicators */}
              <div className="space-y-2">
                <Label>Technical Indicators</Label>
                <IndicatorMultiSelect
                  value={selectedIndicators}
                  onChange={setSelectedIndicators}
                />
              </div>

              {/* Theme */}
              <div className="space-y-2">
                <Label htmlFor="theme">Chart Theme</Label>
                <Select
                  value={theme}
                  onValueChange={(value: string) => setTheme(value as 'dark' | 'light')}
                >
                  <SelectTrigger id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CHART_THEMES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={updateConfig.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={updateConfig.isPending}
          >
            {updateConfig.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
