# Frontend Components

## Overview

React Components für die chart-img.com Integration. Diese Components ermöglichen User, Chart-Konfigurationen zu verwalten und Chart-Snapshots anzuzeigen.

## Technology Stack

- **Framework**: Next.js 16 (App Router)
- **UI Library**: shadcn/ui
- **Styling**: Tailwind CSS
- **State Management**: React Hooks (useState, useEffect)
- **API Client**: Supabase Client
- **TypeScript**: 5.x

---

## Component Structure

```
apps/web/src/components/
├── charts/
│   ├── ChartConfigModal.tsx          # Main configuration modal
│   ├── TimeframeSelector.tsx         # Multi-select for timeframes
│   ├── IndicatorSelector.tsx         # Checkbox list for indicators
│   ├── ChartPreview.tsx              # Live chart preview
│   ├── ChartSnapshotGallery.tsx      # Grid view of snapshots
│   ├── ChartSnapshotCard.tsx         # Single snapshot card
│   └── ChartConfigButton.tsx         # Trigger button for modal
└── dashboard/
    └── MarketSymbolsCard.tsx         # Extended with chart config button
```

---

## 1. ChartConfigModal

Main modal for configuring chart settings per symbol.

### Props

```typescript
interface ChartConfigModalProps {
  symbol: {
    id: string;
    symbol: string;
    name: string;
    chart_config?: ChartConfig;
  };
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: ChartConfig) => void;
}

interface ChartConfig {
  tv_symbol: string;
  timeframes: string[];
  indicators: string[];
  chart_type: "candles" | "bars" | "line" | "area";
  theme: "dark" | "light";
  width: number;
  height: number;
  show_volume: boolean;
  show_legend: boolean;
  timezone: string;
}
```

### Implementation

```typescript
// apps/web/src/components/charts/ChartConfigModal.tsx
"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import TimeframeSelector from "./TimeframeSelector";
import IndicatorSelector from "./IndicatorSelector";
import ChartPreview from "./ChartPreview";
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";
import { toast } from "sonner";

const SYMBOL_MAPPING: Record<string, string> = {
  "^GDAXI": "XETR:DAX",
  "^NDX": "NASDAQ:NDX",
  "^DJI": "DJCFD:DJI",
  "EURUSD=X": "OANDA:EURUSD",
  "EURGBP=X": "OANDA:EURGBP",
  "GBPUSD=X": "OANDA:GBPUSD",
};

export default function ChartConfigModal({ symbol, isOpen, onClose, onSave }: ChartConfigModalProps) {
  const supabase = createClientComponentClient();

  const [config, setConfig] = useState<ChartConfig>({
    tv_symbol: SYMBOL_MAPPING[symbol.symbol] || symbol.symbol,
    timeframes: ["15", "60", "D"],
    indicators: [],
    chart_type: "candles",
    theme: "dark",
    width: 1200,
    height: 800,
    show_volume: true,
    show_legend: true,
    timezone: "Europe/Berlin",
  });

  const [isSaving, setIsSaving] = useState(false);

  // Load existing config
  useEffect(() => {
    if (symbol.chart_config) {
      setConfig(symbol.chart_config);
    }
  }, [symbol.chart_config]);

  const handleSave = async () => {
    setIsSaving(true);

    try {
      // Update chart_config in Supabase
      const { error } = await supabase
        .from("market_symbols")
        .update({ chart_config: config })
        .eq("id", symbol.id);

      if (error) throw error;

      toast.success("Chart configuration saved");
      onSave(config);
      onClose();
    } catch (error) {
      console.error("Error saving chart config:", error);
      toast.error("Failed to save chart configuration");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Chart Configuration - {symbol.name} ({symbol.symbol})
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="basic" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">Basic</TabsTrigger>
            <TabsTrigger value="indicators">Indicators</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-4">
            {/* TradingView Symbol */}
            <div className="space-y-2">
              <Label htmlFor="tv_symbol">TradingView Symbol</Label>
              <Input
                id="tv_symbol"
                value={config.tv_symbol}
                onChange={(e) => setConfig({ ...config, tv_symbol: e.target.value })}
                placeholder="XETR:DAX"
              />
              <p className="text-xs text-muted-foreground">
                Find symbols at tradingview.com (e.g., XETR:DAX, NASDAQ:NDX)
              </p>
            </div>

            {/* Timeframes */}
            <TimeframeSelector
              selected={config.timeframes}
              onChange={(timeframes) => setConfig({ ...config, timeframes })}
            />

            {/* Chart Type */}
            <div className="space-y-2">
              <Label htmlFor="chart_type">Chart Type</Label>
              <Select
                value={config.chart_type}
                onValueChange={(value) => setConfig({ ...config, chart_type: value as any })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="candles">Candlesticks</SelectItem>
                  <SelectItem value="bars">Bars (OHLC)</SelectItem>
                  <SelectItem value="line">Line</SelectItem>
                  <SelectItem value="area">Area</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Theme */}
            <div className="space-y-2">
              <Label htmlFor="theme">Theme</Label>
              <Select
                value={config.theme}
                onValueChange={(value) => setConfig({ ...config, theme: value as any })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="light">Light</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Dimensions */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="width">Width (px)</Label>
                <Input
                  id="width"
                  type="number"
                  value={config.width}
                  onChange={(e) => setConfig({ ...config, width: parseInt(e.target.value) })}
                  min={800}
                  max={1920}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="height">Height (px)</Label>
                <Input
                  id="height"
                  type="number"
                  value={config.height}
                  onChange={(e) => setConfig({ ...config, height: parseInt(e.target.value) })}
                  min={600}
                  max={1600}
                />
              </div>
            </div>

            {/* Switches */}
            <div className="flex items-center justify-between">
              <Label htmlFor="show_volume">Show Volume</Label>
              <Switch
                id="show_volume"
                checked={config.show_volume}
                onCheckedChange={(checked) => setConfig({ ...config, show_volume: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="show_legend">Show Legend</Label>
              <Switch
                id="show_legend"
                checked={config.show_legend}
                onCheckedChange={(checked) => setConfig({ ...config, show_legend: checked })}
              />
            </div>
          </TabsContent>

          <TabsContent value="indicators" className="space-y-4">
            <IndicatorSelector
              selected={config.indicators}
              onChange={(indicators) => setConfig({ ...config, indicators })}
            />
          </TabsContent>

          <TabsContent value="preview" className="space-y-4">
            <ChartPreview config={config} />
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Configuration"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 2. TimeframeSelector

Multi-select component for timeframes.

### Implementation

```typescript
// apps/web/src/components/charts/TimeframeSelector.tsx
"use client";

