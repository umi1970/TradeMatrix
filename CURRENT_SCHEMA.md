# TradeMatrix Database Schema - COMPLETE

## Core Tables (von Migrations verifiziert)

### 1. USER & AUTH
- **profiles** (001)
  - id, email, full_name, avatar_url
  - subscription_tier, subscription_status, stripe_customer_id, stripe_subscription_id, stripe_price_id
  
- **subscriptions** (001)
  - Stripe webhook events

- **ai_usage_log** (025)
  - Track OpenAI API usage & costs

### 2. MARKET DATA
- **market_symbols** (003) - PRIMARY SYMBOL TABLE
  - id, vendor, symbol, alias, tick_size, timezone, active
  - api_symbol (024) - API format (^GDAXI, EUR/USD)
  - chart_img_symbol (024) - TradingView format (XETR:DAX)
  - chart_enabled, chart_config (024) - chart-img.com config
  - tv_symbol (027) - TradingView widget format

- **current_prices** (009)
  - Latest prices, updated every 60s
  - FK: symbol_id → market_symbols (024)

- **ohlc** (003)
  - Historical OHLC candles
  - FK: symbol_id → market_symbols

- **eod_data** (010)
  - End-of-day data (stooq/yahoo)
  - FK: symbol_id → symbols (DEPRECATED)

- **eod_levels** (010)
  - Yesterday High/Low, Pivot Points
  - FK: symbol_id → symbols (DEPRECATED)

### 3. SETUPS & SIGNALS
- **setups** (003) ⭐ WICHTIG!
  ```sql
  id UUID PRIMARY KEY
  user_id UUID
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ
  module TEXT -- 'morning' | 'usopen'
  symbol_id UUID → market_symbols
  strategy TEXT -- 'asia_sweep', 'y_low_rebound', 'orb'
  side TEXT -- 'long' | 'short'
  entry_price NUMERIC
  stop_loss NUMERIC
  take_profit NUMERIC
  confidence NUMERIC (0.0-1.0)
  status TEXT -- 'pending' | 'active' | 'invalid' | 'filled' | 'cancelled'
  payload JSONB -- Custom data
  ```

- **signals** (005)
  - Entry/exit signals from SignalBot
  - FK: symbol_id → market_symbols, setup_id → setups

- **levels_daily** (003)
  - Daily pivot points

### 4. CHART ANALYSIS
- **chart_analyses** (006)
  - AI pattern analysis from ChartWatcher
  - FK: symbol_id → market_symbols

- **chart_snapshots** (020)
  - Generated charts from chart-img.com
  - FK: symbol_id → market_symbols (024)

### 5. ALERTS
- **alerts** (012)
  - Liquidity level alerts
  - FK: symbol_id → market_symbols (024a)

- **alert_subscriptions** (012)
  - User alert preferences
  - FK: symbol_id → market_symbols (024a)

- **user_push_subscriptions** (012)
  - Browser push subscriptions

- **user_watchlist** (018)
  - User's watched symbols
  - FK: symbol_id → market_symbols (024a)

### 6. TRADING JOURNAL
- **trades** (001)
  - Manual trades

- **trade_decisions** (019)
  - Decisions from TradeDecisionEngine

- **journal_entries** (019)
  - Trading journal

- **report_queue** (019)
  - Queue for JournalBot

### 7. REPORTS
- **reports** (001, 007, 015)
  - Daily/weekly/monthly reports
  - report_date, file_url_docx, metrics

- **agent_logs** (001, 004)
  - AI agent execution logs

- **eod_fetch_log** (010)
  - EOD data fetch audit log

## CRITICAL FINDINGS:

### ❌ Was NICHT existiert in `setups`:
- entry_hit (boolean)
- entry_hit_at (timestamp)
- sl_hit_at (timestamp)
- tp_hit_at (timestamp)
- outcome (text)
- pnl_percent (numeric)
- last_checked_at (timestamp)
- last_price (numeric)

### ✅ Was existiert:
- status: 'pending' | 'active' | 'invalid' | 'filled' | 'cancelled'
- payload: JSONB (für custom data)

### 🔴 Deprecated Tables:
- `symbols` - Deleted in Migration 024
- `price_cache` - Deleted in Migration 024

