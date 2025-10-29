'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export interface ChartSettings {
  symbol: string
  timeframe: string
  showEMA20: boolean
  showEMA50: boolean
  showEMA200: boolean
  showRSI: boolean
  showMACD: boolean
}

interface ChartControlsProps {
  settings: ChartSettings
  onSettingsChange: (settings: ChartSettings) => void
}

const SYMBOLS = [
  { value: 'DAX', label: 'DAX 40', description: 'Germany 40' },
  { value: 'NASDAQ', label: 'NASDAQ 100', description: 'US Tech 100' },
  { value: 'DJI', label: 'Dow Jones', description: 'US 30' },
  { value: 'EURUSD', label: 'EUR/USD', description: 'Euro vs US Dollar' },
  { value: 'GBPUSD', label: 'GBP/USD', description: 'Pound vs US Dollar' },
  { value: 'USDJPY', label: 'USD/JPY', description: 'US Dollar vs Yen' },
]

const TIMEFRAMES = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '1w', label: '1 Week' },
]

export function ChartControls({ settings, onSettingsChange }: ChartControlsProps) {
  const handleSymbolChange = (value: string) => {
    onSettingsChange({ ...settings, symbol: value })
  }

  const handleTimeframeChange = (value: string) => {
    onSettingsChange({ ...settings, timeframe: value })
  }

  const toggleIndicator = (indicator: keyof ChartSettings) => {
    onSettingsChange({ ...settings, [indicator]: !settings[indicator] })
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {/* Symbol Selector */}
          <div className="space-y-2">
            <Label htmlFor="symbol">Symbol</Label>
            <Select value={settings.symbol} onValueChange={handleSymbolChange}>
              <SelectTrigger id="symbol">
                <SelectValue placeholder="Select symbol" />
              </SelectTrigger>
              <SelectContent>
                {SYMBOLS.map((symbol) => (
                  <SelectItem key={symbol.value} value={symbol.value}>
                    <div>
                      <div className="font-medium">{symbol.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {symbol.description}
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Timeframe Selector */}
          <div className="space-y-2">
            <Label htmlFor="timeframe">Timeframe</Label>
            <Select value={settings.timeframe} onValueChange={handleTimeframeChange}>
              <SelectTrigger id="timeframe">
                <SelectValue placeholder="Select timeframe" />
              </SelectTrigger>
              <SelectContent>
                {TIMEFRAMES.map((timeframe) => (
                  <SelectItem key={timeframe.value} value={timeframe.value}>
                    {timeframe.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* EMA Indicators */}
          <div className="space-y-2">
            <Label>Moving Averages</Label>
            <div className="flex flex-wrap gap-2">
              <Badge
                variant={settings.showEMA20 ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleIndicator('showEMA20')}
              >
                EMA 20
              </Badge>
              <Badge
                variant={settings.showEMA50 ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleIndicator('showEMA50')}
              >
                EMA 50
              </Badge>
              <Badge
                variant={settings.showEMA200 ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleIndicator('showEMA200')}
              >
                EMA 200
              </Badge>
            </div>
          </div>

          {/* Other Indicators */}
          <div className="space-y-2">
            <Label>Oscillators</Label>
            <div className="flex flex-wrap gap-2">
              <Badge
                variant={settings.showRSI ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleIndicator('showRSI')}
              >
                RSI
              </Badge>
              <Badge
                variant={settings.showMACD ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => toggleIndicator('showMACD')}
              >
                MACD
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              (Coming soon)
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 mt-4 pt-4 border-t">
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              onSettingsChange({
                ...settings,
                showEMA20: true,
                showEMA50: true,
                showEMA200: true,
              })
            }
          >
            Show All EMAs
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              onSettingsChange({
                ...settings,
                showEMA20: false,
                showEMA50: false,
                showEMA200: false,
              })
            }
          >
            Hide All EMAs
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default ChartControls
