#!/bin/bash
# Start Celery worker for market data tasks
#
# Usage: ./start_market_data_worker.sh

set -e

echo "==========================================="
echo "  TradeMatrix.ai - Market Data Worker"
echo "==========================================="
echo ""

# Change to agents directory
cd "$(dirname "$0")"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file with required variables:"
    echo "  - TWELVE_DATA_API_KEY"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_SERVICE_KEY"
    echo "  - CELERY_BROKER_URL"
    echo ""
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo "Starting Celery worker for market data tasks..."
echo ""
echo "Configuration:"
echo "  - Worker: market_data_worker"
echo "  - Concurrency: 4"
echo "  - Log level: info"
echo "  - Queues: default, market_data"
echo ""

# Start Celery worker
celery -A src.market_data_tasks worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=50 \
    --hostname=market_data_worker@%h \
    --queues=default,market_data \
    --logfile=logs/market_data_worker.log \
    --pidfile=logs/market_data_worker.pid

echo ""
echo "Worker stopped."
