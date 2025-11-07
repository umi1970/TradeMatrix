"""
Celery Background Tasks for Liquidity Alert System
Simplified version - only includes liquidity level monitoring
"""

import asyncio
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

# Import AI agents (ChartWatcher, MorningPlanner, JournalBot)
from .chart_watcher import ChartWatcher
from .morning_planner import MorningPlanner
from .journal_bot import JournalBot

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

        # Step 1: Fetch all prices and update cache
        logger.info("\n📊 Fetching realtime prices...")
        fetched_prices = price_fetcher.fetch_all_prices()
        logger.info(f"✓ Fetched prices for {len(fetched_prices)} symbol(s)")

        # Step 2: Check all alerts (AlertEngine reads from price_cache)
        logger.info("\n🔔 Checking liquidity alerts...")
        triggered_alerts = alert_engine.check_all_alerts()

        # Step 3: Send push notifications for triggered alerts
        total_notifications_sent = 0

        if triggered_alerts:
            logger.info(f"\n🎯 {len(triggered_alerts)} alert(s) triggered!")

            for alert in triggered_alerts:
                try:
                    # Format notification using context from AlertEngine
                    context = alert.get('context', {})
                    title = f"{context.get('emoji', '🔔')} {alert['symbol']} Alert!"
                    body = f"{context.get('title', 'Level crossed')}: {alert['level_price']} (Current: {alert['current_price']})"

                    success = push_service.send_push_notification(
                        user_id=alert['user_id'],
                        title=title,
                        body=body,
                        data={
                            'symbol': alert['symbol'],
                            'level_type': alert['level_type'],
                            'level_price': str(alert['level_price']),
                            'current_price': str(alert['current_price']),
                        }
                    )

                    if success:
                        total_notifications_sent += 1
                        logger.info(f"  ✅ Notification sent: {alert['symbol']} ({alert['level_type']})")
                    else:
                        logger.warning(f"  ⚠️  Failed to send notification: {alert['symbol']}")

                except Exception as e:
                    logger.error(f"  ❌ Error sending notification for {alert.get('symbol', 'unknown')}: {str(e)}")
        else:
            logger.info("  ✓ No alerts triggered")

        logger.info("=" * 70)
        logger.info(f"✅ Check complete! {total_notifications_sent} notification(s) sent")
        logger.info("=" * 70)

        return {
            'status': 'success',
            'alerts_triggered': total_notifications_sent,
            'symbols_checked': len(fetched_prices)
        }

    except Exception as e:
        logger.error(f"❌ Fatal error in liquidity alert check: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


# ================================================
# Celery Tasks - AI Agents
# ================================================

@celery.task(name='run_chart_analysis', bind=True)
def run_chart_analysis_task(self, symbol: str = None, user_id: str = None, tier: str = "free"):
    """
    ChartWatcher - runs every 6 hours (or on-demand via /api/agents/trigger)
    Analyzes chart images using OpenAI Vision API

    Args:
        symbol: Optional single symbol to analyze (e.g., "DAX", "NDX")
                If None, analyzes all active symbols
        user_id: Optional user ID who triggered this (None for system-triggered)
        tier: User's subscription tier (free, starter, pro, expert)
    """
    try:
        logger.info("=" * 70)
        if symbol:
            logger.info(f"📊 Starting ChartWatcher analysis for {symbol}")
        else:
            logger.info("📊 Starting ChartWatcher analysis for all symbols")
        if user_id:
            logger.info(f"   Triggered by user: {user_id} (tier: {tier})")
        else:
            logger.info("   System-triggered (scheduled)")
        logger.info("=" * 70)

        # Initialize ChartWatcher
        from src.config.supabase import get_supabase_admin
        watcher = ChartWatcher(
            supabase_client=get_supabase_admin(),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            user_id=user_id,
            tier=tier
        )

        # Run chart analysis (async method - use asyncio.run)
        # Pass symbol as list if provided (ChartWatcher.run() expects List[str])
        symbols_list = [symbol] if symbol else None
        result = asyncio.run(watcher.run(symbols=symbols_list, timeframe='4h'))

        logger.info("=" * 70)
        logger.info(f"✅ ChartWatcher completed: {result.get('analyses_created', 0)} analyses created")
        logger.info("=" * 70)

        return result

    except Exception as e:
        logger.error(f"❌ Fatal error in ChartWatcher: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@celery.task(name='run_morning_planner', bind=True)
def run_morning_planner_task(self):
    """
    MorningPlanner - runs daily at 08:25 MEZ
    Analyzes overnight movements and generates trading setups
    """
    try:
        logger.info("=" * 70)
        logger.info("🌅 Starting MorningPlanner analysis")
        logger.info("=" * 70)

        # Initialize MorningPlanner
        from src.config.supabase import get_supabase_admin
        planner = MorningPlanner(
            supabase_client=get_supabase_admin()
        )

        # Run morning analysis (async method - use asyncio.run)
        result = asyncio.run(planner.run())

        logger.info("=" * 70)
        logger.info(f"✅ MorningPlanner completed: {result.get('setups_generated', 0)} setups generated")
        logger.info("=" * 70)

        return result

    except Exception as e:
        logger.error(f"❌ Fatal error in MorningPlanner: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@celery.task(name='run_journal_bot', bind=True)
def run_journal_bot_task(self):
    """
    JournalBot - runs daily at 21:00 MEZ
    Generates trading reports with AI insights
    """
    try:
        logger.info("=" * 70)
        logger.info("📓 Starting JournalBot report generation")
        logger.info("=" * 70)

        # Initialize JournalBot
        from src.config.supabase import get_supabase_admin
        bot = JournalBot(
            supabase_client=get_supabase_admin(),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

        # Run report generation (async method - use asyncio.run)
        result = asyncio.run(bot.run())

        logger.info("=" * 70)
        logger.info(f"✅ JournalBot completed: {result.get('reports_generated', 0)} reports generated")
        logger.info("=" * 70)

        return result

    except Exception as e:
        logger.error(f"❌ Fatal error in JournalBot: {str(e)}")
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

    # ChartWatcher - runs every 6 hours
    'chart-analysis-6h': {
        'task': 'run_chart_analysis',
        'schedule': crontab(hour='*/6'),  # Every 6 hours (0, 6, 12, 18)
    },

    # MorningPlanner - runs daily at 08:25 MEZ
    'morning-planner-daily': {
        'task': 'run_morning_planner',
        'schedule': crontab(hour=8, minute=25),  # Daily at 08:25 UTC+1 (07:25 UTC in winter)
    },

    # JournalBot - runs daily at 21:00 MEZ
    'journal-bot-daily': {
        'task': 'run_journal_bot',
        'schedule': crontab(hour=21, minute=0),  # Daily at 21:00 UTC+1 (20:00 UTC in winter)
    },
}
