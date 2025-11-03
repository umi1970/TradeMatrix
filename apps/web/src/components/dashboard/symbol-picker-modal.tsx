'use client'

import { useState, useEffect } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Search, Plus, X, GripVertical } from 'lucide-react'

interface Symbol {
  id: string
  symbol: string
  name: string
  tv_symbol: string | null
  asset_type: string
}

interface WatchlistItem {
  id: string
  position: number
  symbol: Symbol
}

interface SymbolPickerModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  userId: string
  onSaved?: () => void
}

export function SymbolPickerModal({
  open,
  onOpenChange,
  userId,
  onSaved
}: SymbolPickerModalProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [allSymbols, setAllSymbols] = useState<Symbol[]>([])
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const supabase = createBrowserClient()

  // Load symbols and watchlist on open
  useEffect(() => {
    if (open) {
      loadData()
    }
  }, [open])

  async function loadData() {
    setLoading(true)
    try {
      // Fetch all active symbols
      const { data: symbols } = await supabase
        .from('symbols')
        .select('*')
        .eq('is_active', true)
        .order('symbol')

      // Fetch user's current watchlist
      const { data: watchlistData } = await supabase
        .from('user_watchlist')
        .select('id, position, symbols(*)')
        .eq('user_id', userId)
        .order('position')

      setAllSymbols((symbols || []) as Symbol[])
      setWatchlist(
        (watchlistData || []).map(item => ({
          id: item.id,
          position: item.position,
          symbol: (item.symbols as unknown) as Symbol
        }))
      )
    } catch (err) {
      console.error('Failed to load symbols:', err)
    } finally {
      setLoading(false)
    }
  }

  // Filter available symbols (not in watchlist)
  const availableSymbols = allSymbols.filter(
    symbol => !watchlist.some(item => item.symbol.id === symbol.id)
  )

  // Filter by search query
  const filteredSymbols = availableSymbols.filter(symbol =>
    symbol.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    symbol.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Add symbol to watchlist
  function addSymbol(symbol: Symbol) {
    if (watchlist.length >= 10) {
      alert('Maximum 10 symbols allowed')
      return
    }

    const newPosition = watchlist.length + 1
    setWatchlist([
      ...watchlist,
      {
        id: `temp-${Date.now()}`, // Temporary ID until saved
        position: newPosition,
        symbol
      }
    ])
  }

  // Remove symbol from watchlist
  function removeSymbol(symbolId: string) {
    const filtered = watchlist.filter(item => item.symbol.id !== symbolId)
    // Recalculate positions
    setWatchlist(
      filtered.map((item, index) => ({
        ...item,
        position: index + 1
      }))
    )
  }

  // Save watchlist to database
  async function saveWatchlist() {
    setSaving(true)
    try {
      // Delete all existing entries
      await supabase
        .from('user_watchlist')
        .delete()
        .eq('user_id', userId)

      // Insert new entries
      if (watchlist.length > 0) {
        const entries = watchlist.map(item => ({
          user_id: userId,
          symbol_id: item.symbol.id,
          position: item.position
        }))

        const { error } = await supabase
          .from('user_watchlist')
          .insert(entries)

        if (error) throw error
      }

      onSaved?.()
      onOpenChange(false)
    } catch (err) {
      console.error('Failed to save watchlist:', err)
      alert('Failed to save watchlist. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Edit Market Watchlist</DialogTitle>
          <DialogDescription>
            Choose up to 10 symbols to display on your dashboard
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-4 py-4">
          {/* Left: Current Watchlist */}
          <div>
            <h3 className="text-sm font-semibold mb-2">
              Your Watchlist ({watchlist.length}/10)
            </h3>
            <ScrollArea className="h-[400px] border rounded-lg p-2">
              {watchlist.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No symbols selected
                </p>
              ) : (
                <div className="space-y-2">
                  {watchlist.map(item => (
                    <div
                      key={item.symbol.id}
                      className="flex items-center gap-2 p-2 bg-muted rounded"
                    >
                      <GripVertical className="h-4 w-4 text-muted-foreground" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{item.symbol.symbol}</p>
                        <p className="text-xs text-muted-foreground">{item.symbol.name}</p>
                      </div>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => removeSymbol(item.symbol.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          {/* Right: Available Symbols */}
          <div>
            <h3 className="text-sm font-semibold mb-2">Add Symbols</h3>
            <div className="relative mb-2">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search symbols..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
            <ScrollArea className="h-[360px] border rounded-lg p-2">
              {loading ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Loading...
                </p>
              ) : filteredSymbols.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No symbols found
                </p>
              ) : (
                <div className="space-y-2">
                  {filteredSymbols.map(symbol => (
                    <div
                      key={symbol.id}
                      className="flex items-center gap-2 p-2 hover:bg-muted rounded cursor-pointer"
                      onClick={() => addSymbol(symbol)}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium">{symbol.symbol}</p>
                          <Badge variant="outline" className="text-xs">
                            {symbol.asset_type}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{symbol.name}</p>
                      </div>
                      <Button size="icon" variant="ghost">
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={saveWatchlist} disabled={saving}>
            {saving ? 'Saving...' : 'Save Watchlist'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
