# Implementation Checklist: TradingView Watchlist

**Feature ID:** Phase 5C
**Started:** 2025-11-03
**Target Completion:** 2025-11-05

---

## 📊 Overall Progress: 15% Complete

**Estimated Total Time:** ~6 hours
**Time Spent:** ~1 hour (planning + database)
**Time Remaining:** ~5 hours

---

## ✅ Phase 1: Database Setup (100% DONE)

### Migration 017: user_watchlist Table
- [x] SQL migration created
- [x] Executed in Supabase SQL Editor
- [x] Table exists: `user_watchlist`
- [x] Columns: id, user_id, symbol_id, position, created_at, updated_at
- [x] Constraints: UNIQUE(user_id, symbol_id), UNIQUE(user_id, position), CHECK(position 1-10)

### RLS Policies
- [x] Row Level Security enabled
- [x] Policy "Users manage own watchlist" created
- [x] Tested: Users see only their own watchlists

### Indexes
- [x] `idx_user_watchlist_user` created
- [x] `idx_user_watchlist_position` created

### Migration 018: symbols.tv_symbol Column
- [ ] **TODO:** Add tv_symbol column to symbols table
  ```sql
  ALTER TABLE public.symbols ADD COLUMN tv_symbol TEXT;
  ```
- [ ] **TODO:** Update existing symbols with TradingView format
  ```sql
  UPDATE symbols SET tv_symbol = 'XETR:DAX' WHERE symbol = '^GDAXI';
  UPDATE symbols SET tv_symbol = 'NASDAQ:NDX' WHERE symbol = '^NDX';
  UPDATE symbols SET tv_symbol = 'DJ:DJI' WHERE symbol = '^DJI';
  UPDATE symbols SET tv_symbol = 'FX:EURUSD' WHERE symbol = 'EURUSD';
  UPDATE symbols SET tv_symbol = 'FX:EURGBP' WHERE symbol = 'EURGBP';
  UPDATE symbols SET tv_symbol = 'FX:GBPUSD' WHERE symbol = 'GBPUSD';
  ```

### Default Watchlist Function
- [ ] **TODO:** Create `create_default_watchlist(p_user_id)` function
- [ ] **TODO:** Call on new user signup (trigger or manual call)

**Phase 1 Status:** ⏸️ Waiting for Migration 018

---

## 🎨 Phase 2: Frontend - Symbol Picker (0% DONE)

### Component: symbol-picker-modal.tsx
**File:** `apps/web/src/components/dashboard/symbol-picker-modal.tsx`

- [ ] Create file
- [ ] Import shadcn components (Dialog, Button, Input, Badge, ScrollArea)
- [ ] State management (searchQuery, allSymbols, watchlist, loading, saving)
- [ ] `loadData()` function (fetch symbols + watchlist from Supabase)
- [ ] Symbol search & filtering logic
- [ ] `addSymbol()` function (max 10 check)
- [ ] `removeSymbol()` function (recalculate positions)
- [ ] `saveWatchlist()` function (delete all + insert new)
- [ ] Two-column layout (Watchlist | Available Symbols)
- [ ] Search input with icon
- [ ] Drag & drop (optional, v2 feature)
- [ ] Loading states
- [ ] Error handling

### Testing
- [ ] Modal opens/closes correctly
- [ ] Search filters symbols
- [ ] Add symbol (up to 10)
- [ ] Remove symbol
- [ ] Save persists to database
- [ ] Cancel discards changes

**Estimated Time:** 2 hours
**Phase 2 Status:** ⏳ Not Started

---

## 📺 Phase 3: Frontend - TradingView Widgets (0% DONE)

### Component: tradingview-widget.tsx
**File:** `apps/web/src/components/dashboard/tradingview-widget.tsx`

- [ ] Create file
- [ ] Props interface (symbol, width, height, colorTheme)
- [ ] `useEffect` to load TradingView script
- [ ] Widget configuration (Symbol Overview type)
- [ ] Loading state with spinner
- [ ] Error state with message
- [ ] Cleanup on unmount
- [ ] Dark mode styling

