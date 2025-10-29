# E2E Tests - Quick Start Guide

## 30-Second Setup

```bash
# 1. Navigate to tests directory
cd services/tests

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your test database credentials
nano .env  # or use any editor

# 4. Run tests
./run_tests.sh
```

## Common Commands

```bash
# Run all tests
./run_tests.sh

# Run fast tests only (skip slow benchmarks)
./run_tests.sh fast

# Run specific test
./run_tests.sh morning      # Morning trading flow
./run_tests.sh usopen       # US Open trading flow
./run_tests.sh alert        # Alert generation
./run_tests.sh risk         # Risk management

# Run with coverage report
./run_tests.sh coverage

# See all options
./run_tests.sh help
```

## What Gets Tested

✅ **Morning Flow** - Asia Sweep → EU Open Reversal
✅ **US Open Flow** - ORB Detection → Breakout → Setup
✅ **Alert Flow** - Price Movement → Alert Triggered
✅ **Risk Management** - 1% Rule, Position Sizing, R:R
✅ **Multi-Symbol** - DAX + NASDAQ + DOW processing
✅ **Error Recovery** - System resilience with missing data
✅ **Performance** - All flows meet speed benchmarks
✅ **Database** - Constraints and integrity checks

## Expected Results

```
============================= test session starts ==============================
collected 8 items

test_e2e_trading_flow.py::test_complete_morning_flow PASSED           [ 12%]
test_e2e_trading_flow.py::test_complete_usopen_flow PASSED            [ 25%]
test_e2e_trading_flow.py::test_realtime_alert_flow PASSED             [ 37%]
test_e2e_trading_flow.py::test_risk_management_flow PASSED            [ 50%]
test_e2e_trading_flow.py::test_multi_symbol_flow PASSED               [ 62%]
test_e2e_trading_flow.py::test_error_recovery_flow PASSED             [ 75%]
test_e2e_trading_flow.py::test_performance_benchmark PASSED           [ 87%]
test_e2e_trading_flow.py::test_database_integrity PASSED              [100%]

============================== 8 passed in 18.42s ==============================

✅ All tests passed!
```

## Troubleshooting

**Connection Error?**
→ Check `TEST_SUPABASE_URL` and `TEST_SUPABASE_KEY` in `.env`

**Missing Symbols?**
→ Run migration 003 to seed default symbols:
```sql
-- In Supabase SQL Editor
-- Copy from: services/api/supabase/migrations/003_market_data_schema.sql
```

**Slow Tests?**
→ Use fast mode: `./run_tests.sh fast`

**Need Help?**
→ Read [README.md](./README.md) for full documentation

## Performance

- Full suite: **~18 seconds**
- Fast tests: **~12 seconds**
- Single test: **~2-3 seconds**

## Files Overview

| File | Purpose |
|------|---------|
| `test_e2e_trading_flow.py` | Main test cases (8 tests) |
| `conftest.py` | Fixtures & utilities |
| `sample_data_generator.py` | Realistic data generation |
| `run_tests.sh` | Test runner script |
| `pytest.ini` | PyTest configuration |
| `README.md` | Full documentation |
| `EXAMPLE_OUTPUT.md` | Expected outputs |

## Next Steps

1. ✅ Run tests successfully
2. Read [README.md](./README.md) for details
3. Check [EXAMPLE_OUTPUT.md](./EXAMPLE_OUTPUT.md) for examples
4. Integrate with CI/CD pipeline

---

**Questions?** Check the full [README.md](./README.md)
