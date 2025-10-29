"""
Test suite for ValidationEngine
================================

Demonstrates usage and validates functionality of the ValidationEngine.
"""

from validation_engine import (
    ValidationEngine,
    ValidationResult,
    StrategyType,
    validate_trade_signal
)


def test_basic_validation():
    """Test basic signal validation with all metrics"""
    print("\n" + "="*60)
    print("TEST 1: Basic Signal Validation")
    print("="*60)

    engine = ValidationEngine()

    # Create a test signal with strong metrics
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

    result = engine.validate_signal(signal_data)

    print(f"\nOverall Confidence: {result.confidence:.2%}")
    print(f"Valid Signal: {result.is_valid}")
    print(f"Priority Override: {result.priority_override}")
    print(f"\nMetric Breakdown:")
    for metric, score in result.breakdown.items():
        print(f"  {metric:.<30} {score:.2f} ({score:.1%})")
    print(f"\nNotes: {result.notes}")

    assert result.confidence >= 0.0 and result.confidence <= 1.0
    print("\n✓ Test passed!")


def test_priority_override():
    """Test priority override for MR-04 and MR-06 strategies"""
    print("\n" + "="*60)
    print("TEST 2: Priority Override (MR-04)")
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
        'volume': 20000,  # High volume
        'avg_volume': 10000,
        'candle': {
            'open': 18380.0,
            'high': 18410.0,
            'low': 18375.0,  # Long lower wick (hammer)
            'close': 18405.0
        },
        'context': {
            'trend': 'bearish',
            'volatility': 0.20
        },
        'strategy': 'MR-04'  # Priority override strategy
    }

    result = engine.validate_signal(signal_data)

    print(f"\nOverall Confidence: {result.confidence:.2%}")
    print(f"Valid Signal: {result.is_valid}")
    print(f"Priority Override: {result.priority_override}")
    print(f"\nMetric Breakdown:")
    for metric, score in result.breakdown.items():
        print(f"  {metric:.<30} {score:.2f} ({score:.1%})")
    print(f"\nNotes: {result.notes}")

    assert result.priority_override == True
    print("\n✓ Test passed!")


def test_weak_signal():
    """Test signal with weak metrics (should fail validation)"""
    print("\n" + "="*60)
    print("TEST 3: Weak Signal (Should Fail)")
    print("="*60)

    engine = ValidationEngine()

    # Create a weak signal
    signal_data = {
        'price': 18500.0,
        'emas': {
            '20': 18520.0,  # Price below EMA20 (bearish)
            '50': 18480.0,  # But EMA50 below EMA20 (conflicting)
            '200': 18300.0
        },
        'levels': {
            'pivot': 18300.0,  # Far from pivot
            'r1': 18350.0,
            's1': 18250.0
        },
        'volume': 5000,  # Low volume
        'avg_volume': 10000,
        'candle': {
            'open': 18505.0,
            'high': 18508.0,
            'low': 18498.0,
            'close': 18500.0  # Doji-like (indecision)
        },
        'context': {
            'trend': 'neutral',
            'volatility': 0.05  # Low volatility
        },
        'strategy': 'MR-02'
    }

    result = engine.validate_signal(signal_data)

    print(f"\nOverall Confidence: {result.confidence:.2%}")
    print(f"Valid Signal: {result.is_valid}")
    print(f"Priority Override: {result.priority_override}")
    print(f"\nMetric Breakdown:")
    for metric, score in result.breakdown.items():
        print(f"  {metric:.<30} {score:.2f} ({score:.1%})")
    print(f"\nNotes: {result.notes}")

    assert result.is_valid == False
    print("\n✓ Test passed!")


