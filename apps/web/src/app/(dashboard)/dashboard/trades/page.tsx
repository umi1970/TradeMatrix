'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { TradesTable } from '@/components/dashboard/trades-table'
import { TradeFiltersComponent } from '@/components/dashboard/trade-filters'
import { TradeDialog } from '@/components/dashboard/trade-dialog'
import { createBrowserClient } from '@/lib/supabase/client'
import {
  getFilteredTrades,
  getUserSymbols,
  createTrade,
  updateTrade,
  deleteTrade,
  type Trade,
  type TradeFilters,
} from '@/lib/supabase/queries-client'
import { useToast } from '@/hooks/use-toast'

export default function TradesPage() {
  const { toast } = useToast()
  const [trades, setTrades] = useState<Trade[]>([])
  const [symbols, setSymbols] = useState<string[]>([])
  const [filters, setFilters] = useState<TradeFilters>({})
  const [currentPage, setCurrentPage] = useState(1)
  const [totalTrades, setTotalTrades] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [userId, setUserId] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null)

  const pageSize = 10

  // Get user ID
  useEffect(() => {
    const supabase = createBrowserClient()
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (user) {
        setUserId(user.id)
      }
    })
  }, [])

  // Fetch trades when userId, filters, or page changes
  useEffect(() => {
    if (!userId) return

    const fetchTrades = async () => {
      setIsLoading(true)
      try {
        const { trades: fetchedTrades, total } = await getFilteredTrades(
          userId,
          filters,
          currentPage,
          pageSize
        )
        setTrades(fetchedTrades)
        setTotalTrades(total)
      } catch (error) {
        console.error('Error fetching trades:', error)
        toast({
          title: 'Error',
          description: 'Failed to load trades',
          variant: 'destructive',
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchTrades()
  }, [userId, filters, currentPage, toast])

  // Fetch symbols for filter
  useEffect(() => {
    if (!userId) return

    const fetchSymbols = async () => {
      const userSymbols = await getUserSymbols(userId)
      setSymbols(userSymbols)
    }

    fetchSymbols()
  }, [userId])

  const handleFilterChange = (newFilters: TradeFilters) => {
    setFilters(newFilters)
    setCurrentPage(1) // Reset to first page when filters change
  }

  const handleCreateTrade = () => {
    setSelectedTrade(null)
    setDialogOpen(true)
  }

  const handleEditTrade = (trade: Trade) => {
    setSelectedTrade(trade)
    setDialogOpen(true)
  }

  const handleViewTrade = (trade: Trade) => {
    // For now, just open edit dialog
    // In future, can implement a read-only view dialog
    handleEditTrade(trade)
  }

  const handleDeleteTrade = async (tradeId: string) => {
    if (!confirm('Are you sure you want to delete this trade?')) return

    try {
      await deleteTrade(tradeId)
      toast({
        title: 'Success',
        description: 'Trade deleted successfully',
      })

      // Refresh trades list
      if (userId) {
        const { trades: fetchedTrades, total } = await getFilteredTrades(
          userId,
          filters,
          currentPage,
          pageSize
        )
        setTrades(fetchedTrades)
        setTotalTrades(total)

        // Update symbols list
        const userSymbols = await getUserSymbols(userId)
        setSymbols(userSymbols)
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete trade',
        variant: 'destructive',
      })
    }
  }

  const handleSaveTrade = async (tradeData: Partial<Trade>) => {
    if (!userId) return

    try {
      if (selectedTrade) {
        // Update existing trade
        await updateTrade(selectedTrade.id, tradeData)
      } else {
        // Create new trade
        await createTrade({
          ...tradeData,
          user_id: userId,
        } as any)
      }

      // Refresh trades list
      const { trades: fetchedTrades, total } = await getFilteredTrades(
        userId,
        filters,
        currentPage,
        pageSize
      )
      setTrades(fetchedTrades)
      setTotalTrades(total)

      // Update symbols list
      const userSymbols = await getUserSymbols(userId)
      setSymbols(userSymbols)
    } catch (error) {
      throw error // Let dialog handle the error
    }
  }

  const totalPages = Math.ceil(totalTrades / pageSize)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trades</h1>
          <p className="text-muted-foreground mt-1">
            Manage and analyze your trading positions
          </p>
        </div>
        <Button onClick={handleCreateTrade}>
          <Plus className="h-4 w-4 mr-2" />
          New Trade
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <TradeFiltersComponent
            symbols={symbols}
            onFilterChange={handleFilterChange}
            initialFilters={filters}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trade History</CardTitle>
          <p className="text-sm text-muted-foreground">
            Showing {trades.length} of {totalTrades} trades
          </p>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading trades...</p>
            </div>
          ) : (
            <>
              <TradesTable
                trades={trades}
                onEdit={handleEditTrade}
                onDelete={handleDeleteTrade}
                onView={handleViewTrade}
              />

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setCurrentPage((p) => Math.min(totalPages, p + 1))
                      }
                      disabled={currentPage === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Trade Dialog */}
      {userId && (
        <TradeDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          trade={selectedTrade}
          userId={userId}
          onSave={handleSaveTrade}
        />
      )}
    </div>
  )
}
