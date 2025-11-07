# TradeMatrix.ai - Claude Session Onboarding

**📌 LIES DIESE DATEI ZU BEGINN JEDER NEUEN SESSION!**

---

## 🎯 Was ist TradeMatrix.ai?

**AI-Powered Trading Analysis & Automation Platform**

- **Märkte:** DAX, NASDAQ, Dow Jones, Forex (EUR/USD, etc.)
- **Kern:** Technische Analyse + AI Pattern Recognition + Automated Reporting
- **Business Model:** SaaS mit Subscription Tiers (Free, Starter, Pro, Expert)

**Status:** 🚧 In Development (MVP Phase)

---

## ⚡ Quick Context (30 Sekunden Lesezeit)

### Architektur (WICHTIG - NEU vereinfacht!)

```
┌─────────────────┐
│  Next.js 16     │  React 19.2, TypeScript, Tailwind, shadcn/ui
│  Frontend       │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──────┐  │
│ SUPABASE │  │  ← PRIMÄRES BACKEND!
│──────────│  │
│ Database │  │  • PostgreSQL (auto-generated REST APIs)
│ Auth     │  │  • Authentication (Email, Social, JWT)
│ Storage  │  │  • File Storage (Charts, PDFs)
│ Edge Fn  │  │  • Webhooks (Stripe, etc.)
│ RLS      │  │  • Row Level Security
└──────────┘  │
              │
         ┌────▼──────┐
         │ FastAPI   │  ← NUR FÜR AI AGENTS!
         │───────────│
         │ Celery    │  • AI Agent Orchestration
         │ + Redis   │  • Background Tasks
         │ LangChain │  • ChartWatcher, SignalBot
         │ OpenAI    │  • RiskManager, JournalBot
         └───────────┘
```

**Kernprinzip:** EINFACH & STRIKT
- **Supabase** = Database + Auth + Storage + CRUD APIs
- **FastAPI** = Nur AI Agents
- **Keine Redundanz!**

---

## 📋 Session Start Checklist (IMMER durchgehen!)

- [ ] ✅ Diese Datei (`claude.md`) gelesen
- [ ] ✅ [docs/PROJECT_OVERVIEW.md](./docs/PROJECT_OVERVIEW.md) überflogen
- [ ] ✅ [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) angeschaut (Supabase-Architektur!)
- [ ] ✅ [docs/DEVELOPMENT_WORKFLOW.md](./docs/DEVELOPMENT_WORKFLOW.md) bei Bedarf
- [ ] ✅ Aktuellen Status überprüft (siehe unten)
- [ ] ✅ Git Branch checken: `git branch --show-current`

---

## 🗺️ Wichtigste Dokumente (Priorität)

### 🔥 Must-Read (Start HIER!)

1. **[docs/00_MASTER_ROADMAP.md](./docs/00_MASTER_ROADMAP.md)** ⭐ NEU!
   - 5 Phases to MVP (Foundation → SaaS)
   - Current status & next steps
   - Dependencies & timeline
   - Complete project roadmap

2. **[docs/PROJECT_OVERVIEW.md](./docs/PROJECT_OVERVIEW.md)**
   - Vollständiger Projekt-Überblick
   - Tech Stack (updated mit Supabase!)
   - Subscription Tiers
   - Current Status

3. **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)**
   - Komplette Supabase-Architektur (Deutsch!)
   - Verantwortlichkeiten (Supabase vs FastAPI)
   - Best Practices
   - Deployment-Strategie

4. **[QUICKSTART.md](./QUICKSTART.md)**
   - Setup in 5 Minuten
   - Supabase Projekt erstellen
   - Backend & Frontend starten

### 📚 Reference Docs

5. **[docs/DEVELOPMENT_WORKFLOW.md](./docs/DEVELOPMENT_WORKFLOW.md)**
   - Feature-Entwicklung
   - Template-System
   - Checklists

6. **[docs/README.md](./docs/README.md)**
   - Dokumentations-Übersicht
   - Alle Dokumentations-Kategorien

