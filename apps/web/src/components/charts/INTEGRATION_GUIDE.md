# Chart Components Integration Guide

## Overview

This directory contains 7 React/TypeScript components for the chart-img.com integration (Phase 3).

## Components Created

### 1. **ChartConfigModal.tsx**
Main modal with 3 tabs (Basic, Indicators, Preview) for configuring chart settings per symbol.

**Props:**
- `symbol`: Symbol object with id, symbol, name, chart_config
- `isOpen`: Boolean to control modal visibility
- `onClose`: Callback when modal is closed
- `onSave`: Optional callback after successful save

**Features:**
- TradingView symbol mapping
- Timeframe multi-select
- Indicator selection
- Chart preview
- Saves to Supabase `market_symbols.chart_config`

---

### 2. **TimeframeSelector.tsx**
Multi-select checkbox component for timeframes (1m, 5m, 15m, 1h, 4h, 1d, 1W, 1M).

**Props:**
- `selected`: Array of selected timeframe strings
- `onChange`: Callback with updated timeframes array

**Features:**
- Validation: At least 1 timeframe required
- Grid layout (2 columns)

---

### 3. **IndicatorSelector.tsx**
Checkbox list for technical indicators (RSI, MACD, BB, Stochastic, Volume, EMA, SMA, ATR).

**Props:**
- `selected`: Array of selected indicator strings
- `onChange`: Callback with updated indicators array

**Features:**
- Multiple selection allowed
- TradingView-compatible indicator names

---

### 4. **ChartPreview.tsx**
Live preview of chart configuration using chart-img.com API.

**Props:**
- `config`: ChartPreviewConfig object with tv_symbol, timeframes, indicators, theme, dimensions, etc.

**Features:**
- Builds chart-img.com URL from config
- Shows image preview
- Displays generated URL for debugging
- Uses first timeframe for preview
- Error handling with placeholder

---

### 5. **ChartSnapshotGallery.tsx**
Grid view of saved chart snapshots with filters.

**Props:** None (standalone component)

**Features:**
- Fetches from `chart_snapshots` table with JOIN to `market_symbols`
- Filters by agent and timeframe
- Refresh button
- Grid layout (1/2/3 columns responsive)
- Shows 50 most recent snapshots

---

### 6. **ChartSnapshotCard.tsx**
Individual snapshot card with delete action.

**Props:**
- `snapshot`: Snapshot object with id, chart_url, timeframe, created_by_agent, symbol
- `onDelete`: Callback after successful deletion

**Features:**
- Displays chart image
- Shows symbol, timeframe badge
- External link button
- Delete confirmation
- Relative time display ("5 min ago")

---

### 7. **ChartConfigButton.tsx**
Trigger button to open ChartConfigModal.

**Props:**
- `symbol`: Symbol object
- `onSave`: Optional callback after save

**Features:**
- Settings icon + text
- Opens modal on click

---

## Integration Instructions

### Option A: Use New Components in `/charts/`

If you want to use these newly created components:

#### 1. Market Symbols Card (Add Chart Config Button)

**File:** `apps/web/src/components/dashboard/market-symbols-card.tsx` (if exists) or integrate into watchlist display

```tsx
import { ChartConfigButton } from '@/components/charts'

// Inside symbol card render:
<div className="flex items-center justify-between">
  <div>
    <h3 className="font-semibold">{symbol.name}</h3>
    <p className="text-xs text-muted-foreground">{symbol.symbol}</p>
  </div>
  <ChartConfigButton symbol={symbol} onSave={loadSymbols} />
</div>
```

#### 2. Dashboard Page (Add Chart Snapshots Tab)

**File:** `apps/web/src/app/(dashboard)/dashboard/page.tsx`

```tsx
import { ChartSnapshotGallery } from '@/components/charts'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

// Add to existing dashboard layout:
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="charts">Chart Snapshots</TabsTrigger>
  </TabsList>

  <TabsContent value="overview">
    {/* Existing dashboard content */}
  </TabsContent>

  <TabsContent value="charts">
    <ChartSnapshotGallery />
  </TabsContent>
</Tabs>
```

