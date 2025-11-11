#!/bin/bash
# Quick Deployment Script for Hetzner Server
# Run this ON THE HETZNER SERVER after executing database migration

set -e  # Exit on error

echo "======================================================================"
echo "🚀 TradeMatrix - Twelvedata Integration Deployment"
echo "======================================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "Please run this script from /root/TradeMatrix/hetzner-deploy"
    exit 1
fi

echo "📂 Current directory: $(pwd)"
echo ""

# Step 1: Pull latest code
echo "Step 1/5: Pulling latest code from git..."
cd /root/TradeMatrix
git pull origin main
echo "✅ Code updated"
echo ""

# Step 2: Fix environment variable
echo "Step 2/5: Fixing environment variable name..."
cd /root/TradeMatrix/hetzner-deploy
sed -i 's/TWELVE_DATA_API_KEY=/TWELVEDATA_API_KEY=/' .env
if grep -q "TWELVEDATA_API_KEY" .env; then
    echo "✅ TWELVEDATA_API_KEY configured"
else
    echo "❌ Failed to update .env"
    exit 1
fi
echo ""

# Step 3: Test symbols (optional)
echo "Step 3/5: Testing Twelvedata symbols..."
if python3 test_twelvedata_symbols.py; then
    echo "✅ All symbols working"
else
    echo "⚠️  Some symbols failed - check API key"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Step 4: Restart Docker services
echo "Step 4/5: Restarting Docker services..."
docker-compose down
docker-compose up -d
echo "✅ Services restarted"
echo ""

# Step 5: Check service status
echo "Step 5/5: Checking service status..."
sleep 3
docker-compose ps
echo ""

echo "======================================================================"
echo "✅ Deployment Complete!"
echo "======================================================================"
echo ""
echo "📋 Next steps:"
echo "1. Check Celery logs: docker-compose logs -f celery-worker --tail=50"
echo "2. Verify dashboard: https://tradematrix.netlify.app"
echo "3. Monitor for 2-3 minutes to ensure price updates working"
echo ""
echo "🎯 Expected behavior:"
echo "  - Celery should fetch prices every 60 seconds"
echo "  - All 5 symbols should update successfully"
echo "  - Dashboard should show current prices (not Friday EOD)"
echo ""
