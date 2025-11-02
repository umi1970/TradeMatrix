'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from '@/hooks/use-toast'
import type { ChartSnapshot } from '@/types/chart'

/**
 * Hook for fetching chart snapshots
 */
export function useChartSnapshots(symbolId?: string) {
  return useQuery({
    queryKey: ['chart_snapshots', symbolId],
    queryFn: async (): Promise<ChartSnapshot[]> => {
      const url = symbolId
        ? `/api/charts/snapshots/${symbolId}`
        : '/api/charts/snapshots'

      const res = await fetch(url)

      if (!res.ok) {
        throw new Error('Failed to fetch chart snapshots')
      }

      return res.json()
    },
    enabled: true,
    staleTime: 60000, // 1 minute
  })
}

/**
 * Hook for deleting chart snapshots
 */
export function useDeleteChartSnapshot() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (snapshotId: string): Promise<void> => {
      const res = await fetch(`/api/charts/snapshots/${snapshotId}`, {
        method: 'DELETE',
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.message || 'Failed to delete snapshot')
      }
    },
    onSuccess: () => {
      toast({
        title: 'Snapshot Deleted',
        description: 'The chart snapshot has been deleted.',
      })

      // Invalidate all snapshots queries
      queryClient.invalidateQueries({ queryKey: ['chart_snapshots'] })
    },
    onError: (error: Error) => {
      toast({
        title: 'Delete Failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook for getting latest snapshot for a symbol
 */
export function useLatestSnapshot(symbolId: string, timeframe?: string) {
  const { data: snapshots = [] } = useChartSnapshots(symbolId)

  if (!snapshots.length) return null

  if (timeframe) {
    return snapshots.find(s => s.timeframe === timeframe) || null
  }

  // Return most recent snapshot
  return snapshots.sort((a, b) =>
    new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime()
  )[0]
}
