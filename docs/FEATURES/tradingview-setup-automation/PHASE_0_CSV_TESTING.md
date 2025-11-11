# Phase 0: TradingView CSV Data Quality Testing

**Status:** 🔴 CRITICAL - DO THIS FIRST!
**Time:** 1-2 hours
**Cost:** $0 (No subscription needed)
**Goal:** Validate CSV export is usable BEFORE buying TradingView Plus

---

## ⚠️ Why This Matters

**Problem:** We're considering TradingView Plus ($33.95/month) to get CSV exports instead of expensive Vision API screenshots ($0.015 per analysis).

**Risk:** What if CSV data is incomplete/unusable?
- ❌ Missing indicators (EMA, RSI, ATR)
- ❌ Delayed data (15min lag on free tier)
- ❌ Inconsistent format
- ❌ Rate limited

**Solution:** Test with FREE tier FIRST!

---

## 📋 Testing Steps

### Step 1: Manual CSV Export (5 min)

1. Go to TradingView (free account): https://www.tradingview.com
2. Open chart: DAX or XAG/USD, 1h timeframe
3. Add indicators:
   - EMA(20)
   - EMA(50)
   - EMA(200)
   - RSI(14)
   - ATR(14)
4. Click "..." menu → **Export chart data**
5. Save as `tradingview_test_export.csv`

### Step 2: Inspect CSV (10 min)

```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix
head -20 tradingview_test_export.csv
```

**Expected columns:**
```
time,open,high,low,close,volume,ema20,ema50,ema200,rsi,atr
```

**Check:**
- [ ] Does it have timestamp/time column?
- [ ] Does it have OHLC (open, high, low, close)?
- [ ] Does it have indicators (ema20, ema50, rsi, atr)?
- [ ] Are values numeric (not text)?
- [ ] How many rows? (Need at least 100 for analysis)

### Step 3: Parse Test CSV (30 min)

Create test parser:

```python
# test_csv_parser.py

import pandas as pd
from datetime import datetime

def test_tradingview_csv(file_path: str):
    """Test if TradingView CSV has required data."""

    print("=" * 70)
    print("TradingView CSV Quality Test")
    print("=" * 70)

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return False

    print(f"\n📊 CSV Stats:")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Size: {len(df) * len(df.columns)} cells")

    print(f"\n📋 Columns found:")
    for col in df.columns:
        print(f"   - {col}")

    # Check required columns
    required = ['time', 'open', 'high', 'low', 'close']
    missing_required = [col for col in required if col not in df.columns]

    if missing_required:
        print(f"\n❌ MISSING REQUIRED COLUMNS: {missing_required}")
        return False
    else:
        print(f"\n✅ All required columns present")

    # Check optional indicators
    indicators = ['ema20', 'ema50', 'ema200', 'rsi', 'atr']
    found_indicators = [ind for ind in indicators if ind in df.columns]
    missing_indicators = [ind for ind in indicators if ind not in df.columns]

    if found_indicators:
        print(f"\n✅ Indicators included: {found_indicators}")
    else:
        print(f"\n❌ NO INDICATORS found - we'll need to calculate ourselves")

    if missing_indicators:
        print(f"⚠️  Missing indicators: {missing_indicators}")

    # Check data quality
    print(f"\n🔍 Data Quality:")
    print(f"   Null values: {df.isnull().sum().sum()}")
    print(f"   Duplicate rows: {df.duplicated().sum()}")

    # Check OHLC range
    print(f"\n💰 Price Range:")
    print(f"   Low: {df['low'].min():.2f}")
    print(f"   High: {df['high'].max():.2f}")
    print(f"   Latest Close: {df['close'].iloc[-1]:.2f}")

    # Check if data is recent
    if 'time' in df.columns:
        latest_time = df['time'].iloc[-1]
        print(f"\n⏰ Data Freshness:")
        print(f"   Latest timestamp: {latest_time}")

    print(f"\n📈 First 5 rows:")
    print(df.head())

    # Decision
    print("\n" + "=" * 70)
    if not missing_required and len(df) >= 50:
        if found_indicators:
            print("✅ CSV FORMAT IS EXCELLENT!")
            print("   → Proceed with TradingView Plus subscription")
            print("   → Implement CSV parser service")
        else:
            print("✅ CSV FORMAT IS USABLE (but no indicators)")
            print("   → We'll calculate indicators ourselves (Pandas)")
            print("   → Still better than screenshots (exact prices)")
        return True
    else:
        print("❌ CSV FORMAT IS NOT USABLE")
        print("   → SKIP CSV approach")
        print("   → Use Pine Script integration instead")
        return False

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_csv_parser.py <csv_file_path>")
        print("\nExample:")
        print("  python test_csv_parser.py tradingview_test_export.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    test_tradingview_csv(csv_path)
```

