# AI Agents Page Implementation - Phase 4D

## Overview
Created a new `/agents` page in the Next.js dashboard to display AI-generated trading setups from the 5 AI agents. The page shows trading setup cards with inline chart images, pattern detection results, and analysis details.

## Implementation Summary

### Files Created (4 new files)

#### 1. **Page Route**: `/apps/web/src/app/(dashboard)/agents/page.tsx`
- **Type**: Server Component (RSC)
- **Purpose**: Main agents page that fetches and displays trading setups
- **Features**:
  - Fetches trading setups from `chart_analyses` table
  - Supports agent filtering via URL query params
  - Server-side data fetching with Supabase
  - Renders stats, filters, and setup cards

**Key Functions**:
```typescript
async function getSetups(agentFilter?: string[]): Promise<TradingSetup[]>
```
- Queries `chart_analyses` table (ChartWatcher/SignalBot results)
- Joins with `market_symbols` for symbol names
- Filters by selected agents
- Returns up to 50 recent setups

**Data Structure**:
```typescript
interface TradingSetup {
  id: string
  symbol_id: string
  symbol: string
  timeframe: string
  agent_name: string
  analysis: string
  chart_url: string
  chart_snapshot_id: string | null
  confidence_score: number
  created_at: string
  metadata: {
    setup_type?: string
    entry?: number
    sl?: number
    tp?: number
    patterns?: Pattern[]
    trend?: string
    support_levels?: number[]
    resistance_levels?: number[]
  }
}
```

#### 2. **Component**: `/apps/web/src/components/agents/trading-setup-card.tsx`
- **Type**: Client Component
- **Purpose**: Display individual trading setup with inline chart
- **Features**:
  - Symbol + timeframe badges
  - Agent name badge with color coding
  - Trend indicator (bullish/bearish/sideways)
  - Inline chart image (not clickable gallery)
  - Analysis text summary
  - Detected patterns list
  - Entry/SL/TP levels (if available)
  - Support/Resistance levels
  - Confidence score
  - Timestamp (relative format)

**Agent Colors**:
- ChartWatcher: Blue
- SignalBot: Green
- MorningPlanner: Purple
- JournalBot: Orange
- USOpenPlanner: Pink

**Layout**: Card with chart at top, details below
**Responsive**: Full width mobile, 2 cols tablet, 3 cols desktop

#### 3. **Component**: `/apps/web/src/components/agents/agent-filter.tsx`
- **Type**: Client Component
- **Purpose**: Multi-select filter for 5 agents
- **Features**:
  - Checkbox grid for agent selection
  - Apply filter button
  - Clear filter button
  - Shows selected count
  - Uses URL query params for state persistence

**Available Agents**:
1. ChartWatcher - Pattern Detection & Analysis
2. SignalBot - Entry & Exit Signals
3. MorningPlanner - Daily Market Setup
4. JournalBot - Trade Review & Analysis
5. US Open Planner - US Market Opening Strategy

**URL Format**: `/agents?agents=ChartWatcher,SignalBot`

#### 4. **Component**: `/apps/web/src/components/agents/setup-stats.tsx`
- **Type**: Client Component (receives data as props)
- **Purpose**: Display aggregate statistics
- **Stats Displayed**:
  - **Setups Today**: Count of setups created today
  - **Active Setups**: High confidence setups (score >= 0.8)
  - **Avg Quality**: Average confidence score across all setups
  - **Latest Update**: Time since last setup + most active agent

**Layout**: 4 stat cards in responsive grid

### Files Modified (1 file)

#### 5. **Navigation**: `/apps/web/src/components/dashboard/sidebar.tsx`
- **Change**: Added "AI Agents" link between Dashboard and Trades
- **Icon**: Bot icon from lucide-react
- **Path**: `/agents`
- **Position**: 2nd item in navigation

**Updated Navigation Order**:
1. Dashboard
2. **AI Agents** (NEW)
3. Trades
4. Charts
5. Symbols
6. Reports
7. Profile

## Database Schema Assumptions

The page queries the following Supabase tables:

### 1. `chart_analyses` table
**Created by**: Migration 006 (`006_chart_analyses_table.sql`)
**Used by**: ChartWatcher and SignalBot agents
**Columns Used**:
```sql
- id (UUID)
- symbol_id (UUID, references market_symbols)
- timeframe (TEXT: '1m', '5m', '15m', '1h', '4h', '1d', '1w')
- chart_url (TEXT)
- patterns_detected (JSONB array)
- trend (TEXT: 'bullish', 'bearish', 'sideways', 'unknown')
- support_levels (DECIMAL[])
- resistance_levels (DECIMAL[])
- confidence_score (DECIMAL 0.0-1.0)
- analysis_summary (TEXT)
- created_at (TIMESTAMPTZ)
- payload (JSONB)
```

