'use client'

import { useState } from 'react'
import { Check, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Badge } from '@/components/ui/badge'
import { INDICATORS, type IndicatorValue } from '@/types/chart'

interface IndicatorMultiSelectProps {
  value: string[]
  onChange: (value: string[]) => void
  className?: string
  maxIndicators?: number
}

export function IndicatorMultiSelect({
  value,
  onChange,
  className,
  maxIndicators = 10,
}: IndicatorMultiSelectProps) {
  const [open, setOpen] = useState(false)

  const groupedIndicators = INDICATORS.reduce((acc, indicator) => {
    if (!acc[indicator.group]) {
      acc[indicator.group] = []
    }
    acc[indicator.group].push(indicator)
    return acc
  }, {} as Record<string, typeof INDICATORS[number][]>)

  const toggleIndicator = (indicatorValue: string) => {
    if (value.includes(indicatorValue)) {
      onChange(value.filter(v => v !== indicatorValue))
    } else {
      if (value.length >= maxIndicators) {
        return // Don't add more than max
      }
      onChange([...value, indicatorValue])
    }
  }

  const selectAll = () => {
    const allValues = INDICATORS.map(i => i.value).slice(0, maxIndicators)
    onChange(allValues)
  }

  const deselectAll = () => {
    onChange([])
  }

  return (
    <div className={cn('space-y-2', className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between"
          >
            <span className="truncate">
              {value.length === 0
                ? 'Select indicators...'
                : `${value.length} indicator${value.length === 1 ? '' : 's'} selected`}
            </span>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[300px] p-0">
          <Command>
            <CommandInput placeholder="Search indicators..." />
            <CommandEmpty>No indicator found.</CommandEmpty>

            <div className="p-2 border-b flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={selectAll}
                className="flex-1"
              >
                Select All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={deselectAll}
                className="flex-1"
              >
                Clear
              </Button>
            </div>

            {Object.entries(groupedIndicators).map(([group, indicators]) => (
              <CommandGroup key={group} heading={group}>
                {indicators.map((indicator) => {
                  const isSelected = value.includes(indicator.value)
                  const isDisabled = !isSelected && value.length >= maxIndicators

                  return (
                    <CommandItem
                      key={indicator.value}
                      onSelect={() => {
                        if (!isDisabled) {
                          toggleIndicator(indicator.value)
                        }
                      }}
                      disabled={isDisabled}
                    >
                      <div
                        className={cn(
                          'mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary',
                          isSelected
                            ? 'bg-primary text-primary-foreground'
                            : 'opacity-50 [&_svg]:invisible'
                        )}
                      >
                        <Check className={cn('h-4 w-4')} />
                      </div>
                      <span className={cn(isDisabled && 'opacity-50')}>
                        {indicator.label}
                      </span>
                    </CommandItem>
                  )
                })}
              </CommandGroup>
            ))}
          </Command>
        </PopoverContent>
      </Popover>

      {/* Selected indicators display */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {value.map((indicatorValue) => {
            const indicator = INDICATORS.find(i => i.value === indicatorValue)
            return (
              <Badge
                key={indicatorValue}
                variant="secondary"
                className="cursor-pointer hover:bg-secondary/80"
                onClick={() => toggleIndicator(indicatorValue)}
              >
                {indicator?.label || indicatorValue}
                <span className="ml-1 text-xs">×</span>
              </Badge>
            )
          })}
        </div>
      )}

      {value.length >= maxIndicators && (
        <p className="text-xs text-muted-foreground">
          Maximum {maxIndicators} indicators reached
        </p>
      )}
    </div>
  )
}
