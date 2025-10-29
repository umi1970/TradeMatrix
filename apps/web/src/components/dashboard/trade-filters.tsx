'use client'

import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Filter, X } from 'lucide-react'
import type { TradeFilters } from '@/lib/supabase/queries'

interface TradeFiltersProps {
  symbols: string[]
  onFilterChange: (filters: TradeFilters) => void
  initialFilters?: TradeFilters
}

export function TradeFiltersComponent({
  symbols,
  onFilterChange,
  initialFilters = {},
}: TradeFiltersProps) {
  const [filters, setFilters] = useState<TradeFilters>(initialFilters)

  const handleFilterChange = (
    key: keyof TradeFilters,
    value: string | undefined
  ) => {
    const newFilters = { ...filters }

    if (value === 'all' || !value) {
      delete newFilters[key]
    } else {
      newFilters[key] = value as any
    }

    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const clearFilters = () => {
    setFilters({})
    onFilterChange({})
  }

  const hasActiveFilters = Object.keys(filters).length > 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-medium">Filters</h3>
        </div>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="h-8 px-2 lg:px-3"
          >
            Clear
            <X className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {/* Status Filter */}
        <div className="space-y-2">
          <Label htmlFor="status-filter">Status</Label>
          <Select
            value={filters.status || 'all'}
            onValueChange={(value: string) => handleFilterChange('status', value)}
          >
            <SelectTrigger id="status-filter">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Side Filter */}
        <div className="space-y-2">
          <Label htmlFor="side-filter">Side</Label>
          <Select
            value={filters.side || 'all'}
            onValueChange={(value: string) => handleFilterChange('side', value)}
          >
            <SelectTrigger id="side-filter">
              <SelectValue placeholder="All sides" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sides</SelectItem>
              <SelectItem value="long">Long</SelectItem>
              <SelectItem value="short">Short</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Symbol Filter */}
        <div className="space-y-2">
          <Label htmlFor="symbol-filter">Symbol</Label>
          <Select
            value={filters.symbol || 'all'}
            onValueChange={(value: string) => handleFilterChange('symbol', value)}
          >
            <SelectTrigger id="symbol-filter">
              <SelectValue placeholder="All symbols" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All symbols</SelectItem>
              {symbols.map((symbol) => (
                <SelectItem key={symbol} value={symbol}>
                  {symbol}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Start Date Filter */}
        <div className="space-y-2">
          <Label htmlFor="start-date-filter">Start Date</Label>
          <Input
            id="start-date-filter"
            type="date"
            value={filters.startDate || ''}
            onChange={(e) => handleFilterChange('startDate', e.target.value)}
          />
        </div>

        {/* End Date Filter */}
        <div className="space-y-2">
          <Label htmlFor="end-date-filter">End Date</Label>
          <Input
            id="end-date-filter"
            type="date"
            value={filters.endDate || ''}
            onChange={(e) => handleFilterChange('endDate', e.target.value)}
          />
        </div>
      </div>
    </div>
  )
}
