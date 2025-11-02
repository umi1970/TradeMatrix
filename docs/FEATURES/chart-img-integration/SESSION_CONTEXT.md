# Session Context - chart-img.com Integration

**Quick Start Guide für neue Claude Sessions**

---

## 🎯 Was ist dieses Feature?

Integration der **chart-img.com API** zur dynamischen Generierung von TradingView-Charts für alle AI Agents (ChartWatcher, MorningPlanner, JournalBot, TradeMonitor).

---

## ⚡ Quick Status Check

Run these commands to check current status:

### 1. Database Status

```sql
-- Connect to Supabase SQL Editor

-- Check if chart_config column exists
SELECT column_name FROM information_schema.columns
WHERE table_name = 'market_symbols' AND column_name = 'chart_config';
-- Expected: 1 row if migration done

-- Check if chart_snapshots table exists
SELECT table_name FROM information_schema.tables
WHERE table_name = 'chart_snapshots';
-- Expected: 1 row if migration done

-- Count existing snapshots
SELECT COUNT(*) FROM chart_snapshots;
-- Expected: 0 if not deployed, >0 if agents running
```

### 2. Backend Status

```bash
# SSH into Hetzner server
ssh root@135.191.195.241

# Check if ChartService exists
ls -la /root/tradematrix-agents/src/chart_service.py
# Expected: File exists if deployed

# Check if CHART_IMG_API_KEY is set
grep CHART_IMG_API_KEY /root/tradematrix-agents/.env
# Expected: CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l

# Check Redis for API usage
docker-compose exec redis redis-cli GET chart_api:daily:$(date +%Y-%m-%d)
# Expected: Number between 0 and 1000 (or null if no requests today)
```

### 3. Frontend Status

```bash
# Local machine
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/apps/web

# Check if chart components exist
ls -la src/components/charts/
# Expected: 7 files (ChartConfigModal, TimeframeSelector, etc.)
```

---

## 📊 Current Implementation Status

| Phase | Status | Completion |
|-------|--------|------------|
| **Phase 1: Database Setup** | ⏳ Pending | 0% |
| **Phase 2: Backend API** | ⏳ Pending | 0% |
| **Phase 3: Frontend UI** | ⏳ Pending | 0% |
| **Phase 4: Agent Integration** | ⏳ Pending | 0% |
| **Phase 5: Testing** | ⏳ Pending | 0% |
| **Phase 6: Deployment** | ⏳ Pending | 0% |

**Legend**:
- ✅ Complete
- 🚧 In Progress
- ⏳ Pending
- ❌ Blocked

---

## 🗂️ Important Files

### Documentation (Read These First!)

```
docs/FEATURES/chart-img-integration/
├── README.md                       ← START HERE! Feature overview
├── 01_ARCHITECTURE.md              ← System design & components
├── 02_DATABASE_SCHEMA.md           ← Tables, migrations, RLS
├── 03_API_ENDPOINTS.md             ← FastAPI routes (future)
├── 04_FRONTEND_COMPONENTS.md       ← React components
├── 05_AGENT_INTEGRATION.md         ← ChartWatcher, MorningPlanner, JournalBot
├── 06_DEPLOYMENT.md                ← Hetzner deployment guide
├── 07_TESTING.md                   ← Test checklists
├── 08_TROUBLESHOOTING.md           ← Common issues & solutions
├── IMPLEMENTATION_CHECKLIST.md     ← Master checklist (6 phases)
└── SESSION_CONTEXT.md              ← YOU ARE HERE!
```

### Code Files (To Be Created)

```
Backend (Hetzner Server):
  hetzner-deploy/src/chart_service.py          ← Core service (300+ lines)
  hetzner-deploy/src/chart_watcher.py          ← Fix lines 554-560
  hetzner-deploy/src/morning_planner.py        ← Add chart integration
  hetzner-deploy/src/journal_bot.py            ← Add chart integration

Frontend (Local):
  apps/web/src/components/charts/
    ├── ChartConfigModal.tsx                   ← Main config UI
    ├── TimeframeSelector.tsx                  ← Multi-select timeframes
    ├── IndicatorSelector.tsx                  ← Multi-select indicators
    ├── ChartPreview.tsx                       ← Live preview
    ├── ChartSnapshotGallery.tsx               ← Grid of snapshots
    ├── ChartSnapshotCard.tsx                  ← Single snapshot card
    └── ChartConfigButton.tsx                  ← Trigger button

Database (Supabase):
  services/api/supabase/migrations/
    ├── 016_chart_config.sql                   ← Extend market_symbols
    ├── 017_chart_snapshots.sql                ← New table
    └── 018_chart_snapshots_cleanup.sql        ← Cleanup function
```

---

## 🚀 Next Steps (What to Do Now)

### If Phase 1 Not Started (Database Setup)

1. **Read Documentation**:
   - [ ] Read [README.md](./README.md) (5 min)
   - [ ] Read [02_DATABASE_SCHEMA.md](./02_DATABASE_SCHEMA.md) (10 min)

