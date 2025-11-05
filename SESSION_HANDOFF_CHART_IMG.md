# Session Handoff: chart-img.com Integration

**Date:** 2025-11-05
**Session Duration:** ~3 hours
**Status:** Testing Complete - Ready for Implementation

---

## 🎯 Was wurde erreicht?

### ✅ Phase 5C: TradingView Watchlist Widget Issue
- **Problem:** TradingView FREE Widgets können KEINE echten Index-Daten (TVC:DJI)
- **Versucht:** ETF Proxies (DIA, QQQ, EXS1) - User will echte Indices
- **Entscheidung:** chart-img.com stattdessen nutzen

### ✅ chart-img.com API Tests
- **Plan:** MEGA Plan aktiviert ($10/Monat)
- **API Version:** v2 (POST + JSON body)
- **Tests erfolgreich:**
  - ✅ DAX (XETR:DAX) - funktioniert (aber 15min delay)
  - ✅ DOW JONES (TVC:DJI) - funktioniert (real-time!)
  - ✅ NASDAQ 100 (NASDAQ:NDX) - nicht getestet, aber sollte funktionieren

### ⚠️ Bekannte Issues

#### 1. DAX hat 15 Minuten Delay
- **Symbol:** `XETR:DAX`
- **Problem:** XETRA Exchange = 15min delayed
- **TODO:** Alternative Exchange finden (z.B. FWB:DAX, DE:DAX, etc.)

#### 2. Indicators funktionieren nicht
- **Problem:** `studies:[{"name":"RSI"}]` → Error: "must be a supported name"
- **Grund:** v2 nutzt andere Indicator-Namen als v1
- **TODO:** Richtige Namen aus v2 API Doku finden

---

## 📊 Working curl Commands

### Ohne Indicators (funktioniert):

```bash
curl -X POST https://api.chart-img.com/v2/tradingview/advanced-chart -H "x-api-key: 3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l" -H "content-type: application/json" -d "{\"theme\":\"dark\",\"interval\":\"5m\",\"symbol\":\"XETR:DAX\"}" -o dax_5m.png
```

```bash
curl -X POST https://api.chart-img.com/v2/tradingview/advanced-chart -H "x-api-key: 3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l" -H "content-type: application/json" -d "{\"theme\":\"dark\",\"interval\":\"1h\",\"symbol\":\"TVC:DJI\"}" -o dji_1h.png
```

**Wichtige Timeframes:** 5m, 15m, 1h, 1D (für AI Agents)

---

## 🚀 Nächste Schritte (Neue Session)

### 1. Indicators fixen (30 Min)
**Aufgabe:** Finde richtige Indicator-Namen für v2 API

**Recherche:**
- Suche in chart-img.com v2 Dokumentation nach "studies" oder "indicators"
- Teste verschiedene Namen: "RSI@tv-basicstudies", "Relative Strength Index", etc.
- TradingView's Pine Script Indicator Namen könnten funktionieren

**Test Command Template:**
```bash
curl -X POST https://api.chart-img.com/v2/tradingview/advanced-chart -H "x-api-key: 3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l" -H "content-type: application/json" -d "{\"theme\":\"dark\",\"interval\":\"1h\",\"symbol\":\"XETR:DAX\",\"studies\":[{\"name\":\"CORRECT_NAME_HERE\"}]}" -o test.png
```

---

### 2. DAX Real-Time Exchange finden (15 Min)

**Problem:** XETR:DAX = 15min delay

**Test Alternative Exchanges:**
```bash
# Frankfurt Stock Exchange
curl -X POST https://api.chart-img.com/v2/tradingview/advanced-chart -H "x-api-key: 3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l" -H "content-type: application/json" -d "{\"theme\":\"dark\",\"interval\":\"1h\",\"symbol\":\"FWB:DAX\"}" -o dax_fwb.png

# TradingView Composite
curl -X POST https://api.chart-img.com/v2/tradingview/advanced-chart -H "x-api-key: 3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l" -H "content-type: application/json" -d "{\"theme\":\"dark\",\"interval\":\"1h\",\"symbol\":\"TVC:DAX\"}" -o dax_tvc.png

# Index (generic)
curl -X POST https://api.chart-img.com/v2/tradingview/advanced-chart -H "x-api-key: 3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l" -H "content-type: application/json" -d "{\"theme\":\"dark\",\"interval\":\"1h\",\"symbol\":\"INDEX:DAX\"}" -o dax_index.png
```

**Prüfe welche real-time ist!**

---

### 3. Phase 5D: chart-img.com Implementation (12 Stunden)

**Dokumentation vorhanden:**
- `docs/FEATURES/chart-img-integration/` (11 Files, komplett durchgeplant!)
- `docs/FEATURES/chart-img-integration/IMPLEMENTATION_CHECKLIST.md` (6 Phases)