### 🔧 Technical Docs

7. **[services/api/supabase/README.md](./services/api/supabase/README.md)**
   - Supabase Setup
   - Migrationen
   - RLS Policies

8. **[services/api/supabase/functions/README.md](./services/api/supabase/functions/README.md)**
   - Edge Functions
   - Deployment

---

## 📊 Aktueller Status (2025-11-03)

### ✅ Phase 1-4: Foundation to Dashboard - COMPLETED (100%)
- [x] Projekt-Struktur, Dokumentation, Supabase Integration
- [x] Next.js 16, Authentication, Protected Routes
- [x] Database Schema mit RLS Policies
- [x] Trading Rules, Validation Engine, Risk Management
- [x] Market Data Fetcher, Technical Indicators
- [x] Dashboard UI mit shadcn/ui Components
- [x] Netlify Deployment: https://tradematrix.netlify.app

### ✅ Phase 5A: Liquidity Alert System - DEPLOYED TO PRODUCTION (100%)
- [x] **EOD Data Layer** - 86,469+ records (5 symbols: DAX, NASDAQ, DOW, EUR/USD, EUR/GBP)
- [x] **EOD Levels Calculation** - 100% complete (Yesterday High/Low, Pivot Points)
- [x] **Dashboard Widgets** - 8 neue Widgets (EOD Levels Today, Market Sentiment, etc.)
- [x] **Liquidity Alert Engine** - Real-time Price Monitoring every 60s
- [x] **Browser Push Notifications** - VAPID Keys configured, Web Push API
- [x] **Hetzner Production Deployment** - CX11 Server running 24/7 ⭐
  - Server: 135.181.195.241 (2 vCPU, 4GB RAM, 40GB SSD)
  - Services: Redis 7-alpine, Celery Worker, Celery Beat
  - Repository: `hetzner-deploy/` (Docker Compose)
  - Latest Commit: 6f952fb (JSON serialization fix)
  - Status: LIVE, monitoring 5 symbols, 6 test subscriptions active

### ⏸️ Phase 5C: TradingView Watchlist - ON HOLD (Replaced by Phase 5D)
**Feature:** User-customizable watchlist with TradingView Widgets

**Problem gefunden (2025-11-05):**
- ❌ TradingView FREE Widgets haben KEINE echten Index-Daten (TVC:DJI nur Premium)
- ❌ ETF Proxies (DIA, QQQ) funktionieren, aber User will echte Indices
- ✅ **Entscheidung:** chart-img.com stattdessen nutzen (Phase 5D)

**Status:** Code existiert, aber nicht deployed (wartet auf chart-img Integration)

---

### 🚧 Phase 5D: chart-img.com Integration - IN PROGRESS (5%) ⭐ CURRENT!
**Feature:** AI-Powered Chart Analysis mit echten Index-Daten

**Architecture Decision (2025-11-05):**
- 💡 **chart-img.com API:** Generiert JPG/PNG Charts von TradingView
- ✅ **Echte Index-Daten:** TVC:DJI, NASDAQ:NDX, XETR:DAX funktionieren!
- ✅ **MEGA Plan:** $10/Monat, 1000 requests/day, alle Indicators
- ✅ **Perfect für AI Agents:** ChartWatcher, MorningPlanner, JournalBot

**Status:**
- [x] **API Tests:** DAX + DJI funktionieren ✅
- [x] **MEGA Plan:** Aktiviert ($10/mo) ✅
- [ ] **BLOCKER 1:** Indicator-Namen für v2 API finden (RSI, MACD)
- [ ] **BLOCKER 2:** DAX real-time Exchange finden (aktuell 15min delay)
- [ ] **Phase 1:** Database (1h) - chart_config, chart_snapshots
- [ ] **Phase 2:** Backend (2h) - ChartService, API endpoints
- [ ] **Phase 3:** Frontend (3h) - Chart config modal, gallery
- [ ] **Phase 4:** Agents (3h) - ChartWatcher, MorningPlanner, JournalBot
- [ ] **Phase 5:** Testing (2h)
- [ ] **Phase 6:** Deployment (1h)

