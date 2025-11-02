'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

interface EODLevel {
  id: string
  trade_date: string
  yesterday_high: number
  yesterday_low: number
  yesterday_close: number
  yesterday_range: number
  atr_5d: number | null
  atr_20d: number | null
  daily_change_points: number
  daily_change_percent: number
  symbols: {
    symbol: string
    name: string
  }
}

interface DatabaseStats {
  eod_data_count: number
  eod_levels_count: number
  symbols_count: number
  date_range: {
    first: string | null
    last: string | null
  }
}

interface Symbol {
  id: string
  symbol: string
  name: string
}

export default function EODPage() {
  const [levels, setLevels] = useState<EODLevel[]>([])
  const [stats, setStats] = useState<DatabaseStats | null>(null)
  const [symbols, setSymbols] = useState<Symbol[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter states
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')

  // Pagination state
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const PAGE_SIZE = 50

  // Fetch symbols on mount
  useEffect(() => {
    async function fetchSymbols() {
      try {
        const supabase = createBrowserClient()
        const { data } = await supabase
          .from('symbols' as any)
          .select('id, symbol, name')
          .eq('is_active', true)
          .order('symbol')

        setSymbols((data as any) || [])
      } catch (err) {
        console.error('Error fetching symbols:', err)
      }
    }
    fetchSymbols()
  }, [])

  // Fetch data when filters change
  useEffect(() => {
    // Reset page when filters change
    setPage(0)
    setLevels([])
    setHasMore(true)
  }, [selectedSymbol, startDate, endDate])

  // Fetch data when page changes
  useEffect(() => {
    async function fetchData() {
      try {
        if (page === 0) {
          setLoading(true)
        } else {
          setLoadingMore(true)
        }

        const supabase = createBrowserClient()

        // Build query with filters
        let query = supabase
          .from('eod_levels' as any)
          .select('*, symbols(symbol, name)', { count: 'exact' })

        // Apply symbol filter
        if (selectedSymbol !== 'all') {
          query = query.eq('symbol_id', selectedSymbol)
        }

        // Apply date range filters
        if (startDate) {
          query = query.gte('trade_date', startDate)
        }
        if (endDate) {
          query = query.lte('trade_date', endDate)
        }

        // Pagination with range
        const from = page * PAGE_SIZE
        const to = from + PAGE_SIZE - 1

        const { data: levelsData, error: levelsError, count } = await query
          .order('trade_date', { ascending: false })
          .range(from, to)

        if (levelsError) throw levelsError

        // Append or replace data
        if (page === 0) {
          setLevels((levelsData as any) || [])
        } else {
          setLevels(prev => [...prev, ...((levelsData as any) || [])])
        }

        // Check if there's more data
        setHasMore((levelsData?.length || 0) === PAGE_SIZE)

        // Fetch stats only on first load
        if (page === 0) {
          // Fetch database stats
          const [eodDataCount, eodLevelsCount, symbolsCount] = await Promise.all([
            supabase.from('eod_data' as any).select('id', { count: 'exact', head: true }),
            supabase.from('eod_levels' as any).select('id', { count: 'exact', head: true }),
            supabase.from('symbols' as any).select('id', { count: 'exact', head: true })
          ])

          // Get date range
          const { data: dateRangeData } = await supabase
            .from('eod_data' as any)
            .select('trade_date')
            .order('trade_date', { ascending: true })
            .limit(1)
            .single()

          const { data: latestDateData } = await supabase
            .from('eod_data' as any)
            .select('trade_date')
            .order('trade_date', { ascending: false })
            .limit(1)
            .single()

          setStats({
            eod_data_count: eodDataCount.count || 0,
            eod_levels_count: eodLevelsCount.count || 0,
            symbols_count: symbolsCount.count || 0,
            date_range: {
              first: (dateRangeData as any)?.trade_date || null,
              last: (latestDateData as any)?.trade_date || null
            }
          })
        }

      } catch (err) {
        console.error('Error fetching EOD data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
        setLoadingMore(false)
      }
    }

    fetchData()
  }, [page, selectedSymbol, startDate, endDate])

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      setPage(prev => prev + 1)
    }
  }

  const formatNumber = (value: number | null | undefined, symbol?: string): string => {
    if (value === null || value === undefined) return '-'
    // Forex pairs need 4-5 decimal places, indices need 2
    const isForex = symbol && (symbol.includes('USD') || symbol.includes('EUR') || symbol.includes('GBP'))
    const decimals = isForex ? 5 : 2
    return value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading EOD data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">EOD Historical Data</h1>
        <p className="text-muted-foreground mt-2">
          View historical end-of-day market data and calculated levels
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
          <CardDescription>Filter EOD data by symbol and date range</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Symbol Filter */}
            <div className="space-y-2">
              <Label htmlFor="symbol-filter">Symbol</Label>
              <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                <SelectTrigger id="symbol-filter">
                  <SelectValue placeholder="All Symbols" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Symbols</SelectItem>
                  {symbols.map((symbol) => (
                    <SelectItem key={symbol.id} value={symbol.id}>
                      {symbol.symbol} - {symbol.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Start Date Filter */}
            <div className="space-y-2">
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>

            {/* End Date Filter */}
            <div className="space-y-2">
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          {/* Clear Filters Button */}
          {(selectedSymbol !== 'all' || startDate || endDate) && (
            <div className="mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedSymbol('all')
                  setStartDate('')
                  setEndDate('')
                }}
              >
                Clear Filters
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Database Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total EOD Records</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {stats.eod_data_count.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Historical data points
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Calculated Levels</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {stats.eod_levels_count.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Yesterday levels + ATR
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Active Symbols</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.symbols_count}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Markets tracked
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Date Range</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm font-semibold">
                {stats.date_range.first || 'N/A'}
              </div>
              <div className="text-sm font-semibold">
                to {stats.date_range.last || 'N/A'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats.date_range.first && stats.date_range.last
                  ? `${Math.floor(
                      (new Date(stats.date_range.last).getTime() -
                        new Date(stats.date_range.first).getTime()) /
                        (1000 * 60 * 60 * 24 * 365)
                    )} years`
                  : 'N/A'}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Latest EOD Levels */}
      <Card>
        <CardHeader>
          <CardTitle>
            EOD Levels {levels.length > 0 && `(${levels.length} records)`}
          </CardTitle>
          <CardDescription>
            Yesterday&apos;s High/Low/Close and calculated indicators
          </CardDescription>
        </CardHeader>
        <CardContent>
          {levels.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p className="text-lg font-semibold mb-2">No levels data yet</p>
              <p className="text-sm">
                Levels are being calculated in the background.
                <br />
                Check back in a few minutes.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-2">Date</th>
                    <th className="text-left py-3 px-2">Symbol</th>
                    <th className="text-right py-3 px-2">Y-High</th>
                    <th className="text-right py-3 px-2">Y-Low</th>
                    <th className="text-right py-3 px-2">Y-Close</th>
                    <th className="text-right py-3 px-2">Range</th>
                    <th className="text-right py-3 px-2">ATR 5d</th>
                    <th className="text-right py-3 px-2">ATR 20d</th>
                    <th className="text-right py-3 px-2">Change</th>
                  </tr>
                </thead>
                <tbody>
                  {levels.map((level) => (
                    <tr key={level.id} className="border-b border-border hover:bg-muted transition-colors">
                      <td className="py-3 px-2 font-mono text-xs">
                        {level.trade_date}
                      </td>
                      <td className="py-3 px-2">
                        <div>
                          <div className="font-semibold">
                            {level.symbols?.symbol}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {level.symbols?.name}
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-2 text-right font-mono">
                        {formatNumber(level.yesterday_high, level.symbols?.symbol)}
                      </td>
                      <td className="py-3 px-2 text-right font-mono">
                        {formatNumber(level.yesterday_low, level.symbols?.symbol)}
                      </td>
                      <td className="py-3 px-2 text-right font-mono">
                        {formatNumber(level.yesterday_close, level.symbols?.symbol)}
                      </td>
                      <td className="py-3 px-2 text-right font-mono text-xs">
                        {formatNumber(level.yesterday_range, level.symbols?.symbol)}
                      </td>
                      <td className="py-3 px-2 text-right font-mono text-xs text-muted-foreground">
                        {formatNumber(level.atr_5d, level.symbols?.symbol)}
                      </td>
                      <td className="py-3 px-2 text-right font-mono text-xs text-muted-foreground">
                        {formatNumber(level.atr_20d, level.symbols?.symbol)}
                      </td>
                      <td className="py-3 px-2 text-right">
                        <Badge
                          variant={
                            level.daily_change_percent >= 0
                              ? 'default'
                              : 'destructive'
                          }
                        >
                          {level.daily_change_percent >= 0 ? '+' : ''}
                          {level.daily_change_percent.toFixed(2)}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Load More Button */}
          {levels.length > 0 && hasMore && (
            <div className="mt-6 text-center">
              <Button
                onClick={loadMore}
                disabled={loadingMore}
                variant="outline"
              >
                {loadingMore ? 'Loading...' : `Load More (${levels.length} of many)`}
              </Button>
            </div>
          )}

          {/* End of results message */}
          {levels.length > 0 && !hasMore && (
            <div className="mt-6 text-center text-sm text-muted-foreground">
              End of results - showing {levels.length} records
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
