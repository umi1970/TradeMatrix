# RiskManager Agent - Quick Reference

**Location:** `services/agents/src/risk_manager.py`
**Execution:** Every 60 seconds (via Celery scheduler)
**Celery Task:** `risk_manager_task`

---

## Purpose

The **RiskManager** agent monitors portfolio risk exposure, validates position sizing rules, enforces daily loss limits, and automatically adjusts stop losses to break-even when trades reach profit targets.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RiskManager Agent                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input Data Sources:                                         │
│  • trades table (active trades, positions, P&L)             │
│  • market_symbols table (current prices via ohlc)           │
│  • profiles table (account balance, risk settings)          │
│                                                              │
│  Methods:                                                    │
│  1. check_position_sizes()    → Validate 1% risk rule       │
│  2. check_portfolio_risk()    → Aggregate risk exposure     │
│  3. check_daily_loss_limit()  → Enforce 3-loss rule         │
│  4. adjust_stop_loss()        → Move SL to break-even       │
│  5. validate_new_trade()      → Pre-trade risk check        │
│  6. run()                     → Main execution method        │
│                                                              │
│  Output:                                                     │
│  • alerts table (risk violation alerts)                     │
│  • trades table (updated stop losses)                       │
│  • Execution summary (risks, adjustments, alerts)           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Position Size Validation
- **Rule:** Max 1% risk per trade
- **Checks:**
  - Risk amount = Position Size × |Entry - Stop Loss|
  - Risk percentage = (Risk Amount / Account Balance) × 100
  - Must be ≤ 1%
- **Output:** Violations list with warnings

### 2. Portfolio Risk Aggregation
- **Rule:** Max 5% total portfolio risk
- **Metrics:**
  - Total risk across all active trades
  - Total position value (leverage exposure)
  - Symbol concentration (max 2-3 trades per symbol)
  - Total leverage (position value / account balance)
- **Warnings:**
  - Total risk > 5%
  - Leverage > 10x
  - Too many trades per symbol (> 3)
  - Too many concurrent trades (> 10)

### 3. Daily Loss Limit
- **Rule:** Max 3 losing trades per day
- **Process:**
  - Count closed trades for current day
  - Track wins vs losses
  - Calculate daily P&L
  - Stop trading if 3 losses reached
- **Warnings:**
  - 2 losses today (1 more triggers limit)
  - Negative daily P&L

### 4. Break-Even Stop Loss
- **Rule:** Move SL to entry at +0.5R profit
- **Process:**
  - Get current market price
  - Calculate current R-multiple: (Current Price - Entry) / (Entry - SL)
  - If current R ≥ 0.5R, update stop loss to entry price
  - Log adjustment in trade record
- **Result:** Risk-free trade (no loss possible)

### 5. Pre-Trade Validation
- **Checks before executing new trade:**
  1. Position size meets 1% rule
  2. Portfolio risk won't exceed 5% after trade
  3. Daily loss limit not reached (< 3 losses)
  4. Leverage acceptable
  5. Symbol concentration acceptable (< 3 trades)
- **Output:** Validation result with errors/warnings

---

## Risk Calculator Integration

The RiskManager uses `services/api/src/core/risk_calculator.py` for:

```python
from core.risk_calculator import RiskCalculator

# Initialize with account balance
risk_calc = RiskCalculator(account_balance=10000, risk_per_trade=0.01)

# Validate trade risk
validation = risk_calc.validate_trade_risk(
    entry=18200.0,
    stop_loss=18150.0,
    position_size=2.0,
    account_balance=10000.0
)
# Returns: {'is_valid': bool, 'risk_amount': float, 'warnings': List[str]}

# Check break-even condition
be_check = risk_calc.should_move_to_break_even(
    entry=18200.0,
    current_price=18225.0,
    stop_loss=18150.0,
    threshold_r=0.5
)
# Returns: {'should_move': bool, 'current_r': float, 'new_stop_loss': float}
```

---

## Method Reference

### 1. `check_position_sizes(symbol_id, symbol_name)`
**Purpose:** Validate position sizing for active trades

