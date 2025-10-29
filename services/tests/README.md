# TradeMatrix.ai - End-to-End Test Suite

## Overview

Comprehensive end-to-end integration tests for the complete trading flow, from data ingestion to setup generation and alert triggering.

## Test Coverage

### 1. Complete Morning Trading Flow ✅
- **Purpose**: Test Asia Sweep → EU Open Reversal pattern detection
- **Steps**:
  1. Ingest market data (simulated via fixtures)
  2. Calculate daily levels and pivots
  3. Run Morning Planner
  4. Validate generated setups
  5. Check alerts generated
- **Expected Outcome**: Asia Sweep or Y-Low Rebound setup created
- **Performance**: < 5 seconds

### 2. Complete US Open Trading Flow ✅
- **Purpose**: Test ORB (Opening Range Breakout) detection
- **Steps**:
  1. Detect ORB range (15:30-15:45 MEZ)
  2. Detect breakout (15:45+)
  3. Generate setup
  4. Generate alert
  5. Validate risk parameters
- **Expected Outcome**: ORB setup with 2:1 R:R ratio
- **Performance**: < 3 seconds

### 3. Real-time Alert Flow ✅
- **Purpose**: Test alert generation and delivery
- **Steps**:
  1. Active setup exists
  2. Price moves (simulated)
  3. Alert triggered
  4. Alert stored in DB
  5. Frontend can fetch alert
- **Expected Outcome**: Range break alert created
- **Performance**: < 1 second per symbol

### 4. Risk Management Flow ✅
- **Purpose**: Test position sizing and risk rules
- **Steps**:
  1. Setup generated with confidence
  2. Validation engine validates
  3. Risk calculator calculates position
  4. Trade meets 1% rule
  5. Break-even rule applied at +0.5R
- **Expected Outcome**: All risk rules validated
- **Performance**: < 1 second

### 5. Multi-Symbol Flow ✅
- **Purpose**: Test concurrent symbol processing
- **Steps**:
  1. DAX + NASDAQ + DOW data ingested
  2. Morning Planner runs for DAX
  3. US Open Planner runs for US symbols
  4. Multiple setups generated
  5. No cross-contamination
- **Expected Outcome**: Each symbol processed independently
- **Performance**: < 10 seconds for all symbols

### 6. Error Recovery Flow ✅
- **Purpose**: Test system resilience
- **Steps**:
  1. One symbol has missing data
  2. System continues with other symbols
  3. Errors logged
  4. Other setups still generated
- **Expected Outcome**: Partial success, graceful degradation
- **Performance**: No impact on working symbols

### 7. Performance Benchmark ✅
- **Purpose**: Validate performance requirements
- **Tests**:
  - Morning flow: < 5 seconds
  - US Open flow: < 3 seconds
  - Alert generation: < 1 second per symbol
- **Expected Outcome**: All benchmarks met

### 8. Database Integrity ✅
- **Purpose**: Test database constraints
- **Tests**:
  - Foreign key constraints
  - Unique constraints
  - Check constraints
  - Auto-timestamps
- **Expected Outcome**: All constraints enforced

---

## Setup

### Prerequisites

1. **Python 3.11+**
2. **Supabase Project** (test database recommended)
3. **Required packages**:
   ```bash
   pip install -r ../api/requirements.txt
   ```

### Environment Configuration

Create `.env` file in `services/tests/`:

```bash
# Test Database (recommended: use separate test project)
TEST_SUPABASE_URL=https://xxxxx.supabase.co
TEST_SUPABASE_KEY=your-service-role-key

# Or use development database (will create test data)
# USE_MOCK_DB=false
```

### Database Setup

#### Option 1: Test Database (Recommended)

1. Create a new Supabase project for testing
2. Run migrations:
   ```sql
   -- In Supabase SQL Editor
   -- Run: services/api/supabase/migrations/001_initial_schema.sql
   -- Run: services/api/supabase/migrations/002_rls_policies.sql
   -- Run: services/api/supabase/migrations/003_market_data_schema.sql
   ```

