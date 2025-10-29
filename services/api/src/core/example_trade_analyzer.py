"""
Example Usage: TradeAnalyzer Integration Module

This script demonstrates how to use the TradeAnalyzer to perform
complete trade analysis from data fetching to risk calculation.

Author: TradeMatrix.ai
Date: 2025-10-29
"""

import os
import sys
from pprint import pprint

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trade_analyzer import TradeAnalyzer, create_analyzer, TradeAnalyzerError


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def example_1_basic_analysis():
    """
    Example 1: Basic Analysis (No Trade Plan)

    Demonstrates:
    - Fetching market data
    - Calculating indicators
    - Validating trade signal
    - No risk calculation
    """
    print_section("Example 1: Basic Analysis (No Trade Plan)")

    # Create analyzer with default settings
    analyzer = create_analyzer(
        account_balance=10000.0,
        risk_per_trade=0.01
    )

    try:
        # Perform basic analysis (no entry/SL)
        analysis = analyzer.analyze_symbol(
            symbol="DAX",
            strategy_id="MR-02"
        )

        # Display results
        print("Market Data:")
        print(f"  Symbol: {analysis['market_data']['current_price']}")
        print(f"  Current Price: {analysis['market_data']['current_price']:.2f}")
        print(f"  Candle Count: {analysis['market_data']['candle_count']}")

        print("\nTechnical Indicators:")
        print(f"  EMA 20:  {analysis['indicators']['ema']['20']:.2f}")
        print(f"  EMA 50:  {analysis['indicators']['ema']['50']:.2f}")
        print(f"  EMA 200: {analysis['indicators']['ema']['200']:.2f}")
        print(f"  RSI:     {analysis['indicators']['rsi']:.2f}")
        print(f"  ATR:     {analysis['indicators']['atr']:.2f}")
        print(f"  Trend:   {analysis['indicators']['trend']}")

        print("\nSignal Validation:")
        print(f"  Confidence: {analysis['signal']['confidence']:.1%}")
        print(f"  Valid:      {analysis['signal']['is_valid']}")
        print(f"  Notes:      {analysis['signal']['notes']}")

        print("\nMetric Breakdown:")
        for metric, score in analysis['signal']['breakdown'].items():
            print(f"  {metric:25s}: {score:.2f}")

        print("\nSummary:")
        pprint(analysis['summary'], indent=2)

    except TradeAnalyzerError as e:
        print(f"❌ Error: {str(e)}")


def example_2_complete_analysis():
    """
    Example 2: Complete Analysis (With Trade Plan)

    Demonstrates:
    - Full analysis workflow
    - Entry/SL/TP calculation
    - Position sizing
    - Risk management
    """
    print_section("Example 2: Complete Analysis (With Trade Plan)")

    # Create analyzer
    analyzer = TradeAnalyzer(
        account_balance=10000.0,
        risk_per_trade=0.01
    )

    try:
        # Perform complete analysis with trade parameters
        analysis = analyzer.get_complete_analysis(
            symbol="DAX",
            strategy_id="MR-02",
            interval="1h",
            entry_price=19500.0,
            stop_loss=19450.0,
            position_type='long',
            risk_reward_ratio=2.0,
            product_type='CFD'
        )

        # Display market data
        print("Market Overview:")
        print(f"  Symbol:        {analysis['symbol']}")
        print(f"  Strategy:      {analysis['strategy']}")
        print(f"  Current Price: {analysis['market_data']['current_price']:.2f}")
        print(f"  Trend:         {analysis['indicators']['trend']}")

        # Display signal
        print("\nSignal Analysis:")
        print(f"  Confidence:    {analysis['signal']['confidence']:.1%}")
        print(f"  Valid Signal:  {analysis['signal']['is_valid']}")
        print(f"  Recommendation: {analysis['summary']['recommendation']}")

        # Display trade plan
        if analysis['trade_plan']:
            plan = analysis['trade_plan']
            print("\nTrade Plan:")
            print(f"  Entry:         {plan['entry']:.2f} EUR")
            print(f"  Stop Loss:     {plan['stop_loss']:.2f} EUR")
            print(f"  Take Profit:   {plan['take_profit']:.2f} EUR")
            print(f"  Break-Even:    {plan['break_even_price']:.2f} EUR")

            print("\nPosition Sizing:")
            print(f"  Position Size: {plan['position_size']:.2f} units")
            print(f"  Risk Amount:   {plan['risk_amount']:.2f} EUR ({plan['risk_percentage']:.2f}%)")
            print(f"  1R Distance:   {plan['one_r']:.4f} EUR")
            print(f"  Risk:Reward:   1:{plan['risk_reward_ratio']}")
            print(f"  Leverage:      {plan['leverage']:.2f}x")

            print("\nRisk Assessment:")
            print(f"  Valid Trade:   {'YES ✓' if plan['is_valid'] else 'NO ✗'}")
            if plan['warnings']:
                print("\n  Warnings:")
                for warning in plan['warnings']:
                    print(f"    ⚠️  {warning}")

    except TradeAnalyzerError as e:
        print(f"❌ Error: {str(e)}")


