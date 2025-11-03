# Frontend Implementation: TradingView Widgets

**Last Updated:** 2025-11-03

---

## 📋 Implementation Overview

### Components to Create/Update

1. **New:** `tradingview-widget.tsx` - Reusable TradingView embed
2. **New:** `symbol-picker-modal.tsx` - Add/remove symbols dialog
3. **Update:** `dashboard/page.tsx` - Replace market cards with widgets
4. **Update:** `market-overview-card.tsx` - Delete (no longer needed)

---

## 🎨 Component 1: TradingView Widget

### File: `apps/web/src/components/dashboard/tradingview-widget.tsx`

```typescript
'use client'

import { useEffect, useRef, useState } from 'react'

interface TradingViewWidgetProps {
  symbol: string          // TradingView format: "XETR:DAX", "FX:EURUSD"
  width?: string | number
  height?: string | number
  colorTheme?: 'light' | 'dark'
}

export function TradingViewWidget({
  symbol,
  width = '100%',
  height = 200,
  colorTheme = 'dark'
}: TradingViewWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Clear previous content
    if (containerRef.current) {
      containerRef.current.innerHTML = ''
    }

    setIsLoading(true)
    setError(null)

    try {
      // Create widget configuration
      const widgetConfig = {
        symbols: [[symbol, '|1D']], // Symbol + timeframe
        chartOnly: false,
        width,
        height,
        locale: 'en',
        colorTheme,
        autosize: false,
        showVolume: false,
        showMA: false,
        hideDateRanges: false,
        hideMarketStatus: false,
        hideSymbolLogo: false,
        scalePosition: 'right',
        scaleMode: 'Normal',
        fontFamily: 'Trebuchet MS, sans-serif',
        fontSize: '10',
        noTimeScale: false,
        valuesTracking: '1',
        changeMode: 'price-and-percent',
        chartType: 'area',
        upColor: '#22c55e',      // Green
        downColor: '#ef4444',     // Red
        borderUpColor: '#22c55e',
        borderDownColor: '#ef4444',
        wickUpColor: '#22c55e',
        wickDownColor: '#ef4444'
      }

      // Create script element
      const script = document.createElement('script')
      script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js'
      script.type = 'text/javascript'
      script.async = true
      script.innerHTML = JSON.stringify(widgetConfig)

      script.onload = () => setIsLoading(false)
      script.onerror = () => {
        setError('Failed to load TradingView widget')
        setIsLoading(false)
      }

      containerRef.current?.appendChild(script)
    } catch (err) {
      setError('Error initializing widget')
      setIsLoading(false)
    }

    // Cleanup on unmount
    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = ''
      }
    }
  }, [symbol, width, height, colorTheme])

  return (
    <div className="relative">
      {/* Loading State */}
      {isLoading && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-card rounded-lg"
          style={{ height: typeof height === 'number' ? `${height}px` : height }}
        >
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div
          className="absolute inset-0 flex items-center justify-center bg-card rounded-lg border border-destructive"
          style={{ height: typeof height === 'number' ? `${height}px` : height }}
        >
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* TradingView Widget Container */}
      <div
        ref={containerRef}
        className="tradingview-widget-container rounded-lg overflow-hidden"
      />
    </div>
  )
}
```

---

## 🔧 Component 2: Symbol Picker Modal

### File: `apps/web/src/components/dashboard/symbol-picker-modal.tsx`

```typescript
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
  tv_symbol: string
  type: 'index' | 'forex' | 'stock'
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

      setAllSymbols(symbols || [])
      setWatchlist(
        watchlistData?.map(item => ({
          id: item.id,
          position: item.position,
          symbol: item.symbols as Symbol
        })) || []
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
                            {symbol.type}
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
```

---

## 🏠 Component 3: Update Dashboard Page

### File: `apps/web/src/app/(dashboard)/dashboard/page.tsx`

**Changes:**

1. **Remove old import:**
```typescript
// OLD
import { MarketOverviewCard } from '@/components/dashboard/market-overview-card'

// NEW
import { TradingViewWidget } from '@/components/dashboard/tradingview-widget'
import { SymbolPickerModal } from '@/components/dashboard/symbol-picker-modal'
```

2. **Add watchlist state:**
```typescript
const [watchlist, setWatchlist] = useState([])
const [showSymbolPicker, setShowSymbolPicker] = useState(false)
```

3. **Fetch watchlist instead of market data:**
```typescript
// OLD
const fetchMarketData = async () => {
  const response = await fetch('/api/market-data/current')
  const result = await response.json()
  setMarketData(result.data)
}

// NEW
const fetchWatchlist = async () => {
  const supabase = createBrowserClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session) return

  const { data } = await supabase
    .from('user_watchlist')
    .select('*, symbols(*)')
    .eq('user_id', session.user.id)
    .order('position')

  setWatchlist(data || [])
}
```

4. **Replace Market Overview section:**
```typescript
{/* Market Overview */}
<section>
  <div className="flex items-center justify-between mb-4">
    <h2 className="text-xl font-semibold">Market Overview</h2>
    <Button
      variant="outline"
      size="sm"
      onClick={() => setShowSymbolPicker(true)}
    >
      <Settings className="h-4 w-4 mr-2" />
      Edit Watchlist
    </Button>
  </div>

  {watchlist.length === 0 ? (
    <Card>
      <CardContent className="py-12 text-center">
        <p className="text-muted-foreground mb-4">
          No symbols in your watchlist
        </p>
        <Button onClick={() => setShowSymbolPicker(true)}>
          Add Symbols
        </Button>
      </CardContent>
    </Card>
  ) : (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {watchlist.map((item) => (
        <TradingViewWidget
          key={item.id}
          symbol={item.symbols.tv_symbol}
          height={200}
        />
      ))}
    </div>
  )}
</section>

{/* Symbol Picker Modal */}
<SymbolPickerModal
  open={showSymbolPicker}
  onOpenChange={setShowSymbolPicker}
  userId={session?.user.id}
  onSaved={fetchWatchlist}
/>
```

---

## 🧪 Testing Checklist

### Local Testing

- [ ] `npm install` (if new dependencies added)
- [ ] `npm run dev`
- [ ] Navigate to http://localhost:3000/dashboard
- [ ] Click "Edit Watchlist" button
- [ ] Modal opens with available symbols
- [ ] Add symbols to watchlist (max 10)
- [ ] Remove symbols from watchlist
- [ ] Save watchlist
- [ ] Widgets render correctly
- [ ] Live prices update automatically
- [ ] Responsive on mobile/tablet

### Database Testing

- [ ] Check `user_watchlist` table in Supabase
- [ ] Verify positions (1-10)
- [ ] Test RLS (can't see other users' watchlists)
- [ ] Test constraints (duplicate symbol fails)

---

**Next:** [04_BACKEND_UPDATES.md](./04_BACKEND_UPDATES.md)
