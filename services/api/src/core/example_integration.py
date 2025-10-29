"""
Integration Example: Trading Logic + Validation + Risk Management

Demonstrates how MarketDataFetcher, ValidationEngine, and RiskCalculator
work together to create a complete trading system.

Author: TradeMatrix.ai
Date: 2025-10-29
"""

from risk_calculator import RiskCalculator, format_trade_plan


def example_complete_trade_workflow():
    """
    Example: Complete trade workflow from analysis to execution.

    This simulates the full trading workflow:
    1. Market analysis (simulated)
    2. Signal generation (simulated)
    3. Risk calculation (real)
    4. Trade validation (real)
    5. Position management (simulated)
    """

    print("=" * 80)
    print("COMPLETE TRADE WORKFLOW EXAMPLE")
    print("=" * 80)
    print()

    # Step 1: Initialize Risk Calculator
    print("Step 1: Initialize Risk Calculator")
    print("-" * 80)

    account_balance = 10000.0  # EUR
    calc = RiskCalculator(account_balance=account_balance, risk_per_trade=0.01)

    print(f"Account Balance: {account_balance} EUR")
    print(f"Risk per Trade: {calc.risk_per_trade * 100}%")
    print(f"Max Risk Amount: {calc.max_risk_amount} EUR")
    print()

    # Step 2: Simulated Market Analysis
    print("Step 2: Market Analysis (Simulated)")
    print("-" * 80)

    # Simulated market data (in real system, from MarketDataFetcher)
    market_data = {
        'symbol': 'DAX',
        'current_price': 19500.0,
        'ema_20': 19480.0,
        'ema_50': 19420.0,
        'rsi': 58.5,
        'macd': 12.3,
        'trend': 'bullish',
        'structure': 'higher_high'
    }

    print(f"Symbol: {market_data['symbol']}")
    print(f"Current Price: {market_data['current_price']} EUR")
    print(f"EMA 20: {market_data['ema_20']} EUR")
    print(f"EMA 50: {market_data['ema_50']} EUR")
    print(f"RSI: {market_data['rsi']}")
    print(f"Trend: {market_data['trend']}")
    print()

    # Step 3: Signal Generation
    print("Step 3: Trade Signal Generation")
    print("-" * 80)

    # Trading signal based on strategy
    signal = {
        'type': 'LONG',
        'entry': 19500.0,
        'stop_loss': 19450.0,  # 50 EUR risk = 0.25% from entry
        'confidence': 0.85,
        'reason': 'Pullback to EMA 20 with bullish structure'
    }

    print(f"Signal Type: {signal['type']}")
    print(f"Entry: {signal['entry']} EUR")
    print(f"Stop Loss: {signal['stop_loss']} EUR")
    print(f"Confidence: {signal['confidence'] * 100}%")
    print(f"Reason: {signal['reason']}")
    print()

    # Step 4: Calculate Complete Trade Plan
    print("Step 4: Risk Management & Position Sizing")
    print("-" * 80)

    trade_plan = calc.calculate_full_trade_plan(
        entry=signal['entry'],
        stop_loss=signal['stop_loss'],
        direction='long',
        risk_reward_ratio=2.0,
        product_type='CFD',
        commission_percentage=0.0001  # 0.01% commission
    )

    print(format_trade_plan(trade_plan))
    print()

    # Step 5: Trade Validation
    print("Step 5: Trade Validation")
    print("-" * 80)

    validation = calc.validate_trade_risk(
        entry=trade_plan['entry'],
        stop_loss=trade_plan['stop_loss'],
        position_size=trade_plan['position_size']
    )

    if validation['is_valid']:
        print("✓ Trade is VALID and ready for execution")
        print(f"  Risk Amount: {validation['risk_amount']} EUR ({validation['risk_percentage']}%)")
        print(f"  Leverage: {validation['leverage']}x")
        print(f"  Position Value: {validation['position_value']} EUR")
    else:
        print("✗ Trade FAILED validation:")
        for warning in validation['warnings']:
            print(f"  - {warning}")

    print()

    # Step 6: Simulated Trade Execution
    print("Step 6: Trade Execution (Simulated)")
    print("-" * 80)

    if validation['is_valid']:
        print("Executing trade...")
        print(f"  Entry Order: BUY {trade_plan['position_size']} units @ {trade_plan['entry']} EUR")
        print(f"  Stop Loss: {trade_plan['stop_loss']} EUR")
        print(f"  Take Profit: {trade_plan['take_profit']} EUR")
        print(f"  Break-Even: {trade_plan['break_even_price']} EUR")
        print("Trade executed successfully!")
    else:
        print("Trade execution ABORTED due to validation failure")

    print()

    # Step 7: Position Management Simulation
    print("Step 7: Position Management (Simulated)")
    print("-" * 80)

    # Simulate price movement
    price_updates = [
        19505.0,  # +5 EUR (+0.1R)
        19510.0,  # +10 EUR (+0.2R)
        19525.0,  # +25 EUR (+0.5R) - Break-even trigger!
        19540.0,  # +40 EUR (+0.8R)
        19550.0,  # +50 EUR (+1.0R)
        19575.0,  # +75 EUR (+1.5R)
        19600.0,  # +100 EUR (+2.0R) - Target!
    ]

    current_stop_loss = trade_plan['stop_loss']

    for i, current_price in enumerate(price_updates, 1):
        print(f"\nPrice Update #{i}: {current_price} EUR")

        # Check if should move to break-even
        be_check = calc.should_move_to_break_even(
            entry=trade_plan['entry'],
            current_price=current_price,
            stop_loss=current_stop_loss
        )

        print(f"  Current Profit: +{be_check['current_r']:.2f}R ({current_price - trade_plan['entry']:.2f} EUR)")

        if be_check['should_move'] and current_stop_loss != be_check['new_stop_loss']:
            print(f"  ⚠️  MOVE STOP LOSS TO BREAK-EVEN!")
            print(f"  Old SL: {current_stop_loss} EUR")
            print(f"  New SL: {be_check['new_stop_loss']} EUR")
            current_stop_loss = be_check['new_stop_loss']

        # Check if target reached
        if current_price >= trade_plan['take_profit']:
            profit = (current_price - trade_plan['entry']) * trade_plan['position_size']
            print(f"  🎯 TAKE PROFIT TARGET REACHED!")
            print(f"  Profit: +{profit:.2f} EUR (+{be_check['current_r']:.1f}R)")
            print(f"  Account Balance: {account_balance + profit:.2f} EUR")
            break

    print()
    print("=" * 80)
    print("Trade workflow completed successfully!")
    print("=" * 80)


