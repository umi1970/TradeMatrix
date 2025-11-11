'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Loader2, TrendingUp, TrendingDown, Minus, ExternalLink } from 'lucide-react'

interface Analysis {
  id: string
  symbol: string
  vendor: string
  alias?: string
  timeframe: string
  trend: string
  confidence_score: number
  chart_url: string
  created_at: string
}

interface AnalysesResponse {
  analyses: Analysis[]
  total: number
  limit: number
  offset: number
  hasMore: boolean
}

export function AnalysesTable() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(false)
  const [total, setTotal] = useState(0)

  const fetchAnalyses = async (offset: number = 0, append: boolean = false) => {
    try {
      if (append) {
        setIsLoadingMore(true)
      } else {
        setIsLoading(true)
      }

      const response = await fetch(`/api/charts/analyses?limit=20&offset=${offset}`)

      if (!response.ok) {
        throw new Error('Failed to fetch analyses')
      }

      const data: AnalysesResponse = await response.json()

      if (append) {
        setAnalyses((prev) => [...prev, ...data.analyses])
      } else {
        setAnalyses(data.analyses)
      }

      setHasMore(data.hasMore)
      setTotal(data.total)
      setError(null)
    } catch (err) {
      console.error('Error fetching analyses:', err)
      setError(err instanceof Error ? err.message : 'Failed to load analyses')
    } finally {
      setIsLoading(false)
      setIsLoadingMore(false)
    }
  }

  useEffect(() => {
    fetchAnalyses()
  }, [])

  const handleLoadMore = () => {
    fetchAnalyses(analyses.length, true)
  }

  const getTrendIcon = (trend: string) => {
    if (trend === 'bullish') return <TrendingUp className="h-4 w-4 text-green-500" />
    if (trend === 'bearish') return <TrendingDown className="h-4 w-4 text-red-500" />
    return <Minus className="h-4 w-4 text-gray-500" />
  }

  const getTrendBadge = (trend: string) => {
    const variant = trend === 'bullish' ? 'default' : trend === 'bearish' ? 'destructive' : 'secondary'
    return <Badge variant={variant}>{trend.toUpperCase()}</Badge>
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading analyses...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center">
            <p className="text-sm text-destructive">{error}</p>
            <Button onClick={() => fetchAnalyses()} variant="outline" size="sm" className="mt-4">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (analyses.length === 0) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center">
            <p className="text-muted-foreground">No analyses yet</p>
            <p className="text-sm text-muted-foreground mt-2">Upload a CSV to get started</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Analyses</CardTitle>
        <CardDescription>
          {total} total analysis{total !== 1 ? 'es' : ''} • Showing {analyses.length}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>Timeframe</TableHead>
                <TableHead>Trend</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analyses.map((analysis) => (
                <TableRow key={analysis.id}>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium">{analysis.symbol}</span>
                      {analysis.alias && (
                        <span className="text-xs text-muted-foreground">{analysis.alias}</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{analysis.timeframe}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getTrendIcon(analysis.trend)}
                      {getTrendBadge(analysis.trend)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-muted rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            analysis.confidence_score >= 0.7
                              ? 'bg-green-500'
                              : analysis.confidence_score >= 0.5
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${analysis.confidence_score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {(analysis.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {formatDate(analysis.created_at)}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                    >
                      <a href={analysis.chart_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {hasMore && (
          <div className="flex justify-center mt-4">
            <Button
              onClick={handleLoadMore}
              disabled={isLoadingMore}
              variant="outline"
            >
              {isLoadingMore ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading...
                </>
              ) : (
                'Load More'
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
