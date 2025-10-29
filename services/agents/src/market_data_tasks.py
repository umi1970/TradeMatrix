"""
Market Data Celery Tasks
========================

Background tasks for fetching and storing market data from Twelve Data API.

Tasks:
- fetch_realtime_prices: Fetch current prices every 1 minute
- fetch_historical_data: Fetch historical OHLCV data (on-demand or daily)
- update_symbol_data: Update data for a single symbol

Author: TradeMatrix.ai Development Team
Date: 2025-10-29
"""

import os
import sys
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from celery import Celery, Task
from celery.schedules import crontab

# Add parent directory to path to import from services/api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../api/src'))

from core.market_data_fetcher import MarketDataFetcher
from config.supabase import get_supabase_admin_client, get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    'market_data_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Symbols to track
TRACKED_SYMBOLS = [
    {'symbol': 'DAX', 'name': 'DAX 40', 'priority': 'high'},
    {'symbol': 'NDX', 'name': 'NASDAQ 100', 'priority': 'high'},
    {'symbol': 'DJI', 'name': 'Dow Jones 30', 'priority': 'high'},
    {'symbol': 'EUR/USD', 'name': 'EUR/USD', 'priority': 'medium'},
    {'symbol': 'GBP/USD', 'name': 'GBP/USD', 'priority': 'medium'},
]

# Extract symbol names
SYMBOL_NAMES = [s['symbol'] for s in TRACKED_SYMBOLS]


class MarketDataTask(Task):
    """Base task class with shared functionality"""

    _fetcher = None

    @property
    def fetcher(self) -> MarketDataFetcher:
        """Lazy-load fetcher instance"""
        if self._fetcher is None:
            self._fetcher = MarketDataFetcher(
                api_key=settings.TWELVE_DATA_API_KEY
            )
        return self._fetcher


@celery_app.task(
    bind=True,
    base=MarketDataTask,
    name='market_data.fetch_realtime_prices',
    max_retries=3,
    default_retry_delay=30
)
def fetch_realtime_prices(self) -> Dict[str, Any]:
    """
    Fetch current prices for all tracked symbols and save to database.

    This task runs every 1 minute to keep current_prices table updated.

    Returns:
        Dictionary with task results:
        - success: Number of successful fetches
        - failed: Number of failed fetches
        - symbols: List of processed symbols
        - timestamp: Task execution timestamp
    """
    logger.info(f"Starting realtime price fetch for {len(SYMBOL_NAMES)} symbols")

    try:
        # Fetch and save current prices
        results = self.fetcher.batch_fetch_and_save_current_prices(
            symbols=SYMBOL_NAMES,
            delay_between=1.5  # 1.5 seconds between requests to respect rate limits
        )

        # Count successes and failures
        success_count = sum(1 for quote in results.values() if quote is not None)
        failed_count = len(results) - success_count

        # Log results
        logger.info(
            f"Realtime price fetch completed: {success_count} successful, "
            f"{failed_count} failed"
        )

        return {
            'success': success_count,
            'failed': failed_count,
            'symbols': list(results.keys()),
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                symbol: {
                    'price': quote.get('close') if quote else None,
                    'success': quote is not None
                }
                for symbol, quote in results.items()
            }
        }

    except Exception as e:
        logger.error(f"Error in fetch_realtime_prices: {str(e)}", exc_info=True)
        # Retry the task
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=MarketDataTask,
    name='market_data.fetch_historical_data',
    max_retries=2,
    default_retry_delay=60
)
def fetch_historical_data(
    self,
    symbol: str,
    interval: str = '1h',
    outputsize: int = 500,
    days_back: int = None
) -> Dict[str, Any]:
    """
    Fetch historical OHLCV data for a symbol and save to database.

    Args:
        symbol: Trading symbol (e.g., 'DAX')
        interval: Timeframe (e.g., '1h', '1d')
        outputsize: Number of candles to fetch (default: 500)
        days_back: Number of days to fetch (alternative to outputsize)

    Returns:
        Dictionary with task results:
        - symbol: Symbol name
        - interval: Timeframe
        - candles_fetched: Number of candles fetched
        - candles_saved: Number of candles saved
        - timestamp: Task execution timestamp
    """
    logger.info(f"Fetching historical data for {symbol} ({interval})")

    try:
        # Fetch data
        if days_back:
            candles = self.fetcher.fetch_historical_range(
                symbol=symbol,
                interval=interval,
                days_back=days_back
            )
        else:
            candles = self.fetcher.fetch_time_series(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )

        # Save to database
        saved_count = self.fetcher.save_to_database(
            symbol=symbol,
            interval=interval,
            candles=candles
        )

        logger.info(
            f"Historical data fetch completed for {symbol}: "
            f"{len(candles)} fetched, {saved_count} saved"
        )

        return {
            'symbol': symbol,
            'interval': interval,
            'candles_fetched': len(candles),
            'candles_saved': saved_count,
            'timestamp': datetime.utcnow().isoformat(),
            'success': saved_count > 0
        }

    except Exception as e:
        logger.error(
            f"Error fetching historical data for {symbol}: {str(e)}",
            exc_info=True
        )
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=MarketDataTask,
    name='market_data.update_symbol_data',
    max_retries=2
)
def update_symbol_data(
    self,
    symbol: str,
    intervals: List[str] = None
) -> Dict[str, Any]:
    """
    Update data for a single symbol across multiple timeframes.

    Args:
        symbol: Trading symbol
        intervals: List of intervals to update (default: ['5m', '15m', '1h', '4h', '1d'])

    Returns:
        Dictionary with task results per interval
    """
    if intervals is None:
        intervals = ['5m', '15m', '1h', '4h', '1d']

    logger.info(f"Updating data for {symbol} across {len(intervals)} timeframes")

    results = {}

    for interval in intervals:
        try:
            # Determine appropriate outputsize based on interval
            outputsize_map = {
                '1m': 100,
                '5m': 200,
                '15m': 300,
                '30m': 300,
                '1h': 500,
                '4h': 500,
                '1d': 365,
                '1w': 52
            }
            outputsize = outputsize_map.get(interval, 200)

            # Fetch and save
            candles = self.fetcher.fetch_time_series(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )

            saved_count = self.fetcher.save_to_database(
                symbol=symbol,
                interval=interval,
                candles=candles
            )

            results[interval] = {
                'success': True,
                'fetched': len(candles),
                'saved': saved_count
            }

            logger.info(f"Updated {symbol} {interval}: {saved_count} candles saved")

        except Exception as e:
            logger.error(f"Error updating {symbol} {interval}: {str(e)}")
            results[interval] = {
                'success': False,
                'error': str(e)
            }

    return {
        'symbol': symbol,
        'intervals': results,
        'timestamp': datetime.utcnow().isoformat()
    }


