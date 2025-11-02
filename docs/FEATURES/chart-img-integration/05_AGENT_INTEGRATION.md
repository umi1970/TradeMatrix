# Agent Integration

## Overview

Integration der chart-img.com API in die 4 AI Agents: ChartWatcher, MorningPlanner, JournalBot und TradeMonitor (optional).

## Shared Chart Service

Alle Agents nutzen die zentrale `ChartService` Klasse für Chart-Generierung.

### ChartService Implementation

**File**: `services/agents/src/chart_service.py`

```python
import os
import httpx
from typing import List, Optional, Dict
from supabase import create_client, Client
from datetime import datetime, timedelta
import redis
import hashlib

class ChartService:
    """
    Centralized service for chart-img.com API integration.
    Used by all AI agents (ChartWatcher, MorningPlanner, JournalBot, TradeMonitor).
    """

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

    def __init__(self):
        self.api_key = os.getenv("CHART_IMG_API_KEY")
        self.base_url = "https://api.chart-img.com"
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")  # Service key for admin access
        )
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )

    def map_symbol(self, yahoo_symbol: str) -> str:
        """Map Yahoo symbol to TradingView symbol."""
        return self.SYMBOL_MAPPING.get(yahoo_symbol, yahoo_symbol)

    async def get_chart_config(self, symbol: str) -> Optional[Dict]:
        """
        Fetch chart configuration from database.
        """
        try:
            response = self.supabase.table("market_symbols").select("chart_config").eq("symbol", symbol).single().execute()

            if response.data and response.data.get("chart_config"):
                return response.data["chart_config"]

            # Return default config if not found
            return {
                "tv_symbol": self.map_symbol(symbol),
                "timeframes": ["15", "60", "D"],
                "indicators": [],
                "chart_type": "candles",
                "theme": "dark",
                "width": 1200,
                "height": 800,
                "show_volume": True
            }
        except Exception as e:
            print(f"Error fetching chart config for {symbol}: {e}")
            return None

    def build_chart_url(
        self,
        tv_symbol: str,
        timeframe: str,
        indicators: List[str],
        chart_type: str = "candles",
        theme: str = "dark",
        width: int = 1200,
        height: int = 800,
        show_volume: bool = True
    ) -> str:
        """
        Build chart-img.com API URL with parameters.
        """
        params = {
            "symbol": tv_symbol,
            "interval": timeframe,
            "theme": theme,
            "width": str(width),
            "height": str(height),
            "hide_top_toolbar": "false",
            "hide_legend": "false",
            "hide_side_toolbar": "false",
        }

        if indicators:
            params["studies"] = ",".join(indicators)

        if not show_volume:
            params["hide_volume"] = "true"

        # Build URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/tradingview/advanced-chart?{query_string}"

    def get_cache_key(self, symbol: str, timeframe: str, indicators: List[str]) -> str:
        """Generate cache key for chart URL."""
        indicators_hash = hashlib.md5(",".join(sorted(indicators)).encode()).hexdigest()[:8]
        return f"chart:url:{symbol}:{timeframe}:{indicators_hash}"

    async def generate_chart_url(
        self,
        symbol: str,
        timeframe: str,
        custom_indicators: Optional[List[str]] = None,
        save_snapshot: bool = True,
        agent_name: str = "Unknown"
    ) -> Dict:
        """
        Generate chart URL from chart-img.com API.

        Args:
            symbol: Yahoo symbol (e.g., ^GDAXI)
            timeframe: Timeframe (e.g., M15, H1, D1)
            custom_indicators: Override config indicators
            save_snapshot: Save to chart_snapshots table
            agent_name: Name of agent requesting chart

        Returns:
            Dict with chart_url, snapshot_id, cached, remaining_requests
        """
        # Fetch chart config
        config = await self.get_chart_config(symbol)
        if not config:
            raise ValueError(f"Chart config not found for symbol {symbol}")

        # Use custom indicators or config indicators
        indicators = custom_indicators or config.get("indicators", [])

        # Check cache first
        cache_key = self.get_cache_key(symbol, timeframe, indicators)
        cached_url = self.redis_client.get(cache_key)

        if cached_url:
            return {
                "chart_url": cached_url,
                "snapshot_id": None,
                "cached": True,
                "remaining_requests": await self.get_remaining_requests()
            }

        # Check rate limits
        if not await self.check_rate_limits():
            raise Exception("Rate limit exceeded")

        # Build chart URL
        chart_url = self.build_chart_url(
            tv_symbol=config["tv_symbol"],
            timeframe=timeframe,
            indicators=indicators,
            chart_type=config.get("chart_type", "candles"),
            theme=config.get("theme", "dark"),
            width=config.get("width", 1200),
            height=config.get("height", 800),
            show_volume=config.get("show_volume", True)
        )

        # Cache URL for 1 hour
        self.redis_client.setex(cache_key, 3600, chart_url)

        # Increment daily counter
        await self.increment_request_count()

        # Save snapshot to database
        snapshot_id = None
        if save_snapshot:
            snapshot_id = await self.save_snapshot(
                symbol=symbol,
                chart_url=chart_url,
                timeframe=timeframe,
                agent_name=agent_name,
                metadata={
                    "indicators": indicators,
                    "chart_type": config.get("chart_type"),
                    "theme": config.get("theme"),
                    "width": config.get("width"),
                    "height": config.get("height")
                }
            )

        return {
            "chart_url": chart_url,
            "snapshot_id": snapshot_id,
            "cached": False,
            "remaining_requests": await self.get_remaining_requests()
        }

    async def save_snapshot(
        self,
        symbol: str,
        chart_url: str,
        timeframe: str,
        agent_name: str,
        metadata: Dict
    ) -> str:
        """
        Save chart snapshot to database.
        """
        try:
            # Get symbol_id
            symbol_response = self.supabase.table("market_symbols").select("id").eq("symbol", symbol).single().execute()
            if not symbol_response.data:
                raise ValueError(f"Symbol {symbol} not found in database")

            symbol_id = symbol_response.data["id"]

            # Insert snapshot
            snapshot = {
                "symbol_id": symbol_id,
                "chart_url": chart_url,
                "timeframe": timeframe,
                "created_by_agent": agent_name,
                "metadata": metadata,
                "request_timestamp": datetime.utcnow().isoformat()
            }

            response = self.supabase.table("chart_snapshots").insert(snapshot).execute()

            if response.data:
                return response.data[0]["id"]

            return None
        except Exception as e:
            print(f"Error saving chart snapshot: {e}")
            return None

    async def check_rate_limits(self) -> bool:
        """
        Check if we're within rate limits (1000/day, 15/sec).
        """
        # Check daily limit
        daily_count = await self.get_daily_request_count()
        if daily_count >= 1000:
            print("Daily rate limit exceeded (1000/1000)")
            return False

        # Check per-second limit
        current_second = int(datetime.now().timestamp())
        second_key = f"chart_api:second:{current_second}"
        second_count = self.redis_client.incr(second_key)
        self.redis_client.expire(second_key, 1)  # 1 second TTL

        if second_count > 15:
            print("Per-second rate limit exceeded (15/sec)")
            return False

        return True

    async def increment_request_count(self):
        """Increment daily request counter."""
        today = datetime.now().date().isoformat()
        daily_key = f"chart_api:daily:{today}"
        self.redis_client.incr(daily_key)
        self.redis_client.expire(daily_key, 86400)  # 24 hours TTL

    async def get_daily_request_count(self) -> int:
        """Get today's request count."""
        today = datetime.now().date().isoformat()
        daily_key = f"chart_api:daily:{today}"
        count = self.redis_client.get(daily_key)
        return int(count) if count else 0

    async def get_remaining_requests(self) -> int:
        """Get remaining requests for today."""
        used = await self.get_daily_request_count()
        return max(0, 1000 - used)
```

