'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react'

interface Performer {
  symbol: string
  name: string
  change_percent: number
  yesterday_close: number
}

interface PerformersData {
  gainers: Performer[]
  losers: Performer[]
}

export function TopPerformersCard() {
  const [performers, setPerformers] = useState<PerformersData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchPerformers() {
      try {
        const supabase = createBrowserClient()

        // Get today's date
        const today = new Date().toISOString().split('T')[0]

        // Query today's eod_levels ordered by daily_change_percent
        let { data, error } = await supabase
          .from('eod_levels' as any)
          .select(`
            daily_change_percent,
            yesterday_close,
            symbols!inner (
              symbol,
              name,
              is_active
            )
          `)
          .eq('symbols.is_active', true)
          .gte('trade_date', today)
          .not('daily_change_percent', 'is', null)
          .order('daily_change_percent', { ascending: false })

        if (error) throw error

        // If no data for today, try yesterday
        if (!data || data.length === 0) {
          const yesterday = new Date()
          yesterday.setDate(yesterday.getDate() - 1)
          const yesterdayStr = yesterday.toISOString().split('T')[0]

          const result = await supabase
            .from('eod_levels' as any)
            .select(`
              daily_change_percent,
              yesterday_close,
              symbols!inner (
                symbol,
                name,
                is_active
              )
            `)
            .eq('symbols.is_active', true)
            .eq('trade_date', yesterdayStr)
            .not('daily_change_percent', 'is', null)
            .order('daily_change_percent', { ascending: false })

          data = result.data
          if (result.error) throw result.error
        }

        if (!data || data.length === 0) {
          setPerformers(null)
          setLoading(false)
          return
        }

        // Transform and separate gainers and losers
        const allPerformers: Performer[] = data.map((item: any) => ({
          symbol: item.symbols.symbol,
          name: item.symbols.name,
          change_percent: item.daily_change_percent,
          yesterday_close: item.yesterday_close,
        }))

        // Top 3 gainers and bottom 3 losers
        const gainers = allPerformers.slice(0, 3)
        const losers = allPerformers.slice(-3).reverse()

        setPerformers({ gainers, losers })
      } catch (err) {
        console.error('Error fetching top performers:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch performers')
      } finally {
        setLoading(false)
      }
    }

    fetchPerformers()
  }, [])

  const formatPercent = (value: number): string => {
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  const formatPrice = (value: number, symbol: string): string => {
    // Forex pairs need 4-5 decimal places, indices need 2
    const isForex = symbol && (symbol.includes('USD') || symbol.includes('EUR') || symbol.includes('GBP'))
    const decimals = isForex ? 5 : 2
    return value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  }

  const getPercentColor = (value: number): string => {
    if (value > 0) return 'text-green-600 dark:text-green-400'
    if (value < 0) return 'text-red-600 dark:text-red-400'
    return 'text-muted-foreground'
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Performers</CardTitle>
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
          <CardTitle>Top Performers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!performers || (performers.gainers.length === 0 && performers.losers.length === 0)) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Performers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No performance data available</p>
            <p className="text-xs mt-2">Check back after market close</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Performers</CardTitle>
        <p className="text-sm text-muted-foreground mt-1">
          Best and worst performing symbols today
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Top Gainers */}
          {performers.gainers.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
                <h3 className="text-sm font-semibold">Top Gainers</h3>
              </div>
              <div className="space-y-2">
                {performers.gainers.map((performer, index) => (
                  <div
                    key={`gainer-${performer.symbol}`}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="text-xs font-mono w-20 justify-center">
                        {performer.symbol}
                      </Badge>
                      <div>
                        <p className="text-sm font-medium">{performer.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Close: {formatPrice(performer.yesterday_close, performer.symbol)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-lg font-bold ${getPercentColor(performer.change_percent)}`}>
                        {formatPercent(performer.change_percent)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Losers */}
          {performers.losers.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
                <h3 className="text-sm font-semibold">Top Losers</h3>
              </div>
              <div className="space-y-2">
                {performers.losers.map((performer, index) => (
                  <div
                    key={`loser-${performer.symbol}`}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="text-xs font-mono w-20 justify-center">
                        {performer.symbol}
                      </Badge>
                      <div>
                        <p className="text-sm font-medium">{performer.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Close: {formatPrice(performer.yesterday_close, performer.symbol)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-lg font-bold ${getPercentColor(performer.change_percent)}`}>
                        {formatPercent(performer.change_percent)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default TopPerformersCard