**📖 Dokumentation:**
- **Feature Docs:** [docs/FEATURES/chart-img-integration/](./docs/FEATURES/chart-img-integration/) (11 Files!)
- **Implementation:** [IMPLEMENTATION_CHECKLIST.md](./docs/FEATURES/chart-img-integration/IMPLEMENTATION_CHECKLIST.md)
- **Session Handoff:** [SESSION_HANDOFF_CHART_IMG.md](./SESSION_HANDOFF_CHART_IMG.md) 👈 **START HERE!**

**🎯 Nächster Schritt:**
1. Fix Blocker 1: Indicator-Namen (30 min)
2. Fix Blocker 2: DAX real-time Exchange (15 min)
3. Start Phase 1: Database Setup (1h)

**Estimated Time:** 13h total (1h Blockers + 12h Implementation)

---

### 📋 Phase 5B: Stripe Integration & SaaS Features - PLANNED
- [ ] Stripe Subscription Billing
- [ ] Subscription Management (upgrade/downgrade)
- [ ] Usage Tracking & Limits
- [ ] Email Notifications
- [ ] Report Publishing (subdomain/blog)
- [ ] WhatsApp Alerts (Expert tier)

**For detailed roadmap:** See [docs/00_MASTER_ROADMAP.md](./docs/00_MASTER_ROADMAP.md)

---

## 🏗️ Repository Struktur

```
TradeMatrix/
├── claude.md                      # 👈 DU BIST HIER!
├── QUICKSTART.md                  # Setup Guide (5 min)
├── README.md                      # Public README
│
├── apps/
│   └── web/                       # Next.js 16 Frontend
│       ├── src/app/               # App Router
│       ├── src/components/        # React Components
│       └── .env.example           # Frontend Env Vars
│
├── services/
│   ├── api/                       # FastAPI Backend (AI Agents)
│   │   ├── src/
│   │   │   ├── main.py           # FastAPI App (AI Endpoints)
│   │   │   └── config/           # Supabase Client
│   │   ├── supabase/             # ⭐ SUPABASE SETUP
│   │   │   ├── migrations/       # SQL Migrationen
│   │   │   └── functions/        # Edge Functions
│   │   ├── requirements.txt      # Python Deps (simplified!)
│   │   └── .env.example          # Backend Env Vars
│   │
│   └── agents/                    # AI Agents (Celery Tasks)
│       └── src/
│           ├── chart_watcher.py  # (planned)
│           ├── signal_bot.py     # (planned)
│           ├── risk_manager.py   # (planned)
│           └── journal_bot.py    # (planned)
│
├── packages/
│   ├── ui/                        # Shared UI Components
│   ├── database/                  # (deprecated - now in supabase/)
│   └── shared/                    # Shared Types
│
├── docs/                          # 📚 DOCUMENTATION HUB
│   ├── 00_MASTER_ROADMAP.md       # ⭐ ROADMAP! 5 Phases to MVP
│   ├── PROJECT_OVERVIEW.md        # ⭐ Project Overview
│   ├── ARCHITECTURE.md            # ⭐ Supabase Architecture
│   ├── DEVELOPMENT_WORKFLOW.md    # Feature Development
│   ├── README.md                  # Docs Overview
│   ├── FEATURES/                  # Feature Planning
│   │   └── _template/            # Feature Templates
│   ├── ARCHIVE/                   # Old documentation (pre-Supabase)
│   └── STRATEGIES/                # Trading Strategies
│
└── config/
    ├── rules/                     # Trading Rules (YAML)
    └── settings/                  # App Settings
```

---

## 🔧 Tech Stack (Aktuelle Version)

### Frontend
- **Next.js 16** (React 19.2, Turbopack, PPR, React Compiler)
- **TypeScript** 5.x
- **ESLint 9** (Flat Config - eslint.config.mjs)
- **Tailwind CSS** + **shadcn/ui**
- **TradingView Lightweight Charts**
- **Supabase JS Client** (für Auth & Data)

