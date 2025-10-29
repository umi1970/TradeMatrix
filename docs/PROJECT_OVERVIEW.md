# TradeMatrix.ai - Project Overview

**Version:** 1.0.0
**Status:** 🚧 In Development (MVP Phase)
**Last Updated:** 2025-10-26

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
- Vercel (Next.js Frontend)
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
│   ├── PROJECT_OVERVIEW.md     # 👈 Start here every session!
│   ├── DEVELOPMENT_WORKFLOW.md # How to develop features
│   ├── ARCHITECTURE/           # System design
│   ├── FEATURES/               # Feature planning & checklists
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
| **Starter** | €29/mo | Daily reports, email alerts |
| **Pro** | €79/mo | All features + backtesting, API access |
| **Expert** | €199/mo | Custom strategies, priority support, WhatsApp alerts |

---

## 🚀 Current Status

### ✅ Completed
- [x] Project structure setup
- [x] Documentation system
- [x] Backend architecture simplified (Supabase integration)
- [x] Database schema designed (SQL migrations ready)
- [x] Supabase project created ("tradematrix Projekt")
- [x] Database migrations executed (001_initial_schema.sql, 002_rls_policies.sql)
- [x] FastAPI simplified to AI agents only
- [x] Edge Functions templates created
- [x] **Next.js 16 app setup** ⭐ (App Router, React 19.2)
- [x] **ESLint 9 with Flat Config** (eslint.config.mjs)
- [x] **Supabase client integration** (@supabase/supabase-js, @supabase/ssr)
- [x] **Authentication (Email/Password)** - Signup, Login, Protected Routes
- [x] **Auth pages** - Login, Signup, Dashboard with middleware protection

### 🚧 In Progress
- [ ] Google OAuth integration (prepared, needs Supabase configuration)

### 📋 Planned
- [ ] UI components library (shadcn/ui)
- [ ] User profile & settings page
- [ ] AI agent implementation (ChartWatcher, SignalBot, etc.)
- [ ] Subscription/billing integration (Stripe webhooks)
- [ ] Chart analysis system
- [ ] Report generator
- [ ] Storage bucket configuration

---

## 📝 For New Sessions

**When starting a new chat/session:**

1. **Read this file first** (`docs/PROJECT_OVERVIEW.md`)
2. Check `docs/DEVELOPMENT_WORKFLOW.md` for feature development process
3. Review current features in `docs/FEATURES/`
4. Check implementation checklists for pending tasks

**Quick Links:**
- [Development Workflow](./DEVELOPMENT_WORKFLOW.md)
- [Architecture (Supabase-based)](./ARCHITECTURE.md) 👈 **NEU!**
- [Features](./FEATURES/)
- [Supabase Setup](../services/api/supabase/README.md)

---

## 🔗 Important Links

- **Repository:** github.com/umi1970/TradeMatrix
- **Branch:** `claude/init-saas-project-011CUS1no4jgfoELpLgTnhch`
- **Documentation:** `/docs`

---

**Remember:** This is a SaaS product. Focus on scalability, user experience, and automated workflows!