def example_multiple_trades():
    """
    Example: Managing multiple trades with risk allocation.
    """

    print("\n\n")
    print("=" * 80)
    print("MULTIPLE TRADES RISK MANAGEMENT")
    print("=" * 80)
    print()

    account_balance = 10000.0
    calc = RiskCalculator(account_balance=account_balance, risk_per_trade=0.01)

    # Multiple trade opportunities
    trades = [
        {'symbol': 'DAX', 'entry': 19500.0, 'stop_loss': 19450.0},
        {'symbol': 'NASDAQ', 'entry': 18000.0, 'stop_loss': 17950.0},
        {'symbol': 'EUR/USD', 'entry': 1.0850, 'stop_loss': 1.0800},
    ]

    print(f"Account Balance: {account_balance} EUR")
    print(f"Max Risk per Trade: {calc.max_risk_amount} EUR (1%)")
    print(f"Available for {len(trades)} trades: {calc.max_risk_amount * len(trades)} EUR ({len(trades)}%)")
    print()

    total_risk = 0
    for i, trade in enumerate(trades, 1):
        print(f"Trade #{i}: {trade['symbol']}")
        print("-" * 40)

        plan = calc.calculate_full_trade_plan(
            entry=trade['entry'],
            stop_loss=trade['stop_loss'],
            direction='long',
            risk_reward_ratio=2.0
        )

        print(f"Entry: {plan['entry']} | SL: {plan['stop_loss']} | TP: {plan['take_profit']}")
        print(f"Position Size: {plan['position_size']:.2f} units")
        print(f"Risk: {plan['risk_amount']} EUR ({plan['risk_percentage']}%)")
        print(f"Valid: {'✓' if plan['is_valid'] else '✗'}")

        total_risk += plan['risk_amount']
        print()

    print("-" * 80)
    print(f"Total Risk Across All Trades: {total_risk} EUR ({(total_risk/account_balance)*100:.1f}%)")
    print()

    if total_risk <= account_balance * 0.03:  # Max 3% total risk
        print("✓ Total risk is within acceptable limits (< 3%)")
    else:
        print("⚠️  WARNING: Total risk exceeds 3% - consider reducing positions")

    print("=" * 80)


def example_ko_product_comparison():
    """
    Example: Compare CFD vs KO product for same trade.
    """

    print("\n\n")
    print("=" * 80)
    print("CFD vs KO PRODUCT COMPARISON")
    print("=" * 80)
    print()

    account_balance = 10000.0
    calc = RiskCalculator(account_balance=account_balance)

    entry = 19500.0
    stop_loss = 19450.0

    print(f"Trade Setup:")
    print(f"  Entry: {entry} EUR")
    print(f"  Stop Loss: {stop_loss} EUR")
    print(f"  Direction: LONG")
    print()

    # CFD Trade
    print("Option 1: CFD")
    print("-" * 40)
    cfd_plan = calc.calculate_full_trade_plan(
        entry=entry,
        stop_loss=stop_loss,
        direction='long',
        product_type='CFD'
    )
    print(f"Position Size: {cfd_plan['position_size']} units")
    print(f"Leverage: {cfd_plan['leverage']}x")
    print(f"Risk: {cfd_plan['risk_amount']} EUR")
    print()

    # KO Product
    print("Option 2: KO Certificate")
    print("-" * 40)
    ko_plan = calc.calculate_full_trade_plan(
        entry=entry,
        stop_loss=stop_loss,
        direction='long',
        product_type='KO'
    )
    print(f"Position Size: {ko_plan['position_size']} units")
    print(f"Leverage: {ko_plan['leverage']}x")
    print(f"KO Threshold: {ko_plan['ko_data']['ko_threshold']} EUR")
    print(f"KO Leverage: {ko_plan['ko_data']['leverage']}x")
    print(f"Risk: {ko_plan['risk_amount']} EUR")
    print()

    # Comparison
    print("Comparison:")
    print("-" * 40)
    print(f"CFD Leverage: {cfd_plan['leverage']}x")
    print(f"KO Leverage: {ko_plan['ko_data']['leverage']}x")
    print()
    print("Recommendation:")
    if cfd_plan['leverage'] < 10:
        print("✓ CFD is suitable (low leverage)")
    else:
        print("⚠️  CFD has high leverage - consider KO product")

    print("=" * 80)


if __name__ == "__main__":
    # Run all examples
    example_complete_trade_workflow()
    example_multiple_trades()
    example_ko_product_comparison()

    print("\n\nAll integration examples completed successfully!")
