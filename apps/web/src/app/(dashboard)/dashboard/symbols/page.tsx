'use client'

import { useState } from 'react'
import { Pencil, BarChart3, Search, Filter, Check, X } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { SymbolEditModal } from '@/components/dashboard/symbol-edit-modal'
import { ChartGeneratorWidget } from '@/components/dashboard/chart-generator-widget'
import { ChartApiUsage } from '@/components/dashboard/chart-api-usage'
import { ChartSnapshotsGallery } from '@/components/dashboard/chart-snapshots-gallery'
import { useMarketSymbols } from '@/hooks/useMarketSymbols'
import type { MarketSymbol } from '@/types/chart'

export default function SymbolsPage() {
  const { data: symbols = [], isLoading } = useMarketSymbols()

  const [searchQuery, setSearchQuery] = useState('')
  const [chartEnabledFilter, setChartEnabledFilter] = useState<string>('all')
  const [editingSymbol, setEditingSymbol] = useState<MarketSymbol | null>(null)
  const [generatingSymbol, setGeneratingSymbol] = useState<MarketSymbol | null>(null)

  // Filter symbols
  const filteredSymbols = symbols.filter((symbol) => {
    const matchesSearch =
      symbol.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      symbol.name.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesChartFilter =
      chartEnabledFilter === 'all' ||
      (chartEnabledFilter === 'enabled' && symbol.chart_enabled) ||
      (chartEnabledFilter === 'disabled' && !symbol.chart_enabled)

    return matchesSearch && matchesChartFilter
  })

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Market Symbols</h1>
          <p className="text-muted-foreground">
            Manage chart generation settings for market symbols
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search symbols..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Chart Enabled Filter */}
            <div className="w-full md:w-[200px]">
              <Select value={chartEnabledFilter} onValueChange={setChartEnabledFilter}>
                <SelectTrigger>
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Symbols</SelectItem>
                  <SelectItem value="enabled">Chart Enabled</SelectItem>
                  <SelectItem value="disabled">Chart Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Results count */}
          <div className="mt-4 text-sm text-muted-foreground">
            Showing {filteredSymbols.length} of {symbols.length} symbols
          </div>
        </CardContent>
      </Card>

      {/* Symbols Table */}
      <Card>
        <CardHeader>
          <CardTitle>Symbols</CardTitle>
          <CardDescription>
            Configure chart generation settings for each symbol
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Chart Enabled</TableHead>
                    <TableHead>TradingView Symbol</TableHead>
                    <TableHead>Timeframes</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSymbols.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                        No symbols found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredSymbols.map((symbol) => (
                      <TableRow key={symbol.id}>
                        <TableCell className="font-medium">{symbol.symbol}</TableCell>
                        <TableCell>{symbol.name}</TableCell>
                        <TableCell>
                          {symbol.chart_enabled ? (
                            <Badge variant="default" className="gap-1">
                              <Check className="h-3 w-3" />
                              Enabled
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="gap-1">
                              <X className="h-3 w-3" />
                              Disabled
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <code className="text-xs bg-muted px-2 py-1 rounded">
                            {symbol.chart_img_symbol || '-'}
                          </code>
                        </TableCell>
                        <TableCell>
                          {symbol.chart_config?.timeframes ? (
                            <div className="flex flex-wrap gap-1">
                              {symbol.chart_config.timeframes.slice(0, 3).map((tf) => (
                                <Badge key={tf} variant="outline" className="text-xs">
                                  {tf}
                                </Badge>
                              ))}
                              {symbol.chart_config.timeframes.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{symbol.chart_config.timeframes.length - 3}
                                </Badge>
                              )}
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-sm">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setEditingSymbol(symbol)}
                            >
                              <Pencil className="h-4 w-4 mr-2" />
                              Edit
                            </Button>
                            {symbol.chart_enabled && (
                              <Button
                                variant="default"
                                size="sm"
                                onClick={() => setGeneratingSymbol(symbol)}
                              >
                                <BarChart3 className="h-4 w-4 mr-2" />
                                Generate
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Chart API Usage */}
      <ChartApiUsage />

      {/* Chart Snapshots Gallery */}
      <ChartSnapshotsGallery limit={12} />

      {/* Edit Modal */}
      <SymbolEditModal
        symbol={editingSymbol}
        open={!!editingSymbol}
        onOpenChange={(open) => !open && setEditingSymbol(null)}
      />

      {/* Chart Generator Modal */}
      {generatingSymbol && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative w-full max-w-4xl">
            <Button
              variant="outline"
              size="icon"
              className="absolute -top-12 right-0"
              onClick={() => setGeneratingSymbol(null)}
            >
              <X className="h-4 w-4" />
            </Button>
            <ChartGeneratorWidget symbol={generatingSymbol} />
          </div>
        </div>
      )}
    </div>
  )
}
