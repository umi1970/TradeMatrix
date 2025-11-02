'use client'

import { useQuery } from '@tanstack/react-query'
import type { ChartUsageData } from '@/types/chart'

/**
 * Hook for fetching chart API usage statistics
 */
export function useChartUsage() {
  return useQuery({
    queryKey: ['chart_usage'],
    queryFn: async (): Promise<ChartUsageData> => {
      const res = await fetch('/api/charts/usage')

      if (!res.ok) {
        throw new Error('Failed to fetch chart usage')
      }

      return res.json()
    },
    refetchInterval: 60000, // Auto-refresh every 1 minute
    staleTime: 30000, // Consider data stale after 30 seconds
  })
}

/**
 * Helper function to determine if usage is at warning level
 */
export function isUsageAtWarning(usage?: ChartUsageData): boolean {
  if (!usage) return false
  return usage.percentage >= 80
}

/**
 * Helper function to determine if usage is at critical level
 */
export function isUsageAtCritical(usage?: ChartUsageData): boolean {
  if (!usage) return false
  return usage.percentage >= 95
}

/**
 * Helper function to get usage status
 */
export function getUsageStatus(usage?: ChartUsageData): 'normal' | 'warning' | 'critical' {
  if (!usage) return 'normal'

  if (usage.percentage >= 95) return 'critical'
  if (usage.percentage >= 80) return 'warning'
  return 'normal'
}