### Step 4: Run Test (5 min)

```bash
cd services/agents
python test_csv_parser.py ../../tradingview_test_export.csv
```

---

## 🎯 Decision Matrix

### Scenario 1: CSV Excellent (OHLC + Indicators)
**Result:** ✅ All columns present, indicators included

**Decision:**
- ✅ Buy TradingView Plus ($33.95/month)
- ✅ Implement CSV parser service
- ✅ Cost analysis: Break-even at >2266 analyses/month (>75/day)

**Next Steps:**
1. Subscribe to TradingView Plus
2. Implement `tv_csv_parser.py`
3. Create `/api/charts/upload` endpoint
4. Test with real user data

---

### Scenario 2: CSV Good (OHLC only, no indicators)
**Result:** ✅ OHLC present, ❌ Indicators missing

**Decision:**
- ⚠️ We calculate indicators ourselves (Pandas + TA-Lib)
- ✅ Still better than screenshots (exact prices)
- ✅ Consider TradingView Plus IF high volume (>75 analyses/day)

**Next Steps:**
1. Implement indicator calculation service
2. Test calculation accuracy vs TradingView
3. Decide on subscription based on volume

---

### Scenario 3: CSV Poor (Incomplete/Unusable)
**Result:** ❌ Missing OHLC or < 50 rows

**Decision:**
- ❌ SKIP CSV approach entirely
- ✅ Use **Pine Script** instead (see Phase 0.5)
- ✅ NO TradingView Plus subscription needed

**Next Steps:**
1. Go to Phase 0.5: Pine Script POC
2. Test Pine Script + Webhooks
3. If Pine Script works → Free solution!

---

## 📊 Expected Outcomes

### Best Case
- CSV has OHLC + all indicators
- Data is fresh (< 5 minutes old)
- 100+ rows available
- **→ Proceed with CSV integration (Phase 5)**

### Medium Case
- CSV has OHLC but no indicators
- We calculate indicators ourselves
- **→ Proceed with CSV + indicator calculation**

### Worst Case
- CSV is incomplete/unusable
- **→ SKIP to Pine Script (Phase 0.5)**

---

## 🚀 Next Steps

**After completing Phase 0:**

1. **If CSV is good:**
   - Create JIRA ticket: "Implement TradingView CSV Parser"
   - Estimate: 4-5 hours
   - Dependencies: TradingView Plus subscription

2. **If CSV is poor:**
   - Go to Phase 0.5: Pine Script POC
   - Test Pine Script + Webhooks
   - Estimate: 1-2 hours

3. **Update Documentation:**
   - Document CSV format in `docs/FEATURES/tradingview-setup-automation/CSV_FORMAT.md`
   - Update `README.md` with decision

---

## 🎯 Success Criteria

- [ ] CSV exported successfully
- [ ] CSV has OHLC data
- [ ] CSV has at least 50 rows
- [ ] CSV parsed without errors
- [ ] Decision made: CSV vs Pine Script
- [ ] Next phase planned

---

**Last Updated:** 2025-11-11
**Status:** Ready to execute
**Owner:** User (umi1970) + Claude
