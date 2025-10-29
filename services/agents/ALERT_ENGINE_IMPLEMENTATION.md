# Alert Engine Implementation Summary

## Overview
Complete implementation of the Alert Engine agent for TradeMatrix.ai. The Alert Engine monitors market data in real-time and generates trading alerts.

## File Location
`/mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/agents/src/alert_engine.py`

## Implementation Details

### 1. `check_range_break()` Method ✅

**Purpose:** Detect ORB (Opening Range Breakout) 5m close above/below 15m range

**Implementation:**
```python
# Step 1: Fetch active ORB setups
- Query 'setups' table for active ORB strategies
- Filter: symbol_id, strategy='orb', status='active'
- Order by created_at DESC, limit 1

# Step 2: Extract range boundaries
- Parse payload JSON for range_high and range_low
- Validate values are non-zero

# Step 3: Fetch latest 5m candle
- Query 'ohlc' table
- Filter: symbol_id, timeframe='5m'
- Order by ts DESC, limit 1

# Step 4: Check for breakout
- Bullish: close_price > range_high
- Bearish: close_price < range_low

# Step 5: Return alert data
- kind: 'range_break'
- direction: 'bullish' or 'bearish'
- price, range_high, range_low, timestamps
```

**Error Handling:**
- Try/except blocks for all database queries
- Validation of payload data
- Graceful return of None if no setup or candle found

**Example Output:**
```json
{
  "kind": "range_break",
  "direction": "bullish",
  "price": 18250.50,
  "range_high": 18200.00,
  "range_low": 18150.00,
  "candle_timestamp": "2025-10-29T08:30:00Z",
  "detection_time": "2025-10-29T08:30:15Z"
}
```

---

### 2. `check_retest_touch()` Method ✅

**Purpose:** Detect when price returns to range edge after breakout (retest)

**Implementation:**
```python
# Step 1: Fetch active setup with breakout
- Query 'setups' table
- Check payload for break_detected flag

# Step 2: Extract break data
- Get range_high, range_low
- Get break_direction from payload

# Step 3: Fetch latest 1m candle
- Query 'ohlc' table with timeframe='1m'
- More precise detection than 5m

# Step 4: Check for retest
- Bullish: current_price within 0.1% of range_high
- Bearish: current_price within 0.1% of range_low
- Tolerance: 0.001 (0.1%)

# Step 5: Return alert data
```

**Tolerance Calculation:**
```python
tolerance = Decimal("0.001")  # 0.1%

# For bullish break
price_diff = abs(current_price - range_high)
is_retest = (price_diff / range_high) <= tolerance
```

**Example Output:**
```json
{
  "kind": "retest_touch",
  "direction": "bullish",
  "price": 18202.30,
  "range_edge": 18200.00,
  "candle_timestamp": "2025-10-29T08:45:00Z",
  "detection_time": "2025-10-29T08:45:10Z"
}
```

---

### 3. `check_asia_sweep_confirmed()` Method ✅

**Purpose:** Detect EU-Open confirmation after Asia session swept below y_low

**Implementation:**
```python
# Step 1: Check if in EU session
- Current hour: 7-9 UTC (08:00-10:00 CET)
- Return None if outside session

# Step 2: Fetch today's y_low
- Query 'levels_daily' table
- Filter: symbol_id, trade_date=today

# Step 3: Check Asia sweep
- Asia session: 01:00-06:00 UTC (02:00-07:00 CET)
- Query all 5m candles in Asia session
- Find minimum low
- Confirm: asia_low < y_low

# Step 4: Fetch last 3 candles
- Get most recent 3x 5m candles
- Need 3 for confirmation

# Step 5: Confirm reversal
- Check all 3 candles have close > y_low
- All must be above to confirm

# Step 6: Return alert data
```