import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

const TIMEFRAMES = [
  { value: "1", label: "1 Minute" },
  { value: "5", label: "5 Minutes" },
  { value: "15", label: "15 Minutes (M15)" },
  { value: "60", label: "1 Hour (H1)" },
  { value: "240", label: "4 Hours (H4)" },
  { value: "D", label: "1 Day (D1)" },
  { value: "W", label: "1 Week" },
  { value: "M", label: "1 Month" },
];

interface TimeframeSelectorProps {
  selected: string[];
  onChange: (timeframes: string[]) => void;
}

export default function TimeframeSelector({ selected, onChange }: TimeframeSelectorProps) {
  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((tf) => tf !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <div className="space-y-2">
      <Label>Timeframes</Label>
      <div className="grid grid-cols-2 gap-3">
        {TIMEFRAMES.map((tf) => (
          <div key={tf.value} className="flex items-center space-x-2">
            <Checkbox
              id={`tf-${tf.value}`}
              checked={selected.includes(tf.value)}
              onCheckedChange={() => handleToggle(tf.value)}
            />
            <label
              htmlFor={`tf-${tf.value}`}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
            >
              {tf.label}
            </label>
          </div>
        ))}
      </div>
      {selected.length === 0 && (
        <p className="text-xs text-destructive">Please select at least one timeframe</p>
      )}
    </div>
  );
}
```

---

## 3. IndicatorSelector

Checkbox list for technical indicators.

### Implementation

```typescript
// apps/web/src/components/charts/IndicatorSelector.tsx
"use client";

import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

const INDICATORS = [
  { value: "RSI@tv-basicstudies", label: "RSI (Relative Strength Index)" },
  { value: "MACD@tv-basicstudies", label: "MACD" },
  { value: "BB@tv-basicstudies", label: "Bollinger Bands" },
  { value: "Stochastic@tv-basicstudies", label: "Stochastic" },
  { value: "Volume@tv-basicstudies", label: "Volume" },
  { value: "EMA@tv-basicstudies", label: "EMA (Exponential Moving Average)" },
  { value: "SMA@tv-basicstudies", label: "SMA (Simple Moving Average)" },
  { value: "ATR@tv-basicstudies", label: "ATR (Average True Range)" },
];

