# TradeMatrix.ai - Complete Trade Flow: Setup Generation to Publishing

**Author:** Claude Code (Session: 2025-11-07)
**Purpose:** Document the complete flow chain from SetupGenerator through ValidationEngine to JournalBot and Publisher
**Status:** Active Architecture (v1.3)

---

## Overview

This document describes the **complete data flow** for trading setup generation, validation, journaling, and publishing in TradeMatrix.ai. Understanding this flow is critical because **ValidationEngine is NOT a Python file** - it's a **FLOW LAYER** composed of multiple modules working in sequence.

---

## Architecture Principle: Flow Layers vs Code Files

**CRITICAL UNDERSTANDING:**

- ❌ **WRONG:** "Where is `ValidationEngine.py`?"
- ✅ **CORRECT:** "ValidationEngine is a flow layer defined in `ValidationAndRisk.yaml`"

**Why This Matters:**
- TradeMatrix.ai is designed as **orchestrated flows** defined in YAML
- Each flow chains multiple Python modules together
- The system behavior is defined by the YAML flow, not individual Python files

---

## Complete Flow Chain

```
┌──────────────────────────────────────────────────────────────────────┐
│                      DATA INTEGRITY PIPELINE                          │
└──────────────────────────────────────────────────────────────────────┘

1. PriceFetcher (Celery Beat - every 60s)
   ├─ Data Source: yfinance (indices) or Twelvedata (forex)
   ├─ Validation: Real-time API data only, NO estimation
   └─ Output: current_prices table
            ↓

2. ChartWatcher (AI Agent)
   ├─ Input: Reads current_prices table
   ├─ Validation: current_price must exist in table
   ├─ AI Analysis: OpenAI Vision analyzes chart image
   └─ Output: chart_analyses table
            └─ payload.current_price (stored for SetupGenerator)
            ↓

3. SetupGeneratorV13 (on "Generate Setup" button click)
   ├─ Input 1 (Priority): chart_analyses.payload.current_price
   ├─ Input 2 (Fallback): current_prices table
   ├─ Validation: FAILS if current_price is None (NO estimation!)
   ├─ Processing:
   │  ├─ EMA Alignment Detection (bullish/bearish trend)
   │  ├─ Entry/SL/TP Calculation (based on support/resistance + ATR)
   │  ├─ Risk/Reward Validation (minimum 2.0 ratio)
   │  └─ Confidence Scoring (0.0-0.95, multi-factor)
   └─ Output: setups table (status: "pending" if confidence >= 0.6)
            ↓

┌──────────────────────────────────────────────────────────────────────┐
│           VALIDATION & RISK FLOW (ValidationEngine Layer)             │
│         Defined in: docs/yaml/flows/ValidationAndRisk.yaml            │
└──────────────────────────────────────────────────────────────────────┘

4a. EventWatcher
    ├─ Input: trade_proposal from SetupGenerator
    ├─ Checks: High-impact news events (ForexFactory, TradingEconomics)
    ├─ Validation: Country = "United States", Importance = "high"
    └─ Output: risk_events[], high_risk (boolean)
             ↓

4b. TradeValidationEngine
    ├─ Input: trade_proposal from SetupGenerator
    ├─ Validation:
    │  ├─ Data Origin Check (must be from allowed sources)
    │  ├─ Confidence Threshold (>= 0.6 for execution)
    │  ├─ R:R Ratio Check (>= 2.5 minimum)
    │  ├─ Price Age Check (<= 300 seconds)
    │  └─ Source Confidence (1.0 = 100% reliable only)
    ├─ Processing: Calculates bias_score (directional bias strength)
    └─ Output: validation_result (status: APPROVED/REJECTED)
             ↓

4c. RiskManager
    ├─ Input: validation_result from TradeValidationEngine
    ├─ Calculation:
    │  ├─ position_size = account_balance * 0.01 / (entry - sl)
    │  ├─ adjusted_sl = entry - (ATR * 1.2)
    │  └─ breakeven_level = entry + (tp - entry) * 0.5
    └─ Output: position_size, adjusted_sl
             ↓

4d. RiskContextEvaluator
    ├─ Input: Current account state
    ├─ Checks:
    │  ├─ Daily Loss Limit (max 3% per day)
    │  ├─ Open Trades Count (max 5 concurrent)
    │  ├─ Loss Streak (pause after 3 consecutive losses)
    │  └─ Account Drawdown (current exposure)
    ├─ Determines: risk_mode
    │  ├─ NORMAL: All systems go
    │  ├─ LIMITED_MODE: Max trades reached
    │  └─ STOP_TRADING: Daily loss limit hit
    └─ Output: risk_context {mode, exposure, warnings}
             ↓

4e. TradeDecisionEngine
    ├─ Inputs:
    │  ├─ validation_result (from TradeValidationEngine)
    │  ├─ risk_context (from RiskContextEvaluator)
    │  ├─ high_risk (from EventWatcher)
    │  └─ position_size (from RiskManager)
    ├─ Decision Logic:
    │  ├─ IF validation_result.status != "APPROVED" → REJECT
    │  ├─ ELSE IF high_risk == true → WAIT
    │  ├─ ELSE IF risk_mode == "STOP_TRADING" → HALT
    │  ├─ ELSE IF risk_mode == "LIMITED_MODE" → REDUCE
    │  ├─ ELSE → EXECUTE
    └─ Output: final_decision {decision, reason, rr, bias_score}
             ↓

4f. ReportBridge
    ├─ Input: final_decision (from TradeDecisionEngine)
    ├─ Processing:
    │  ├─ Creates journal_entry (timestamp, decision, reason, rr, bias_score)
    │  └─ Creates publish_packet (title, content, tags)
    └─ Outputs:
         ├─ journal_entry → sent to JournalBot
         └─ publish_packet → sent to Publisher
             ↓              ↓

5. JournalBot          6. Publisher
   ├─ Input: journal_entry    ├─ Input: publish_packet
   ├─ Processing:              ├─ Processing:
   │  ├─ Timestamp             │  ├─ Format content (Markdown)
   │  ├─ Format entry          │  ├─ Add tags
   │  └─ Store in DB           │  └─ Upload to subdomain
   └─ Output: Saved to         └─ Output: Published to
      trade_journal table         blog/reports subdomain
```

