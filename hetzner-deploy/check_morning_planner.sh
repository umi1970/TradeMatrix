#!/bin/bash
# Diagnostic Script: Check why MorningPlanner is not running
# Run this ON HETZNER SERVER: ssh root@135.181.195.241
# Then: cd /root/TradeMatrix/hetzner-deploy && bash check_morning_planner.sh

echo "======================================================================"
echo "🔍 MorningPlanner Diagnostic Check"
echo "======================================================================"
echo ""

# Check 1: Are containers running?
echo "1️⃣ Checking Docker containers..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "tradematrix|NAMES"
echo ""

# Check 2: Is Celery Beat running?
echo "2️⃣ Checking Celery Beat status..."
if docker ps | grep -q tradematrix_celery_beat; then
    echo "✅ Celery Beat container is running"
else
    echo "❌ Celery Beat container is NOT running!"
    echo "   Try: docker-compose up -d celery_beat"
fi
echo ""

# Check 3: Is Celery Worker running?
echo "3️⃣ Checking Celery Worker status..."
if docker ps | grep -q tradematrix_celery_worker; then
    echo "✅ Celery Worker container is running"
else
    echo "❌ Celery Worker container is NOT running!"
    echo "   Try: docker-compose up -d celery_worker"
fi
echo ""

# Check 4: Check Celery Beat schedule (last 100 lines)
echo "4️⃣ Checking Celery Beat schedule logs..."
echo "   Looking for 'morning-planner-daily' schedule entry..."
docker logs tradematrix_celery_beat --tail 100 2>&1 | grep -E "morning|planner|schedule" | tail -10
echo ""

# Check 5: Check if MorningPlanner task is registered
echo "5️⃣ Checking registered tasks..."
docker exec tradematrix_celery_worker celery -A src.tasks inspect registered 2>&1 | grep -E "morning_planner|registered" | head -20
echo ""

# Check 6: Check for errors in Celery Beat
echo "6️⃣ Checking for errors in Celery Beat..."
docker logs tradematrix_celery_beat --tail 50 2>&1 | grep -iE "error|exception|failed|traceback" | tail -10
if [ $? -eq 0 ]; then
    echo "⚠️  Errors found (see above)"
else
    echo "✅ No errors in last 50 lines"
fi
echo ""

# Check 7: Check for errors in Celery Worker
echo "7️⃣ Checking for errors in Celery Worker..."
docker logs tradematrix_celery_worker --tail 50 2>&1 | grep -iE "error|exception|failed|traceback" | tail -10
if [ $? -eq 0 ]; then
    echo "⚠️  Errors found (see above)"
else
    echo "✅ No errors in last 50 lines"
fi
echo ""

# Check 8: Verify timezone setting
echo "8️⃣ Checking Celery timezone config..."
docker exec tradematrix_celery_beat python3 -c "from src.tasks import celery; print(f'Timezone: {celery.conf.timezone}')" 2>&1
docker exec tradematrix_celery_beat python3 -c "from src.tasks import celery; print(f'Enable UTC: {celery.conf.enable_utc}')" 2>&1
echo ""

# Check 9: Test MorningPlanner manually
echo "9️⃣ Testing MorningPlanner manually (this may take 30-60 seconds)..."
echo "   Running: python3 -c \"from src.tasks import run_morning_planner_task; print(run_morning_planner_task())\""
docker exec tradematrix_celery_worker timeout 60 python3 -c "
from src.tasks import run_morning_planner_task
import asyncio
result = run_morning_planner_task()
print(f'Result: {result}')
" 2>&1 | tail -20
echo ""

# Check 10: Check beat schedule file
echo "🔟 Checking Celery Beat schedule config..."
docker exec tradematrix_celery_beat python3 -c "
from src.tasks import celery
for name, config in celery.conf.beat_schedule.items():
    print(f'{name}:')
    print(f'  Task: {config[\"task\"]}')
    print(f'  Schedule: {config[\"schedule\"]}')
    print()
" 2>&1 | grep -A 3 "morning"
echo ""

echo "======================================================================"
echo "✅ Diagnostic Check Complete"
echo "======================================================================"
echo ""
echo "📋 Common Issues & Fixes:"
echo ""
echo "Issue 1: Containers not running"
echo "  Fix: cd /root/TradeMatrix/hetzner-deploy && docker-compose up -d"
echo ""
echo "Issue 2: Task not registered"
echo "  Fix: cd /root/TradeMatrix/hetzner-deploy && docker-compose restart celery_worker celery_beat"
echo ""
echo "Issue 3: Import errors"
echo "  Fix: Check requirements.txt dependencies"
echo "       docker-compose down && docker-compose up -d --build"
echo ""
echo "Issue 4: Timezone still UTC"
echo "  Fix: cd /root/TradeMatrix && git pull && docker-compose up -d --build"
echo ""
echo "📖 Full logs:"
echo "  Celery Beat:   docker logs tradematrix_celery_beat -f"
echo "  Celery Worker: docker logs tradematrix_celery_worker -f"
echo ""
