# Implementation Checklist

## Master Checklist - chart-img.com Integration

**Total Estimated Time**: 12 hours
**Complexity**: Medium
**Priority**: High

---

## Phase 1: Database Setup (1 hour)

### 1.1 Create Migrations

- [ ] Create `016_chart_config.sql` migration file
  - [ ] Add `chart_config` JSONB column to `market_symbols`
  - [ ] Add GIN index on `chart_config`
  - [ ] Set default config for existing symbols
  - Location: `services/api/supabase/migrations/016_chart_config.sql`

- [ ] Create `017_chart_snapshots.sql` migration file
  - [ ] Create `chart_snapshots` table with all columns
  - [ ] Add table and column comments
  - [ ] Create 6 indexes (symbol_id, agent, created_at, expires_at, metadata)
  - [ ] Enable RLS
  - [ ] Create 4 RLS policies (SELECT, INSERT, DELETE, service role)
  - Location: `services/api/supabase/migrations/017_chart_snapshots.sql`

- [ ] Create `018_chart_snapshots_cleanup.sql` migration file
  - [ ] Create `cleanup_expired_chart_snapshots()` function
  - [ ] Add NOTICE for deleted count
  - Location: `services/api/supabase/migrations/018_chart_snapshots_cleanup.sql`

### 1.2 Run Migrations

- [ ] Open Supabase SQL Editor
- [ ] Run migration 016 (chart_config)
- [ ] Verify column exists: `SELECT chart_config FROM market_symbols LIMIT 1;`
- [ ] Run migration 017 (chart_snapshots)
- [ ] Verify table exists: `SELECT * FROM chart_snapshots LIMIT 1;`
- [ ] Run migration 018 (cleanup function)
- [ ] Verify function exists: `SELECT cleanup_expired_chart_snapshots();`

### 1.3 Test Database

- [ ] Insert test chart_config:
  ```sql
  UPDATE market_symbols SET chart_config = '{"tv_symbol":"XETR:DAX"}'::JSONB WHERE symbol='^GDAXI';
  ```
- [ ] Query with JSONB operator:
  ```sql
  SELECT symbol FROM market_symbols WHERE chart_config->>'tv_symbol'='XETR:DAX';
  ```
- [ ] Test RLS policies (as authenticated user)
- [ ] Verify indexes created: `\di chart_snapshots*`

**Completion Criteria**: All migrations run successfully, tables/columns exist, RLS policies active.

---

## Phase 2: Backend API (2 hours)

### 2.1 Create ChartService

- [ ] Create file: `services/agents/src/chart_service.py`
- [ ] Implement `ChartService` class:
  - [ ] `__init__()` - Initialize Supabase, Redis, API key
  - [ ] `SYMBOL_MAPPING` - Dictionary with 8+ symbols
  - [ ] `map_symbol()` - Yahoo → TradingView symbol mapping
  - [ ] `get_chart_config()` - Fetch from database
  - [ ] `build_chart_url()` - Construct chart-img.com URL
  - [ ] `get_cache_key()` - Generate Redis cache key
  - [ ] `generate_chart_url()` - Main method (with caching & rate limits)
  - [ ] `save_snapshot()` - Insert into chart_snapshots table
  - [ ] `check_rate_limits()` - Daily (1000) & per-second (15) limits
  - [ ] `increment_request_count()` - Increment Redis counter
  - [ ] `get_daily_request_count()` - Get from Redis
  - [ ] `get_remaining_requests()` - Calculate remaining

### 2.2 Add Environment Variables

- [ ] Add to `hetzner-deploy/.env`:
  ```bash
  CHART_IMG_API_KEY=3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l
  CHART_API_DAILY_LIMIT=1000
  CHART_API_PER_SECOND_LIMIT=15
  CHART_CACHE_TTL=3600
  ```
- [ ] Update `docker-compose.yml` to pass env vars to containers
- [ ] Verify `.env` is in `.gitignore`

### 2.3 Update Dependencies

