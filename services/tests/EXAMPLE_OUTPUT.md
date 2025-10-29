# E2E Test Suite - Example Output

## Full Test Run

```bash
$ ./run_tests.sh all
================================================
TradeMatrix.ai - E2E Test Runner
================================================
✓ Python version: 3.11.0
✓ pytest installed

Running all E2E tests...

============================= test session starts ==============================
platform linux -- Python 3.11.0, pytest-7.4.3, pluggy-1.3.0
rootdir: /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/tests
configfile: pytest.ini
plugins: asyncio-0.21.1
collected 8 items

test_e2e_trading_flow.py::test_complete_morning_flow
============================================================
TEST: Complete Morning Trading Flow
============================================================
2025-10-29 08:25:15 [    INFO] MorningPlanner initialized
2025-10-29 08:25:15 [    INFO] Found 1 active symbols to analyze
2025-10-29 08:25:15 [    INFO] Processing symbol: DAX
2025-10-29 08:25:16 [    INFO] Analyzing Asia Sweep for DAX on 2025-10-29
2025-10-29 08:25:16 [    INFO] Asia Sweep setup detected for DAX: ...
2025-10-29 08:25:16 [    INFO] Generating setup for DAX: asia_sweep
2025-10-29 08:25:17 [    INFO] Setup created with ID: 550e8400-e29b-41d5-a716-446655440000
2025-10-29 08:25:17 [    INFO] Morning Planner execution completed

⏱️  Morning Planner Execution: 1847ms

✅ Morning Flow Test PASSED
   - Setup ID: 550e8400-e29b-41d5-a716-446655440000
   - Strategy: asia_sweep
   - Confidence: 0.78
   - Entry: 18510.0
   - Duration: 1847ms

PASSED                                                                  [ 12%]

test_e2e_trading_flow.py::test_complete_usopen_flow
============================================================
TEST: Complete US Open Trading Flow
============================================================
2025-10-29 15:25:00 [    INFO] US Open Planner initialized
2025-10-29 15:25:01 [    INFO] Detecting ORB range for NDX
2025-10-29 15:25:01 [    INFO] ORB range detected: 16480.0 - 16530.0
2025-10-29 15:25:02 [    INFO] Analyzing breakout for NDX
2025-10-29 15:25:02 [    INFO] Bullish breakout detected at 16545.0
2025-10-29 15:25:03 [    INFO] Generating setup for NDX
2025-10-29 15:25:03 [    INFO] Setup created with ID: 660e8400-e29b-41d5-a716-446655440001

⏱️  US Open Planner Execution: 2134ms

✅ US Open Flow Test PASSED
   - Setup ID: 660e8400-e29b-41d5-a716-446655440001
   - Symbol: NDX
   - ORB Range: 16480.0 - 16530.0
   - Breakout: 16545.0 (32.5% strength)
   - R:R Ratio: 2.15:1

PASSED                                                                  [ 25%]

test_e2e_trading_flow.py::test_realtime_alert_flow
============================================================
TEST: Real-time Alert Flow
============================================================
   Created active setup: 770e8400-e29b-41d5-a716-446655440002
2025-10-29 15:30:00 [    INFO] AlertEngine initialized
2025-10-29 15:30:00 [    INFO] Checking range break for DAX
2025-10-29 15:30:01 [    INFO] Range break detected for DAX: bullish at 18510.0
2025-10-29 15:30:01 [    INFO] Creating alert: range_break for symbol DAX
2025-10-29 15:30:01 [    INFO] Alert created with ID: 880e8400-e29b-41d5-a716-446655440003

⏱️  Alert Engine Execution: 876ms

✅ Alert Generated:
   - Alert ID: 880e8400-e29b-41d5-a716-446655440003
   - Kind: range_break
   - Direction: bullish
   - Price: 18510.0

PASSED                                                                  [ 37%]

test_e2e_trading_flow.py::test_risk_management_flow
============================================================
TEST: Risk Management Flow
============================================================

✅ Risk Management Test PASSED
   - Account Size: €10000
   - Risk Per Trade: 1.0% (€100.0)
   - Position Size: 2.0 contracts
   - Entry: 18500.0
   - Stop Loss: 18450.0
   - Take Profit: 18600.0
   - Risk: 50.0 points
   - Reward: 100.0 points
   - R:R Ratio: 2.00:1
   - Break-even at: 18525.0

PASSED                                                                  [ 50%]

test_e2e_trading_flow.py::test_multi_symbol_flow
============================================================
TEST: Multi-Symbol Flow
============================================================
2025-10-29 08:25:30 [    INFO] Morning Planner initialized
2025-10-29 08:25:30 [    INFO] Processing symbol: DAX

⏱️  Morning Planner (DAX): 1923ms

2025-10-29 15:25:30 [    INFO] US Open Planner initialized
2025-10-29 15:25:31 [    INFO] Detecting ORB for NDX
2025-10-29 15:25:32 [    INFO] Detecting ORB for DJI

⏱️  US Open Planner (NDX, DJI): 3456ms

✅ Multi-Symbol Flow Test PASSED
   - Morning Setups (DAX): 1
   - US Open Setups (NDX): 1
   - US Open Setups (DJI): 1
   - Total Setups: 3

PASSED                                                                  [ 62%]

test_e2e_trading_flow.py::test_error_recovery_flow
============================================================
TEST: Error Recovery Flow
============================================================
   Deleted NDX OHLC data to simulate missing data scenario
   Created minimal OHLC data for DAX
2025-10-29 08:25:45 [    INFO] Morning Planner execution started
2025-10-29 08:25:45 [    INFO] Processing symbol: DAX
2025-10-29 08:25:46 [    INFO] Processing symbol: NDX
2025-10-29 08:25:46 [  WARNING] No Asia session candles for NDX
   Symbols Analyzed: 2
   Setups Generated: 0
   ✓ NDX correctly skipped due to missing data

✅ Error Recovery Test PASSED
   - System continued despite missing data
   - No crashes or exceptions raised
   - Valid symbols processed normally

PASSED                                                                  [ 75%]

test_e2e_trading_flow.py::test_performance_benchmark
============================================================
TEST: Performance Benchmark
============================================================
2025-10-29 08:26:00 [    INFO] Running performance benchmarks

⏱️  Morning Planner (Full Flow): 2134ms
⏱️  US Open Planner (Full Flow): 2678ms
⏱️  Alert Engine (Per Symbol): 734ms

✅ Performance Benchmark PASSED
   - Morning Flow: 2134ms (< 5000ms) ✓
   - US Open Flow: 2678ms (< 3000ms) ✓
   - Alert Engine: 734ms (< 1000ms) ✓

PASSED                                                                  [ 87%]

test_e2e_trading_flow.py::test_database_integrity
============================================================
TEST: Database Integrity
============================================================
   ✓ Foreign key constraint working: APIError
   ✓ Check constraint working: APIError

✅ Database Integrity Test PASSED
   - Foreign key constraints: ✓
   - Check constraints: ✓
   - Auto-timestamps: ✓

PASSED                                                                  [100%]

============================== 8 passed in 18.42s ==============================

================================================
✅ All tests passed!
================================================
```

