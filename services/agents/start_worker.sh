#!/bin/bash
# ================================================
# TradeMatrix.ai - Celery Worker Start Script
# ================================================
# Usage: ./start_worker.sh [mode]
# Modes:
#   worker  - Start worker only
#   beat    - Start beat scheduler only
#   both    - Start worker + beat (default)
# ================================================

set -e

MODE=${1:-both}
LOG_LEVEL=${LOG_LEVEL:-info}

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  TradeMatrix.ai - Celery Worker${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if .env exists
if [ ! -f "../.env" ] && [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "Please copy .env.example to .env and configure your API keys"
    exit 1
fi

# Check if Redis is running
echo -e "${BLUE}Checking Redis connection...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis is not running!${NC}"
    echo "Start Redis with:"
    echo "  docker run -d -p 6379:6379 --name redis redis:7-alpine"
    exit 1
fi
echo -e "${GREEN}✅ Redis is running${NC}"
echo ""

# Change to src directory
cd "$(dirname "$0")/src"

# Start Celery based on mode
case $MODE in
    worker)
        echo -e "${BLUE}Starting Celery Worker...${NC}"
        celery -A tasks worker --loglevel=$LOG_LEVEL
        ;;
    beat)
        echo -e "${BLUE}Starting Celery Beat Scheduler...${NC}"
        celery -A tasks beat --loglevel=$LOG_LEVEL
        ;;
    both)
        echo -e "${BLUE}Starting Celery Worker + Beat...${NC}"
        celery -A tasks worker --beat --loglevel=$LOG_LEVEL
        ;;
    *)
        echo "Invalid mode: $MODE"
        echo "Usage: $0 [worker|beat|both]"
        exit 1
        ;;
esac
