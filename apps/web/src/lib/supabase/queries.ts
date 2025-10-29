import { createServerClient } from './server'

export interface Trade {
  id: string
  user_id: string
  symbol: string
  side: 'long' | 'short'
  entry_price: number
  exit_price?: number | null
  position_size: number
  stop_loss?: number | null
  take_profit?: number | null
  status: 'open' | 'closed' | 'cancelled'
  pnl?: number | null
  pnl_percentage?: number | null
  entry_time: string
  exit_time?: string | null
  notes?: string | null
  tags?: string[] | null
  created_at: string
  updated_at: string
}

export interface MarketData {
  id: string
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
  volume?: number
  timestamp: string
  created_at: string
}

export interface Profile {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  subscription_tier: 'free' | 'starter' | 'pro' | 'expert'
  created_at: string
  updated_at: string
}

/**
 * Fetch user trades
 */
export async function getUserTrades(userId: string, limit = 10) {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit)

  if (error) {
    console.error('Error fetching trades:', error)
    return []
  }

  return (data || []) as Trade[]
}

/**
 * Fetch user open trades
 */
export async function getOpenTrades(userId: string) {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('user_id', userId)
    .eq('status', 'open')
    .order('entry_time', { ascending: false })

  if (error) {
    console.error('Error fetching open trades:', error)
    return []
  }

  return (data || []) as Trade[]
}

/**
 * Calculate trade summary statistics
 */
export async function getTradeSummary(userId: string) {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('user_id', userId)
    .eq('status', 'closed')

  if (error) {
    console.error('Error fetching trade summary:', error)
    return {
      totalTrades: 0,
      winningTrades: 0,
      losingTrades: 0,
      winRate: 0,
      totalProfitLoss: 0,
      averageWin: 0,
      averageLoss: 0,
    }
  }

  const trades: any[] = data || []
  const totalTrades = trades.length
  const winningTrades = trades.filter(
    (t: any) => t.pnl && t.pnl > 0
  ).length
  const losingTrades = trades.filter(
    (t: any) => t.pnl && t.pnl < 0
  ).length
  const totalProfitLoss = trades.reduce(
    (sum: number, t: any) => sum + (t.pnl || 0),
    0
  )

  const wins = trades.filter((t: any) => t.pnl && t.pnl > 0)
  const losses = trades.filter((t: any) => t.pnl && t.pnl < 0)

  const averageWin =
    wins.length > 0
      ? wins.reduce((sum: number, t: any) => sum + (t.pnl || 0), 0) /
        wins.length
      : 0
  const averageLoss =
    losses.length > 0
      ? losses.reduce((sum: number, t: any) => sum + (t.pnl || 0), 0) /
        losses.length
      : 0

  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0

  return {
    totalTrades,
    winningTrades,
    losingTrades,
    winRate,
    totalProfitLoss,
    averageWin,
    averageLoss,
  }
}

/**
 * Fetch latest market data
 * Note: market_data table needs to be created in Supabase
 */
export async function getMarketData(symbols?: string[]) {
  // Market data table not yet implemented
  // Will be implemented in Phase 2
  return []
}

/**
 * Get user profile
 */
export async function getUserProfile(userId: string) {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single()

  if (error) {
    console.error('Error fetching profile:', error)
    return null
  }

  return data as Profile
}

/**
 * Create a new trade
 */
export async function createTrade(
  trade: Omit<Trade, 'id' | 'created_at' | 'updated_at'>
) {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('trades')
    .insert([trade])
    .select()
    .single()

  if (error) {
    console.error('Error creating trade:', error)
    throw new Error(error.message)
  }

  return data as Trade
}

/**
 * Update an existing trade
 */
export async function updateTrade(
  tradeId: string,
  updates: Partial<Omit<Trade, 'id' | 'user_id' | 'created_at' | 'updated_at'>>
) {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('trades')
    .update(updates)
    .eq('id', tradeId)
    .select()
    .single()

  if (error) {
    console.error('Error updating trade:', error)
    throw new Error(error.message)
  }

  return data as Trade
}

/**
 * Delete a trade
 */
export async function deleteTrade(tradeId: string) {
  const supabase = await createServerClient()

  const { error } = await supabase.from('trades').delete().eq('id', tradeId)

  if (error) {
    console.error('Error deleting trade:', error)
    throw new Error(error.message)
  }

  return true
}

/**
 * Get a single trade by ID
 */
export async function getTrade(tradeId: string) {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .eq('id', tradeId)
    .single()

  if (error) {
    console.error('Error fetching trade:', error)
    return null
  }

  return data as Trade
}

export interface TradeFilters {
  status?: 'open' | 'closed' | 'cancelled'
  side?: 'long' | 'short'
  symbol?: string
  startDate?: string
  endDate?: string
}

/**
 * Get filtered trades with pagination
 */
export async function getFilteredTrades(
  userId: string,
  filters: TradeFilters = {},
  page = 1,
  pageSize = 10
) {
  const supabase = await createServerClient()

  let query = supabase
    .from('trades')
    .select('*', { count: 'exact' })
    .eq('user_id', userId)

  // Apply filters
  if (filters.status) {
    query = query.eq('status', filters.status)
  }

  if (filters.side) {
    query = query.eq('side', filters.side)
  }

  if (filters.symbol) {
    query = query.eq('symbol', filters.symbol)
  }

  if (filters.startDate) {
    query = query.gte('entry_time', filters.startDate)
  }

  if (filters.endDate) {
    query = query.lte('entry_time', filters.endDate)
  }

  // Apply pagination
  const from = (page - 1) * pageSize
  const to = from + pageSize - 1

  const { data, error, count } = await query
    .order('entry_time', { ascending: false })
    .range(from, to)

  if (error) {
    console.error('Error fetching filtered trades:', error)
    return { trades: [], total: 0 }
  }

  return {
    trades: (data || []) as Trade[],
    total: count || 0,
  }
}

/**
 * Get unique symbols from user's trades
 */
export async function getUserSymbols(userId: string) {
  const supabase = await createServerClient()

  const { data, error } = await supabase
    .from('trades')
    .select('symbol')
    .eq('user_id', userId)

  if (error) {
    console.error('Error fetching symbols:', error)
    return []
  }

  // Extract unique symbols
  const symbols = [...new Set(data.map((t: any) => t.symbol))]
  return symbols
}

/**
 * Subscribe to real-time trade updates
 * Note: This is a client-side function, use in client components
 */
export function subscribeToTrades(
  userId: string,
  callback: (payload: any) => void
) {
  // This will be implemented on client side
  // Left as reference for future implementation
}