### 2. `market_symbols` table
**Purpose**: Symbol metadata
**Joined for**: Symbol name display
**Column Used**: `symbol` (e.g., "DAX", "NASDAQ")

### 3. Future Tables (not implemented yet)
For MorningPlanner, JournalBot, and USOpenPlanner, these tables would be needed:

**`morning_setups`** (for MorningPlanner):
```sql
- id (UUID)
- symbol_id (UUID)
- setup_type (TEXT)
- bias ('bullish' | 'bearish')
- chart_url_1h (TEXT)
- chart_url_15m (TEXT)
- chart_url_1d (TEXT)
- analysis (TEXT)
- confidence (DECIMAL)
- created_at (TIMESTAMPTZ)
```

**`signals`** (for SignalBot):
**Already exists** (Migration 005)
```sql
- id (UUID)
- symbol_id (UUID)
- setup_id (UUID)
- signal_type ('entry' | 'exit')
- side ('long' | 'short')
- price (DECIMAL)
- confidence (DECIMAL)
- metadata (JSONB)
- created_at (TIMESTAMPTZ)
```

## Integration with AI Agents

### ChartWatcher Agent
**File**: `hetzner-deploy/src/chart_watcher.py`
**Execution**: Every 5 minutes (Celery scheduler)
**Output**: Inserts records into `chart_analyses` table
**Chart Generation**: Uses chart-img.com API via `ChartService`
**Timeframes**: 5m (scalping), 15m (intraday)

**Flow**:
1. Fetches active symbols from `market_symbols`
2. Generates chart URLs for 5m and 15m
3. Downloads chart images
4. Analyzes with OpenAI Vision API (pattern detection)
5. Inserts analysis into `chart_analyses` table
6. Saves chart snapshot to `chart_snapshots` table

### SignalBot Agent
**File**: `hetzner-deploy/src/signal_bot.py`
**Execution**: Every 60 seconds (Celery scheduler)
**Output**: Could insert into `chart_analyses` or separate `signals` table
**Chart Generation**: Uses chart-img.com API via `ChartService`
**Timeframes**: 15m, 1h

**Flow**:
1. Analyzes market structure (EMAs, RSI, MACD, etc.)
2. Generates entry/exit signals
3. Validates signals with ValidationEngine
4. Generates charts for valid signals
5. Inserts into database

### MorningPlanner, JournalBot, USOpenPlanner
**Status**: Planned but not yet implemented
**Future Work**: These agents would need dedicated database tables and backend implementations

## Styling & UI Components

### shadcn/ui Components Used
- `Card`, `CardContent`, `CardHeader`, `CardTitle` - Layout
- `Badge` - Agent names, timeframes, trends
- `Button` - Filter actions
- `Checkbox` - Agent selection
- `Alert`, `AlertDescription` - Error messages

### Lucide Icons Used
- `Bot` - AI agent icon
- `TrendingUp`, `TrendingDown`, `Minus` - Trend indicators
- `Clock` - Timestamp
- `Activity`, `Target` - Stats icons
- `FilterX` - Clear filter

### Responsive Design
- Mobile: 1 column cards, full width
- Tablet (md): 2 column cards
- Desktop (lg): 3 column cards

### Dark Mode Support
- All components support dark mode via next-themes
- Chart images: dark theme applied via chart-img.com API

## Dependencies

### Already Installed (verified)
- `date-fns@^4.1.0` - Date formatting (formatDistanceToNow)
- `@supabase/ssr@^0.7.0` - Server-side Supabase client
- `@supabase/supabase-js@^2.76.1` - Client-side Supabase
- `lucide-react@^0.548.0` - Icons
- `next@^16.0.0` - Framework
- All shadcn/ui components (already installed)

### TypeScript Configuration
- Mode: Strict
- No TypeScript errors in new code
- Used `as any` for `chart_analyses` table (not in generated types yet)

## Backend Requirements

### Deployment Checklist

1. **Database Migration Status**:
   - ✅ Migration 006: `chart_analyses` table exists
   - ✅ Migration 020: `chart_snapshots` table exists
   - ⚠️ TypeScript types need regeneration to include `chart_analyses`

2. **Agent Deployment**:
   - ✅ ChartWatcher deployed on Hetzner (CX11 server)
   - ✅ SignalBot implemented (needs deployment)
   - ❌ MorningPlanner not implemented
   - ❌ JournalBot not implemented
   - ❌ USOpenPlanner not implemented

3. **Data Requirements**:
   - At least one `chart_analyses` record to display setups
   - ChartWatcher must run successfully and insert data
   - Chart URLs must be valid and accessible