---

## 1. ChartWatcher Integration

### Problem (Lines 554-560)

**Current broken code**:
```python
# services/agents/src/chart_watcher.py (lines 554-560)
chart_url = self.chart_service.generate_url(symbol)  # ❌ Wrong method name
```

### Fix

**File**: `services/agents/src/chart_watcher.py`

```python
import asyncio
from src.chart_service import ChartService

class ChartWatcher:
    def __init__(self):
        self.chart_service = ChartService()

    async def analyze_symbol(self, symbol: str, timeframes: List[str] = ["M15", "H1", "D1"]):
        """
        Analyze symbol across multiple timeframes.

        Args:
            symbol: Yahoo symbol (e.g., ^GDAXI)
            timeframes: List of timeframes to analyze
        """
        results = []

        for timeframe in timeframes:
            try:
                # ✅ FIXED: Use correct method name
                chart_data = await self.chart_service.generate_chart_url(
                    symbol=symbol,
                    timeframe=timeframe,
                    save_snapshot=True,
                    agent_name="ChartWatcher"
                )

                chart_url = chart_data["chart_url"]

                # Perform OCR/pattern detection on chart
                analysis = await self.analyze_chart_image(chart_url, timeframe)

                results.append({
                    "timeframe": timeframe,
                    "chart_url": chart_url,
                    "snapshot_id": chart_data["snapshot_id"],
                    "analysis": analysis
                })

                print(f"ChartWatcher analyzed {symbol} {timeframe}: {analysis['summary']}")

            except Exception as e:
                print(f"Error analyzing {symbol} {timeframe}: {e}")
                results.append({
                    "timeframe": timeframe,
                    "error": str(e)
                })

        return results

    async def analyze_chart_image(self, chart_url: str, timeframe: str) -> Dict:
        """
        Perform OCR and pattern detection on chart image.
        (Placeholder for future LangChain/OpenAI Vision integration)
        """
        # TODO: Implement OCR with OpenAI Vision API
        # TODO: Detect patterns (double top/bottom, H&S, flags, etc.)

        return {
            "summary": "Chart analysis placeholder",
            "patterns": [],
            "support_levels": [],
            "resistance_levels": [],
            "trend": "neutral"
        }
```

