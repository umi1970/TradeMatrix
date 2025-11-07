# TradeMatrix.ai — Architecture Overview
Version: 1.0 • Last Updated: 2025-11-07

---

## 📐 Data Flow Overview

```
MarketDataFetcher → ChartWatcher → AI-Analyzer → TradeDecisionEngine
                                                   ↓
                         TradeValidationEngine → JournalBot → Publisher
```

### 1. MarketDataFetcher
Pulls real-time & historical data (Twelve Data, Finnhub, Alpha Vantage).
- Normalizes OHLCV data
- Caches latest tick
- Passes validated snapshot to Analyzer

### 2. ChartWatcher
Validates chart consistency and extracts pivots, supports, resistances.
- Detects outliers / OCR misreads
- Confirms data origin

### 3. AI-Analyzer
Computes indicators (EMA, RSI, MACD, ATR, Ichimoku, BB, Pivot PP)
and outputs standardized metrics used for setup generation.

### 4. TradeDecisionEngine
Creates preliminary setups (Entry, SL, TP, R:R) using trading rules MR-01 – MR-06.
Output example:
```json
{ "entry": 24080, "stop_loss": 23920, "take_profit": 24480, "confidence": 0.68, "valid": true }
```

### 5. TradeValidationEngine

Filter-Layer enforcing:

✅ Real data source check (MarketDataFetcher, ChartWatcher)

✅ Confidence ≥ 0.5

✅ Logical order of Entry/SL/TP

✅ Rule conformance (EMA alignment, pivot confluence)

Invalid trades → STOP → no journal entry.

### 6. JournalBot

Writes validated trades into the Supabase table `trade_journal`.

- Appends metadata (RR, timestamp, signal type)
- Archives raw record to storage

### 7. Publisher

Broadcasts journal updates to:

- Dashboard widgets (Realtime feed)
- Report generator (DOCX/PDF)
- Notification system (Push / Email / WhatsApp)

---

## 🧩 Fail Path Logic

If any step fails:

```
ValidationEngine → STOP
JournalBot → SKIP ENTRY
Publisher → NO EVENT
```

No partial commits. No pending states. Fail-fast architecture.

---

## ⚙️ System Philosophy

- Deterministic data flow
- Real data only — never estimated
- Confidence-based filtering before persistence
- Audit-friendly logging
- Modular AI agents (loosely coupled via YAML flows)

---

## 📁 Related Documentation

- `05_Validation_Engine.md`
- `06_Risk_Management.md`
- `trade_validation_flow.yaml`
- `journal_commit_flow.yaml`
- `SystemIntegrityRules.yaml`
