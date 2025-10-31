"""
TradeMatrix.ai - EOD Data Layer Celery Tasks
Scheduled tasks for fetching and processing End-of-Day market data
"""

from celery import Celery
from celery.schedules import crontab
from datetime import datetime
import os
import logging
from supabase import create_client

from eod_data_fetcher import fetch_eod_data_task

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app = Celery('eod_tasks', broker=redis_url, backend=redis_url)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Berlin',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    result_expires=86400,  # Results expire after 24 hours
)

# Supabase client (service role)
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

supabase = create_client(supabase_url, supabase_key)


# ============================================================
# Scheduled Tasks
# ============================================================

@celery_app.task(name='eod.fetch_daily', bind=True)
def fetch_daily_eod_data(self):
    """
    Daily EOD data fetch task
    
    Scheduled: Daily at 07:30 CET
    Purpose: Fetch previous day's EOD data for all enabled symbols
    
    Returns:
        Dict with fetch results
    """
    logger.info("Starting daily EOD data fetch")
    
    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Fetching EOD data'})
        
        # Run async fetch
        import asyncio
        results = asyncio.run(fetch_eod_data_task(supabase))
        
        # Log results
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        logger.info(f"Daily EOD fetch complete: {success_count}/{total_count} successful")
        
        return {
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat(),
            'success_count': success_count,
            'total_count': total_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Daily EOD fetch failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(name='eod.pre_us_open_refresh', bind=True)
def pre_us_open_refresh(self):
    """
    Pre-US Open data refresh (optional)
    
    Scheduled: Daily at 14:45 CET (before US market opens at 15:30)
    Purpose: Refresh EOD data in case of corrections or late updates
    
    Note: This is optional and disabled by default in config
    """
    logger.info("Starting pre-US open EOD refresh")
    
    try:
        import asyncio
        results = asyncio.run(fetch_eod_data_task(supabase))
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Pre-US open refresh complete: {success_count}/{len(results)} successful")
        
        return {
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat(),
            'success_count': success_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Pre-US open refresh failed: {e}")
        return {'status': 'failed', 'error': str(e)}


@celery_app.task(name='eod.weekend_maintenance', bind=True)
def weekend_maintenance(self):
    """
    Weekend maintenance task
    
    Scheduled: Saturday at 09:00 CET
    Purpose: Archive old EOD data, cleanup logs, generate weekly summaries
    """
    logger.info("Starting weekend EOD maintenance")
    
    try:
        # Archive old fetch logs (keep last 30 days)
        cutoff_date = (datetime.utcnow() - timedelta(days=30)).date()
        
        delete_result = supabase.table('eod_fetch_log')\
            .delete()\
            .lt('fetch_date', cutoff_date.isoformat())\
            .execute()
        
        deleted_count = len(delete_result.data) if delete_result.data else 0
        
        logger.info(f"Weekend maintenance complete: Deleted {deleted_count} old fetch logs")
        
        return {
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat(),
            'deleted_logs': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Weekend maintenance failed: {e}")
        return {'status': 'failed', 'error': str(e)}


@celery_app.task(name='eod.calculate_weekly_summary', bind=True)
def calculate_weekly_summary(self):
    """
    Calculate weekly market summary statistics
    
    Purpose: Generate ATR, weekly high/low, performance metrics
    Can be called on-demand or scheduled weekly
    """
    logger.info("Calculating weekly market summary")
    
    try:
        # Get all active symbols
        symbols_result = supabase.table('symbols')\
            .select('id, symbol')\
            .eq('is_active', True)\
            .execute()
        
        summaries = []
        
        for symbol_data in symbols_result.data:
            symbol_id = symbol_data['id']
            symbol_name = symbol_data['symbol']
            
            # Get last 7 days of EOD data
            eod_result = supabase.table('eod_data')\
                .select('*')\
                .eq('symbol_id', symbol_id)\
                .order('trade_date', desc=True)\
                .limit(7)\
                .execute()
            
            if not eod_result.data or len(eod_result.data) < 5:
                continue
            
            data = eod_result.data
            
            # Calculate weekly metrics
            weekly_high = max(float(d['high']) for d in data)
            weekly_low = min(float(d['low']) for d in data)
            weekly_range = weekly_high - weekly_low
            
            # ATR
            ranges = [float(d['high']) - float(d['low']) for d in data]
            avg_range = sum(ranges) / len(ranges)
            
            summaries.append({
                'symbol': symbol_name,
                'weekly_high': weekly_high,
                'weekly_low': weekly_low,
                'weekly_range': weekly_range,
                'avg_daily_range': avg_range
            })
        
        logger.info(f"Weekly summary calculated for {len(summaries)} symbols")
        
        return {
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat(),
            'summaries': summaries
        }
        
    except Exception as e:
        logger.error(f"Weekly summary calculation failed: {e}")
        return {'status': 'failed', 'error': str(e)}


# ============================================================
# On-Demand Tasks
# ============================================================

@celery_app.task(name='eod.fetch_single_symbol')
def fetch_single_symbol(symbol_name: str):
    """
    Fetch EOD data for a single symbol (on-demand)
    
    Args:
        symbol_name: Symbol to fetch (e.g., '^GDAXI')
        
    Returns:
        Dict with fetch result
    """
    logger.info(f"Fetching EOD data for {symbol_name}")
    
    try:
        from eod_data_fetcher import EODDataFetcher
        
        fetcher = EODDataFetcher(supabase)
        
        # Find symbol config
        import yaml
        with open('config/eod_data_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        symbol_config = None
        for category in ['indices', 'forex']:
            if category in config['symbols']:
                for s in config['symbols'][category]:
                    if s['symbol'] == symbol_name:
                        symbol_config = s
                        break
        
        if not symbol_config:
            return {'status': 'failed', 'error': f'Symbol {symbol_name} not found in config'}
        
        # Fetch
        import asyncio
        success = asyncio.run(fetcher.fetch_and_store_symbol(symbol_config))
        
        return {
            'status': 'completed' if success else 'failed',
            'symbol': symbol_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Single symbol fetch failed for {symbol_name}: {e}")
        return {'status': 'failed', 'error': str(e)}


@celery_app.task(name='eod.validate_data_quality')
def validate_data_quality(days: int = 7):
    """
    Validate data quality for recent EOD data
    
    Args:
        days: Number of recent days to validate
        
    Returns:
        Dict with validation results
    """
    logger.info(f"Validating EOD data quality for last {days} days")
    
    try:
        from datetime import timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
        
        # Get EOD data from last N days
        eod_result = supabase.table('eod_data')\
            .select('symbol_id, trade_date, quality_score, is_validated')\
            .gte('trade_date', cutoff_date.isoformat())\
            .execute()
        
        if not eod_result.data:
            return {'status': 'no_data', 'message': 'No data found in date range'}
        
        data = eod_result.data
        
        # Calculate metrics
        total_records = len(data)
        validated_records = sum(1 for d in data if d['is_validated'])
        avg_quality_score = sum(float(d['quality_score'] or 0) for d in data) / total_records
        
        validation_rate = (validated_records / total_records) * 100
        
        result = {
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat(),
            'days_analyzed': days,
            'total_records': total_records,
            'validated_records': validated_records,
            'validation_rate_percent': round(validation_rate, 2),
            'avg_quality_score': round(avg_quality_score, 2)
        }
        
        logger.info(f"Quality validation complete: {validation_rate:.1f}% validated")
        
        return result
        
    except Exception as e:
        logger.error(f"Data quality validation failed: {e}")
        return {'status': 'failed', 'error': str(e)}


# ============================================================
# Celery Beat Schedule
# ============================================================

celery_app.conf.beat_schedule = {
    # Daily EOD fetch at 07:30 CET
    'fetch-eod-daily': {
        'task': 'eod.fetch_daily',
        'schedule': crontab(hour=7, minute=30),
        'options': {'queue': 'eod_tasks'}
    },
    
    # Pre-US Open refresh at 14:45 CET (disabled by default)
    # Uncomment to enable
    # 'pre-us-open-refresh': {
    #     'task': 'eod.pre_us_open_refresh',
    #     'schedule': crontab(hour=14, minute=45),
    #     'options': {'queue': 'eod_tasks'}
    # },
    
    # Weekend maintenance on Saturday at 09:00 CET
    'weekend-maintenance': {
        'task': 'eod.weekend_maintenance',
        'schedule': crontab(hour=9, minute=0, day_of_week=6),  # Saturday
        'options': {'queue': 'eod_tasks'}
    },
    
    # Weekly summary on Monday at 08:00 CET
    'weekly-summary': {
        'task': 'eod.calculate_weekly_summary',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Monday
        'options': {'queue': 'eod_tasks'}
    },
}


# ============================================================
# Manual Execution
# ============================================================

if __name__ == '__main__':
    # For manual testing
    print("=== EOD Data Layer Tasks ===")
    print("Available tasks:")
    print("1. fetch_daily_eod_data() - Fetch all symbols")
    print("2. fetch_single_symbol('SYMBOL') - Fetch specific symbol")
    print("3. validate_data_quality(days=7) - Validate recent data")
    print("4. calculate_weekly_summary() - Generate weekly stats")
    print("\nRun with: celery -A eod_tasks worker --loglevel=info")
    print("Schedule with: celery -A eod_tasks beat --loglevel=info")