### Update: dashboard/page.tsx
**File:** `apps/web/src/app/(dashboard)/dashboard/page.tsx`

- [ ] Import TradingViewWidget component
- [ ] Import SymbolPickerModal component
- [ ] Add `watchlist` state
- [ ] Add `showSymbolPicker` state
- [ ] Create `fetchWatchlist()` function
- [ ] Replace `fetchMarketData()` with `fetchWatchlist()`
- [ ] Update useEffect to call fetchWatchlist
- [ ] Remove old market-overview-card import
- [ ] Update Market Overview section:
  - [ ] Add "Edit Watchlist" button
  - [ ] Render TradingView widgets (grid layout)
  - [ ] Empty state ("No symbols")
- [ ] Add SymbolPickerModal at end
- [ ] Pass userId prop to modal
- [ ] Pass onSaved callback (calls fetchWatchlist)

### Delete: market-overview-card.tsx
**File:** `apps/web/src/components/dashboard/market-overview-card.tsx`

- [ ] Confirm no other files import this component
- [ ] Delete file

### Testing
- [ ] Widgets render for each symbol
- [ ] Live prices visible
- [ ] Widgets update automatically (TradingView handles)
- [ ] Responsive grid (3 cols desktop, 2 tablet, 1 mobile)
- [ ] Edit button opens Symbol Picker
- [ ] Empty state shows correctly
- [ ] No console errors

**Estimated Time:** 2 hours
**Phase 3 Status:** ⏳ Not Started

---

## 🖥️ Phase 4: Backend Updates (0% DONE)

### File: hetzner-deploy/src/alert_engine.py

- [ ] Add `get_all_watched_symbols()` function
  - [ ] Query user_watchlist + symbols JOIN
  - [ ] Extract unique symbols where is_active = true
  - [ ] Fallback to default symbols if error
  - [ ] Optional: Limit to top 50 most popular
- [ ] Update `check_all_alerts()` function
  - [ ] Call get_all_watched_symbols() instead of hardcoded list
  - [ ] Log: "Checking alerts for N symbols: [...]"
- [ ] Test fallback mechanism (simulate DB error)

### Deployment (Hetzner Server)

**Option A: Direct Edit**
- [ ] SSH: `ssh root@135.181.195.241`
- [ ] Edit: `nano /root/TradeMatrix/hetzner-deploy/src/alert_engine.py`
- [ ] Paste new `get_all_watched_symbols()` function
- [ ] Update `check_all_alerts()` call
- [ ] Restart: `docker-compose restart celery-worker`
- [ ] Monitor: `docker-compose logs -f celery-worker`

**Option B: Git Pull**
- [ ] Commit changes locally
- [ ] Push to GitHub: `git push origin main`
- [ ] SSH to server
- [ ] Pull: `git pull origin main`
- [ ] Restart: `docker-compose restart celery-worker`

### Testing
- [ ] Celery logs show dynamic symbol list
- [ ] Add new symbol via frontend
- [ ] Check logs within 60s (new symbol appears)
- [ ] Remove symbol via frontend
- [ ] Check logs within 60s (symbol disappears)
- [ ] Simulate DB error → fallback works

**Estimated Time:** 30 minutes
**Phase 4 Status:** ⏳ Not Started

---

## 🧪 Phase 5: Testing & Deployment (0% DONE)

### End-to-End Testing (Localhost)
- [ ] Run: `npm run dev`
- [ ] Navigate to http://localhost:3000/dashboard
- [ ] Test Symbol Picker (add, remove, save)
- [ ] Test TradingView Widgets (load, display prices)
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Check browser console (no errors)
- [ ] Test with different users (RLS working)

### Database Verification
- [ ] Query: Check user_watchlist for test user
- [ ] Query: Verify symbols have tv_symbol values
- [ ] Query: Check RLS policies active