def example_3_short_position():
    """
    Example 3: Short Position Analysis

    Demonstrates:
    - Short position setup
    - Inverted stop loss/take profit
    - Risk calculation for shorts
    """
    print_section("Example 3: Short Position Analysis")

    analyzer = create_analyzer(account_balance=10000.0)

    try:
        # Analyze short position
        analysis = analyzer.get_complete_analysis(
            symbol="NASDAQ",
            strategy_id="MR-01",
            entry_price=18000.0,
            stop_loss=18100.0,  # Above entry for short
            position_type='short',
            risk_reward_ratio=2.0
        )

        print("Short Position Setup:")
        if analysis['trade_plan']:
            plan = analysis['trade_plan']
            print(f"  Direction:     {plan['direction'].upper()}")
            print(f"  Entry:         {plan['entry']:.2f} EUR")
            print(f"  Stop Loss:     {plan['stop_loss']:.2f} EUR (above entry)")
            print(f"  Take Profit:   {plan['take_profit']:.2f} EUR (below entry)")
            print(f"  Position Size: {plan['position_size']:.2f} units")
            print(f"  Risk Amount:   {plan['risk_amount']:.2f} EUR")

    except TradeAnalyzerError as e:
        print(f"❌ Error: {str(e)}")


def example_4_ko_product():
    """
    Example 4: KO Product (Knock-Out Certificate)

    Demonstrates:
    - KO product analysis
    - KO threshold calculation
    - Leverage calculation
    """
    print_section("Example 4: KO Product Analysis")

    analyzer = create_analyzer(account_balance=10000.0)

    try:
        # Analyze with KO product
        analysis = analyzer.get_complete_analysis(
            symbol="DAX",
            strategy_id="MR-04",
            entry_price=19500.0,
            stop_loss=19450.0,
            position_type='long',
            risk_reward_ratio=2.0,
            product_type='KO'
        )

        print("KO Product Setup:")
        if analysis['trade_plan'] and analysis['trade_plan']['ko_data']:
            ko = analysis['trade_plan']['ko_data']
            print(f"  Entry:         {ko['entry']:.2f} EUR")
            print(f"  Stop Loss:     {ko['stop_loss']:.2f} EUR")
            print(f"  KO Threshold:  {ko['ko_threshold']:.2f} EUR")
            print(f"  Safety Buffer: {ko['safety_distance']:.2f} EUR ({ko['safety_distance_pct']:.2f}%)")
            print(f"  KO Leverage:   {ko['leverage']:.2f}x")

            if ko['warnings']:
                print("\n  KO Warnings:")
                for warning in ko['warnings']:
                    print(f"    ⚠️  {warning}")

    except TradeAnalyzerError as e:
        print(f"❌ Error: {str(e)}")


