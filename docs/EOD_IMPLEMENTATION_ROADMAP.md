# EOD Data Layer - Implementation Roadmap

**Project:** TradeMatrix.ai EOD Data Layer  
**Version:** 1.0.0  
**Status:** Planning → Implementation  
**Timeline:** 4 Weeks  
**Last Updated:** 2025-10-31

---

## 📋 Overview

This roadmap outlines the step-by-step implementation plan for integrating the EOD Data Layer into TradeMatrix.ai, replacing Twelve Data dependency with cost-free alternatives.

---

## 🎯 Goals

✅ **Zero Cost** - Eliminate Twelve Data subscription  
✅ **Same Functionality** - Maintain all existing features  
✅ **Better Quality** - Cross-validated data from multiple sources  
✅ **Automated** - Fully scheduled and monitored  
✅ **Integrated** - Seamless integration with all modules  

---

## 📅 Phase Overview

| Phase | Duration | Focus | Status |
|-------|----------|-------|--------|
| **Phase 0** | Day 0 | Planning & Documentation | ✅ Complete |
| **Phase 1** | Week 1 | Database & Core Fetcher | 🟡 Ready |
| **Phase 2** | Week 2 | Module Integration | ⏳ Pending |
| **Phase 3** | Week 3 | Automation & Monitoring | ⏳ Pending |
| **Phase 4** | Week 4 | Testing & Optimization | ⏳ Pending |

---

## Phase 0: Planning & Documentation ✅

**Duration:** Day 0 (2025-10-31)  
**Status:** ✅ **COMPLETE**

### Deliverables

- [x] Complete configuration YAML
- [x] Database schema design
- [x] Data fetcher module
- [x] Celery task structure
- [x] Full documentation
- [x] Quick reference guide
- [x] Implementation roadmap

### Files Created

```
config/
  └── eod_data_config.yaml          ✅ Configuration

services/api/supabase/migrations/
  └── 004_eod_data_layer.sql        ✅ Database schema

services/agents/
  ├── src/eod_data_fetcher.py       ✅ Core fetcher
  └── eod_tasks.py                  ✅ Celery tasks

docs/
  ├── EOD_DATA_LAYER.md             ✅ Full documentation
  ├── EOD_DATA_LAYER_QUICKREF.md    ✅ Quick reference
  └── EOD_IMPLEMENTATION_ROADMAP.md ✅ This file
```

---

## Phase 1: Database & Core Fetcher 🟡

**Duration:** Week 1 (Days 1-5)  
**Status:** 🟡 **READY TO START**

### Day 1: Database Setup

**Tasks:**
- [ ] Review database schema
- [ ] Run Supabase migration
- [ ] Verify tables created
- [ ] Test utility functions
- [ ] Create test data

**Commands:**
```bash
# Run migration
cd services/api/supabase/migrations
supabase db push 004_eod_data_layer.sql

# Verify tables
supabase db ls

# Test functions
SELECT * FROM get_latest_eod('^GDAXI');
```

**Acceptance Criteria:**
- ✅ All 3 tables exist: `eod_data`, `eod_levels`, `eod_fetch_log`
- ✅ All indexes created
- ✅ RLS policies active
- ✅ Utility functions working

### Day 2: Data Fetcher Setup

**Tasks:**
- [ ] Install Python dependencies
- [ ] Configure environment variables
- [ ] Test Stooq.com connection
- [ ] Test Yahoo Finance connection
- [ ] Verify cross-validation logic

**Commands:**
```bash
# Install dependencies
pip install aiohttp pyyaml

# Set environment
export SUPABASE_URL=...
export SUPABASE_SERVICE_ROLE_KEY=...

# Test fetch
cd services/agents
python src/eod_data_fetcher.py
```

**Acceptance Criteria:**
- ✅ Can fetch from Stooq for all symbols
- ✅ Can fetch from Yahoo for all symbols
- ✅ Cross-validation returns quality scores
- ✅ Data stored in `eod_data` table

### Day 3: Level Calculation

**Tasks:**
- [ ] Test yesterday level calculation
- [ ] Test ATR calculation (5d, 20d)
- [ ] Test daily change calculation
- [ ] Verify `eod_levels` table population
- [ ] Test SQL utility functions

**Commands:**
```sql
-- Check levels
SELECT * FROM eod_levels WHERE symbol_id = ?;

-- Test ATR function
SELECT calculate_atr('^GDAXI', 5);

-- Check yesterday levels
SELECT * FROM get_yesterday_levels('^GDAXI', CURRENT_DATE);
```

**Acceptance Criteria:**
- ✅ Levels calculated correctly for all symbols
- ✅ ATR values match manual calculations
- ✅ Utility functions return expected results

### Day 4: Error Handling

