'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Loader2, TrendingUp } from 'lucide-react'

interface EODLevel {
  id: string
  symbol_id: string
  symbol: string
  name: string
  yesterday_high: number
  yesterday_low: number
  yesterday_close: number
  yesterday_range: number
  atr_5d: number
  atr_20d: number
  trade_date: string
}

export function EODLevelsToday() {
  const [levels, setLevels] = useState<EODLevel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchEODLevels() {
      try {
        const supabase = createBrowserClient()

        // Query latest eod_levels with symbols (JOIN)
        // Fetch more records to ensure we get all symbols
        const { data, error } = await supabase
          .from('eod_levels' as any)
          .select(`
            id,
            symbol_id,
            yesterday_high,
            yesterday_low,
            yesterday_close,
            yesterday_range,
            atr_5d,
            atr_20d,
            trade_date,
            symbols!inner (
              symbol,
              name,
              is_active
            )
          `)
          .eq('symbols.is_active', true)
          .order('trade_date', { ascending: false })
          .limit(100) // Fetch more to ensure we get all symbols

        if (error) throw error

        // Transform data to flat structure
        const allLevels: EODLevel[] = (data || []).map((item: any) => ({
          id: item.id,
          symbol_id: item.symbol_id,
          symbol: item.symbols.symbol,
          name: item.symbols.name,
          yesterday_high: item.yesterday_high,
          yesterday_low: item.yesterday_low,
          yesterday_close: item.yesterday_close,
          yesterday_range: item.yesterday_range,
          atr_5d: item.atr_5d,
          atr_20d: item.atr_20d,
          trade_date: item.trade_date,
        }))

        // Group by symbol and keep only the latest (first) entry per symbol
        const uniqueSymbolMap = new Map<string, EODLevel>()
        for (const level of allLevels) {
          if (!uniqueSymbolMap.has(level.symbol_id)) {
            uniqueSymbolMap.set(level.symbol_id, level)
          }
        }

        // Convert to array and sort by symbol for consistent display
        const transformedData = Array.from(uniqueSymbolMap.values())
          .sort((a, b) => a.symbol.localeCompare(b.symbol))

        setLevels(transformedData)
      } catch (err) {
        console.error('Error fetching EOD levels:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch EOD levels')
      } finally {
        setLoading(false)
      }
    }

    fetchEODLevels()
  }, [])

  const formatNumber = (value: number | null | undefined, symbol?: string): string => {
    if (value === null || value === undefined) return 'N/A'
    // Forex pairs need 4-5 decimal places, indices need 2
    const isForex = symbol && (symbol.includes('USD') || symbol.includes('EUR') || symbol.includes('GBP'))
    const decimals = isForex ? 5 : 2
    return value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            EOD Levels Today
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            EOD Levels Today
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (levels.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            EOD Levels Today
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No EOD data available yet</p>
            <p className="text-xs mt-2">Check back after market close</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          EOD Levels Today
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-1">
          Yesterday's key levels and volatility metrics
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead className="text-right">High</TableHead>
                <TableHead className="text-right">Low</TableHead>
                <TableHead className="text-right">Close</TableHead>
                <TableHead className="text-right">Range</TableHead>
                <TableHead className="text-right">ATR 5d</TableHead>
                <TableHead className="text-right">ATR 20d</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {levels.map((level) => (
                <TableRow key={level.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className="text-xs font-mono text-center"
                        style={{
                          width: '80px',
                          minWidth: '80px',
                          maxWidth: '80px',
                          padding: '2px 10px',
                          display: 'inline-flex',
                          justifyContent: 'center',
                          boxSizing: 'border-box'
                        }}
                      >
                        {level.symbol}
                      </Badge>
                      <span className="text-sm font-medium whitespace-nowrap">{level.name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatNumber(level.yesterday_high, level.symbol)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatNumber(level.yesterday_low, level.symbol)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatNumber(level.yesterday_close, level.symbol)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-muted-foreground">
                    {formatNumber(level.yesterday_range, level.symbol)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatNumber(level.atr_5d, level.symbol)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatNumber(level.atr_20d, level.symbol)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div className="mt-4 text-xs text-muted-foreground">
          <p>Last updated: {new Date().toLocaleString()}</p>
        </div>
      </CardContent>
    </Card>
  )
}

export default EODLevelsToday
