'use client'

import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

const TIMEFRAMES = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes (M15)' },
  { value: '1h', label: '1 Hour (H1)' },
  { value: '4h', label: '4 Hours (H4)' },
  { value: '1d', label: '1 Day (D1)' },
  { value: '1W', label: '1 Week' },
  { value: '1M', label: '1 Month' },
]

interface TimeframeSelectorProps {
  selected: string[]
  onChange: (timeframes: string[]) => void
}

export function TimeframeSelector({ selected, onChange }: TimeframeSelectorProps) {
  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((tf) => tf !== value))
    } else {
      onChange([...selected, value])
    }
  }

  return (
    <div className="space-y-2">
      <Label>Timeframes</Label>
      <p className="text-sm text-muted-foreground">
        Select timeframes for chart generation
      </p>
      <div className="grid grid-cols-2 gap-3">
        {TIMEFRAMES.map((tf) => (
          <div key={tf.value} className="flex items-center space-x-2">
            <Checkbox
              id={`tf-${tf.value}`}
              checked={selected.includes(tf.value)}
              onCheckedChange={() => handleToggle(tf.value)}
            />
            <label
              htmlFor={`tf-${tf.value}`}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
            >
              {tf.label}
            </label>
          </div>
        ))}
      </div>
      {selected.length === 0 && (
        <p className="text-xs text-destructive">
          Please select at least one timeframe
        </p>
      )}
    </div>
  )
}