interface IndicatorSelectorProps {
  selected: string[];
  onChange: (indicators: string[]) => void;
}

export default function IndicatorSelector({ selected, onChange }: IndicatorSelectorProps) {
  const handleToggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((ind) => ind !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <div className="space-y-2">
      <Label>Technical Indicators</Label>
      <p className="text-sm text-muted-foreground">
        Select indicators to overlay on your charts
      </p>
      <div className="grid grid-cols-2 gap-3 pt-2">
        {INDICATORS.map((ind) => (
          <div key={ind.value} className="flex items-center space-x-2">
            <Checkbox
              id={`ind-${ind.value}`}
              checked={selected.includes(ind.value)}
              onCheckedChange={() => handleToggle(ind.value)}
            />
            <label
              htmlFor={`ind-${ind.value}`}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
            >
              {ind.label}
            </label>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 4. ChartPreview

Live preview of chart configuration (shows generated URL).

### Implementation

```typescript
// apps/web/src/components/charts/ChartPreview.tsx
"use client";

import { useState, useEffect } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { InfoIcon } from "lucide-react";

interface ChartPreviewProps {
  config: ChartConfig;
}

export default function ChartPreview({ config }: ChartPreviewProps) {
  const [chartUrl, setChartUrl] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Build chart-img.com URL
    const buildChartUrl = () => {
      const params = new URLSearchParams({
        symbol: config.tv_symbol,
        interval: config.timeframes[0] || "60", // Use first timeframe for preview
        theme: config.theme,
        width: config.width.toString(),
        height: config.height.toString(),
        hide_top_toolbar: "false",
        hide_legend: (!config.show_legend).toString(),
        hide_side_toolbar: "false",
      });

      if (config.indicators.length > 0) {
        params.append("studies", config.indicators.join(","));
      }

      if (!config.show_volume) {
        params.append("hide_volume", "true");
      }

      return `https://api.chart-img.com/tradingview/advanced-chart?${params.toString()}`;
    };

    const url = buildChartUrl();
    setChartUrl(url);
    setIsLoading(false);
  }, [config]);

  if (isLoading) {
    return <Skeleton className="w-full h-[400px]" />;
  }

  return (
    <div className="space-y-4">
      <Alert>
        <InfoIcon className="h-4 w-4" />
        <AlertDescription>
          This is a preview using the first selected timeframe ({config.timeframes[0] || "H1"}).
          All configured timeframes will be available to AI agents.
        </AlertDescription>
      </Alert>

      <div className="border rounded-lg overflow-hidden bg-muted">
        <img
          src={chartUrl}
          alt={`Chart preview for ${config.tv_symbol}`}
          className="w-full h-auto"
          onError={(e) => {
            (e.target as HTMLImageElement).src = "https://via.placeholder.com/1200x800?text=Chart+Preview+Unavailable";
          }}
        />
      </div>

      <div className="text-xs text-muted-foreground break-all">
        <strong>Generated URL:</strong>
        <br />
        {chartUrl}
      </div>
    </div>
  );
}
```

---

## 5. ChartSnapshotGallery

Grid view of saved chart snapshots.

### Implementation

```typescript
// apps/web/src/components/charts/ChartSnapshotGallery.tsx
"use client";

import { useState, useEffect } from "react";
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import ChartSnapshotCard from "./ChartSnapshotCard";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface ChartSnapshot {
  id: string;
  symbol_id: string;
  chart_url: string;
  timeframe: string;
  created_by_agent: string;
  metadata: any;
  created_at: string;
  symbol: {
    symbol: string;
    name: string;
  };
}

export default function ChartSnapshotGallery() {
  const supabase = createClientComponentClient();
  const [snapshots, setSnapshots] = useState<ChartSnapshot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterAgent, setFilterAgent] = useState<string | null>(null);
  const [filterTimeframe, setFilterTimeframe] = useState<string | null>(null);

  useEffect(() => {
    loadSnapshots();
  }, [filterAgent, filterTimeframe]);

  const loadSnapshots = async () => {
    setIsLoading(true);

    try {
      let query = supabase
        .from("chart_snapshots")
        .select(`
          *,
          symbol:market_symbols(symbol, name)
        `)
        .order("created_at", { ascending: false })
        .limit(50);

      if (filterAgent) {
        query = query.eq("created_by_agent", filterAgent);
      }

      if (filterTimeframe) {
        query = query.eq("timeframe", filterTimeframe);
      }

      const { data, error } = await query;

      if (error) throw error;

      setSnapshots(data || []);
    } catch (error) {
      console.error("Error loading snapshots:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const uniqueAgents = Array.from(new Set(snapshots.map((s) => s.created_by_agent)));
  const uniqueTimeframes = Array.from(new Set(snapshots.map((s) => s.timeframe)));

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Chart Snapshots</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="w-full h-[300px]" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Chart Snapshots ({snapshots.length})</CardTitle>
          <div className="flex gap-2">
            <Select value={filterAgent || "all"} onValueChange={(v) => setFilterAgent(v === "all" ? null : v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by agent" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Agents</SelectItem>
                {uniqueAgents.map((agent) => (
                  <SelectItem key={agent} value={agent}>
                    {agent}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filterTimeframe || "all"} onValueChange={(v) => setFilterTimeframe(v === "all" ? null : v)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by timeframe" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Timeframes</SelectItem>
                {uniqueTimeframes.map((tf) => (
                  <SelectItem key={tf} value={tf}>
                    {tf}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button variant="outline" onClick={loadSnapshots}>
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {snapshots.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No chart snapshots found. Configure symbols and let AI agents generate charts.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {snapshots.map((snapshot) => (
              <ChartSnapshotCard key={snapshot.id} snapshot={snapshot} onDelete={loadSnapshots} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

---

## 6. ChartSnapshotCard

Single snapshot card with delete action.

### Implementation

```typescript
// apps/web/src/components/charts/ChartSnapshotCard.tsx
"use client";

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrashIcon, ExternalLinkIcon } from "lucide-react";
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

interface ChartSnapshotCardProps {
  snapshot: ChartSnapshot;
  onDelete: () => void;
}

export default function ChartSnapshotCard({ snapshot, onDelete }: ChartSnapshotCardProps) {
  const supabase = createClientComponentClient();

  const handleDelete = async () => {
    if (!confirm("Delete this chart snapshot?")) return;

    try {
      const { error } = await supabase.from("chart_snapshots").delete().eq("id", snapshot.id);

      if (error) throw error;

      toast.success("Chart snapshot deleted");
      onDelete();
    } catch (error) {
      console.error("Error deleting snapshot:", error);
      toast.error("Failed to delete snapshot");
    }
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">
              {snapshot.symbol?.name || "Unknown"}
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              {snapshot.symbol?.symbol || "N/A"}
            </p>
          </div>
          <Badge variant="secondary">{snapshot.timeframe}</Badge>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <div className="aspect-video bg-muted rounded-md overflow-hidden">
          <img
            src={snapshot.chart_url}
            alt={`Chart for ${snapshot.symbol?.symbol}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = "https://via.placeholder.com/400x300?text=Chart+Unavailable";
            }}
          />
        </div>
      </CardContent>
      <CardFooter className="flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          <div>{snapshot.created_by_agent}</div>
          <div>{formatDistanceToNow(new Date(snapshot.created_at), { addSuffix: true })}</div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" asChild>
            <a href={snapshot.chart_url} target="_blank" rel="noopener noreferrer">
              <ExternalLinkIcon className="h-4 w-4" />
            </a>
          </Button>
          <Button variant="ghost" size="sm" onClick={handleDelete}>
            <TrashIcon className="h-4 w-4" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
```

---

## 7. ChartConfigButton

Trigger button to open ChartConfigModal (integrated into existing cards).

### Implementation

```typescript
// apps/web/src/components/charts/ChartConfigButton.tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SettingsIcon } from "lucide-react";
import ChartConfigModal from "./ChartConfigModal";

interface ChartConfigButtonProps {
  symbol: {
    id: string;
    symbol: string;
    name: string;
    chart_config?: any;
  };
  onSave?: () => void;
}

export default function ChartConfigButton({ symbol, onSave }: ChartConfigButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleSave = () => {
    setIsOpen(false);
    onSave?.();
  };

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <SettingsIcon className="h-4 w-4 mr-2" />
        Chart Config
      </Button>

      <ChartConfigModal symbol={symbol} isOpen={isOpen} onClose={() => setIsOpen(false)} onSave={handleSave} />
    </>
  );
}
```

---

## User Flows

### Flow 1: Configure Chart Settings

```
User clicks "Chart Config" button on Market Symbol Card
  → ChartConfigModal opens
    → User selects timeframes (M15, H1, D1)
    → User selects indicators (RSI, MACD)
    → User switches to Preview tab
      → Sees live chart preview
    → User clicks "Save Configuration"
      → Config saved to Supabase (market_symbols.chart_config)
      → Toast notification: "Chart configuration saved"
      → Modal closes
```

### Flow 2: View Chart Snapshots

```
User navigates to Dashboard → Chart Snapshots tab
  → ChartSnapshotGallery loads
    → Fetches chart_snapshots from Supabase
    → Displays grid of ChartSnapshotCards
    → User filters by Agent (e.g., "ChartWatcher")
      → Grid updates with filtered results
    → User clicks external link icon
      → Chart opens in new tab (full resolution)
```

### Flow 3: Delete Chart Snapshot

```
User clicks trash icon on ChartSnapshotCard
  → Confirm dialog: "Delete this chart snapshot?"
    → User confirms
      → DELETE request to Supabase
      → Toast notification: "Chart snapshot deleted"
      → Gallery refreshes
```

---

## Integration with Existing Components

### Extend MarketSymbolsCard

```typescript
// apps/web/src/components/dashboard/market-symbols-card.tsx

import ChartConfigButton from "@/components/charts/ChartConfigButton";

// Inside MarketSymbolsCard render:
<div className="flex items-center justify-between">
  <div>
    <h3 className="font-semibold">{symbol.name}</h3>
    <p className="text-xs text-muted-foreground">{symbol.symbol}</p>
  </div>
  <ChartConfigButton symbol={symbol} onSave={loadSymbols} />
</div>
```

### Add Chart Snapshots Tab to Dashboard

```typescript
// apps/web/src/app/(dashboard)/dashboard/page.tsx

import ChartSnapshotGallery from "@/components/charts/ChartSnapshotGallery";

// Add new tab
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="charts">Chart Snapshots</TabsTrigger>
  </TabsList>

  <TabsContent value="charts">
    <ChartSnapshotGallery />
  </TabsContent>
</Tabs>
```

---

## Styling & Responsiveness

### Mobile View
- Modal becomes full-screen on mobile
- Grid switches to single column
- Preview tab shows smaller image

### Dark Mode Support
- All components use shadcn/ui primitives
- Auto-adapts to user's theme preference
- Chart theme (dark/light) independent from app theme

---

## Error Handling

### Network Errors
```typescript
try {
  const { error } = await supabase.from("market_symbols").update(...);
  if (error) throw error;
} catch (error) {
  toast.error("Failed to save configuration. Please try again.");
  console.error(error);
}
```

### Image Loading Errors
```typescript
<img
  src={chartUrl}
  onError={(e) => {
    (e.target as HTMLImageElement).src = "https://via.placeholder.com/1200x800?text=Chart+Unavailable";
  }}
/>
```

---

## Performance Optimization

### Lazy Loading
```typescript
// Load ChartConfigModal only when needed
const ChartConfigModal = dynamic(() => import("./ChartConfigModal"), {
  loading: () => <Skeleton className="w-full h-[600px]" />,
});
```

### Debounced Preview
```typescript
// Debounce chart preview generation
useEffect(() => {
  const timer = setTimeout(() => {
    setChartUrl(buildChartUrl());
  }, 500);

  return () => clearTimeout(timer);
}, [config]);
```

---

## Testing

### Component Tests (Jest + React Testing Library)

```typescript
// __tests__/ChartConfigModal.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import ChartConfigModal from "../ChartConfigModal";

test("renders modal with symbol name", () => {
  const symbol = { id: "1", symbol: "^GDAXI", name: "DAX" };
  render(<ChartConfigModal symbol={symbol} isOpen={true} onClose={() => {}} onSave={() => {}} />);

  expect(screen.getByText(/Chart Configuration - DAX/)).toBeInTheDocument();
});

test("saves config on submit", async () => {
  const onSave = jest.fn();
  const symbol = { id: "1", symbol: "^GDAXI", name: "DAX" };

  render(<ChartConfigModal symbol={symbol} isOpen={true} onClose={() => {}} onSave={onSave} />);

  fireEvent.click(screen.getByText("Save Configuration"));

  await waitFor(() => {
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
      tv_symbol: "XETR:DAX",
    }));
  });
});
```

---

## Next Steps

1. Review [Agent Integration](./05_AGENT_INTEGRATION.md)
2. Check [Deployment Guide](./06_DEPLOYMENT.md)
3. Read [Testing Checklist](./07_TESTING.md)

---

**Last Updated**: 2025-11-02
**Component Library**: shadcn/ui
