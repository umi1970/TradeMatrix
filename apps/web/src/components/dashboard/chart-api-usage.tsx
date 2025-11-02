'use client'

import { AlertCircle, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useChartUsage, getUsageStatus } from '@/hooks/useChartUsage'
import { cn } from '@/lib/utils'

export function ChartApiUsage() {
  const { data: usage, isLoading, error, refetch, isRefetching } = useChartUsage()

  const status = getUsageStatus(usage)

  const getProgressColor = () => {
    switch (status) {
      case 'critical':
        return 'bg-red-500'
      case 'warning':
        return 'bg-yellow-500'
      default:
        return 'bg-primary'
    }
  }

  const getTextColor = () => {
    switch (status) {
      case 'critical':
        return 'text-red-500'
      case 'warning':
        return 'text-yellow-500'
      default:
        return 'text-primary'
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>API Usage</CardTitle>
          <CardDescription>Chart generation requests</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-10 w-full" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>API Usage</CardTitle>
          <CardDescription>Chart generation requests</CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              Failed to load API usage data. Please try again.
            </AlertDescription>
          </Alert>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => refetch()}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!usage) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>API Usage</CardTitle>
            <CardDescription>Chart generation requests</CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={cn('h-4 w-4', isRefetching && 'animate-spin')} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Warning Alert */}
        {status === 'warning' && (
          <Alert variant="default" className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
            <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
            <AlertTitle className="text-yellow-600 dark:text-yellow-400">
              High Usage
            </AlertTitle>
            <AlertDescription className="text-yellow-600 dark:text-yellow-400">
              You've used {usage.percentage.toFixed(1)}% of your monthly quota.
            </AlertDescription>
          </Alert>
        )}

        {status === 'critical' && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Critical Usage</AlertTitle>
            <AlertDescription>
              You're approaching the monthly limit. Only {usage.remaining} requests remaining.
            </AlertDescription>
          </Alert>
        )}

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Current Usage</span>
            <span className={cn('font-semibold', getTextColor())}>
              {usage.percentage.toFixed(1)}%
            </span>
          </div>
          <Progress
            value={usage.percentage}
            className="h-3"
            indicatorClassName={getProgressColor()}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{usage.total_requests} / {usage.limit} requests</span>
            <span>{usage.remaining} remaining</span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg border p-3">
            <div className="text-2xl font-bold">{usage.total_requests}</div>
            <div className="text-xs text-muted-foreground">Total Requests</div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="text-2xl font-bold">{usage.remaining}</div>
            <div className="text-xs text-muted-foreground">Remaining</div>
          </div>
        </div>

        {/* Reset Info */}
        {usage.reset_at && (
          <div className="text-xs text-muted-foreground text-center">
            Resets on {new Date(usage.reset_at).toLocaleDateString()}
          </div>
        )}

        {/* Auto-refresh indicator */}
        <div className="text-xs text-muted-foreground text-center">
          Auto-refreshes every minute
        </div>
      </CardContent>
    </Card>
  )
}