**Tasks:**
- [ ] Test network failure scenarios
- [ ] Test invalid data responses
- [ ] Test missing symbol handling
- [ ] Verify retry logic (3 attempts)
- [ ] Check error logging

**Test Scenarios:**
```python
# Scenario 1: Network timeout
# Expected: Retry 3 times, log error

# Scenario 2: Invalid CSV format
# Expected: Use backup source (Yahoo)

# Scenario 3: No data from any source
# Expected: Log failure, don't crash
```

**Acceptance Criteria:**
- ✅ Graceful handling of all error types
- ✅ Retry logic works correctly
- ✅ Errors logged to `eod_fetch_log`

### Day 5: Manual Testing

**Tasks:**
- [ ] Run manual fetch for all symbols
- [ ] Verify data quality scores
- [ ] Check cross-validation results
- [ ] Review fetch logs
- [ ] Generate test report

**Commands:**
```bash
# Full manual fetch
python src/eod_data_fetcher.py

# Check results
psql -c "SELECT * FROM eod_quality_summary;"
psql -c "SELECT * FROM eod_fetch_log ORDER BY created_at DESC LIMIT 10;"
```

**Acceptance Criteria:**
- ✅ All symbols fetched successfully
- ✅ Quality scores ≥ 0.80
- ✅ No critical errors in logs

---

## Phase 2: Module Integration ⏳

**Duration:** Week 2 (Days 6-10)  
**Status:** ⏳ **PENDING PHASE 1**

### Day 6: MorningPlanner Integration

**Tasks:**
- [ ] Update `morning_planner.py` to use `eod_levels`
- [ ] Replace hardcoded levels with database queries
- [ ] Test Asia Sweep detection with new data
- [ ] Test Y-Low Pivot Rebound with new data
- [ ] Verify confidence scoring unchanged

**Code Changes:**
```python
# OLD: Manual level input
y_low = 17500  # Hardcoded

# NEW: Query from eod_levels
levels = self.supabase.table('eod_levels')\
    .select('yesterday_low')\
    .eq('symbol_id', symbol_id)\
    .execute()
y_low = Decimal(str(levels.data[0]['yesterday_low']))
```

**Acceptance Criteria:**
- ✅ MorningPlanner uses database levels
- ✅ All existing tests pass
- ✅ No degradation in signal quality

### Day 7: USOpenPlanner Integration

**Tasks:**
- [ ] Update `us_open_planner.py` to use `eod_levels`
- [ ] Add liquidity sweep detection
- [ ] Test pre-market range comparison
- [ ] Test breakout detection
- [ ] Update confidence calculations

**Acceptance Criteria:**
- ✅ USOpenPlanner uses database levels
- ✅ Liquidity sweep detection working
- ✅ All existing functionality preserved

### Day 8: ValidationEngine Creation

**Tasks:**
- [ ] Create new `validation_engine.py` module
- [ ] Implement yesterday level context check
- [ ] Add breakout vs. liquidity sweep detection
- [ ] Integrate with existing validation rules
- [ ] Test with historical data

**New Features:**
```python
def validate_entry_context(price, symbol_id, date):
    """Check entry against yesterday levels"""
    levels = get_yesterday_levels(symbol_id, date)
    
    if price > levels['yesterday_high']:
        return {
            'context': 'breakout',
            'confidence_boost': 0.05
        }
    elif price < levels['yesterday_low']:
        return {
            'context': 'liquidity_sweep',
            'confidence_boost': 0.10
        }
```

**Acceptance Criteria:**
- ✅ ValidationEngine provides level context
- ✅ Confidence boosts applied correctly
- ✅ Integrates with existing rules

### Day 9: ReportPublisher Integration

**Tasks:**
- [ ] Add EOD performance section to daily reports
- [ ] Include yesterday levels in trade summaries
- [ ] Add weekly performance comparison
- [ ] Update report templates
- [ ] Test report generation

**Report Enhancements:**
```
📊 Market Performance (2025-10-31)
─────────────────────────────────
DAX:     17,810.55  (+0.45% | +79.50 pts)
NASDAQ:  15,234.67  (-0.12% | -18.30 pts)

Yesterday Levels:
  DAX High:  17,892.34  → Rejected
  DAX Low:   17,602.10  → Held
```

**Acceptance Criteria:**
- ✅ Reports include EOD summary
- ✅ Yesterday levels shown in trade context
- ✅ Weekly comparisons accurate

### Day 10: Integration Testing

**Tasks:**
- [ ] End-to-end test: Fetch → Calculate → Use in modules
- [ ] Test full morning workflow
- [ ] Test full US Open workflow
- [ ] Verify report generation
- [ ] Check data consistency

**Test Workflow:**
```
07:30 → EOD Fetch (all symbols)
08:25 → MorningPlanner (uses new levels)
14:30 → USOpenPlanner (uses new levels)
22:00 → ReportPublisher (includes EOD data)
```