**Time Handling:**
```python
# EU session check (UTC)
is_eu_session = 7 <= current_hour <= 9

# Asia session range
asia_start = now.replace(hour=1, minute=0, second=0, microsecond=0)
asia_end = now.replace(hour=6, minute=0, second=0, microsecond=0)
```

**Example Output:**
```json
{
  "kind": "asia_sweep_confirmed",
  "price": 18180.00,
  "y_low": 18100.00,
  "asia_low": 18095.50,
  "candle_timestamp": "2025-10-29T08:15:00Z",
  "detection_time": "2025-10-29T08:15:20Z"
}
```

---

### 4. `check_pivot_touches()` Method ✅

**Purpose:** Detect when price touches Pivot Point, R1, or S1 levels

**Implementation:**
```python
# Step 1: Fetch today's pivot levels
- Query 'levels_daily' table
- Select: pivot, r1, s1
- Filter: symbol_id, trade_date=today

# Step 2: Fetch latest 1m candle
- Query 'ohlc' table
- Get close, high, low prices

# Step 3: Define tolerance
- tolerance_pct = 0.0005 (0.05%)

# Step 4: Check each level
- For Pivot: Check if level within candle range ± tolerance
- For R1: Same check
- For S1: Same check
- Can detect multiple touches in single candle
```

**Touch Detection Logic:**
```python
# Check if level touched within tolerance
if pivot > 0:
    pivot_tolerance = pivot * tolerance_pct
    is_pivot_touch = (candle_low - pivot_tolerance) <= pivot <= (candle_high + pivot_tolerance)
```

**Example Output (Multiple Alerts):**
```json
[
  {
    "kind": "pivot_touch",
    "price": 18175.00,
    "level": 18175.50,
    "level_name": "Pivot",
    "candle_high": 18180.00,
    "candle_low": 18170.00,
    "candle_timestamp": "2025-10-29T09:00:00Z",
    "detection_time": "2025-10-29T09:00:05Z"
  },
  {
    "kind": "r1_touch",
    "price": 18225.00,
    "level": 18225.30,
    "level_name": "R1",
    "candle_high": 18230.00,
    "candle_low": 18220.00,
    "candle_timestamp": "2025-10-29T09:30:00Z",
    "detection_time": "2025-10-29T09:30:05Z"
  }
]
```

---

### 5. `create_alert()` Method ✅

**Purpose:** Write alert to database for frontend consumption

**Implementation:**
```python
# Build alert record
alert_record = {
    'user_id': str(user_id) if user_id else None,  # NULL for global alerts
    'symbol_id': str(symbol_id),
    'kind': alert_data['kind'],
    'context': alert_data,  # Full JSON context
    'sent': False  # Frontend will mark True after display
}

# Insert to 'alerts' table
result = self.supabase.table('alerts').insert(alert_record).execute()

# Return UUID
alert_id = result.data[0]['id']
```

**Error Handling:**
- Try/except for database insert
- Check if data returned
- Log errors and return None on failure

**Database Record:**
```sql
-- alerts table structure
id          UUID PRIMARY KEY
user_id     UUID (nullable - NULL for global alerts)
symbol_id   UUID NOT NULL
kind        TEXT NOT NULL
context     JSONB NOT NULL
sent        BOOLEAN DEFAULT false
created_at  TIMESTAMP DEFAULT now()
```

---

### 6. `run()` Method ✅

**Purpose:** Main execution method called by Celery scheduler every 60 seconds

**Implementation:**
```python
# Step 1: Fetch active symbols
- Query 'market_symbols' where active=true
- Optional filter by symbols parameter
- Handle errors gracefully

# Step 2: Analyze each symbol
for symbol in active_symbols:
    try:
        # Check 1: Range Break
        # Check 2: Retest Touch
        # Check 3: Asia Sweep Confirmed
        # Check 4: Pivot Touches (returns list)

        # Create alerts for each detection
        if alert_detected:
            alert_id = create_alert(...)
            generated_alerts.append(...)

    except Exception as e:
        logger.error(...)
        continue  # Don't stop on single symbol failure

# Step 3: Log execution summary
- Log to agent_logs table (optional)
- Calculate duration
- Return summary
```

