# SignalBot Test Quick Reference

## Test Coverage

| Method | Test Class | Tests | Status |
|--------|------------|-------|--------|
| `analyze_market_structure()` | TestSignalBotMarketStructure | 4 | ✅ |
| `generate_entry_signals()` | TestSignalBotEntrySignals | 4 | ✅ |
| `generate_exit_signals()` | TestSignalBotExitSignals | 7 | ✅ |
| `create_signal()` | TestSignalBotCreateSignal | 3 | ✅ |
| `run()` | TestSignalBotRun | 4 | ✅ |
| **Integration** | TestSignalBotIntegration | 1 | ✅ |
| **TOTAL** | **6 classes** | **23 tests** | **✅** |

---

## Quick Commands

### Run All Tests
```bash
cd services/agents
pytest tests/test_signal_bot.py -v
```

### Run Specific Method Tests
```bash
# Market Structure
pytest tests/test_signal_bot.py::TestSignalBotMarketStructure -v

# Entry Signals
pytest tests/test_signal_bot.py::TestSignalBotEntrySignals -v

# Exit Signals
pytest tests/test_signal_bot.py::TestSignalBotExitSignals -v

# Signal Creation
pytest tests/test_signal_bot.py::TestSignalBotCreateSignal -v

# Full Run
pytest tests/test_signal_bot.py::TestSignalBotRun -v

# Integration
pytest tests/test_signal_bot.py::TestSignalBotIntegration -v
```

### Run Single Test
```bash
pytest tests/test_signal_bot.py::TestSignalBotMarketStructure::test_analyze_market_structure_success -v
```

### Coverage Report
```bash
pytest tests/test_signal_bot.py --cov=src.signal_bot --cov-report=term-missing
```

---

## Test Categories

### Unit Tests (22)
```bash
pytest tests/test_signal_bot.py -m unit -v
```

### Integration Tests (1)
```bash
pytest tests/test_signal_bot.py -m integration -v
```

### Agent Tests (23)
```bash
pytest tests/test_signal_bot.py -m agent -v
```

---

## Mocked Dependencies

### Always Mocked
- ✅ Supabase client (via `create_mock_supabase_client()`)
- ✅ TechnicalIndicators (EMA, RSI, MACD, BB, ATR)
- ✅ ValidationEngine (signal validation)
- ✅ RiskCalculator (break-even logic)

### Database Tables
- ✅ `market_symbols` - Active symbols
- ✅ `ohlc` - Price candles (5m, 1m)
- ✅ `levels_daily` - Pivot levels
- ✅ `setups` - Trading setups (pending/active)
- ✅ `signals` - Generated signals

---

## Test Fixtures Used

From `conftest.py`:
- `mock_supabase` - Mock Supabase client
- `test_symbol_id` - Fixed UUID for testing
- `test_trade_date` - Fixed date (2025-10-29)

From `fixtures.py`:
- `generate_ohlc_data()` - Generate realistic OHLC candles
- `create_test_setup()` - Create test setup records

From `utils.py`:
- `create_mock_supabase_client()` - Mock Supabase with table data
- `assert_confidence_valid()` - Validate confidence scores
- `assert_price_valid()` - Validate price values
- `extract_setup_metrics()` - Extract setup metrics

---

## Key Test Scenarios

### Market Structure Analysis
1. ✅ Success with 250 candles
2. ✅ Insufficient data (< 200 candles)
3. ✅ No data
4. ✅ Missing pivot levels (optional)

### Entry Signals
1. ✅ Valid signal with ValidationEngine pass
2. ✅ No pending setups
3. ✅ Validation failure (confidence < 0.8)
4. ✅ Market data unavailable

### Exit Signals
1. ✅ Take Profit hit (long & short)
2. ✅ Stop Loss hit (long & short)
3. ✅ Break-even condition (+0.5R)
4. ✅ No active trades
5. ✅ Missing current price

### Signal Creation
1. ✅ Entry signal creation
2. ✅ Exit signal creation
3. ✅ Database error handling

### Full Execution
1. ✅ Complete workflow with entry + exit signals
2. ✅ No active symbols
3. ✅ Symbol filtering
4. ✅ Exception handling

---

## Expected Output