### Backend (Supabase)
- **PostgreSQL** (managed by Supabase)
- **Supabase Auth** (Email/Password, Google OAuth, GitHub OAuth - No MagicLink)
- **Supabase Storage** (Charts, PDFs)
- **Edge Functions** (Deno/TypeScript)
- **Row Level Security** (RLS)

### Backend (FastAPI - AI Only!)
- **FastAPI** 0.110+
- **Celery** + **Redis** (Background AI Tasks)
- **OpenAI API** + **LangChain**
- **Supabase Python Client**

### Entfernt (nicht mehr nötig!)
- ❌ SQLAlchemy + Alembic
- ❌ python-jose + passlib
- ❌ psycopg2-binary

---

## 🤖 AI Agents (Planned)

| Agent | Rolle | Status |
|-------|-------|--------|
| **ChartWatcher** | Monitors charts, extracts values, detects patterns | 📋 Planned |
| **SignalBot** | Evaluates market structure, decides entries/exits | 📋 Planned |
| **RiskManager** | Calculates position sizes, sets SL/TP zones | 📋 Planned |
| **JournalBot** | Creates automated reports and journal entries | 📋 Planned |
| **Publisher** | Uploads reports to subdomain/blog | 📋 Planned |

---

## 💰 Subscription Tiers

| Tier | Preis | Features |
|------|-------|----------|
| **Free** | €0/mo | Basic market overview, limited reports |
| **Starter** | €9/mo | Daily reports, email alerts |
| **Pro** | €39/mo | All features + backtesting, API access |
| **Expert** | €79/mo | Custom strategies, priority support, WhatsApp alerts |

---

## 🎯 Development Workflow

### Wenn User Feature-Request hat:

1. **Planning Phase**
   ```bash
   # Lies relevante Docs
   cat docs/PROJECT_OVERVIEW.md
   cat docs/DEVELOPMENT_WORKFLOW.md

   # Check ob Feature existiert
   ls docs/FEATURES/
   ```

2. **Create Feature Folder** (wenn neu)
   ```bash
   # Kopiere Template
   cp -r docs/FEATURES/_template docs/FEATURES/[feature-name]
   ```

3. **Implement**
   - Folge Checklists in Feature-Folder
   - Update Dokumentation während Implementierung
   - Commit regelmäßig

4. **Testing**
   - Folge Testing Checklist
   - Unit + Integration Tests

5. **Documentation**
   - Update PROJECT_OVERVIEW.md Status
   - Update ARCHITECTURE.md bei Architektur-Änderungen

### Git Workflow

```bash
# Feature Branch erstellen
git checkout -b feature/[name]

# Änderungen committen
git add .
git commit -m "feat: [description]"

# Push
git push -u origin feature/[name]

# Pull Request erstellen (GitHub UI oder gh CLI)
gh pr create --title "feat: [name]" --body "[description]" --base main
```

---

## ⚠️ Wichtige Regeln

### Architektur
1. **Nutze Supabase für CRUD** - Nie eigene Endpoints für einfache Datenoperationen
2. **FastAPI nur für AI** - Keine CRUD, keine Auth-Endpoints
3. **Edge Functions für Webhooks** - Stripe, externe APIs
4. **RLS immer aktivieren** - Row Level Security für alle Tabellen

### Datenbank
5. **MIGRATIONS ERST CHECKEN** - BEVOR du `.table('xyz')` oder `.select('abc')` verwendest, lies `services/api/supabase/migrations/*.sql` um Tabellennamen und Spalten zu verifizieren
6. **Nie Tabellen/Spalten raten** - Glob migrations, Read relevante SQL-Datei, dann Code schreiben
7. **Schema-Dokumentation nutzen** - Siehe `services/api/supabase/README.md` für Migrations-Übersicht