**Return Summary:**
```json
{
  "execution_time": "2025-10-29T08:00:00Z",
  "execution_duration_ms": 2350,
  "symbols_analyzed": 4,
  "alerts_generated": 7,
  "alerts": [
    {
      "symbol": "DAX",
      "kind": "range_break",
      "alert_id": "uuid...",
      "details": { ... }
    },
    {
      "symbol": "DAX",
      "kind": "pivot_touch",
      "alert_id": "uuid...",
      "details": { ... }
    },
    {
      "symbol": "NDX",
      "kind": "asia_sweep_confirmed",
      "alert_id": "uuid...",
      "details": { ... }
    }
  ]
}
```

---

## Key Features

### Error Handling
- **Try/Except blocks** around all database queries
- **Graceful degradation**: Single symbol failure doesn't stop execution
- **Comprehensive logging**: Error, warning, info, and debug levels
- **Validation**: Check for null/zero values before processing

### Database Queries
All queries use proper Supabase Python client syntax:
```python
result = self.supabase.table('table_name')\
    .select('columns')\
    .eq('column', value)\
    .order('column', desc=True)\
    .limit(1)\
    .execute()

data = result.data[0] if result.data else None
```

### Tolerance Calculations
```python
# Example: 0.05% tolerance for pivot touches
tolerance_pct = Decimal("0.0005")
level_tolerance = level * tolerance_pct
is_touched = (candle_low - level_tolerance) <= level <= (candle_high + level_tolerance)

# Example: 0.1% tolerance for retest
tolerance = Decimal("0.001")
price_diff = abs(current_price - range_edge)
is_retest = (price_diff / range_edge) <= tolerance
```

### Type Safety
- Use `Decimal` for all price calculations (avoid float precision issues)
- Convert UUIDs to strings for database queries
- Convert Decimals to floats only for JSON output

---

## Testing

### Test Execution
```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/agents

# Test single execution
python src/alert_engine.py

# Test with specific symbols
python -c "
from src.alert_engine import AlertEngine
from config.supabase import get_supabase_admin

engine = AlertEngine(get_supabase_admin())
result = engine.run(symbols=['DAX', 'NDX'])
print(result)
"
```

### Expected Behavior

**Scenario 1: Range Break**
```
Input: ORB setup with range 18150-18200, current 5m close at 18205
Output: range_break alert (bullish)
```

**Scenario 2: Retest Touch**
```
Input: Bullish break at 18205, current price returns to 18201
Output: retest_touch alert (bullish)
```

**Scenario 3: Asia Sweep Confirmed**
```
Input: Asia low 18095, y_low 18100, EU open 3 candles all above 18100
Output: asia_sweep_confirmed alert
```

**Scenario 4: Pivot Touch**
```
Input: Pivot at 18175, current candle high 18180, low 18170
Output: pivot_touch alert (level within candle range)
```

---

## Integration with Celery

### Task Definition
```python
# tasks.py
from celery import Celery
from src.alert_engine import AlertEngine
from config.supabase import get_supabase_admin

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def run_alert_engine():
    engine = AlertEngine(get_supabase_admin())
    result = engine.run()
    return result

# Schedule: Every 60 seconds
app.conf.beat_schedule = {
    'alert-engine-every-60s': {
        'task': 'tasks.run_alert_engine',
        'schedule': 60.0,
    },
}
```

### Execution
```bash
# Start Celery worker
celery -A tasks worker --loglevel=info

# Start Celery beat (scheduler)
celery -A tasks beat --loglevel=info
```

---

## Frontend Integration

