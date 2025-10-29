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

## 📊 Aktueller Status (2025-10-29)

### ✅ Phase 1: Foundation - COMPLETED (100%)
- [x] Projekt-Struktur
- [x] Dokumentationssystem (inkl. Master Roadmap!)
- [x] **Backend auf Supabase vereinfacht** ⭐
- [x] **Datenbank-Schema designed** (SQL Migrationen)
- [x] **Supabase Projekt erstellt** ("tradematrix Projekt")
- [x] **Database Migrationen ausgeführt** (001_initial_schema.sql, 002_rls_policies.sql)
- [x] **FastAPI vereinfacht** (nur AI Agents)
- [x] **Edge Functions Templates** (create-trade, stripe-webhook)
- [x] **Next.js 16 App Setup** ⭐
- [x] **ESLint 9 mit Flat Config** (eslint.config.mjs)
- [x] **Supabase Client Integration** (@supabase/supabase-js, @supabase/ssr)
- [x] **Authentication (Email/Password)** - Login, Signup, Protected Routes
- [x] **Auth Pages erstellt** (Login, Signup, Dashboard)
- [x] **Middleware für Route Protection**

### 🚧 Phase 2: Trading Logic - IN PROGRESS (20%)
- [x] Trading rules documented
- [x] Validation engine concept
- [x] Risk management principles
- [ ] Market data fetcher (Twelve Data API)
- [ ] Technical indicators (EMA, RSI, MACD, BB, ATR)
- [ ] Trade validation engine
- [ ] Risk calculator

### 📋 Phase 3-5: See Master Roadmap
- [ ] Phase 3: AI Agents (ChartWatcher, SignalBot, RiskManager, JournalBot)
- [ ] Phase 4: Dashboard UX (shadcn/ui, Charts, Real-time updates)
- [ ] Phase 5: SaaS Features (Stripe, Publishing, Notifications)

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
| **Starter** | €29/mo | Daily reports, email alerts |
| **Pro** | €79/mo | All features + backtesting, API access |
| **Expert** | €199/mo | Custom strategies, priority support, WhatsApp alerts |

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

### Code
5. **Keine Redundanz** - Wenn Supabase es kann, nutze Supabase
6. **Server Components bevorzugen** - Next.js (weniger Client JS)
7. **TypeScript strikt** - Keine `any` types
8. **Environment Variables** - Nie Secrets committen

### Dokumentation
9. **Update während Entwicklung** - Nicht nachträglich
10. **Checklists nutzen** - TodoWrite tool für Tracking
11. **Status aktualisieren** - PROJECT_OVERVIEW.md Status immer aktuell

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
