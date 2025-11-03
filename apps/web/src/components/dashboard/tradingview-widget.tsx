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
    } catch {
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