**Returns:**
```python
{
    'symbol_id': str,
    'symbol_name': str,
    'trades_checked': int,
    'violations': [
        {
            'trade_id': str,
            'symbol': str,
            'risk_amount': float,
            'risk_percentage': float,
            'warnings': List[str]
        }
    ],
    'total_risk': float,
    'account_balance': float
}
```

---

### 2. `check_portfolio_risk()`
**Purpose:** Calculate aggregate portfolio risk

**Returns:**
```python
{
    'total_risk_amount': float,           # Total risk in EUR
    'total_risk_percentage': float,       # % of account balance
    'total_position_value': float,        # Sum of all positions
    'total_leverage': float,              # Position value / balance
    'active_trades_count': int,
    'symbols_exposed': int,
    'account_balance': float,
    'warnings': [str]                     # Risk warnings
}
```

**Warnings Generated:**
- `"Total portfolio risk (X%) exceeds 5% limit"`
- `"Symbol has X active trades (max: 3)"`
- `"Total leverage (Xx) exceeds safe limit (10x)"`
- `"Too many concurrent trades (X) - reduce exposure"`

---

### 3. `check_daily_loss_limit()`
**Purpose:** Enforce 3-loss daily limit

**Returns:**
```python
{
    'trade_date': str,                   # YYYY-MM-DD
    'losses_today': int,
    'wins_today': int,
    'daily_pnl': float,                  # Total P&L for today
    'limit_reached': bool,               # True if 3 losses
    'total_trades_today': int,
    'warnings': [str]
}
```

**Warnings Generated:**
- `"STOP TRADING: 3-loss limit reached today (X losses)"`
- `"WARNING: 2 losses today - one more triggers limit"`
- `"Daily P&L is negative: X EUR"`

---

### 4. `adjust_stop_loss(trade_id)`
**Purpose:** Move stop loss to break-even when +0.5R reached

**Returns:**
```python
{
    'trade_id': str,
    'adjusted': bool,                    # True if SL moved
    'old_stop_loss': float,
    'new_stop_loss': float,              # Entry price if adjusted
    'current_r': float,                  # Current R-multiple
    'current_price': float,
    'reason': str
}
```

**Adjustment Conditions:**
- Trade must be `status='active'`
- Current R ≥ 0.5R (default threshold)
- Direction-aware (long vs short)

**Example:**
```
Entry: 18200.00
Stop Loss: 18150.00
Current Price: 18225.00

1R = |18200 - 18150| = 50.00
Current Profit = 18225 - 18200 = 25.00
Current R = 25.00 / 50.00 = 0.50R

✅ Threshold met → Move SL to 18200.00 (break-even)
```

---

### 5. `validate_new_trade(trade_data)`
**Purpose:** Pre-trade risk validation

**Input:**
```python
trade_data = {
    'user_id': str,
    'symbol_id': str,
    'side': 'long' | 'short',
    'entry_price': float,
    'stop_loss': float,
    'position_size': float
}
```

**Returns:**
```python
{
    'is_valid': bool,                    # True if trade approved
    'risk_amount': float,
    'risk_percentage': float,
    'portfolio_risk_after': float,       # Risk % after trade
    'warnings': [str],
    'errors': [str]                      # Blocking errors
}
```

**Validation Checks:**
1. ✅ Position size meets 1% rule
2. ✅ Portfolio risk ≤ 5% after trade
3. ✅ Daily loss limit not reached
4. ✅ Symbol concentration ≤ 3 trades
5. ✅ Leverage acceptable

---

### 6. `run()`
**Purpose:** Main execution method (called by Celery)

**Process:**
1. Check portfolio-wide risk metrics
2. Check daily loss limit
3. Validate position sizes for all symbols
4. Adjust stop losses for active trades
5. Generate risk alerts for violations
6. Return execution summary

**Returns:**
```python
{
    'execution_time': str,               # ISO timestamp
    'execution_duration_ms': int,
    'portfolio_risk': Dict,              # From check_portfolio_risk()
    'daily_loss_check': Dict,            # From check_daily_loss_limit()
    'position_violations_count': int,
    'position_violations': [Dict],
    'stop_loss_adjustments_count': int,
    'stop_loss_adjustments': [Dict],
    'risk_alerts_generated': int         # Total alerts created
}
```

