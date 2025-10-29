"""
Celery Background Tasks for Market Data Ingestion
Handles historical seeding, real-time updates, daily calculations, and pivot calculations
"""

import logging
from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import List, Dict, Any, Optional
import pytz

from celery import Celery
from celery.schedules import crontab

# Import configuration and utilities
import sys
import os

# Add API src to path for imports
api_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api/src'))
sys.path.insert(0, api_src_path)

from config import settings, supabase_admin
from core.market_data_fetcher import MarketDataFetcher

# Import agents
from alert_engine import AlertEngine
from signal_bot import SignalBot
from risk_manager import RiskManager
from chart_watcher import ChartWatcher
from journal_bot import JournalBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery(
    'tradematrix_agents',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Berlin',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Initialize Market Data Fetcher
fetcher = MarketDataFetcher()


# ================================================
# Helper Functions
# ================================================

def get_active_symbols() -> List[Dict[str, Any]]:
    """
    Fetch all active symbols from database

    Returns:
        List of active symbol records
    """
    try:
        response = supabase_admin.table('market_symbols') \
            .select('*') \
            .eq('active', True) \
            .execute()

        symbols = response.data
        logger.info(f"Found {len(symbols)} active symbols")
        return symbols

    except Exception as e:
        logger.error(f"Error fetching active symbols: {str(e)}")
        return []


def get_symbol_by_id(symbol_id: str) -> Optional[Dict[str, Any]]:
    """
    Get symbol record by ID

    Args:
        symbol_id: UUID of symbol

    Returns:
        Symbol record or None
    """
    try:
        response = supabase_admin.table('market_symbols') \
            .select('*') \
            .eq('id', symbol_id) \
            .single() \
            .execute()

        return response.data

    except Exception as e:
        logger.error(f"Error fetching symbol {symbol_id}: {str(e)}")
        return None


def insert_candles(candles: List[Dict[str, Any]], symbol_id: str, timeframe: str) -> int:
    """
    Insert OHLCV candles into database (with conflict handling)

    Args:
        candles: List of candle dictionaries
        symbol_id: UUID of symbol
        timeframe: Timeframe (1m, 5m, 15m, 1h, 1d)

    Returns:
        Number of candles inserted
    """
    if not candles:
        return 0

    rows = []
    for candle in candles:
        rows.append({
            'ts': candle.get('datetime'),
            'symbol_id': symbol_id,
            'timeframe': timeframe,
            'open': float(candle.get('open', 0)),
            'high': float(candle.get('high', 0)),
            'low': float(candle.get('low', 0)),
            'close': float(candle.get('close', 0)),
            'volume': int(candle.get('volume', 0))
        })

    try:
        # Upsert to handle duplicates
        response = supabase_admin.table('ohlc').upsert(
            rows,
            on_conflict='symbol_id,timeframe,ts'
        ).execute()

        inserted = len(response.data) if response.data else 0
        logger.info(f"Inserted/Updated {inserted} candles for symbol {symbol_id} ({timeframe})")
        return inserted

    except Exception as e:
        logger.error(f"Error inserting candles: {str(e)}")
        return 0


def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Pivot Points (PP, R1, R2, S1, S2)

    Args:
        high: Yesterday's high
        low: Yesterday's low
        close: Yesterday's close

    Returns:
        Dictionary with pivot levels
    """
    pp = (high + low + close) / 3
    r1 = (2 * pp) - low
    r2 = pp + (high - low)
    s1 = (2 * pp) - high
    s2 = pp - (high - low)

    return {
        'pivot': round(pp, 2),
        'r1': round(r1, 2),
        'r2': round(r2, 2),
        's1': round(s1, 2),
        's2': round(s2, 2)
    }


# ================================================
# Celery Tasks
# ================================================

@celery.task(name='historical_seed_task', bind=True)
def historical_seed_task(self, symbol: str, interval: str = '1h', days: int = 30):
    """
    One-time historical data fetch for a symbol

    Args:
        symbol: Trading symbol (e.g., "DAX", "NDX")
        interval: Time interval (1m, 5m, 15m, 1h, 1d)
        days: Number of days to fetch (max 365)

    Returns:
        Number of candles inserted
    """
    logger.info(f"Starting historical seed for {symbol} ({interval}, {days} days)")

    try:
        # Get symbol record from database
        symbol_record = supabase_admin.table('market_symbols') \
            .select('*') \
            .eq('symbol', symbol) \
            .eq('active', True) \
            .single() \
            .execute()

        if not symbol_record.data:
            logger.error(f"Symbol {symbol} not found or inactive")
            return 0

        symbol_id = symbol_record.data['id']

        # Fetch historical data
        candles = fetcher.fetch_historical_range(
            symbol=symbol,
            interval=interval,
            days_back=days
        )

        if not candles:
            logger.warning(f"No candles fetched for {symbol}")
            return 0

        # Insert into database
        inserted = insert_candles(candles, symbol_id, interval)

        logger.info(f"Historical seed completed for {symbol}: {inserted} candles inserted")
        return inserted

    except Exception as e:
        logger.error(f"Error in historical_seed_task for {symbol}: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)


@celery.task(name='realtime_pull_task', bind=True)
def realtime_pull_task(self):
    """
    Fetch latest candles for all active symbols (runs every 60 seconds)

    This task fetches the most recent candle for each active symbol
    and updates the database. Handles multiple timeframes.

    Returns:
        Dictionary with results per symbol
    """
    logger.info("Starting real-time data pull for all active symbols")

    results = {}
    symbols = get_active_symbols()

    if not symbols:
        logger.warning("No active symbols found")
        return results

    # Timeframes to update
    timeframes = ['1m', '5m', '15m', '1h']

    for symbol_record in symbols:
        symbol = symbol_record['symbol']
        symbol_id = symbol_record['id']

        logger.info(f"Fetching real-time data for {symbol}")

        for timeframe in timeframes:
            try:
                # Fetch latest candles (last 2 to ensure we get the current one)
                data = fetcher.fetch_time_series(
                    symbol=symbol,
                    interval=timeframe,
                    outputsize=2
                )

                candles = data.get('values', [])

                if candles:
                    # Insert into database
                    inserted = insert_candles(candles, symbol_id, timeframe)
                    results[f"{symbol}_{timeframe}"] = {
                        'success': True,
                        'candles': inserted
                    }
                else:
                    results[f"{symbol}_{timeframe}"] = {
                        'success': False,
                        'error': 'No candles returned'
                    }

            except Exception as e:
                logger.error(f"Error fetching {symbol} ({timeframe}): {str(e)}")
                results[f"{symbol}_{timeframe}"] = {
                    'success': False,
                    'error': str(e)
                }

    logger.info(f"Real-time pull completed: {len(results)} symbol-timeframe combinations processed")
    return results


@celery.task(name='daily_close_task', bind=True)
def daily_close_task(self):
    """
    Calculate Yesterday's High, Low, Close and save to levels_daily
    Runs daily at 20:59 MEZ (end of trading day)

    Returns:
        Dictionary with results per symbol
    """
    logger.info("Starting daily close calculation")

    results = {}
    symbols = get_active_symbols()

    if not symbols:
        logger.warning("No active symbols found")
        return results

    # Get yesterday's date (since we run at 20:59 on the same day)
    berlin_tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(berlin_tz)
    trade_date = now.date()

    for symbol_record in symbols:
        symbol = symbol_record['symbol']
        symbol_id = symbol_record['id']

        logger.info(f"Calculating daily levels for {symbol} on {trade_date}")

        try:
            # Fetch today's daily candle
            data = fetcher.fetch_time_series(
                symbol=symbol,
                interval='1day',
                outputsize=1,
                timezone='Europe/Berlin'
            )

            candles = data.get('values', [])

            if not candles:
                logger.warning(f"No daily candle found for {symbol}")
                results[symbol] = {'success': False, 'error': 'No data'}
                continue

            candle = candles[0]

            # Extract values
            y_high = float(candle.get('high', 0))
            y_low = float(candle.get('low', 0))
            y_close = float(candle.get('close', 0))

            # Upsert into levels_daily
            response = supabase_admin.table('levels_daily').upsert({
                'trade_date': str(trade_date),
                'symbol_id': symbol_id,
                'y_high': y_high,
                'y_low': y_low,
                'y_close': y_close,
            }, on_conflict='trade_date,symbol_id').execute()

            logger.info(f"Daily levels saved for {symbol}: H={y_high}, L={y_low}, C={y_close}")

            results[symbol] = {
                'success': True,
                'y_high': y_high,
                'y_low': y_low,
                'y_close': y_close
            }

        except Exception as e:
            logger.error(f"Error calculating daily levels for {symbol}: {str(e)}")
            results[symbol] = {'success': False, 'error': str(e)}

    logger.info(f"Daily close calculation completed: {len(results)} symbols processed")
    return results


@celery.task(name='calculate_pivots_task', bind=True)
def calculate_pivots_task(self):
    """
    Calculate Pivot Points (PP, R1, R2, S1, S2) for all active symbols
    Runs daily at 07:55 MEZ (before market open)

    Uses yesterday's H, L, C from levels_daily table

    Returns:
        Dictionary with results per symbol
    """
    logger.info("Starting pivot points calculation")

    results = {}
    symbols = get_active_symbols()

    if not symbols:
        logger.warning("No active symbols found")
        return results

    # Get today's date
    berlin_tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(berlin_tz)
    today = now.date()

    # Get yesterday's date
    yesterday = today - timedelta(days=1)

    for symbol_record in symbols:
        symbol = symbol_record['symbol']
        symbol_id = symbol_record['id']

        logger.info(f"Calculating pivots for {symbol} on {today}")

        try:
            # Fetch yesterday's levels from database
            response = supabase_admin.table('levels_daily') \
                .select('*') \
                .eq('symbol_id', symbol_id) \
                .eq('trade_date', str(yesterday)) \
                .single() \
                .execute()

            if not response.data:
                logger.warning(f"No yesterday's data found for {symbol}")
                results[symbol] = {'success': False, 'error': 'No yesterday data'}
                continue

            levels = response.data

            # Extract yesterday's values
            y_high = float(levels['y_high'])
            y_low = float(levels['y_low'])
            y_close = float(levels['y_close'])

            # Calculate pivot points
            pivots = calculate_pivot_points(y_high, y_low, y_close)

            # Update today's record with pivot points
            response = supabase_admin.table('levels_daily').upsert({
                'trade_date': str(today),
                'symbol_id': symbol_id,
                'pivot': pivots['pivot'],
                'r1': pivots['r1'],
                'r2': pivots['r2'],
                's1': pivots['s1'],
                's2': pivots['s2'],
            }, on_conflict='trade_date,symbol_id').execute()

            logger.info(f"Pivots calculated for {symbol}: PP={pivots['pivot']}, "
                       f"R1={pivots['r1']}, R2={pivots['r2']}, S1={pivots['s1']}, S2={pivots['s2']}")

            results[symbol] = {
                'success': True,
                **pivots
            }

        except Exception as e:
            logger.error(f"Error calculating pivots for {symbol}: {str(e)}")
            results[symbol] = {'success': False, 'error': str(e)}

    logger.info(f"Pivot calculation completed: {len(results)} symbols processed")
    return results


@celery.task(name='alert_engine_task', bind=True)
def alert_engine_task(self):
    """
    Monitor market data and generate real-time alerts
    Runs every 60 seconds

    Alert Types:
    - range_break: ORB 5m Close above/below 15m Range
    - retest_touch: Price returns to Range edge
    - asia_sweep_confirmed: EU Open above y_low after Asia sweep
    - pivot_touch: Price touches Pivot Point
    - r1_touch: Price touches R1
    - s1_touch: Price touches S1

    Returns:
        Dictionary with execution summary and generated alerts
    """
    logger.info("Starting Alert Engine execution")

    try:
        # Initialize Alert Engine with admin client
        engine = AlertEngine(supabase_client=supabase_admin)

        # Run alert checks for all active symbols
        result = engine.run()

        logger.info(f"Alert Engine completed: {result['alerts_generated']} alerts generated")
        return result

    except Exception as e:
        logger.error(f"Error in alert_engine_task: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)


@celery.task(name='signal_bot_task', bind=True)
def signal_bot_task(self):
    """
    Generate entry/exit signals based on market structure analysis
    Runs every 60 seconds during market hours

    Signal Types:
    - entry: Long/Short entry signals validated by ValidationEngine
    - exit: TP/SL/breakeven exit signals using RiskCalculator

    Returns:
        Dictionary with execution summary and generated signals
    """
    logger.info("Starting SignalBot execution")

    try:
        # Initialize SignalBot with admin client
        bot = SignalBot(supabase_client=supabase_admin)

        # Run signal generation for all active symbols
        result = bot.run()

        logger.info(f"SignalBot completed: {result['entry_signals']} entry, {result['exit_signals']} exit signals")
        return result

    except Exception as e:
        logger.error(f"Error in signal_bot_task: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)


@celery.task(name='risk_manager_task', bind=True)
def risk_manager_task(self):
    """
    Monitor portfolio risk and enforce risk management rules
    Runs every 60 seconds

    Checks:
    - Portfolio risk exposure (max 5% total risk)
    - Daily loss limit (3-loss rule)
    - Position size compliance (1% risk per trade)
    - Stop loss adjustments (break-even at +0.5R)

    Returns:
        Dictionary with execution summary and risk alerts
    """
    logger.info("Starting RiskManager execution")

    try:
        # Initialize RiskManager with admin client
        manager = RiskManager(supabase_client=supabase_admin)

        # Run risk checks for portfolio
        result = manager.run()

        logger.info(
            f"RiskManager completed: {result['risk_alerts_generated']} alerts, "
            f"{result['stop_loss_adjustments_count']} SL adjustments"
        )
        return result

    except Exception as e:
        logger.error(f"Error in risk_manager_task: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)


@celery.task(name='chart_watcher_task', bind=True)
def chart_watcher_task(self, timeframe: str = '1h'):
    """
    Analyze chart images using OpenAI Vision API to detect patterns
    Runs every 5 minutes during market hours

    Pattern Types:
    - Head & Shoulders (bullish/bearish)
    - Double Top/Bottom
    - Triangles (ascending/descending/symmetrical)
    - Flags & Pennants
    - Wedges (rising/falling)
    - Channels

    Args:
        timeframe: Chart timeframe to analyze (default: 1h)

    Returns:
        Dictionary with execution summary and detected patterns
    """
    logger.info(f"Starting ChartWatcher execution for {timeframe} timeframe")

    try:
        # Initialize ChartWatcher with admin client and OpenAI API key
        watcher = ChartWatcher(
            supabase_client=supabase_admin,
            openai_api_key=settings.OPENAI_API_KEY
        )

        # Run chart analysis for all active symbols
        result = watcher.run(timeframe=timeframe)

        logger.info(f"ChartWatcher completed: {result['analyses_created']} charts analyzed")
        return result

    except Exception as e:
        logger.error(f"Error in chart_watcher_task: {str(e)}")
        self.retry(exc=e, countdown=300, max_retries=3)  # Retry after 5 minutes


@celery.task(name='journal_bot_task', bind=True)
def journal_bot_task(self):
    """
    Generate automated trading reports (PDF/DOCX) with AI insights
    Runs daily at 21:00 MEZ (end of trading day)

    Report Contents:
    - Trade Summary (win/loss ratio, P&L, R-multiples)
    - AI Insights (LangChain analysis of trading patterns)
    - Trade List (detailed table)
    - Performance Metrics (charts/stats)
    - Recommendations (AI-generated improvement suggestions)

    Outputs:
    - PDF report (reportlab)
    - DOCX report (python-docx)
    - Uploaded to Supabase Storage (bucket: 'reports')
    - Metadata saved to 'reports' table

    Returns:
        Dictionary with execution summary and generated reports
    """
    logger.info("Starting JournalBot execution")

    try:
        # Initialize JournalBot with admin client and OpenAI API key
        bot = JournalBot(
            supabase_client=supabase_admin,
            openai_api_key=settings.OPENAI_API_KEY
        )

        # Run report generation for all users
        result = bot.run()

        logger.info(f"JournalBot completed: {result['reports_generated']} reports generated")
        return result

    except Exception as e:
        logger.error(f"Error in journal_bot_task: {str(e)}")
        self.retry(exc=e, countdown=300, max_retries=3)  # Retry after 5 minutes


# ================================================
# Celery Beat Schedule
# ================================================

celery.conf.beat_schedule = {
    # Real-time data pull - every 60 seconds
    'realtime-pull': {
        'task': 'realtime_pull_task',
        'schedule': 60.0,  # Every 60 seconds
        'options': {
            'expires': 55.0,  # Expire if not executed within 55 seconds
        }
    },

    # Alert Engine - every 60 seconds
    'alert-engine': {
        'task': 'alert_engine_task',
        'schedule': 60.0,  # Every 60 seconds
        'options': {
            'expires': 55.0,  # Expire if not executed within 55 seconds
        }
    },

    # SignalBot - every 60 seconds
    'signal-bot': {
        'task': 'signal_bot_task',
        'schedule': 60.0,  # Every 60 seconds
        'options': {
            'expires': 55.0,  # Expire if not executed within 55 seconds
        }
    },

    # RiskManager - every 60 seconds
    'risk-manager': {
        'task': 'risk_manager_task',
        'schedule': 60.0,  # Every 60 seconds
        'options': {
            'expires': 55.0,  # Expire if not executed within 55 seconds
        }
    },

    # ChartWatcher - every 5 minutes (300 seconds)
    'chart-watcher': {
        'task': 'chart_watcher_task',
        'schedule': 300.0,  # Every 5 minutes
        'kwargs': {'timeframe': '1h'},
        'options': {
            'expires': 290.0,  # Expire if not executed within 290 seconds
        }
    },

    # Daily close calculation - 20:59 MEZ
    'daily-close': {
        'task': 'daily_close_task',
        'schedule': crontab(hour=20, minute=59, day_of_week='0-4'),  # Mon-Fri only
        'options': {
            'expires': 300.0,  # 5 minutes to complete
        }
    },

    # Pivot calculation - 07:55 MEZ
    'calculate-pivots': {
        'task': 'calculate_pivots_task',
        'schedule': crontab(hour=7, minute=55, day_of_week='1-5'),  # Tue-Sat (for Mon-Fri trading)
        'options': {
            'expires': 300.0,  # 5 minutes to complete
        }
    },

    # JournalBot - Daily reports at 21:00 MEZ
    'journal-bot': {
        'task': 'journal_bot_task',
        'schedule': crontab(hour=21, minute=0, day_of_week='0-4'),  # Mon-Fri only
        'options': {
            'expires': 600.0,  # 10 minutes to complete
        }
    },
}


# ================================================
# Manual Task Triggers (for testing)
# ================================================

@celery.task(name='test_connection')
def test_connection():
    """
    Test task to verify Celery is working

    Returns:
        Success message
    """
    logger.info("Test task executed successfully")
    return {
        'status': 'success',
        'message': 'Celery is working!',
        'timestamp': datetime.now().isoformat()
    }


if __name__ == '__main__':
    # Run worker
    celery.start()