---

## Flow Stops (Rejection Points)

The flow can **STOP** at any of these points:

### 1. PriceFetcher Failure
- **Condition:** API request fails (network, rate limit, invalid API key)
- **Action:** SKIP current cycle, retry in next Beat (60s)
- **Impact:** ChartWatcher cannot run (no current_price available)

### 2. ChartWatcher Validation Failure
- **Condition:** current_prices table is empty OR symbol_id not found
- **Action:** Log warning, SKIP analysis for this symbol
- **Impact:** No chart_analyses entry created

### 3. SetupGeneratorV13 Data Validation Failure
- **Condition:** current_price is None (not in payload AND not in current_prices table)
- **Action:** FAIL with error: "No current_price available - cannot generate setup"
- **Impact:** No setup created, user sees error toast
- **System Integrity Rule:** **NEVER estimate prices** - better to fail than guess

### 4. TradeValidationEngine Rejection
- **Condition:**
  - Data origin NOT in allowed list (PriceFetcher, ChartWatcher, MarketDataFetcher)
  - Confidence < 0.6
  - R:R < 2.5
  - Price age > 300 seconds
  - Source confidence < 1.0
- **Action:** validation_result.status = "REJECTED"
- **Impact:** TradeDecisionEngine returns decision = "REJECT"

### 5. EventWatcher High-Risk Alert
- **Condition:** high_risk = true (major news event detected)
- **Action:** TradeDecisionEngine returns decision = "WAIT"
- **Impact:** Setup saved but not executed, user notified to wait

### 6. RiskContextEvaluator Limits Hit
- **Condition:**
  - Daily loss >= 3% → risk_mode = "STOP_TRADING"
  - Open trades >= 5 → risk_mode = "LIMITED_MODE"
  - 3 consecutive losses → pause_trading = true
- **Action:** TradeDecisionEngine returns decision = "HALT" or "REDUCE"
- **Impact:** Setup rejected for risk management reasons

---

## Flow Continues (Success Path)

For a setup to reach **JournalBot and Publisher**, ALL of these must be true:

✅ **PriceFetcher:** Successfully fetched price from API
✅ **ChartWatcher:** current_price exists in current_prices table
✅ **SetupGenerator:** current_price retrieved (NOT estimated), confidence >= 0.6, R:R >= 2.0
✅ **EventWatcher:** high_risk = false (no major news events)
✅ **TradeValidationEngine:** status = "APPROVED" (all data integrity checks passed)
✅ **RiskContextEvaluator:** risk_mode = "NORMAL" (no daily loss limit, no max trades reached)
✅ **TradeDecisionEngine:** decision = "EXECUTE"

**Result:** ReportBridge sends to JournalBot + Publisher

---

## Module Responsibilities

### Data Layer (Real Market Data)
- **PriceFetcher** - Fetches ONLY real market data from yfinance/Twelvedata
- **ChartWatcher** - Reads real prices, NEVER estimates or guesses
- **SetupGeneratorV13** - FAILS if no real data available

### Validation Layer (Data Integrity)
- **EventWatcher** - External risk factors (news events)
- **TradeValidationEngine** - Data origin, confidence, R:R, freshness
- **RiskManager** - Position sizing, SL/TP adjustment
- **RiskContextEvaluator** - Account-level risk (daily loss, max trades)
- **TradeDecisionEngine** - Final go/no-go decision

