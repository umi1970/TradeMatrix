# Architecture

## System Overview

Die chart-img.com Integration besteht aus 4 Hauptkomponenten:

1. **Configuration Layer** (Frontend): User konfiguriert Symbole & Chart-Settings
2. **Storage Layer** (Supabase): Speichert Konfiguration und Snapshots
3. **Generation Layer** (FastAPI): Generiert Chart-URLs via chart-img.com API
4. **Consumer Layer** (AI Agents): Nutzen Charts für Analysen

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            TRADEMATRIX SYSTEM                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ CONFIGURATION LAYER (Frontend)                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐      ┌──────────────────┐      ┌───────────────┐ │
│  │ Symbol Config    │      │ Timeframe        │      │ Indicator     │ │
│  │ Modal            │─────▶│ Selector         │─────▶│ Checkboxes    │ │
│  │                  │      │ (M5,M15,H1,...)  │      │ (RSI,MACD,...)│ │
│  └──────────────────┘      └──────────────────┘      └───────────────┘ │
│           │                                                             │
│           │ saves config via Supabase Client                           │
│           ▼                                                             │
└───────────┼─────────────────────────────────────────────────────────────┘
            │
            │
┌───────────▼─────────────────────────────────────────────────────────────┐
│ STORAGE LAYER (Supabase PostgreSQL)                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Table: market_symbols                                            │   │
│  │ ─────────────────────────────────────────────────────────────────│   │
│  │ id | symbol | name | chart_config (JSONB)                       │   │
│  │ ───────────────────────────────────────────────────────────────  │   │
│  │ 1  | ^GDAXI | DAX  | {"tv_symbol": "XETR:DAX",                 │   │
│  │    |        |      |  "timeframes": ["M15","H1","D1"],         │   │
│  │    |        |      |  "indicators": ["RSI","MACD"],            │   │
│  │    |        |      |  "chart_type": "candles",                 │   │
│  │    |        |      |  "theme": "dark"}                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Table: chart_snapshots                                           │   │
│  │ ─────────────────────────────────────────────────────────────────│   │
│  │ id | symbol_id | chart_url | timeframe | created_by_agent |     │   │
│  │    | metadata (JSONB) | created_at                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└───────────┬─────────────────────────────────────────────────────────────┘
            │
            │ reads config & writes snapshots
            ▼
┌───────────────────────────────────────────────────────────────────────┐
│ GENERATION LAYER (FastAPI + chart-img.com Client)                     │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ ChartService (Python Class)                                     │ │
│  │ ─────────────────────────────────────────────────────────────────│ │
│  │                                                                  │ │
│  │  def generate_chart_url(symbol, timeframe, indicators):        │ │
│  │      1. Fetch chart_config from DB                             │ │
│  │      2. Map Yahoo symbol → TradingView symbol                  │ │
│  │      3. Build API URL with parameters                          │ │
│  │      4. Add indicators to URL                                  │ │
│  │      5. Return chart-img.com URL                               │ │
│  │                                                                  │ │
│  │  def save_snapshot(symbol, url, metadata):                     │ │
│  │      1. Insert into chart_snapshots table                      │ │
│  │      2. Return snapshot_id                                     │ │
│  │                                                                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ RateLimiter (Middleware)                                        │ │
│  │ ─────────────────────────────────────────────────────────────────│ │
│  │  - Redis counter: "chart_api:requests:YYYY-MM-DD"              │ │
│  │  - Daily limit: 1,000                                          │ │
│  │  - Per-second limit: 15                                        │ │
│  │  - Returns 429 if exceeded                                     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                        │
└───────────┬────────────────────────────────────────────────────────────┘
            │
            │ calls API
            ▼
┌───────────────────────────────────────────────────────────────────────┐
│ EXTERNAL API (chart-img.com)                                          │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  GET https://api.chart-img.com/tradingview/advanced-chart?            │
│      symbol=XETR:DAX                                                  │
│      &interval=15                                                     │
│      &studies=RSI@tv-basicstudies,MACD@tv-basicstudies               │
│      &theme=dark                                                      │
│      &width=1200                                                      │
│      &height=800                                                      │
│                                                                        │
│  Returns: PNG image or public URL                                    │
│                                                                        │
└───────────┬────────────────────────────────────────────────────────────┘
            │
            │ returns chart URL
            ▼
