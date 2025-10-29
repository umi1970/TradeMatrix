'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, Edit, Trash2, Eye, ArrowUpDown } from 'lucide-react'
import type { Trade } from '@/lib/supabase/queries'

interface TradesTableProps {
  trades: Trade[]
  onEdit: (trade: Trade) => void
  onDelete: (tradeId: string) => void
  onView: (trade: Trade) => void
}

type SortField = 'entry_time' | 'symbol' | 'side' | 'pnl' | 'status'
type SortOrder = 'asc' | 'desc'

export function TradesTable({
  trades,
  onEdit,
  onDelete,
  onView,
}: TradesTableProps) {
  const [sortField, setSortField] = useState<SortField>('entry_time')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('asc')
    }
  }

  const sortedTrades = [...trades].sort((a, b) => {
    let aValue: any
    let bValue: any

    switch (sortField) {
      case 'entry_time':
        aValue = new Date(a.entry_time).getTime()
        bValue = new Date(b.entry_time).getTime()
        break
      case 'symbol':
        aValue = a.symbol
        bValue = b.symbol
        break
      case 'side':
        aValue = a.side
        bValue = b.side
        break
      case 'pnl':
        aValue = a.pnl || 0
        bValue = b.pnl || 0
        break
      case 'status':
        aValue = a.status
        bValue = b.status
        break
      default:
        return 0
    }

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open':
        return <Badge className="bg-blue-500">Open</Badge>
      case 'closed':
        return <Badge className="bg-green-500">Closed</Badge>
      case 'cancelled':
        return <Badge variant="secondary">Cancelled</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const getSideBadge = (side: string) => {
    return side === 'long' ? (
      <Badge className="bg-green-600">Long</Badge>
    ) : (
      <Badge className="bg-red-600">Short</Badge>
    )
  }

  const formatPnL = (pnl: number | null, percentage: number | null) => {
    if (pnl === null) return '-'

    const isPositive = pnl >= 0
    const color = isPositive ? 'text-green-600' : 'text-red-600'

    return (
      <span className={color}>
        {isPositive ? '+' : ''}
        {pnl.toFixed(2)}
        {percentage !== null && (
          <span className="text-xs ml-1">({percentage.toFixed(2)}%)</span>
        )}
      </span>
    )
  }

  const SortButton = ({
    field,
    children,
  }: {
    field: SortField
    children: React.ReactNode
  }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center space-x-1 hover:text-foreground transition-colors"
    >
      <span>{children}</span>
      <ArrowUpDown className="h-3 w-3" />
    </button>
  )

  if (trades.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">
          No trades found. Try adjusting your filters.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <SortButton field="entry_time">Date</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="symbol">Symbol</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="side">Side</SortButton>
            </TableHead>
            <TableHead className="text-right">Entry</TableHead>
            <TableHead className="text-right">Exit</TableHead>
            <TableHead className="text-right">Size</TableHead>
            <TableHead className="text-right">
              <SortButton field="pnl">P&L</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="status">Status</SortButton>
            </TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedTrades.map((trade) => (
            <TableRow key={trade.id}>
              <TableCell className="font-medium">
                {format(new Date(trade.entry_time), 'MMM dd, yyyy')}
                <div className="text-xs text-muted-foreground">
                  {format(new Date(trade.entry_time), 'HH:mm')}
                </div>
              </TableCell>
              <TableCell className="font-medium">{trade.symbol}</TableCell>
              <TableCell>{getSideBadge(trade.side)}</TableCell>
              <TableCell className="text-right">
                {trade.entry_price.toFixed(2)}
              </TableCell>
              <TableCell className="text-right">
                {trade.exit_price ? trade.exit_price.toFixed(2) : '-'}
              </TableCell>
              <TableCell className="text-right">
                {trade.position_size.toFixed(2)}
              </TableCell>
              <TableCell className="text-right">
                {formatPnL(trade.pnl || null, trade.pnl_percentage || null)}
              </TableCell>
              <TableCell>{getStatusBadge(trade.status)}</TableCell>
              <TableCell className="text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="h-8 w-8 p-0">
                      <span className="sr-only">Open menu</span>
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                    <DropdownMenuItem onClick={() => onView(trade)}>
                      <Eye className="mr-2 h-4 w-4" />
                      View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEdit(trade)}>
                      <Edit className="mr-2 h-4 w-4" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => onDelete(trade.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