2. **Create Migration Files**:
   - [ ] Copy SQL from 02_DATABASE_SCHEMA.md
   - [ ] Create `016_chart_config.sql`
   - [ ] Create `017_chart_snapshots.sql`
   - [ ] Create `018_chart_snapshots_cleanup.sql`

3. **Run Migrations**:
   - [ ] Login to Supabase Dashboard
   - [ ] Open SQL Editor
   - [ ] Run migrations in order (016, 017, 018)
   - [ ] Verify tables exist

4. **Verify**:
   ```sql
   SELECT chart_config FROM market_symbols LIMIT 1;
   SELECT COUNT(*) FROM chart_snapshots;
   ```

### If Phase 1 Complete (Database Setup Done)

1. **Read Documentation**:
   - [ ] Read [05_AGENT_INTEGRATION.md](./05_AGENT_INTEGRATION.md) (15 min)

2. **Create ChartService**:
   - [ ] Copy full ChartService code from 05_AGENT_INTEGRATION.md
   - [ ] Create file: `hetzner-deploy/src/chart_service.py`
   - [ ] Add environment variables to `.env`
   - [ ] Update `requirements.txt` (add httpx)

3. **Test Locally**:
   ```bash
   cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/agents
   python -c "from src.chart_service import ChartService; import asyncio; print(asyncio.run(ChartService().generate_chart_url('^GDAXI', 'M15', agent_name='Test')))"
   ```

4. **Fix ChartWatcher**:
   - [ ] Open `hetzner-deploy/src/chart_watcher.py`
   - [ ] Fix lines 554-560 (see 05_AGENT_INTEGRATION.md)
   - [ ] Test manually

### If Phase 2 Complete (Backend API Done)

1. **Read Documentation**:
   - [ ] Read [04_FRONTEND_COMPONENTS.md](./04_FRONTEND_COMPONENTS.md) (15 min)

2. **Create React Components**:
   - [ ] Create 7 components from 04_FRONTEND_COMPONENTS.md
   - [ ] Place in `apps/web/src/components/charts/`

3. **Integrate with Dashboard**:
   - [ ] Update MarketSymbolsCard (add ChartConfigButton)
   - [ ] Add Chart Snapshots tab to Dashboard

4. **Test Locally**:
   ```bash
   cd apps/web
   npm run dev
   # Open http://localhost:3000
   # Test chart config modal
   ```

### If Phase 3 Complete (Frontend UI Done)

1. **Read Documentation**:
   - [ ] Read [06_DEPLOYMENT.md](./06_DEPLOYMENT.md) (10 min)
   - [ ] Read [07_TESTING.md](./07_TESTING.md) (10 min)

2. **Run Tests**:
   ```bash
   # Unit tests
   cd services/agents
   pytest tests/test_chart_service.py -v

   # Integration tests
   pytest tests/test_agent_integration.py -v -m integration

   # Manual tests (see 07_TESTING.md)
   ```

3. **Deploy to Hetzner**:
   - [ ] Follow deployment steps in 06_DEPLOYMENT.md
   - [ ] SSH into server
   - [ ] Copy files, update .env, rebuild Docker
   - [ ] Verify deployment

### If Deployment Complete

1. **Monitor Production**:
   - [ ] Check logs: `docker-compose logs -f celery-worker`
   - [ ] Check API usage: `docker-compose exec redis redis-cli GET chart_api:daily:$(date +%Y-%m-%d)`
   - [ ] Check snapshots: `SELECT COUNT(*) FROM chart_snapshots;`

2. **Test End-to-End**:
   - [ ] Configure chart for DAX (frontend)
   - [ ] Trigger ChartWatcher (backend)
   - [ ] Verify snapshot in database
   - [ ] View snapshot in gallery (frontend)

3. **Troubleshooting**:
   - [ ] If errors, check [08_TROUBLESHOOTING.md](./08_TROUBLESHOOTING.md)

---

## 🔑 Key Information

### API Details

- **Provider**: chart-img.com
- **Plan**: MEGA ($10/month)
- **API Key**: `3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l`
- **Daily Limit**: 1,000 requests
- **Per-Second Limit**: 15 requests
- **Max Resolution**: 1920x1600
- **Retention**: 60 days

### Symbol Mapping

| Yahoo Symbol | TradingView Symbol |
|--------------|-------------------|
| ^GDAXI | XETR:DAX |
| ^NDX | NASDAQ:NDX |
| ^DJI | DJCFD:DJI |
| EURUSD=X | OANDA:EURUSD |
| EURGBP=X | OANDA:EURGBP |

### Database Tables

1. **market_symbols** (extended):
   - New column: `chart_config` (JSONB)
   - Stores: tv_symbol, timeframes, indicators, theme, dimensions

2. **chart_snapshots** (new):
   - Stores: chart_url, timeframe, created_by_agent, metadata
   - Auto-expires after 60 days

### Agent Integration

- **ChartWatcher**: Analyze symbols across multiple timeframes (M15, H1, D1)
- **MorningPlanner**: Generate daily setup charts (H1, M15, D1 per symbol)
- **JournalBot**: Add chart snapshots to trade journal entries
- **TradeMonitor**: Live monitoring charts (optional)

