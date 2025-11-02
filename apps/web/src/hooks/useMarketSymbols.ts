'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from '@/hooks/use-toast'
import type { MarketSymbol, ChartConfig } from '@/types/chart'

/**
 * Hook for fetching market symbols
 */
export function useMarketSymbols() {
  return useQuery({
    queryKey: ['market_symbols'],
    queryFn: async (): Promise<MarketSymbol[]> => {
      const res = await fetch('/api/symbols')

      if (!res.ok) {
        throw new Error('Failed to fetch market symbols')
      }

      return res.json()
    },
    staleTime: 300000, // 5 minutes
  })
}

/**
 * Hook for fetching a single market symbol
 */
export function useMarketSymbol(symbolId: string) {
  return useQuery({
    queryKey: ['market_symbols', symbolId],
    queryFn: async (): Promise<MarketSymbol> => {
      const res = await fetch(`/api/symbols/${symbolId}`)

      if (!res.ok) {
        throw new Error('Failed to fetch market symbol')
      }

      return res.json()
    },
    enabled: !!symbolId,
  })
}

/**
 * Hook for updating market symbol configuration
 */
export function useUpdateSymbolConfig() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (params: {
      symbolId: string
      chart_img_symbol: string
      chart_enabled: boolean
      chart_config: ChartConfig
    }): Promise<MarketSymbol> => {
      const res = await fetch(`/api/symbols/${params.symbolId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          chart_img_symbol: params.chart_img_symbol,
          chart_enabled: params.chart_enabled,
          chart_config: params.chart_config,
        }),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.message || 'Failed to update symbol configuration')
      }

      return res.json()
    },
    onSuccess: (data) => {
      toast({
        title: 'Configuration Updated',
        description: `Chart settings for ${data.symbol} have been saved.`,
      })

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['market_symbols'] })
      queryClient.invalidateQueries({ queryKey: ['market_symbols', data.id] })
    },
    onError: (error: Error) => {
      toast({
        title: 'Update Failed',
        description: error.message,
        variant: 'destructive',
      })
    },
  })
}
