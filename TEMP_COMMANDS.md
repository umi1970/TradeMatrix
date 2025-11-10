# Aktuelle Commands (Copy/Paste)

Commands für **JETZT** - copy/paste direkt ins Terminal:

---

## 1. Frontend Build & Test

```bash
cd apps/web
npm run build
```

Wenn erfolgreich, Netlify deployed automatisch (git push wurde gemacht).

---

## 2. Screenshot Analysis testen

1. **Gehe zu:** https://tradematrix.netlify.app/dashboard/screenshots
2. **Upload dow5m.png** (oder andere Chart-Screenshots)
3. **Klick "Analyze Screenshots"**
4. **Warte 10-20 Sekunden** (Vision AI analysiert)

---

## 3. Was Vision AI JETZT alles erkennt (ENHANCED!)

### ✅ Basic Data
- Symbol, Timeframe, OHLC, Current Price, Timestamp

### ✅ Technical Indicators
- EMA20, EMA50, EMA200, RSI
- Pivot Points (R3, R2, R1, PP, S1, S2, S3)
- Other indicators (MACD, VWAP, etc.)

### ✅ Support/Resistance Levels
- Horizontal lines, Swing highs/lows, Consolidation zones

### ✅ Trend Analysis (IMPROVED!)
- **Trend:** bullish/bearish/sideways
- **Trend Strength:** strong/moderate/weak
- **Price vs EMAs:** above_all, below_all, mixed ⭐ NEW!
- **Momentum Bias:** Textual summary (e.g. "bullish momentum slowing near resistance") ⭐ NEW!

### ✅ Price Action & Patterns
- **Patterns:** double_top, breakout, rejection, range, etc.
- **Key Events:** 2-3 bullet points describing recent price actions
- **Market Structure:** higher_highs, lower_lows, range_bound, mixed

### ✅ Trading Setup (ENHANCED!)
- **Setup Type:** long/short/no_trade
- **Entry, Stop, Target:** Precise levels
- **Risk:Reward Ratio** ⭐ NEW!
- **Reasoning:** 2-3 sentences explaining the logic
- **Timeframe Validity:** intraday, swing, midterm ⭐ NEW!

### ✅ Confidence & Quality (IMPROVED!)
- **Confidence Score:** 0.0-1.0
- **Chart Quality:** excellent, good, fair, poor
- **Key Factors:** 2-3 factors influencing confidence ⭐ NEW!
  - Example: "clear EMA confluence", "low volume", "strong rejection"

---

## 4. UI Improvements

**Jetzt zeigt die UI:**
- ✅ Trend + Trend Strength badges
- ✅ Momentum Bias + Price vs EMAs (info box)
- ✅ Patterns as badges
- ✅ Key Factors as bullet points
- ✅ Chart Quality label
- ✅ Timeframe Validity in setup card
- ✅ R:R Ratio (4-column grid: Entry, Stop, Target, R:R)

---

## 5. Technical Improvements

**Backend:**
- ✅ `temperature: 0.2` → Stable numeric values (kein Halluzinieren)
- ✅ Backup Heuristic: confidence=0.0 → 0.4 (wenn Daten vorhanden)
- ✅ Stricter JSON rules (kein Markdown wrapping)

**Prompt:**
- ✅ Optimierte Struktur (vom User)
- ✅ Klarere Anweisungen (nie Zahlen erfinden!)
- ✅ ML-ready Pattern-Namen

---

## 6. Workflow (komplett automatisiert!)

```
1. Mache Screenshots (30 Sek für 5-10 Charts)
2. Upload auf /screenshots
3. Vision analysiert ALLES (10-20 Sek pro Chart)
4. Schreibt in chart_analyses
5. Klick "Generate Setup" → SetupGenerator nutzt die Daten
6. FERTIG! Vollständiges Trading Setup
```

---

## 7. Kosten

**OpenAI Vision (GPT-4o) mit temperature=0.2:**
- ~$0.015 pro Bild (mit 2000 tokens Output)
- 10 Charts/Tag = $0.15/Tag = $4.50/Monat
- 50 Charts/Tag = $0.75/Tag = $22.50/Monat

**VIEL günstiger als:**
- Alpha Vantage: $49.99/mo ❌
- Finnhub Premium: $59.99/mo ❌
- Polygon.io: $89/mo ❌

---

## 8. Beispiel Output für dow5m.png

```json
{
  "symbol": "Dow Jones",
  "timeframe": "5m",
  "current_price": 47036.54,
  "trend": "bearish",
  "trend_strength": "strong",
  "price_vs_emas": "below_all",
  "momentum_bias": "Strong bearish momentum after 350-point crash, price below all EMAs",
  "confidence_score": 0.85,
  "chart_quality": "excellent",
  "key_factors": [
    "Clear EMA confluence below price",
    "Strong rejection from 47,300",
    "Sharp volume spike on crash"
  ],
  "setup_type": "short",
  "entry_price": 47000,
  "stop_loss": 47300,
  "take_profit": 46850,
  "risk_reward": 2.0,
  "reasoning": "Sharp rejection after uptrend, price broke below all EMAs. Entry on pullback to 47,000 with stop above structure at 47,300. Target previous support at 46,850 (2:1 R:R).",
  "timeframe_validity": "intraday",
  "patterns_detected": ["crash", "rejection", "breakdown"],
  "support_levels": [46950, 46851],
  "resistance_levels": [47073, 47300]
}
```

---