┌───────────────────────────────────────────────────────────────────────┐
│ CONSUMER LAYER (AI Agents)                                            │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ ChartWatcher     │  │ MorningPlanner   │  │ JournalBot        │  │
│  │ ──────────────── │  │ ──────────────── │  │ ─────────────────  │  │
│  │ - Loads charts   │  │ - Setup charts   │  │ - Report charts   │  │
│  │ - OCR extraction │  │ - Daily preview  │  │ - Trade snapshots │  │
│  │ - Pattern detect │  │ - Multi-TF view  │  │ - P&L visual      │  │
│  └──────────────────┘  └──────────────────┘  └───────────────────┘  │
│                                                                        │
│  ┌──────────────────┐                                                 │
│  │ TradeMonitor     │ (Optional)                                     │
│  │ ──────────────── │                                                 │
│  │ - Live charts    │                                                 │
│  │ - Entry/Exit viz │                                                 │
│  └──────────────────┘                                                 │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Configuration Layer

**Technology**: Next.js 16 (React 19.2), TypeScript, shadcn/ui

**Components**:
- `ChartConfigModal.tsx`: Main configuration interface
- `TimeframeSelector.tsx`: Multi-select for timeframes
- `IndicatorSelector.tsx`: Checkboxes for indicators
- `ChartPreview.tsx`: Live preview of chart settings

**Responsibilities**:
- User inputs symbol chart settings
- Validates configuration
- Saves to Supabase via client SDK
- Shows preview before saving

**Data Flow**:
```
User Input → Validation → Supabase Client → market_symbols.chart_config
```

### 2. Storage Layer

**Technology**: Supabase PostgreSQL with JSONB

**Tables**:

#### `market_symbols` (Extended)
```sql
ALTER TABLE market_symbols ADD COLUMN chart_config JSONB;
```

**JSONB Structure**:
```json
{
  "tv_symbol": "XETR:DAX",         // TradingView symbol
  "timeframes": ["M15", "H1", "D1"], // User-selected timeframes
  "indicators": ["RSI", "MACD"],   // User-selected indicators
  "chart_type": "candles",         // candles | bars | line
  "theme": "dark",                 // dark | light
  "width": 1200,                   // pixels
  "height": 800                    // pixels
}
```

#### `chart_snapshots` (New)
```sql
CREATE TABLE chart_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol_id UUID REFERENCES market_symbols(id),
  chart_url TEXT NOT NULL,
  timeframe VARCHAR(10) NOT NULL,
  created_by_agent VARCHAR(50) NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Responsibilities**:
- Store user chart preferences per symbol
- Store generated chart snapshots with metadata
- RLS policies for user access control

### 3. Generation Layer

**Technology**: FastAPI, Python 3.11+, httpx

**Core Service**: `ChartService`

```python
class ChartService:
    def __init__(self, api_key: str, supabase_client):
        self.api_key = api_key
        self.base_url = "https://api.chart-img.com"
        self.supabase = supabase_client

    async def generate_chart_url(
        self,
        symbol: str,
        timeframe: str,
        custom_indicators: List[str] = None
    ) -> str:
        """
        1. Fetch chart_config from market_symbols
        2. Map Yahoo symbol to TradingView symbol
        3. Build API URL
        4. Check rate limits
        5. Return chart URL
        """
        pass

    async def save_snapshot(
        self,
        symbol_id: str,
        chart_url: str,
        timeframe: str,
        agent_name: str,
        metadata: dict
    ) -> str:
        """
        Save chart snapshot to database
        """
        pass
```

**Rate Limiting**:
```python
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_daily_limit(self) -> bool:
        """Check if < 1,000 requests today"""
        key = f"chart_api:daily:{date.today()}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 86400)  # 24h TTL
        return count <= 1000

    async def check_per_second_limit(self) -> bool:
        """Check if < 15 requests this second"""
        key = f"chart_api:second:{int(time.time())}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 1)  # 1s TTL
        return count <= 15
