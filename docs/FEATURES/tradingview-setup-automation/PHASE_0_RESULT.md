# Phase 0 Result: CSV Data Quality Test

**Date:** 2025-11-11
**Status:** ✅ COMPLETED
**Decision:** CSV is USABLE (with indicator calculation)

---

## 📊 Test Results

### CSV Format Analysis
- **File:** GER30 (DAX CFD), 5-minute timeframe
- **Rows:** 300 (299 data rows + 1 header)
- **Columns:** 8 (time, OHLC, 3x Plot)

### What's Included ✅
1. **Timestamp** - `time` (ISO 8601 with timezone)
2. **OHLC** - `open, high, low, close` (all numeric, consistent)
3. **EMA 20** - `Plot` column (unnamed)
4. **EMA 50** - `Plot.1` column (pandas renamed it)
5. **EMA 200** - `Plot.2` column (pandas renamed it)

### What's Missing ❌
1. **Volume** - Not exported by TradingView
2. **RSI(14)** - Not in CSV
3. **ATR(14)** - Not in CSV
4. **MACD** - Not in CSV

### Data Quality ✅
- ✅ Zero null values
- ✅ Zero duplicate rows
- ✅ OHLC logic is consistent (High >= Low, Close within range)
- ✅ Data is FRESH (latest bar is 5 minutes old)

### Usability Score: 3/5

**Breakdown:**
- +2 points: Has OHLC with sufficient rows
- +1 point: Data quality is excellent
- +0 points: No labeled indicators (but we confirmed 3x Plot = EMAs)
- -2 points: Missing Volume, RSI, ATR

---

## 🎯 Decision

**CSV Format is USABLE (with limitations)**

### Rationale
1. **OHLC data is perfect** - This is the most critical data
2. **EMAs are included** - Even though unnamed, we confirmed Plot = EMA 20/50/200
3. **Missing indicators can be calculated** - We'll use `pandas_ta` or `ta-lib`
4. **Better than screenshots** - Exact values, no OCR errors, no Vision API cost

### Recommendation
✅ **Proceed with CSV integration**
- Implement CSV parser service
- Calculate RSI + ATR ourselves (pandas_ta)
- NO TradingView Plus subscription needed (free tier is sufficient!)

---

## 💰 Cost Analysis

| Approach | Monthly Cost | Data Quality | Effort |
|----------|--------------|--------------|--------|
| **Screenshots (current)** | ~$18 (Vision API) | ⚠️ OCR errors | Low (existing) |
| **CSV + Calc (chosen)** | $0 (free tier) | ✅ Exact values | Medium (4-5h) |
| **TradingView Plus** | $33.95 | ✅ All indicators | Medium (4-5h) |
| **Pine Script** | $0 (free tier) | ✅ Exact values | High (6-8h) |

**Winner:** CSV + Indicator Calculation
- ✅ $0 cost (saves $18/month vs screenshots)
- ✅ Exact OHLC values
- ✅ No subscription needed
- ⚠️ Need to calculate RSI/ATR (one-time effort)

---

## 📝 Implementation Plan

### Phase 1: CSV Parser Service (2h)
**File:** `services/agents/src/services/tv_csv_parser.py`

**Tasks:**
- [ ] Parse CSV (pandas)
- [ ] Rename Plot columns → ema20, ema50, ema200
- [ ] Validate OHLC consistency
- [ ] Return structured dict (same format as Vision API)

### Phase 2: Indicator Calculator (1-2h)
**File:** `services/agents/src/services/indicator_calculator.py`

**Tasks:**
- [ ] Install pandas_ta: `pip install pandas_ta`
- [ ] Calculate RSI(14): `df.ta.rsi(length=14)`
- [ ] Calculate ATR(14): `df.ta.atr(length=14)`
- [ ] Validate calculations vs TradingView (manual check)

### Phase 3: API Endpoint (1h)
**File:** `apps/web/src/app/api/charts/upload/route.ts`

**Tasks:**
- [ ] Accept CSV upload (FormData)
- [ ] Upload to Supabase Storage
- [ ] Call FastAPI parser service
- [ ] Create setup in DB (same as screenshots)
- [ ] Return analysis result

### Phase 4: Frontend UI (1h)
**File:** `apps/web/src/app/(dashboard)/charts/page.tsx`

**Tasks:**
- [ ] CSV upload dropzone
- [ ] File validation (CSV only, max 10MB)
- [ ] Loading state
- [ ] Display analysis result
- [ ] Link to setup page

**Total Estimate:** 5-6 hours

---

## 🧪 Testing Plan

### Unit Tests
- [ ] `test_csv_parser.py` - Parse various CSV formats
- [ ] `test_indicator_calculator.py` - Verify RSI/ATR accuracy

### Integration Tests
- [ ] Upload CSV → Parse → Calculate → Create Setup
- [ ] Compare CSV-based setup vs Screenshot-based setup
- [ ] Verify indicator calculations match TradingView

### Manual Testing
1. Export 3 CSV files (1m, 5m, 15m) from TradingView
2. Upload each via /charts page
3. Verify:
   - OHLC values exact match
   - EMAs correct (compare with TradingView chart)
   - RSI/ATR within 1% of TradingView values
   - Setup created with correct Entry/SL/TP

---

## 🚀 Next Steps

1. ✅ **Phase 0 completed** - CSV format validated
2. **Start Phase 1:** Implement CSV parser service
3. **Start Phase 2:** Implement indicator calculator
4. **Start Phase 3:** Create API endpoint
5. **Start Phase 4:** Build frontend UI
6. **Deploy:** Test with real user data

**Expected timeline:** 5-6 hours (1 day of focused work)

---

## ❓ Open Questions

### Q1: Should we support multiple CSV formats?
**Answer:** Start with TradingView format only. Can extend later if needed.

### Q2: What if indicator calculations don't match TradingView?
**Answer:** Accept ±2% variance. TradingView uses proprietary calculations that may differ slightly.

### Q3: Should we still keep screenshot analysis?
**Answer:** YES! Users who don't have TradingView can still use screenshots. CSV is an additional option, not a replacement.

### Q4: What about other symbols (not just GER30)?
**Answer:** CSV format should be the same. Test with at least 3 different symbols before going live.

---

## 📚 Related Documentation

- [Phase 0 CSV Testing Guide](./PHASE_0_CSV_TESTING.md)
- [TradingView Setup Automation README](./README.md)
- [Vision Screenshot Analysis](../vision-screenshot/README.md)

---

**Test Conducted By:** Claude + User (umi1970)
**Last Updated:** 2025-11-11
**Status:** ✅ CSV approach validated and approved