### Frontend Deployment (Netlify)
- [ ] Run: `npm run build` (no errors)
- [ ] Run: `npm run type-check` (no TypeScript errors)
- [ ] Run: `npm run lint` (no ESLint errors)
- [ ] Commit changes
- [ ] Push to GitHub: `git push origin main`
- [ ] Netlify auto-deploys
- [ ] Test on https://tradematrix.netlify.app
- [ ] Verify: Widgets load on production

### Backend Verification (Hetzner)
- [ ] SSH to server
- [ ] Check Celery logs: `docker-compose logs -f celery-worker`
- [ ] Verify: Symbols from database appear in logs
- [ ] Test: Add symbol via production frontend
- [ ] Wait 60s
- [ ] Verify: New symbol in logs

### Documentation Updates
- [ ] Update ARCHITECTURE.md
- [ ] Update PROJECT_OVERVIEW.md
- [ ] Update 00_MASTER_ROADMAP.md
- [ ] Update CLAUDE.md
- [ ] Mark this checklist as complete

**Estimated Time:** 1 hour
**Phase 5 Status:** ⏳ Not Started

---

## 🚨 Blockers & Issues

### Current Blockers
- **Migration 018:** symbols.tv_symbol column not added yet
  - **Impact:** Frontend can't render widgets (no tv_symbol)
  - **Action:** Execute migration in next session

### Resolved Issues
- ✅ Migration 017 executed successfully
- ✅ RLS policies working

### Known Risks
- **TradingView Widget Loading:** Ad blockers may block script
  - **Mitigation:** Show error message, suggest disabling ad blocker
- **Too Many Unique Symbols:** Could hit Twelvedata rate limit
  - **Mitigation:** Implement top-N prioritization (Phase 4)

---

## 📅 Session Plan (Next Session)

### Session 1: Finish Database + Start Frontend (2h)
1. Execute Migration 018 (symbols.tv_symbol)
2. Create tradingview-widget.tsx
3. Create symbol-picker-modal.tsx (basic structure)
4. Test components in isolation

### Session 2: Complete Frontend (2h)
1. Update dashboard/page.tsx
2. Delete market-overview-card.tsx
3. Connect components
4. Test E2E locally

### Session 3: Backend + Deployment (1h)
1. Update alert_engine.py
2. Deploy to Hetzner
3. Test production
4. Update documentation

---

## ✅ Definition of Done

Feature is complete when ALL these are true:

- [ ] User can open Symbol Picker modal
- [ ] User can add up to 10 symbols
- [ ] User can remove symbols
- [ ] Changes persist to database
- [ ] Dashboard shows TradingView widgets
- [ ] Widgets display live prices
- [ ] Backend monitors all unique symbols
- [ ] Alerts still work (unchanged)
- [ ] No TypeScript/ESLint errors
- [ ] Responsive on mobile/tablet/desktop
- [ ] Deployed to Netlify (production)
- [ ] Backend deployed to Hetzner
- [ ] Documentation updated
- [ ] Tests passing

---

## 📝 Notes & Learnings

### Decision Log
- **2025-11-03:** Chose Hybrid approach (TradingView + Alerts) over full WebSocket
  - **Reason:** Simpler, cheaper, faster to implement
  - **Savings:** $29/mo + 2 days development time

### Technical Insights
- TradingView Widgets are free and reliable
- shadcn components make UI development faster
- Supabase RLS simplifies multi-user data isolation
- Celery dynamic symbol loading adds minimal overhead

### Future Enhancements
- **Drag & Drop Reordering:** Use `@dnd-kit/core` library
- **Subscription Limits:** Free = 3, Pro = 10, Expert = 20 symbols
- **Custom Alerts per Symbol:** Price thresholds, % changes
- **Symbol Categories:** Group by type (indices, forex, stocks)

---

**Last Updated:** 2025-11-03
**Next Update:** After Phase 2 completion
