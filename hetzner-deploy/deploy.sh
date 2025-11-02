#!/bin/bash
set -e

# TradeMatrix Hetzner Deployment Script
# Usage: ./deploy.sh
# This script automates the deployment process for TradeMatrix on Hetzner CX11

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  TradeMatrix Hetzner Deployment"
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
    exit 1
}

print_info() {
    echo -e "ℹ️  $1"
}

# Step 1: Check environment file
print_info "Checking for .env file..."
if [ ! -f .env ]; then
    print_error ".env file not found! Please create one from .env.example"
fi
print_success ".env file found"

# Step 2: Verify required environment variables
print_info "Verifying environment variables..."
required_vars=(
    "SUPABASE_URL"
    "SUPABASE_SERVICE_KEY"
    "REDIS_URL"
    "CHART_IMG_API_KEY"
    "OPENAI_API_KEY"
    "FINNHUB_API_KEY"
)

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env; then
        print_error "Missing required variable: ${var}"
    fi
done
print_success "All required variables present"

# Step 3: Create backup
print_info "Creating backup..."
BACKUP_DIR="./backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup .env
cp .env "$BACKUP_DIR/.env" 2>/dev/null || true

# Backup Redis data (if exists)
if [ -d "./data/redis" ]; then
    docker exec tradematrix-agents-redis-1 redis-cli SAVE 2>/dev/null || true
    cp -r ./data/redis "$BACKUP_DIR/" 2>/dev/null || true
fi

print_success "Backup created at $BACKUP_DIR"

# Step 4: Pull latest code
print_info "Pulling latest code from main branch..."
git fetch origin
CURRENT_COMMIT=$(git rev-parse HEAD)
git pull origin main

NEW_COMMIT=$(git rev-parse HEAD)
if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    print_warning "No new changes to deploy"
else
    print_success "Code updated from $CURRENT_COMMIT to $NEW_COMMIT"
fi

# Step 5: Stop services
print_info "Stopping services..."
docker-compose down
print_success "Services stopped"

# Step 6: Build services
print_info "Building services (this may take 2-3 minutes)..."
docker-compose build --no-cache
print_success "Services built successfully"

# Step 7: Start services
print_info "Starting services..."
docker-compose up -d
print_success "Services started"

# Step 8: Wait for initialization
print_info "Waiting for services to initialize (15 seconds)..."
sleep 15

# Step 9: Verify services are running
print_info "Verifying services..."
SERVICE_COUNT=$(docker-compose ps | grep -c "Up" || true)
if [ "$SERVICE_COUNT" -lt 3 ]; then
    print_error "Not all services are running! Check logs with: docker-compose logs"
fi
print_success "All services are running"

# Step 10: Check Redis connection
print_info "Testing Redis connection..."
REDIS_RESPONSE=$(docker exec tradematrix-agents-redis-1 redis-cli ping 2>/dev/null || echo "ERROR")
if [ "$REDIS_RESPONSE" != "PONG" ]; then
    print_error "Redis is not responding!"
fi
print_success "Redis is healthy"

# Step 11: Display recent logs
print_info "Displaying recent logs..."
echo ""
echo "=== Celery Worker Logs ==="
docker-compose logs celery_worker --tail=20
echo ""
echo "=== Celery Beat Logs ==="
docker-compose logs celery_beat --tail=10
echo ""

# Step 12: Final status
print_info "Checking service status..."
docker-compose ps
echo ""

# Summary
echo "=========================================="
print_success "Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Monitor logs: docker-compose logs -f celery_worker"
echo "  2. Run health check: ./health_check.sh"
echo "  3. Verify chart generation in Supabase dashboard"
echo ""
echo "Backup location: $BACKUP_DIR"
echo "Git commit: $NEW_COMMIT"
echo ""
