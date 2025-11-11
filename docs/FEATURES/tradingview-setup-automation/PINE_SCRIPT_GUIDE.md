# TradingView Pine Script Integration Guide

**Purpose:** Generate perfect CSV exports with ALL indicators needed for AI analysis

---

## 📝 Pine Script: TradeMatrix AI Indicators

**File:** `config/pinescript/tradematrix_ai_indicators.pine`

**What it does:**
- Calculates 23 indicators optimized for AI analysis
- Outputs ALL values as plots (exportable in CSV)
- No manual calculation needed in Python!

---

## 🎯 Indicators Included

### 1. Trend Indicators
- **EMA 20, 50, 200** - Exponential Moving Averages
- **MACD (12,26,9)** - Line, Signal, Histogram
- **ADX(14)** - Trend Strength (+ DI+, DI-)

### 2. Momentum Indicators
- **RSI(14)** - Relative Strength Index
- **Price vs EMA %** - Distance from EMAs as percentage

### 3. Volatility Indicators
- **ATR(14)** - Average True Range
- **Bollinger Bands (20,2)** - Upper, Middle, Lower
- **Volatility %** - ATR as % of price

### 4. Support/Resistance
- **Pivot Points** - Daily PP, R1, R2, S1, S2
- **Pivot Timeframe** - Customizable (default: Daily)

### 5. Volume
- **Volume** - Trading volume per bar

---

## 📊 CSV Export Format

After adding Pine Script to your chart and exporting, CSV will have:

```csv
time,open,high,low,close,EMA_20,EMA_50,EMA_200,RSI_14,ATR_14,MACD_Line,MACD_Signal,MACD_Histogram,BB_Upper,BB_Middle,BB_Lower,Pivot_Point,Resistance_1,Support_1,Resistance_2,Support_2,ADX_14,DI_Plus,DI_Minus,Volume,Price_vs_EMA20_Pct,Price_vs_EMA50_Pct,Price_vs_EMA200_Pct,Volatility_Pct
2025-11-11T10:00:00+01:00,24000.5,24020.3,23990.2,24015.8,24010.2,23980.5,23850.3,68.5,45.2,12.3,8.5,3.8,24080.5,24010.2,23940.0,23995.5,24050.2,23940.8,24105.0,23886.0,28.5,25.3,18.7,125000,0.02,0.18,0.71,0.19
...
```

**Total:** 28 columns (5 OHLC + 23 indicators)

---

## 🚀 Setup Instructions

### Step 1: Add Pine Script to TradingView

1. Open TradingView chart (any symbol, any timeframe)
2. Click **Pine Editor** (bottom of screen)
3. Copy entire content of `config/pinescript/tradematrix_ai_indicators.pine`
4. Paste into Pine Editor
5. Click **"Add to Chart"**

### Step 2: Configure Settings (Optional)

**Default settings are optimized for AI analysis**, but you can customize:

- **EMA Lengths:** 20, 50, 200 (standard)
- **RSI Length:** 14 (standard)
- **RSI Levels:** 70 (overbought), 30 (oversold)
- **ATR Length:** 14 (standard)
- **MACD:** 12, 26, 9 (standard)
- **Bollinger Bands:** 20 period, 2 StdDev (standard)
- **ADX Length:** 14 (standard)
- **Pivot Timeframe:** D (daily) - change to W for weekly, M for monthly

### Step 3: Export CSV

1. Chart is now showing all indicators
2. Click **"..." menu** (top right)
3. Select **"Export chart data..."**
4. Save as CSV (e.g., `GER30_5m_ai_indicators.csv`)

### Step 4: Upload to TradeMatrix

1. Go to TradeMatrix → `/charts` page
2. Upload CSV
3. System automatically parses ALL indicators
4. Setup is generated with perfect indicator values!

---

## 📋 CSV Columns Explained