---

## Risk Alert Types

Alerts are written to `alerts` table with `kind='risk_warning'`:

### 1. Portfolio Risk Warning
```python
{
    'kind': 'risk_warning',
    'context': {
        'type': 'portfolio_risk',
        'message': 'Total portfolio risk (6.2%) exceeds 5% limit',
        'portfolio_metrics': {...}
    }
}
```

### 2. Daily Loss Limit Alert
```python
{
    'kind': 'risk_warning',
    'context': {
        'type': 'daily_loss_limit',
        'message': 'STOP TRADING: 3-loss daily limit reached',
        'daily_metrics': {...}
    }
}
```

### 3. Position Size Violation
```python
{
    'kind': 'risk_warning',
    'context': {
        'type': 'position_size_violation',
        'trade_id': 'uuid',
        'symbol': 'DAX',
        'warnings': [...]
    }
}
```

---

## Celery Task Configuration

**Task Name:** `risk_manager_task`
**Schedule:** Every 60 seconds
**Timeout:** 600 seconds (10 minutes)
**Retry:** Max 3 retries with 60s countdown

```python
@celery.task(name='risk_manager_task', bind=True)
def risk_manager_task(self):
    try:
        manager = RiskManager(supabase_client=supabase_admin)
        result = manager.run()
        logger.info(f"RiskManager completed: {result['risk_alerts_generated']} alerts")
        return result
    except Exception as e:
        logger.error(f"Error in risk_manager_task: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)
```

**Beat Schedule:**
```python
'risk-manager': {
    'task': 'risk_manager_task',
    'schedule': 60.0,  # Every 60 seconds
    'options': {
        'expires': 55.0,
    }
}
```

---

## Testing

**Test File:** `services/agents/tests/test_risk_manager.py`

**Run Tests:**
```bash
cd services/agents
python tests/test_risk_manager.py
```

**Test Coverage:**
1. ✅ Position size validation (1% rule)
2. ✅ Portfolio risk aggregation (5% limit)
3. ✅ Daily loss limit (3-loss rule)
4. ✅ Break-even adjustment (+0.5R)
5. ✅ Pre-trade validation (all checks)
6. ✅ Full execution summary

**Example Test Output:**
```
TEST 1: Position Size Validation
  Account Balance: 10000 EUR
  Max Risk (1%): 100 EUR
  Trade Risk: 100.00 EUR (1.00%)
  ✅ VALID: Position size complies with 1% risk rule

TEST 2: Portfolio Risk Aggregation
  Total Risk: 280.00 EUR (2.80%)
  Total Leverage: 5.45x
  ✅ VALID: Portfolio risk within limits

TEST 3: Daily Loss Limit (3-Loss Rule)
  Wins: 2, Losses: 1
  Daily P&L: +45.00 EUR
  ✅ SAFE: Continue trading (1 losses)

TEST 4: Break-Even Stop Loss Adjustment
  Current R: +0.62R
  ✅ ADJUST: Move SL to break-even
  18150.00 → 18200.00 (entry)
```

---

## Database Schema

### trades table
```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    symbol_id UUID REFERENCES market_symbols(id),
    side TEXT,                    -- 'long' | 'short'
    status TEXT,                  -- 'pending' | 'active' | 'closed'
    entry_price NUMERIC(12, 4),
    stop_loss NUMERIC(12, 4),     -- Updated by adjust_stop_loss()
    take_profit NUMERIC(12, 4),
    position_size NUMERIC(12, 4),
    pnl NUMERIC(12, 2),           -- Profit/Loss
    closed_at TIMESTAMPTZ,        -- For daily loss tracking
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### alerts table
```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    symbol_id UUID REFERENCES market_symbols(id),
    kind TEXT,                    -- 'risk_warning' | ...
    context JSONB,                -- Alert details
    sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### profiles table (metadata)
```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY,
    metadata JSONB,               -- { account_balance: 10000 }
    ...
);
```

