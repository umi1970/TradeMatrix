# Liquidity Alert System - Complete Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LIQUIDITY LEVEL ALERT SYSTEM                             │
│                     (5 Phase Implementation - COMPLETE)                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────┐     ┌───────────────────┐     ┌────────────────────┐
│   PHASE 1-2       │     │   PHASE 3          │     │   PHASE 4-5         │
│   Database        │────▶│   Alert Engine     │────▶│   Push Notification │
│   + Price Fetch   │     │   + Detection      │     │   + User Delivery   │
└───────────────────┘     └───────────────────┘     └────────────────────┘
```

## Detailed Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA INGESTION LAYER                               │
└─────────────────────────────────────────────────────────────────────────────┘

1. HISTORICAL DATA (Phase 1)
   ┌──────────────────┐
   │ EOD Data Fetcher │ ── Fetches daily OHLC from EODHD API
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Calculate Levels │ ── Calculates yesterday_high, yesterday_low, pivot
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ levels_daily     │ ── Stores computed liquidity levels
   └──────────────────┘


2. REALTIME PRICES (Phase 2)
   ┌──────────────────┐
   │ Price Fetcher    │ ── Fetches current prices (Finnhub + Alpha Vantage)
   │ (Celery Task)    │    Runs every 60 seconds
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ price_cache      │ ── Stores latest market prices
   └──────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                          ALERT DETECTION LAYER                               │
└─────────────────────────────────────────────────────────────────────────────┘

3. ALERT ENGINE (Phase 3)
   ┌──────────────────────────────────────────────────────────────┐
   │ LiquidityAlertEngine                                         │
   │ (Celery Task: check_liquidity_alerts)                       │
   │                                                              │
   │  1. Fetch user alerts from user_liquidity_alerts table      │
   │  2. Get current prices from price_cache                      │
   │  3. Get liquidity levels from levels_daily                   │
   │  4. Check if price crossed level (tolerance: 5 points)      │
   │  5. Prevent duplicate alerts (cooldown: 4 hours)            │
   │  6. Return triggered alerts                                  │
   └────────┬─────────────────────────────────────────────────────┘
            │
            ▼
   ┌──────────────────┐
   │ Triggered Alerts │ ── List of alerts that need notification
   └────────┬─────────┘
            │
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NOTIFICATION DELIVERY LAYER                           │
└─────────────────────────────────────────────────────────────────────────────┘

4. PUSH NOTIFICATION SERVICE (Phase 5)
   ┌──────────────────────────────────────────────────────────────┐
   │ PushNotificationService                                      │
   │                                                              │
   │  1. Get user subscriptions from user_push_subscriptions     │
   │  2. Format notification (title, body, data)                 │
   │  3. Send push via pywebpush (VAPID auth)                   │
   │  4. Handle invalid subscriptions (404/410)                  │
   │  5. Update last_used_at timestamp                           │
   └────────┬─────────────────────────────────────────────────────┘
            │
            ▼
   ┌──────────────────┐
   │ Web Push API     │ ── Browser push notification service
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Service Worker   │ ── Frontend receives and displays notification
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ User's Browser   │ ── User sees notification 🔔
   └──────────────────┘
```

## Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE TABLES                                 │
└─────────────────────────────────────────────────────────────────────────────┘

1. market_symbols
   ├── id (UUID)
   ├── symbol (TEXT) ── "DAX", "NASDAQ", "EURUSD"
   ├── name (TEXT)
   ├── asset_type (TEXT)
   └── active (BOOLEAN)

2. levels_daily
   ├── id (UUID)
   ├── trade_date (DATE)
   ├── symbol_id (UUID) ── FK to market_symbols
   ├── yesterday_high (DECIMAL)
   ├── yesterday_low (DECIMAL)
   ├── pivot (DECIMAL)
   └── calculated_at (TIMESTAMP)

3. price_cache
   ├── id (UUID)
   ├── symbol_id (UUID) ── FK to market_symbols
   ├── price (DECIMAL)
   ├── timestamp (TIMESTAMP)
   └── source (TEXT) ── "finnhub" or "alphavantage"

4. user_liquidity_alerts
   ├── id (UUID)
   ├── user_id (UUID) ── FK to auth.users
   ├── symbol_id (UUID) ── FK to market_symbols
   ├── level_type (TEXT) ── "yesterday_high", "yesterday_low", "pivot"
   ├── enabled (BOOLEAN)
   ├── last_triggered_at (TIMESTAMP)
   └── created_at (TIMESTAMP)

5. user_push_subscriptions
   ├── id (UUID)
   ├── user_id (UUID) ── FK to auth.users
   ├── endpoint (TEXT) ── Push subscription endpoint
   ├── p256dh (TEXT) ── Encryption key
   ├── auth (TEXT) ── Authentication key
   ├── created_at (TIMESTAMP)
   └── last_used_at (TIMESTAMP)
