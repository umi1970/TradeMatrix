"""
ValidationEngine Quick Start Examples
======================================

This file demonstrates common usage patterns for the ValidationEngine.
"""

from validation_engine import ValidationEngine, ValidationResult, validate_trade_signal


def example_1_basic_validation():
    """Example 1: Basic signal validation"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Signal Validation")
    print("="*60)

    # Initialize engine
    engine = ValidationEngine()

    # Prepare signal data (strong bullish setup)
    signal_data = {
        'price': 18500.0,
        'emas': {
            '20': 18450.0,
            '50': 18400.0,
            '200': 18300.0
        },
        'levels': {
            'pivot': 18480.0,
            'r1': 18550.0,
            's1': 18410.0
        },
        'volume': 15000,
        'avg_volume': 10000,
        'candle': {
            'open': 18490.0,
            'high': 18510.0,
            'low': 18485.0,
            'close': 18505.0
        },
        'context': {
            'trend': 'bullish',
            'volatility': 0.15
        },
        'strategy': 'MR-02'
    }

    # Validate signal
    result = engine.validate_signal(signal_data)

    # Display results
    print(f"\nOverall Confidence: {result.confidence:.2%}")
    print(f"Signal Valid: {result.is_valid}")
    print(f"Priority Override: {result.priority_override}")

    print(f"\nMetric Breakdown:")
    for metric, score in result.breakdown.items():
        bar = "█" * int(score * 20)
        print(f"  {metric:.<25} {score:.2f} |{bar}")

    print(f"\nNotes: {result.notes}")

    # Decision logic
    if result.is_valid:
        print("\n✅ TRADE SIGNAL: GO!")
        print(f"   Confidence: {result.confidence:.1%}")
    else:
        print("\n❌ TRADE SIGNAL: PASS")
        print(f"   Confidence too low: {result.confidence:.1%}")


def example_2_priority_override():
    """Example 2: Priority override strategy (MR-04)"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Priority Override Strategy (MR-04)")
    print("="*60)

    engine = ValidationEngine()

    # MR-04: Vortagstief-Reversal with hammer pattern
    signal_data = {
        'price': 18400.0,
        'emas': {
            '20': 18420.0,
            '50': 18450.0,
            '200': 18500.0
        },
        'levels': {
            'pivot': 18480.0,
            'r1': 18550.0,
            's1': 18410.0
        },
        'volume': 20000,  # High volume (2x average)
        'avg_volume': 10000,
        'candle': {
            'open': 18390.0,
            'high': 18405.0,
            'low': 18360.0,  # Long lower wick (hammer)
            'close': 18398.0
        },
        'context': {
            'trend': 'bearish',
            'volatility': 0.20
        },
        'strategy': 'MR-04'  # Priority strategy!
    }

    result = engine.validate_signal(signal_data)

    print(f"\nStrategy: {signal_data['strategy']}")
    print(f"Priority Override: {'✓ YES' if result.priority_override else '✗ NO'}")
    print(f"Confidence: {result.confidence:.2%}")

    if result.priority_override:
        print("\n⚡ PRIORITY SIGNAL - This overrides MR-02 pullback setups!")


def example_3_convenience_function():
    """Example 3: Using the convenience function"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Convenience Function")
    print("="*60)

    # Quick validation without creating engine
    signal_data = {
        'price': 18520.0,
        'emas': {'20': 18500.0, '50': 18480.0, '200': 18450.0},
        'levels': {'pivot': 18500.0, 'r1': 18560.0, 's1': 18440.0},
        'volume': 12000,
        'avg_volume': 10000,
        'candle': {'open': 18510.0, 'high': 18525.0, 'low': 18508.0, 'close': 18522.0},
        'context': {'trend': 'bullish', 'volatility': 0.12},
        'strategy': 'MR-01'
    }

    # One-line validation
    result = validate_trade_signal(signal_data)

    print(f"Quick validation result: {result.confidence:.2%}")
    print(f"Valid: {'✓' if result.is_valid else '✗'}")


def example_4_individual_metrics():
    """Example 4: Checking individual metrics"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Individual Metric Checks")
    print("="*60)

    engine = ValidationEngine()

    # Check EMA alignment
    print("\n1. EMA Alignment Check:")
    ema_score = engine.check_ema_alignment(
        current_price=18500,
        ema_20=18450,
        ema_50=18400,
        ema_200=18300
    )
    print(f"   Score: {ema_score:.2f} ({'✓ Perfect alignment' if ema_score == 1.0 else 'Partial alignment'})")

    # Check pivot confluence
    print("\n2. Pivot Confluence Check:")
    levels = {'pivot': 18480.0, 'r1': 18550.0, 's1': 18410.0}
    pivot_score = engine.check_pivot_confluence(18485.0, levels)
    print(f"   Score: {pivot_score:.2f} (Price: 18485 vs Pivot: 18480)")

    # Check volume
    print("\n3. Volume Confirmation Check:")
    vol_score = engine.check_volume_confirmation(15000, 10000)
    print(f"   Score: {vol_score:.2f} (Current: 15000 vs Avg: 10000 = 1.5x)")

    # Check candle pattern
    print("\n4. Candle Structure Check:")
    hammer = {
        'open': 18390.0,
        'high': 18400.0,
        'low': 18360.0,
        'close': 18395.0
    }
    candle_score = engine.check_candle_structure(hammer)
    print(f"   Score: {candle_score:.2f} (Hammer pattern detected)")

    # Check context
    print("\n5. Context Flow Check:")
    context = {'trend': 'bullish', 'volatility': 0.15}
    context_score = engine.check_context_flow(context)
    print(f"   Score: {context_score:.2f} (Bullish trend, moderate volatility)")


