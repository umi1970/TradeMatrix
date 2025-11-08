/**
 * Chart-related TypeScript interfaces for TradeMatrix.ai
 */

export interface ChartConfig {
  timeframes: string[]
  indicators: string[]
  default_timeframe: string
  theme?: 'dark' | 'light'
}

export interface MarketSymbol {
  id: string
  symbol: string
  alias: string | null
  chart_img_symbol: string | null
  chart_enabled: boolean
  chart_config: ChartConfig | null
  created_at?: string
  updated_at?: string
}

export interface ChartSnapshot {
  id: string
  symbol_id: string
  timeframe: string
  chart_url: string
  trigger_type: string
  generated_at: string
  expires_at: string
  metadata: Record<string, unknown> | null
  symbol?: MarketSymbol
}

export interface ChartGenerationParams {
  symbol_id: string
  timeframe: string
}

export interface ChartGenerationResponse {
  chart_url: string
  snapshot_id: string
  expires_at: string
}

export interface ChartUsageData {
  total_requests: number
  limit: number
  remaining: number
  percentage: number
  reset_at: string
}

// Available timeframes
export const TIMEFRAMES = [
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '1W', label: '1 Week' },
] as const

export type TimeframeValue = typeof TIMEFRAMES[number]['value']

// Available indicators
export const INDICATORS = [
  {
    value: 'EMA_20',
    label: 'EMA 20',
    group: 'Trend'
  },
  {
    value: 'EMA_50',
    label: 'EMA 50',
    group: 'Trend'
  },
  {
    value: 'EMA_200',
    label: 'EMA 200',
    group: 'Trend'
  },
  {
    value: 'SMA_20',
    label: 'SMA 20',
    group: 'Trend'
  },
  {
    value: 'SMA_50',
    label: 'SMA 50',
    group: 'Trend'
  },
  {
    value: 'RSI',
    label: 'RSI (14)',
    group: 'Momentum'
  },
  {
    value: 'MACD',
    label: 'MACD',
    group: 'Momentum'
  },
  {
    value: 'Stochastic',
    label: 'Stochastic',
    group: 'Momentum'
  },
  {
    value: 'Volume',
    label: 'Volume',
    group: 'Volume'
  },
  {
    value: 'BB',
    label: 'Bollinger Bands',
    group: 'Volatility'
  },
  {
    value: 'ATR',
    label: 'ATR',
    group: 'Volatility'
  },
] as const

export type IndicatorValue = typeof INDICATORS[number]['value']

// Chart themes
export const CHART_THEMES = [
  { value: 'dark', label: 'Dark' },
  { value: 'light', label: 'Light' },
] as const

export type ChartTheme = typeof CHART_THEMES[number]['value']

// Trigger types for chart snapshots
export const TRIGGER_TYPES = [
  { value: 'manual', label: 'Manual' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'alert', label: 'Alert Triggered' },
] as const

export type TriggerType = typeof TRIGGER_TYPES[number]['value']
