# Migration 013: chart-img.com Integration

**Created:** 2025-11-02
**Status:** Ready for deployment
**Dependencies:** Migration 010 (EOD Data Layer with symbols table)

---

## Overview

This migration adds support for dynamic chart generation via the chart-img.com API. It enables TradeMatrix to generate, store, and display TradingView-style charts for 5 main trading symbols.

### Key Features

1. **Chart Configuration** - Extends `symbols` table with TradingView symbol mappings
2. **Snapshot Storage** - New `chart_snapshots` table tracks generated chart URLs
3. **Multi-Timeframe Support** - 1h, 4h, 1d (and 12 more timeframes)
4. **Automated Cleanup** - Utility function to remove expired snapshots
5. **RLS Security** - Row-level security policies for user data protection

---

## Changes Summary

### Tables Modified

#### `public.symbols`
**New Columns:**
- `chart_img_symbol` (TEXT) - TradingView symbol for chart-img.com API
- `chart_enabled` (BOOLEAN) - Whether chart generation is enabled
- `chart_config` (JSONB) - Chart configuration (timeframes, indicators, theme)

**Example `chart_config`:**
```json
{
  "timeframes": ["1h", "4h", "1d"],
  "indicators": ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"],
  "default_timeframe": "4h",
  "theme": "dark"
}
```

### Tables Created

#### `public.chart_snapshots`
Stores generated chart snapshots with metadata.

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (auto-generated) |
| symbol_id | UUID | Reference to `symbols.id` |
| timeframe | TEXT | Chart timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 3d, 1w, 1M) |
| chart_url | TEXT | Full URL to chart image on chart-img.com CDN |
| trigger_type | TEXT | What triggered generation (manual, report, setup, analysis, monitoring, alert) |
| generated_by | UUID | User who triggered (NULL for automated) |
| generated_at | TIMESTAMPTZ | When chart was generated |
| expires_at | TIMESTAMPTZ | When chart-img.com will delete chart (typically 60 days) |
| metadata | JSONB | Additional metadata (annotations, notes, indicator values) |
| created_at | TIMESTAMPTZ | Record creation timestamp |

**Constraints:**
- `symbol_id` references `public.symbols(id)` ON DELETE CASCADE
- `generated_by` references `auth.users(id)` ON DELETE SET NULL
- `timeframe` must be one of 13 valid values
- `trigger_type` must be one of 6 valid values

---

## Indexes Created

Performance optimization for common query patterns:

1. `idx_symbols_chart_enabled` - Partial index on `symbols.chart_enabled = true`
2. `idx_chart_snapshots_symbol_id` - Fast symbol lookups
3. `idx_chart_snapshots_generated_at` - Ordered by generation time (DESC)
4. `idx_chart_snapshots_timeframe` - Filter by timeframe
5. `idx_chart_snapshots_trigger_type` - Filter by trigger type
6. `idx_chart_snapshots_symbol_timeframe` - Composite index for common queries

---

## RLS Policies

### `chart_snapshots` Table

| Policy Name | Command | Description |
|-------------|---------|-------------|
| Anyone can view chart_snapshots | SELECT | Public read access |
| Authenticated users can create chart_snapshots | INSERT | Logged-in users can generate charts |
| Users can delete own chart_snapshots | DELETE | Users can delete their own snapshots |
| Service role can manage all chart_snapshots | ALL | Backend service has full access |

---

## Configured Symbols

5 symbols are pre-configured with TradingView mappings:

| Symbol | Name | Type | TradingView Symbol | Config |
|--------|------|------|-------------------|--------|
| ^GDAXI | DAX 40 | index | XETR:DAX | 1h/4h/1d, EMAs, RSI, Volume |
| ^NDX | NASDAQ 100 | index | NASDAQ:NDX | 1h/4h/1d, EMAs, RSI, Volume |
| ^DJI | Dow Jones | index | DJCFD:DJI | 1h/4h/1d, EMAs, RSI, Volume |
| EURUSD | EUR/USD | forex | OANDA:EURUSD | 1h/4h/1d, EMAs, RSI, Volume |
| EURGBP | EUR/GBP | forex | OANDA:EURGBP | 1h/4h/1d, EMAs, RSI, Volume |
| GBPUSD | GBP/USD | forex | OANDA:GBPUSD | 1h/4h/1d, EMAs, RSI, Volume (if exists) |

---

## Utility Functions

### `get_latest_chart_snapshot(p_symbol_id UUID, p_timeframe TEXT)`