def example_5_step_by_step():
    """
    Example 5: Step-by-Step Analysis

    Demonstrates:
    - Using individual methods
    - Customized workflow
    - Manual processing
    """
    print_section("Example 5: Step-by-Step Analysis")

    analyzer = create_analyzer(account_balance=10000.0)

    try:
        print("Step 1: Fetch Market Data and Calculate Indicators")
        print("-" * 50)

        data = analyzer.fetch_and_calculate_indicators(
            symbol="EUR/USD",
            interval="1h",
            outputsize=300
        )

        print(f"✓ Fetched {data['candle_count']} candles")
        print(f"✓ Current Price: {data['current_price']:.5f}")
        print(f"✓ Calculated all indicators")

        print("\nStep 2: Validate Trade Setup")
        print("-" * 50)

        validation = analyzer.validate_trade_setup(
            symbol="EUR/USD",
            strategy_id="MR-02",
            indicators=data['indicators'],
            current_price=data['current_price']
        )

        print(f"✓ Confidence: {validation.confidence:.1%}")
        print(f"✓ Valid: {validation.is_valid}")
        print(f"✓ Priority Override: {validation.priority_override}")

        print("\nStep 3: Calculate Trade Parameters")
        print("-" * 50)

        trade_params = analyzer.calculate_trade_params(
            entry_price=1.0850,
            stop_loss=1.0825,
            position_type='long',
            risk_reward_ratio=2.0
        )

        print(f"✓ Entry: {trade_params['entry']:.5f}")
        print(f"✓ Stop Loss: {trade_params['stop_loss']:.5f}")
        print(f"✓ Take Profit: {trade_params['take_profit']:.5f}")
        print(f"✓ Position Size: {trade_params['position_size']:.2f} units")
        print(f"✓ Risk: {trade_params['risk_amount']:.2f} EUR ({trade_params['risk_percentage']:.2f}%)")

        print("\n✅ Step-by-step analysis complete!")

    except TradeAnalyzerError as e:
        print(f"❌ Error: {str(e)}")


def example_6_multiple_strategies():
    """
    Example 6: Compare Multiple Strategies

    Demonstrates:
    - Analyzing same symbol with different strategies
    - Strategy comparison
    - Best setup selection
    """
    print_section("Example 6: Multiple Strategy Comparison")

    analyzer = create_analyzer(account_balance=10000.0)

    strategies = ["MR-01", "MR-02", "MR-03"]
    results = []

    try:
        print("Analyzing DAX with multiple strategies...\n")

        for strategy in strategies:
            analysis = analyzer.analyze_symbol("DAX", strategy)
            results.append({
                'strategy': strategy,
                'confidence': analysis['signal']['confidence'],
                'valid': analysis['signal']['is_valid'],
                'trend': analysis['indicators']['trend']
            })

        # Display comparison
        print("Strategy Comparison:")
        print(f"{'Strategy':<10} {'Confidence':>12} {'Valid':>8} {'Trend':>10}")
        print("-" * 45)

        for result in results:
            valid_mark = "✓" if result['valid'] else "✗"
            print(f"{result['strategy']:<10} {result['confidence']:>11.1%} {valid_mark:>8} {result['trend']:>10}")

        # Find best strategy
        best = max(results, key=lambda x: x['confidence'])
        print(f"\n🏆 Best Strategy: {best['strategy']} ({best['confidence']:.1%} confidence)")

    except TradeAnalyzerError as e:
        print(f"❌ Error: {str(e)}")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  TradeAnalyzer - Integration Module Examples".center(68) + "║")
    print("║" + "  Complete Trade Analysis Workflow".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")

    # Note: Examples require Twelve Data API key and Supabase connection
    print("\n⚠️  Note: These examples require:")
    print("   - TWELVE_DATA_API_KEY environment variable")
    print("   - Supabase connection configured")
    print("   - Market symbols in database (DAX, NASDAQ, EUR/USD)")

    input("\n Press Enter to continue (or Ctrl+C to exit)... ")

    # Run examples
    example_1_basic_analysis()
    example_2_complete_analysis()
    example_3_short_position()
    example_4_ko_product()
    example_5_step_by_step()
    example_6_multiple_strategies()

    print("\n")
    print("=" * 70)
    print("  All Examples Complete!")
    print("=" * 70)
    print("\nFor more information, see:")
    print("  - services/api/src/core/trade_analyzer.py")
    print("  - services/api/src/core/test_trade_analyzer.py")
    print("  - docs/PROJECT_OVERVIEW.md")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()
