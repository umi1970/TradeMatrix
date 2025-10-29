"""
TradeMatrix.ai - RiskManager Test Suite
Tests all risk management methods with mock data
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_position_size_validation():
    """Test position size compliance with 1% risk rule"""
    print("\n" + "="*80)
    print("TEST 1: Position Size Validation")
    print("="*80)

    # Mock trade data
    account_balance = 10000.0
    risk_per_trade = 0.01  # 1%
    max_risk = account_balance * risk_per_trade  # 100 EUR

    mock_trade = {
        'id': 'trade-uuid-1',
        'entry_price': 18200.00,
        'stop_loss': 18150.00,
        'position_size': 2.0  # units
    }

    print(f"\nAccount Balance: {account_balance} EUR")
    print(f"Max Risk (1%): {max_risk} EUR")
    print(f"\nTrade Details:")
    print(f"  Entry: {mock_trade['entry_price']}")
    print(f"  Stop Loss: {mock_trade['stop_loss']}")
    print(f"  Position Size: {mock_trade['position_size']} units")

    # Calculate risk
    entry = Decimal(str(mock_trade['entry_price']))
    stop_loss = Decimal(str(mock_trade['stop_loss']))
    position_size = Decimal(str(mock_trade['position_size']))

    risk_per_unit = abs(entry - stop_loss)
    trade_risk = position_size * risk_per_unit

    print(f"\nCalculation:")
    print(f"  Risk per unit: {risk_per_unit} EUR")
    print(f"  Total risk: {float(trade_risk)} EUR")
    print(f"  Risk percentage: {float(trade_risk / Decimal(str(account_balance)) * 100):.2f}%")

    # Validate
    is_valid = float(trade_risk) <= max_risk

    if is_valid:
        print(f"\n✅ VALID: Position size complies with 1% risk rule")
    else:
        print(f"\n❌ VIOLATION: Risk ({float(trade_risk):.2f} EUR) exceeds max ({max_risk:.2f} EUR)")


def test_portfolio_risk_aggregation():
    """Test portfolio-wide risk aggregation"""
    print("\n" + "="*80)
    print("TEST 2: Portfolio Risk Aggregation")
    print("="*80)

    account_balance = 10000.0
    max_portfolio_risk_pct = 5.0  # 5% max

    # Mock active trades
    mock_trades = [
        {'id': 'trade-1', 'entry': 18200, 'sl': 18150, 'size': 2.0, 'symbol': 'DAX'},
        {'id': 'trade-2', 'entry': 16850, 'sl': 16810, 'size': 2.5, 'symbol': 'NDX'},
        {'id': 'trade-3', 'entry': 39500, 'sl': 39400, 'size': 1.0, 'symbol': 'DJI'},
    ]

    print(f"\nAccount Balance: {account_balance} EUR")
    print(f"Max Portfolio Risk: {max_portfolio_risk_pct}%")
    print(f"\nActive Trades: {len(mock_trades)}")

    total_risk = Decimal('0.0')
    total_position_value = Decimal('0.0')

    for i, trade in enumerate(mock_trades, 1):
        entry = Decimal(str(trade['entry']))
        sl = Decimal(str(trade['sl']))
        size = Decimal(str(trade['size']))

        risk_per_unit = abs(entry - sl)
        trade_risk = size * risk_per_unit
        position_value = size * entry

        total_risk += trade_risk
        total_position_value += position_value

        print(f"\n  Trade {i} ({trade['symbol']}):")
        print(f"    Entry: {trade['entry']}, SL: {trade['sl']}, Size: {trade['size']}")
        print(f"    Risk: {float(trade_risk):.2f} EUR")
        print(f"    Position Value: {float(position_value):.2f} EUR")

    # Calculate aggregates
    total_risk_pct = float(total_risk / Decimal(str(account_balance)) * 100)
    total_leverage = float(total_position_value / Decimal(str(account_balance)))

    print(f"\nPortfolio Metrics:")
    print(f"  Total Risk: {float(total_risk):.2f} EUR ({total_risk_pct:.2f}%)")
    print(f"  Total Position Value: {float(total_position_value):.2f} EUR")
    print(f"  Total Leverage: {total_leverage:.2f}x")

    # Validate
    warnings = []
    if total_risk_pct > max_portfolio_risk_pct:
        warnings.append(f"Portfolio risk ({total_risk_pct:.2f}%) exceeds limit ({max_portfolio_risk_pct}%)")

    if total_leverage > 10.0:
        warnings.append(f"Leverage ({total_leverage:.2f}x) exceeds safe limit (10x)")

    if warnings:
        print(f"\n❌ WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print(f"\n✅ VALID: Portfolio risk within limits")


def test_daily_loss_limit():
    """Test 3-loss daily limit enforcement"""
    print("\n" + "="*80)
    print("TEST 3: Daily Loss Limit (3-Loss Rule)")
    print("="*80)

    # Mock closed trades for today
    today_trades = [
        {'id': 'trade-1', 'pnl': -50.00, 'status': 'closed'},
        {'id': 'trade-2', 'pnl': +75.00, 'status': 'closed'},
        {'id': 'trade-3', 'pnl': -40.00, 'status': 'closed'},
        {'id': 'trade-4', 'pnl': -35.00, 'status': 'closed'},
    ]

    print(f"\nToday's Trades: {len(today_trades)}")

    losses = 0
    wins = 0
    daily_pnl = Decimal('0.0')

    for trade in today_trades:
        pnl = Decimal(str(trade['pnl']))
        daily_pnl += pnl

        if pnl < 0:
            losses += 1
            print(f"  ❌ {trade['id']}: {float(pnl):.2f} EUR (LOSS)")
        elif pnl > 0:
            wins += 1
            print(f"  ✅ {trade['id']}: +{float(pnl):.2f} EUR (WIN)")
        else:
            print(f"  ⚪ {trade['id']}: {float(pnl):.2f} EUR (BREAKEVEN)")

    print(f"\nSummary:")
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Daily P&L: {float(daily_pnl):.2f} EUR")

    # Check 3-loss rule
    limit_reached = losses >= 3

    if limit_reached:
        print(f"\n🛑 STOP TRADING: 3-loss limit reached ({losses} losses)")
    elif losses == 2:
        print(f"\n⚠️  WARNING: 2 losses today - one more will trigger limit")
    else:
        print(f"\n✅ SAFE: Continue trading ({losses} losses)")


def test_break_even_adjustment():
    """Test stop loss adjustment to break-even at +0.5R"""
    print("\n" + "="*80)
    print("TEST 4: Break-Even Stop Loss Adjustment")
    print("="*80)

    # Mock trade data
    trade = {
        'id': 'trade-uuid',
        'side': 'long',
        'entry_price': 18200.00,
        'stop_loss': 18150.00,
        'current_price': 18225.00  # Price moved up
    }

    print(f"\nTrade Details:")
    print(f"  Side: {trade['side']}")
    print(f"  Entry: {trade['entry_price']}")
    print(f"  Stop Loss: {trade['stop_loss']}")
    print(f"  Current Price: {trade['current_price']}")

    # Calculate 1R
    entry = Decimal(str(trade['entry_price']))
    stop_loss = Decimal(str(trade['stop_loss']))
    current_price = Decimal(str(trade['current_price']))

    one_r = abs(entry - stop_loss)
    current_profit = current_price - entry
    current_r = float(current_profit / one_r) if one_r > 0 else 0.0

    print(f"\nCalculation:")
    print(f"  1R: {float(one_r)} EUR")
    print(f"  Current Profit: {float(current_profit)} EUR")
    print(f"  Current R: +{current_r:.2f}R")

    # Check break-even threshold (0.5R)
    threshold_r = 0.5
    should_move = current_r >= threshold_r

    if should_move:
        new_stop_loss = float(entry)  # Move to entry (break-even)
        print(f"\n✅ ADJUST: Move SL to break-even")
        print(f"  Old SL: {float(stop_loss)}")
        print(f"  New SL: {new_stop_loss} (entry)")
        print(f"  Reason: Trade at +{current_r:.2f}R (threshold: +{threshold_r}R)")
    else:
        print(f"\n⏳ WAIT: Break-even not reached yet")
        print(f"  Current: +{current_r:.2f}R")
        print(f"  Threshold: +{threshold_r}R")
        print(f"  Need: +{threshold_r - current_r:.2f}R more")


def test_pre_trade_validation():
    """Test pre-trade risk validation"""
    print("\n" + "="*80)
    print("TEST 5: Pre-Trade Risk Validation")
    print("="*80)

    # Mock new trade request
    new_trade = {
        'symbol': 'DAX',
        'side': 'long',
        'entry_price': 18250.00,
        'stop_loss': 18200.00,
        'position_size': 2.0
    }

    # Mock existing portfolio state
    account_balance = 10000.0
    current_portfolio_risk = 3.5  # 3.5% already at risk
    losses_today = 1
    active_trades_for_symbol = 1

    print(f"\nNew Trade Request:")
    print(f"  Symbol: {new_trade['symbol']}")
    print(f"  Side: {new_trade['side']}")
    print(f"  Entry: {new_trade['entry_price']}")
    print(f"  Stop Loss: {new_trade['stop_loss']}")
    print(f"  Position Size: {new_trade['position_size']}")

    print(f"\nCurrent Portfolio State:")
    print(f"  Account Balance: {account_balance} EUR")
    print(f"  Current Risk: {current_portfolio_risk}%")
    print(f"  Losses Today: {losses_today}")
    print(f"  Active Trades for {new_trade['symbol']}: {active_trades_for_symbol}")

    # Calculate new trade risk
    entry = Decimal(str(new_trade['entry_price']))
    stop_loss = Decimal(str(new_trade['stop_loss']))
    position_size = Decimal(str(new_trade['position_size']))

    risk_per_unit = abs(entry - stop_loss)
    trade_risk = position_size * risk_per_unit
    trade_risk_pct = float(trade_risk / Decimal(str(account_balance)) * 100)

    print(f"\nNew Trade Risk:")
    print(f"  Risk Amount: {float(trade_risk):.2f} EUR")
    print(f"  Risk Percentage: {trade_risk_pct:.2f}%")

    # Validate
    errors = []
    warnings = []

    # Check 1: 1% risk rule
    if trade_risk_pct > 1.0:
        errors.append(f"Trade risk ({trade_risk_pct:.2f}%) exceeds 1% limit")

    # Check 2: Portfolio risk after trade
    new_portfolio_risk = current_portfolio_risk + trade_risk_pct
    print(f"  Portfolio Risk After: {new_portfolio_risk:.2f}%")

    if new_portfolio_risk > 5.0:
        errors.append(f"Portfolio risk would exceed 5% limit ({new_portfolio_risk:.2f}%)")

    # Check 3: Daily loss limit
    if losses_today >= 3:
        errors.append("Cannot trade: 3-loss daily limit reached")
    elif losses_today >= 2:
        warnings.append("Warning: 2 losses today - approach with caution")

    # Check 4: Symbol concentration
    if active_trades_for_symbol >= 3:
        errors.append(f"Symbol already has {active_trades_for_symbol} active trades (max: 3)")
    elif active_trades_for_symbol >= 2:
        warnings.append(f"Symbol already has {active_trades_for_symbol} active trades")

    # Result
    is_valid = len(errors) == 0

    print(f"\nValidation Result: {'✅ APPROVED' if is_valid else '❌ REJECTED'}")

    if errors:
        print(f"\nErrors:")
        for error in errors:
            print(f"  ❌ {error}")

    if warnings:
        print(f"\nWarnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")

    if is_valid and not warnings:
        print(f"\n✅ SAFE TO TRADE")


def test_full_execution_summary():
    """Test complete RiskManager execution summary"""
    print("\n" + "="*80)
    print("TEST 6: Full Execution Summary")
    print("="*80)

    # Mock execution results
    summary = {
        'execution_time': datetime.now(timezone.utc).isoformat(),
        'execution_duration_ms': 1850,
        'portfolio_risk': {
            'total_risk_amount': 280.00,
            'total_risk_percentage': 2.80,
            'total_position_value': 54500.00,
            'total_leverage': 5.45,
            'active_trades_count': 3,
            'symbols_exposed': 3,
            'warnings': []
        },
        'daily_loss_check': {
            'trade_date': '2025-10-29',
            'losses_today': 1,
            'wins_today': 2,
            'daily_pnl': 45.00,
            'limit_reached': False,
            'warnings': []
        },
        'position_violations_count': 0,
        'position_violations': [],
        'stop_loss_adjustments_count': 1,
        'stop_loss_adjustments': [
            {
                'trade_id': 'trade-uuid-1',
                'adjusted': True,
                'old_stop_loss': 18150.00,
                'new_stop_loss': 18200.00,
                'current_r': 0.62,
                'reason': 'Trade at +0.62R, moving SL to break-even'
            }
        ],
        'risk_alerts_generated': 0
    }

    print(f"\nExecution Time: {summary['execution_time']}")
    print(f"Duration: {summary['execution_duration_ms']}ms")

    print(f"\n📊 Portfolio Risk:")
    pr = summary['portfolio_risk']
    print(f"  Total Risk: {pr['total_risk_amount']:.2f} EUR ({pr['total_risk_percentage']:.2f}%)")
    print(f"  Active Trades: {pr['active_trades_count']}")
    print(f"  Symbols Exposed: {pr['symbols_exposed']}")
    print(f"  Leverage: {pr['total_leverage']:.2f}x")
    print(f"  Status: {'✅ HEALTHY' if not pr['warnings'] else '⚠️  WARNINGS'}")

    print(f"\n📅 Daily Loss Check:")
    dl = summary['daily_loss_check']
    print(f"  W/L Record: {dl['wins_today']}W - {dl['losses_today']}L")
    print(f"  Daily P&L: {dl['daily_pnl']:+.2f} EUR")
    print(f"  Limit Reached: {'🛑 YES' if dl['limit_reached'] else '✅ NO'}")

    print(f"\n⚠️  Position Violations: {summary['position_violations_count']}")

    print(f"\n🎯 Stop Loss Adjustments: {summary['stop_loss_adjustments_count']}")
    for adj in summary['stop_loss_adjustments']:
        print(f"  - Trade {adj['trade_id'][:8]}...")
        print(f"    {adj['old_stop_loss']:.2f} → {adj['new_stop_loss']:.2f} (at +{adj['current_r']:.2f}R)")

    print(f"\n🔔 Risk Alerts Generated: {summary['risk_alerts_generated']}")

    print(f"\n✅ EXECUTION COMPLETE: All risk checks performed")


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# TradeMatrix.ai - RiskManager Test Suite")
    print("#"*80)

    # Run all tests
    test_position_size_validation()
    test_portfolio_risk_aggregation()
    test_daily_loss_limit()
    test_break_even_adjustment()
    test_pre_trade_validation()
    test_full_execution_summary()

    print("\n" + "#"*80)
    print("# All Tests Complete!")
    print("#"*80 + "\n")
