# TradeMatrix.ai

**AI-Powered Trading Analysis & Automation Platform**

[![Status](https://img.shields.io/badge/status-in%20development-yellow)](https://github.com/umi1970/TradeMatrix)
[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)

---

## 🎯 Vision

TradeMatrix.ai combines **technical analysis**, **AI-powered pattern recognition**, and **automated reporting** to deliver professional trading insights for DAX, NASDAQ, Dow Jones, and Forex markets.

### Key Features
- 📊 Real-time market data analysis
- 🤖 AI-powered chart pattern recognition
- 📈 Automated trading signals (EMA-Cross, Pivot-Reversal, Gap-Close, Smart-Money)
- 📝 Daily & weekly market reports
- 🔐 Multi-tier SaaS subscription model (Free, Starter, Pro, Expert)

---

## 🏗️ Project Structure

```
TradeMatrix/
├── apps/
│   └── web/                    # Next.js 16 Frontend
│       └── src/
│           ├── app/            # App Router (React 19.2)
│           ├── components/     # React Components
│           ├── lib/            # Utilities
│           └── styles/         # Global Styles
│
├── services/
│   ├── api/                    # FastAPI Backend
│   │   └── src/
│   │       ├── core/           # Market Fetcher, Analyzer, Decision Engine
│   │       ├── api/            # REST API Routes
│   │       ├── models/         # Database Models
│   │       └── schemas/        # Pydantic Schemas
│   │
│   └── agents/                 # AI Agents
│       └── src/
│           ├── chart_watcher.py    # Chart monitoring
│           ├── signal_bot.py       # Signal detection
│           ├── risk_manager.py     # Risk calculations
│           └── journal_bot.py      # Report generation
│
├── packages/
│   ├── ui/                     # Shared UI Components
│   ├── database/               # Database Schemas & Migrations
│   └── shared/                 # Shared Types & Utilities
│
├── docs/                       # 📚 Comprehensive Documentation
│   ├── PROJECT_OVERVIEW.md     # 👈 Start here!
│   ├── DEVELOPMENT_WORKFLOW.md # Development process
│   ├── ARCHITECTURE/           # System architecture
│   ├── FEATURES/               # Feature planning & checklists
│   │   └── _template/          # Templates for new features
│   ├── STRATEGIES/             # Trading strategies
│   └── ...
│
└── config/
    ├── rules/                  # Trading rules (YAML)
    └── settings/               # Application settings
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ (for Next.js 16)
- **Python** 3.11+ (for FastAPI)
- **PostgreSQL** 15+
- **Redis** 7+
- **Docker** (optional, for local development)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/umi1970/TradeMatrix.git
cd TradeMatrix

# Install dependencies (to be set up)
# Frontend
cd apps/web && npm install

# Backend
cd services/api && pip install -r requirements.txt

# Start development servers
# (detailed instructions coming soon)
```

### Documentation

**New here? Start with these docs:**
1. [📖 Project Overview](./docs/PROJECT_OVERVIEW.md) - Understand the project
2. [🛠️ Development Workflow](./docs/DEVELOPMENT_WORKFLOW.md) - Learn how to develop features
3. [🏛️ Architecture](./docs/ARCHITECTURE/) - System design
4. [⚙️ Setup Guide](./docs/SETUP/) - Development environment setup

---

## 🎨 Design System - "Matrix Black"

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Matrix Black** | `#0C0C0C` | Background, Dark Mode |
| **Signal Blue** | `#0070F3` | Primary actions, CTAs |
| **Logic Gray** | `#E0E0E0` | Secondary text, borders |
| **Profit Green** | `#00D084` | Positive trades, success states |
| **Risk Red** | `#FF3B30` | Losses, warnings, errors |

---

## 🤖 Core Modules

| Module | Purpose |
|--------|---------|
| **MarketDataFetcher** | Real-time market data ingestion |
| **AI-Analyzer** | Chart pattern recognition with AI |
| **TradeDecisionEngine** | Signal evaluation based on rule sets |
| **TradeJournalWriter** | Automated report generation |
| **ReportPublisher** | Content distribution & publishing |

---

## 📊 Trading Strategies

### Rule-Based Setups
1. **EMA-Cross:** EMA 20 × EMA 50 (EMA 200 trend filter)
2. **Pivot-Reversal:** Daily/Weekly Pivot reactions
3. **Gap-Close:** Price closing open gaps
4. **Smart-Money-Pattern:** 1st trading day bias

### Risk Management
- Max risk: **1% per trade**
- Trading hours: **08:00 - 22:00** (Broker time)
- Stop-loss & take-profit **required** before entry
- **3 losses = pause** until next trading day

---

## 💰 Subscription Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | €0/mo | Basic market overview |
| **Starter** | €29/mo | Daily reports, email alerts |
| **Pro** | €79/mo | All features + backtesting + API |
| **Expert** | €199/mo | Custom strategies + priority support |

---

## 🛠️ Tech Stack

### Frontend
- **Next.js 16** (React 19.2, Turbopack, PPR)
- **TypeScript** 5.x
- **Tailwind CSS** 3.x + **shadcn/ui**
- **TradingView Lightweight Charts**

### Backend
- **FastAPI** 0.110+
- **SQLAlchemy** 2.x ORM
- **Celery** + **Redis** (Background jobs)
- **OpenAI API** + **LangChain** (AI agents)

### Infrastructure
- **PostgreSQL** (User data, trades, reports)
- **Redis** (Caching, job queue)
- **Docker Compose** (Local dev)
- **GitHub Actions** (CI/CD)
- **Vercel** (Frontend) + **Railway/Fly.io** (Backend)

---

## 📈 Current Status

### ✅ Completed
- [x] Repository structure
- [x] Documentation system
- [x] Feature planning templates

### 🚧 In Progress
- [ ] Next.js 16 app setup
- [ ] FastAPI backend setup
- [ ] Database schema design
- [ ] AI agent framework

### 📋 Planned
- [ ] Authentication & authorization
- [ ] Stripe subscription integration
- [ ] Market data pipeline
- [ ] Chart analysis system
- [ ] Report generator
- [ ] Admin dashboard

---

## 🤝 Contributing

This is currently a private project in development. Contribution guidelines will be added once the project reaches a stable state.

---

## 📄 License

Proprietary - All rights reserved

---

## 📞 Contact

**Developer:** umi1970
**Project:** TradeMatrix.ai
**Repository:** [github.com/umi1970/TradeMatrix](https://github.com/umi1970/TradeMatrix)

---

## 🙏 Acknowledgments

- Built with [Next.js 16](https://nextjs.org/)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- AI by [OpenAI](https://openai.com/)
- Charts by [TradingView](https://www.tradingview.com/)

---

**Made with 🧠 for traders by developers**