#### 3. Charts Page (Optional)

**File:** `apps/web/src/app/(dashboard)/dashboard/charts/page.tsx`

Add snapshot gallery below existing chart:

```tsx
import { ChartSnapshotGallery } from '@/components/charts'

// After TradingChart component:
<ChartSnapshotGallery />
```

---

### Option B: Keep Existing Components in `/dashboard/`

If you prefer to keep using existing components in `/dashboard/`, you can:

1. **Delete the new `/charts/` directory** (duplicate functionality)
2. **Use existing components:**
   - `SymbolEditModal` (instead of ChartConfigModal)
   - `ChartGeneratorWidget` (instead of ChartConfigButton)
   - `ChartSnapshotsGallery` (instead of ChartSnapshotGallery)
   - Existing timeframe/indicator selectors

These components already provide similar functionality and are integrated into the codebase.

---

## Files That Need Updates

If using new `/charts/` components:

### 1. Market Symbols Display
**Location:** Where watchlist symbols are rendered (likely in `dashboard/page.tsx` or a MarketSymbolsCard component)

**Changes:**
- Import `ChartConfigButton`
- Add button next to each symbol
- Pass symbol data to button

### 2. Dashboard Page
**Location:** `apps/web/src/app/(dashboard)/dashboard/page.tsx`

**Changes:**
- Import `ChartSnapshotGallery`
- Add Tabs component with "Chart Snapshots" tab
- Render ChartSnapshotGallery in tab content

### 3. Charts Page (Optional)
**Location:** `apps/web/src/app/(dashboard)/dashboard/charts/page.tsx`

**Changes:**
- Import `ChartSnapshotGallery`
- Add gallery below existing chart

---

## Database Requirements

These components expect the following database schema:

### 1. `market_symbols` table
```sql
ALTER TABLE market_symbols ADD COLUMN chart_config JSONB;
```

### 2. `chart_snapshots` table
```sql
CREATE TABLE chart_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol_id UUID REFERENCES market_symbols(id) ON DELETE CASCADE,
  timeframe TEXT NOT NULL,
  chart_url TEXT NOT NULL,
  created_by_agent TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  ...
);
```

See `docs/FEATURES/chart-img-integration/02_DATABASE_SCHEMA.md` for full schema.

---

## Styling & Responsiveness

All components use:
- **shadcn/ui** primitives (Dialog, Tabs, Button, Card, etc.)
- **Tailwind CSS** for styling
- **Dark mode** support (auto-adapts)
- **Responsive design:**
  - Modal: Full-screen on mobile, centered on desktop
  - Grid: 1 column mobile, 2 tablet, 3 desktop

---

## Error Handling

- Network errors show toast notifications
- Image loading errors show placeholder
- Form validation with error messages
- Delete confirmations before destructive actions

---

## Testing

Manual testing checklist:

1. Click "Chart Config" → Modal opens
2. Select timeframes → Preview updates
3. Select indicators → Preview updates
4. Save config → Database updated, toast shown
5. Navigate to Chart Snapshots tab → Gallery loads
6. Filter by agent → Results update
7. Filter by timeframe → Results update
8. Delete snapshot → Confirmation shown, deleted on confirm
9. Refresh button → Gallery reloads

---

## Next Steps

1. **Choose integration approach** (Option A or B above)
2. **Execute database migrations** (if not done)
3. **Integrate components** into dashboard/charts pages
4. **Test all user flows**
5. **Deploy frontend** to Netlify
6. **Implement backend** (Phase 4: Agent Integration)

---

## Notes

- **Duplicate Functionality:** Similar components already exist in `/dashboard/`. This implementation follows the architecture spec in `04_FRONTEND_COMPONENTS.md` more closely.
- **Naming Convention:** Documentation uses different names than existing implementation (ChartConfigModal vs SymbolEditModal).
- **Consider Refactoring:** Decide whether to consolidate or keep both sets of components.

---

**Created:** 2025-11-05
**Status:** Implementation complete, integration pending
**Next Phase:** Agent Integration (Phase 4)
