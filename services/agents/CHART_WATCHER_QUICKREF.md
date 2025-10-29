# ChartWatcher - Quick Reference

## Overview
AI-powered chart pattern detection agent using OpenAI Vision API for TradeMatrix.ai

**File:** `/mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/agents/src/chart_watcher.py`

**Status:** ✅ FULLY IMPLEMENTED

---

## Pattern Types

| Pattern Category | Patterns | Type | Description |
|-----------------|----------|------|-------------|
| **Reversal** | Head & Shoulders | Bearish | Top formation signaling downtrend |
| | Inverse H&S | Bullish | Bottom formation signaling uptrend |
| | Double Top | Bearish | Two peaks at resistance |
| | Double Bottom | Bullish | Two troughs at support |
| **Continuation** | Ascending Triangle | Bullish | Higher lows, flat resistance |
| | Descending Triangle | Bearish | Lower highs, flat support |
| | Symmetrical Triangle | Neutral | Converging trendlines |
| | Bull Flag/Pennant | Bullish | Consolidation after rally |
| | Bear Flag/Pennant | Bearish | Consolidation after decline |
| **Wedge** | Rising Wedge | Bearish* | Upward slope, narrowing range |
| | Falling Wedge | Bullish* | Downward slope, narrowing range |
| **Channel** | Uptrend Channel | Bullish | Parallel upward lines |
| | Downtrend Channel | Bearish | Parallel downward lines |
| | Horizontal Channel | Sideways | Range-bound trading |

*Can vary depending on trend context

---

## Method Summary

### 1. `download_chart(chart_url)`
**Purpose:** Download chart image from URL

**Logic:**
```python
# 1. Use httpx to fetch image from URL
# 2. Handle HTTP errors gracefully
# 3. Return raw image bytes
```

**Returns:**
```python
bytes  # Raw image data
# or None on failure
```

---

### 2. `extract_price_values(image_bytes, symbol_name)`
**Purpose:** OCR-style price extraction using GPT-4 Vision

**Logic:**
```python
# 1. Convert image bytes to base64
# 2. Call OpenAI Vision API with price extraction prompt
# 3. Parse JSON response with price data
# 4. Return structured price information
```

**Returns:**
```json
{
  "current_price": 18500.50,
  "high_24h": 18650.00,
  "low_24h": 18420.00,
  "visible_levels": [18300.0, 18200.0, 18700.0],
  "confidence": 0.85
}
```

**OpenAI Model:** `gpt-4o` (GPT-4 Omni with vision)

**Temperature:** `0.1` (low for consistent extraction)

---

### 3. `detect_patterns(image_bytes, symbol_name, context)`
**Purpose:** AI-powered chart pattern recognition

**Logic:**
```python
# 1. Convert image to base64
# 2. Build prompt with pattern definitions
# 3. Include context (current price, timeframe)
# 4. Call OpenAI Vision API for pattern detection
# 5. Parse JSON response with detected patterns
# 6. Return structured pattern data with confidence scores
```

**Context Input:**
```python
{
  'current_price': 18500.0,
  'timeframe': '1h'
}
```

**Returns:**
```json
{
  "patterns": [
    {
      "name": "head_and_shoulders",
      "type": "bearish",
      "confidence": 0.82,
      "description": "Clear H&S formation with neckline at 18450",
      "key_levels": {
        "neckline": 18450.0,
        "target": 18200.0,
        "left_shoulder": 18480.0,
        "head": 18550.0,
        "right_shoulder": 18490.0
      }
    }
  ],
  "trend": "bearish",
  "support_levels": [18400.0, 18300.0, 18200.0],
  "resistance_levels": [18550.0, 18600.0],
  "analysis_summary": "Bearish H&S pattern suggests downside to 18200"
}
```

**OpenAI Model:** `gpt-4o`

**Temperature:** `0.2` (slightly higher for nuanced analysis)

---

### 4. `analyze_chart(symbol_id, symbol_name, chart_url, timeframe)`
**Purpose:** Complete chart analysis workflow