### Celery Task

**File**: `services/agents/src/tasks.py`

```python
from celery import shared_task
from src.chart_watcher import ChartWatcher
import asyncio

@shared_task(name="chart_watcher.analyze_all_symbols")
def chart_watcher_analyze_all():
    """
    Celery task: Analyze all enabled symbols with ChartWatcher.
    Scheduled every hour.
    """
    chart_watcher = ChartWatcher()
    symbols = ["^GDAXI", "^NDX", "^DJI", "EURUSD=X", "EURGBP=X"]

    for symbol in symbols:
        asyncio.run(chart_watcher.analyze_symbol(symbol))

    return {"status": "success", "symbols_analyzed": len(symbols)}
```

---

## 2. MorningPlanner Integration

Generiert Setup-Charts für den täglichen Morning Report.

**File**: `hetzner-deploy/src/morning_planner.py`

```python
import asyncio
from src.chart_service import ChartService
from datetime import datetime

class MorningPlanner:
    def __init__(self):
        self.chart_service = ChartService()

    async def generate_morning_report(self, symbols: List[str]):
        """
        Generate morning report with setup charts for all symbols.

        Args:
            symbols: List of Yahoo symbols

        Returns:
            Dict with report data and chart URLs
        """
        report = {
            "date": datetime.now().date().isoformat(),
            "symbols": []
        }

        for symbol in symbols:
            symbol_report = await self.generate_symbol_setup(symbol)
            report["symbols"].append(symbol_report)

        return report

    async def generate_symbol_setup(self, symbol: str):
        """
        Generate multi-timeframe setup charts for a symbol.

        Args:
            symbol: Yahoo symbol (e.g., ^GDAXI)

        Returns:
            Dict with charts and setup analysis
        """
        # Generate H1 chart (structure)
        h1_chart = await self.chart_service.generate_chart_url(
            symbol=symbol,
            timeframe="60",  # H1
            custom_indicators=["RSI@tv-basicstudies"],
            save_snapshot=True,
            agent_name="MorningPlanner"
        )

        # Generate M15 chart (entry)
        m15_chart = await self.chart_service.generate_chart_url(
            symbol=symbol,
            timeframe="15",  # M15
            custom_indicators=["MACD@tv-basicstudies"],
            save_snapshot=True,
            agent_name="MorningPlanner"
        )

        # Generate D1 chart (context)
        d1_chart = await self.chart_service.generate_chart_url(
            symbol=symbol,
            timeframe="D",  # D1
            custom_indicators=["BB@tv-basicstudies"],
            save_snapshot=True,
            agent_name="MorningPlanner"
        )

        return {
            "symbol": symbol,
            "charts": {
                "H1": {
                    "url": h1_chart["chart_url"],
                    "snapshot_id": h1_chart["snapshot_id"],
                    "purpose": "Market structure & trend"
                },
                "M15": {
                    "url": m15_chart["chart_url"],
                    "snapshot_id": m15_chart["snapshot_id"],
                    "purpose": "Entry setup"
                },
                "D1": {
                    "url": d1_chart["chart_url"],
                    "snapshot_id": d1_chart["snapshot_id"],
                    "purpose": "Higher timeframe context"
                }
            },
            "setup_analysis": await self.analyze_setup(symbol, h1_chart["chart_url"], m15_chart["chart_url"])
        }

    async def analyze_setup(self, symbol: str, h1_url: str, m15_url: str) -> Dict:
        """
        Analyze multi-timeframe setup.
        (Placeholder for future AI integration)
        """
        # TODO: Use OpenAI Vision to analyze chart alignment
        # TODO: Check if H1 trend aligns with M15 entry setup
        # TODO: Generate setup summary and trade plan

        return {
            "summary": f"Setup analysis for {symbol} placeholder",
            "h1_trend": "bullish",
            "m15_setup": "pullback to support",
            "trade_plan": "Wait for M15 confirmation",
            "confidence": 0.75
        }
```

