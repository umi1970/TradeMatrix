# Architecture: TradingView Watchlist (Hybrid Approach)

**Last Updated:** 2025-11-03

---

## 🎯 Design Decision: Hybrid Approach

### Why NOT WebSocket?

**Original Plan (Rejected):**
```
Browser → Backend WebSocket Server → Twelvedata WebSocket (8 connections)
```

**Problems:**
- ❌ **Complex**: WebSocket server, connection management, broadcasting
- ❌ **Costly**: Twelvedata $29/mo for only 8 symbols
- ❌ **Limited**: Max 8 live symbols, others need HTTP fallback anyway
- ❌ **Development Time**: 2-3 days implementation

**Chosen Solution (Hybrid):**
```
Browser → TradingView Widgets (live data, free)
         ↓
Hetzner Backend (only for alerts, HTTP polling)
```

**Benefits:**
- ✅ **Simple**: TradingView handles all live data
- ✅ **Free**: No API costs for display
- ✅ **Scalable**: Unlimited symbols
- ✅ **Fast**: ~6 hours implementation

---

## 🏗️ System Architecture

### Component Overview

```
┌───────────────────────────────────────────────────────────┐
│                    Browser (Next.js)                      │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │ Dashboard Page                                  │     │
│  │                                                 │     │
│  │  1. Fetch user_watchlist from Supabase         │     │
│  │  2. Render TradingView Widgets (max 10)        │     │
│  │  3. Widgets auto-fetch live prices             │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │ Symbol Picker Modal                             │     │
│  │                                                 │     │
│  │  • Search symbols                               │     │
│  │  • Add/Remove (max 10)                          │     │
│  │  • Drag & Drop reordering                       │     │
│  │  • Save to Supabase                             │     │
│  └─────────────────────────────────────────────────┘     │
└───────────────┬───────────────────────────────────────────┘
                │
                │ HTTPS (read/write)
                ↓
┌───────────────────────────────────────────────────────────┐
│                    Supabase (PostgreSQL)                  │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │ user_watchlist                                  │     │
│  │ ────────────────────────────────────────────    │     │
│  │ id         | UUID                               │     │
│  │ user_id    | UUID (FK → auth.users)             │     │
│  │ symbol_id  | UUID (FK → symbols)                │     │
│  │ position   | INT (1-10)                         │     │
│  │ created_at | TIMESTAMPTZ                        │     │
│  │                                                 │     │
│  │ RLS: auth.uid() = user_id                       │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │ symbols                                         │     │
│  │ ────────────────────────────────────────────    │     │
│  │ id         | UUID                               │     │
│  │ symbol     | TEXT (^GDAXI, EURUSD, etc.)        │     │
│  │ name       | TEXT (DAX Performance Index)       │     │
│  │ tv_symbol  | TEXT (XETR:DAX) ← NEW!             │     │
│  │ type       | TEXT (index, forex, stock)         │     │
│  │ is_active  | BOOLEAN                            │     │
│  └─────────────────────────────────────────────────┘     │
└───────────────┬───────────────────────────────────────────┘
                │
                │ (Only for Alert System)
                ↓
┌───────────────────────────────────────────────────────────┐
│         Hetzner Server (135.181.195.241)                  │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │ Celery Beat (60s interval)                      │     │
│  │                                                 │     │
│  │  1. Fetch all unique symbols from               │     │
│  │     user_watchlist (dynamic!)                   │     │
│  │  2. Trigger price fetch task                    │     │
│  └───────────────┬─────────────────────────────────┘     │
│                  │                                        │
│                  ↓                                        │
│  ┌─────────────────────────────────────────────────┐     │
│  │ Celery Worker (Hybrid Price Fetcher)           │     │
│  │                                                 │     │
│  │  Indices (^GDAXI, ^NDX, ^DJI):                  │     │
│  │  → yfinance HTTP (free, accurate)               │     │
│  │                                                 │     │
│  │  Forex (EURUSD, EURGBP, etc.):                  │     │
│  │  → Twelvedata HTTP (not WebSocket!)             │     │
│  │                                                 │     │
│  │  Updates:                                       │     │
│  │  1. Supabase price_cache                        │     │
│  │  2. Check liquidity alerts                      │     │
│  │  3. Send push notifications                     │     │
│  └─────────────────────────────────────────────────┘     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │ Redis 7-alpine                                  │     │
│  │ • Celery broker                                 │     │
│  │ • Result backend                                │     │
│  └─────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

### 1. User Customizes Watchlist

```
User clicks "Edit Watchlist"
    ↓
Symbol Picker Modal opens
    ↓
User searches & adds symbols (max 10)
    ↓
Frontend saves to Supabase:
  INSERT INTO user_watchlist (user_id, symbol_id, position)
    ↓
Modal closes
    ↓
Dashboard re-fetches watchlist
    ↓
Renders TradingView Widgets
```

### 2. Live Price Display (TradingView)

```
Dashboard component mounts
    ↓