def test_individual_metrics():
    """Test individual metric calculation methods"""
    print("\n" + "="*60)
    print("TEST 4: Individual Metric Calculations")
    print("="*60)

    engine = ValidationEngine()

    # Test EMA alignment
    print("\n--- EMA Alignment ---")
    ema_score = engine.check_ema_alignment(18500, 18450, 18400, 18300)
    print(f"Perfect bullish alignment: {ema_score:.2f}")
    assert ema_score == 1.0

    ema_score_partial = engine.check_ema_alignment(18500, 18450, 18420, 18300)
    print(f"Partial alignment: {ema_score_partial:.2f}")

    # Test pivot confluence
    print("\n--- Pivot Confluence ---")
    levels = {'pivot': 18480.0, 'r1': 18550.0, 's1': 18410.0}
    pivot_score = engine.check_pivot_confluence(18485.0, levels)
    print(f"Close to pivot (18485 vs 18480): {pivot_score:.2f}")
    assert pivot_score > 0.8

    pivot_score_far = engine.check_pivot_confluence(18600.0, levels)
    print(f"Far from levels (18600): {pivot_score_far:.2f}")

    # Test volume confirmation
    print("\n--- Volume Confirmation ---")
    vol_score = engine.check_volume_confirmation(15000, 10000)
    print(f"1.5x average volume: {vol_score:.2f}")
    assert vol_score >= 0.8

    vol_score_low = engine.check_volume_confirmation(5000, 10000)
    print(f"0.5x average volume: {vol_score_low:.2f}")

    # Test candle structure
    print("\n--- Candle Structure ---")
    # Proper hammer: small body, long lower wick (>50%), minimal upper wick
    hammer = {
        'open': 18390.0,
        'high': 18400.0,
        'low': 18360.0,  # Long lower wick (30 points)
        'close': 18395.0  # Small body (5 points) at top of range
    }
    # Total range: 40, Body: 5 (12.5%), Lower wick: 30 (75%), Upper wick: 5 (12.5%)
    candle_score = engine.check_candle_structure(hammer)
    print(f"Hammer pattern: {candle_score:.2f}")
    assert candle_score > 0.8

    # Test context flow
    print("\n--- Context Flow ---")
    context = {'trend': 'bullish', 'volatility': 0.15}
    context_score = engine.check_context_flow(context)
    print(f"Bullish trend, moderate volatility: {context_score:.2f}")

    print("\n✓ All individual metric tests passed!")


def test_convenience_function():
    """Test the convenience function"""
    print("\n" + "="*60)
    print("TEST 5: Convenience Function")
    print("="*60)

    signal_data = {
        'price': 18500.0,
        'emas': {'20': 18450.0, '50': 18400.0, '200': 18300.0},
        'levels': {'pivot': 18480.0, 'r1': 18550.0, 's1': 18410.0},
        'volume': 15000,
        'avg_volume': 10000,
        'candle': {'open': 18490.0, 'high': 18510.0, 'low': 18485.0, 'close': 18505.0},
        'context': {'trend': 'bullish', 'volatility': 0.15},
        'strategy': 'MR-02'
    }

    result = validate_trade_signal(signal_data)

    print(f"\nConfidence: {result.confidence:.2%}")
    print(f"Valid: {result.is_valid}")

    assert isinstance(result, ValidationResult)
    print("\n✓ Test passed!")


def test_custom_config():
    """Test custom configuration"""
    print("\n" + "="*60)
    print("TEST 6: Custom Configuration")
    print("="*60)

    # Create engine with lower threshold
    custom_config = {
        'threshold': 0.65  # Lower threshold
    }
    engine = ValidationEngine(config=custom_config)

    signal_data = {
        'price': 18500.0,
        'emas': {'20': 18480.0, '50': 18450.0, '200': 18400.0},
        'levels': {'pivot': 18450.0, 'r1': 18550.0, 's1': 18410.0},
        'volume': 12000,
        'avg_volume': 10000,
        'candle': {'open': 18495.0, 'high': 18505.0, 'low': 18490.0, 'close': 18502.0},
        'context': {'trend': 'neutral', 'volatility': 0.12},
        'strategy': 'MR-01'
    }

    result = engine.validate_signal(signal_data)

    print(f"\nCustom threshold: {custom_config['threshold']:.2%}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Valid: {result.is_valid}")

    assert engine.threshold == 0.65
    print("\n✓ Test passed!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("VALIDATION ENGINE TEST SUITE")
    print("="*60)

    try:
        test_basic_validation()
        test_priority_override()
        test_weak_signal()
        test_individual_metrics()
        test_convenience_function()
        test_custom_config()

        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✓")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
