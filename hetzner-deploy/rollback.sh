#!/bin/bash
set -e

# TradeMatrix Rollback Script
# Usage: ./rollback.sh [commit-hash]
# This script rolls back to a previous version

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  TradeMatrix Rollback"
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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Get target commit
TARGET_COMMIT=$1

if [ -z "$TARGET_COMMIT" ]; then
    print_warning "No commit specified. Showing recent commits:"
    echo ""
    git log --oneline -10
    echo ""
    read -p "Enter commit hash to rollback to (or press Ctrl+C to cancel): " TARGET_COMMIT
fi

# Validate commit exists
if ! git rev-parse --verify "$TARGET_COMMIT" > /dev/null 2>&1; then
    print_error "Invalid commit hash: $TARGET_COMMIT"
fi

# Show current commit
CURRENT_COMMIT=$(git rev-parse HEAD)
CURRENT_SHORT=$(git rev-parse --short HEAD)
TARGET_SHORT=$(git rev-parse --short "$TARGET_COMMIT")

print_info "Current commit: $CURRENT_SHORT"
print_info "Target commit: $TARGET_SHORT"
echo ""

# Show what will change
print_info "Changes that will be reverted:"
echo ""
git log --oneline "$TARGET_COMMIT..$CURRENT_COMMIT"
echo ""

# Confirm rollback
print_warning "This will rollback your code to commit $TARGET_SHORT"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    print_info "Rollback cancelled"
    exit 0
fi

# Create emergency backup
print_info "Creating emergency backup..."
BACKUP_DIR="./backups/rollback-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup current .env
cp .env "$BACKUP_DIR/.env" 2>/dev/null || true

# Backup Redis data
if docker ps | grep -q "tradematrix_redis"; then
    docker exec tradematrix_redis redis-cli SAVE 2>/dev/null || true
    cp -r ./data/redis "$BACKUP_DIR/" 2>/dev/null || true
fi

# Backup current commit info
echo "$CURRENT_COMMIT" > "$BACKUP_DIR/previous_commit.txt"
git log -1 > "$BACKUP_DIR/commit_info.txt"

print_success "Backup created at $BACKUP_DIR"

# Stop services
print_info "Stopping services..."
docker-compose down
print_success "Services stopped"

# Rollback code
print_info "Rolling back code to $TARGET_SHORT..."
git reset --hard "$TARGET_COMMIT"
print_success "Code rolled back"

# Check if .env needs to be restored
if [ -f "$BACKUP_DIR/.env" ]; then
    print_info "Restoring .env file..."
    cp "$BACKUP_DIR/.env" .env
    print_success ".env restored"
fi

# Rebuild services
print_info "Rebuilding services..."
docker-compose build --no-cache
print_success "Services rebuilt"

# Start services
print_info "Starting services..."
docker-compose up -d
print_success "Services started"

# Wait for initialization
print_info "Waiting for services to initialize..."
sleep 15

# Verify services
print_info "Verifying services..."
SERVICE_COUNT=$(docker-compose ps | grep -c "Up" || true)
if [ "$SERVICE_COUNT" -lt 3 ]; then
    print_error "Not all services started! Check logs with: docker-compose logs"
fi
print_success "All services running"

# Check Redis
REDIS_RESPONSE=$(docker exec tradematrix_redis redis-cli ping 2>/dev/null || echo "ERROR")
if [ "$REDIS_RESPONSE" != "PONG" ]; then
    print_warning "Redis is not responding"
else
    print_success "Redis is healthy"
fi

# Show logs
print_info "Recent logs:"
echo ""
docker-compose logs celery_worker --tail=20
echo ""

# Summary
echo "=========================================="
print_success "Rollback completed!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  Rolled back from: $CURRENT_SHORT"
echo "  Current commit:   $TARGET_SHORT"
echo "  Backup location:  $BACKUP_DIR"
echo ""
echo "To restore the previous version:"
echo "  git reset --hard $CURRENT_COMMIT"
echo "  docker-compose down && docker-compose build && docker-compose up -d"
echo ""
print_warning "Monitor the system for the next 30 minutes!"
echo ""
