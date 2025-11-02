#!/bin/bash

# TradeMatrix Health Check Script
# Usage: ./health_check.sh
# This script checks the health of all TradeMatrix services

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  TradeMatrix Health Check"
echo "=========================================="
echo ""

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check if Docker is running
print_header "1. Docker Status"
if ! docker ps &> /dev/null; then
    print_error "Docker is not running!"
    exit 1
fi
print_success "Docker is running"

# Check Docker Compose services
print_header "2. Docker Services Status"
echo ""
docker-compose ps
echo ""

# Count running services
SERVICE_COUNT=$(docker-compose ps | grep -c "Up" || true)
if [ "$SERVICE_COUNT" -lt 3 ]; then
    print_warning "Only $SERVICE_COUNT/3 services are running!"
else
    print_success "All 3 services are running"
fi

# Check Redis
print_header "3. Redis Health"
REDIS_RESPONSE=$(docker exec tradematrix_redis redis-cli ping 2>/dev/null || echo "ERROR")
if [ "$REDIS_RESPONSE" = "PONG" ]; then
    print_success "Redis is healthy"

    # Get Redis info
    REDIS_MEMORY=$(docker exec tradematrix_redis redis-cli INFO memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
    REDIS_KEYS=$(docker exec tradematrix_redis redis-cli DBSIZE | cut -d: -f2 | tr -d '\r')
    echo "  Memory Used: $REDIS_MEMORY"
    echo "  Total Keys: $REDIS_KEYS"
else
    print_error "Redis is not responding!"
fi

# Check Celery Worker
print_header "4. Celery Worker Status"
WORKER_RUNNING=$(docker-compose ps celery_worker | grep -c "Up" || echo "0")
if [ "$WORKER_RUNNING" -eq 1 ]; then
    print_success "Celery Worker is running"

    # Check recent logs for errors
    ERROR_COUNT=$(docker-compose logs celery_worker --tail=100 | grep -ic "ERROR" || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        print_warning "Found $ERROR_COUNT errors in recent logs"
    else
        print_success "No errors in recent logs"
    fi
else
    print_error "Celery Worker is not running!"
fi

# Check Celery Beat
print_header "5. Celery Beat Status"
BEAT_RUNNING=$(docker-compose ps celery_beat | grep -c "Up" || echo "0")
if [ "$BEAT_RUNNING" -eq 1 ]; then
    print_success "Celery Beat is running"

    # Check if tasks are being scheduled
    LAST_TASK=$(docker-compose logs celery_beat --tail=50 | grep "Scheduler: Sending due task" | tail -1)
    if [ -n "$LAST_TASK" ]; then
        echo "  Last scheduled task: $(echo $LAST_TASK | awk '{print $NF}')"
    fi
else
    print_error "Celery Beat is not running!"
fi

# Check API Usage
print_header "6. chart-img.com API Usage"
TODAY=$(date +%Y-%m-%d)
USAGE=$(docker exec tradematrix_redis redis-cli GET "chart_img:requests:daily:$TODAY" 2>/dev/null || echo "0")
if [ -z "$USAGE" ] || [ "$USAGE" = "(nil)" ]; then
    USAGE=0
fi

echo "  Date: $TODAY"
echo "  Requests: $USAGE / 1,000"

if [ "$USAGE" -lt 800 ]; then
    print_success "API usage is within limits"
elif [ "$USAGE" -lt 1000 ]; then
    print_warning "API usage is high (${USAGE}/1,000)"
else
    print_error "API limit exceeded! Using fallback charts."
fi

# Check disk space
print_header "7. System Resources"
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
echo "  Disk Usage: ${DISK_USAGE}%"
if [ "$DISK_USAGE" -gt 80 ]; then
    print_warning "Disk usage is high (${DISK_USAGE}%)"
else
    print_success "Disk usage is healthy (${DISK_USAGE}%)"
fi

# Check memory
MEMORY_TOTAL=$(free -m | awk '/^Mem:/{print $2}')
MEMORY_USED=$(free -m | awk '/^Mem:/{print $3}')
MEMORY_PERCENT=$(awk "BEGIN {printf \"%.0f\", ($MEMORY_USED/$MEMORY_TOTAL)*100}")
echo "  Memory Usage: ${MEMORY_USED}MB / ${MEMORY_TOTAL}MB (${MEMORY_PERCENT}%)"
if [ "$MEMORY_PERCENT" -gt 80 ]; then
    print_warning "Memory usage is high (${MEMORY_PERCENT}%)"
else
    print_success "Memory usage is healthy (${MEMORY_PERCENT}%)"
fi

# Recent activity
print_header "8. Recent Activity"
echo ""
echo "Last 5 log entries from Celery Worker:"
docker-compose logs celery_worker --tail=5
echo ""

# Summary
print_header "9. Summary"
echo ""

ISSUES=0

if [ "$SERVICE_COUNT" -lt 3 ]; then
    ((ISSUES++))
fi

if [ "$REDIS_RESPONSE" != "PONG" ]; then
    ((ISSUES++))
fi

if [ "$ERROR_COUNT" -gt 0 ]; then
    ((ISSUES++))
fi

if [ "$DISK_USAGE" -gt 80 ]; then
    ((ISSUES++))
fi

if [ "$MEMORY_PERCENT" -gt 80 ]; then
    ((ISSUES++))
fi

if [ "$ISSUES" -eq 0 ]; then
    print_success "All systems healthy! No issues detected."
else
    print_warning "Found $ISSUES potential issue(s). Review the details above."
fi

echo ""
echo "=========================================="
echo "  Health check completed at $(date)"
echo "=========================================="
echo ""
echo "For detailed logs, run:"
echo "  docker-compose logs -f celery_worker"
echo "  docker-compose logs -f celery_beat"
echo ""