### Output Layer (Reporting)
- **ReportBridge** - Formats and routes validated trades
- **JournalBot** - Stores trade decisions in journal
- **Publisher** - Publishes approved trades to blog/reports

---

## Critical Rules (System Integrity)

From `config/system_integrity_rules.yaml`:

### NO Estimation Policy
```yaml
validation:
  no_estimated_prices: true
  prohibited_fields:
    - "guessed_price"
    - "estimated_price"
    - "approximate_price"
    - "fallback_price"
```

**Why:** TradeMatrix.ai operates with REAL MONEY. Estimated prices destroy data integrity and can cause financial loss.

### Data Origin Validation
```yaml
validation:
  data_origin_required:
    - "ChartWatcher"
    - "MarketDataFetcher"
    - "PriceFetcher"
  fail_on_invalid_source: true
```

**Why:** Only trusted data sources that fetch from official APIs (yfinance, Twelvedata) are allowed.

### Minimum Data Quality
```yaml
validation:
  min_data_quality:
    price_age_max_seconds: 300  # Price must be < 5 minutes old
    source_confidence_min: 1.0  # Only 100% reliable sources
```

**Why:** Stale data (> 5 minutes old) can lead to incorrect Entry/SL/TP calculations.

---

## YAML Flow Definitions

### ValidationAndRisk.yaml
**Path:** `docs/yaml/flows/ValidationAndRisk.yaml`

**Trigger:**
```yaml
trigger:
  source: "signal_bot"
  condition: "trade_proposal.generated == true"
```

**Sequence:**
```yaml
sequence:
  - EventWatcher
  - TradeValidationEngine
  - RiskManager
  - RiskContextEvaluator
  - TradeDecisionEngine
  - ReportBridge
```

**Success Handoff:**
```yaml
on_success:
  - log: "✅ Trade validated and risk-managed successfully"
  - send_to: "journal_bot"
```

**Failure Handoff:**
```yaml
on_fail:
  - log: "❌ Validation or Risk check failed"
  - send_to: "monitoring"
```

---

## Python Bridge Modules

### TradeDecisionEngine.py
**Path:** `docs/yaml/flows/trade_decision_engine.py`

**Core Logic:**
```python
def decide(self, validation_result, risk_context, high_risk):
    approved = validation_result.get("status") == "APPROVED"
    risk_mode = risk_context.get("mode", "NORMAL")
    final = "REJECT"

    if not approved:
        reason = "Validation failed"
    elif high_risk:
        final = "WAIT"
        reason = "High-impact news ahead"
    elif risk_mode == "STOP_TRADING":
        final = "HALT"
        reason = "Daily loss limit hit"
    elif risk_mode == "LIMITED_MODE":
        final = "REDUCE"
        reason = "Max trades reached"
    else:
        final = "EXECUTE"
        reason = "All checks passed"

    return {
        "decision": final,
        "reason": reason,
        "bias_score": validation_result.get("bias_score"),
        "rr": validation_result.get("rr"),
        "timestamp": validation_result.get("timestamp")
    }
```

**Possible Decisions:**
- `EXECUTE` - All checks passed, trade approved
- `REJECT` - Validation failed
- `WAIT` - High-impact news event detected
- `HALT` - Daily loss limit reached
- `REDUCE` - Max concurrent trades reached

### ReportBridge.py
**Path:** `docs/yaml/flows/report_bridge.py`

**Core Logic:**
```python
def process(self, final_decision):
    entry = {
        "time": datetime.utcnow().isoformat(),
        "decision": final_decision.get("decision"),
        "reason": final_decision.get("reason"),
        "rr": final_decision.get("rr"),
        "bias_score": final_decision.get("bias_score")
    }
    packet = {
        "title": f"Trade Decision {entry['decision']}",
        "content": json.dumps(entry, indent=2),
        "tags": ["validation", "risk", "journal"]
    }
    return {"journal_entry": entry, "publish_packet": packet}
```

**Outputs:**
- `journal_entry` → sent to JournalBot (stores in database)
- `publish_packet` → sent to Publisher (publishes to blog)

---

## Example: Successful Trade Flow

**Scenario:** User clicks "Generate Trading Setup" for DAX analysis

