'use client'

import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

const INDICATORS = [
  { value: 'RSI@tv-basicstudies', label: 'RSI (Relative Strength Index)' },
  { value: 'MACD@tv-basicstudies', label: 'MACD' },
  { value: 'BB@tv-basicstudies', label: 'Bollinger Bands' },
  { value: 'Stochastic@tv-basicstudies', label: 'Stochastic' },
  { value: 'Volume@tv-basicstudies', label: 'Volume' },
  { value: 'EMA@tv-basicstudies', label: 'EMA (Exponential Moving Average)' },
  { value: 'SMA@tv-basicstudies', label: 'SMA (Simple Moving Average)' },
  { value: 'ATR@tv-basicstudies', label: 'ATR (Average True Range)' },
]

interface IndicatorSelectorProps {
  selected: string[]
  onChange: (indicators: string[]) => void
}

export function IndicatorSelector({ selected, onChange }: IndicatorSelectorProps) {
  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((ind) => ind !== value))
    } else {
      onChange([...selected, value])
    }
  }

  return (
    <div className="space-y-2">
      <Label>Technical Indicators</Label>
      <p className="text-sm text-muted-foreground">
        Select indicators to overlay on your charts
      </p>
      <div className="grid grid-cols-2 gap-3 pt-2">
        {INDICATORS.map((ind) => (
          <div key={ind.value} className="flex items-center space-x-2">
            <Checkbox
              id={`ind-${ind.value}`}
              checked={selected.includes(ind.value)}
              onCheckedChange={() => handleToggle(ind.value)}
            />
            <label
              htmlFor={`ind-${ind.value}`}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
            >
              {ind.label}
            </label>
          </div>
        ))}
      </div>
    </div>
  )
}