def example_5_custom_threshold():
    """Example 5: Using custom threshold"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Custom Threshold Configuration")
    print("="*60)

    # Default engine (threshold = 0.8)
    default_engine = ValidationEngine()

    # Custom engine (threshold = 0.7)
    custom_config = {'threshold': 0.7}
    custom_engine = ValidationEngine(config=custom_config)

    # Moderate quality signal
    signal_data = {
        'price': 18500.0,
        'emas': {'20': 18480.0, '50': 18460.0, '200': 18440.0},
        'levels': {'pivot': 18450.0, 'r1': 18520.0, 's1': 18380.0},
        'volume': 11000,
        'avg_volume': 10000,
        'candle': {'open': 18495.0, 'high': 18505.0, 'low': 18490.0, 'close': 18502.0},
        'context': {'trend': 'neutral', 'volatility': 0.10},
        'strategy': 'MR-02'
    }

    default_result = default_engine.validate_signal(signal_data)
    custom_result = custom_engine.validate_signal(signal_data)

    print(f"\nSignal Confidence: {default_result.confidence:.2%}")
    print(f"\nDefault Engine (threshold: 0.80): {'✓ VALID' if default_result.is_valid else '✗ INVALID'}")
    print(f"Custom Engine (threshold: 0.70):  {'✓ VALID' if custom_result.is_valid else '✗ INVALID'}")


def example_6_batch_validation():
    """Example 6: Validating multiple signals"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Batch Signal Validation")
    print("="*60)

    engine = ValidationEngine()

    # Multiple signals
    signals = [
        {
            'name': 'DAX Long Setup',
            'data': {
                'price': 18500.0,
                'emas': {'20': 18450.0, '50': 18400.0, '200': 18300.0},
                'levels': {'pivot': 18480.0, 'r1': 18550.0, 's1': 18410.0},
                'volume': 15000,
                'avg_volume': 10000,
                'candle': {'open': 18490.0, 'high': 18510.0, 'low': 18485.0, 'close': 18505.0},
                'context': {'trend': 'bullish', 'volatility': 0.15},
                'strategy': 'MR-02'
            }
        },
        {
            'name': 'NASDAQ Reversal',
            'data': {
                'price': 16200.0,
                'emas': {'20': 16220.0, '50': 16250.0, '200': 16280.0},
                'levels': {'pivot': 16180.0, 'r1': 16240.0, 's1': 16120.0},
                'volume': 22000,
                'avg_volume': 11000,
                'candle': {'open': 16190.0, 'high': 16205.0, 'low': 16165.0, 'close': 16198.0},
                'context': {'trend': 'bearish', 'volatility': 0.18},
                'strategy': 'MR-04'
            }
        },
        {
            'name': 'EUR/USD Weak Setup',
            'data': {
                'price': 1.0850,
                'emas': {'20': 1.0860, '50': 1.0840, '200': 1.0820},
                'levels': {'pivot': 1.0800, 'r1': 1.0880, 's1': 1.0720},
                'volume': 5000,
                'avg_volume': 10000,
                'candle': {'open': 1.0848, 'high': 1.0852, 'low': 1.0846, 'close': 1.0849},
                'context': {'trend': 'neutral', 'volatility': 0.08},
                'strategy': 'MR-02'
            }
        }
    ]

    # Validate all signals
    print("\nValidating signals...\n")
    valid_signals = []

    for signal in signals:
        result = engine.validate_signal(signal['data'])
        status = "✓ VALID" if result.is_valid else "✗ INVALID"
        print(f"{signal['name']:.<30} {result.confidence:.2%} {status}")

        if result.is_valid:
            valid_signals.append(signal)

    print(f"\n{len(valid_signals)}/{len(signals)} signals passed validation")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("VALIDATION ENGINE - QUICK START EXAMPLES")
    print("="*60)

    try:
        example_1_basic_validation()
        example_2_priority_override()
        example_3_convenience_function()
        example_4_individual_metrics()
        example_5_custom_threshold()
        example_6_batch_validation()

        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
