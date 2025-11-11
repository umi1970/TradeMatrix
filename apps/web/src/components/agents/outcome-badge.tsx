'use client'

import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, XCircle, Clock } from 'lucide-react'

interface OutcomeBadgeProps {
  outcome: string | null | undefined
  pnl?: number | null
  size?: 'sm' | 'default' | 'lg'
}

export function OutcomeBadge({ outcome, pnl, size = 'default' }: OutcomeBadgeProps) {
  if (!outcome) return null

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    default: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  }

  const getOutcomeConfig = (outcome: string) => {
    switch (outcome) {
      case 'win':
        return {
          label: 'WIN',
          icon: <TrendingUp className="h-3 w-3" />,
          className: 'bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/50 font-bold',
        }
      case 'loss':
        return {
          label: 'LOSS',
          icon: <TrendingDown className="h-3 w-3" />,
          className: 'bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/50 font-bold',
        }
      case 'invalidated':
        return {
          label: 'INVALIDATED',
          icon: <XCircle className="h-3 w-3" />,
          className: 'bg-orange-500/20 text-orange-700 dark:text-orange-400 border-orange-500/50 font-semibold',
        }
      case 'missed':
        return {
          label: 'MISSED',
          icon: <Clock className="h-3 w-3" />,
          className: 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 border-yellow-500/50 font-semibold',
        }
      default:
        return {
          label: outcome.toUpperCase(),
          icon: null,
          className: 'bg-gray-500/20 text-gray-700 dark:text-gray-400 border-gray-500/50',
        }
    }
  }

  const config = getOutcomeConfig(outcome)

  return (
    <Badge variant="outline" className={`${config.className} ${sizeClasses[size]} gap-1.5 font-mono`}>
      {config.icon}
      <span>{config.label}</span>
      {pnl !== null && pnl !== undefined && (
        <span className="ml-1 font-bold">
          {pnl > 0 ? '+' : ''}{pnl.toFixed(2)}%
        </span>
      )}
    </Badge>
  )
}
