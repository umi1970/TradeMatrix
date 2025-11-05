'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { SettingsIcon } from 'lucide-react'
import { ChartConfigModal } from './ChartConfigModal'
import type { ChartConfig } from '@/types/chart'

interface ChartConfigButtonProps {
  symbol: {
    id: string
    symbol: string
    name: string
    chart_config?: ChartConfig | null
  }
  onSave?: () => void
}

export function ChartConfigButton({ symbol, onSave }: ChartConfigButtonProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleSave = (config: ChartConfig) => {
    setIsOpen(false)
    onSave?.()
  }

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <SettingsIcon className="h-4 w-4 mr-2" />
        Chart Config
      </Button>

      <ChartConfigModal
        symbol={symbol}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onSave={handleSave}
      />
    </>
  )
}
