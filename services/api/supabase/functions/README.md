# Supabase Edge Functions

Serverless TypeScript functions that run on Supabase infrastructure.

## Available Functions

### create-trade
Creates a new trade record with validation.

**Endpoint:** `POST /functions/v1/create-trade`

**Payload:**
```json
{
  "symbol": "BTCUSD",
  "side": "long",
  "entry_price": 50000,
  "position_size": 0.1,
  "stop_loss": 49000,
  "take_profit": 52000,
  "notes": "Breakout setup",
  "tags": ["breakout", "btc"]
}
```

### stripe-webhook
Handles Stripe subscription webhooks.

**Endpoint:** `POST /functions/v1/stripe-webhook`

**Events handled:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

## Setup

1. **Install Supabase CLI:**
```bash
npm install -g supabase
```

2. **Link to your project:**
```bash
supabase link --project-ref your-project-ref
```

3. **Deploy functions:**
```bash
# Deploy all
supabase functions deploy

# Deploy specific function
supabase functions deploy create-trade
supabase functions deploy stripe-webhook
```

4. **Set secrets:**
```bash
supabase secrets set STRIPE_SECRET_KEY=sk_...
supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_...
```

## Local Development

```bash
# Start local Supabase
supabase start

# Serve functions locally
supabase functions serve

# Test function
curl -i --location --request POST 'http://localhost:54321/functions/v1/create-trade' \
  --header 'Authorization: Bearer YOUR_ANON_KEY' \
  --header 'Content-Type: application/json' \
  --data '{"symbol":"BTCUSD","side":"long","entry_price":50000,"position_size":0.1}'
```

## Why Edge Functions?

**Use Edge Functions for:**
- Webhooks (Stripe, external APIs)
- Simple CRUD with validation
- Serverless background jobs
- Public APIs without auth

**Use FastAPI for:**
- Complex AI agent orchestration
- Long-running background tasks (Celery)
- Heavy computations
- Multi-step workflows

## Architecture Decision

```
┌─────────────────────────────────────────┐
│           Client (Next.js)              │
└────────────┬────────────────┬───────────┘
             │                │
             │                │
   ┌─────────▼──────┐  ┌──────▼─────────┐
   │   Supabase     │  │   FastAPI      │
   │  Edge Functions│  │  (AI Agents)   │
   │                │  │                │
   │ - CRUD ops     │  │ - AI tasks     │
   │ - Webhooks     │  │ - Analytics    │
   │ - Validation   │  │ - Celery jobs  │
   └────────┬───────┘  └────────┬───────┘
            │                   │
            └───────┬───────────┘
                    │
            ┌───────▼────────┐
            │   Supabase     │
            │   PostgreSQL   │
            └────────────────┘
```

## Best Practices

1. **Keep functions small** - Single responsibility
2. **Use RLS** - Row Level Security for data access
3. **Validate input** - Always validate request data
4. **Handle errors** - Proper error messages and status codes
5. **Log events** - Use console.log for debugging
6. **Set timeouts** - Edge Functions have 60s timeout