```

## Celery Tasks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CELERY BEAT SCHEDULE                              │
└─────────────────────────────────────────────────────────────────────────────┘

REALTIME TASKS (Every 60 seconds)
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  fetch_realtime_prices                                     │
│  ├── Fetch: DAX, NASDAQ, DOW (Finnhub)                   │
│  ├── Fetch: EURUSD, EURGBP (Alpha Vantage)               │
│  └── Update: price_cache table                            │
│                                                            │
│  check_liquidity_alerts                                    │
│  ├── Check: All user alerts vs current prices            │
│  ├── Detect: Level crosses (tolerance ±5 points)         │
│  ├── Filter: Cooldown period (4 hours)                   │
│  └── Send: Push notifications via PushNotificationService │
│                                                            │
└────────────────────────────────────────────────────────────┘

DAILY TASKS
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  fetch_eod_data (03:00 CET)                               │
│  ├── Fetch: Previous day's OHLC from EODHD               │
│  └── Store: Raw OHLC data                                 │
│                                                            │
│  calculate_liquidity_levels (03:30 CET)                   │
│  ├── Calculate: yesterday_high, yesterday_low            │
│  ├── Calculate: pivot points                              │
│  └── Update: levels_daily table                           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Notification Format

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NOTIFICATION EXAMPLES                                │
└─────────────────────────────────────────────────────────────────────────────┘

1. YESTERDAY HIGH (SHORT SETUP)
   ┌───────────────────────────────────────────┐
   │ 🔴 DAX - Yesterday High                  │
   ├───────────────────────────────────────────┤
   │ Consider: MR-01 (Reversal from           │
   │           Yesterday High)                 │
   │                                           │
   │ Level:   24,215.38                       │
   │ Current: 24,214.89                       │
   │                                           │
   │ Setup Type: SHORT                         │
   └───────────────────────────────────────────┘

2. YESTERDAY LOW (LONG SETUP)
   ┌───────────────────────────────────────────┐
   │ 🟢 DAX - Yesterday Low                   │
   ├───────────────────────────────────────────┤
   │ Consider: MR-04 (Reversal from           │
   │           Yesterday Low)                  │
   │                                           │
   │ Level:   24,015.12                       │
   │ Current: 24,014.67                       │
   │                                           │
   │ Setup Type: LONG                          │
   └───────────────────────────────────────────┘

3. PIVOT POINT
   ┌───────────────────────────────────────────┐
   │ 🟡 DAX - Pivot Point                     │
   ├───────────────────────────────────────────┤
   │ Consider: Pivot Bounce/Break Strategy    │
   │                                           │
   │ Level:   24,115.25                       │
   │ Current: 24,114.89                       │
   │                                           │
   │ Monitor for reaction                      │
   └───────────────────────────────────────────┘
```

## API Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL API CALLS                                 │
└─────────────────────────────────────────────────────────────────────────────┘

PRICE SOURCES
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Finnhub API (Indices)                                     │
│  ├── GET /quote                                            │
│  ├── Symbols: DAX, NASDAQ, DOW                            │
│  ├── Returns: { c: current_price, ... }                   │
│  └── Rate Limit: 60 calls/minute                          │
│                                                            │
│  Alpha Vantage API (Forex)                                 │
│  ├── GET /query?function=CURRENCY_EXCHANGE_RATE           │
│  ├── Pairs: EURUSD, EURGBP                                │
│  ├── Returns: { "Realtime Currency Exchange Rate": ... }  │
│  └── Rate Limit: 25 calls/day (free tier)                 │
│                                                            │
│  EODHD API (Historical Data)                               │
│  ├── GET /eod/{symbol}                                     │
│  ├── Returns: OHLC data                                    │
│  └── Rate Limit: 100,000 calls/day                        │
│                                                            │
└────────────────────────────────────────────────────────────┘

PUSH NOTIFICATION
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Web Push API (Browser-specific)                          │
│  ├── POST {subscription.endpoint}                         │
│  ├── Headers: VAPID Authorization                         │
│  ├── Body: Encrypted notification payload                 │
│  └── Rate Limit: Varies by browser (typically 1000s/hour) │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Environment Variables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REQUIRED CONFIGURATION                               │
└─────────────────────────────────────────────────────────────────────────────┘

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0

# API Keys
FINNHUB_API_KEY=your-finnhub-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
EODHD_API_KEY=your-eodhd-key

# VAPID (Push Notifications)
VAPID_PUBLIC_KEY=BNWo7JkF8xQ3...
VAPID_PRIVATE_KEY=aGx1M2N4V5bZ...
VAPID_SUBJECT=mailto:info@tradematrix.ai
```

## Component Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PYTHON DEPENDENCIES                                │
└─────────────────────────────────────────────────────────────────────────────┘

Core:
├── celery==5.3.4           ── Task queue
├── redis==5.0.1            ── Message broker
├── supabase==2.3.3         ── Database client
└── python-dotenv==1.0.0    ── Environment config

APIs:
├── requests>=2.31.0        ── HTTP client
└── httpx==0.25.2           ── Async HTTP (supabase dependency)

Push Notifications:
├── pywebpush>=1.14.0       ── Web Push protocol
└── py-vapid>=1.9.0         ── VAPID authentication

Data:
├── pandas==2.1.4           ── Data processing
└── pyyaml==6.0.1           ── Config files
```

---

**Last Updated:** 2025-11-01
**Status:** COMPLETE ✅