#### Option 2: Development Database

Tests will use your development database and create test data. Ensure you clean up after tests.

---

## Running Tests

### All Tests

```bash
cd services/tests
pytest test_e2e_trading_flow.py -v
```

### Specific Test

```bash
pytest test_e2e_trading_flow.py::test_complete_morning_flow -v
```

### Exclude Slow Tests

```bash
pytest test_e2e_trading_flow.py -v -m "not slow"
```

### Run Only E2E Tests

```bash
pytest test_e2e_trading_flow.py -v -m "e2e"
```

### With Coverage

```bash
pytest test_e2e_trading_flow.py --cov=. --cov-report=html
```

### Verbose Output

```bash
pytest test_e2e_trading_flow.py -v -s
```

---

## Test Structure

### Fixtures (`conftest.py`)

- **`supabase_client`**: Supabase client for test database
- **`dax_symbol_id`**: DAX symbol UUID
- **`ndx_symbol_id`**: NASDAQ symbol UUID
- **`dji_symbol_id`**: DOW JONES symbol UUID
- **`sample_ohlc_dax`**: Realistic DAX OHLC data (Asia session + EU open)
- **`sample_ohlc_us_markets`**: US market OHLC data (ORB range + breakout)
- **`sample_daily_levels`**: Daily levels (pivots, y-high, y-low) for all symbols
- **`cleanup_test_data`**: Auto-cleanup of created setups and alerts
- **`performance_timer`**: Context manager for timing test execution
- **`assert_setup_valid`**: Helper to validate setup structure
- **`assert_alert_valid`**: Helper to validate alert structure

### Sample Data Generator (`sample_data_generator.py`)

Generates realistic market data for testing:

```python
from sample_data_generator import generate_sample_data

# Generate 14 days of DAX data with test scenarios
data = generate_sample_data('DAX', days=14, include_scenarios=True)

# data['ohlc'] - OHLC candles
# data['levels'] - Daily levels
# data['scenarios']['asia_sweep'] - Asia sweep scenario
```

Features:
- Realistic price action with configurable volatility
- Trend simulation (up/down/neutral)
- Specific test scenarios (Asia sweep, ORB breakout)
- Pivot point calculations

---

## Performance Benchmarks

| Test | Expected Duration | Actual |
|------|-------------------|--------|
| Complete Morning Flow | < 5 seconds | ⏱️ |
| Complete US Open Flow | < 3 seconds | ⏱️ |
| Alert Generation (per symbol) | < 1 second | ⏱️ |
| Risk Management Flow | < 1 second | ⏱️ |
| Multi-Symbol Flow | < 10 seconds | ⏱️ |

Run performance benchmark test:

```bash
pytest test_e2e_trading_flow.py::test_performance_benchmark -v -s
```

---

## Assertions

### Setup Validation

```python
assert_setup_valid(setup)
```

Validates:
- ✅ Has ID, module, strategy, side
- ✅ entry_price > 0
- ✅ stop_loss > 0
- ✅ take_profit > 0
- ✅ 0.0 ≤ confidence ≤ 1.0
- ✅ Long: entry > SL, TP > entry
- ✅ Short: entry < SL, TP < entry

### Alert Validation

```python
assert_alert_valid(alert)
```

Validates:
- ✅ Has ID, kind, context
- ✅ kind in allowed values
- ✅ context is dict
- ✅ sent is boolean

---

## Example Test Output