---

## Fast Tests Only

```bash
$ ./run_tests.sh fast

Running fast tests (excluding slow tests)...

============================= test session starts ==============================
collected 7 items / 1 deselected / 7 selected

test_e2e_trading_flow.py::test_complete_morning_flow PASSED           [ 14%]
test_e2e_trading_flow.py::test_complete_usopen_flow PASSED            [ 28%]
test_e2e_trading_flow.py::test_realtime_alert_flow PASSED             [ 42%]
test_e2e_trading_flow.py::test_risk_management_flow PASSED            [ 57%]
test_e2e_trading_flow.py::test_multi_symbol_flow PASSED               [ 71%]
test_e2e_trading_flow.py::test_error_recovery_flow PASSED             [ 85%]
test_e2e_trading_flow.py::test_database_integrity PASSED              [100%]

============================== 7 passed, 1 deselected in 12.34s =================

================================================
✅ All tests passed!
================================================
```

---

## Single Test Run

```bash
$ ./run_tests.sh morning

Running Morning Flow test...

============================= test session starts ==============================
collected 1 item

test_e2e_trading_flow.py::test_complete_morning_flow
============================================================
TEST: Complete Morning Trading Flow
============================================================

⏱️  Morning Planner Execution: 1847ms

✅ Morning Flow Test PASSED
   - Setup ID: 550e8400-e29b-41d5-a716-446655440000
   - Strategy: asia_sweep
   - Confidence: 0.78
   - Entry: 18510.0
   - Duration: 1847ms

PASSED                                                                  [100%]

============================== 1 passed in 2.34s ================================

================================================
✅ All tests passed!
================================================
```