- [ ] Add to `requirements.txt`:
  ```
  httpx==0.25.0
  ```
- [ ] Rebuild Docker image: `docker-compose build --no-cache`

### 2.4 Test ChartService

- [ ] Unit test: `test_map_symbol()`
- [ ] Unit test: `test_get_chart_config()`
- [ ] Unit test: `test_build_chart_url()`
- [ ] Unit test: `test_check_rate_limits()`
- [ ] Integration test: Generate chart for ^GDAXI
- [ ] Verify chart URL is accessible (HTTP GET)
- [ ] Verify snapshot saved to database

**Completion Criteria**: ChartService generates valid URLs, saves snapshots, enforces rate limits.

---

## Phase 3: Frontend UI (3 hours)

### 3.1 Create Chart Components

- [ ] Create `apps/web/src/components/charts/` directory
- [ ] **ChartConfigModal.tsx**:
  - [ ] Props: symbol, isOpen, onClose, onSave
  - [ ] 3 tabs: Basic, Indicators, Preview
  - [ ] Basic tab: TradingView symbol, chart type, theme, dimensions, switches
  - [ ] Indicators tab: IndicatorSelector component
  - [ ] Preview tab: ChartPreview component
  - [ ] Save to Supabase on submit
  - [ ] Toast notification on success/error

- [ ] **TimeframeSelector.tsx**:
  - [ ] Multi-select checkboxes for 8 timeframes
  - [ ] Validation: At least 1 selected

- [ ] **IndicatorSelector.tsx**:
  - [ ] Checkboxes for 8 indicators
  - [ ] Multiple selection allowed

- [ ] **ChartPreview.tsx**:
  - [ ] Build chart URL from config
  - [ ] Show image preview
  - [ ] Alert: "Using first timeframe for preview"
  - [ ] Show generated URL (for debugging)

- [ ] **ChartSnapshotGallery.tsx**:
  - [ ] Fetch snapshots from Supabase
  - [ ] Filters: Agent, Timeframe
  - [ ] Grid layout (3 columns on desktop)
  - [ ] Refresh button

- [ ] **ChartSnapshotCard.tsx**:
  - [ ] Display chart image, symbol, timeframe
  - [ ] Badge for timeframe
  - [ ] External link button
  - [ ] Delete button with confirmation

- [ ] **ChartConfigButton.tsx**:
  - [ ] Settings icon + "Chart Config" text
  - [ ] Opens ChartConfigModal on click

### 3.2 Integrate with Existing Components

- [ ] Update `MarketSymbolsCard.tsx`:
  - [ ] Import ChartConfigButton
  - [ ] Add button next to each symbol
  - [ ] Pass symbol data to button

- [ ] Update Dashboard page (`apps/web/src/app/(dashboard)/dashboard/page.tsx`):
  - [ ] Add "Chart Snapshots" tab
  - [ ] Render ChartSnapshotGallery in tab content

### 3.3 Styling & Responsiveness

- [ ] Modal: Full-screen on mobile, centered on desktop
- [ ] Grid: 1 column mobile, 2 tablet, 3 desktop
- [ ] Buttons: Consistent sizing with existing UI
- [ ] Dark mode: Verify all components adapt

### 3.4 Test Frontend

- [ ] Click "Chart Config" → Modal opens
- [ ] Select timeframes → Preview updates
- [ ] Select indicators → Preview updates
- [ ] Save config → Database updated
- [ ] Chart Snapshots tab → Gallery loads
- [ ] Filter by agent → Results update
- [ ] Delete snapshot → Removed from gallery

**Completion Criteria**: User can configure charts, view snapshots, all UI responsive.

---

## Phase 4: Agent Integration (3 hours)

### 4.1 Fix ChartWatcher

- [ ] Open `hetzner-deploy/src/chart_watcher.py`
- [ ] Add import: `from src.chart_service import ChartService`
- [ ] Fix lines 554-560:
  - [ ] Replace `self.chart_service.generate_url()` with `await chart_service.generate_chart_url()`
  - [ ] Update method signature to async
  - [ ] Pass correct parameters (symbol, timeframe, agent_name)
