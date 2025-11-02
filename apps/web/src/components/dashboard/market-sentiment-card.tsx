'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface SentimentData {
  averageChange: number
  sentiment: 'bullish' | 'bearish' | 'neutral'
  activeSymbols: number
  positiveCount: number
  negativeCount: number
}

export function MarketSentimentCard() {
  const [sentiment, setSentiment] = useState<SentimentData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSentiment() {
      try {
        const supabase = createBrowserClient()

        // Get today's date
        const today = new Date().toISOString().split('T')[0]

        // Query today's eod_levels for all active symbols
        const { data, error } = await supabase
          .from('eod_levels' as any)
          .select(`
            daily_change_percent,
            symbols!inner (
              is_active
            )
          `)
          .eq('symbols.is_active', true)
          .gte('trade_date', today)

        if (error) throw error

        if (!data || data.length === 0) {
          // No data for today, try yesterday
          const yesterday = new Date()
          yesterday.setDate(yesterday.getDate() - 1)
          const yesterdayStr = yesterday.toISOString().split('T')[0]

          const { data: yesterdayData, error: yesterdayError } = await supabase
            .from('eod_levels' as any)
            .select(`
              daily_change_percent,
              symbols!inner (
                is_active
              )
            `)
            .eq('symbols.is_active', true)
            .eq('trade_date', yesterdayStr)

          if (yesterdayError) throw yesterdayError
          if (!yesterdayData || yesterdayData.length === 0) {
            setSentiment(null)
            setLoading(false)
            return
          }

          calculateSentiment(yesterdayData)
          return
        }

        calculateSentiment(data)
      } catch (err) {
        console.error('Error fetching market sentiment:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch sentiment')
      } finally {
        setLoading(false)
      }
    }

    function calculateSentiment(data: any[]) {
      const changes = data
        .map((item) => item.daily_change_percent)
        .filter((change): change is number => change !== null && change !== undefined)

      if (changes.length === 0) {
        setSentiment(null)
        return
      }

      const avgChange = changes.reduce((sum, change) => sum + change, 0) / changes.length
      const positiveCount = changes.filter((change) => change > 0).length
      const negativeCount = changes.filter((change) => change < 0).length

      let sentimentType: 'bullish' | 'bearish' | 'neutral' = 'neutral'
      if (avgChange > 0.5) sentimentType = 'bullish'
      else if (avgChange < -0.5) sentimentType = 'bearish'

      setSentiment({
        averageChange: avgChange,
        sentiment: sentimentType,
        activeSymbols: changes.length,
        positiveCount,
        negativeCount,
      })
    }

    fetchSentiment()
  }, [])

  const getSentimentConfig = (sentiment: 'bullish' | 'bearish' | 'neutral') => {
    switch (sentiment) {
      case 'bullish':
        return {
          label: 'Bullish',
          icon: TrendingUp,
          color: 'text-green-600 dark:text-green-400',
          bgColor: 'bg-green-50 dark:bg-green-950',
          badgeVariant: 'default' as const,
        }
      case 'bearish':
        return {
          label: 'Bearish',
          icon: TrendingDown,
          color: 'text-red-600 dark:text-red-400',
          bgColor: 'bg-red-50 dark:bg-red-950',
          badgeVariant: 'destructive' as const,
        }
      default:
        return {
          label: 'Neutral',
          icon: Minus,
          color: 'text-gray-600 dark:text-gray-400',
          bgColor: 'bg-gray-50 dark:bg-gray-950',
          badgeVariant: 'secondary' as const,
        }
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Sentiment</CardTitle>
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
          <CardTitle>Market Sentiment</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!sentiment) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Sentiment</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No sentiment data available</p>
            <p className="text-xs mt-2">Waiting for market data</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const config = getSentimentConfig(sentiment.sentiment)
  const Icon = config.icon

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Market Sentiment</CardTitle>
        <Badge variant={config.badgeVariant} className="text-xs">
          {config.label}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Main Sentiment Display */}
          <div className={`flex items-center gap-3 p-4 rounded-lg ${config.bgColor}`}>
            <Icon className={`h-8 w-8 ${config.color}`} />
            <div>
              <p className={`text-2xl font-bold ${config.color}`}>
                {sentiment.averageChange >= 0 ? '+' : ''}
                {sentiment.averageChange.toFixed(2)}%
              </p>
              <p className="text-xs text-muted-foreground">Average Daily Change</p>
            </div>
          </div>

          {/* Statistics Grid */}
          <div className="grid grid-cols-3 gap-4 pt-2">
            <div className="text-center">
              <p className="text-2xl font-bold">{sentiment.activeSymbols}</p>
              <p className="text-xs text-muted-foreground">Symbols</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {sentiment.positiveCount}
              </p>
              <p className="text-xs text-muted-foreground">Up</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {sentiment.negativeCount}
              </p>
              <p className="text-xs text-muted-foreground">Down</p>
            </div>
          </div>

          {/* Sentiment Description */}
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground">
              {sentiment.sentiment === 'bullish' && 'Markets showing positive momentum across tracked symbols.'}
              {sentiment.sentiment === 'bearish' && 'Markets showing negative pressure across tracked symbols.'}
              {sentiment.sentiment === 'neutral' && 'Markets showing mixed signals with no clear direction.'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default MarketSentimentCard