### Celery Task

**File**: `hetzner-deploy/src/tasks.py`

```python
@shared_task(name="morning_planner.generate_report")
def morning_planner_generate():
    """
    Celery task: Generate morning report with setup charts.
    Scheduled daily at 06:00 UTC.
    """
    planner = MorningPlanner()
    symbols = ["^GDAXI", "^NDX", "^DJI", "EURUSD=X", "EURGBP=X"]

    report = asyncio.run(planner.generate_morning_report(symbols))

    # Save report to database or send via email
    # TODO: Implement report storage/distribution

    return {"status": "success", "report_date": report["date"]}
```

### Beat Schedule

```python
# hetzner-deploy/src/tasks.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    "morning-planner-daily": {
        "task": "morning_planner.generate_report",
        "schedule": crontab(hour=6, minute=0),  # 06:00 UTC daily
    },
}
```

---

## 3. JournalBot Integration

Fügt Chart-Snapshots zu Trade-Journal-Entries hinzu.

**File**: `hetzner-deploy/src/journal_bot.py`

```python
import asyncio
from src.chart_service import ChartService
from datetime import datetime

class JournalBot:
    def __init__(self):
        self.chart_service = ChartService()
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )

    async def create_journal_entry(self, trade_data: Dict):
        """
        Create journal entry with chart snapshot.

        Args:
            trade_data: Dict with trade details (symbol, entry, exit, etc.)

        Returns:
            journal_entry_id
        """
        symbol = trade_data["symbol"]
        timeframe = trade_data.get("timeframe", "M15")

        # Generate chart snapshot at entry time
        chart_data = await self.chart_service.generate_chart_url(
            symbol=symbol,
            timeframe=timeframe,
            custom_indicators=[],  # Clean chart for journal
            save_snapshot=True,
            agent_name="JournalBot"
        )

        # Create journal entry
        journal_entry = {
            "trade_id": trade_data["trade_id"],
            "symbol": symbol,
            "entry_price": trade_data["entry_price"],
            "exit_price": trade_data.get("exit_price"),
            "pnl": trade_data.get("pnl"),
            "chart_snapshot_id": chart_data["snapshot_id"],
            "notes": await self.generate_trade_notes(trade_data, chart_data["chart_url"]),
            "created_at": datetime.utcnow().isoformat()
        }

        # Save to database
        response = self.supabase.table("journal_entries").insert(journal_entry).execute()

        return response.data[0]["id"] if response.data else None

    async def generate_trade_notes(self, trade_data: Dict, chart_url: str) -> str:
        """
        Generate AI-powered trade notes based on chart and trade data.
        (Placeholder for future LangChain integration)
        """
        # TODO: Use OpenAI to analyze chart and generate insights
        # TODO: Compare entry setup with exit conditions
        # TODO: Generate lessons learned

        return f"Trade on {trade_data['symbol']} - Manual notes placeholder"

    async def add_chart_to_existing_entry(self, entry_id: str, symbol: str, timeframe: str):
        """
        Add chart snapshot to existing journal entry.
        """
        chart_data = await self.chart_service.generate_chart_url(
            symbol=symbol,
            timeframe=timeframe,
            save_snapshot=True,
            agent_name="JournalBot"
        )

        # Update journal entry
        self.supabase.table("journal_entries").update({
            "chart_snapshot_id": chart_data["snapshot_id"]
        }).eq("id", entry_id).execute()

        return chart_data["snapshot_id"]
```

### Celery Task

```python
@shared_task(name="journal_bot.process_closed_trades")
def journal_bot_process_trades():
    """
    Celery task: Process closed trades and create journal entries.
    Scheduled every 4 hours.
    """
    journal_bot = JournalBot()

    # Fetch closed trades without journal entries
    # TODO: Query trades from database

    closed_trades = []  # Placeholder

    for trade in closed_trades:
        asyncio.run(journal_bot.create_journal_entry(trade))

    return {"status": "success", "entries_created": len(closed_trades)}
```