```
1. SetupGeneratorV13 starts
   ├─ Reads chart_analyses.payload.current_price = 19245.50
   ├─ Validates: current_price is NOT None ✅
   ├─ Calculates:
   │  ├─ Trend: bullish (EMA20 > EMA50 > EMA200)
   │  ├─ Entry: 19230.00 (near support)
   │  ├─ Stop Loss: 19200.00 (below support - ATR*2)
   │  ├─ Take Profit: 19290.00 (2:1 R:R)
   │  ├─ Risk/Reward: 2.0 ✅
   │  └─ Confidence: 0.75 ✅
   └─ Saves to setups table (status: "pending")

2. EventWatcher checks
   ├─ Query: High-impact US news events in next 4 hours
   └─ Result: None found → high_risk = false ✅

3. TradeValidationEngine validates
   ├─ Data origin: "ChartWatcher" ✅ (in allowed list)
   ├─ Confidence: 0.75 ✅ (>= 0.6)
   ├─ R:R: 2.0 ✅ (>= 2.5... wait, this would FAIL!)
   └─ Result: status = "REJECTED" (R:R < 2.5)

   ❌ Flow STOPS here - Trade rejected due to R:R below minimum 2.5

TradeDecisionEngine: decision = "REJECT", reason = "Validation failed"
ReportBridge: Sends rejection to JournalBot (logged but not published)
```

**Fix Required:** SetupGeneratorV13 needs to use MinRRR: 2.5 (from RiskManagement.yaml) instead of 2.0

---

## Example: Rejected Trade Flow (High-Risk News)

```
1. SetupGeneratorV13: Generates setup with confidence 0.85, R:R 3.0 ✅

2. EventWatcher checks
   ├─ Query: High-impact US news events in next 4 hours
   └─ Result: "FOMC Interest Rate Decision" at 14:00 EST → high_risk = true ❌

3. TradeValidationEngine validates
   └─ Result: status = "APPROVED" ✅

4. RiskManager calculates
   └─ position_size, adjusted_sl ✅

5. RiskContextEvaluator checks
   └─ risk_mode = "NORMAL" ✅

6. TradeDecisionEngine decides
   ├─ validation approved: ✅
   ├─ high_risk: ❌ (true)
   └─ decision = "WAIT", reason = "High-impact news ahead"

7. ReportBridge sends
   ├─ journal_entry → JournalBot (logged as "WAIT")
   └─ publish_packet → Publisher (NOT published, flagged as "wait")
```

**User sees:** "Setup ready but waiting for FOMC news event to pass"

---

## Integration Checklist for New Modules

When creating a new module that generates trade proposals:

- [ ] Read current_price from `current_prices` table (NOT from estimation)
- [ ] Store current_price in output payload for downstream modules
- [ ] Validate data_source is in allowed list (PriceFetcher, ChartWatcher, MarketDataFetcher)
- [ ] Check price age (fetched_at must be < 300 seconds old)
- [ ] Set confidence score (0.0-0.95) based on technical factors
- [ ] Validate R:R >= 2.5 (from RiskManagement.yaml)
- [ ] If ANY validation fails → FAIL (do NOT estimate or guess)
- [ ] Log error message with specific failure reason
- [ ] Update `system_integrity_rules.yaml` if adding new data sources

---

## Glossary

**Flow Layer** - A sequence of Python modules orchestrated by YAML definition (e.g., ValidationAndRisk flow)

**Module** - A single Python class/file that performs one specific task (e.g., TradeValidationEngine.py)

**Data Origin** - The source of current_price data (must be: PriceFetcher, ChartWatcher, or MarketDataFetcher)

**Validation** - Checking data integrity, freshness, confidence, and source reliability BEFORE creating setups

**Risk Context** - Account-level state (daily loss, open trades, loss streak) that affects trade execution

**Journal Entry** - A record of a trade decision (EXECUTE/REJECT/WAIT/HALT/REDUCE) stored in trade_journal table

**Publish Packet** - Formatted trade information sent to Publisher for blog/subdomain publishing

**Confidence Score** - Multi-factor technical analysis score (0.0-0.95):
  - 0.30: Trend strength (bullish/bearish)
  - 0.25: Pattern detected (EMA alignment)
  - 0.10-0.20: RSI confirmation
  - 0.15: R:R >= 2.5
  - 0.10: Valid setup (Entry/SL/TP positioning)

**Bias Score** - Directional bias strength (TradeValidationEngine output, 0.0-1.0)

---

## References

- **System Integrity Rules:** `config/system_integrity_rules.yaml`
- **ValidationAndRisk Flow:** `docs/yaml/flows/ValidationAndRisk.yaml`
- **RiskManagement Parameters:** `docs/yaml/RiskManagement.yaml`
- **MorningPlanner Flow:** `docs/yaml/MorningPlanner_v3.yaml`
- **SetupGeneratorV13:** `hetzner-deploy/src/setup_generator_v13.py`
- **PriceFetcher:** `hetzner-deploy/src/price_fetcher.py`
- **ChartWatcher:** `hetzner-deploy/src/chart_watcher.py`

---

**Last Updated:** 2025-11-07
**Version:** 1.0
**Status:** Active Architecture Documentation