---

## Risk Management Rules Summary

| Rule | Threshold | Action |
|------|-----------|--------|
| **Position Risk** | 1% per trade | Reject trade if exceeded |
| **Portfolio Risk** | 5% total | Generate warning alert |
| **Daily Loss Limit** | 3 losses | Stop trading for the day |
| **Symbol Concentration** | 3 trades per symbol | Warn at 2, block at 3 |
| **Leverage** | 10x max | Warn if exceeded |
| **Break-Even Move** | +0.5R profit | Auto-adjust SL to entry |
| **Concurrent Trades** | 10 max | Warn if exceeded |

---

## Example Usage

### Manual Execution
```python
from config.supabase import get_supabase_admin
from risk_manager import RiskManager

# Initialize with admin client
manager = RiskManager(supabase_client=get_supabase_admin())

# Run all risk checks
result = manager.run()

print(f"Portfolio Risk: {result['portfolio_risk']['total_risk_percentage']:.2f}%")
print(f"Losses Today: {result['daily_loss_check']['losses_today']}")
print(f"SL Adjustments: {result['stop_loss_adjustments_count']}")
print(f"Alerts Generated: {result['risk_alerts_generated']}")
```

### Validate New Trade
```python
trade_data = {
    'user_id': 'user-uuid',
    'symbol_id': 'symbol-uuid',
    'side': 'long',
    'entry_price': 18200.0,
    'stop_loss': 18150.0,
    'position_size': 2.0
}

validation = manager.validate_new_trade(trade_data)

if validation['is_valid']:
    print(f"✅ Trade approved: {validation['risk_percentage']:.2f}% risk")
else:
    print(f"❌ Trade rejected: {validation['errors']}")
```

---

## Integration with Other Agents

```
┌──────────────────┐      ┌──────────────────┐
│   SignalBot      │──────│  RiskManager     │
│  (Entry/Exit)    │      │  (Validation)    │
└──────────────────┘      └──────────────────┘
         │                         │
         ├─────────────────────────┤
         │                         │
    ┌────▼─────────────────────────▼────┐
    │         trades table               │
    │  • Validate before creation        │
    │  • Adjust SL during active trade   │
    └────────────────────────────────────┘
```

**Workflow:**
1. SignalBot generates entry signal
2. RiskManager validates via `validate_new_trade()`
3. If valid, trade created in `trades` table
4. RiskManager monitors active trade
5. At +0.5R, RiskManager moves SL to break-even
6. SignalBot generates exit signal at TP/SL

---

## Troubleshooting

### Issue: "Account balance not found"
**Cause:** User profile missing `metadata.account_balance`
**Fix:** Set default balance or update profile

### Issue: "Stop loss not adjusted"
**Cause:** Trade not at +0.5R yet or not active
**Solution:** Check current price and trade status

### Issue: "Too many risk alerts"
**Cause:** Portfolio genuinely over-leveraged
**Solution:** Close some positions to reduce risk

### Issue: "Daily loss limit false positive"
**Cause:** Using UTC timezone, trade date mismatch
**Solution:** Verify `closed_at` timestamps match trading day

---

## Performance Notes

- **Execution Time:** ~1-2 seconds per run
- **Database Queries:** ~5-10 queries (depends on active trades)
- **Optimization:** Uses single query to fetch all active trades
- **Caching:** Account balances could be cached (future)

---

## Future Enhancements

1. **User-specific risk settings** (custom risk % per user)
2. **Correlation risk detection** (correlated symbols)
3. **Max drawdown tracking** (weekly/monthly limits)
4. **Risk-adjusted position sizing** (volatility-based)
5. **Trailing stop loss automation** (move SL as trade progresses)

---

## References

- **RiskCalculator:** `services/api/src/core/risk_calculator.py`
- **Validation Engine:** `services/api/src/core/validation_engine.py`
- **Database Schema:** `services/api/supabase/migrations/001_initial_schema.sql`
- **Celery Tasks:** `services/agents/src/tasks.py`

---

**Last Updated:** 2025-10-29
**Author:** TradeMatrix.ai Development Team
