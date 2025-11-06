#!/usr/bin/env python3
"""
ChartService - Chart-img.com Integration Service
Generates TradingView chart URLs with timeframe-optimized indicator profiles

Features:
- Symbol mapping (Yahoo Finance → TradingView)
- Profile selection based on timeframe (scalping/intraday/swing)
- Rate limiting (1000/day, 15/second)
- Redis caching (1 hour TTL)
- Supabase Storage upload (persistent chart images)
- Database persistence (chart_snapshots table)
- Dynamic drawing integration (prev_high/prev_low from eod_levels)

Workflow:
1. Generate chart via chart-img.com API
2. Download PNG image bytes
3. Upload to Supabase Storage (bucket: charts)
4. Return public Storage URL (no expiration, no 403 errors)

Usage:
    service = ChartService()
    chart_url = await service.generate_chart_url(
        symbol="^GDAXI",
        timeframe="1h",
        agent_name="ChartWatcher"
    )
    # Returns: https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/charts/agents/...
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID

import httpx
import redis
from supabase import Client
from dotenv import load_dotenv

from src.config.supabase import get_supabase_admin

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChartService:
    """
    Service for generating TradingView charts via chart-img.com API

    Responsibilities:
    - Map Yahoo Finance symbols to TradingView symbols
    - Select appropriate indicator profile based on timeframe
    - Generate chart images via chart-img.com API
    - Upload chart images to Supabase Storage
    - Enforce rate limits (daily & per-second)
    - Cache chart URLs in Redis
    - Save snapshots to database

    Storage Structure:
    - Bucket: charts
    - Path: agents/{agent_name}/{YYYY}/{MM}/{DD}/{symbol}_{timeframe}_{timestamp}.png
    - URL: https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/charts/agents/...
    """

    # Symbol mapping: market_symbols.symbol → TradingView
    # Supports BOTH market_symbols (DAX, EUR/USD) AND symbols table (^GDAXI, EURUSD=X)
    SYMBOL_MAPPING = {
        # market_symbols format (PRIMARY - used by all AI Agents)
        "DAX": "TVC:DAX",           # DAX 40 Index (Real-time composite)
        "NDX": "NASDAQ:NDX",        # NASDAQ 100 Index
        "DJI": "TVC:DJI",           # Dow Jones Industrial Average
        "EUR/USD": "FX:EURUSD",     # Euro / US Dollar
        "XAG/USD": "FX:XAGUSD",     # Silver Spot

        # symbols table format (for EOD Data Layer compatibility)
        "^GDAXI": "TVC:DAX",        # DAX (Yahoo Finance format)
        "^DJI": "TVC:DJI",          # Dow Jones (Yahoo Finance format)
        "^NDX": "NASDAQ:NDX",       # NASDAQ 100 (Yahoo Finance format)
        "^IXIC": "NASDAQ:IXIC",     # NASDAQ Composite
        "EURUSD": "FX:EURUSD",      # EUR/USD (EOD format)
        "EURUSD=X": "FX:EURUSD",    # EUR/USD (Yahoo Finance format)
        "EURGBP": "FX:EURGBP",      # EUR/GBP (EOD format)
        "EURGBP=X": "FX:EURGBP",    # EUR/GBP (Yahoo Finance format)
        "GBPUSD": "FX:GBPUSD",      # GBP/USD (EOD format)
        "GBPUSD=X": "FX:GBPUSD",    # GBP/USD (Yahoo Finance format)
        "BTC-USD": "BINANCE:BTCUSDT",  # Bitcoin
        "ETH-USD": "BINANCE:ETHUSDT",  # Ethereum
    }

    # Timeframe mapping: Internal → TradingView API v2
    # API v2 accepts: 1m, 3m, 5m, 15m, 30m, 45m, 1h, 2h, 3h, 4h, 1D, 1W, 1M
    TIMEFRAME_MAPPING = {
        "1m": "1m",
        "5m": "5m",     # v2 API needs "5m" not "5"
        "15m": "15m",   # v2 API needs "15m" not "15"
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1D": "1D",
        "1W": "1W",
    }

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize ChartService

        Args:
            supabase_client: Optional Supabase client (defaults to admin client)
        """
        self.supabase = supabase_client or get_supabase_admin()

        # Initialize Redis
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connection successful")
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

        # API Configuration
        self.api_key = os.getenv('CHART_IMG_API_KEY')
        self.base_url = os.getenv('CHART_IMG_BASE_URL', 'https://api.chart-img.com')
        self.daily_limit = int(os.getenv('CHART_API_DAILY_LIMIT', '1000'))
        self.cache_ttl = int(os.getenv('CHART_CACHE_TTL', '3600'))  # 1 hour

        if not self.api_key:
            raise ValueError("CHART_IMG_API_KEY environment variable is required")

        logger.info("✅ ChartService initialized")

    def map_symbol(self, yahoo_symbol: str) -> Optional[str]:
        """
        Map Yahoo Finance symbol to TradingView symbol

        Args:
            yahoo_symbol: Yahoo Finance symbol (e.g., "^GDAXI")

        Returns:
            TradingView symbol (e.g., "TVC:DAX") or None if not found
        """
        tv_symbol = self.SYMBOL_MAPPING.get(yahoo_symbol)
        if not tv_symbol:
            logger.warning(f"No TradingView mapping for symbol: {yahoo_symbol}")
        return tv_symbol

    def get_chart_profile(self, timeframe: str) -> Dict[str, Any]:
        """
        Get timeframe-optimized indicator profile

        Profiles:
        - scalping (1m, 5m): 9 studies - All EMAs, Volume, Pivots
        - intraday (15m, 1h): 9 studies - All EMAs, Ichimoku, no Volume
        - swing (4h, 1D): 8 studies + 2 drawings - EMA50/200, Smart-Money levels

        Args:
            timeframe: Timeframe string (e.g., "5m", "1h", "1D")

        Returns:
            Dict with "studies" and "drawings" keys
        """
        # Scalping profile: 1m, 5m
        if timeframe in ["1m", "5m"]:
            return {
                "studies": [
                    {"name": "Moving Average Exponential", "input": {"length": 20}, "forceOverlay": True},
                    {"name": "Moving Average Exponential", "input": {"length": 50}, "forceOverlay": True},
                    {"name": "Moving Average Exponential", "input": {"length": 200}, "forceOverlay": True},
                    {"name": "Relative Strength Index", "input": {"length": 14}},
                    {"name": "MACD", "input": {"fastLength": 12, "slowLength": 26, "signalLength": 9}},
                    {"name": "Bollinger Bands", "input": {"length": 20, "stdDev": 2}},
                    {"name": "Average True Range", "input": {"length": 14}},
                    {"name": "Pivot Points Standard"},
                    {"name": "Volume"}
                ],
                "drawings": []
            }

        # Intraday profile: 15m, 1h
        elif timeframe in ["15m", "1h"]:
            return {
                "studies": [
                    {"name": "Moving Average Exponential", "input": {"length": 20}, "forceOverlay": True},
                    {"name": "Moving Average Exponential", "input": {"length": 50}, "forceOverlay": True},
                    {"name": "Moving Average Exponential", "input": {"length": 200}, "forceOverlay": True},
                    {"name": "Relative Strength Index", "input": {"length": 14}},
                    {"name": "MACD", "input": {"fastLength": 12, "slowLength": 26, "signalLength": 9}},
                    {"name": "Ichimoku Cloud"},
                    {"name": "Bollinger Bands", "input": {"length": 20, "stdDev": 2}},
                    {"name": "Average True Range", "input": {"length": 14}},
                    {"name": "Pivot Points Standard"}
                ],
                "drawings": []
            }

        # Swing profile: 4h, 1D
        elif timeframe in ["4h", "1D"]:
            return {
                "studies": [
                    {"name": "Moving Average Exponential", "input": {"length": 50}, "forceOverlay": True},
                    {"name": "Moving Average Exponential", "input": {"length": 200}, "forceOverlay": True},
                    {"name": "Ichimoku Cloud"},
                    {"name": "Relative Strength Index", "input": {"length": 14}},
                    {"name": "MACD", "input": {"fastLength": 12, "slowLength": 26, "signalLength": 9}},
                    {"name": "Bollinger Bands", "input": {"length": 20, "stdDev": 2}},
                    {"name": "Average True Range", "input": {"length": 14}},
                    {"name": "Volume"}
                ],
                "drawings": []  # Will be populated dynamically from eod_levels
            }

        # Default: intraday profile
        else:
            logger.warning(f"Unknown timeframe {timeframe}, using intraday profile")
            return self.get_chart_profile("1h")

    def get_eod_levels(self, symbol_id: str) -> Optional[Dict[str, float]]:
        """
        Fetch EOD levels (yesterday_high, yesterday_low) from database

        Args:
            symbol_id: UUID of the symbol

        Returns:
            Dict with "yesterday_high" and "yesterday_low" or None
        """
        try:
            response = self.supabase.table('eod_levels')\
                .select('yesterday_high, yesterday_low')\
                .eq('symbol_id', symbol_id)\
                .eq('date', date.today().isoformat())\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                levels = response.data[0]
                return {
                    "yesterday_high": float(levels['yesterday_high']),
                    "yesterday_low": float(levels['yesterday_low'])
                }
            return None

        except Exception as e:
            logger.error(f"Error fetching EOD levels: {e}")
            return None

    def build_chart_payload(
        self,
        tv_symbol: str,
        timeframe: str,
        symbol_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build complete chart API payload

        Args:
            tv_symbol: TradingView symbol (e.g., "TVC:DAX")
            timeframe: Timeframe string (e.g., "1h")
            symbol_id: Optional symbol ID for EOD levels (swing profile only)

        Returns:
            Dict ready for JSON serialization
        """
        # Get base profile
        profile = self.get_chart_profile(timeframe)

        # Add dynamic drawings for swing profile
        if timeframe in ["4h", "1D"] and symbol_id:
            eod_levels = self.get_eod_levels(symbol_id)
            if eod_levels:
                profile["drawings"] = [
                    {
                        "name": "Horizontal Line",
                        "input": {"price": eod_levels["yesterday_high"]},
                        "override": {"lineWidth": 2, "lineColor": "rgb(255,255,0)"}  # Yellow
                    },
                    {
                        "name": "Horizontal Line",
                        "input": {"price": eod_levels["yesterday_low"]},
                        "override": {"lineWidth": 2, "lineColor": "rgb(0,255,255)"}  # Cyan
                    }
                ]
                logger.info(f"Added EOD levels: High={eod_levels['yesterday_high']}, Low={eod_levels['yesterday_low']}")

        # Map timeframe to API format
        api_timeframe = self.TIMEFRAME_MAPPING.get(timeframe, timeframe)

        # Build payload
        payload = {
            "theme": "dark",
            "interval": api_timeframe,
            "symbol": tv_symbol,
            "width": 1200,
            "height": 800,
            "studies": profile["studies"]
        }

        # Add drawings if present
        if profile["drawings"]:
            payload["drawings"] = profile["drawings"]

        return payload

    def get_cache_key(self, symbol: str, timeframe: str) -> str:
        """
        Generate Redis cache key

        Args:
            symbol: Yahoo Finance symbol
            timeframe: Timeframe string

        Returns:
            Cache key string
        """
        return f"chart:url:{symbol}:{timeframe}"

    def check_rate_limits(self) -> bool:
        """
        Check if rate limits allow new request

        Limits:
        - Daily: 1000 requests
        - Per-second: 15 requests

        Returns:
            True if request allowed, False otherwise
        """
        # Check daily limit
        daily_key = f"chart_api:daily:{date.today().isoformat()}"
        daily_count = self.redis_client.get(daily_key)

        if daily_count and int(daily_count) >= self.daily_limit:
            logger.warning(f"Daily rate limit exceeded: {daily_count}/{self.daily_limit}")
            return False

        # Check per-second limit
        second_key = f"chart_api:second:{int(datetime.now().timestamp())}"
        second_count = self.redis_client.get(second_key)

        if second_count and int(second_count) >= 15:
            logger.warning(f"Per-second rate limit exceeded: {second_count}/15")
            return False

        return True

    def increment_request_count(self):
        """Increment rate limit counters in Redis"""
        # Daily counter
        daily_key = f"chart_api:daily:{date.today().isoformat()}"
        pipe = self.redis_client.pipeline()
        pipe.incr(daily_key)
        pipe.expire(daily_key, 86400)  # 24 hours

        # Per-second counter
        second_key = f"chart_api:second:{int(datetime.now().timestamp())}"
        pipe.incr(second_key)
        pipe.expire(second_key, 1)  # 1 second

        pipe.execute()

    def get_daily_request_count(self) -> int:
        """Get current daily request count"""
        daily_key = f"chart_api:daily:{date.today().isoformat()}"
        count = self.redis_client.get(daily_key)
        return int(count) if count else 0

    def get_remaining_requests(self) -> int:
        """Get remaining daily requests"""
        return self.daily_limit - self.get_daily_request_count()

    async def generate_chart_url(
        self,
        symbol: str,
        timeframe: str,
        agent_name: str,
        symbol_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> Optional[str]:
        """
        Generate chart URL (with caching and rate limiting)

        Process:
        1. Check Redis cache
        2. Generate chart via chart-img.com API
        3. Download image bytes
        4. Upload to Supabase Storage (bucket: charts)
        5. Return Supabase Storage public URL

        Args:
            symbol: Yahoo Finance symbol (e.g., "^GDAXI")
            timeframe: Timeframe string (e.g., "1h")
            agent_name: Name of calling agent (for logging)
            symbol_id: Optional symbol ID (required for swing profile drawings)
            force_refresh: Skip cache and generate new chart

        Returns:
            Supabase Storage URL string or None if failed
        """
        logger.info(f"Generating chart: {symbol} {timeframe} (agent={agent_name})")

        # Check cache first
        cache_key = self.get_cache_key(symbol, timeframe)
        if not force_refresh:
            cached_url = self.redis_client.get(cache_key)
            if cached_url:
                logger.info(f"✅ Cache hit: {cache_key}")
                return cached_url

        # Map symbol
        tv_symbol = self.map_symbol(symbol)
        if not tv_symbol:
            logger.error(f"❌ Symbol mapping failed: {symbol}")
            return None

        # Check rate limits
        if not self.check_rate_limits():
            logger.error("❌ Rate limit exceeded, returning cached URL if available")
            cached_url = self.redis_client.get(cache_key)
            return cached_url

        # Build payload
        payload = self.build_chart_payload(tv_symbol, timeframe, symbol_id)

        # Call API and upload to Supabase Storage
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Generate chart via chart-img.com API
                response = await client.post(
                    f"{self.base_url}/v2/tradingview/advanced-chart",
                    headers={
                        "x-api-key": self.api_key,
                        "content-type": "application/json"
                    },
                    json=payload
                )

                response.raise_for_status()

                # Step 2: Download image bytes (chart-img.com returns PNG directly)
                image_bytes = response.content
                logger.info(f"Downloaded chart image: {len(image_bytes)} bytes")

                # Step 3: Upload to Supabase Storage
                storage_url = self._upload_to_storage(
                    image_bytes=image_bytes,
                    symbol=symbol,
                    timeframe=timeframe,
                    agent_name=agent_name
                )

                if not storage_url:
                    logger.error(f"❌ Failed to upload chart to Supabase Storage")
                    return None

                # Increment counters
                self.increment_request_count()

                # Cache Supabase Storage URL
                self.redis_client.setex(cache_key, self.cache_ttl, storage_url)

                logger.info(f"✅ Chart generated and uploaded: {symbol} {timeframe}")
                logger.info(f"📊 Storage URL: {storage_url}")
                logger.info(f"📊 API Usage: {self.get_daily_request_count()}/{self.daily_limit}")

                return storage_url

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Chart API error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error(f"❌ Chart API timeout for {symbol}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error generating chart: {e}")
            return None

    def _upload_to_storage(
        self,
        image_bytes: bytes,
        symbol: str,
        timeframe: str,
        agent_name: str
    ) -> Optional[str]:
        """
        Upload chart image to Supabase Storage

        Args:
            image_bytes: PNG image bytes
            symbol: Symbol name (e.g., "DAX")
            timeframe: Timeframe (e.g., "1h")
            agent_name: Agent name for path organization

        Returns:
            Public URL of uploaded image or None if failed
        """
        try:
            bucket = "charts"

            # Generate storage path: agents/agent_name/YYYY/MM/DD/symbol_timeframe_timestamp.png
            now = datetime.utcnow()
            date_path = now.strftime('%Y/%m/%d')
            timestamp = now.strftime('%Y%m%d_%H%M%S')
            filename = f"{symbol}_{timeframe}_{timestamp}.png"
            storage_path = f"agents/{agent_name}/{date_path}/{filename}"

            # Upload to Supabase Storage
            result = self.supabase.storage.from_(bucket).upload(
                storage_path,
                image_bytes,
                file_options={"content-type": "image/png"}
            )

            # Get public URL
            public_url = self.supabase.storage.from_(bucket).get_public_url(storage_path)

            # Remove trailing '?' if present (Supabase SDK bug)
            public_url = public_url.rstrip('?')

            logger.info(f"✅ Chart uploaded to storage: {storage_path}")
            return public_url

        except Exception as e:
            logger.error(f"❌ Error uploading chart to storage: {e}")
            return None

    async def save_snapshot(
        self,
        symbol_id: str,
        chart_url: str,
        timeframe: str,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Save chart snapshot to database

        Args:
            symbol_id: UUID of the symbol
            chart_url: Generated chart URL
            timeframe: Timeframe string
            agent_name: Name of calling agent
            metadata: Optional metadata dict

        Returns:
            Snapshot ID (UUID) or None if failed
        """
        try:
            # Map agent_name to trigger_type (existing table schema from migration 013)
            trigger_type_map = {
                "ChartWatcher": "analysis",
                "SignalBot": "setup",
                "MorningPlanner": "report",
                "JournalBot": "report",
                "USOpenPlanner": "setup"
            }
            trigger_type = trigger_type_map.get(agent_name, "analysis")

            snapshot_data = {
                "symbol_id": symbol_id,
                "chart_url": chart_url,
                "timeframe": timeframe,
                "trigger_type": trigger_type,  # Uses existing column from migration 013
                "metadata": {
                    **(metadata or {}),
                    "agent_name": agent_name  # Store agent name in metadata
                },
                "expires_at": (datetime.utcnow() + timedelta(days=60)).isoformat()
                # generated_at is set automatically by database DEFAULT NOW()
            }

            response = self.supabase.table('chart_snapshots')\
                .insert(snapshot_data)\
                .execute()

            if response.data and len(response.data) > 0:
                snapshot_id = response.data[0]['id']
                logger.info(f"✅ Snapshot saved: {snapshot_id}")
                return snapshot_id

            return None

        except Exception as e:
            logger.error(f"❌ Error saving snapshot: {e}")
            return None


# Standalone test function
async def test_chart_service():
    """Test ChartService functionality"""
    service = ChartService()

    # Test symbol mapping
    assert service.map_symbol("^GDAXI") == "TVC:DAX"
    assert service.map_symbol("^DJI") == "TVC:DJI"

    # Test profile selection
    scalping_profile = service.get_chart_profile("5m")
    assert len(scalping_profile["studies"]) == 9

    intraday_profile = service.get_chart_profile("1h")
    assert len(intraday_profile["studies"]) == 9

    swing_profile = service.get_chart_profile("1D")
    assert len(swing_profile["studies"]) == 8

    # Test rate limits
    assert service.check_rate_limits() == True

    logger.info("✅ All tests passed!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chart_service())
