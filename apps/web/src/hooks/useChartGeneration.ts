'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from '@/hooks/use-toast'
import type { ChartGenerationParams, ChartGenerationResponse } from '@/types/chart'

/**
 * Hook for generating charts via API
 */
export function useChartGeneration() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const generateMutation = useMutation({
    mutationFn: async (params: ChartGenerationParams): Promise<ChartGenerationResponse> => {
      const res = await fetch('/api/charts/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.message || 'Failed to generate chart')
      }

      return res.json()
    },
    onSuccess: (data, variables) => {
      toast({
        title: 'Chart Generated',
        description: 'Your chart has been generated successfully.',
      })

      // Invalidate chart snapshots to refetch
      queryClient.invalidateQueries({ queryKey: ['chart_snapshots', variables.symbol_id] })
      queryClient.invalidateQueries({ queryKey: ['chart_usage'] })
    },
    onError: (error: Error) => {
      toast({
        title: 'Generation Failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  return {
    generate: generateMutation.mutate,
    generateAsync: generateMutation.mutateAsync,
    isGenerating: generateMutation.isPending,
    isSuccess: generateMutation.isSuccess,
    isError: generateMutation.isError,
    error: generateMutation.error,
    data: generateMutation.data,
    reset: generateMutation.reset,
  }
}
