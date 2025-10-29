# Morning Planner Agent

**AI Agent for analyzing overnight market movements and generating morning trading setups**

---

## Overview

The **Morning Planner** agent runs daily at **08:25 MEZ** (Berlin time) to analyze overnight price action from Asia and early European sessions. It detects specific trading patterns and generates actionable trading setups stored in the `setups` table.

**Execution Time:** 08:25 MEZ (Mon-Fri)
**Module ID:** `morning`
**Data Range:** 02:00 - 08:25 MEZ

---

## Trading Strategies

### 1. Asia Sweep → EU Open Reversal

**Pattern Description:**
- During Asia session (02:00-05:00 MEZ), price sweeps below yesterday's low (`y_low`)
- At EU Open (08:00+ MEZ), price reverses and closes back above `y_low`
- Signals potential long entry for reversal back towards pivot/resistance

**Entry Logic:**
- **Condition 1:** Any candle during Asia session has `low < y_low` (sweep detected)
- **Condition 2:** EU Open candle closes above `y_low` (reversal confirmed)
- **Signal:** Long entry

**Trade Parameters:**
- **Entry Price:** Current price at detection (EU Open close)
- **Stop Loss:** Asia session low - 0.25% buffer
- **Take Profit:** Pivot point or R1 resistance
- **Side:** Long

**Confidence Factors:**
- Deeper sweep below `y_low` = higher confidence
- Stronger reversal (close further above `y_low`) = higher confidence
- Volume increase during reversal = higher confidence

---

### 2. Y-Low → Pivot Rebound

**Pattern Description:**
- Market opens below pivot point
- No immediate breakout above pivot detected
- Entry zone exists between `y_low` and `pivot`
- Expectation: Price rebounds from `y_low` area towards pivot/R1

**Entry Logic:**
- **Condition 1:** Market open < pivot point
- **Condition 2:** Current price still < pivot (no breakout yet)
- **Condition 3:** Price in range [y_low, pivot]
- **Signal:** Long entry in bounce zone

**Trade Parameters:**
- **Entry Price:** Current price or midpoint of [y_low, pivot] range
- **Stop Loss:** y_low - 0.25% buffer
- **Take Profit:** Pivot point or R1
- **Side:** Long

**Confidence Factors:**
- Closer to `y_low` = higher risk but clearer support level
- Earlier in the day = more time for rebound
- Recent price strength/momentum

---

## Data Sources

### Tables Used

#### 1. `ohlc` - OHLC Candle Data
```sql
SELECT * FROM ohlc
WHERE symbol_id = :symbol_id
  AND timeframe = '5m'
  AND ts BETWEEN '2025-10-29 02:00:00+01' AND '2025-10-29 08:25:00+01'
ORDER BY ts ASC
```

**Required Timeframes:**
- `5m` (primary)
- `1m` (optional, for more granular analysis)

**Time Ranges:**
- Asia Session: 02:00 - 05:00 MEZ
- EU Open: 08:00 - 08:25 MEZ

---

#### 2. `levels_daily` - Daily Calculated Levels
```sql
SELECT
  pivot, r1, r2, s1, s2,
  y_high, y_low, y_close
FROM levels_daily
WHERE symbol_id = :symbol_id
  AND trade_date = :today
```

**Key Levels:**
- `pivot` - Daily pivot point
- `r1`, `r2` - Resistance levels
- `s1`, `s2` - Support levels
- `y_high`, `y_low` - Yesterday's high/low
- `y_close` - Yesterday's close

---

#### 3. `market_symbols` - Active Symbols
```sql
SELECT id, symbol, alias
FROM market_symbols
WHERE active = true
```

**Default Symbols:**
- DAX (DAX 40)
- NDX (NASDAQ 100)
- DJI (Dow Jones 30)
- EUR/USD
- XAG/USD (Silver)

---

## Output Format

### Setups Table Record

Each detected setup is inserted into the `setups` table:

```json
{
  "id": "uuid",
  "user_id": null,                    // Global setup (null) or user-specific
  "module": "morning",                 // Always "morning" for this agent
  "symbol_id": "uuid",
  "strategy": "asia_sweep",            // or "y_low_rebound"
  "side": "long",                      // or "short"
  "entry_price": 18450.50,
  "stop_loss": 18420.25,
  "take_profit": 18500.00,
  "confidence": 0.75,                  // 0.0 - 1.0
  "status": "pending",                 // "pending" | "active" | "invalid" | "filled" | "cancelled"
  "payload": {
    "strategy": "asia_sweep",
    "side": "long",
    "entry_price": 18450.50,
    "stop_loss": 18420.25,
    "take_profit": 18500.00,
    "confidence": 0.75,
    "metadata": {
      "asia_low": 18415.00,
      "y_low": 18430.00,
      "pivot": 18500.00,
      "eu_open_close": 18450.50,
      "detection_time": "2025-10-29T08:25:00Z"
    }
  },
  "created_at": "2025-10-29T08:25:15Z",
  "updated_at": "2025-10-29T08:25:15Z"
}
```

---

## Class Structure

### `MorningPlanner` Class

```python
from morning_planner import MorningPlanner
from config.supabase import get_supabase_admin

# Initialize agent
planner = MorningPlanner(supabase_client=get_supabase_admin())

# Run analysis for all active symbols
result = planner.run()

# Or analyze specific symbols only
result = planner.run(symbols=["DAX", "NDX"])
```

### Methods

#### `__init__(supabase_client: Client)`
Initialize agent with Supabase client (admin client recommended for bypassing RLS)

#### `analyze_asia_sweep(symbol_id, symbol_name, trade_date) -> Optional[Dict]`
Detect Asia Sweep → EU Open Reversal pattern

**Returns:**
```python
{
  "strategy": "asia_sweep",
  "side": "long",
  "entry_price": Decimal,
  "stop_loss": Decimal,
  "take_profit": Decimal,
  "confidence": float,
  "metadata": {...}
}
```

#### `analyze_y_low_rebound(symbol_id, symbol_name, trade_date) -> Optional[Dict]`
Detect Y-Low → Pivot Rebound pattern

**Returns:** Same structure as `analyze_asia_sweep()`

#### `generate_setup(symbol_id, symbol_name, setup_data, user_id=None) -> UUID`
Save setup to database

**Returns:** UUID of created setup record

#### `run(symbols=None) -> Dict`
Main execution method (called by Celery scheduler)

**Returns:**
```python
{
  "execution_time": "2025-10-29T08:25:00Z",
  "execution_duration_ms": 1234,
  "symbols_analyzed": 5,
  "setups_generated": 2,
  "setups": [
    {"symbol": "DAX", "strategy": "asia_sweep", "setup_id": "uuid"},
    {"symbol": "NDX", "strategy": "y_low_rebound", "setup_id": "uuid"}
  ]
}
```

---

## Celery Scheduling

### Celery Beat Schedule

Add to `celeryconfig.py` or Celery app configuration:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'morning-planner-daily': {
        'task': 'agents.morning_planner.run_daily',
        'schedule': crontab(hour=8, minute=25, day_of_week='1-5'),  # Weekdays 08:25 MEZ
        'options': {
            'expires': 3600,  # Expires after 1 hour
        }
    },
}
```

### Task File

See: `tasks_morning_planner.py`

```python
from tasks_morning_planner import run_morning_planner_task

# Manual execution (for testing)
result = run_morning_planner_task.apply()
print(result.get())