---

## 4. TradeMonitor Integration (Optional)

Live-Monitoring mit Chart-Updates.

**File**: `services/agents/src/trade_monitor.py`

```python
import asyncio
from src.chart_service import ChartService

class TradeMonitor:
    def __init__(self):
        self.chart_service = ChartService()

    async def monitor_active_trades(self, trades: List[Dict]):
        """
        Monitor active trades with live chart updates.

        Args:
            trades: List of active trades

        Returns:
            List of monitoring results
        """
        results = []

        for trade in trades:
            chart_data = await self.chart_service.generate_chart_url(
                symbol=trade["symbol"],
                timeframe=trade.get("timeframe", "M15"),
                save_snapshot=True,
                agent_name="TradeMonitor"
            )

            # Check if stop loss or take profit levels are near current price
            monitoring_status = await self.check_trade_levels(
                trade,
                chart_data["chart_url"]
            )

            results.append({
                "trade_id": trade["trade_id"],
                "chart_url": chart_data["chart_url"],
                "snapshot_id": chart_data["snapshot_id"],
                "status": monitoring_status
            })

        return results

    async def check_trade_levels(self, trade: Dict, chart_url: str) -> Dict:
        """
        Check if price is near SL/TP levels.
        (Placeholder for future implementation)
        """
        # TODO: Analyze chart to detect if SL/TP is close
        # TODO: Send alert if level is breached

        return {
            "near_sl": False,
            "near_tp": False,
            "current_pnl": 0.0
        }
```

---

## Rate Limit Management

### Aggressive Caching Strategy

```python
# Cache chart URLs for 1 hour
# Reduces API calls by ~70%

# Example: ChartWatcher runs every hour
# - Without cache: 5 symbols × 3 timeframes = 15 requests/hour = 360/day
# - With cache: First run = 15, subsequent runs = 0 (cached) = 15/day
# - Savings: 96% reduction
```

### Prioritization

```python
# Priority order (if approaching daily limit):
# 1. MorningPlanner (daily report - critical)
# 2. JournalBot (trade entries - important)
# 3. ChartWatcher (analysis - nice-to-have)
# 4. TradeMonitor (monitoring - optional)

async def generate_chart_with_priority(agent_name: str, ...):
    remaining = await chart_service.get_remaining_requests()

    if remaining < 100:  # Reserve last 100 for critical agents
        if agent_name not in ["MorningPlanner", "JournalBot"]:
            print(f"Skipping chart generation for {agent_name} (low rate limit)")
            return None

    return await chart_service.generate_chart_url(...)
```

---

## Error Handling

### Graceful Fallbacks

```python
async def analyze_with_fallback(symbol: str, timeframe: str):
    try:
        chart_data = await chart_service.generate_chart_url(symbol, timeframe)
        return chart_data["chart_url"]
    except Exception as e:
        if "rate limit" in str(e).lower():
            # Use cached chart if available
            cached = await get_cached_chart(symbol, timeframe)
            if cached:
                return cached

            # Or use placeholder
            return "https://via.placeholder.com/1200x800?text=Chart+Unavailable"
        else:
            raise e
```

---

## Testing

### Unit Tests

**File**: `services/agents/tests/test_chart_service.py`

```python
import pytest
from src.chart_service import ChartService

@pytest.mark.asyncio
async def test_generate_chart_url():
    service = ChartService()
    result = await service.generate_chart_url(
        symbol="^GDAXI",
        timeframe="M15",
        agent_name="TestAgent"
    )

    assert "chart_url" in result
    assert "snapshot_id" in result
    assert result["chart_url"].startswith("https://api.chart-img.com")

@pytest.mark.asyncio
async def test_rate_limit_check():
    service = ChartService()
    allowed = await service.check_rate_limits()
    assert isinstance(allowed, bool)
```

---

## Monitoring

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"ChartWatcher: Generated chart for {symbol} {timeframe}")
logger.warning(f"Rate limit: {daily_count}/1000 requests used")
logger.error(f"Chart generation failed for {symbol}: {error}")
```

### Metrics

Track in Redis or dedicated monitoring:
- Charts generated per agent
- Average response time
- Cache hit rate
- Rate limit warnings

---

## Next Steps

1. Review [Deployment Guide](./06_DEPLOYMENT.md)
2. Check [Testing Checklist](./07_TESTING.md)
3. Read [Troubleshooting](./08_TROUBLESHOOTING.md)

---

**Last Updated**: 2025-11-02
**Integration Status**: Ready for implementation