### Testing Data

To test the page without waiting for agents:

**Insert Test Data** (SQL):
```sql
INSERT INTO chart_analyses (
  symbol_id,
  timeframe,
  chart_url,
  patterns_detected,
  trend,
  support_levels,
  resistance_levels,
  confidence_score,
  analysis_summary,
  payload
) VALUES (
  (SELECT id FROM market_symbols WHERE symbol = 'DAX' LIMIT 1),
  '1h',
  'https://api.chart-img.com/tradingview/advanced-chart?symbol=TVC:DAX&interval=1h',
  '[{"name": "head_and_shoulders", "type": "bearish", "confidence": 0.85}]'::jsonb,
  'bearish',
  ARRAY[19300.0, 19200.0],
  ARRAY[19500.0, 19600.0],
  0.85,
  'Bearish head and shoulders pattern detected with strong resistance at 19500',
  '{}'::jsonb
);
```

## Known Limitations

1. **Database Types**:
   - `chart_analyses` table not in generated TypeScript types
   - Using `as any` workaround (regenerate types with `supabase gen types`)

2. **Missing Agent Data**:
   - Only ChartWatcher data available initially
   - MorningPlanner, JournalBot, USOpenPlanner need backend implementation

3. **Chart Image Loading**:
   - No loading states for images (Next.js Image handles this)
   - Failed images hide silently (via onError handler)

4. **Real-time Updates**:
   - Page uses static data fetching (SSR)
   - Requires page refresh to see new setups
   - Future: Add real-time subscriptions with Supabase Realtime

5. **Pagination**:
   - Limited to 50 most recent setups
   - No pagination UI yet
   - Future: Add infinite scroll or pagination

## Future Enhancements

1. **Real-time Updates**:
   ```typescript
   // Use Supabase Realtime
   supabase
     .channel('chart_analyses')
     .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'chart_analyses' }, payload => {
       // Update setups list
     })
     .subscribe()
   ```

2. **Setup Details Modal**:
   - Click card to open detailed view
   - Show full analysis, all patterns, complete levels
   - Chart comparison (multiple timeframes)

3. **Export/Share**:
   - Export setup as PDF
   - Share setup link
   - Copy trading parameters

4. **Performance Tracking**:
   - Track setup outcomes (win/loss)
   - Calculate agent accuracy
   - Display historical performance

5. **Notifications**:
   - Browser push when new high-confidence setup
   - Email digest of daily setups

## Testing Checklist

### Manual Testing
- [ ] Navigate to `/agents` from sidebar
- [ ] Verify page loads without errors
- [ ] Check "No setups" state displays correctly
- [ ] Verify setup cards display with mock/real data
- [ ] Test agent filter selection
- [ ] Test filter apply/clear functionality
- [ ] Verify chart images load correctly
- [ ] Check responsive layout (mobile, tablet, desktop)
- [ ] Test dark mode appearance
- [ ] Verify stats calculations
- [ ] Check timestamp formatting

### Backend Testing
- [ ] ChartWatcher agent running on Hetzner
- [ ] Chart analyses being inserted into database
- [ ] Chart URLs are valid and accessible
- [ ] Supabase RLS policies allow public read access

### Integration Testing
- [ ] Test with 0 setups (empty state)
- [ ] Test with 1 setup
- [ ] Test with 50+ setups (pagination limit)
- [ ] Test with all agent types
- [ ] Test filter with different agent combinations

## Deployment Instructions

### 1. Deploy Frontend (Netlify)
```bash
cd apps/web
npm run build
# Verify build succeeds
# Deploy to Netlify
```

### 2. Verify Database
```sql
-- Check chart_analyses table exists
SELECT * FROM chart_analyses LIMIT 1;

-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'chart_analyses';
```

### 3. Verify Agents
```bash
# SSH to Hetzner server
ssh root@135.181.195.241

# Check ChartWatcher status
docker logs hetzner-deploy-celery_worker-1

# Check latest chart analyses
# (via Supabase SQL Editor)
SELECT COUNT(*) FROM chart_analyses;
```

### 4. Access Page
- URL: `https://tradematrix.netlify.app/agents`
- Login required (protected by dashboard layout)

## Documentation
- User Guide: (TODO: Add user documentation)
- API Reference: See `chart_watcher.py` and `signal_bot.py`
- Database Schema: See migrations 005, 006, 020

## Support
- Questions: Contact development team
- Issues: Create GitHub issue
- Feature Requests: Add to roadmap discussion

---

**Implementation Date**: 2025-11-05
**Implemented By**: Claude Code
**Status**: ✅ Ready for Testing
**Next Steps**: Deploy to Netlify, verify with real agent data