```

**Responsibilities**:
- Generate chart-img.com URLs
- Handle symbol mapping
- Enforce rate limits
- Save snapshots to database
- Error handling & retries

### 4. Consumer Layer

**Technology**: Python, Celery, LangChain

**Agents**:

#### ChartWatcher (Updated)
```python
# Before (lines 554-560 - broken)
chart_url = self.chart_service.generate_url(symbol)

# After (fixed)
from src.chart_service import ChartService

chart_service = ChartService(api_key=os.getenv("CHART_IMG_API_KEY"))
chart_url = await chart_service.generate_chart_url(
    symbol="^GDAXI",
    timeframe="M15"
)
```

#### MorningPlanner
```python
async def generate_daily_setup(symbols: List[str]):
    charts = []
    for symbol in symbols:
        # H1 chart for structure
        h1_url = await chart_service.generate_chart_url(symbol, "H1")
        charts.append({"symbol": symbol, "tf": "H1", "url": h1_url})

        # M15 chart for entry
        m15_url = await chart_service.generate_chart_url(symbol, "M15")
        charts.append({"symbol": symbol, "tf": "M15", "url": m15_url})

    return charts
```

#### JournalBot
```python
async def add_chart_to_entry(trade_id: str, symbol: str):
    # Get trade timestamp
    trade = await get_trade(trade_id)

    # Generate chart at trade time (if possible)
    chart_url = await chart_service.generate_chart_url(
        symbol=symbol,
        timeframe="M15"
    )

    # Save snapshot
    snapshot_id = await chart_service.save_snapshot(
        symbol_id=symbol.id,
        chart_url=chart_url,
        timeframe="M15",
        agent_name="JournalBot",
        metadata={"trade_id": trade_id, "timestamp": trade.timestamp}
    )

    return snapshot_id
```

**Responsibilities**:
- Request charts from ChartService
- Process chart images (OCR, pattern detection)
- Save snapshots for reports
- Handle errors gracefully

## Data Flow

### Scenario 1: User Configures Symbol

```
User → ChartConfigModal
    → Supabase Client (Insert)
        → market_symbols.chart_config (JSONB)
            → Success Toast
```

### Scenario 2: Agent Generates Chart

```
Agent Task Triggered (e.g., Morning Planner)
    → ChartService.generate_chart_url()
        → Fetch chart_config from Supabase
        → Check Rate Limits (Redis)
            → If OK:
                → Build API URL
                → Call chart-img.com
                → Return URL
                → Save snapshot to chart_snapshots
            → If Rate Limited:
                → Return cached URL (if available)
                → Or skip chart generation
```

### Scenario 3: Rate Limit Exceeded

```
ChartService.generate_chart_url()
    → RateLimiter.check_daily_limit()
        → Redis: GET chart_api:daily:2025-11-02 = 1001
        → Limit Exceeded
            → Log Warning
            → Return fallback (cached URL or placeholder)
            → Notify Admin (optional)
```

## Symbol Mapping

TradeMatrix uses Yahoo Finance symbols, but chart-img.com requires TradingView symbols.

**Mapping Table**:

| TradeMatrix Symbol | TradingView Symbol | Exchange |
|--------------------|-------------------|----------|
| ^GDAXI | XETR:DAX | Xetra |
| ^NDX | NASDAQ:NDX | NASDAQ |
| ^DJI | DJCFD:DJI | DJ CFD |
| EURUSD=X | OANDA:EURUSD | Oanda |
| EURGBP=X | OANDA:EURGBP | Oanda |
| GBPUSD=X | OANDA:GBPUSD | Oanda |
| BTC-USD | BINANCE:BTCUSDT | Binance |
| ETH-USD | BINANCE:ETHUSDT | Binance |

**Implementation**:
```python
SYMBOL_MAPPING = {
    "^GDAXI": "XETR:DAX",
    "^NDX": "NASDAQ:NDX",
    "^DJI": "DJCFD:DJI",
    "EURUSD=X": "OANDA:EURUSD",
    "EURGBP=X": "OANDA:EURGBP",
    "GBPUSD=X": "OANDA:GBPUSD",
    "BTC-USD": "BINANCE:BTCUSDT",
    "ETH-USD": "BINANCE:ETHUSDT",
}

def map_symbol(yahoo_symbol: str) -> str:
    return SYMBOL_MAPPING.get(yahoo_symbol, yahoo_symbol)