| Column | Description | Usage |
|--------|-------------|-------|
| **time** | Timestamp (ISO 8601) | Bar timestamp |
| **open, high, low, close** | OHLC prices | Candle data |
| **EMA_20, EMA_50, EMA_200** | Moving averages | Trend direction |
| **RSI_14** | Momentum (0-100) | Overbought/Oversold |
| **ATR_14** | Volatility (points) | Stop loss sizing |
| **MACD_Line, MACD_Signal** | Momentum trend | Crossovers |
| **MACD_Histogram** | Momentum strength | Divergence |
| **BB_Upper, BB_Middle, BB_Lower** | Volatility bands | Breakout detection |
| **Pivot_Point** | Key level | Support/Resistance |
| **Resistance_1, Support_1** | First levels | TP/SL targets |
| **Resistance_2, Support_2** | Second levels | Extended targets |
| **ADX_14** | Trend strength (0-100) | >25 = strong trend |
| **DI_Plus, DI_Minus** | Directional indicators | Trend direction |
| **Volume** | Trading volume | Confirmation |
| **Price_vs_EMA20_Pct** | Distance from EMA20 (%) | Overbought/Oversold |
| **Price_vs_EMA50_Pct** | Distance from EMA50 (%) | Mean reversion |
| **Price_vs_EMA200_Pct** | Distance from EMA200 (%) | Long-term trend |
| **Volatility_Pct** | ATR as % of price | Relative volatility |

---

## 🔍 AI Analysis Usage

### Trend Detection
```python
if ema20 > ema50 > ema200 and adx > 25:
    trend = "strong_bullish"
elif ema20 < ema50 < ema200 and adx > 25:
    trend = "strong_bearish"
elif adx < 25:
    trend = "sideways"
```

### Entry/Exit Calculation
```python
# Long Setup
if rsi < 30 and price_vs_ema20_pct < -1.0:
    entry = close
    stop_loss = support_1  # From pivot points
    take_profit = resistance_1  # From pivot points

# ATR-based SL/TP
stop_loss_atr = close - (atr * 1.5)
take_profit_atr = close + (atr * 3.0)  # 2:1 R:R
```

### Confidence Scoring
```python
confidence = 0.0

# Trend alignment (+30%)
if ema20 > ema50 > ema200:
    confidence += 0.3

# Momentum confirmation (+20%)
if 30 < rsi < 70 and macd_histogram > 0:
    confidence += 0.2

# Volatility check (+10%)
if volatility_pct < 1.0:  # Low volatility
    confidence += 0.1

# Volume confirmation (+10%)
if volume > avg_volume:
    confidence += 0.1

# ADX strong trend (+20%)
if adx > 25:
    confidence += 0.2

# Bollinger position (+10%)
if close > bb_middle:
    confidence += 0.1

# Total: 0.0 - 1.0
```

---

## 🎨 Visualization

### Indicator Panel Layout

**Panel 1: Trend (overlay=true on price chart)**
- EMA 20 (yellow)
- EMA 50 (blue)
- EMA 200 (red)
- Bollinger Bands (green/red)
- Pivot Points (white + colored circles)

**Panel 2: Momentum (separate panel)**
- RSI (purple)
- Overbought/Oversold lines (70/30)

**Panel 3: MACD (separate panel)**
- MACD Line (blue)
- Signal Line (orange)
- Histogram (gray bars)

**Panel 4: Trend Strength (separate panel)**
- ADX (navy)
- DI+ (green)
- DI- (red)

**Panel 5: Volume (separate panel)**
- Volume bars (blue)

---

## 🧪 Testing & Validation

### Step 1: Visual Verification
1. Add Pine Script to chart
2. Compare indicator values with built-in TradingView indicators
3. Verify RSI, MACD, Bollinger Bands match exactly

### Step 2: CSV Export Test
1. Export CSV for GER30 5m
2. Open in Excel/Google Sheets
3. Check columns:
   - ✅ All 28 columns present?
   - ✅ No null values?
   - ✅ Numeric values correct?

