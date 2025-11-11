# TradingView Setup Automation

**Status:** 📋 Planning
**Priority:** High
**Estimated Time:** 12-16 hours
**Created:** 2025-11-11
**Last Updated:** 2025-11-11

---

## 📋 Inhaltsverzeichnis
1. [Overview](#overview)
2. [User Story](#user-story)
3. [Complete Flow](#complete-flow)
4. [Technical Architecture](#technical-architecture)
5. [Database Schema](#database-schema)
6. [Implementation Phases](#implementation-phases)
7. [Open Questions](#open-questions)

---

## 🎯 Overview

Automatische Setup-Erstellung aus TradingView Alerts:
- User setzt Alert in TradingView
- Alert sendet historische Chart-Daten (100 bars OHLC) via Webhook
- AI analysiert Daten → berechnet Entry/SL/TP
- Setup wird in DB erstellt
- Setup-Monitoring startet automatisch (Entry/SL/TP Tracking)

**Ziel:** User braucht keine Screenshots mehr hochladen, TradingView Alert reicht!

---

## 👤 User Story

### Ausgangssituation
User hat TradingView Pro Account und nutzt TradeMatrix für Trading-Analysen.

### Problem
- Screenshot-Upload ist umständlich (speichern, hochladen, löschen)
- User will schnell AI-Feedback zu Trade-Ideen

### Lösung
```
User sieht Trade-Chance in TradingView Chart
    ↓
User setzt Alert (1 Klick)
    ↓
Alert triggered → Webhook an TradeMatrix
    ↓
AI analysiert automatisch
    ↓
Setup erstellt + Monitoring aktiv
    ↓
Push Notification: "✅ Setup erstellt - DAX Long @ 19.500"
```

### Benefit
- ⚡ Schneller (1 Klick statt 5 Schritte)
- 🤖 Automatisch (kein manueller Upload)
- 📊 Bessere Daten (100 bars statt 1 Screenshot)
- 🔔 Real-time Monitoring (Entry/SL/TP Alerts)

---

## 🔄 Complete Flow

### Phase 1: Setup Creation (TradingView → TradeMatrix)

```
┌─────────────────────────────────────────────────┐
│ 1. USER SETZT ALERT IN TRADINGVIEW            │
├─────────────────────────────────────────────────┤
│ - Alert Condition: z.B. "Price crosses EMA 20" │
│ - Alert Actions: Webhook URL aktivieren        │
│ - Message: Pine Script JSON (100 bars OHLC)    │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 2. ALERT TRIGGERED                             │
├─────────────────────────────────────────────────┤
│ TradingView sendet HTTP POST an:               │
│ https://tradematrix.ai/api/webhooks/tradingview│
│                                                 │
│ Payload (JSON):                                 │
│ {                                               │
│   "ticker": "DAX",                              │
│   "interval": "1h",                             │
│   "bars": [                                     │
│     {"open": 19480, "high": 19520, ...},        │
│     {"open": 19500, "high": 19530, ...},        │
│     ... (100 bars)                              │
│   ]                                             │
│ }                                               │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 3. TRADEMATRIX WEBHOOK EMPFÄNGT DATEN          │
├─────────────────────────────────────────────────┤
│ Backend: /api/webhooks/tradingview/route.ts    │
│ - Validiert JSON                                │
│ - Parsed OHLC Daten                             │
│ - Findet symbol_id in market_symbols            │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 4. AI ANALYSIS SERVICE                          │
├─────────────────────────────────────────────────┤
│ FastAPI: /api/analyze-ohlc                      │
│                                                 │
│ Analysiert 100 bars:                            │
│ ✓ Trend Detection (Higher Highs/Lows)          │
│ ✓ Support/Resistance Levels                    │
│ ✓ Pattern Recognition (Flags, Triangles)       │
│ ✓ Volume Confirmation                          │
│ ✓ Entry/SL/TP Calculation                      │
│ ✓ Confidence Score (0.0-1.0)                    │
│                                                 │
│ Returns:                                        │
│ {                                               │
│   "side": "long",                               │
│   "entry_price": 19500,                         │
│   "stop_loss": 19450,                           │
│   "take_profit": 19600,                         │
│   "confidence": 0.85,                           │
│   "reasoning": "Bullish trend + support..."     │
│ }                                               │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 5. SETUP CREATION IN DATABASE                  │
├─────────────────────────────────────────────────┤
│ INSERT INTO setups:                             │
│ - module: 'tradingview'                         │
│ - symbol_id: (DAX UUID)                         │
│ - strategy: 'tv_alert'                          │
│ - side: 'long'                                  │
│ - entry_price: 19500                            │
│ - stop_loss: 19450                              │
│ - take_profit: 19600                            │
│ - confidence: 0.85                              │
│ - status: 'pending'                             │
│ - payload: {ohlc_data, reasoning, ...}          │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ 6. PINE SCRIPT GENERATOR                        │
├─────────────────────────────────────────────────┤
│ Generiert Pine Script für Setup-Monitoring:     │
│ - Zeichnet Entry/SL/TP Linien im Chart         │
│ - Alerts bei Price Touch:                       │
│   → entry_hit                                   │
│   → sl_hit                                      │
│   → tp_hit                                      │
│                                                 │
│ User kopiert Code → TradingView Pine Editor    │
└─────────────────────────────────────────────────┘
```

### Phase 2: Setup Monitoring (Price Tracking)

```
┌─────────────────────────────────────────────────┐
│ 7. SETUP MONITORING AKTIV                      │
├─────────────────────────────────────────────────┤
│ Pine Script überwacht Setup 24/7:              │
│                                                 │
│ IF price crosses entry_price:                   │
│   → Webhook: entry_hit                          │
│   → Status: pending → entry_hit                 │
│   → Alert: "✅ Entry Hit - DAX @ 19.500"        │
│                                                 │
│ IF price crosses stop_loss:                     │
│   → Webhook: sl_hit                             │
│   → Status: entry_hit → sl_hit                  │
│   → Outcome: "loss" (if entry hit)              │
│   → Outcome: "invalidated" (if no entry)        │
│   → Alert: "❌ SL Hit - DAX @ 19.450"           │
│                                                 │
│ IF price crosses take_profit:                   │
│   → Webhook: tp_hit                             │
│   → Status: entry_hit → tp_hit                  │
│   → Outcome: "win" (if entry hit)               │
│   → Outcome: "missed" (if no entry)             │
│   → Alert: "✅ TP Hit - DAX @ 19.600"           │
└─────────────────────────────────────────────────┘
```

---

## 🏗️ Technical Architecture

### Components

```
┌──────────────────────────────────────────────────┐
│                  TRADINGVIEW                     │
│  - User setzt Alerts                             │
│  - Pine Script generiert JSON (100 bars)         │
│  - Webhooks senden Daten                         │
└────────────────┬─────────────────────────────────┘
                 │ HTTP POST
                 ↓
┌──────────────────────────────────────────────────┐
│              NEXT.JS FRONTEND                    │
│  Route: /api/webhooks/tradingview/route.ts      │
│  - Empfängt Webhook                              │
│  - Validiert JSON                                │
│  - Ruft FastAPI auf                              │
└────────────────┬─────────────────────────────────┘
                 │ HTTP POST
                 ↓
┌──────────────────────────────────────────────────┐
│               FASTAPI BACKEND                    │
│  Endpoint: POST /api/analyze-ohlc                │
│  - AI Analysis (OpenAI GPT-4)                    │
│  - Technical Indicators (pandas_ta)              │
│  - Entry/SL/TP Calculation                       │
└────────────────┬─────────────────────────────────┘
                 │ Returns Analysis
                 ↓
┌──────────────────────────────────────────────────┐
│            SUPABASE DATABASE                     │
│  Table: setups                                   │
│  - INSERT new setup                              │
│  - status: 'pending'                             │
└────────────────┬─────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────┐
│         PINE SCRIPT MONITORING                   │
│  - User kopiert generierten Code                 │
│  - Pine Script überwacht Entry/SL/TP             │
│  - Webhooks bei Hit                              │
└──────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### Option A: Migration (neue Spalten) - EMPFOHLEN

**Neue Spalten für `setups` Tabelle:**

```sql
-- Setup Monitoring Fields
ALTER TABLE setups ADD COLUMN entry_hit BOOLEAN DEFAULT false;
ALTER TABLE setups ADD COLUMN entry_hit_at TIMESTAMPTZ;
ALTER TABLE setups ADD COLUMN sl_hit_at TIMESTAMPTZ;
ALTER TABLE setups ADD COLUMN tp_hit_at TIMESTAMPTZ;
ALTER TABLE setups ADD COLUMN outcome TEXT CHECK (outcome IN ('win', 'loss', 'invalidated', 'missed'));
ALTER TABLE setups ADD COLUMN pnl_percent NUMERIC(6,2);

-- Monitoring Metadata
ALTER TABLE setups ADD COLUMN last_price NUMERIC;
ALTER TABLE setups ADD COLUMN last_checked_at TIMESTAMPTZ;

-- Pine Script Integration
ALTER TABLE setups ADD COLUMN pine_script TEXT;
ALTER TABLE setups ADD COLUMN pine_script_active BOOLEAN DEFAULT false;

-- Extend status enum
ALTER TABLE setups DROP CONSTRAINT IF EXISTS setups_status_check;
ALTER TABLE setups ADD CONSTRAINT setups_status_check
  CHECK (status IN ('pending', 'active', 'invalid', 'filled', 'cancelled',
                    'entry_hit', 'sl_hit', 'tp_hit', 'expired'));
```

**Vorteile:**
- ✅ Bessere Performance (indexed columns)
- ✅ Type Safety
- ✅ Einfachere Queries
- ✅ Klare Schema-Definition

**Nachteile:**
- ❌ Braucht Migration
- ❌ Weniger flexibel

---

### Option B: JSONB payload (keine Migration)

**Nutzt bestehendes `payload` JSONB Feld:**

```json
{
  "monitoring": {
    "entry_hit": true,
    "entry_hit_at": "2025-11-11T10:30:00Z",
    "sl_hit_at": null,
    "tp_hit_at": "2025-11-11T14:20:00Z",
    "outcome": "win",
    "pnl_percent": 2.5,
    "last_price": 19600,
    "last_checked_at": "2025-11-11T14:20:05Z"
  },
  "pine_script": "...",
  "pine_script_active": true,
  "ohlc_data": [...],
  "ai_reasoning": "Bullish trend confirmation..."
}
```

**Vorteile:**
- ✅ Keine Migration nötig
- ✅ Sehr flexibel
- ✅ Kann jederzeit erweitert werden

**Nachteile:**
- ❌ Langsamere Queries (JSONB parsing)
- ❌ Keine Type Safety
- ❌ Komplexere WHERE clauses

---

### 🤔 ENTSCHEIDUNG NÖTIG!

**Frage an User:** Option A (Migration) oder Option B (JSONB)?

---

## 📝 Implementation Phases

### Phase 0: Planning & Schema Decision (AKTUELL)
- [x] Feature dokumentieren
- [ ] **Schema-Entscheidung:** Migration vs JSONB
- [ ] API Endpoints designen
- [ ] Pine Script Templates erstellen

---

### Phase 1: Webhook Endpoint (2-3h)

**File:** `apps/web/src/app/api/webhooks/tradingview/route.ts`

```typescript
export async function POST(request: NextRequest) {
  // 1. Parse JSON payload
  // 2. Validate required fields (ticker, interval, bars)
  // 3. Find symbol_id in market_symbols
  // 4. Call FastAPI analyze-ohlc
  // 5. Create setup in DB
  // 6. Return response
}
```

**Tasks:**
- [ ] Route erstellen
- [ ] JSON validation
- [ ] Symbol lookup
- [ ] Error handling
- [ ] Tests

---

### Phase 2: AI Analysis Service (4-5h)

**File:** `services/api/src/api/analyze_ohlc.py`

```python
@router.post("/analyze-ohlc")
async def analyze_ohlc(data: OHLCRequest):
    # 1. Parse OHLC bars
    # 2. Calculate indicators (EMA, RSI, etc.)
    # 3. Detect trend
    # 4. Find support/resistance
    # 5. Calculate Entry/SL/TP
    # 6. Generate confidence score
    # 7. Return analysis
```

**AI Analysis Steps:**
1. **Trend Detection:**
   - Higher Highs & Higher Lows = Bullish
   - Lower Highs & Lower Lows = Bearish

2. **Support/Resistance:**
   - Recent swing highs/lows
   - Previous day high/low

3. **Entry Calculation:**
   - Long: Break above recent high
   - Short: Break below recent low

4. **SL/TP Calculation:**
   - SL: Below support (long) / Above resistance (short)
   - TP: 2:1 Risk/Reward minimum

5. **Confidence Score:**
   - 0.85+ = Strong setup (clear trend + volume)
   - 0.70-0.85 = Good setup
   - 0.50-0.70 = Moderate setup
   - <0.50 = Weak setup (reject)

**Tasks:**
- [ ] Endpoint erstellen
- [ ] OHLC Parser
- [ ] Indicator calculation (pandas_ta)
- [ ] Trend detection logic
- [ ] Entry/SL/TP calculator
- [ ] Confidence scoring
- [ ] OpenAI integration (reasoning)
- [ ] Tests

---

### Phase 3: Pine Script Generator (2-3h)

**File:** `services/api/src/services/pine_script_generator.py`

Generiert Pine Script Code für Setup-Monitoring:

```pinescript
//@version=5
indicator("TradeMatrix Setup - DAX Long", overlay=true)

// Setup Levels
entryPrice = 19500
stopLoss = 19450
takeProfit = 19600

// Draw Lines
line.new(bar_index, entryPrice, bar_index + 100, entryPrice,
         color=color.green, width=2)
line.new(bar_index, stopLoss, bar_index + 100, stopLoss,
         color=color.red, width=2)
line.new(bar_index, takeProfit, bar_index + 100, takeProfit,
         color=color.blue, width=2)

// Entry Hit Alert
if ta.cross(close, entryPrice)
    alert('{"setup_id": "...uuid...", "event": "entry_hit", "price": ' +
          str.tostring(close) + '}', alert.freq_once_per_bar)

// SL Hit Alert
if close <= stopLoss
    alert('{"setup_id": "...uuid...", "event": "sl_hit", "price": ' +
          str.tostring(close) + '}', alert.freq_once_per_bar)

// TP Hit Alert
if close >= takeProfit
    alert('{"setup_id": "...uuid...", "event": "tp_hit", "price": ' +
          str.tostring(close) + '}', alert.freq_once_per_bar)
```

**Tasks:**
- [ ] Generator function
- [ ] Template erstellen
- [ ] Dynamic values injection
- [ ] Webhook URL in alerts
- [ ] Tests

---

### Phase 4: Monitoring Webhook (2h)

**File:** `apps/web/src/app/api/webhooks/tradingview-monitor/route.ts`

Empfängt Monitoring-Webhooks (entry_hit, sl_hit, tp_hit):

```typescript
export async function POST(request: NextRequest) {
  const { setup_id, event, price } = await request.json()

  // Update setup based on event
  // Send push notification
  // Calculate P&L if needed
}
```

**Tasks:**
- [ ] Route erstellen
- [ ] Event handling (entry_hit, sl_hit, tp_hit)
- [ ] Setup status updates
- [ ] P&L calculation
- [ ] Push notifications
- [ ] Tests

---

### Phase 5: Frontend Integration (2-3h)

**Components:**
1. **Setup Display** (agents/page.tsx) - zeigt Pine Script
2. **Copy Button** - kopiert Pine Script in Clipboard
3. **Monitoring Status** - zeigt Entry/SL/TP Status
4. **Outcome Badge** - WIN/LOSS/INVALIDATED

**Tasks:**
- [ ] Pine Script anzeigen
- [ ] Copy to clipboard button
- [ ] Monitoring status indicators
- [ ] Outcome badges
- [ ] Tests

---

### Phase 6: Testing & Deployment (2h)

**Tests:**
- [ ] Unit tests (AI analysis)
- [ ] Integration tests (Webhook → DB)
- [ ] E2E test (TradingView → Setup → Monitoring)
- [ ] Manual testing mit echtem TradingView Alert

**Deployment:**
- [ ] Migration auf Netlify
- [ ] FastAPI update auf Railway
- [ ] Dokumentation aktualisieren

---

## ✅ Decisions Made

### 1. Schema Decision
**Entscheidung:** ✅ **Option A: Migration (neue Spalten)**
- Migration 030 erstellt: `services/api/supabase/migrations/030_setup_monitoring.sql`
- 10 neue Spalten: entry_hit, entry_hit_at, sl_hit_at, tp_hit_at, outcome, pnl_percent, last_price, last_checked_at, pine_script, pine_script_active
- 4 Performance Indexes
- 2 Helper Views: active_setups, completed_setups
- 3 Helper Functions: calculate_pnl_percent, get_setup_stats, expire_old_setups

### 2. AI Model Wahl
**Entscheidung:** ✅ **GPT-4o-mini** (fallback: GPT-4o)
- Beste Balance: Qualität vs Kosten
- 80% günstiger als GPT-4
- Ausreichend für Technical Analysis

### 3. Minimum Confidence Threshold
**Entscheidung:** ✅ **0.60 (balanced)**
- Nicht zu konservativ (0.70)
- Nicht zu aggressiv (0.50)
- User kann später in Settings anpassen

### 4. Alert Delivery
**Entscheidung:** ✅ **Browser Push Notifications**
- Nutzt existierende Infrastruktur (Hetzner Celery Worker)
- Bereits live und getestet
- Email + WhatsApp in späteren Phases

---

## 📊 Success Metrics

- [ ] Setup-Erstellung funktioniert (TradingView → TradeMatrix)
- [ ] AI Analysis läuft (<5s Response Time)
- [ ] Pine Script generiert korrekt
- [ ] Monitoring Webhooks funktionieren
- [ ] User kann Setup-Outcomes sehen (WIN/LOSS)
- [ ] Push Notifications bei Entry/SL/TP Hit

---

## 🚀 Next Steps

1. **User entscheidet:** Migration vs JSONB
2. **Erstelle detaillierte Docs:**
   - API Specs
   - Pine Script Templates
   - Test Cases
3. **Start Implementation:** Phase 1 (Webhook Endpoint)

---

**Created by:** Claude
**Last Updated:** 2025-11-11