```
============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-7.4.3, pluggy-1.3.0
rootdir: /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/tests
plugins: asyncio-0.21.1
collected 8 items

test_e2e_trading_flow.py::test_complete_morning_flow
============================================================
TEST: Complete Morning Trading Flow
============================================================

⏱️  Morning Planner Execution: 1234ms

✅ Morning Flow Test PASSED
   - Setup ID: 550e8400-e29b-41d5-a716-446655440000
   - Strategy: asia_sweep
   - Confidence: 0.78
   - Entry: 18510.0
   - Duration: 1234ms

PASSED                                                                  [ 12%]

test_e2e_trading_flow.py::test_complete_usopen_flow
============================================================
TEST: Complete US Open Trading Flow
============================================================

⏱️  US Open Planner Execution: 987ms

✅ US Open Flow Test PASSED
   - Setup ID: 660e8400-e29b-41d5-a716-446655440001
   - Symbol: NDX
   - ORB Range: 16480.0 - 16530.0
   - Breakout: 16545.0 (32.5% strength)
   - R:R Ratio: 2.15:1

PASSED                                                                  [ 25%]

... (more tests)

============================== 8 passed in 12.34s ==============================
```

---

## Debugging

### View Test Database

```python
# In Python shell
from supabase import create_client

client = create_client(
    'https://xxxxx.supabase.co',
    'your-service-role-key'
)

# View setups
setups = client.table('setups').select('*').limit(10).execute()
print(setups.data)

# View alerts
alerts = client.table('alerts').select('*').limit(10).execute()
print(alerts.data)
```

### Common Issues

#### 1. Database Connection Failed

**Error**: `Unable to connect to Supabase`

**Solution**:
- Check `TEST_SUPABASE_URL` and `TEST_SUPABASE_KEY` in `.env`
- Verify Supabase project is active
- Check network connectivity

#### 2. Missing Symbols

**Error**: `Symbol DAX not found in database`

**Solution**:
- Run migration 003 to seed default symbols
- Or manually insert symbols:
  ```sql
  INSERT INTO market_symbols (vendor, symbol, alias, active)
  VALUES ('twelve_data', 'DAX', 'DAX 40', true);
  ```

#### 3. No OHLC Data

**Error**: `No Asia session candles for DAX`

**Solution**:
- Test fixtures auto-generate sample data
- Check `sample_ohlc_dax` fixture is working
- Manually check:
  ```sql
  SELECT COUNT(*) FROM ohlc WHERE symbol_id = '...';
  ```

#### 4. Performance Test Failing

**Error**: `Morning flow should complete in < 5s, took 7234ms`

**Solution**:
- Check database performance (may be slow connection)
- Reduce test data volume
- Run on faster machine
- Check for other processes consuming resources

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd services/tests
          pip install -r ../api/requirements.txt

      - name: Run E2E Tests
        env:
          TEST_SUPABASE_URL: ${{ secrets.TEST_SUPABASE_URL }}
          TEST_SUPABASE_KEY: ${{ secrets.TEST_SUPABASE_KEY }}
        run: |
          cd services/tests
          pytest test_e2e_trading_flow.py -v -m "not slow"
```

---

## Contributing

### Adding New Tests

1. Add test function to `test_e2e_trading_flow.py`:
   ```python
   @pytest.mark.e2e
   def test_my_new_flow(supabase_client, ...):
       """Test description"""
       # Arrange
       # Act
       # Assert
   ```

2. Add fixtures to `conftest.py` if needed

3. Update README with new test details

### Test Naming Convention

- `test_complete_*_flow`: Full workflow tests
- `test_*_validation`: Data validation tests
- `test_*_performance`: Performance benchmark tests
- `test_error_*`: Error handling tests

---

## Resources

- [PyTest Documentation](https://docs.pytest.org/)
- [PyTest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [TradeMatrix Architecture](../../docs/ARCHITECTURE.md)

---

## Support

Questions or issues? Check:

1. **Project Docs**: `/docs/PROJECT_OVERVIEW.md`
2. **Architecture**: `/docs/ARCHITECTURE.md`
3. **Development Workflow**: `/docs/DEVELOPMENT_WORKFLOW.md`

---

**Last Updated**: 2025-10-29
**Version**: 1.0.0
**Status**: ✅ Complete