### Trading Data Integrity (KRITISCH!)
8. **NIEMALS Preise schätzen** - NO estimation, NO guessing, NO approximation
9. **Datenfluss befolgen** - PriceFetcher → current_prices → ChartWatcher → SetupGenerator
10. **Validierung vor Setup** - Setup Generation MUSS fehlschlagen wenn current_price fehlt
11. **Erlaubte Datenquellen** - Nur: PriceFetcher (yfinance/Twelvedata), ChartWatcher, MarketDataFetcher
12. **System Integrity Rules** - Siehe `config/system_integrity_rules.yaml` - KEINE Ausnahmen!

### 🔴 NIEMALS QUICK-FIXES!!! 🔴
13. **NIEMALS Quick-Fixes implementieren** - Quick-Fix = kein sauberer Refactor
14. **IMMER saubere Architektur** - ERST Schema checken, DANN Datenquellen checken, DANN Normalisierung planen, DANN Code schreiben
15. **WENN ich Quick-Fixes mache** - bin ich der größte HURENSOHN
16. **Vendor Lock-in vermeiden** - API-agnostische Normalisierung auf Persistence-Layer (MarketDataFetcher → Normalizer → Database)
17. **Schema = Single Source of Truth** - Migration-Spalten IMMER vor Code-Spalten priorisieren

### Code
18. **Keine Redundanz** - Wenn Supabase es kann, nutze Supabase
19. **Server Components bevorzugen** - Next.js (weniger Client JS)
20. **TypeScript strikt** - Keine `any` types
21. **Environment Variables** - Nie Secrets committen

### Dokumentation
22. **Update während Entwicklung** - Nicht nachträglich
23. **Checklists nutzen** - TodoWrite tool für Tracking
24. **Status aktualisieren** - PROJECT_OVERVIEW.md Status immer aktuell

---

## 🚀 Quick Commands

### Backend starten
```bash
cd services/api/src
uvicorn main:app --reload
# http://localhost:8000
```

### Frontend starten
```bash
cd apps/web
npm run dev
# http://localhost:3000
```

### Celery Worker starten
```bash
cd services/agents
celery -A tasks worker --loglevel=info
```

### Redis starten (Docker)
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Supabase Migrationen ausführen
```sql
-- In Supabase SQL Editor:
-- 1. Copy content from services/api/supabase/migrations/001_initial_schema.sql
-- 2. Run
-- 3. Repeat for 002_rls_policies.sql
```

---

## 🐛 Debugging

### "Database connection failed"
→ Check SUPABASE_URL und SUPABASE_KEY in .env

### "Module not found"
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

### "Port already in use"
```bash
# Change port
uvicorn main:app --port 8001
```

### "Supabase client error"
→ Check .env hat richtige Keys (anon key für client, service_role für admin)

---

## 📞 Fragen?

**Lies diese Docs:**
1. [docs/PROJECT_OVERVIEW.md](./docs/PROJECT_OVERVIEW.md) - Projekt-Übersicht
2. [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - Architektur-Details
3. [QUICKSTART.md](./QUICKSTART.md) - Setup-Anleitung
4. [docs/README.md](./docs/README.md) - Alle Docs

**Oder frage den User direkt!**

---

## 🎯 Session Best Practices

1. **Start immer hier** (claude.md)
2. **Check Git Branch** (`git branch --show-current`)
3. **Lies PROJECT_OVERVIEW.md** (5 Min)
4. **Check aktuellen Status** (Was ist done? Was ist next?)
5. **Bei Feature-Requests:** Check docs/FEATURES/ ob schon geplant
6. **Nutze TodoWrite** für Task Tracking
7. **Commit regelmäßig** mit klaren Messages
8. **Update Docs** während Entwicklung

---

## 🎉 Du bist bereit!

**Jetzt kennst du:**
- ✅ Was TradeMatrix.ai ist
- ✅ Die Architektur (Supabase!)
- ✅ Wo die Docs sind
- ✅ Den aktuellen Status
- ✅ Den Workflow

**Frage den User:** "Was soll ich heute für dich tun?"

---

**Made with 🧠 by Claude + umi1970**