**Logic:**
```python
# 1. Download chart image from URL
# 2. Fetch recent price context from database
# 3. Extract price values (OCR)
# 4. Detect patterns (AI Vision)
# 5. Calculate overall confidence score
# 6. Store results in chart_analyses table
# 7. Return analysis UUID
```

**Database Record:**
```python
{
  'symbol_id': 'uuid',
  'timeframe': '1h',
  'chart_url': 'https://...',
  'patterns_detected': [...],  # JSONB array
  'trend': 'bearish',
  'support_levels': [18400.0, 18300.0],
  'resistance_levels': [18550.0, 18600.0],
  'analysis_summary': 'Bearish H&S pattern...',
  'confidence_score': 0.82,
  'payload': {...}  # Full analysis data
}
```

**Returns:**
```python
UUID  # Analysis record ID
# or None on failure
```

---

### 5. `_calculate_overall_confidence(pattern_data)`
**Purpose:** Calculate aggregate confidence score

**Logic:**
```python
# 1. Extract confidence scores from all detected patterns
# 2. Calculate average confidence
# 3. Round to 2 decimal places
# 4. Return 0.0 if no patterns detected
```

**Example:**
```python
# Input: patterns with confidences [0.85, 0.75, 0.90]
# Output: 0.83 (average)
```

---

### 6. `run(symbols=None, timeframe='1h')`
**Purpose:** Main execution method (called by Celery every 5 minutes)

**Logic:**
```python
# 1. Fetch active symbols from market_symbols
# 2. For each symbol:
#    - Check if chart URL exists (Storage/table)
#    - If found, run analyze_chart()
#    - Handle errors gracefully
# 3. Return execution summary
```

**Returns:**
```json
{
  "execution_time": "2025-10-29T08:00:00Z",
  "execution_duration_ms": 4250,
  "symbols_analyzed": 4,
  "analyses_created": 3,
  "analyses": [
    {
      "symbol": "DAX",
      "analysis_id": "uuid",
      "timeframe": "1h"
    }
  ]
}
```

---

## Usage

### Standalone Test
```bash
cd services/agents
python src/chart_watcher.py
```

### With Celery
```python
# tasks.py
from celery import Celery
from src.chart_watcher import ChartWatcher
from config.supabase import get_supabase_admin
from config import settings

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def run_chart_watcher(timeframe='1h'):
    watcher = ChartWatcher(
        get_supabase_admin(),
        settings.OPENAI_API_KEY
    )
    return watcher.run(timeframe=timeframe)

# Schedule every 5 minutes (300 seconds)
app.conf.beat_schedule = {
    'chart-watcher-every-5min': {
        'task': 'tasks.run_chart_watcher',
        'schedule': 300.0,
        'kwargs': {'timeframe': '1h'}
    },
}
```

### Run Celery
```bash
# Terminal 1: Start worker
celery -A tasks worker --loglevel=info

# Terminal 2: Start scheduler
celery -A tasks beat --loglevel=info
```

---

## Database Tables

### Input Tables
- `market_symbols` - Active symbols to analyze
- `ohlc` - OHLC data for price context
- (Future) `chart_snapshots` - Chart image URLs/metadata

### Output Table
- `chart_analyses` - AI-generated pattern analysis results

### Migration
```sql
-- Run migration 006_chart_analyses_table.sql
-- Location: services/api/supabase/migrations/006_chart_analyses_table.sql
```

**Table Schema:**
```sql
CREATE TABLE chart_analyses (
    id UUID PRIMARY KEY,
    symbol_id UUID REFERENCES market_symbols(id),
    timeframe TEXT,
    chart_url TEXT,
    patterns_detected JSONB,
    trend TEXT,
    support_levels DECIMAL[],
    resistance_levels DECIMAL[],
    confidence_score DECIMAL(5,2),
    analysis_summary TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

---

## Frontend Integration

### Fetch Latest Analysis
```typescript
const { data, error } = await supabase
  .from('chart_analyses')
  .select('*')
  .eq('symbol_id', symbolId)
  .eq('timeframe', '1h')
  .order('created_at', { ascending: false })
  .limit(1)
  .single();