**Acceptance Criteria:**
- ✅ Full workflow runs without errors
- ✅ All modules use EOD data correctly
- ✅ Reports accurate and complete

---

## Phase 3: Automation & Monitoring ⏳

**Duration:** Week 3 (Days 11-15)  
**Status:** ⏳ **PENDING PHASE 2**

### Day 11: Celery Setup

**Tasks:**
- [ ] Configure Celery workers
- [ ] Set up Celery Beat scheduler
- [ ] Configure task queues
- [ ] Test scheduled task execution
- [ ] Verify timezone handling (CET)

**Commands:**
```bash
# Start worker
celery -A eod_tasks worker --loglevel=info --queue=eod_tasks

# Start scheduler
celery -A eod_tasks beat --loglevel=info

# Monitor tasks
celery -A eod_tasks inspect active
celery -A eod_tasks inspect scheduled
```

**Acceptance Criteria:**
- ✅ Workers start without errors
- ✅ Beat scheduler running
- ✅ Tasks execute at scheduled times

### Day 12: Task Scheduling

**Tasks:**
- [ ] Verify daily fetch at 07:30 CET
- [ ] Test weekend maintenance task
- [ ] Test weekly summary task
- [ ] Configure retry logic
- [ ] Test task failure recovery

**Schedule Verification:**
```python
# Daily Fetch: 07:30 CET
'fetch-eod-daily': {
    'task': 'eod.fetch_daily',
    'schedule': crontab(hour=7, minute=30)
}

# Weekend Maintenance: Saturday 09:00
'weekend-maintenance': {
    'task': 'eod.weekend_maintenance',
    'schedule': crontab(hour=9, minute=0, day_of_week=6)
}
```

**Acceptance Criteria:**
- ✅ All tasks execute at correct times
- ✅ Timezone handling correct (CET)
- ✅ Retry logic works on failure

### Day 13: Monitoring Setup

**Tasks:**
- [ ] Create monitoring dashboard (Supabase)
- [ ] Set up quality alerts
- [ ] Configure performance metrics
- [ ] Test alert notifications
- [ ] Create monitoring queries

**Key Metrics:**
```sql
-- Fetch success rate (last 7 days)
SELECT 
    COUNT(CASE WHEN status = 'success' THEN 1 END)::FLOAT / COUNT(*) * 100 AS success_rate
FROM eod_fetch_log
WHERE fetch_date >= CURRENT_DATE - INTERVAL '7 days';

-- Average quality score
SELECT AVG(quality_score) FROM eod_data WHERE trade_date >= CURRENT_DATE - 7;

-- Data freshness
SELECT symbol, MAX(trade_date) FROM eod_data GROUP BY symbol;
```

**Acceptance Criteria:**
- ✅ Dashboard shows key metrics
- ✅ Alerts trigger on issues
- ✅ Performance tracked over time

### Day 14: Logging & Debugging

**Tasks:**
- [ ] Configure structured logging
- [ ] Set up log rotation
- [ ] Create debug utilities
- [ ] Test log aggregation
- [ ] Document troubleshooting steps

**Log Configuration:**
```python
logging.config.dictConfig({
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/eod_data_layer.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    }
})
```

**Acceptance Criteria:**
- ✅ All operations logged
- ✅ Log rotation working
- ✅ Debug tools available

### Day 15: Notification Setup

**Tasks:**
- [ ] Configure Slack webhooks (optional)
- [ ] Configure Telegram bot (optional)
- [ ] Test failure notifications
- [ ] Test quality warning alerts
- [ ] Set up daily summary notifications

**Notification Events:**
- Daily fetch complete (success/failure)
- Quality score below threshold
- Missing data detected
- Network issues

**Acceptance Criteria:**
- ✅ Notifications deliver correctly
- ✅ Alert levels appropriate
- ✅ No spam/false positives

---

## Phase 4: Testing & Optimization ⏳

**Duration:** Week 4 (Days 16-20)  
**Status:** ⏳ **PENDING PHASE 3**

### Day 16: Load Testing

**Tasks:**
- [ ] Test concurrent fetches
- [ ] Test database query performance
- [ ] Optimize slow queries
- [ ] Add database indexes if needed
- [ ] Test with large historical datasets

**Performance Targets:**
- Fetch all symbols: < 30 seconds
- Level calculation: < 5 seconds
- Query yesterday levels: < 100ms

**Acceptance Criteria:**
- ✅ Meets performance targets
- ✅ No bottlenecks identified
- ✅ Scales for future growth

### Day 17: Comprehensive Testing

**Tasks:**
- [ ] Run full test suite
- [ ] Test edge cases
- [ ] Test error scenarios
- [ ] Test data recovery
- [ ] Verify data consistency

