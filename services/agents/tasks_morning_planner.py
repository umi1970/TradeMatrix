"""
Celery tasks for Morning Planner Agent
Schedule: Daily at 08:25 MEZ (Berlin time)
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime
import pytz

from src.morning_planner import MorningPlanner
from config.supabase import get_supabase_admin

logger = get_task_logger(__name__)


@shared_task(name="agents.morning_planner.run_daily")
def run_morning_planner_task(symbols: list = None):
    """
    Celery task: Run Morning Planner analysis

    This task is scheduled to run daily at 08:25 MEZ (Berlin time)
    It analyzes overnight market movements and generates morning trading setups

    Args:
        symbols: Optional list of symbol names to analyze (e.g., ["DAX", "NDX"])
                 If None, all active symbols will be analyzed

    Returns:
        Dict with execution summary
    """
    berlin_tz = pytz.timezone("Europe/Berlin")
    current_time = datetime.now(berlin_tz)

    logger.info(f"Starting Morning Planner task at {current_time}")

    try:
        # Initialize agent with admin client
        planner = MorningPlanner(supabase_client=get_supabase_admin())

        # Run analysis
        result = planner.run(symbols=symbols)

        logger.info(f"Morning Planner completed successfully: {result}")
        return result

    except Exception as e:
        logger.error(f"Morning Planner task failed: {str(e)}", exc_info=True)
        raise


# Example Celery beat schedule (add this to your celeryconfig.py or Celery app config)
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'morning-planner-daily': {
        'task': 'agents.morning_planner.run_daily',
        'schedule': crontab(hour=8, minute=25, day_of_week='1-5'),  # Weekdays only
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not picked up
        }
    },
}
"""

# Manual execution example (for testing)
if __name__ == "__main__":
    # Run immediately for testing
    result = run_morning_planner_task.apply()
    print(result.get())
