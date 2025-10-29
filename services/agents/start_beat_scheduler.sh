#!/bin/bash
# Start Celery Beat scheduler for periodic market data tasks
#
# Usage: ./start_beat_scheduler.sh

set -e

echo "==========================================="
echo "  TradeMatrix.ai - Beat Scheduler"
echo "==========================================="
echo ""

# Change to agents directory
cd "$(dirname "$0")"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "Starting Celery Beat scheduler..."
echo ""
echo "Scheduled tasks:"
echo "  - Fetch realtime prices: Every 1 minute"
echo "  - Daily data refresh: 2:00 AM UTC"
echo "  - API usage check: Every hour"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Celery beat
celery -A src.market_data_tasks beat \
    --loglevel=info \
    --logfile=logs/beat_scheduler.log \
    --pidfile=logs/beat_scheduler.pid \
    --schedule=logs/celerybeat-schedule.db

echo ""
echo "Beat scheduler stopped."