---

## Coverage Report

```bash
$ ./run_tests.sh coverage

Running tests with coverage report...

============================= test session starts ==============================
...
============================== 8 passed in 19.23s ==============================

----------- coverage: platform linux, python 3.11.0 -----------
Name                                Stmts   Miss  Cover
-------------------------------------------------------
conftest.py                           145      8    94%
sample_data_generator.py              178     22    88%
test_e2e_trading_flow.py              452     15    97%
-------------------------------------------------------
TOTAL                                 775     45    94%

Coverage HTML written to dir htmlcov

✓ Coverage report generated in htmlcov/index.html

================================================
✅ All tests passed!
================================================
```

---

## Test Failure Example

```bash
$ ./run_tests.sh morning

Running Morning Flow test...

============================= test session starts ==============================
collected 1 item

test_e2e_trading_flow.py::test_complete_morning_flow
============================================================
TEST: Complete Morning Trading Flow
============================================================

⏱️  Morning Planner Execution: 6234ms

FAILED                                                                  [100%]

=================================== FAILURES ===================================
___________________________ test_complete_morning_flow _________________________

    def test_complete_morning_flow(...):
>       assert result['execution_duration_ms'] < 5000, \
            f"Morning flow should complete in < 5s, took {result['execution_duration_ms']}ms"
E       AssertionError: Morning flow should complete in < 5s, took 6234ms
E       assert 6234 < 5000

test_e2e_trading_flow.py:156: AssertionError
=========================== short test summary info ============================
FAILED test_e2e_trading_flow.py::test_complete_morning_flow - AssertionError...
============================== 1 failed in 6.78s ================================

================================================
❌ Some tests failed
================================================
```

---

## Help Output

```bash
$ ./run_tests.sh help

Available commands:
  all         - Run all tests (default)
  fast        - Run fast tests only (exclude slow)
  morning     - Run Morning Flow test
  usopen      - Run US Open Flow test
  alert       - Run Alert Flow test
  risk        - Run Risk Management test
  multi       - Run Multi-Symbol test
  error       - Run Error Recovery test
  benchmark   - Run Performance Benchmarks
  coverage    - Run with coverage report
  integrity   - Run Database Integrity test
  smoke       - Run quick smoke tests
  help        - Show this help message

Examples:
  ./run_tests.sh
  ./run_tests.sh fast
  ./run_tests.sh morning
  ./run_tests.sh coverage
```

---

## Notes

- **Duration**: Full test suite typically runs in 15-20 seconds
- **Performance**: Tests include timing assertions to ensure system meets requirements
- **Cleanup**: Test data is automatically cleaned up after each test
- **Database**: Tests use Supabase test database (configure in `.env`)
- **Parallel**: Tests can be run in parallel with `pytest-xdist` plugin

---

**Generated on**: 2025-10-29