@celery_app.task(
    bind=True,
    base=MarketDataTask,
    name='market_data.daily_data_refresh'
)
def daily_data_refresh(self) -> Dict[str, Any]:
    """
    Daily task to refresh all symbol data across all timeframes.

    Runs once per day at 2:00 AM UTC.

    Returns:
        Dictionary with refresh results for all symbols
    """
    logger.info("Starting daily data refresh for all symbols")

    results = {}

    for symbol_data in TRACKED_SYMBOLS:
        symbol = symbol_data['symbol']

        try:
            # Update symbol across all timeframes
            result = update_symbol_data.apply(args=[symbol])
            results[symbol] = result.get() if result else {'error': 'Task failed'}

        except Exception as e:
            logger.error(f"Error refreshing data for {symbol}: {str(e)}")
            results[symbol] = {'error': str(e)}

    logger.info(f"Daily data refresh completed for {len(results)} symbols")

    return {
        'symbols': results,
        'timestamp': datetime.utcnow().isoformat()
    }


@celery_app.task(name='market_data.check_api_usage')
def check_api_usage() -> Dict[str, Any]:
    """
    Check Twelve Data API usage and log it.

    Returns:
        Dictionary with API usage information
    """
    try:
        fetcher = MarketDataFetcher(api_key=settings.TWELVE_DATA_API_KEY)
        usage = fetcher.get_api_usage()

        logger.info(
            f"Twelve Data API Usage: {usage.get('current_usage', 'N/A')}/"
            f"{usage.get('plan_limit', 'N/A')} requests"
        )

        return usage

    except Exception as e:
        logger.error(f"Error checking API usage: {str(e)}")
        return {'error': str(e)}


# ================================================
# CELERY BEAT SCHEDULE
# ================================================

celery_app.conf.beat_schedule = {
    # Fetch realtime prices every 1 minute
    'fetch-realtime-prices-every-minute': {
        'task': 'market_data.fetch_realtime_prices',
        'schedule': 60.0,  # Every 60 seconds
        'options': {
            'expires': 55  # Expire if not executed within 55 seconds
        }
    },

    # Daily data refresh at 2:00 AM UTC
    'daily-data-refresh': {
        'task': 'market_data.daily_data_refresh',
        'schedule': crontab(hour=2, minute=0),
    },

    # Check API usage every hour
    'check-api-usage-hourly': {
        'task': 'market_data.check_api_usage',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
}

# ================================================
# UTILITY FUNCTIONS
# ================================================

def trigger_historical_fetch_for_all_symbols(
    interval: str = '1h',
    outputsize: int = 500
) -> List[str]:
    """
    Trigger historical data fetch for all symbols (for manual execution).

    Args:
        interval: Timeframe
        outputsize: Number of candles

    Returns:
        List of task IDs
    """
    task_ids = []

    for symbol in SYMBOL_NAMES:
        result = fetch_historical_data.delay(
            symbol=symbol,
            interval=interval,
            outputsize=outputsize
        )
        task_ids.append(result.id)
        logger.info(f"Triggered historical fetch for {symbol}: {result.id}")

    return task_ids


if __name__ == '__main__':
    # For testing tasks directly
    print("Market Data Tasks Module")
    print(f"Tracked symbols: {SYMBOL_NAMES}")
    print(f"Celery broker: {settings.CELERY_BROKER_URL}")
    print("\nAvailable tasks:")
    print("- fetch_realtime_prices")
    print("- fetch_historical_data")
    print("- update_symbol_data")
    print("- daily_data_refresh")
    print("- check_api_usage")
