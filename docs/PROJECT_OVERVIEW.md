# TradeMatrix.ai - Project Overview

**Version:** 1.2.0
**Status:** ✅ Phase 1-4 Complete - Phase 5 Liquidity Alerts DEPLOYED TO PRODUCTION
**Last Updated:** 2025-11-01

---

## 🎯 Vision

TradeMatrix.ai is an AI-powered, fully automated trading analysis system focused on:
- **Markets:** DAX, NASDAQ, Dow Jones, Forex (EUR/USD, etc.)
- **Core Features:** Technical analysis, AI pattern recognition, automated reporting
- **Business Model:** SaaS with subscription tiers (Free, Starter, Pro, Expert)

**Goal:** Combine technical analysis, AI-based pattern recognition, and automated reporting in the form of daily and weekly market reports.

---

## 🏗️ Architecture Overview

### Tech Stack (Simplified!)

**Frontend:**
- Next.js 16 (React 19.2, Turbopack, PPR, React Compiler)
- TypeScript 5.x
- ESLint 9 (Flat Config)
- Tailwind CSS + shadcn/ui
- TradingView Lightweight Charts
- Supabase JS Client (@supabase/supabase-js, @supabase/ssr)

**Backend (Supabase - All-in-One):**
- PostgreSQL Database (auto-generated REST APIs)
- Authentication (Email, Social Login, JWT)
- Storage (Charts, PDFs)
- Edge Functions (Webhooks, Serverless)
- Row Level Security (RLS)

**Backend (FastAPI - AI Agents Only):**
- AI Agent orchestration
- Celery + Redis (Background AI tasks)
- OpenAI API + LangChain (AI agents)
- Complex business logic

**Infrastructure:**
- Supabase (Database + Auth + Storage)
- Railway/Fly.io (FastAPI + Celery)
- Netlify (Next.js Frontend) ✅ Live: https://tradematrix.netlify.app
- Upstash (Redis)

---

## 📁 Repository Structure

```
TradeMatrix/
├── apps/
│   └── web/                    # Next.js 16 Frontend
│       └── src/
│           ├── app/            # App Router
│           ├── components/     # React Components
│           ├── lib/            # Utilities
│           └── styles/         # Global styles
│
├── services/
│   ├── api/                    # FastAPI Backend
│   │   └── src/
│   │       ├── core/           # Core modules (MarketFetcher, Analyzer, etc.)
│   │       ├── api/            # API routes
│   │       ├── models/         # Database models
│   │       └── schemas/        # Pydantic schemas
│   │
│   └── agents/                 # AI Agents
│       └── src/
│           ├── chart_watcher.py
│           ├── signal_bot.py
│           ├── risk_manager.py
│           └── journal_bot.py
│
├── packages/
│   ├── ui/                     # Shared UI components
│   ├── database/               # Database schemas & migrations
│   └── shared/                 # Shared types & utilities
│
├── docs/                       # Documentation (YOU ARE HERE!)
│   ├── 00_MASTER_ROADMAP.md    # 👈 Complete 5-phase roadmap!
│   ├── PROJECT_OVERVIEW.md     # 👈 Start here every session!
│   ├── DEVELOPMENT_WORKFLOW.md # How to develop features
│   ├── ARCHITECTURE.md         # System design (Supabase)
│   ├── FEATURES/               # Feature planning & checklists
│   ├── ARCHIVE/                # Old documentation (pre-Supabase)
│   ├── STRATEGIES/             # Trading strategies
│   └── ...
│
└── config/
    ├── rules/                  # Trading rules (YAML)
    └── settings/               # App settings
```

---

## 🎨 Design System - "Matrix Black"

| Color | Hex | Usage |
|-------|-----|-------|
| Matrix Black | `#0C0C0C` | Background (Dark Mode) |
| Signal Blue | `#0070F3` | Primary actions, buttons |
| Logic Gray | `#E0E0E0` | Secondary text, borders |
| Profit Green | `#00D084` | Positive trades |
| Risk Red | `#FF3B30` | Losses, warnings |

---

## 🤖 Core Modules

| Module | Description |
|--------|-------------|
| **MarketDataFetcher** | Fetches real-time data (DAX, Dow, Forex) via APIs or OCR |
| **AI-Analyzer** | Analyzes price structure, recognizes chart patterns, EMAs, gaps |
| **TradeDecisionEngine** | Evaluates signals based on rule sets (EMA crosses, pivots) |
| **TradeJournalWriter** | Generates DOCX/PDF reports from completed trades |
| **ReportPublisher** | Publishes daily & weekly reports as blog posts |

---

## 🤖 AI Agents

| Agent | Role |
|-------|------|
| **ChartWatcher** | Monitors charts, extracts values, detects patterns |
| **SignalBot** | Evaluates market structure, decides entries/exits |
| **RiskManager** | Calculates position sizes, sets SL/TP zones |
| **JournalBot** | Creates automated reports and journal entries |
| **Publisher** | Uploads reports to subdomain/blog |

---

## 📊 Trading Rules

