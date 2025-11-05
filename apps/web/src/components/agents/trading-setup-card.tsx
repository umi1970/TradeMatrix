'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Bot, TrendingUp, TrendingDown, Minus, Clock } from 'lucide-react'
import Image from 'next/image'
import { formatDistanceToNow } from 'date-fns'

interface Pattern {
  name: string
  type: string
  confidence: number
  description?: string
}

interface TradingSetup {
  id: string
  symbol: string
  timeframe: string
  agent_name: string
  analysis: string
  chart_url: string
  confidence_score: number
  created_at: string
  metadata: {
    setup_type?: string
    entry?: number
    sl?: number
    tp?: number
    patterns?: Pattern[]
    trend?: string
    support_levels?: number[]
    resistance_levels?: number[]
  }
}

interface TradingSetupCardProps {
  setup: TradingSetup
}

export function TradingSetupCard({ setup }: TradingSetupCardProps) {
  const getAgentColor = (agentName: string) => {
    switch (agentName) {
      case 'ChartWatcher':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
      case 'SignalBot':
        return 'bg-green-500/10 text-green-500 border-green-500/20'
      case 'MorningPlanner':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/20'
      case 'JournalBot':
        return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
      case 'USOpenPlanner':
        return 'bg-pink-500/10 text-pink-500 border-pink-500/20'
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    }
  }

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'bullish':
        return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'bearish':
        return <TrendingDown className="h-4 w-4 text-red-500" />
      case 'sideways':
        return <Minus className="h-4 w-4 text-yellow-500" />
      default:
        return null
    }
  }

  const getTrendBadgeVariant = (trend?: string) => {
    switch (trend) {
      case 'bullish':
        return 'default'
      case 'bearish':
        return 'destructive'
      case 'sideways':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  const formatTimeAgo = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true })
    } catch {
      return 'recently'
    }
  }

  const confidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-500'
    if (score >= 0.6) return 'text-yellow-500'
    return 'text-orange-500'
  }

  return (
    <Card className="overflow-hidden flex flex-col">
      {/* Card Header */}
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base font-semibold">
              {setup.symbol}
            </CardTitle>
            <Badge variant="outline" className="text-xs">
              {setup.timeframe}
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-2">
          <Badge className={`${getAgentColor(setup.agent_name)} text-xs`}>
            {setup.agent_name}
          </Badge>
          {setup.metadata.trend && (
            <Badge variant={getTrendBadgeVariant(setup.metadata.trend)} className="gap-1">
              {getTrendIcon(setup.metadata.trend)}
              <span className="capitalize">{setup.metadata.trend}</span>
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 flex-1">
        {/* Chart Image - Inline Display */}
        {setup.chart_url && (
          <div className="relative w-full aspect-[3/2] rounded-md overflow-hidden bg-muted">
            <Image
              src={setup.chart_url}
              alt={`${setup.symbol} ${setup.timeframe} chart`}
              fill
              className="object-cover"
              unoptimized
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
              }}
            />
          </div>
        )}

        {/* Analysis Text */}
        {setup.analysis && (
          <div className="text-sm text-muted-foreground line-clamp-3">
            {setup.analysis}
          </div>
        )}

        {/* Detected Patterns */}
        {setup.metadata.patterns && setup.metadata.patterns.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">
              Detected Patterns:
            </p>
            <div className="flex flex-wrap gap-1">
              {setup.metadata.patterns.slice(0, 3).map((pattern, idx) => (
                <Badge
                  key={idx}
                  variant="outline"
                  className="text-xs"
                >
                  {pattern.name.replace(/_/g, ' ')}
                </Badge>
              ))}
              {setup.metadata.patterns.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{setup.metadata.patterns.length - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Entry/SL/TP Levels */}
        {(setup.metadata.entry || setup.metadata.sl || setup.metadata.tp) && (
          <div className="grid grid-cols-3 gap-2 text-xs">
            {setup.metadata.entry && (
              <div className="space-y-1">
                <p className="text-muted-foreground">Entry</p>
                <p className="font-semibold">{setup.metadata.entry.toFixed(2)}</p>
              </div>
            )}
            {setup.metadata.sl && (
              <div className="space-y-1">
                <p className="text-muted-foreground">SL</p>
                <p className="font-semibold text-red-500">
                  {setup.metadata.sl.toFixed(2)}
                </p>
              </div>
            )}
            {setup.metadata.tp && (
              <div className="space-y-1">
                <p className="text-muted-foreground">TP</p>
                <p className="font-semibold text-green-500">
                  {setup.metadata.tp.toFixed(2)}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Support/Resistance Levels */}
        {((setup.metadata.support_levels && setup.metadata.support_levels.length > 0) ||
          (setup.metadata.resistance_levels &&
            setup.metadata.resistance_levels.length > 0)) && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            {setup.metadata.support_levels && setup.metadata.support_levels.length > 0 && (
              <div className="space-y-1">
                <p className="text-muted-foreground">Support</p>
                <div className="space-y-0.5">
                  {setup.metadata.support_levels.slice(0, 2).map((level, idx) => (
                    <p key={idx} className="font-mono text-xs">
                      {Number(level).toFixed(2)}
                    </p>
                  ))}
                </div>
              </div>
            )}
            {setup.metadata.resistance_levels &&
              setup.metadata.resistance_levels.length > 0 && (
                <div className="space-y-1">
                  <p className="text-muted-foreground">Resistance</p>
                  <div className="space-y-0.5">
                    {setup.metadata.resistance_levels.slice(0, 2).map((level, idx) => (
                      <p key={idx} className="font-mono text-xs">
                        {Number(level).toFixed(2)}
                      </p>
                    ))}
                  </div>
                </div>
              )}
          </div>
        )}

        {/* Confidence Score & Timestamp */}
        <div className="flex items-center justify-between pt-2 border-t text-xs">
          <div className="flex items-center gap-1 text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>{formatTimeAgo(setup.created_at)}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">Confidence:</span>
            <span className={`font-semibold ${confidenceColor(setup.confidence_score)}`}>
              {(setup.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
