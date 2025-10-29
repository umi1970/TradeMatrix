# US Open Planner - Example Output

## Overview
The US Open Planner monitors the first 15 minutes of US market open (15:30-15:45 MEZ) to detect Opening Range Breakouts (ORB) and generate trading setups.

---

## Example 1: Bullish ORB Breakout (NDX)

### Input Data
```json
{
  "symbol": "NDX",
  "trade_date": "2025-10-29",
  "orb_window": "15:30-15:45 MEZ"
}
```

### Step 1: Detect ORB Range
**Query:** Fetch 1m candles from 15:30-15:45 MEZ

**Result:**
```json
{
  "high": 15825.50,
  "low": 15810.25,
  "range_size": 15.25,
  "start_time": "2025-10-29T15:30:00",
  "end_time": "2025-10-29T15:45:00",
  "candle_count": 15,
  "opening_candle": {
    "open": 15815.00,
    "high": 15820.00,
    "low": 15812.00,
    "close": 15818.50,
    "volume": 125000,
    "ts": "2025-10-29T15:30:00"
  }
}
```

**ORB Range Visualization:**
```
15825.50 ─────────────── ORB High
          │           │
          │  Range    │  15.25 points
          │  15 min   │
          │           │
15810.25 ─────────────── ORB Low
```

---

### Step 2: Analyze Breakout
**Query:** Fetch 5m candles from 15:45-16:00 MEZ

**First 5m Candle (15:45-15:50):**
```json
{
  "open": 15823.00,
  "high": 15832.75,
  "low": 15821.00,
  "close": 15830.50,
  "volume": 185000,
  "ts": "2025-10-29T15:45:00"
}
```

**Breakout Detection:**
- Close (15830.50) > ORB High (15825.50) ✅ **BULLISH BREAKOUT**
- Low (15821.00) <= ORB High (15825.50) ✅ **RETEST AVAILABLE**

**Result:**
```json
{
  "direction": "long",
  "breakout_price": 15830.50,
  "breakout_time": "2025-10-29T15:45:00",
  "candle_close": 15830.50,
  "volume": 185000,
  "retest_available": true,
  "retest_price": 15825.50,
  "breakout_strength": 0.33
}
```

**Breakout Visualization:**
```
15832.75 ────────── Breakout High
15830.50 ────────── Close (BREAKOUT!) ✅
15825.50 ────────── ORB High (Entry)
15821.00 ────────── Breakout Low (Retest)
15810.25 ────────── ORB Low (Stop Loss)
```

---

### Step 3: Generate Setup
**Daily Levels (from levels_daily table):**
```json
{
  "trade_date": "2025-10-29",
  "pivot": 15800.00,
  "r1": 15850.00,
  "r2": 15900.00,
  "s1": 15750.00,
  "s2": 15700.00,
  "y_high": 15875.00,
  "y_low": 15725.00
}
```

**Setup Calculation:**
```python
# LONG SETUP
entry = 15825.50          # ORB High (retest available)
stop_loss = 15810.25      # ORB Low
risk = 15825.50 - 15810.25 = 15.25 points

# Take Profit: 2R or Daily High (whichever closer)
tp_2r = 15825.50 + (15.25 * 2) = 15856.00
tp_daily = 15875.00  # y_high
take_profit = min(15856.00, 15875.00) = 15856.00  # 2R is closer

# Risk:Reward = 2.0
```

**Confidence Score:**
```python
base_confidence = 0.3
+ range_factor = 0.006      # Small range (15.25 / 500 * 0.2)
+ breakout_strength = 0.2   # Moderate (33% of range)
+ retest_bonus = 0.15       # Retest available
+ volume_bonus = 0.05       # Volume present
+ pivot_alignment = 0.15    # Long above pivot (15830 > 15800)
─────────────────────────
TOTAL = 0.856 (85.6%)
```