- [ ] Test: Run ChartWatcher task manually
- [ ] Verify: Chart snapshots created in database

### 4.2 Integrate MorningPlanner

- [ ] Open `hetzner-deploy/src/morning_planner.py`
- [ ] Add ChartService import
- [ ] Add `generate_symbol_setup()` method:
  - [ ] Generate H1 chart (structure)
  - [ ] Generate M15 chart (entry)
  - [ ] Generate D1 chart (context)
  - [ ] Return dict with 3 chart URLs
- [ ] Add Celery task: `morning_planner.generate_report`
- [ ] Add to beat_schedule: Daily at 06:00 UTC
- [ ] Test: Run task manually
- [ ] Verify: 15 snapshots created (5 symbols × 3 TFs)

### 4.3 Integrate JournalBot

- [ ] Open `hetzner-deploy/src/journal_bot.py`
- [ ] Add ChartService import
- [ ] Add `create_journal_entry()` method:
  - [ ] Generate chart snapshot
  - [ ] Create journal entry with snapshot_id
  - [ ] Generate AI-powered notes (placeholder)
- [ ] Add `add_chart_to_existing_entry()` method
- [ ] Add Celery task: `journal_bot.process_closed_trades`
- [ ] Test: Create test trade, run task
- [ ] Verify: Journal entry with chart created

### 4.4 TradeMonitor (Optional)

- [ ] Create `services/agents/src/trade_monitor.py`
- [ ] Implement `monitor_active_trades()` method
- [ ] Generate charts for active trades
- [ ] Check SL/TP levels (placeholder)
- [ ] Add Celery task (scheduled every 15 min)

### 4.5 Update tasks.py

- [ ] Import all agent modules
- [ ] Register all tasks with `@shared_task` decorator
- [ ] Update `beat_schedule`:
  - [ ] ChartWatcher: Every hour
  - [ ] MorningPlanner: Daily 06:00 UTC
  - [ ] JournalBot: Every 4 hours
  - [ ] TradeMonitor: Every 15 min (optional)

**Completion Criteria**: All agents generate charts, save snapshots, respect rate limits.

---

## Phase 5: Testing (2 hours)

### 5.1 Unit Tests

- [ ] Create `services/agents/tests/test_chart_service.py`
- [ ] Test `map_symbol()` - 3 cases
- [ ] Test `get_chart_config()` - Success & not found
- [ ] Test `build_chart_url()` - URL format
- [ ] Test `get_cache_key()` - Deterministic hash
- [ ] Test `check_rate_limits()` - Within & exceeded
- [ ] Test `generate_chart_url()` - Success, cached, rate limited
- [ ] Run: `pytest tests/test_chart_service.py -v`
- [ ] Target: > 80% coverage

### 5.2 Integration Tests

- [ ] Create `services/agents/tests/test_agent_integration.py`
- [ ] Test ChartWatcher integration
- [ ] Test MorningPlanner integration
- [ ] Test JournalBot integration
- [ ] Run: `pytest tests/test_agent_integration.py -v -m integration`

### 5.3 E2E Tests

- [ ] Create `services/agents/tests/test_e2e.py`
- [ ] Test full flow: Generate → Verify URL → Check DB → Test cache
- [ ] Run: `pytest tests/test_e2e.py -v -m e2e`

### 5.4 Manual Testing

- [ ] **User configures chart**:
  - [ ] Login to dashboard
  - [ ] Click "Chart Config" for DAX
  - [ ] Select timeframes & indicators
  - [ ] Save config
  - [ ] Verify database updated

- [ ] **ChartWatcher generates charts**:
  - [ ] SSH into server
  - [ ] Trigger task manually
  - [ ] Check logs for success
  - [ ] Verify snapshots in database

- [ ] **MorningPlanner daily report**:
  - [ ] Trigger task manually
  - [ ] Verify 3 charts per symbol
  - [ ] Check chart URLs accessible

