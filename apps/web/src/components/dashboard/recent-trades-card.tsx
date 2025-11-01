'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'

interface Trade {
  id: string
  symbol: string
  side: 'long' | 'short'
  entry_price: number
  exit_price: number | null
  position_size: number
  status: 'open' | 'closed' | 'cancelled'
  pnl: number | null
  pnl_percentage: number | null
  entry_time: string
  exit_time: string | null
  created_at: string
}

export function RecentTradesCard() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchRecentTrades() {
      try {
        const supabase = createBrowserClient()

        // Get current user
        const { data: { user }, error: userError } = await supabase.auth.getUser()
        if (userError || !user) {
          setError('Authentication required')
          setLoading(false)
          return
        }

        // Fetch last 10 trades
        const { data, error: tradesError } = await supabase
          .from('trades')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false })
          .limit(10)

        if (tradesError) {
          throw tradesError
        }

        setTrades(data || [])
      } catch (err) {
        console.error('Error fetching recent trades:', err)
        setError('Failed to load recent trades')
      } finally {
        setLoading(false)
      }
    }

    fetchRecentTrades()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    )
  }

  if (trades.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
          <CardDescription>Your latest trading activity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-sm text-muted-foreground">
              No trades yet. Start trading to see your history here!
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      open: 'bg-blue-500/10 text-blue-500',
      closed: 'bg-green-500/10 text-green-500',
      cancelled: 'bg-gray-500/10 text-gray-500'
    }
    return styles[status as keyof typeof styles] || styles.open
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Trades</CardTitle>
        <CardDescription>Your latest trading activity</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-xs text-muted-foreground">
                <th className="pb-3 font-medium">Symbol</th>
                <th className="pb-3 font-medium">Date</th>
                <th className="pb-3 font-medium text-right">P/L</th>
                <th className="pb-3 font-medium text-center">Status</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {trades.map((trade) => (
                <tr key={trade.id} className="border-b last:border-0">
                  <td className="py-3">
                    <div className="font-medium">{trade.symbol}</div>
                    <div className="text-xs text-muted-foreground capitalize">
                      {trade.side}
                    </div>
                  </td>
                  <td className="py-3 text-muted-foreground">
                    {formatDate(trade.created_at)}
                  </td>
                  <td className="py-3 text-right">
                    {trade.pnl !== null ? (
                      <div>
                        <div
                          className={`font-semibold ${
                            trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'
                          }`}
                        >
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                        </div>
                        {trade.pnl_percentage !== null && (
                          <div
                            className={`text-xs ${
                              trade.pnl >= 0 ? 'text-green-500/70' : 'text-red-500/70'
                            }`}
                          >
                            {trade.pnl_percentage >= 0 ? '+' : ''}
                            {trade.pnl_percentage.toFixed(2)}%
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="py-3 text-center">
                    <span
                      className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${getStatusBadge(trade.status)}`}
                    >
                      {trade.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