if (data) {
  console.log('Detected patterns:', data.patterns_detected);
  console.log('Trend:', data.trend);
  console.log('Confidence:', data.confidence_score);
}
```

### Subscribe to New Analyses
```typescript
const subscription = supabase
  .channel('chart_analyses')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'chart_analyses',
    filter: `symbol_id=eq.${symbolId}`
  }, (payload) => {
    updateChartAnalysis(payload.new);
  })
  .subscribe();
```

### Display Patterns
```typescript
interface Pattern {
  name: string;
  type: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  description: string;
  key_levels: Record<string, number>;
}

function PatternCard({ pattern }: { pattern: Pattern }) {
  return (
    <div className="pattern-card">
      <h3>{pattern.name}</h3>
      <span className={pattern.type}>{pattern.type}</span>
      <p>Confidence: {(pattern.confidence * 100).toFixed(0)}%</p>
      <p>{pattern.description}</p>
    </div>
  );
}
```

---

## Error Handling

All methods include:
- Try/except blocks for API calls and database queries
- Graceful return of None on failures
- Comprehensive logging (error, warning, info, debug)
- HTTP timeout handling (30 seconds)
- OpenAI API error handling
- Image download retries (via httpx)
- Validation before database insert

---

## Performance

**Target:** < 10 seconds per chart analysis

**Considerations:**
- OpenAI Vision API calls: 2-5 seconds each
- Image download: 1-2 seconds
- Database queries: <500ms
- Total per symbol: ~5-8 seconds

**Optimizations:**
- Process symbols sequentially (parallel can hit API rate limits)
- Cache chart images when possible
- Use timeouts for all external calls
- Continue execution on single symbol failure

---

## Testing

### Unit Tests
```bash
cd services/agents
pytest tests/test_chart_watcher.py -v
```

**Tests:**
1. ChartWatcher initialization
2. Chart download (success/failure)
3. Price value extraction
4. Pattern detection (single pattern)
5. Pattern detection (multiple patterns)
6. Overall confidence calculation
7. Complete analysis workflow
8. Database integration

### Expected Output
```
✅ ChartWatcher initialized successfully
✅ Downloaded 1024 bytes from chart URL
✅ Correctly handled download failure
✅ Extracted price values (confidence: 0.85)
✅ Detected pattern: head_and_shoulders (bearish, 0.82)
✅ Detected 2 patterns: ascending_triangle, bull_flag
✅ Overall Confidence: 0.83
✅ Chart Analysis Complete
```

---

## Example Scenarios

### Scenario 1: Head & Shoulders Detection
```
Input:
- Chart: DAX 1h showing H&S formation
- Current price: 18500.00

Output:
{
  "patterns": [{
    "name": "head_and_shoulders",
    "type": "bearish",
    "confidence": 0.82,
    "key_levels": {
      "neckline": 18450.0,
      "target": 18200.0
    }
  }],
  "trend": "bearish",
  "support_levels": [18400.0, 18300.0],
  "resistance_levels": [18550.0]
}
```

### Scenario 2: Multiple Patterns (Bullish)
```
Input:
- Chart: EUR/USD 4h with triangle + flag
- Current price: 1.0850

Output:
{
  "patterns": [
    {
      "name": "ascending_triangle",
      "type": "bullish",
      "confidence": 0.78
    },
    {
      "name": "bull_flag",
      "type": "bullish",
      "confidence": 0.65
    }
  ],
  "trend": "bullish",
  "overall_confidence": 0.72
}
```

### Scenario 3: No Clear Patterns
```
Input:
- Chart: Dow Jones 1h, choppy/sideways