**Test Categories:**
- Unit tests (fetcher, calculations)
- Integration tests (end-to-end)
- Edge cases (missing data, API failures)
- Performance tests (load, stress)

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ Test coverage ≥ 80%
- ✅ No critical bugs

### Day 18: Documentation Review

**Tasks:**
- [ ] Review all documentation
- [ ] Add missing examples
- [ ] Create video tutorials (optional)
- [ ] Update README files
- [ ] Create troubleshooting guide

**Documentation Checklist:**
- [x] EOD_DATA_LAYER.md (complete guide)
- [x] EOD_DATA_LAYER_QUICKREF.md (quick start)
- [x] EOD_IMPLEMENTATION_ROADMAP.md (this file)
- [ ] API reference (code comments)
- [ ] Video walkthrough (optional)

**Acceptance Criteria:**
- ✅ Documentation complete and accurate
- ✅ Examples tested and working
- ✅ Easy for new developers to understand

### Day 19: Deployment Preparation

**Tasks:**
- [ ] Create deployment checklist
- [ ] Test production environment
- [ ] Set up backup procedures
- [ ] Create rollback plan
- [ ] Final security review

**Deployment Checklist:**
```
□ Database migration tested
□ Environment variables set
□ Celery workers configured
□ Redis connection verified
□ Monitoring dashboard live
□ Alerts configured
□ Backup strategy in place
□ Rollback plan documented
```

**Acceptance Criteria:**
- ✅ Production environment ready
- ✅ All services configured
- ✅ Rollback plan tested

### Day 20: Go-Live

**Tasks:**
- [ ] Deploy to production
- [ ] Monitor first fetch
- [ ] Verify all modules using new data
- [ ] Check system health
- [ ] Decommission Twelve Data (if applicable)

**Go-Live Steps:**
1. Deploy database migration
2. Start Celery workers
3. Enable Celery Beat scheduler
4. Monitor first scheduled fetch (07:30 CET next day)
5. Verify data quality
6. Check module integrations
7. Monitor for 48 hours
8. Mark as production-ready ✅

**Acceptance Criteria:**
- ✅ System running in production
- ✅ All modules functioning correctly
- ✅ No critical issues
- ✅ Zero downtime migration

---

## 📊 Success Metrics

### Technical Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Fetch Success Rate | ≥ 99% | - |
| Data Quality Score | ≥ 0.90 | - |
| Fetch Duration | < 30s | - |
| Query Performance | < 100ms | - |
| System Uptime | ≥ 99.9% | - |

### Business Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Cost Savings | €50-200/mo | €0 |
| Data Coverage | 5 symbols | - |
| Module Integration | 4 modules | - |
| User Satisfaction | ≥ 90% | - |

---

## 🚧 Risk Management

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data source downtime | Medium | High | Multiple fallback sources |
| Quality degradation | Low | Medium | Cross-validation, monitoring |
| Integration bugs | Medium | Medium | Comprehensive testing |
| Performance issues | Low | High | Load testing, optimization |
| Deployment issues | Low | High | Rollback plan, staging env |

### Contingency Plans

**If Stooq fails:**
→ Automatically fallback to Yahoo Finance

**If both sources fail:**
→ Use cached data + alert team

**If database issues:**
→ Store in local files, batch upload later

**If integration breaks:**
→ Rollback to Twelve Data temporarily

---

## ✅ Completion Criteria

The EOD Data Layer is considered **production-ready** when:

- [x] All code and configurations committed
- [x] Database schema deployed
- [ ] All automated tests passing
- [ ] Data fetching running on schedule
- [ ] All modules integrated
- [ ] Monitoring and alerts active
- [ ] Documentation complete
- [ ] Team trained on system
- [ ] 48-hour production monitoring complete
- [ ] Twelve Data dependency removed

---

## 👥 Team & Responsibilities

| Role | Responsibility | Owner |
|------|---------------|-------|
| **Backend Developer** | Database, API integration | TBD |
| **DevOps Engineer** | Celery, monitoring, deployment | TBD |
| **QA Engineer** | Testing, quality assurance | TBD |
| **Product Owner** | Requirements, acceptance | TBD |
| **Tech Lead** | Architecture, code review | TBD |

---

## 📞 Communication Plan

### Daily Standups
- Progress updates
- Blocker identification
- Next steps alignment

### Weekly Reviews
- Sprint retrospective
- Metrics review
- Roadmap adjustments

### Documentation Updates
- Keep docs in sync with code
- Document all decisions
- Update this roadmap

---

## 📝 Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-31 | 1.0.0 | Initial roadmap created |

---

**Document Status:** 🟢 Active  
**Next Review Date:** Start of Phase 1  
**Maintained By:** TradeMatrix.ai Team

---

**Ready to start Phase 1? Let's go! 🚀**
