# TradingView Watchlist Feature

**Feature ID:** Phase 5C
**Status:** 🚧 In Progress
**Started:** 2025-11-03
**Target Completion:** 2025-11-05

---

## 🎯 Overview

User-customizable watchlist with up to 10 symbols displayed via **TradingView Widgets** (live prices, free). Hybrid approach: TradingView for display, Hetzner backend for alerts.

**Key Benefits:**
- ✅ **€0 cost** for live prices (TradingView free widgets)
- ✅ **No WebSocket** complexity
- ✅ **Fast implementation** (~6 hours vs 2-3 days)
- ✅ **Unlimited symbols** possible (no API limits)
- ✅ **Hetzner stays** for alert system

---

## 🏗️ Architecture: Hybrid Approach

```
┌─────────────────────────────────────┐
│ Frontend (Next.js)                  │
│                                     │
│ 1. User selects 10 symbols          │
│ 2. Saves to user_watchlist (DB)     │
│ 3. Renders TradingView Widgets      │
│    → Widgets fetch live data        │
│    → No backend needed!             │
└─────────────────────────────────────┘
              │
              │ (Only for Alerts)
              ↓
┌─────────────────────────────────────┐
│ Hetzner Backend (Celery)            │
│                                     │
│ • Reads user_watchlist from DB      │
│ • Fetches prices (yfinance + TD)    │
│ • Checks liquidity alerts           │
│ • Sends push notifications          │
│                                     │
│ NO WebSocket needed!                │
└─────────────────────────────────────┘
```

**Why NOT WebSocket?**
- TradingView Widgets already provide live data
- WebSocket only needed if we build custom UI
- Saves development time & reduces complexity

---

## 📋 Implementation Phases

| Phase | Description | Time | Status |
|-------|-------------|------|--------|
| **1. Database** | user_watchlist table + RLS | 30 min | ✅ Complete |
| **2. Symbol Picker** | UI to add/remove symbols | 2 hours | ⏳ Pending |
| **3. TradingView Widgets** | Replace market cards | 2 hours | ⏳ Pending |
| **4. Backend Update** | Dynamic symbol loading | 30 min | ⏳ Pending |
| **5. Testing** | E2E + Deployment | 1 hour | ⏳ Pending |

**Total:** ~6 hours

---

## 📁 Documentation Files

1. **[01_ARCHITECTURE.md](./01_ARCHITECTURE.md)** - System design & data flow
2. **[02_DATABASE_SCHEMA.md](./02_DATABASE_SCHEMA.md)** - user_watchlist table & migration
3. **[03_FRONTEND_IMPLEMENTATION.md](./03_FRONTEND_IMPLEMENTATION.md)** - TradingView Widget integration
4. **[04_BACKEND_UPDATES.md](./04_BACKEND_UPDATES.md)** - Alert system changes
5. **[05_TESTING_GUIDE.md](./05_TESTING_GUIDE.md)** - Testing checklist
6. **[IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)** - Session tracking

---

## 🚀 Quick Start (Next Session)

**Read this first:**
1. [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) - Check current status
2. [01_ARCHITECTURE.md](./01_ARCHITECTURE.md) - Understand system design

**Then implement:**
- Next task from checklist
- Update checklist after completion

---

## 🎯 Success Criteria

- [ ] User can add/remove up to 10 symbols
- [ ] Dashboard shows live prices via TradingView Widgets
- [ ] Symbol Picker UI intuitive & responsive
- [ ] Alerts still work (Hetzner unchanged)
- [ ] No additional API costs
- [ ] Documentation complete

---

## 🔗 Related Documentation

- **Architecture:** [../../ARCHITECTURE.md](../../ARCHITECTURE.md)
- **Master Roadmap:** [../../00_MASTER_ROADMAP.md](../../00_MASTER_ROADMAP.md)
- **Project Overview:** [../../PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md)

---

**Last Updated:** 2025-11-03
**Next Review:** After Phase 2 completion