**Generated Setup:**
```json
{
  "id": "a1b2c3d4-e5f6-4g7h-8i9j-0k1l2m3n4o5p",
  "module": "usopen",
  "symbol_id": "uuid-of-NDX",
  "strategy": "orb",
  "side": "long",
  "entry_price": 15825.50,
  "stop_loss": 15810.25,
  "take_profit": 15856.00,
  "confidence": 0.856,
  "status": "pending",
  "payload": {
    "symbol": "NDX",
    "trade_date": "2025-10-29",
    "orb_range": {
      "high": 15825.50,
      "low": 15810.25,
      "range_size": 15.25,
      "candle_count": 15
    },
    "breakout": {
      "price": 15830.50,
      "time": "2025-10-29T15:45:00",
      "strength": 0.33,
      "volume": 185000,
      "retest_available": true
    },
    "risk_reward": 2.0,
    "risk_amount": 15.25,
    "daily_levels": {
      "pivot": 15800.00,
      "r1": 15850.00,
      "y_high": 15875.00
    }
  },
  "created_at": "2025-10-29T15:50:00"
}
```

**Trade Visualization:**
```
15856.00 ════════════════ Take Profit (2R) 🎯
             ↑
             │  30.5 pts (2R)
             │
15825.50 ────────────────── Entry (ORB High Retest) 📍
             │
             │  15.25 pts (1R)
             │
15810.25 ────────────────── Stop Loss (ORB Low) 🛑
```

---

## Example 2: Bearish ORB Breakout (DJI)

### Step 1: Detect ORB Range
```json
{
  "high": 34125.75,
  "low": 34085.50,
  "range_size": 40.25,
  "candle_count": 14
}
```

### Step 2: Analyze Breakout
**First 5m Candle:**
```json
{
  "close": 34070.25,  // Below ORB Low ✅
  "high": 34088.00,   // Above ORB Low (retest) ✅
  "volume": 210000
}
```

**Result:**
```json
{
  "direction": "short",
  "breakout_price": 34070.25,
  "retest_available": true,
  "retest_price": 34085.50,
  "breakout_strength": 0.38
}
```

### Step 3: Generate Setup
```json
{
  "side": "short",
  "entry_price": 34085.50,     // ORB Low (retest)
  "stop_loss": 34125.75,       // ORB High
  "take_profit": 34005.00,     // 2R (80.5 pts)
  "confidence": 0.82,
  "risk_reward": 2.0
}
```

**Trade Visualization:**
```
34125.75 ────────────────── Stop Loss (ORB High) 🛑
             │
             │  40.25 pts (1R)
             │
34085.50 ────────────────── Entry (ORB Low Retest) 📍
             │
             │  80.5 pts (2R)
             ↓
34005.00 ════════════════ Take Profit (2R) 🎯
```

---

## Example 3: No Breakout Detected

### Step 1: Detect ORB Range
```json
{
  "high": 15820.00,
  "low": 15805.00,
  "range_size": 15.0,
  "candle_count": 15
}
```

### Step 2: Analyze Breakout
**5m Candles (15:45-16:00):**
```json
[
  {"close": 15817.50, "high": 15819.00, "low": 15810.00},  // Inside range
  {"close": 15812.00, "high": 15818.00, "low": 15808.00},  // Inside range
  {"close": 15815.50, "high": 15820.00, "low": 15811.00}   // Inside range (touching high, no breakout)
]
```

**Result:** `null` (No breakout detected)

**Reason:** All 5m closes remained within the ORB range.

---

## Agent Execution Summary

### Successful Run
```json
{
  "status": "success",
  "setups_created": 2,
  "details": {
    "trade_date": "2025-10-29",
    "symbols_analyzed": ["DJI", "NDX"],
    "setups": [
      {
        "symbol": "NDX",
        "side": "long",
        "entry_price": 15825.50,
        "confidence": 0.856
      },
      {
        "symbol": "DJI",
        "side": "short",
        "entry_price": 34085.50,
        "confidence": 0.82
      }
    ]
  }
}
```

### Agent Log Entry
```json
{
  "id": "log-uuid-123",
  "agent_type": "us_open_planner",
  "status": "completed",
  "started_at": "2025-10-29T15:50:00",
  "completed_at": "2025-10-29T15:51:23",
  "duration_ms": 83000,
  "input_data": {
    "symbols": ["DJI", "NDX"],
    "orb_start": "15:30:00",
    "orb_end": "15:45:00"
  },
  "output_data": {
    "setups_created": 2,
    "symbols_analyzed": ["DJI", "NDX"]
  }
}
```