Returns the most recent chart snapshot for a given symbol and timeframe.

**Usage:**
```sql
SELECT * FROM get_latest_chart_snapshot(
  (SELECT id FROM symbols WHERE symbol = '^GDAXI' LIMIT 1),
  '4h'
);
```

**Returns:**
- id (UUID)
- chart_url (TEXT)
- generated_at (TIMESTAMPTZ)
- expires_at (TIMESTAMPTZ)
- metadata (JSONB)

---

### `cleanup_expired_chart_snapshots()`

Deletes chart snapshots that have passed their expiration date.

**Usage:**
```sql
SELECT cleanup_expired_chart_snapshots();
```

**Returns:** INTEGER (count of deleted rows)

**Recommended Schedule:** Run daily via cron or Celery Beat

---

## Deployment Instructions

### 1. Apply Migration

**Via Supabase Dashboard:**
1. Go to SQL Editor
2. Copy content from `013_add_chart_img_support.sql`
3. Run query
4. Verify: "Success. No rows returned" (if no errors)

**Via CLI:**
```bash
supabase db push
# or
supabase migration up
```

### 2. Validate Migration

Run all tests from `013_validation_tests.sql`:

```bash
# Via Supabase SQL Editor
# Copy and run each test block

# Or via psql
psql $DATABASE_URL -f services/api/supabase/migrations/013_validation_tests.sql
```

**Expected Results:**
- ✅ 5+ symbols with `chart_enabled = true`
- ✅ `chart_snapshots` table exists with 9 columns
- ✅ 4 RLS policies active
- ✅ 6+ indexes created
- ✅ Utility functions operational

### 3. Verify Data

```sql
-- Check configured symbols
SELECT symbol, chart_img_symbol, chart_enabled
FROM symbols
WHERE chart_enabled = true;

-- Should return 5 rows
```

---

## Rollback Instructions

If you need to undo this migration:

```sql
-- WARNING: This will delete all chart snapshots!

BEGIN;

-- Drop table (CASCADE removes all dependencies)
DROP TABLE IF EXISTS public.chart_snapshots CASCADE;

-- Remove columns from symbols table
ALTER TABLE public.symbols
  DROP COLUMN IF EXISTS chart_img_symbol,
  DROP COLUMN IF EXISTS chart_enabled,
  DROP COLUMN IF EXISTS chart_config;

-- Drop utility functions
DROP FUNCTION IF EXISTS get_latest_chart_snapshot(UUID, TEXT);
DROP FUNCTION IF EXISTS cleanup_expired_chart_snapshots();

-- Drop indexes
DROP INDEX IF EXISTS idx_symbols_chart_enabled;

COMMIT;
```

---

## Integration Guide

### Backend (FastAPI)

Create a new service: `services/agents/src/chart_generator.py`

```python
import os
import requests
from supabase import Client

class ChartGenerator:
    """Generate charts via chart-img.com API"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.api_base = "https://api.chart-img.com/v2/tradingview/advanced-chart"

    def generate_chart(
        self,
        symbol_id: str,
        timeframe: str = "4h",
        trigger_type: str = "manual",
        user_id: str = None
    ) -> dict:
        """Generate chart and store snapshot"""

        # 1. Get symbol config from DB
        symbol = self.supabase.table("symbols") \
            .select("*") \
            .eq("id", symbol_id) \
            .single() \
            .execute()

        if not symbol.data.get("chart_enabled"):
            raise ValueError("Chart generation not enabled for this symbol")

        # 2. Build chart-img.com URL
        tv_symbol = symbol.data["chart_img_symbol"]
        config = symbol.data["chart_config"]

        chart_url = f"{self.api_base}?symbol={tv_symbol}&interval={timeframe}"
        chart_url += f"&theme={config.get('theme', 'dark')}"

        # Add indicators
        for indicator in config.get("indicators", []):
            chart_url += f"&studies={indicator}"

        # 3. Store snapshot in DB
        snapshot = self.supabase.table("chart_snapshots").insert({
            "symbol_id": symbol_id,
            "timeframe": timeframe,
            "chart_url": chart_url,
            "trigger_type": trigger_type,
            "generated_by": user_id,
            "expires_at": "NOW() + INTERVAL '60 days'"
        }).execute()

        return snapshot.data
```

### Frontend (React)

Create a new component: `apps/web/src/components/charts/ChartSnapshot.tsx`

