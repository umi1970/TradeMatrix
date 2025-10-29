'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import type { Trade } from '@/lib/supabase/queries-client'

interface TradeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  trade?: Trade | null
  userId: string
  onSave: (trade: Partial<Trade>) => Promise<void>
}

interface TradeFormData {
  symbol: string
  side: 'long' | 'short'
  entry_price: string
  exit_price: string
  position_size: string
  stop_loss: string
  take_profit: string
  status: 'open' | 'closed' | 'cancelled'
  notes: string
}

const initialFormData: TradeFormData = {
  symbol: '',
  side: 'long',
  entry_price: '',
  exit_price: '',
  position_size: '',
  stop_loss: '',
  take_profit: '',
  status: 'open',
  notes: '',
}

export function TradeDialog({
  open,
  onOpenChange,
  trade,
  userId,
  onSave,
}: TradeDialogProps) {
  const { toast } = useToast()
  const [formData, setFormData] = useState<TradeFormData>(initialFormData)
  const [isLoading, setIsLoading] = useState(false)

  // Populate form when editing
  useEffect(() => {
    if (trade) {
      setFormData({
        symbol: trade.symbol,
        side: trade.side,
        entry_price: trade.entry_price.toString(),
        exit_price: trade.exit_price?.toString() || '',
        position_size: trade.position_size.toString(),
        stop_loss: trade.stop_loss?.toString() || '',
        take_profit: trade.take_profit?.toString() || '',
        status: trade.status,
        notes: trade.notes || '',
      })
    } else {
      setFormData(initialFormData)
    }
  }, [trade, open])

  const handleChange = (field: keyof TradeFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const calculatePnL = (
    side: 'long' | 'short',
    entryPrice: number,
    exitPrice: number,
    positionSize: number
  ) => {
    if (side === 'long') {
      return (exitPrice - entryPrice) * positionSize
    } else {
      return (entryPrice - exitPrice) * positionSize
    }
  }

  const validateForm = (): string | null => {
    if (!formData.symbol.trim()) return 'Symbol is required'
    if (!formData.entry_price || parseFloat(formData.entry_price) <= 0)
      return 'Valid entry price is required'
    if (!formData.position_size || parseFloat(formData.position_size) <= 0)
      return 'Valid position size is required'

    // If status is closed, exit price is required
    if (formData.status === 'closed') {
      if (!formData.exit_price || parseFloat(formData.exit_price) <= 0) {
        return 'Exit price is required for closed trades'
      }
    }

    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const validationError = validateForm()
    if (validationError) {
      toast({
        title: 'Validation Error',
        description: validationError,
        variant: 'destructive',
      })
      return
    }

    setIsLoading(true)

    try {
      const entryPrice = parseFloat(formData.entry_price)
      const exitPrice = formData.exit_price
        ? parseFloat(formData.exit_price)
        : null
      const positionSize = parseFloat(formData.position_size)
      const stopLoss = formData.stop_loss ? parseFloat(formData.stop_loss) : null
      const takeProfit = formData.take_profit
        ? parseFloat(formData.take_profit)
        : null

      // Calculate P&L if exit price exists
      let pnl = null
      let pnlPercentage = null
      if (exitPrice !== null && formData.status === 'closed') {
        pnl = calculatePnL(formData.side, entryPrice, exitPrice, positionSize)
        pnlPercentage = (pnl / (entryPrice * positionSize)) * 100
      }

      const tradeData: Partial<Trade> = {
        user_id: userId,
        symbol: formData.symbol.toUpperCase().trim(),
        side: formData.side,
        entry_price: entryPrice,
        exit_price: exitPrice,
        position_size: positionSize,
        stop_loss: stopLoss,
        take_profit: takeProfit,
        status: formData.status,
        notes: formData.notes.trim() || null,
        pnl,
        pnl_percentage: pnlPercentage,
      }

      // If it's a closed trade, set exit_time
      if (formData.status === 'closed' && !trade?.exit_time) {
        tradeData.exit_time = new Date().toISOString()
      }

      await onSave(tradeData)

      toast({
        title: 'Success',
        description: `Trade ${trade ? 'updated' : 'created'} successfully`,
      })

      onOpenChange(false)
      setFormData(initialFormData)
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save trade',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>{trade ? 'Edit Trade' : 'Create New Trade'}</DialogTitle>
          <DialogDescription>
            {trade
              ? 'Update the trade details below.'
              : 'Enter the details for your new trade.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {/* Symbol and Side */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="symbol">Symbol *</Label>
                <Input
                  id="symbol"
                  placeholder="e.g., DAX, NASDAQ"
                  value={formData.symbol}
                  onChange={(e) => handleChange('symbol', e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="side">Side *</Label>
                <Select
                  value={formData.side}
                  onValueChange={(value: string) =>
                    handleChange('side', value as 'long' | 'short')
                  }
                >
                  <SelectTrigger id="side">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="long">Long</SelectItem>
                    <SelectItem value="short">Short</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Entry and Exit Price */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="entry_price">Entry Price *</Label>
                <Input
                  id="entry_price"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.entry_price}
                  onChange={(e) => handleChange('entry_price', e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="exit_price">Exit Price</Label>
                <Input
                  id="exit_price"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.exit_price}
                  onChange={(e) => handleChange('exit_price', e.target.value)}
                />
              </div>
            </div>

            {/* Position Size and Status */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="position_size">Position Size *</Label>
                <Input
                  id="position_size"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.position_size}
                  onChange={(e) => handleChange('position_size', e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="status">Status *</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value: string) =>
                    handleChange(
                      'status',
                      value as 'open' | 'closed' | 'cancelled'
                    )
                  }
                >
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Stop Loss and Take Profit */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="stop_loss">Stop Loss</Label>
                <Input
                  id="stop_loss"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.stop_loss}
                  onChange={(e) => handleChange('stop_loss', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="take_profit">Take Profit</Label>
                <Input
                  id="take_profit"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.take_profit}
                  onChange={(e) => handleChange('take_profit', e.target.value)}
                />
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Input
                id="notes"
                placeholder="Optional trade notes..."
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : trade ? 'Update Trade' : 'Create Trade'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
