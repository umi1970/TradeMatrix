'use client'

import { useState, useEffect } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ChartSnapshotCard } from './ChartSnapshotCard'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { RefreshCw } from 'lucide-react'

interface ChartSnapshot {
  id: string
  symbol_id: string
  chart_url: string
  timeframe: string
  created_by_agent: string
  metadata: Record<string, unknown> | null
  created_at: string
  symbol: {
    symbol: string
    name: string
  }
}

export function ChartSnapshotGallery() {
  const supabase = createBrowserClient()
  const [snapshots, setSnapshots] = useState<ChartSnapshot[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filterAgent, setFilterAgent] = useState<string | null>(null)
  const [filterTimeframe, setFilterTimeframe] = useState<string | null>(null)

  useEffect(() => {
    loadSnapshots()
  }, [filterAgent, filterTimeframe])

  const loadSnapshots = async () => {
    setIsLoading(true)

    try {
      // @ts-ignore - chart_snapshots and market_symbols not in generated types yet
      let query = supabase
        .from('chart_snapshots')
        .select(
          `
          *,
          symbol:market_symbols(symbol, name)
        `
        )
        .order('created_at', { ascending: false })
        .limit(50)

      if (filterAgent) {
        query = query.eq('created_by_agent', filterAgent)
      }

      if (filterTimeframe) {
        query = query.eq('timeframe', filterTimeframe)
      }

      const { data, error } = await query

      if (error) throw error

      setSnapshots((data as unknown as ChartSnapshot[]) || [])
    } catch (error) {
      console.error('Error loading snapshots:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const uniqueAgents = Array.from(new Set(snapshots.map((s) => s.created_by_agent)))
  const uniqueTimeframes = Array.from(new Set(snapshots.map((s) => s.timeframe)))

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Chart Snapshots</CardTitle>
          <CardDescription>Recent chart generations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="w-full h-[300px]" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Chart Snapshots ({snapshots.length})</CardTitle>
            <CardDescription>Recent chart generations by AI agents</CardDescription>
          </div>
          <div className="flex gap-2">
            {uniqueAgents.length > 1 && (
              <Select
                value={filterAgent || 'all'}
                onValueChange={(v) => setFilterAgent(v === 'all' ? null : v)}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by agent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Agents</SelectItem>
                  {uniqueAgents.map((agent) => (
                    <SelectItem key={agent} value={agent}>
                      {agent}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {uniqueTimeframes.length > 1 && (
              <Select
                value={filterTimeframe || 'all'}
                onValueChange={(v) => setFilterTimeframe(v === 'all' ? null : v)}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by timeframe" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Timeframes</SelectItem>
                  {uniqueTimeframes.map((tf) => (
                    <SelectItem key={tf} value={tf}>
                      {tf}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            <Button variant="outline" size="icon" onClick={loadSnapshots}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {snapshots.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>No chart snapshots found.</p>
            <p className="text-sm mt-2">
              Configure symbols and let AI agents generate charts.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {snapshots.map((snapshot) => (
              <ChartSnapshotCard
                key={snapshot.id}
                snapshot={snapshot}
                onDelete={loadSnapshots}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