- [ ] **Rate limit handling**:
  - [ ] Set Redis counter to 999
  - [ ] Trigger chart generation
  - [ ] Verify fallback to cache or error

- [ ] **Chart snapshot gallery**:
  - [ ] Navigate to Chart Snapshots tab
  - [ ] Verify gallery loads
  - [ ] Filter by agent
  - [ ] Delete snapshot

### 5.5 Performance Tests

- [ ] Run load test: 100 requests
- [ ] Measure avg response time (< 500ms cached, < 2s uncached)
- [ ] Check cache hit rate (> 70%)
- [ ] Monitor memory usage (Redis, Docker)

**Completion Criteria**: All tests pass, manual scenarios verified, performance acceptable.

---

## Phase 6: Deployment (1 hour)

### 6.1 Pre-Deployment

- [ ] Create database backup
- [ ] Test all changes in local environment
- [ ] Review all code changes (git diff)
- [ ] Update CHANGELOG.md (if exists)

### 6.2 Database Migration (Production)

- [ ] Login to Supabase Dashboard
- [ ] Open SQL Editor
- [ ] Run migration 016 (chart_config)
- [ ] Verify: `SELECT chart_config FROM market_symbols LIMIT 1;`
- [ ] Run migration 017 (chart_snapshots)
- [ ] Verify: `SELECT COUNT(*) FROM chart_snapshots;`
- [ ] Run migration 018 (cleanup function)

### 6.3 Code Deployment (Hetzner)

- [ ] SSH into server: `ssh root@135.181.195.241`
- [ ] Navigate to: `cd /root/tradematrix-agents`
- [ ] Create `src/chart_service.py` (copy from local)
- [ ] Update `src/chart_watcher.py` (fix lines 554-560)
- [ ] Update `src/morning_planner.py` (add chart integration)
- [ ] Update `src/journal_bot.py` (add chart integration)
- [ ] Update `requirements.txt` (add httpx)
- [ ] Update `.env` (add CHART_IMG_API_KEY)
- [ ] Update `docker-compose.yml` (pass env vars)

### 6.4 Build & Restart

- [ ] Stop containers: `docker-compose down`
- [ ] Rebuild images: `docker-compose build --no-cache`
- [ ] Start containers: `docker-compose up -d`
- [ ] Verify running: `docker-compose ps`
- [ ] Check logs: `docker-compose logs -f celery-worker`

### 6.5 Frontend Deployment (Netlify)

- [ ] Commit frontend changes: `git add . && git commit -m "feat: chart-img integration"`
- [ ] Push to GitHub: `git push origin main`
- [ ] Wait for Netlify auto-deploy (~2 min)
- [ ] Verify deployment: https://tradematrix.netlify.app

### 6.6 Verify Production

- [ ] Test ChartWatcher: `docker-compose exec celery-worker celery -A src.tasks call chart_watcher.analyze_all_symbols`
- [ ] Check database: `SELECT COUNT(*) FROM chart_snapshots;`
- [ ] Check Redis: `docker-compose exec redis redis-cli GET chart_api:daily:$(date +%Y-%m-%d)`
- [ ] Test frontend: Configure chart, view snapshots
- [ ] Monitor logs for 1 hour: `docker-compose logs -f`

**Completion Criteria**: All services running, charts generating, no errors in logs.

---

## Post-Deployment Monitoring (24 hours)

### Hour 1-6

- [ ] Check logs every hour for errors
- [ ] Verify chart snapshots increasing
- [ ] Monitor rate limit usage (< 100 in first 6 hours)
- [ ] Test frontend functionality
- [ ] Verify background tasks running (ChartWatcher, MorningPlanner)

### Hour 6-12

- [ ] Check MorningPlanner executed (06:00 UTC)
- [ ] Verify 15 snapshots created (5 symbols × 3 TFs)
- [ ] Monitor Redis memory usage
- [ ] Check Docker stats (CPU, RAM)

### Hour 12-24

