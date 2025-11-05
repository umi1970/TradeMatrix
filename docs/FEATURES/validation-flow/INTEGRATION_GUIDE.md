# ValidationAndRisk Flow - Integration Guide
**Quick Reference for Phase 4B Modules**

**Date:** 2025-11-05
**Status:** Ready for Integration Testing

---

## 🚀 Quick Start

### 1. Database Setup (5 minutes)

Execute Migration 019 in Supabase SQL Editor:

```sql
-- Location: services/api/supabase/migrations/019_validation_flow_tables.sql
-- This creates 3 tables: trade_decisions, journal_entries, report_queue
```

**Verification:**
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('trade_decisions', 'journal_entries', 'report_queue');

-- Check RLS policies
SELECT tablename, policyname FROM pg_policies
WHERE tablename IN ('trade_decisions', 'journal_entries', 'report_queue');

-- Check helper function
SELECT get_decision_stats('00000000-0000-0000-0000-000000000000', 7);
```

---

### 2. Import Modules

```python
# In your flow orchestrator (e.g., tasks.py, celery_tasks.py)
from src.trade_decision_engine import TradeDecisionEngine
from src.risk_context_evaluator import RiskContextEvaluator
from src.report_bridge import ReportBridge
from config.supabase import get_supabase_admin
```

---

## 📋 Flow Integration Example

### Complete ValidationAndRisk Flow

```python
from uuid import UUID
from supabase import Client
from src.trade_decision_engine import TradeDecisionEngine
from src.risk_context_evaluator import RiskContextEvaluator
from src.report_bridge import ReportBridge
from config.supabase import get_supabase_admin

