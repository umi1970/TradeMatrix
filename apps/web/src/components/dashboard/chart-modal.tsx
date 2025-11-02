'use client'

import { useEffect, useRef, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface ChartModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  symbol: string
  symbolName: string
  tvSymbol: string
}

export function ChartModal({ open, onOpenChange, symbol, symbolName, tvSymbol }: ChartModalProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetRef = useRef<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!open) return

    setIsLoading(true)

    // Wait for dialog to be fully rendered
    const timer = setTimeout(() => {
      if (!containerRef.current) return

      // Clear any previous content
      containerRef.current.innerHTML = ''

      // Check if TradingView is already loaded
      if (typeof (window as any).TradingView !== 'undefined') {
        initWidget()
      } else {
        // Load TradingView script
        const script = document.createElement('script')
        script.src = 'https://s3.tradingview.com/tv.js'
        script.async = true
        script.onload = () => {
          initWidget()
        }
        script.onerror = () => {
          console.error('Failed to load TradingView script')
          setIsLoading(false)
        }
        document.head.appendChild(script)
      }
    }, 100)

    function initWidget() {
      if (!containerRef.current) return

      try {
        widgetRef.current = new (window as any).TradingView.widget({
          container_id: containerRef.current.id,
          autosize: true,
          symbol: tvSymbol,
          interval: '5',
          timezone: 'Etc/UTC',
          theme: 'dark',
          style: '1',
          locale: 'en',
          toolbar_bg: '#1a1a1a',
          enable_publishing: false,
          hide_side_toolbar: false,
          allow_symbol_change: true,
          save_image: false,
          studies: [
            'MASimple@tv-basicstudies',
            'RSI@tv-basicstudies'
          ]
        })
        setIsLoading(false)
      } catch (error) {
        console.error('Failed to initialize TradingView widget:', error)
        setIsLoading(false)
      }
    }

    return () => {
      clearTimeout(timer)
      if (widgetRef.current && widgetRef.current.remove) {
        widgetRef.current.remove()
      }
    }
  }, [open, tvSymbol])

  const containerId = `tradingview_${symbol.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}`

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>{symbolName} ({symbol})</DialogTitle>
        </DialogHeader>
        <div className="w-full h-[500px] relative">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
              <div className="text-gray-400">Loading chart...</div>
            </div>
          )}
          <div
            id={containerId}
            ref={containerRef}
            className="w-full h-full"
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