---

## 🛠️ Common Commands

### Database

```sql
-- Check chart_config for a symbol
SELECT symbol, chart_config FROM market_symbols WHERE symbol = '^GDAXI';

-- Count chart snapshots by agent
SELECT created_by_agent, COUNT(*) FROM chart_snapshots GROUP BY created_by_agent;

-- Get latest charts
SELECT cs.id, ms.symbol, cs.timeframe, cs.created_at
FROM chart_snapshots cs
JOIN market_symbols ms ON cs.symbol_id = ms.id
ORDER BY cs.created_at DESC LIMIT 10;

-- Cleanup expired snapshots
SELECT cleanup_expired_chart_snapshots();
```

### Backend (Hetzner Server)

```bash
# SSH into server
ssh root@135.191.195.241
cd /root/tradematrix-agents

# Check logs
docker-compose logs -f celery-worker | grep -i chart

# Trigger ChartWatcher manually
docker-compose exec celery-worker celery -A src.tasks call chart_watcher.analyze_all_symbols

# Check Redis API usage
docker-compose exec redis redis-cli GET chart_api:daily:$(date +%Y-%m-%d)

# Restart services
docker-compose down && docker-compose up -d
```

### Frontend (Local)

```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/apps/web

# Start dev server
npm run dev

# Build for production
npm run build

# Check for errors
npm run lint
```

---

## ⚠️ Known Issues

### Issue 1: ChartWatcher Lines 554-560 Broken

**Problem**: `chart_service.generate_url()` method doesn't exist

**Fix**: Replace with `await chart_service.generate_chart_url()`

**File**: `hetzner-deploy/src/chart_watcher.py`

### Issue 2: Rate Limit Exceeded

**Problem**: Daily limit of 1,000 requests reached

**Solutions**:
- Use cached charts (1 hour TTL)
- Reduce generation frequency
- Wait until midnight UTC for reset

### Issue 3: Symbol Mapping Wrong

**Problem**: TradingView symbol not found (404)

**Fix**: Update SYMBOL_MAPPING in `chart_service.py`

---

## 📞 Need Help?

### Stuck on Implementation?

1. **Check Documentation**: Read relevant .md file in this folder
2. **Check Troubleshooting**: [08_TROUBLESHOOTING.md](./08_TROUBLESHOOTING.md)
3. **Check Checklist**: [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)
4. **Ask User**: If still unclear, ask for clarification

### Error Occurred?

1. **Check Logs**: `docker-compose logs -f celery-worker`
2. **Check Redis**: `docker-compose exec redis redis-cli PING`
3. **Check Database**: Run status queries (see above)
4. **Check Troubleshooting**: [08_TROUBLESHOOTING.md](./08_TROUBLESHOOTING.md)

---

## 🎯 Session Goals Template

Use this when starting a new session:

```markdown
## Session Goal: [Phase X - Description]

**Current Status**: [From status table above]

**Today's Tasks**:
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

**Files to Modify**:
- `path/to/file1.py`
- `path/to/file2.tsx`

**Testing**:
- [ ] Unit test: [description]
- [ ] Manual test: [description]

**Completion Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2
```

---

## 🔄 Git Workflow

```bash
# Always work in feature branch
git checkout -b feature/chart-img-integration

# Commit frequently
git add .
git commit -m "feat: Add ChartService implementation"

# Push to GitHub
git push origin feature/chart-img-integration

# When done, create PR
gh pr create --title "feat: chart-img.com integration" --body "See IMPLEMENTATION_CHECKLIST.md"
```

---

## ✅ Daily Standup Questions

Answer these at the start of each session:

1. **What was completed last session?**
   - Check git log: `git log --oneline -5`

2. **What's the goal for this session?**
   - Refer to IMPLEMENTATION_CHECKLIST.md

3. **Any blockers?**
   - Database migration issues?
   - API key problems?
   - Docker build failures?

4. **Current phase progress?**
   - Update status table above

---

## 📈 Progress Tracking

Update this table after each session:

| Date | Session Duration | Phase | Tasks Completed | Next Steps |
|------|-----------------|-------|-----------------|------------|
| 2025-11-02 | 2h | Phase 1 | Database migrations | Test ChartService |
| ... | ... | ... | ... | ... |

---

## 🎉 Feature Complete Checklist

Feature is done when:

- [ ] All 6 phases complete (IMPLEMENTATION_CHECKLIST.md)
- [ ] All tests pass (unit, integration, E2E)
- [ ] Deployed to production (Hetzner + Netlify)
- [ ] 24h monitoring complete (no errors)
- [ ] Documentation updated (README.md)
- [ ] User can configure charts via frontend
- [ ] Agents generate charts automatically
- [ ] Chart snapshots visible in gallery
- [ ] Rate limits respected (< 1000/day)
- [ ] Cache working (> 70% hit rate)

---

**Last Updated**: 2025-11-02
**Current Phase**: Phase 1 - Database Setup
**Next Milestone**: Database migrations complete

---

**Remember**: Read README.md first, then follow IMPLEMENTATION_CHECKLIST.md phase by phase. Good luck! 🚀