def validation_and_risk_flow(
    trade_proposal: dict,
    user_id: UUID,
    symbol_id: UUID
):
    """
    Complete ValidationAndRisk flow

    Steps:
    1. EventWatcher - Check high-risk events
    2. TradeValidationEngine - Validate trade setup
    3. RiskManager - Calculate position size
    4. RiskContextEvaluator - Check account exposure
    5. TradeDecisionEngine - Make final decision
    6. ReportBridge - Forward to journal + publisher
    """

    # Initialize modules
    supabase = get_supabase_admin()
    risk_evaluator = RiskContextEvaluator(
        supabase_client=supabase,
        max_daily_loss_pct=3.0,
        max_open_trades=5
    )
    decision_engine = TradeDecisionEngine(supabase_client=supabase)
    report_bridge = ReportBridge(supabase_client=supabase)

    try:
        # Step 1 & 2: Get validation result (from existing modules)
        # Assume validation_result comes from TradeValidationEngine
        validation_result = {
            "status": "APPROVED",  # or "REJECTED"
            "bias_score": 0.85,
            "rr": 2.5,
            "timestamp": "2025-11-05T10:00:00Z",
            "warnings": []
        }

        # Step 3: Check high-risk events (from EventWatcher)
        high_risk = False  # Placeholder - replace with actual EventWatcher check

        # Step 4: Evaluate risk context
        risk_context = risk_evaluator.evaluate(user_id=user_id)

        print(f"Risk Context: {risk_context['mode']} - Allowed: {risk_context['allowed']}")

        # Step 5: Make final decision
        final_decision = decision_engine.decide(
            validation_result=validation_result,
            risk_context=risk_context,
            high_risk=high_risk,
            trade_proposal=trade_proposal
        )

        print(f"Final Decision: {final_decision['decision']} - Reason: {final_decision['reason']}")

        # Save decision to database
        decision_id = decision_engine.save_decision(
            decision=final_decision,
            trade_id=trade_proposal.get('trade_id'),
            user_id=user_id,
            symbol_id=symbol_id
        )

        print(f"Decision saved: {decision_id}")

        # Step 6: Forward to journal and publisher
        bridge_result = report_bridge.process(
            final_decision=final_decision,
            trade_data=trade_proposal
        )

        print(f"Journal Entry: {bridge_result['journal_entry_id']}")
        print(f"Report Queue: {bridge_result['publish_queue_id']}")

        return {
            "success": True,
            "decision": final_decision['decision'],
            "decision_id": str(decision_id),
            "journal_entry_id": bridge_result['journal_entry_id'],
            "publish_queue_id": bridge_result['publish_queue_id']
        }

    except Exception as e:
        print(f"Error in validation flow: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Example usage
if __name__ == "__main__":
    trade_proposal = {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "symbol_id": "123e4567-e89b-12d3-a456-426614174001",
        "trade_id": None,  # If creating new trade
        "side": "long",
        "entry_price": 18500.0,
        "stop_loss": 18400.0,
        "take_profit": 18700.0,
        "strategy": "support_bounce"
    }

    result = validation_and_risk_flow(
        trade_proposal=trade_proposal,
        user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        symbol_id=UUID("123e4567-e89b-12d3-a456-426614174001")
    )

    print("\n=== Flow Result ===")
    print(result)
```

---

## 🔧 Individual Module Usage

### RiskContextEvaluator

```python
from src.risk_context_evaluator import RiskContextEvaluator
from config.supabase import get_supabase_admin
from uuid import UUID

# Initialize
evaluator = RiskContextEvaluator(
    supabase_client=get_supabase_admin(),
    max_daily_loss_pct=3.0,
    max_open_trades=5
)

# Evaluate risk context
user_id = UUID("your-user-id")
risk_context = evaluator.evaluate(user_id=user_id)

print(f"Risk Mode: {risk_context['mode']}")
print(f"Allowed to trade: {risk_context['allowed']}")
print(f"Open Trades: {risk_context['open_trades']}")
print(f"Daily P&L: {risk_context['daily_pnl_pct']}%")

# Get comprehensive risk summary
risk_summary = evaluator.get_risk_summary(user_id=user_id)
print(f"Avg Daily P&L (7d): {risk_summary['last_7_days']['avg_daily_pnl']}")
print(f"Max Daily Loss (7d): {risk_summary['last_7_days']['max_daily_loss_pct']}%")
```

**Output:**
```python
{
    'balance': 10000.0,
    'equity': 10000.0,
    'open_trades': 2,
    'daily_pnl_pct': -1.5,
    'mode': 'NORMAL',  # or STOP_TRADING, LIMITED_MODE
    'allowed': True,
    'warnings': [],
    'limits': {
        'max_daily_loss_pct': 3.0,
        'max_open_trades': 5
    }
}
```

---

### TradeDecisionEngine

```python
from src.trade_decision_engine import TradeDecisionEngine
from config.supabase import get_supabase_admin
from uuid import UUID

# Initialize
engine = TradeDecisionEngine(supabase_client=get_supabase_admin())

# Make decision
decision = engine.decide(
    validation_result={
        "status": "APPROVED",
        "bias_score": 0.85,
        "rr": 2.5,
        "timestamp": "2025-11-05T10:00:00Z",
        "warnings": []
    },
    risk_context={
        "mode": "NORMAL",
        "balance": 10000.0,
        "open_trades": 2,
        "daily_pnl_pct": -1.5,
        "allowed": True
    },
    high_risk=False,
    trade_proposal={"side": "long", "entry_price": 18500.0}
)

print(f"Decision: {decision['decision']}")
print(f"Reason: {decision['reason']}")

# Save decision to database
decision_id = engine.save_decision(
    decision=decision,
    trade_id=None,  # or UUID if trade exists
    user_id=UUID("your-user-id"),
    symbol_id=UUID("your-symbol-id")
)

print(f"Saved as: {decision_id}")

# Get decision history
history = engine.get_decision_history(
    user_id=UUID("your-user-id"),
    limit=10
)

print(f"Last 10 decisions: {len(history)}")

# Get statistics
stats = engine.get_decision_stats(
    user_id=UUID("your-user-id"),
    days=7
)

print(f"Execute Rate (7d): {stats['execute_rate']}%")
print(f"Avg Bias Score: {stats['avg_bias_score']}")
print(f"Avg RR Ratio: {stats['avg_rr_ratio']}")
```

**Output:**
```python
{
    'decision': 'EXECUTE',  # or REJECT, WAIT, HALT, REDUCE
    'reason': 'All validation and risk checks passed',
    'bias_score': 0.85,
    'rr': 2.5,
    'risk_context': {...},
    'validation_warnings': [],
    'high_risk_event': False,
    'timestamp': '2025-11-05T10:00:00Z',
    'trade_proposal': {...}
}
```

---

### ReportBridge

```python
from src.report_bridge import ReportBridge
from config.supabase import get_supabase_admin

# Initialize
bridge = ReportBridge(supabase_client=get_supabase_admin())

# Process decision (main method)
result = bridge.process(
    final_decision={
        "decision": "EXECUTE",
        "reason": "All checks passed",
        "bias_score": 0.85,
        "rr": 2.5,
        "timestamp": "2025-11-05T10:00:00Z"
    },
    trade_data={
        "user_id": "your-user-id",
        "symbol_id": "your-symbol-id",
        "side": "long",
        "entry_price": 18500.0
    }
)

print(f"Journal Entry: {result['journal_entry_id']}")
print(f"Report Queue: {result['publish_queue_id']}")
print(f"Success: {result['success']}")

# Or use individual methods:

# Forward to journal only
journal_id = bridge.forward_to_journal(final_decision, trade_data)

# Forward to publisher only
publish_id = bridge.forward_to_publisher(final_decision, trade_data)

# Get queue statistics
queue_stats = bridge.get_queue_stats()
print(f"Pending reports: {queue_stats['pending_count']}")
print(f"Completed reports: {queue_stats['completed_count']}")
```

**Output:**
```python
{
    'journal_entry_id': '123e4567-e89b-12d3-a456-426614174002',
    'publish_queue_id': '123e4567-e89b-12d3-a456-426614174003',
    'success': True,
    'timestamp': '2025-11-05T10:00:00Z',
    'decision': 'EXECUTE'
}
```

---

## 🧪 Testing Examples

### Unit Test - TradeDecisionEngine

```python
def test_decision_execute():
    """Test EXECUTE decision path"""
    engine = TradeDecisionEngine(supabase_client=None)

    decision = engine.decide(
        validation_result={"status": "APPROVED", "bias_score": 0.85, "rr": 2.5},
        risk_context={"mode": "NORMAL", "allowed": True},
        high_risk=False
    )

    assert decision['decision'] == 'EXECUTE'
    assert decision['reason'] == 'All validation and risk checks passed'


def test_decision_reject():
    """Test REJECT decision path"""
    engine = TradeDecisionEngine(supabase_client=None)

    decision = engine.decide(
        validation_result={"status": "REJECTED", "warnings": ["Bias too low"]},
        risk_context={"mode": "NORMAL", "allowed": True},
        high_risk=False
    )

    assert decision['decision'] == 'REJECT'
    assert 'Bias too low' in decision['reason']


def test_decision_halt():
    """Test HALT decision path (daily loss limit)"""
    engine = TradeDecisionEngine(supabase_client=None)

    decision = engine.decide(
        validation_result={"status": "APPROVED"},
        risk_context={"mode": "STOP_TRADING", "allowed": False},
        high_risk=False
    )

    assert decision['decision'] == 'HALT'
    assert 'Daily loss limit' in decision['reason']
```

### Integration Test - Full Flow

```python
def test_full_validation_flow():
    """Test complete ValidationAndRisk flow"""
    from config.supabase import get_supabase_admin

    supabase = get_supabase_admin()

    # Setup
    risk_evaluator = RiskContextEvaluator(supabase, 3.0, 5)
    decision_engine = TradeDecisionEngine(supabase)
    report_bridge = ReportBridge(supabase)

    user_id = UUID("your-test-user-id")
    symbol_id = UUID("your-test-symbol-id")

    # Execute flow
    risk_context = risk_evaluator.evaluate(user_id=user_id)
    assert risk_context['mode'] in ['NORMAL', 'STOP_TRADING', 'LIMITED_MODE']

    final_decision = decision_engine.decide(
        validation_result={"status": "APPROVED", "bias_score": 0.85, "rr": 2.5},
        risk_context=risk_context,
        high_risk=False
    )
    assert final_decision['decision'] in ['EXECUTE', 'REJECT', 'WAIT', 'HALT', 'REDUCE']

    decision_id = decision_engine.save_decision(
        decision=final_decision,
        user_id=user_id,
        symbol_id=symbol_id
    )
    assert decision_id is not None

    bridge_result = report_bridge.process(final_decision)
    assert bridge_result['success'] == True
    assert bridge_result['journal_entry_id'] is not None
    assert bridge_result['publish_queue_id'] is not None
```

---

## 📊 Monitoring Queries

### Check Recent Decisions
```sql
-- Last 10 decisions
SELECT decision, reason, bias_score, rr_ratio, created_at
FROM trade_decisions
ORDER BY created_at DESC
LIMIT 10;
```

### Decision Statistics
```sql
-- Today's decision breakdown
SELECT
    decision,
    COUNT(*) as count,
    AVG(bias_score) as avg_bias,
    AVG(rr_ratio) as avg_rr
FROM trade_decisions
WHERE created_at >= CURRENT_DATE
GROUP BY decision
ORDER BY count DESC;
```

### Report Queue Status
```sql
-- Queue health check
SELECT
    status,
    COUNT(*) as count,
    MIN(created_at) as oldest
FROM report_queue
GROUP BY status
ORDER BY status;
```

### User Decision Stats (Using Helper Function)
```sql
-- Get stats for a user
SELECT * FROM get_decision_stats(
    'your-user-id'::UUID,
    7  -- last 7 days
);
```

---

## 🔍 Troubleshooting

### Issue: "Table does not exist"
**Solution:** Execute Migration 019 in Supabase SQL Editor

### Issue: "RLS policy denies access"
**Solution:** Use `get_supabase_admin()` client (bypasses RLS) for agent operations

### Issue: "Module import error"
**Solution:** Ensure Python path includes `hetzner-deploy/src/`:
```python
import sys
sys.path.insert(0, '/path/to/hetzner-deploy/src')
```

### Issue: "Decision not saved to database"
**Solution:** Check Supabase connection and RLS policies:
```python
result = supabase.table('trade_decisions').select('*').limit(1).execute()
print(result.data)  # Should return data or empty list
```

---

## 📚 Additional Resources

- **Full Documentation:** `/docs/FEATURES/validation-flow/PHASE_4B_IMPLEMENTATION_SUMMARY.md`
- **SQL Migration:** `/services/api/supabase/migrations/019_validation_flow_tables.sql`
- **Flow Definition:** `/docs/yaml/flows/ValidationAndRisk.yaml`
- **Module Source:**
  - `/hetzner-deploy/src/trade_decision_engine.py`
  - `/hetzner-deploy/src/risk_context_evaluator.py`
  - `/hetzner-deploy/src/report_bridge.py`

---

**Need Help?** Check the implementation summary or ask umi1970!
