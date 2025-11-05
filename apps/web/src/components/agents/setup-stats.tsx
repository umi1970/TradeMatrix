'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Activity,
  TrendingUp,
  Target,
  Clock,
  Bot,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface TradingSetup {
  id: string
  agent_name: string
  confidence_score: number
  created_at: string
  metadata: {
    trend?: string
  }
}

interface SetupStatsProps {
  setups: TradingSetup[]
}

export function SetupStats({ setups }: SetupStatsProps) {
  // Calculate total setups
  const totalSetups = setups.length

  // Calculate setups today
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const setupsToday = setups.filter((setup) => {
    const setupDate = new Date(setup.created_at)
    return setupDate >= today
  }).length

  // Calculate average quality score
  const avgQualityScore =
    setups.length > 0
      ? setups.reduce((sum, setup) => sum + setup.confidence_score, 0) /
        setups.length
      : 0

  // Get latest setup time
  const latestSetup = setups.length > 0 ? setups[0] : null
  const latestUpdateTime = latestSetup
    ? formatDistanceToNow(new Date(latestSetup.created_at), { addSuffix: true })
    : 'No setups yet'

  // Count by agent
  const agentCounts = setups.reduce((acc, setup) => {
    acc[setup.agent_name] = (acc[setup.agent_name] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // Get most active agent
  const mostActiveAgent =
    Object.keys(agentCounts).length > 0
      ? Object.entries(agentCounts).sort((a, b) => b[1] - a[1])[0]
      : null

  // Count active setups (high confidence)
  const activeSetups = setups.filter((setup) => setup.confidence_score >= 0.8).length

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Total Setups Today */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Setups Today</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{setupsToday}</div>
          <p className="text-xs text-muted-foreground">
            {totalSetups} total setups
          </p>
        </CardContent>
      </Card>

      {/* Active Setups (High Confidence) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Setups</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-500">{activeSetups}</div>
          <p className="text-xs text-muted-foreground">
            Confidence score &gt;= 80%
          </p>
        </CardContent>
      </Card>

      {/* Average Quality Score */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Quality</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(avgQualityScore * 100).toFixed(0)}%
          </div>
          <p className="text-xs text-muted-foreground">
            {totalSetups > 0
              ? `Based on ${totalSetups} setup${totalSetups === 1 ? '' : 's'}`
              : 'No data available'}
          </p>
        </CardContent>
      </Card>

      {/* Latest Update */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Latest Update</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-lg font-semibold truncate">
            {latestUpdateTime}
          </div>
          <p className="text-xs text-muted-foreground">
            {mostActiveAgent
              ? `Most active: ${mostActiveAgent[0]} (${mostActiveAgent[1]})`
              : 'Waiting for agent activity'}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
