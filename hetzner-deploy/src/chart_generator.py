#!/usr/bin/env python3
"""
ChartGenerator Service (Hetzner Deployment Version)
Generates dynamic trading charts via chart-img.com API integration

This is the Hetzner-optimized version with Docker Compose Redis integration.

Features:
- Rate-limited API calls (1000/day, 15/sec)
- Redis caching (5 min TTL) via Docker Compose
- Database persistence (chart_snapshots table)
- Error handling with custom exceptions
- Structured logging
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

import httpx
import redis
from supabase import create_client, Client
from dotenv import load_dotenv

from src.config.chart_img import ChartImgConfig
from src.exceptions.chart_errors import (
    RateLimitError,
    ChartGenerationError,
    SymbolNotFoundError,
    InvalidTimeframeError,
    ChartAPIError,
    ChartCacheError,
)

load_dotenv()

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Generate trading charts using chart-img.com API

    Usage:
        generator = ChartGenerator()
        chart_url = generator.generate_chart(
            symbol_id="uuid-here",
            timeframe="4h",
            trigger_type="manual",
            user_id="uuid-here"
        )
    """

    def __init__(self):
        """Initialize ChartGenerator with Supabase and Redis clients"""
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )

        # Initialize Redis client (Docker Compose service name: redis)
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connection successful")
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

        self.config = ChartImgConfig()
        logger.info("✅ ChartGenerator initialized")

    def _get_symbol_config(self, symbol_id: str) -> Optional[Dict]:
        """
        Get symbol configuration from database

        Args:
            symbol_id: UUID of the symbol

        Returns:
            Dict with symbol config or None if not found

        Raises:
            SymbolNotFoundError: If symbol doesn't exist or chart not enabled
        """
        try:
            response = self.supabase.table('symbols')\
                .select('id, symbol, chart_img_symbol, chart_enabled, chart_config')\
                .eq('id', symbol_id)\
                .eq('chart_enabled', True)\
                .limit(1)\
                .execute()

            if not response.data or len(response.data) == 0:
                raise SymbolNotFoundError(symbol_id=symbol_id)

            symbol_data = response.data[0]
            logger.info(f"📊 Found symbol: {symbol_data['symbol']} ({symbol_data['chart_img_symbol']})")
            return symbol_data

        except SymbolNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching symbol config: {e}")
            raise ChartGenerationError(
                f"Database error fetching symbol config",
                details={'symbol_id': symbol_id, 'error': str(e)}
            )

    def _check_rate_limit(self) -> int:
        """
        Check current rate limit status

        Returns:
            Current request count for today

        Raises:
            RateLimitError: If rate limit exceeded
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        key = self.config.REDIS_DAILY_COUNTER_KEY_FORMAT.format(
            prefix=self.config.REDIS_KEY_PREFIX,
            date=today
        )

        try:
            current_count = int(self.redis_client.get(key) or 0)

            # Check if we should block
            if self.config.should_block_rate_limit(current_count):
                reset_time = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                raise RateLimitError(
                    current_count=current_count,
                    limit=self.config.RATE_LIMIT_DAILY,
                    reset_time=reset_time.isoformat()
                )

            # Warn if approaching limit
            if self.config.should_warn_rate_limit(current_count):
                percentage = (current_count / self.config.RATE_LIMIT_DAILY) * 100
                logger.warning(
                    f"⚠️  Rate limit warning: {current_count}/{self.config.RATE_LIMIT_DAILY} "
                    f"({percentage:.1f}%) requests used today"
                )

            return current_count

        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"❌ Error checking rate limit: {e}")
            raise ChartCacheError(operation="get", cache_key=key, original_error=e)

    def _increment_request_counter(self) -> None:
        """Increment daily request counter in Redis"""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        key = self.config.REDIS_DAILY_COUNTER_KEY_FORMAT.format(
            prefix=self.config.REDIS_KEY_PREFIX,
            date=today
        )

        try:
            # Increment counter
            new_count = self.redis_client.incr(key)

            # Set expiry to end of day (if first request of the day)
            if new_count == 1:
                tomorrow = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                seconds_until_tomorrow = int((tomorrow - datetime.utcnow()).total_seconds())
                self.redis_client.expire(key, seconds_until_tomorrow)

            logger.debug(f"📊 Request counter: {new_count}/{self.config.RATE_LIMIT_DAILY}")

        except Exception as e:
            logger.error(f"❌ Error incrementing request counter: {e}")
            # Don't fail chart generation if counter fails
            pass

    def _get_cache_key(self, symbol_id: str, timeframe: str) -> str:
        """
        Generate Redis cache key for a chart

        Args:
            symbol_id: UUID of symbol
            timeframe: Chart timeframe

        Returns:
            Redis cache key
        """
        # Round to 5-minute intervals for cache
        now = datetime.utcnow()
        timestamp_5min = now.replace(
            minute=(now.minute // 5) * 5,
            second=0,
            microsecond=0
        ).isoformat()

        return self.config.REDIS_CACHE_KEY_FORMAT.format(
            symbol_id=symbol_id,
            timeframe=timeframe,
            timestamp_5min=timestamp_5min
        )

    def _get_cached_chart(self, symbol_id: str, timeframe: str) -> Optional[str]:
        """
        Get cached chart URL from Redis

        Args:
            symbol_id: UUID of symbol
            timeframe: Chart timeframe

        Returns:
            Chart URL from cache or None
        """
        cache_key = self._get_cache_key(symbol_id, timeframe)

        try:
            cached_url = self.redis_client.get(cache_key)
            if cached_url:
                logger.info(f"✅ Cache hit: {cache_key}")
                return cached_url
            return None

        except Exception as e:
            logger.error(f"❌ Error getting cache: {e}")
            # Don't fail if cache fails, just skip cache
            return None

    def _set_cached_chart(self, symbol_id: str, timeframe: str, chart_url: str) -> None:
        """
        Save chart URL to Redis cache

        Args:
            symbol_id: UUID of symbol
            timeframe: Chart timeframe
            chart_url: URL to cache
        """
        cache_key = self._get_cache_key(symbol_id, timeframe)

        try:
            self.redis_client.setex(
                cache_key,
                self.config.REDIS_CACHE_TTL,
                chart_url
            )
            logger.debug(f"💾 Cached chart: {cache_key} (TTL: {self.config.REDIS_CACHE_TTL}s)")

        except Exception as e:
            logger.error(f"❌ Error setting cache: {e}")
            # Don't fail if cache fails
            pass

    def _call_chart_img_api(
        self,
        symbol: str,
        timeframe: str,
        indicators: List[str]
    ) -> str:
        """
        Call chart-img.com API to generate chart

        Args:
            symbol: TradingView symbol (e.g., "XETR:DAX")
            timeframe: Chart timeframe (e.g., "4h")
            indicators: List of indicator names

        Returns:
            Chart image URL

        Raises:
            ChartAPIError: If API call fails
        """
        # Convert indicators to API format
        studies = self.config.get_indicators_for_api(indicators)

        # Build request payload
        payload = {
            "symbol": symbol,
            "interval": timeframe,
            "width": self.config.DEFAULT_WIDTH,
            "height": self.config.DEFAULT_HEIGHT,
            "studies": studies,
            "theme": self.config.DEFAULT_THEME,
        }

        headers = {
            "x-api-key": self.config.API_KEY,
            "Content-Type": "application/json",
        }

        logger.info(f"🌐 Calling chart-img.com API: {symbol} @ {timeframe}")
        logger.debug(f"   Payload: {json.dumps(payload, indent=2)}")

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.config.API_ENDPOINT,
                    json=payload,
                    headers=headers
                )

                # Check for errors
                if response.status_code != 200:
                    error_body = response.text
                    try:
                        error_json = response.json()
                        error_message = error_json.get('message', error_json.get('error', 'Unknown error'))
                    except:
                        error_message = error_body

                    raise ChartAPIError(
                        status_code=response.status_code,
                        response_body=error_body,
                        api_error_message=error_message
                    )

                # Parse response
                data = response.json()
                chart_url = data.get('url')

                if not chart_url:
                    raise ChartAPIError(
                        status_code=200,
                        response_body=response.text,
                        api_error_message="No 'url' field in API response"
                    )

                logger.info(f"✅ Chart generated: {chart_url}")
                return chart_url

        except ChartAPIError:
            raise
        except httpx.TimeoutException:
            raise ChartAPIError(
                status_code=408,
                api_error_message="Request timed out after 30 seconds"
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error calling chart-img.com API: {e}")
            raise ChartAPIError(
                status_code=500,
                api_error_message=f"Unexpected error: {str(e)}"
            )

    def _save_chart_snapshot(
        self,
        symbol_id: str,
        timeframe: str,
        chart_url: str,
        trigger_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Save chart snapshot to database

        Args:
            symbol_id: UUID of symbol
            timeframe: Chart timeframe
            chart_url: Generated chart URL
            trigger_type: What triggered chart generation
            user_id: User who triggered (optional)
            metadata: Additional metadata

        Returns:
            Inserted snapshot record
        """
        expires_at = datetime.utcnow() + timedelta(days=self.config.CHART_RETENTION_DAYS)

        snapshot_record = {
            'symbol_id': symbol_id,
            'timeframe': timeframe,
            'chart_url': chart_url,
            'trigger_type': trigger_type,
            'generated_by': user_id,
            'generated_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at.isoformat(),
            'metadata': metadata or {},
        }

        try:
            response = self.supabase.table('chart_snapshots')\
                .insert(snapshot_record)\
                .execute()

            if response.data and len(response.data) > 0:
                logger.info(f"💾 Saved chart snapshot: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise ChartGenerationError("Failed to save chart snapshot to database")

        except Exception as e:
            logger.error(f"❌ Error saving chart snapshot: {e}")
            raise ChartGenerationError(
                "Database error saving chart snapshot",
                details={'error': str(e)}
            )

    def generate_chart(
        self,
        symbol_id: str,
        timeframe: str,
        trigger_type: str = "manual",
        user_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict:
        """
        Generate chart for a symbol and timeframe

        Args:
            symbol_id: UUID of the symbol
            timeframe: Chart timeframe (1h, 4h, 1d, etc.)
            trigger_type: What triggered generation (manual, report, alert, etc.)
            user_id: User who triggered (optional)
            force_refresh: Skip cache and force new generation

        Returns:
            Dict with chart_url, snapshot_id, and metadata

        Raises:
            SymbolNotFoundError: Symbol not found or chart not enabled
            InvalidTimeframeError: Invalid timeframe provided
            RateLimitError: Rate limit exceeded
            ChartGenerationError: Other errors during generation
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🎨 CHART GENERATION REQUEST")
        logger.info(f"{'='*60}")
        logger.info(f"   Symbol ID: {symbol_id}")
        logger.info(f"   Timeframe: {timeframe}")
        logger.info(f"   Trigger:   {trigger_type}")
        logger.info(f"   User:      {user_id or 'System'}")
        logger.info(f"{'='*60}\n")

        # 1. Validate timeframe
        if not self.config.is_valid_timeframe(timeframe):
            raise InvalidTimeframeError(
                timeframe=timeframe,
                supported_timeframes=self.config.SUPPORTED_TIMEFRAMES
            )

        # 2. Get symbol config from database
        symbol_config = self._get_symbol_config(symbol_id)
        tradingview_symbol = symbol_config['chart_img_symbol']
        chart_config = symbol_config['chart_config']

        # 3. Check cache (unless force_refresh)
        if not force_refresh:
            cached_url = self._get_cached_chart(symbol_id, timeframe)
            if cached_url:
                logger.info("✅ Returning cached chart (no API call needed)")
                return {
                    'chart_url': cached_url,
                    'cached': True,
                    'generated_at': datetime.utcnow().isoformat(),
                }

        # 4. Check rate limit
        current_count = self._check_rate_limit()

        # 5. Call chart-img.com API
        indicators = chart_config.get('indicators', self.config.DEFAULT_INDICATORS_INDICES)
        chart_url = self._call_chart_img_api(
            symbol=tradingview_symbol,
            timeframe=timeframe,
            indicators=indicators
        )

        # 6. Increment request counter
        self._increment_request_counter()

        # 7. Save to database
        snapshot = self._save_chart_snapshot(
            symbol_id=symbol_id,
            timeframe=timeframe,
            chart_url=chart_url,
            trigger_type=trigger_type,
            user_id=user_id,
            metadata={
                'symbol': symbol_config['symbol'],
                'tradingview_symbol': tradingview_symbol,
                'indicators': indicators,
                'request_count': current_count + 1,
            }
        )

        # 8. Cache the result
        self._set_cached_chart(symbol_id, timeframe, chart_url)

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ CHART GENERATION SUCCESSFUL")
        logger.info(f"{'='*60}")
        logger.info(f"   Chart URL: {chart_url}")
        logger.info(f"   Snapshot:  {snapshot['id']}")
        logger.info(f"   Cached:    Yes (TTL: {self.config.REDIS_CACHE_TTL}s)")
        logger.info(f"{'='*60}\n")

        return {
            'chart_url': chart_url,
            'snapshot_id': snapshot['id'],
            'cached': False,
            'generated_at': snapshot['generated_at'],
            'expires_at': snapshot['expires_at'],
            'metadata': snapshot['metadata'],
        }

    def get_latest_chart_url(self, symbol_id: str, timeframe: str) -> Optional[str]:
        """
        Get latest chart URL from database (without generating new one)

        Args:
            symbol_id: UUID of symbol
            timeframe: Chart timeframe

        Returns:
            Chart URL or None if not found
        """
        try:
            response = self.supabase.table('chart_snapshots')\
                .select('chart_url, generated_at')\
                .eq('symbol_id', symbol_id)\
                .eq('timeframe', timeframe)\
                .order('generated_at', desc=True)\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                chart_url = response.data[0]['chart_url']
                logger.info(f"📊 Found latest chart: {chart_url}")
                return chart_url

            logger.info(f"ℹ️  No chart found for {symbol_id} @ {timeframe}")
            return None

        except Exception as e:
            logger.error(f"❌ Error fetching latest chart: {e}")
            return None

    def cleanup_expired_snapshots(self) -> int:
        """
        Delete expired chart snapshots from database

        Returns:
            Number of deleted snapshots
        """
        logger.info("🧹 Cleaning up expired chart snapshots...")

        try:
            # Use Supabase stored procedure
            response = self.supabase.rpc('cleanup_expired_chart_snapshots').execute()

            deleted_count = response.data if response.data else 0
            logger.info(f"✅ Deleted {deleted_count} expired snapshots")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error cleaning up snapshots: {e}")
            return 0

    def get_usage_stats(self) -> Dict:
        """
        Get API usage statistics

        Returns:
            Dict with usage stats (requests_today, limit, percentage_used, etc.)
        """
        today = datetime.utcnow().strftime('%Y-%m-%d')
        key = self.config.REDIS_DAILY_COUNTER_KEY_FORMAT.format(
            prefix=self.config.REDIS_KEY_PREFIX,
            date=today
        )

        try:
            current_count = int(self.redis_client.get(key) or 0)
            percentage_used = (current_count / self.config.RATE_LIMIT_DAILY) * 100
            remaining = self.config.RATE_LIMIT_DAILY - current_count

            return {
                'requests_today': current_count,
                'limit_daily': self.config.RATE_LIMIT_DAILY,
                'remaining': remaining,
                'percentage_used': round(percentage_used, 2),
                'warning_threshold': int(self.config.RATE_LIMIT_DAILY * self.config.RATE_LIMIT_WARNING_THRESHOLD),
                'hard_stop_threshold': int(self.config.RATE_LIMIT_DAILY * self.config.RATE_LIMIT_HARD_STOP_THRESHOLD),
                'date': today,
            }

        except Exception as e:
            logger.error(f"❌ Error getting usage stats: {e}")
            return {
                'error': str(e),
                'requests_today': 0,
                'limit_daily': self.config.RATE_LIMIT_DAILY,
            }


# Usage Example
if __name__ == "__main__":
    generator = ChartGenerator()

    # Example: Generate chart for DAX, 4h timeframe
    try:
        result = generator.generate_chart(
            symbol_id="<UUID-from-database>",
            timeframe="4h",
            trigger_type="manual"
        )
        print(f"\n✅ Chart URL: {result['chart_url']}")

    except RateLimitError as e:
        print(f"\n❌ Rate limit exceeded: {e}")
    except SymbolNotFoundError as e:
        print(f"\n❌ Symbol not found: {e}")
    except ChartGenerationError as e:
        print(f"\n❌ Chart generation failed: {e}")