### Supabase Realtime Subscription
```typescript
// Frontend subscribes to alerts table
const subscription = supabase
  .channel('alerts')
  .on('postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'alerts'
    },
    (payload) => {
      const alert = payload.new;
      // Display notification
      showNotification({
        title: alert.kind,
        message: `${alert.context.symbol} - ${alert.context.price}`,
        type: alert.context.direction
      });
    }
  )
  .subscribe();
```

### Mark Alert as Sent
```typescript
// After displaying alert to user
await supabase
  .from('alerts')
  .update({ sent: true })
  .eq('id', alertId);
```

---

## Example Alert Scenarios

### Scenario 1: DAX Range Break (Bullish)
```json
{
  "execution_time": "2025-10-29T08:30:15Z",
  "execution_duration_ms": 1250,
  "symbols_analyzed": 4,
  "alerts_generated": 1,
  "alerts": [
    {
      "symbol": "DAX",
      "kind": "range_break",
      "alert_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "details": {
        "kind": "range_break",
        "direction": "bullish",
        "price": 18250.50,
        "range_high": 18200.00,
        "range_low": 18150.00,
        "candle_timestamp": "2025-10-29T08:30:00Z",
        "detection_time": "2025-10-29T08:30:15Z"
      }
    }
  ]
}
```

### Scenario 2: Multiple Alerts (DAX + NDX)
```json
{
  "execution_time": "2025-10-29T09:00:05Z",
  "execution_duration_ms": 2150,
  "symbols_analyzed": 4,
  "alerts_generated": 4,
  "alerts": [
    {
      "symbol": "DAX",
      "kind": "pivot_touch",
      "alert_id": "uuid-1",
      "details": {
        "kind": "pivot_touch",
        "price": 18175.00,
        "level": 18175.50,
        "level_name": "Pivot"
      }
    },
    {
      "symbol": "DAX",
      "kind": "retest_touch",
      "alert_id": "uuid-2",
      "details": {
        "kind": "retest_touch",
        "direction": "bullish",
        "price": 18201.30,
        "range_edge": 18200.00
      }
    },
    {
      "symbol": "NDX",
      "kind": "asia_sweep_confirmed",
      "alert_id": "uuid-3",
      "details": {
        "kind": "asia_sweep_confirmed",
        "price": 16850.00,
        "y_low": 16800.00,
        "asia_low": 16795.50
      }
    },
    {
      "symbol": "NDX",
      "kind": "r1_touch",
      "alert_id": "uuid-4",
      "details": {
        "kind": "r1_touch",
        "price": 16900.00,
        "level": 16900.25,
        "level_name": "R1"
      }
    }
  ]
}
```

---

## Performance Considerations

### Optimization
1. **Single queries per symbol**: Minimize database round-trips
2. **Indexed columns**: Ensure symbol_id, timeframe, ts are indexed
3. **Limit results**: Always use `.limit()` to fetch only needed data
4. **Continue on error**: Don't stop all processing if one symbol fails
5. **Efficient tolerances**: Use Decimal for precision without performance hit

### Monitoring
- Log execution duration (target: < 3 seconds for 10 symbols)
- Track alerts generated per symbol
- Monitor error rates per check method
- Alert on execution failures

---

## Next Steps

### Integration
1. ✅ Alert Engine implementation complete
2. ⏳ Create Celery task definition
3. ⏳ Add to tasks.py with scheduler
4. ⏳ Test with real market data
5. ⏳ Frontend alert display component
6. ⏳ Supabase Realtime subscription

### Enhancements
- Add alert deduplication (don't alert same event multiple times)
- Add user-specific alert preferences
- Add alert cooldown periods
- Add alert priority levels
- Add Telegram/WhatsApp notification integration

---

## Status: ✅ COMPLETE

All TODO sections have been implemented with:
- Proper error handling
- Comprehensive logging
- Type safety (Decimal for prices)
- Database query optimization
- Detailed documentation

**Ready for integration with Celery scheduler and frontend consumption.**
