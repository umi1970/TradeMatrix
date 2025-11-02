'use client'

interface MarketSparklineProps {
  symbol: string
  symbolId?: string
  trend?: 'up' | 'down' | 'neutral'
}

// Map our symbols to TradingView symbols
const symbolMapping: Record<string, string> = {
  '^GDAXI': 'XETR:DAX',
  '^NDX': 'NASDAQ:NDX',
  '^DJI': 'DJ:DJI',
  'EURUSD': 'FX:EURUSD',
  'EURGBP': 'FX:EURGBP',
  'GBPUSD': 'FX:GBPUSD',
}

export function MarketSparkline({ symbol, symbolId, trend = 'neutral' }: MarketSparklineProps) {
  const tvSymbol = symbolMapping[symbol] || symbol

  // TradingView Mini Chart Widget
  // Using Advanced Chart widget in mini mode for sparkline-like appearance
  const widgetSrc = `https://s.tradingview.com/embed-widget/symbol-overview/?symbol=${encodeURIComponent(tvSymbol)}&interval=5&autosize=true&hidelegend=true&hideaxes=true&hidesidetoolbar=true&theme=dark&style=3&timezone=Etc%2FUTC&withdateranges=false&showpopupbutton=false&studies=%5B%5D&locale=en`

  return (
    <div className="relative w-20 h-10 overflow-hidden rounded">
      <iframe
        src={widgetSrc}
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
          margin: 0,
          padding: 0,
        }}
        scrolling="no"
        frameBorder="0"
        allowTransparency={true}
      />
    </div>
  )
}