---

## Key Features Implemented

### 1. ORB Range Detection
- ✅ Fetch 1m candles (15:30-15:45 MEZ)
- ✅ Calculate High/Low range
- ✅ Validate minimum 12 candles (80% threshold)
- ✅ Store opening candle data

### 2. Breakout Analysis
- ✅ Check 5m candles for breakout
- ✅ Detect bullish breakout (close > ORB high)
- ✅ Detect bearish breakout (close < ORB low)
- ✅ Identify retest opportunities
- ✅ Calculate breakout strength

### 3. Setup Generation
- ✅ Calculate entry price (prefer retest)
- ✅ Set stop loss (opposite range edge)
- ✅ Calculate take profit (2R or daily level)
- ✅ Compute confidence score (0.0-1.0)
- ✅ Store in setups table

### 4. Confidence Scoring
- ✅ Range size factor (0-20%)
- ✅ Breakout strength (0-30%)
- ✅ Retest availability (0-15%)
- ✅ Volume confirmation (0-10%)
- ✅ Daily level alignment (0-15%)

### 5. Logging
- ✅ Log execution start
- ✅ Log successful completion
- ✅ Log failures with error messages
- ✅ Track duration and output data

---

## Database Schema Updates

### New Migration: 004_add_us_open_planner_agent.sql
```sql
-- Update agent_logs constraint to include 'us_open_planner'
ALTER TABLE public.agent_logs
DROP CONSTRAINT IF EXISTS agent_logs_agent_type_check;

ALTER TABLE public.agent_logs
ADD CONSTRAINT agent_logs_agent_type_check
CHECK (agent_type IN (
    'chart_watcher',
    'signal_bot',
    'risk_manager',
    'journal_bot',
    'publisher',
    'us_open_planner'  -- NEW!
));
```

---

## Next Steps

### 1. Celery Integration
Add to `/mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/agents/src/tasks.py`:

```python
from celery import Celery
from celery.schedules import crontab
from us_open_planner import USOpenPlanner
import asyncio

app = Celery('tradematrix')

@app.task(name='agents.us_open_planner')
def run_us_open_planner():
    """
    Run US Open Planner
    Scheduled daily at 15:25 MEZ (5 minutes before US market open)
    """
    planner = USOpenPlanner()
    result = asyncio.run(planner.run())
    return result

# Celery Beat schedule
app.conf.beat_schedule = {
    'us-open-planner-daily': {
        'task': 'agents.us_open_planner',
        'schedule': crontab(hour=15, minute=25),  # 15:25 MEZ daily
    }
}
```

### 2. Testing
```bash
# Manual test
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/agents
python -c "
import asyncio
from src.us_open_planner import USOpenPlanner
from datetime import datetime

async def test():
    planner = USOpenPlanner()
    result = await planner.run(trade_date=datetime(2025, 10, 29))
    print(result)

asyncio.run(test())
"
```

### 3. Market Data Population
Before testing, ensure OHLC data exists:
```sql
-- Check if data exists
SELECT COUNT(*) FROM ohlc
WHERE timeframe = '1m'
AND ts BETWEEN '2025-10-29 15:30:00' AND '2025-10-29 15:45:00';

-- Check symbols
SELECT * FROM market_symbols WHERE symbol IN ('DJI', 'NDX');
```

---

## Summary

The US Open Planner is now **fully implemented** with:

1. ✅ **detect_orb_range()** - Fetches 1m candles, calculates range
2. ✅ **analyze_breakout()** - Detects breakouts with retest logic
3. ✅ **generate_setup()** - Creates trading setups with confidence scores
4. ✅ **Helper methods** - Symbol lookup, daily levels, confidence calculation
5. ✅ **Logging methods** - Full execution tracking
6. ✅ **Database schema** - Migration 004 adds us_open_planner to agent_logs

**Ready for Celery integration and live trading!** 🚀