- [ ] Review total API usage (should be < 200/day)
- [ ] Check cache hit rate (> 70%)
- [ ] Verify no rate limit errors
- [ ] Test all frontend features still working
- [ ] Review Supabase logs for RLS errors

### Day 2-7

- [ ] Daily check: API usage trend
- [ ] Weekly cleanup: `SELECT cleanup_expired_chart_snapshots();`
- [ ] Review chart-img.com dashboard for usage stats
- [ ] Monitor for any performance degradation

**Completion Criteria**: No errors for 24 hours, all features working, rate limits respected.

---

## Rollback Plan

If critical issues occur:

1. [ ] Stop containers: `docker-compose down`
2. [ ] Revert code: `git checkout HEAD~1`
3. [ ] Rebuild: `docker-compose build --no-cache && docker-compose up -d`
4. [ ] Verify services: `docker-compose ps`
5. [ ] Roll back database:
   ```sql
   DROP TABLE IF EXISTS chart_snapshots;
   ALTER TABLE market_symbols DROP COLUMN IF EXISTS chart_config;
   ```

---

## Success Metrics

### Technical Metrics

- [ ] Chart generation success rate > 95%
- [ ] Average response time < 500ms (cached), < 2s (uncached)
- [ ] Cache hit rate > 70%
- [ ] Daily API usage < 300/day (with 5 symbols)
- [ ] Zero rate limit errors (with caching)
- [ ] Database query time < 100ms
- [ ] Zero RLS policy violations

### User Metrics

- [ ] User can configure charts in < 2 minutes
- [ ] Chart preview loads in < 3 seconds
- [ ] Snapshot gallery loads in < 2 seconds
- [ ] Zero frontend errors in console
- [ ] Mobile-responsive (tested on iPhone & Android)

### Agent Metrics

- [ ] ChartWatcher analyzes 5 symbols hourly
- [ ] MorningPlanner generates 15 charts daily (06:00 UTC)
- [ ] JournalBot creates entries with charts
- [ ] All agents complete tasks without errors

---

## Documentation Checklist

- [x] README.md (feature overview)
- [x] 01_ARCHITECTURE.md (system design)
- [x] 02_DATABASE_SCHEMA.md (tables, migrations)
- [x] 03_API_ENDPOINTS.md (FastAPI routes)
- [x] 04_FRONTEND_COMPONENTS.md (React components)
- [x] 05_AGENT_INTEGRATION.md (ChartWatcher, MorningPlanner, JournalBot)
- [x] 06_DEPLOYMENT.md (Hetzner deployment guide)
- [x] 07_TESTING.md (test checklists)
- [x] 08_TROUBLESHOOTING.md (common issues)
- [x] IMPLEMENTATION_CHECKLIST.md (this file)
- [ ] SESSION_CONTEXT.md (quick start for new sessions)

---

## Sign-Off

### Phase 1: Database Setup
- [ ] Completed by: ___________
- [ ] Date: ___________
- [ ] Verified by: ___________

### Phase 2: Backend API
- [ ] Completed by: ___________
- [ ] Date: ___________
- [ ] Verified by: ___________

### Phase 3: Frontend UI
- [ ] Completed by: ___________
- [ ] Date: ___________
- [ ] Verified by: ___________

### Phase 4: Agent Integration
- [ ] Completed by: ___________
- [ ] Date: ___________
- [ ] Verified by: ___________

### Phase 5: Testing
- [ ] Completed by: ___________
- [ ] Date: ___________
- [ ] Verified by: ___________

### Phase 6: Deployment
- [ ] Completed by: ___________
- [ ] Date: ___________
- [ ] Verified by: ___________

### Production Sign-Off
- [ ] All tests passed: ___________
- [ ] 24h monitoring complete: ___________
- [ ] No critical issues: ___________
- [ ] Ready for production: ___________
- [ ] Approved by: ___________
- [ ] Date: ___________

---

**Last Updated**: 2025-11-02
**Status**: Ready for implementation
**Estimated Completion**: 12 hours (across 6 phases)
