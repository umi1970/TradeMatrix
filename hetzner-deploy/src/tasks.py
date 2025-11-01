"""
Celery Background Tasks for Liquidity Alert System
Simplified version - only includes liquidity level monitoring
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from celery import Celery
from celery.schedules import crontab

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Import agents for liquidity alerts
# Using relative imports since we're in the src package
from .liquidity_alert_engine import LiquidityAlertEngine
from .price_fetcher import PriceFetcher
from .push_notification_service import PushNotificationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery(
    'tradematrix_liquidity_alerts',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# ================================================
# Celery Tasks - Liquidity Alert System
# ================================================

@celery.task(name='check_liquidity_alerts', bind=True)
def check_liquidity_alerts(self):
    """
    Celery task: Check liquidity levels every 1 minute

    Monitors real-time prices and checks if they crossed key liquidity levels:
    - Yesterday High
    - Yesterday Low
    - Pivot Point

    Sends browser push notifications when levels are crossed.
    """
    try:
        logger.info("=" * 70)
        logger.info("🔍 Starting liquidity alert check (1-minute interval)")
        logger.info("=" * 70)

        # Initialize services
        price_fetcher = PriceFetcher()
        alert_engine = LiquidityAlertEngine()
        push_service = PushNotificationService()

        # Monitor 5 symbols
        symbols = [
            ('^GDAXI', 'DAX'),
            ('^NDX', 'NASDAQ'),
            ('^DJI', 'DOW'),
            ('EURUSD', 'EUR/USD'),
            ('EURGBP', 'EUR/GBP'),
        ]

        # Step 1: Fetch all prices and update cache
        logger.info("\n📊 Fetching prices for all symbols...")
        prices_fetched = 0

        for symbol_code, symbol_name in symbols:
            try:
                logger.info(f"  Fetching {symbol_name} ({symbol_code})...")

                price_data = price_fetcher.fetch_price(symbol_code)
                if price_data:
                    price_fetcher.update_price_cache(symbol_code, price_data)
                    logger.info(f"    💰 {price_data['current_price']}")
                    prices_fetched += 1
                else:
                    logger.warning(f"    ⚠️  Could not fetch price")

            except Exception as e:
                logger.error(f"    ❌ Error fetching price: {str(e)}")
                continue

        logger.info(f"\n✅ Fetched {prices_fetched}/{len(symbols)} prices")

        # Step 2: Check ALL subscriptions for triggered alerts
        logger.info("\n🔍 Checking liquidity levels...")
        triggered_alerts = alert_engine.check_all_alerts()

        # Step 3: Send push notifications for triggered alerts
        total_alerts_triggered = 0

        if triggered_alerts:
            logger.info(f"\n🎯 {len(triggered_alerts)} alert(s) triggered!")

            for alert in triggered_alerts:
                try:
                    # Format notification title and body
                    title = f"🔴 {alert['symbol']} touched {alert['level_type'].replace('_', ' ').title()}"
                    body = f"Level: {alert['level_price']:.2f} | Current: {alert['current_price']:.2f}"

                    success = push_service.send_push_notification(
                        user_id=alert['user_id'],
                        title=title,
                        body=body,
                        data={
                            'symbol': alert['symbol'],
                            'level_type': alert['level_type'],
                            'level_price': float(alert['level_price']),
                            'current_price': float(alert['current_price'])
                        }
                    )

                    if success:
                        total_alerts_triggered += 1
                        logger.info(f"  ✅ {alert['symbol']} - {alert['level_type']} - User {alert['user_id'][:8]}...")
                    else:
                        logger.warning(f"  ⚠️  Failed to send notification for {alert['symbol']}")

                except Exception as e:
                    logger.error(f"  ❌ Error sending notification: {str(e)}")
        else:
            logger.info("  ✓ No levels crossed")

        logger.info("=" * 70)
        logger.info(f"✅ Check complete! {total_alerts_triggered} notification(s) sent")
        logger.info("=" * 70)

        return {
            'status': 'success',
            'alerts_triggered': total_alerts_triggered,
            'symbols_checked': len(symbols)
        }

    except Exception as e:
        logger.error(f"❌ Fatal error in liquidity alert check: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


# ================================================
# Celery Beat Schedule
# ================================================

celery.conf.beat_schedule = {
    # Check liquidity alerts every 60 seconds
    'liquidity-alerts': {
        'task': 'check_liquidity_alerts',
        'schedule': 60.0,  # Every 60 seconds
        'options': {
            'expires': 55,  # Task expires after 55 seconds (before next run)
        }
    },
}
