# Supabase Migrations

This directory contains SQL migration files for the TradeMatrix.ai database schema.

## Migration Files

| Migration | Status | Description | Date |
|-----------|--------|-------------|------|
| `001_initial_schema.sql` | ✅ Applied | Initial database schema (users, profiles, subscriptions) | 2025-10-26 |
| `002_rls_policies.sql` | ✅ Applied | Row Level Security policies | 2025-10-26 |
| `003_market_data_schema.sql` | 🔄 Ready | Market data schema (symbols, OHLC, levels, setups, alerts) | 2025-10-29 |

## How to Apply Migrations

### Method 1: Supabase SQL Editor (Recommended)

1. Open [SQL Editor](https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/sql/new)
2. Copy the content of the migration file
3. Paste into SQL Editor
4. Click "Run" (or press `Ctrl+Enter`)

### Method 2: Helper Script

```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/api/supabase
./quick_apply_migration_003.sh
```

### Method 3: PostgreSQL CLI (requires DB password)

```bash
# Get password from: https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/settings/database
export PGPASSWORD="your-db-password"

psql "postgresql://postgres:$PGPASSWORD@db.htnlhazqzpwfyhnngfsn.supabase.co:5432/postgres" \
  -f migrations/003_market_data_schema.sql
```

### Method 4: Supabase CLI (if installed)

```bash
cd services/api/supabase
supabase db push --db-url "postgresql://postgres:[PASSWORD]@db.htnlhazqzpwfyhnngfsn.supabase.co:5432/postgres"
```

## Migration 003 Details

### Tables Created:

1. **market_symbols** - Tradable symbols (DAX, NASDAQ, DOW, Forex)
2. **ohlc** - OHLCV candle data (all timeframes)
3. **levels_daily** - Daily calculated levels (Pivot Points, Y-High/Low)
4. **setups** - Trading setups (Morning/US Open Planner)
5. **alerts** - Real-time trading alerts

### Features:

- UUID extension enabled
- Indexes for performance (13+ indexes)
- Auto-update triggers for timestamps
- Foreign key relationships
- Data validation constraints
- Seed data (5 default symbols)

### Seed Data:

- DAX (DAX 40)
- NDX (NASDAQ 100)
- DJI (Dow Jones 30)
- EUR/USD (Euro / US Dollar)
- XAG/USD (Silver Spot)

## Verification Queries

### Check All Tables:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### Check Migration 003 Tables:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('market_symbols', 'ohlc', 'levels_daily', 'setups', 'alerts')
ORDER BY table_name;
```

Expected: 5 tables

### Check Seed Data:

```sql
SELECT symbol, alias, vendor, active
FROM market_symbols
ORDER BY symbol;
```

Expected: 5 symbols

### Check Indexes:

```sql
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('market_symbols', 'ohlc', 'levels_daily', 'setups', 'alerts')
ORDER BY tablename, indexname;
```

### Check Triggers:

```sql
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE event_object_schema = 'public'
ORDER BY event_object_table, trigger_name;
```

## Documentation

- **Quick Start:** `../QUICK_START_MIGRATION_003.txt`
- **Detailed Guide:** `../../../APPLY_MIGRATION_003.md`
- **Full Summary:** `../../../MIGRATION_003_SUMMARY.md`
- **Helper Script:** `../quick_apply_migration_003.sh`

## Migration Best Practices

1. **Always backup** your database before applying migrations
2. **Test in development** before applying to production
3. **Review SQL** before executing
4. **Verify results** with verification queries
5. **Check logs** for any errors or warnings
6. **Update RLS policies** if needed after schema changes
7. **Test API access** after migration

## Rollback (if needed)

If you need to rollback Migration 003:

```sql
-- Drop tables (CAREFUL - this deletes data!)
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS setups CASCADE;
DROP TABLE IF EXISTS levels_daily CASCADE;
DROP TABLE IF EXISTS ohlc CASCADE;
DROP TABLE IF EXISTS market_symbols CASCADE;

-- Drop triggers
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
```

## Troubleshooting

### Error: "relation already exists"
Tables already exist. Either skip or drop existing tables first.

### Error: "permission denied"
Make sure you're using database password or have proper admin access.

### Error: "uuid-ossp extension not available"
Run: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`

## Project Info

- **Project:** TradeMatrix.ai
- **Supabase Reference:** htnlhazqzpwfyhnngfsn
- **Dashboard:** https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn
- **SQL Editor:** https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/sql/new
- **Database Settings:** https://supabase.com/dashboard/project/htnlhazqzpwfyhnngfsn/settings/database

## Support

For issues or questions:
1. Check project documentation in `/docs`
2. Review Supabase documentation: https://supabase.com/docs
3. Check migration logs in Supabase dashboard

---

**Last Updated:** 2025-10-29
