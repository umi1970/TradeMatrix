# TradeMatrix.ai Supabase Setup

## Quick Start

1. **Create a Supabase project** at https://supabase.com
2. **Run migrations** in Supabase SQL Editor (in order):
   - `001_initial_schema.sql`
   - `002_rls_policies.sql`
3. **Create storage buckets**:
   - `charts` (for chart images)
   - `reports` (for PDF reports)
4. **Copy credentials** to `.env`:
   - URL: Settings > API > Project URL
   - Anon key: Settings > API > anon public
   - Service key: Settings > API > service_role

## Environment Variables

```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc... # anon key
SUPABASE_SERVICE_KEY=eyJhbGc... # service_role key
```

## Database Schema

### Tables

**profiles** - User profiles (extends auth.users)
- Subscription tier and status
- Stripe customer/subscription IDs

**trades** - Trade records
- Entry/exit prices, position size
- Stop loss, take profit
- P&L tracking

**reports** - Market analysis reports
- AI-generated insights
- Published/draft status
- Chart and PDF references

**agent_logs** - AI agent execution logs
- Task tracking
- Performance metrics

**subscriptions** - Stripe subscription events
- Billing periods
- Cancellation tracking

## Row Level Security (RLS)

All tables have RLS enabled:
- Users can only access their own data
- Published reports are public
- System (service_role) can write agent logs

## Storage Buckets

**charts/**
- `{user_id}/private/` - Private charts
- `{user_id}/public/` - Published charts

**reports/**
- `{user_id}/private/` - Draft reports
- `{user_id}/public/` - Published reports

## Supabase Features Used

✓ **Database** - PostgreSQL with auto-generated APIs
✓ **Authentication** - Email/password, social login
✓ **Storage** - File uploads for charts/PDFs
✓ **Row Level Security** - Data isolation per user
✓ **Real-time** - Live updates for trades (optional)
✓ **Edge Functions** - Serverless functions (see below)

## Next Steps

1. Enable Email Auth in Supabase Dashboard
2. Configure Email templates (optional)
3. Set up storage buckets with policies
4. Deploy Edge Functions (optional, see `/supabase/functions/`)