Output:
{
  "patterns": [],
  "trend": "sideways",
  "support_levels": [34200.0, 34100.0],
  "resistance_levels": [34400.0, 34500.0],
  "analysis_summary": "No clear patterns, range-bound trading"
}
```

---

## Configuration

### OpenAI Settings
```python
MODEL = "gpt-4o"  # GPT-4 Omni with vision
MAX_TOKENS_EXTRACTION = 500
MAX_TOKENS_PATTERNS = 1500
TEMPERATURE_EXTRACTION = 0.1  # Low for consistency
TEMPERATURE_PATTERNS = 0.2  # Slightly higher for nuance
```

### Execution Frequency
```python
SCHEDULE_INTERVAL = 300.0  # Every 5 minutes (300 seconds)
CELERY_EXPIRES = 290.0  # Expire after 290 seconds
```

### Timeframes
```python
SUPPORTED_TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
DEFAULT_TIMEFRAME = '1h'
```

### HTTP Settings
```python
DOWNLOAD_TIMEOUT = 30.0  # 30 seconds
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
```

---

## Requirements

### Python Packages
```
openai>=1.10.0
httpx>=0.24.0
supabase>=2.3.4
```

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
```

### OpenAI API Access
- GPT-4 Vision API access required
- Recommended: Tier 2+ for rate limits
- Cost: ~$0.01-0.03 per image analysis

---

## Chart Generation (Future Implementation)

Currently, ChartWatcher expects chart URLs to be provided. Future enhancements:

### Option 1: TradingView Integration
```python
# Generate chart snapshots using TradingView API
chart_url = tradingview.create_chart_snapshot(
    symbol="DAX",
    timeframe="1h",
    indicators=["EMA", "RSI", "MACD"]
)
```

### Option 2: Custom Chart Generation
```python
# Generate charts from OHLC data using matplotlib/plotly
from chart_generator import generate_chart

chart_url = generate_chart(
    symbol_id=symbol_id,
    timeframe="1h",
    candles=ohlc_data,
    upload_to_storage=True
)
```

### Option 3: Manual Upload
```python
# Upload charts to Supabase Storage
storage_path = f"charts/{symbol_name}_{timeframe}.png"
supabase.storage.from_('charts').upload(storage_path, image_bytes)
chart_url = supabase.storage.from_('charts').get_public_url(storage_path)
```

---

## Cost Estimation

### OpenAI Vision API Costs
- **Price:** $0.01 per image (1024x1024)
- **Usage:** 2 API calls per chart (extraction + patterns)
- **Cost per analysis:** ~$0.02

### Monthly Costs (4 symbols, 5-min frequency, 24/7)
```
4 symbols × 12 analyses/hour × 24 hours × 30 days = 34,560 analyses/month
34,560 × $0.02 = $691.20/month

Optimizations:
- Run only during market hours (8-5 MEZ) = ~$200/month
- Analyze only on significant price moves = ~$50/month
- Use lower frequency (15-min) = ~$150/month
```

---

## Limitations & Considerations

### Current Limitations
1. **No chart generation** - Requires external chart URLs
2. **Sequential processing** - One symbol at a time (API rate limits)
3. **Cost per analysis** - OpenAI Vision API usage fees
4. **Pattern accuracy** - Depends on chart image quality and AI interpretation

### Best Practices
1. Use high-quality chart images (1024x1024 minimum)
2. Include clear price axis and indicators
3. Run during market hours only to reduce costs
4. Monitor OpenAI API usage and rate limits
5. Cache analyses to avoid duplicate processing
6. Validate AI outputs before critical decisions

---

## Next Steps

1. ✅ Implementation complete
2. ✅ Database migration created
3. ✅ Celery task integration
4. ✅ Test suite created
5. ⏳ Chart generation implementation (TradingView/custom)
6. ⏳ Test with real chart images
7. ⏳ Frontend pattern visualization component
8. ⏳ Cost optimization (market hours only)
9. ⏳ Pattern accuracy validation
10. ⏳ Add more pattern types (channels, wedges)

---

## Status: ✅ READY FOR INTEGRATION

ChartWatcher agent fully implemented with OpenAI Vision API.
Awaiting chart URL source (manual upload, TradingView, or custom generation).

**Documentation:**
- Implementation: `chart_watcher.py`
- Test suite: `tests/test_chart_watcher.py`
- Migration: `006_chart_analyses_table.sql`
- Quick reference: `CHART_WATCHER_QUICKREF.md` (this file)