```tsx
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

interface ChartSnapshotProps {
  symbolId: string;
  timeframe?: string;
}

export function ChartSnapshot({ symbolId, timeframe = '4h' }: ChartSnapshotProps) {
  const [chartUrl, setChartUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchLatestSnapshot() {
      const { data, error } = await supabase
        .rpc('get_latest_chart_snapshot', {
          p_symbol_id: symbolId,
          p_timeframe: timeframe
        });

      if (data && data.length > 0) {
        setChartUrl(data[0].chart_url);
      } else {
        // Generate new chart
        await generateChart();
      }

      setLoading(false);
    }

    fetchLatestSnapshot();
  }, [symbolId, timeframe]);

  async function generateChart() {
    // Call FastAPI endpoint to generate chart
    const response = await fetch('/api/charts/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol_id: symbolId, timeframe })
    });

    const snapshot = await response.json();
    setChartUrl(snapshot.chart_url);
  }

  if (loading) return <div>Loading chart...</div>;
  if (!chartUrl) return <div>No chart available</div>;

  return (
    <div className="chart-snapshot">
      <img
        src={chartUrl}
        alt={`Chart ${timeframe}`}
        className="w-full h-auto rounded-lg shadow-lg"
      />
      <button onClick={generateChart} className="mt-2">
        Refresh Chart
      </button>
    </div>
  );
}
```

---

## Maintenance

### Daily Cleanup Job

Add to Celery Beat schedule (`services/agents/src/tasks.py`):

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('tasks')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run chart cleanup daily at 2 AM UTC
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_expired_charts.s(),
        name='cleanup-expired-charts'
    )

@app.task
def cleanup_expired_charts():
    """Delete expired chart snapshots"""
    result = supabase.rpc('cleanup_expired_chart_snapshots').execute()
    deleted_count = result.data
    print(f"Deleted {deleted_count} expired chart snapshots")
    return deleted_count
```

---

## Monitoring

### Key Metrics to Track

1. **Chart Generation Rate**
   ```sql
   SELECT
     DATE(generated_at) as date,
     trigger_type,
     COUNT(*) as count
   FROM chart_snapshots
   WHERE generated_at > NOW() - INTERVAL '7 days'
   GROUP BY DATE(generated_at), trigger_type
   ORDER BY date DESC;
   ```

2. **Storage Usage**
   ```sql
   SELECT
     COUNT(*) as total_snapshots,
     COUNT(DISTINCT symbol_id) as symbols_with_charts,
     COUNT(*) FILTER (WHERE expires_at < NOW()) as expired
   FROM chart_snapshots;
   ```

3. **Most Popular Timeframes**
   ```sql
   SELECT
     timeframe,
     COUNT(*) as count
   FROM chart_snapshots
   WHERE generated_at > NOW() - INTERVAL '30 days'
   GROUP BY timeframe
   ORDER BY count DESC;
   ```

---

## Troubleshooting

### Issue: "relation symbols does not exist"

**Cause:** Migration 010 not applied
**Solution:** Run migration 010 first

```bash
supabase migration up --to 010
```

### Issue: RLS policy blocks chart creation

**Cause:** User not authenticated
**Solution:** Ensure `auth.uid()` returns valid user ID

```sql
-- Check current user
SELECT auth.uid();

-- Should return UUID, not NULL
```

### Issue: Chart URL returns 404

**Cause:** Invalid TradingView symbol or chart-img.com API issue
**Solution:** Verify symbol mapping

```sql
SELECT chart_img_symbol FROM symbols WHERE id = 'YOUR_SYMBOL_ID';

-- Test URL manually:
-- https://api.chart-img.com/v2/tradingview/advanced-chart?symbol=XETR:DAX&interval=4h
```

---

## Resources

- [chart-img.com Documentation](https://chart-img.com/docs)
- [TradingView Symbol Search](https://www.tradingview.com/symbols/)
- [Supabase RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [TradeMatrix Architecture Docs](../../../docs/ARCHITECTURE.md)

---

## Next Steps

After successful migration:

1. ✅ Implement `ChartGenerator` service in FastAPI
2. ✅ Create React components for chart display
3. ✅ Add chart generation to morning planner reports
4. ✅ Integrate charts with liquidity alert notifications
5. ✅ Add chart snapshot management UI in dashboard
6. ✅ Set up automated cleanup job in Celery Beat
7. ✅ Monitor chart generation metrics

---

**Migration created by:** Agent 2: Database-Migration-Agent
**Part of:** Phase 5C - Chart Integration
**Related:** [AGENT_2_TASK.md](../../../AGENT_2_TASK.md)
