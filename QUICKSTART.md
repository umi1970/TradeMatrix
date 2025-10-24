# TradeMatrix.ai - Schnellstart

## 1. Supabase Setup (5 Minuten)

### Projekt erstellen
1. Gehe zu https://supabase.com
2. Klicke "New Project"
3. Name: `tradematrix-dev`
4. Region: Nächstgelegene (Frankfurt/EU)
5. Strong password generieren lassen
6. Klicke "Create new project" (dauert ~2 Minuten)

### Datenbank-Migrationen ausführen
1. Öffne SQL Editor (links im Dashboard)
2. Klicke "New query"
3. Kopiere Inhalt von `services/api/supabase/migrations/001_initial_schema.sql`
4. Klicke "Run"
5. Wiederhole für `002_rls_policies.sql`

### Storage Buckets erstellen
1. Gehe zu "Storage" (links im Dashboard)
2. Klicke "New bucket"
   - Name: `charts`
   - Public: No (Private)
3. Nochmal "New bucket"
   - Name: `reports`
   - Public: No (Private)

### Environment Variables kopieren
1. Gehe zu "Settings" > "API"
2. Kopiere folgende Werte:

```bash
# .env (Root-Verzeichnis)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...  # "anon public" key
SUPABASE_SERVICE_KEY=eyJhbGc...  # "service_role" key (geheim!)
```

---

## 2. Backend Setup (FastAPI)

### Installation
```bash
cd services/api

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

### Environment Variables
```bash
# services/api/.env erstellen
cp .env.example .env

# Füge deine Supabase-Credentials ein:
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...

# Optional (für lokale Entwicklung):
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
```

### Server starten
```bash
cd src
uvicorn main:app --reload

# Server läuft auf http://localhost:8000
# Teste: http://localhost:8000/api/health
```

---

## 3. Frontend Setup (Next.js)

### Installation
```bash
cd apps/web

# Dependencies installieren
npm install
# oder
pnpm install
```

### Environment Variables
```bash
# apps/web/.env.local erstellen
cp .env.example .env.local

# Füge deine Supabase-Credentials ein:
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Dev Server starten
```bash
npm run dev
# oder
pnpm dev

# Server läuft auf http://localhost:3000
```

---

## 4. Redis & Celery (für AI Agents)

### Redis starten (Docker)
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Celery Worker starten
```bash
cd services/agents

# Virtual Environment
python -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Worker starten
celery -A tasks worker --loglevel=info
```

---

## 5. Testen

### Backend
```bash
# Health Check
curl http://localhost:8000/api/health

# Expected:
# {"status":"ok","database":"connected","environment":"development"}
```

### Frontend
```bash
# Browser öffnen
open http://localhost:3000

# Du solltest die TradeMatrix.ai Homepage sehen
```

---

## 6. Nächste Schritte

### Supabase Auth konfigurieren
1. Gehe zu "Authentication" > "Providers"
2. Enable "Email" provider
3. Optional: Enable "Google", "GitHub" etc.

### Edge Functions deployen (optional)
```bash
# Supabase CLI installieren
npm install -g supabase

# Login
supabase login

# Link project
supabase link --project-ref xxxxx

# Deploy functions
cd services/api
supabase functions deploy
```

### Stripe Integration (optional)
1. Erstelle Account auf https://stripe.com
2. Kopiere API Keys (Test Mode)
3. Füge zu `.env` hinzu:
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 🎉 Fertig!

Du hast jetzt:
- ✅ Supabase Database mit Schema
- ✅ FastAPI Backend (AI Agents)
- ✅ Next.js Frontend
- ✅ Redis + Celery (Background tasks)

**Entwickeln:**
```bash
# Terminal 1: Backend
cd services/api/src && uvicorn main:app --reload

# Terminal 2: Frontend
cd apps/web && npm run dev

# Terminal 3: Celery (optional)
cd services/agents && celery -A tasks worker --loglevel=info
```

**Dokumentation:**
- [Architektur](docs/ARCHITECTURE.md)
- [Supabase Setup](services/api/supabase/README.md)
- [Edge Functions](services/api/supabase/functions/README.md)
- [Development Workflow](docs/DEVELOPMENT_WORKFLOW.md)

---

## Probleme?

### "Database connection failed"
→ Check `SUPABASE_URL` und `SUPABASE_KEY` in `.env`

### "Module not found"
→ `pip install -r requirements.txt` bzw. `npm install`

### "Port already in use"
→ Ändere Port in `uvicorn main:app --port 8001`

### "Celery connection refused"
→ Starte Redis: `docker run -d -p 6379:6379 redis:7-alpine`
