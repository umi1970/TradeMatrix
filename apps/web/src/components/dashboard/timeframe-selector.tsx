'use client'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { TIMEFRAMES, type TimeframeValue } from '@/types/chart'

interface TimeframeSelectorProps {
  value: string
  onChange: (value: string) => void
  availableTimeframes?: string[]
  className?: string
}

export function TimeframeSelector({
  value,
  onChange,
  availableTimeframes,
  className,
}: TimeframeSelectorProps) {
  const timeframes = availableTimeframes
    ? TIMEFRAMES.filter(tf => availableTimeframes.includes(tf.value))
    : TIMEFRAMES

  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {timeframes.map((timeframe) => (
        <Button
          key={timeframe.value}
          variant={value === timeframe.value ? 'default' : 'outline'}
          size="sm"
          onClick={() => onChange(timeframe.value)}
          className={cn(
            'transition-all',
            value === timeframe.value && 'ring-2 ring-primary ring-offset-2'
          )}
        >
          {timeframe.label}
        </Button>
      ))}
    </div>
  )
}
