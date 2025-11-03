# TradeMatrix.ai - Simplified Architecture

## Architektur-Prinzip: EINFACH & STRIKT

Wir folgen dem KISS-Prinzip (Keep It Simple, Stupid):
- **Nutze Managed Services** statt eigener Infrastruktur
- **Vermeide Redundanz** - Supabase übernimmt DB, Auth, Storage
- **FastAPI nur für AI** - Keine CRUD-Endpoints
- **Edge Functions für Webhooks** - Serverless wo möglich

---

## System-Übersicht

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                         │
│  Next.js 16 App Router (apps/web/)                     │
│  - React Server Components                              │
│  - Supabase Client für Auth & Data                     │
│  - TanStack Query für State Management                 │
└────────────┬────────────────────────────────────────────┘
             │
             │ HTTPS
             │
┌────────────┴──────────────┬──────────────────────────────┐
│                           │                              │
│   Supabase Platform       │      FastAPI Backend         │
│   (Primary Backend)       │      (AI Agents Only)        │
│                           │                              │
│ ┌─────────────────────┐   │   ┌────────────────────┐    │
│ │ PostgreSQL Database │   │   │  AI Agent Endpoints │    │
│ │ - Auto-generated    │   │   │  /api/agents/*     │    │
│ │   REST APIs         │   │   │                    │    │
│ │ - Row Level Security│   │   │  - ChartWatcher    │    │
│ └─────────────────────┘   │   │  - SignalBot       │    │
│                           │   │  - RiskManager     │    │
│ ┌─────────────────────┐   │   │  - JournalBot      │    │
│ │ Authentication      │   │   │  - Publisher       │    │
│ │ - Email/Password    │   │   └────────┬───────────┘    │
│ │ - Social Login      │   │            │                │
│ │ - JWT Tokens        │   │   ┌────────▼───────────┐    │
│ └─────────────────────┘   │   │  Celery Workers    │    │
│                           │   │  - Background AI   │    │
│ ┌─────────────────────┐   │   │  - LangChain       │    │
│ │ Storage (S3-like)   │   │   │  - OpenAI          │    │
│ │ - Charts (images)   │   │   └────────────────────┘    │
│ │ - Reports (PDFs)    │   │                              │
│ └─────────────────────┘   │            ▲                 │
│                           │            │                 │
│ ┌─────────────────────┐   │   ┌────────┴───────────┐    │
│ │ Edge Functions      │   │   │  Redis             │    │
│ │ (Serverless)        │   │   │  - Celery Broker   │    │
│ │ - Webhooks          │   │   │  - Result Backend  │    │
│ │ - Simple CRUD       │   │   │  - Caching         │    │
│ └─────────────────────┘   │   └────────────────────┘    │
│                           │                              │
└───────────────────────────┴──────────────────────────────┘
```

---

## Verantwortlichkeiten

### 1. Supabase (Primäres Backend)

**Database (PostgreSQL)**
- Auto-generierte REST APIs für alle Tabellen
- Real-time Subscriptions
- Full-text Search
- Row Level Security (RLS)

**Authentication**
- Email/Password Login
- Google OAuth (Social Login)
- GitHub OAuth (Optional)
- JWT Token Management
- Session Management
- No MagicLink (später mit Resend)

**Storage**
- Chart Images Upload
- PDF Report Storage
- Public/Private Bucket Policies

**Edge Functions** (Optional)
- Stripe Webhooks
- Simple Validations
- Serverless APIs

**Was Supabase NICHT macht:**
- ❌ Komplexe AI-Berechnungen
- ❌ Long-running Background Jobs
- ❌ Multi-step Workflows

---

### 2. FastAPI Backend (nur AI Agents!)

**Nur verantwortlich für:**
- ✓ AI Agent Orchestration
- ✓ Trigger für Celery Tasks
- ✓ Komplexe Business Logic
- ✓ Multi-step AI Workflows

**NICHT verantwortlich für:**
- ❌ CRUD Operations (macht Supabase)
- ❌ Authentication (macht Supabase)
- ❌ File Uploads (macht Supabase)
- ❌ Einfache Validierungen

**Endpoints (services/api/src/main.py):**
```
POST /api/agents/chart-analysis    → Trigger ChartWatcher
POST /api/agents/generate-signals  → Trigger SignalBot
POST /api/agents/risk-check        → Run RiskManager
POST /api/agents/generate-report   → Trigger JournalBot
GET  /api/agents/tasks/{id}        → Check Task Status
```

---

### 3. Next.js Frontend

**Server Components:**
- Direkte Supabase-Queries
- SEO-optimiert
- Schnelles Initial Rendering

**Client Components:**
- Supabase Client für Auth
- TanStack Query für Data Fetching
- Real-time Updates via Supabase

**Data Flow:**
```typescript
// Server Component - Direkt von Supabase
async function TradesPage() {
  const supabase = createServerClient()
  const { data: trades } = await supabase
    .from('trades')
    .select('*')
    .order('created_at', { ascending: false })

  return <TradesTable trades={trades} />
}

// Client Component - AI Agent Trigger
'use client'
function AnalyzeButton() {
  const { mutate } = useMutation({
    mutationFn: () => fetch('/api/agents/chart-analysis', { method: 'POST' })
  })

  return <button onClick={mutate}>Analyze Chart</button>
}
```

---

## Datenbank-Schema

### Kern-Tabellen

**profiles** - User-Profile (extends auth.users)
```sql
- id (UUID, FK to auth.users)
- email, full_name, avatar_url
- subscription_tier ('free' | 'starter' | 'pro' | 'expert')
- stripe_customer_id, stripe_subscription_id
```

**trades** - Handels-Aufzeichnungen
```sql
- id, user_id
- symbol, side ('long' | 'short')
- entry_price, exit_price, position_size
- stop_loss, take_profit
- pnl, pnl_percentage
- status ('open' | 'closed' | 'cancelled')
```

**reports** - AI-generierte Reports
```sql
- id, user_id
- title, content, report_type
- ai_summary, ai_insights (JSONB)
- status ('draft' | 'published' | 'archived')
- chart_urls[], pdf_url
```

**agent_logs** - AI Agent Ausführungen
```sql
- id, user_id, agent_type
- task_id, status, input_data, output_data
- started_at, completed_at, duration_ms
```

---

## Authentifizierung & Authorization

### Auth Flow (Supabase)

```typescript
// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Session Check
const { data: { session } } = await supabase.auth.getSession()

// Logout
await supabase.auth.signOut()
```

### Row Level Security (RLS)

Automatisch durch Supabase:
```sql
-- Nutzer sehen nur eigene Trades
CREATE POLICY "Users can view own trades"
  ON trades FOR SELECT
  USING (auth.uid() = user_id);

-- Publizierte Reports sind öffentlich
CREATE POLICY "Published reports are public"
  ON reports FOR SELECT
  USING (status = 'published');
```

### Subscription-basierte Features

```typescript
// Check Subscription Tier
const { data: profile } = await supabase
  .from('profiles')
  .select('subscription_tier')
  .eq('id', userId)
  .single()

// Feature Gate
if (profile.subscription_tier === 'free') {
  throw new Error('Upgrade to Pro for AI Analysis')
}
```

---

## AI Agents Architektur

### Celery Task Flow

```python
# services/agents/src/tasks.py

from celery import Celery
from config import supabase_admin

celery = Celery('tradematrix', broker=REDIS_URL)

@celery.task(name='analyze_chart')
def analyze_chart_task(user_id: str, chart_url: str):
    """Background task: Analyze chart with AI"""

    # Log start
    log_id = supabase_admin.table('agent_logs').insert({
        'user_id': user_id,
        'agent_type': 'chart_watcher',
        'status': 'running',
        'input_data': {'chart_url': chart_url}
    }).execute().data[0]['id']

    try:
        # AI Logic here (LangChain + OpenAI)
        result = chart_watcher.analyze(chart_url)

        # Log completion
        supabase_admin.table('agent_logs').update({
            'status': 'completed',
            'output_data': result,
            'completed_at': 'now()'
        }).eq('id', log_id).execute()

        return result

    except Exception as e:
        # Log error
        supabase_admin.table('agent_logs').update({
            'status': 'failed',
            'error_message': str(e)
        }).eq('id', log_id).execute()
        raise
```

### Agents

**ChartWatcher** - services/agents/src/chart_watcher.py
- Downloads chart from Supabase Storage
- OCR to extract values
- Pattern detection (LangChain)

**SignalBot** - services/agents/src/signal_bot.py
- Analyzes market structure
- Generates entry/exit signals
- Confidence scoring

**RiskManager** - services/agents/src/risk_manager.py
- Position size calculation
- Stop-loss/Take-profit zones
- Risk/Reward validation

**JournalBot** - services/agents/src/journal_bot.py
- Auto-generates trade reports
- AI summaries with insights
- Saves to Supabase

---

## Deployment

### Supabase (Managed)
```bash
1. Create project at supabase.com
2. Run migrations in SQL Editor
3. Deploy Edge Functions: supabase functions deploy
4. Configure Auth providers
5. Create Storage buckets
```

### FastAPI (Railway/Fly.io)
```bash
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY services/api/src .
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Next.js (Vercel)
```bash
vercel --prod
# Auto-deploys from GitHub
```

### Celery Workers (Railway)
```bash
# Separate service
celery -A tasks worker --loglevel=info
```

---

## Kosten-Optimierung

### Supabase Free Tier
- ✓ 500 MB Database
- ✓ 1 GB Storage
- ✓ 50,000 monthly active users
- ✓ Unlimited Edge Function invocations

**Genug für MVP!**

### Bezahlte Services (später)
- Railway: ~$5/Monat (FastAPI + Celery)
- Upstash Redis: ~$0.20/Monat
- Vercel: Free (Next.js)
- OpenAI: Pay-per-use

**Total: ~$5-10/Monat bis zu 1000 Nutzern**

---

## Migration von alter Architektur

### Entfernt:
- ❌ SQLAlchemy & Alembic (ersetzt durch Supabase)
- ❌ python-jose & passlib (ersetzt durch Supabase Auth)
- ❌ psycopg2-binary (nicht mehr nötig)
- ❌ python-multipart (Supabase Storage)

### Behalten:
- ✓ FastAPI (für AI Agents)
- ✓ Celery + Redis (Background Tasks)
- ✓ OpenAI + LangChain (AI)
- ✓ Pydantic (Validation)

### Neu hinzugefügt:
- ✓ supabase-py (Python Client)
- ✓ @supabase/supabase-js (TypeScript Client)

---

## Best Practices

1. **Nutze Supabase für CRUD** - Nie eigene Endpoints dafür bauen
2. **RLS aktivieren** - Immer Row Level Security nutzen
3. **Edge Functions für Webhooks** - Nicht FastAPI
4. **FastAPI nur für AI** - Sonst nichts
5. **Server Components bevorzugen** - Wo möglich
6. **Environment Variables** - Nie Secrets committen

---

## Nächste Schritte

1. ✅ Supabase Projekt erstellen
2. ✅ Migrationen ausführen
3. ⏳ Storage Buckets konfigurieren
4. ⏳ Auth Provider aktivieren
5. ⏳ Edge Functions deployen
6. ⏳ FastAPI auf Railway deployen
7. ⏳ Celery Worker starten
8. ⏳ Next.js auf Vercel deployen

---

## Market Data Architecture (Updated 2025-11-03)

### Display Layer: TradingView Widgets 🆕

**Decision:** Use TradingView Widgets for live price display (free, no backend needed)

**Architecture:**
```
User Dashboard
    ↓
Fetch user_watchlist from Supabase (max 10 symbols)
    ↓
Render TradingView Widgets (one per symbol)
    ↓
TradingView fetches live prices directly (no backend!)
```

**Benefits:**
- ✅ **€0 cost** for live prices
- ✅ **No WebSocket** server needed
- ✅ **Unlimited symbols** (no API limits)
- ✅ **Auto-updates** (TradingView handles)

### Alert Layer: Hetzner Backend

**Decision:** Keep Hetzner server ONLY for liquidity alerts (not for price display)

**Architecture:**
```
Celery Beat (every 60s)
    ↓
Query user_watchlist (get unique symbols)
    ↓
Fetch prices:
  - Indices: yfinance (HTTP, free)
  - Forex: Twelvedata (HTTP, $29/mo)
    ↓
Check liquidity levels (Yesterday High/Low, Pivot Points)
    ↓
Send push notifications if triggered
```

**No WebSocket Needed:** HTTP polling sufficient for alerts (60s latency acceptable)

**See:** [docs/FEATURES/tradingview-watchlist/01_ARCHITECTURE.md](./FEATURES/tradingview-watchlist/01_ARCHITECTURE.md)

---

**Fragen? Siehe:**
- [Supabase Setup](../services/api/supabase/README.md)
- [Edge Functions](../services/api/supabase/functions/README.md)
- [FastAPI Endpoints](../services/api/src/main.py)
- [TradingView Watchlist Feature](./FEATURES/tradingview-watchlist/README.md) 🆕