**Start hier:**
1. Lies: `docs/FEATURES/chart-img-integration/SESSION_CONTEXT.md`
2. Folge: `docs/FEATURES/chart-img-integration/IMPLEMENTATION_CHECKLIST.md`

**Phasen:**
- Phase 1: Database (1h) - chart_config JSONB, chart_snapshots table
- Phase 2: Backend (2h) - ChartService, API endpoints
- Phase 3: Frontend (3h) - Chart config modal, gallery
- Phase 4: Agents (3h) - ChartWatcher, MorningPlanner, JournalBot
- Phase 5: Testing (2h)
- Phase 6: Deployment (1h)

---

## 🔑 Wichtige Infos

### API Key (MEGA Plan)
```
3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l
```

**Plan Details:**
- $10/Monat
- 1000 Requests/Tag
- PNG + JPEG
- Alle Parameter erlaubt

### Symbol Mapping
```
Internal    → TradingView     → Status
^GDAXI      → XETR:DAX        → ⚠️ 15min delay (fix needed)
^DJI        → TVC:DJI         → ✅ Real-time
^NDX        → NASDAQ:NDX      → ❓ Not tested yet
EURUSD      → FX:EURUSD       → ✅ Real-time
EURGBP      → FX:EURGBP       → ✅ Real-time
```

### Timeframes für AI Agents
- **5m** - Entry-Timing (ChartWatcher)
- **15m** - Entry-Confirmation (ChartWatcher)
- **1h** - Structure (MorningPlanner)
- **1D** - Context (MorningPlanner, JournalBot)

---

## 📁 Wichtige Files

### Dokumentation
```
docs/FEATURES/chart-img-integration/
├── README.md                      # Start here
├── IMPLEMENTATION_CHECKLIST.md    # 6 Phases
├── 01_ARCHITECTURE.md
├── 02_DATABASE_SCHEMA.md
├── 03_API_ENDPOINTS.md
├── 04_FRONTEND_COMPONENTS.md
├── 05_AGENT_INTEGRATION.md
├── 06_DEPLOYMENT.md
└── SESSION_CONTEXT.md             # Quick start
```

### Code (existiert bereits - nur Planning!)
- Backend: `services/agents/src/chart_service.py` (geplant, nicht implementiert)
- Frontend: `apps/web/src/components/charts/` (geplant, nicht implementiert)

---

## 🐛 Session Issues (Lessons Learned)

### User Feedback:
1. **Zu kompliziert gedacht** → Einfache Lösungen bevorzugen
2. **Zu viel Text** → Kurz und präzise
3. **Nicht raten** → Erst Fehler lesen, dann fixen
4. **Curl Commands** → Terminal bricht um, ist normal
5. **Copy/Paste** → User nutzt Notepad zum cleanen

### Was gut lief:
- ✅ API Tests systematisch durchgeführt
- ✅ Beide Plan-Optionen evaluiert (TradingView Widgets vs chart-img)
- ✅ MEGA Plan upgrade = richtige Entscheidung

---

## 🎯 Erfolgs-Kriterien

**Phase 5D ist complete wenn:**
1. ✅ AI Agents können Charts generieren (5m, 15m, 1h, 1D)
2. ✅ Charts haben Indicators (RSI, MACD, Bollinger Bands)
3. ✅ DAX ist real-time (kein 15min delay)
4. ✅ User kann im Dashboard Chart-Config ändern
5. ✅ ChartWatcher analysiert Charts für Trading-Setups
6. ✅ MorningPlanner generiert Daily-Reports mit Charts
7. ✅ JournalBot fügt Charts zu Journal-Entries hinzu

---

## 🚨 WICHTIG für neue Session

### Start mit:
1. **Lies diese Datei** (SESSION_HANDOFF_CHART_IMG.md)
2. **Lies CLAUDE.md** (Projekt-Übersicht)
3. **Check aktuellen Status:**
   ```bash
   git log --oneline -5
   git status
   ```

### Dann:
1. **Indicators fixen** (30 min) - BLOCKER!
2. **DAX real-time finden** (15 min) - BLOCKER!
3. **Start Phase 5D** (12h) wenn Blocker gelöst

### User Präferenzen:
- Einfache, direkte Antworten
- Keine langen Erklärungen
- Erst verstehen, dann coden
- Commands als Copy/Paste ready

---

**Status:** ✅ Testing Complete, Ready for Implementation
**Next:** Fix Blockers → Start Phase 5D
**Estimated Time:** 13h total (1h Blockers + 12h Implementation)

---

**Last Updated:** 2025-11-05 23:30
**Created by:** Claude Code Session 1
**For:** Claude Code Session 2