### Core Principles
- **Trading Hours:** 08:00 - 22:00 (Broker time)
- **Risk Management:** Max 1% per trade
- **Stop Loss & Take Profit:** Must be set before order execution
- **Daily Rule:** After 3 losing trades, pause until next trading day

### Setup Types
1. **EMA-Cross:** EMA 20 crosses EMA 50, EMA 200 as trend filter
2. **Pivot-Reversal:** Reaction at Daily/Weekly Pivot with candlestick reversal
3. **Gap-Close:** Price closes open gaps
4. **Smart-Money-Pattern:** Long bias on 1st trading day of month

---

## 💰 Subscription Tiers

| Plan | Price | Features |
|------|-------|----------|
| **Free** | €0/mo | Basic market overview, limited reports |
| **Starter €9/mo | Daily reports, email alerts |
| **Pro €39/mo | All features + backtesting, API access |
| **Expert €79/mo | Custom strategies, priority support, WhatsApp alerts |

---

## 🚀 Current Status

> **See [00_MASTER_ROADMAP.md](./00_MASTER_ROADMAP.md) for complete 5-phase roadmap!**

### ✅ Phase 1-4: Foundation to Dashboard - COMPLETED (100%)
- [x] Project structure, documentation, Supabase integration
- [x] Next.js 16, Authentication, Protected Routes
- [x] Database schema with RLS policies
- [x] Trading rules, Validation engine, Risk management
- [x] Market data fetcher, Technical indicators
- [x] Dashboard UI with shadcn/ui components
- [x] Real-time features with Supabase Realtime

### ✅ Phase 5A: Liquidity Alert System - DEPLOYED TO PRODUCTION (100%)
- [x] **EOD Data Layer** - 86,469+ records (DAX, NASDAQ, DOW, EUR/USD, EUR/GBP)
- [x] **EOD Levels Calculation** - 100% complete (Yesterday High/Low, Pivot Points)
- [x] **Dashboard Widgets** - 8 new widgets (EOD Levels Today, Market Sentiment, Trade Performance, etc.)
- [x] **Liquidity Alert Engine** - Real-time price monitoring every 60 seconds
- [x] **Browser Push Notifications** - VAPID keys configured, Web Push API
- [x] **Hetzner Production Deployment** - CX11 server running 24/7
  - Server: 135.181.195.241 (2 vCPU, 4GB RAM, 40GB SSD)
  - Services: Redis 7-alpine, Celery Worker, Celery Beat
  - Repository: `hetzner-deploy/` (Docker Compose)
  - Latest commit: 6f952fb (JSON serialization fix)

### 🚧 Phase 5C: Editable Market Watchlist - IN PROGRESS (15%)
- [x] **Database:** user_watchlist table + RLS (Migration 017) ✅
- [ ] **Frontend:** TradingView Widget component
- [ ] **Frontend:** Symbol Picker modal (add/remove symbols)
- [ ] **Frontend:** Dashboard integration (replace market cards)
- [ ] **Backend:** Dynamic symbol loading (Hetzner alert_engine.py)
- [ ] **Deployment:** Netlify + Hetzner updates

**Architecture:** Hybrid approach (TradingView Widgets for display + Hetzner for alerts)
**See:** [docs/FEATURES/tradingview-watchlist/README.md](./FEATURES/tradingview-watchlist/README.md)

### 🚧 Phase 5B: Stripe Integration & SaaS Features - PLANNED
- [ ] Stripe subscription billing
- [ ] Subscription management (upgrade/downgrade)
- [ ] Usage tracking & limits
- [ ] Email notifications
- [ ] Report publishing (subdomain/blog)
- [ ] WhatsApp alerts (Expert tier)

### 🎯 Next Immediate Steps
1. ✅ ~~Implement MarketDataFetcher (Twelve Data API)~~ - COMPLETE
2. ✅ ~~Create TechnicalIndicators module (EMA, RSI, MACD, etc.)~~ - COMPLETE
3. Integrate TechnicalIndicators with ValidationEngine
4. Implement RiskCalculator
5. Create trading signal generator

---

## 📝 For New Sessions

**When starting a new chat/session:**

1. **Read** [CLAUDE.md](../CLAUDE.md) **first** (session onboarding!)
2. **Review** [00_MASTER_ROADMAP.md](./00_MASTER_ROADMAP.md) (complete roadmap)
3. Check this file (`PROJECT_OVERVIEW.md`) for current status
4. Review `DEVELOPMENT_WORKFLOW.md` for feature development process
5. Check implementation checklists for pending tasks

**Quick Links:**
- [Master Roadmap](./00_MASTER_ROADMAP.md) 👈 **NEW!**
- [Architecture (Supabase-based)](./ARCHITECTURE.md)
- [Development Workflow](./DEVELOPMENT_WORKFLOW.md)
- [Features](./FEATURES/)
- [Supabase Setup](../services/api/supabase/README.md)

---

## 🔗 Important Links

- **Repository:** github.com/umi1970/TradeMatrix
- **Branch:** `main`
- **Live App:** https://tradematrix.netlify.app ✅
- **Documentation:** `/docs`

---

**Remember:** This is a SaaS product. Focus on scalability, user experience, and automated workflows!