# Async execution
task = run_morning_planner_task.apply_async()
```

---

## Implementation Status

### ✅ Completed
- [x] Class structure and method signatures
- [x] Comprehensive docstrings
- [x] Strategy logic documentation
- [x] Output format specification
- [x] Celery task template
- [x] README documentation

### 🚧 TODO (Implementation Required)

#### `analyze_asia_sweep()` Method
- [ ] Fetch levels from `levels_daily` table
- [ ] Query Asia session candles (02:00-05:00 MEZ)
- [ ] Detect sweep below `y_low`
- [ ] Fetch EU Open candle (08:00-08:25 MEZ)
- [ ] Check reversal condition (close > y_low)
- [ ] Calculate entry, stop loss, take profit
- [ ] Implement confidence scoring
- [ ] Return setup dictionary

#### `analyze_y_low_rebound()` Method
- [ ] Fetch levels from `levels_daily` table
- [ ] Query market open candle
- [ ] Check if open < pivot
- [ ] Verify no breakout occurred
- [ ] Define entry zone [y_low, pivot]
- [ ] Calculate entry, stop loss, take profit
- [ ] Implement confidence scoring
- [ ] Return setup dictionary

#### `generate_setup()` Method
- [ ] Build setup record dictionary
- [ ] Insert into `setups` table via Supabase
- [ ] Handle database errors
- [ ] Return created setup UUID

#### `run()` Method
- [ ] Fetch active symbols from `market_symbols`
- [ ] Filter by symbols parameter if provided
- [ ] Convert current time to Berlin timezone
- [ ] Loop through symbols and run both strategies
- [ ] Generate setups for detected patterns
- [ ] Log execution to `agent_logs` table (optional)
- [ ] Return execution summary

---

## Testing

### Unit Tests (TODO)

```python
# tests/test_morning_planner.py

def test_analyze_asia_sweep_with_sweep_detected():
    # Setup mock data
    # Call analyze_asia_sweep()
    # Assert setup returned
    pass

def test_analyze_asia_sweep_no_sweep():
    # Setup mock data with no sweep
    # Call analyze_asia_sweep()
    # Assert None returned
    pass

def test_analyze_y_low_rebound_valid():
    # Setup mock data with open < pivot
    # Call analyze_y_low_rebound()
    # Assert setup returned
    pass

def test_generate_setup():
    # Mock Supabase client
    # Call generate_setup()
    # Assert database insert called
    pass
```

### Manual Testing

```bash
# Run agent directly
cd services/agents
python -m src.morning_planner

# Run via Celery task
celery -A tasks_morning_planner call agents.morning_planner.run_daily

# Test with specific symbols
celery -A tasks_morning_planner call agents.morning_planner.run_daily --args='[["DAX", "NDX"]]'
```

---

## Error Handling

### Common Errors

**No levels found:**
- Check if `levels_daily` table has data for today
- Verify pivot calculation is running before 08:25

**No Asia session candles:**
- Verify OHLC data ingestion is working
- Check if `ohlc` table has data for 02:00-05:00 timeframe

**No EU Open candle:**
- Check current time (should be >= 08:00 MEZ)
- Verify real-time data feed is active

---

## Dependencies

```python
# Python packages
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from uuid import UUID
import logging

# Third-party
from supabase import Client
import pytz

# Internal
from config.supabase import get_supabase_admin
```

---

## Logging

All operations are logged with INFO/WARNING/ERROR levels:

```python
import logging
logger = logging.getLogger(__name__)

# Example logs
logger.info("Morning Planner execution started")
logger.warning("No levels found for DAX")
logger.error("Failed to insert setup", exc_info=True)
```

---

## Next Steps

1. **Implement TODO sections** in each method
2. **Add Supabase queries** for data fetching
3. **Implement confidence scoring** algorithms
4. **Add unit tests** for each strategy
5. **Test with historical data** to validate logic
6. **Deploy Celery beat scheduler** for production
7. **Monitor execution logs** daily

---

## Related Files

- **Agent:** `/services/agents/src/morning_planner.py`
- **Tasks:** `/services/agents/tasks_morning_planner.py`
- **Schema:** `/services/api/supabase/migrations/003_market_data_schema.sql`
- **Config:** `/services/api/src/config/supabase.py`

---

**Status:** 🚧 Skeleton Created - Implementation Pending
**Created:** 2025-10-29
**Last Updated:** 2025-10-29
