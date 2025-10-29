# Market Data Integration - 5-Minute Quick Start

**Get live market data running in TradeMatrix.ai in 5 minutes!**

---

## Prerequisites

- Supabase project running
- Redis installed
- Python 3.11+
- Node.js 18+

---

## Step 1: Get API Key (1 min)

1. Go to https://twelvedata.com/ → Sign Up
2. Choose "Free Plan" (800 req/day)
3. Copy your API key

---

## Step 2: Configure (1 min)

```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix

# Backend
echo "TWELVE_DATA_API_KEY=your_key_here" >> services/api/.env

# Agents
echo "TWELVE_DATA_API_KEY=your_key_here" >> services/agents/.env
```

---

## Step 3: Apply Migration (1 min)

Open Supabase SQL Editor:

```sql
-- Copy/paste content from:
-- services/api/supabase/migrations/009_current_prices_table.sql
```

Click "Run"

---

## Step 4: Start Redis (30 sec)

```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

---

## Step 5: Start Workers (1 min)

**Terminal 1:**
```bash
cd services/agents
./start_market_data_worker.sh
```

**Terminal 2:**
```bash
cd services/agents
./start_beat_scheduler.sh
```

---

## Step 6: Test (30 sec)

**Open:** http://localhost:3000/dashboard

You should see:
- Real market prices in Market Overview cards
- Auto-updating every 30 seconds

**Open:** http://localhost:3000/dashboard/charts

You should see:
- Real candlestick charts with historical data

---

## Verify It's Working

```bash
# Check workers
celery -A src.market_data_tasks inspect active

# Check database
curl http://localhost:3000/api/market-data/current | jq

# Should see real prices for DAX, NASDAQ, etc.
```

---

## Troubleshooting

**No data?**
```bash
cd services/agents
python -c "from src.market_data_tasks import fetch_realtime_prices; print(fetch_realtime_prices.delay().get())"
```

**Redis error?**
```bash
redis-cli ping  # Should return PONG
```

**API key error?**
```bash
curl "https://api.twelvedata.com/quote?symbol=DAX&apikey=YOUR_KEY"
```

---

## What's Next?

- **Full Setup Guide**: [/docs/TWELVE_DATA_SETUP.md](./docs/TWELVE_DATA_SETUP.md)
- **Implementation Details**: [/LIVE_MARKET_DATA_IMPLEMENTATION.md](./LIVE_MARKET_DATA_IMPLEMENTATION.md)
- **Worker Guide**: [/services/agents/README_MARKET_DATA.md](./services/agents/README_MARKET_DATA.md)

---

## Quick Commands

```bash
# Start everything
docker start redis
cd services/agents && ./start_market_data_worker.sh &
cd services/agents && ./start_beat_scheduler.sh &
cd apps/web && npm run dev

# Check status
celery -A src.market_data_tasks inspect active
redis-cli ping
curl localhost:3000/api/market-data/current

# Stop everything
pkill -f celery
docker stop redis
```

---

**That's it! You now have LIVE MARKET DATA!** 🎉