### Step 3: AI Analysis Test
1. Upload CSV to TradeMatrix
2. Compare setup generation:
   - CSV-based setup vs Screenshot-based setup
   - Verify Entry/SL/TP calculations match
   - Confirm confidence scores are reasonable

---

## 💡 Pro Tips

### Tip 1: Multiple Timeframes
Export CSV for different timeframes to analyze confluence:
- 5m chart → Short-term setups
- 15m chart → Intraday setups
- 1h chart → Swing setups
- Daily chart → Long-term setups

AI can analyze multiple timeframes and increase confidence if all align!

### Tip 2: Symbol Watchlist
Create template with Pine Script for all symbols:
- GER30 (DAX)
- US30 (Dow Jones)
- NAS100 (NASDAQ)
- XAG/USD (Silver)
- XAU/USD (Gold)

Export all → Upload batch → AI analyzes all at once!

### Tip 3: Custom Indicators
Modify Pine Script to add YOUR custom indicators:
```pine
// Custom: Price Distance from Daily Open
dailyOpen = request.security(syminfo.tickerid, "D", open, lookahead=barmerge.lookahead_on)
priceVsDailyOpen = ((close - dailyOpen) / dailyOpen) * 100
plot(priceVsDailyOpen, title="Price_vs_Daily_Open_Pct")
```

### Tip 4: Alerts for Automation
Uncomment alert lines in Pine Script to get TradingView alerts:
- RSI Oversold/Overbought
- MACD Crossovers
- ADX Strong Trend

Configure alerts → Webhook to TradeMatrix → Automated analysis!

---

## 🚧 Troubleshooting

### Problem 1: Pine Script won't compile
**Solution:** Check TradingView version
- Script requires `//@version=5`
- If using older TradingView, upgrade or use compatibility mode

### Problem 2: CSV missing columns
**Solution:** All plots must be added to chart
- Click **"Add to Chart"** (not just save)
- Verify indicator panel shows all plots
- Re-export CSV

### Problem 3: Pivot Points show wrong values
**Solution:** Check timeframe setting
- Default: Daily pivots
- Change `pivotTimeframe` input to "W" (weekly) or "M" (monthly)
- Higher timeframes update less frequently

### Problem 4: Volume is 0 or missing
**Solution:** Some symbols don't have volume data
- Forex pairs: No volume (use tick volume)
- CFDs: Some brokers don't provide volume
- This is expected, AI will work without volume

---

## 📊 Comparison: Before vs After Pine Script

| Feature | Before (Screenshots) | After (Pine Script CSV) |
|---------|---------------------|-------------------------|
| **Data Source** | Vision API OCR | Exact TradingView values |
| **Indicators** | Limited (visible only) | 23+ indicators |
| **Accuracy** | ⚠️ OCR errors | ✅ 100% accurate |
| **Cost** | $0.015/analysis | $0 (free CSV export) |
| **Speed** | 3-5 seconds (Vision API) | <1 second (CSV parse) |
| **Reliability** | ⚠️ Depends on image quality | ✅ Always consistent |
| **Customization** | ❌ Fixed to screenshot | ✅ Unlimited indicators |
| **Automation** | ❌ Manual screenshot | ✅ Batch export possible |

**Winner:** Pine Script + CSV Export 🏆

---

## 🎯 Next Steps

1. ✅ **Add Pine Script to TradingView chart**
2. ✅ **Export 3 test CSVs** (1m, 5m, 15m)
3. ⏳ **Implement CSV Parser** (parse 28 columns)
4. ⏳ **Update AI Analysis** (use all 23 indicators)
5. ⏳ **Deploy to production**

**Estimated Time:** 4-6 hours (parser + AI integration)

---

## 📚 Related Documentation

- [Phase 0 Result: CSV Validation](./PHASE_0_RESULT.md)
- [TradingView Setup Automation README](./README.md)
- [AI Analysis Service](../../../services/agents/README.md)

---

**Created:** 2025-11-11
**Author:** Claude + User (umi1970)
**Status:** Ready for implementation