```

## API Key Handling

**Environment Variables**:
```bash
# Hetzner Server (.env)
CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l

# Local Development (.env.local)
CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l
```

**Security Best Practices**:
- Never commit API key to Git
- Use environment variables only
- Rotate key if exposed
- Monitor usage via chart-img.com dashboard

## Error Handling

### Rate Limit Exceeded
```python
if not await rate_limiter.check_daily_limit():
    logger.warning("Daily chart API limit exceeded")
    # Option 1: Return cached chart
    cached_url = await get_cached_chart(symbol, timeframe)
    if cached_url:
        return cached_url
    # Option 2: Return placeholder
    return "https://via.placeholder.com/1200x800?text=Chart+Unavailable"
```

### API Request Failed
```python
try:
    response = await httpx.get(chart_url, timeout=10.0)
    response.raise_for_status()
except httpx.TimeoutException:
    logger.error(f"Chart API timeout for {symbol}")
    return None
except httpx.HTTPStatusError as e:
    logger.error(f"Chart API error {e.response.status_code}: {e.response.text}")
    return None
```

### Invalid Symbol
```python
tv_symbol = SYMBOL_MAPPING.get(yahoo_symbol)
if not tv_symbol:
    logger.warning(f"No TradingView mapping for {yahoo_symbol}")
    return None
```

## Performance Considerations

### Caching Strategy
- Cache chart URLs in Redis for 1 hour
- Key: `chart:url:{symbol}:{timeframe}:{indicators_hash}`
- Reduces API calls by ~70%

### Async Operations
- Use `httpx` with async/await
- Non-blocking chart generation
- Parallel requests for multiple symbols

### Database Indexes
```sql
CREATE INDEX idx_chart_snapshots_symbol_created
ON chart_snapshots(symbol_id, created_at DESC);

CREATE INDEX idx_chart_snapshots_agent
ON chart_snapshots(created_by_agent, created_at DESC);
```

## Monitoring

### Metrics to Track
- Daily API request count
- Rate limit hits
- Chart generation latency
- Cache hit rate
- Failed requests (by error type)

### Logging
```python
logger.info(f"Chart generated: {symbol} {timeframe} in {elapsed}ms")
logger.warning(f"Rate limit: {daily_count}/1000")
logger.error(f"Chart API failed: {symbol} - {error}")
```

### Alerts
- Daily usage > 900 requests → Slack alert
- Rate limit exceeded → Email to admin
- API error rate > 5% → Pagerduty

## Security

### RLS Policies
```sql
-- Only authenticated users can read their own chart configs
CREATE POLICY "Users can read own chart configs"
ON market_symbols FOR SELECT
USING (auth.uid() = user_id);

-- Only authenticated users can update their own chart configs
CREATE POLICY "Users can update own chart configs"
ON market_symbols FOR UPDATE
USING (auth.uid() = user_id);

-- Only authenticated users can read their own chart snapshots
CREATE POLICY "Users can read own chart snapshots"
ON chart_snapshots FOR SELECT
USING (
  auth.uid() IN (
    SELECT user_id FROM market_symbols WHERE id = chart_snapshots.symbol_id
  )
);
```

### API Key Protection
- Store in environment variables only
- Use Supabase Vault for production
- Rotate key quarterly
- Monitor for unauthorized usage

## Scalability

### Current Limits
- 1,000 requests/day
- 15 requests/second
- Max 5 active symbols

### Future Scaling (if needed)
- Upgrade to MEGA+ plan (5,000/day)
- Implement request queuing
- Add chart snapshot CDN
- Self-hosted chart generation (TradingView library)

## Dependencies

- **chart-img.com API**: External service (required)
- **Supabase**: Database (required)
- **Redis**: Rate limiting & caching (required)
- **httpx**: HTTP client (required)
- **Celery**: Agent task execution (required)

## Next Steps

1. Read [Database Schema](./02_DATABASE_SCHEMA.md)
2. Review [API Endpoints](./03_API_ENDPOINTS.md)
3. Check [Agent Integration](./05_AGENT_INTEGRATION.md)

---

**Last Updated**: 2025-11-02
**Reviewed By**: Architecture Team