Fetch user_watchlist from Supabase
  SELECT * FROM user_watchlist
  WHERE user_id = ?
  ORDER BY position
    ↓
For each symbol:
  Render <TradingViewWidget symbol={tv_symbol} />
    ↓
TradingView Widget:
  • Loads external script
  • Fetches live prices from TradingView servers
  • Auto-updates (TradingView handles refresh)
    ↓
User sees live prices (no backend needed!)
```

### 3. Alert System (Hetzner Backend)

```
Celery Beat (every 60s)
    ↓
Query Supabase:
  SELECT DISTINCT symbols.*
  FROM user_watchlist
  JOIN symbols ON symbols.id = symbol_id
    ↓
For each unique symbol:
  Fetch price (yfinance or Twelvedata HTTP)
    ↓
Update price_cache table
    ↓
Check liquidity alerts:
  • Yesterday High/Low breached?
  • Pivot Point crossed?
    ↓
If triggered:
  Send push notification to subscribed users
```

---

## 🔌 TradingView Integration

### Widget Types

**1. Symbol Overview Widget** (Chosen)
```typescript
<TradingViewWidget
  symbol="XETR:DAX"
  width="100%"
  height={200}
/>
```

**Features:**
- ✅ Mini chart with live price
- ✅ Current price + change %
- ✅ Auto-updates
- ✅ Dark mode support
- ✅ No API key required

**Alternative Widgets (Not Used):**
- Single Ticker: Text-only price
- Ticker Tape: Horizontal scrolling
- Market Overview: Multi-symbol table

### Symbol Mapping

TradingView uses different symbol formats:

| Our Symbol | Type | TradingView Symbol |
|------------|------|-------------------|
| `^GDAXI` | Index | `XETR:DAX` |
| `^NDX` | Index | `NASDAQ:NDX` |
| `^DJI` | Index | `DJ:DJI` |
| `EURUSD` | Forex | `FX:EURUSD` |
| `EURGBP` | Forex | `FX:EURGBP` |
| `GBPUSD` | Forex | `FX:GBPUSD` |

**New Column:** `symbols.tv_symbol`
- Stores TradingView-compatible symbol format
- Used by frontend for widget rendering

---

## 🚀 Deployment Architecture

### Frontend (Netlify)
- **URL:** https://tradematrix.netlify.app
- **Auto-deploy:** On git push to main
- **No changes needed:** Netlify build works out of the box

### Database (Supabase)
- **Migration 017:** user_watchlist table (already executed!)
- **No changes:** Existing tables untouched
- **New column:** symbols.tv_symbol (migration 018)

### Backend (Hetzner)
- **IP:** 135.181.195.241
- **Services:** Redis + Celery Beat + Celery Worker
- **Minimal changes:**
  - `alert_engine.py`: Dynamic symbol loading
  - No new services needed
  - No WebSocket server

---

## 📈 Scalability

### Frontend
- **User Limit:** Unlimited
- **Symbols per User:** 10 (configurable)
- **Performance:** TradingView handles all data fetching
- **Cost:** €0 (TradingView free tier)

### Backend (Alerts)
- **User Limit:** Thousands (Celery scales)
- **Unique Symbols:** Unlimited (HTTP polling scales)
- **Frequency:** 60s interval (adjustable)
- **Cost:** €5/mo (Hetzner CX11)

---

## 🔐 Security

### Row Level Security (RLS)
```sql
-- Users only see their own watchlist
CREATE POLICY "Users manage own watchlist"
  ON user_watchlist FOR ALL
  USING (auth.uid() = user_id);
```

### TradingView Widgets
- ✅ Read-only (cannot modify data)
- ✅ Public data only (no auth needed)
- ✅ HTTPS (encrypted)
- ✅ No API keys exposed

---

## 🎯 Success Metrics

**Performance:**
- Dashboard load: <2s
- Widget render: <1s per widget
- Alert latency: <5 min (60s check + notification)

**Reliability:**
- Frontend: 99.9% (Netlify SLA)
- Database: 99.9% (Supabase SLA)
- Backend: 95%+ (Hetzner, self-managed)

**Cost:**
- Frontend: €0 (Netlify free)
- Database: €0 (Supabase free tier)
- Backend: €5/mo (Hetzner CX11)
- APIs: €0 (TradingView free)

**Total: €5/mo** 🎉

---

## 🔄 Future Enhancements

**Phase 1 (Current):** 10 symbols, TradingView widgets
**Phase 2 (Later):** Subscription tiers
  - Free: 3 symbols
  - Starter: 5 symbols
  - Pro: 10 symbols
  - Expert: 20 symbols

**Phase 3 (Future):** Custom alerts per symbol
  - Price above/below
  - % change thresholds
  - Custom technical indicators

---

**Next:** [02_DATABASE_SCHEMA.md](./02_DATABASE_SCHEMA.md)