### Successful Test Run
```
tests/test_signal_bot.py::TestSignalBotMarketStructure::test_analyze_market_structure_success PASSED
tests/test_signal_bot.py::TestSignalBotMarketStructure::test_analyze_market_structure_insufficient_data PASSED
tests/test_signal_bot.py::TestSignalBotMarketStructure::test_analyze_market_structure_no_data PASSED
tests/test_signal_bot.py::TestSignalBotMarketStructure::test_analyze_market_structure_no_levels PASSED
tests/test_signal_bot.py::TestSignalBotEntrySignals::test_generate_entry_signals_success PASSED
tests/test_signal_bot.py::TestSignalBotEntrySignals::test_generate_entry_signals_no_active_setups PASSED
tests/test_signal_bot.py::TestSignalBotEntrySignals::test_generate_entry_signals_validation_fails PASSED
tests/test_signal_bot.py::TestSignalBotEntrySignals::test_generate_entry_signals_no_market_data PASSED
tests/test_signal_bot.py::TestSignalBotExitSignals::test_generate_exit_signals_take_profit_long PASSED
tests/test_signal_bot.py::TestSignalBotExitSignals::test_generate_exit_signals_take_profit_short PASSED
tests/test_signal_bot.py::TestSignalBotExitSignals::test_generate_exit_signals_stop_loss_long PASSED
tests/test_signal_bot.py::TestSignalBotExitSignals::test_generate_exit_signals_stop_loss_short PASSED
tests/test_signal_bot.py::TestSignalBotExitSignals::test_generate_exit_signals_break_even PASSED
tests/test_signal_bot.py::TestSignalBotExitSignals::test_generate_exit_signals_no_active_trades PASSED
tests/test_signal_bot.py::TestSignalBotExitSignals::test_generate_exit_signals_no_current_price PASSED
tests/test_signal_bot.py::TestSignalBotCreateSignal::test_create_signal_entry_success PASSED
tests/test_signal_bot.py::TestSignalBotCreateSignal::test_create_signal_exit_success PASSED
tests/test_signal_bot.py::TestSignalBotCreateSignal::test_create_signal_database_error PASSED
tests/test_signal_bot.py::TestSignalBotRun::test_run_success_with_entry_and_exit_signals PASSED
tests/test_signal_bot.py::TestSignalBotRun::test_run_no_active_symbols PASSED
tests/test_signal_bot.py::TestSignalBotRun::test_run_with_specific_symbols PASSED
tests/test_signal_bot.py::TestSignalBotRun::test_run_handles_exceptions PASSED
tests/test_signal_bot.py::TestSignalBotIntegration::test_complete_signal_generation_workflow PASSED

======================== 23 passed in X.XXs ========================
```

---

## Troubleshooting

### Import Error
```bash
# Ensure you're in the correct directory
cd services/agents

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Missing Dependencies
```bash
pip install pytest pytest-cov numpy pytz
```

### Numpy Errors
```python
# If you see NaN comparison warnings, they're expected
# Tests handle NaN values with np.isnan() checks
```

---

## File Locations

```
services/agents/
├── src/
│   └── signal_bot.py              # Source code
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest config & fixtures
│   ├── fixtures.py                # Test data generators
│   ├── utils.py                   # Test utilities
│   ├── test_signal_bot.py         # SignalBot tests ← YOU ARE HERE
│   └── test_morning_planner.py    # Reference pattern
├── pytest.ini                     # Pytest configuration
├── TEST_SIGNAL_BOT_SUMMARY.md     # Detailed summary
└── SIGNAL_BOT_TEST_QUICKREF.md    # This file
```

---

## Pattern Followed

Based on `test_alert_engine.py` and `test_morning_planner.py`:

1. ✅ Use pytest fixtures from conftest.py
2. ✅ Mock Supabase client with create_mock_supabase_client()
3. ✅ Mock all external dependencies (TechnicalIndicators, ValidationEngine, RiskCalculator)
4. ✅ Test all public methods
5. ✅ Include edge cases (no data, errors, validation failures)
6. ✅ Integration test for full workflow
7. ✅ Use test markers (@pytest.mark.unit, @pytest.mark.agent)
8. ✅ Clear docstrings and assertions

---

**Status:** ✅ All 23 tests implemented and ready

**Next:** Run `pytest tests/test_signal_bot.py -v` to verify
