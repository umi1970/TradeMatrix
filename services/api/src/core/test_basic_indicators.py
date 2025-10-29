"""
Basic Tests for Technical Indicators (No pytest required)

Simple test script that can run without external dependencies.
Tests core functionality of the technical indicators module.

Author: TradeMatrix.ai
"""

import sys
import traceback


def test_imports():
    """Test that module imports correctly"""
    try:
        import numpy as np
        from technical_indicators import TechnicalIndicators
        print("✓ Imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("\nPlease install dependencies:")
        print("  pip install numpy pandas")
        return False


def test_sma():
    """Test Simple Moving Average"""
    try:
        from technical_indicators import TechnicalIndicators
        import numpy as np

        prices = [10, 11, 12, 13, 14, 15]
        sma = TechnicalIndicators.calculate_sma(prices, 3)

        # Check first two are NaN
        assert np.isnan(sma[0]) and np.isnan(sma[1]), "First values should be NaN"

        # Check calculated values
        assert abs(sma[2] - 11.0) < 0.01, f"SMA[2] should be 11.0, got {sma[2]}"
        assert abs(sma[3] - 12.0) < 0.01, f"SMA[3] should be 12.0, got {sma[3]}"

        print("✓ SMA calculation correct")
        return True
    except Exception as e:
        print(f"✗ SMA test failed: {e}")
        traceback.print_exc()
        return False


def test_ema():
    """Test Exponential Moving Average"""
    try:
        from technical_indicators import TechnicalIndicators
        import numpy as np

        prices = [100.0] * 30
        ema = TechnicalIndicators.calculate_ema(prices, 10)

        # For constant prices, EMA should equal price
        assert abs(ema[-1] - 100.0) < 0.01, "EMA should equal constant price"

        print("✓ EMA calculation correct")
        return True
    except Exception as e:
        print(f"✗ EMA test failed: {e}")
        traceback.print_exc()
        return False


def test_rsi():
    """Test Relative Strength Index"""
    try:
        from technical_indicators import TechnicalIndicators
        import numpy as np

        # Uptrend should give high RSI
        uptrend = list(range(100, 150))
        rsi_up = TechnicalIndicators.calculate_rsi(uptrend, 14)

        # Check RSI is in valid range
        valid_rsi = rsi_up[~np.isnan(rsi_up)]
        assert all(0 <= r <= 100 for r in valid_rsi), "RSI must be 0-100"
        assert rsi_up[-1] > 70, "Strong uptrend should give RSI > 70"

        print("✓ RSI calculation correct")
        return True
    except Exception as e:
        print(f"✗ RSI test failed: {e}")
        traceback.print_exc()
        return False


def test_macd():
    """Test MACD"""
    try:
        from technical_indicators import TechnicalIndicators, MACDResult

        prices = list(range(100, 150))
        macd = TechnicalIndicators.calculate_macd(prices, 12, 26, 9)

        assert isinstance(macd, MACDResult), "Should return MACDResult"
        assert len(macd.macd_line) == len(prices), "MACD length should match input"

        # In uptrend, MACD should be positive
        valid_idx = ~macd.macd_line.isnan()
        assert macd.macd_line[-1] > 0, "Uptrend should have positive MACD"

        print("✓ MACD calculation correct")
        return True
    except Exception as e:
        print(f"✗ MACD test failed: {e}")
        traceback.print_exc()
        return False


def test_bollinger_bands():
    """Test Bollinger Bands"""
    try:
        from technical_indicators import TechnicalIndicators, BollingerBandsResult
        import numpy as np

        prices = [100 + i for i in range(50)]
        bb = TechnicalIndicators.calculate_bollinger_bands(prices, 20, 2)

        assert isinstance(bb, BollingerBandsResult), "Should return BollingerBandsResult"

        # Check bands order: upper > middle > lower
        valid_idx = ~np.isnan(bb.middle)
        assert all(bb.upper[valid_idx] > bb.middle[valid_idx]), "Upper > Middle"
        assert all(bb.middle[valid_idx] > bb.lower[valid_idx]), "Middle > Lower"

        print("✓ Bollinger Bands calculation correct")
        return True
    except Exception as e:
        print(f"✗ Bollinger Bands test failed: {e}")
        traceback.print_exc()
        return False


def test_atr():
    """Test Average True Range"""
    try:
        from technical_indicators import TechnicalIndicators
        import numpy as np

        high = [110, 112, 111, 113, 115] * 5
        low = [105, 107, 106, 108, 110] * 5
        close = [108, 110, 109, 112, 113] * 5

        atr = TechnicalIndicators.calculate_atr(high, low, close, 5)

        # ATR should be positive
        valid_atr = atr[~np.isnan(atr)]
        assert all(a > 0 for a in valid_atr), "ATR must be positive"

        print("✓ ATR calculation correct")
        return True
    except Exception as e:
        print(f"✗ ATR test failed: {e}")
        traceback.print_exc()
        return False


def test_pivot_points():
    """Test Pivot Points"""
    try:
        from technical_indicators import TechnicalIndicators, PivotPointsResult

        high = 1.2050
        low = 1.2000
        close = 1.2030

        pivots = TechnicalIndicators.calculate_pivot_points(high, low, close)

        assert isinstance(pivots, PivotPointsResult), "Should return PivotPointsResult"

        # Check resistance levels are above PP
        assert pivots.r1 > pivots.pp, "R1 > PP"
        assert pivots.r2 > pivots.r1, "R2 > R1"
        assert pivots.r3 > pivots.r2, "R3 > R2"

        # Check support levels are below PP
        assert pivots.s1 < pivots.pp, "S1 < PP"
        assert pivots.s2 < pivots.s1, "S2 < S1"
        assert pivots.s3 < pivots.s2, "S3 < S2"

        print("✓ Pivot Points calculation correct")
        return True
    except Exception as e:
        print(f"✗ Pivot Points test failed: {e}")
        traceback.print_exc()
        return False


def test_trend_direction():
    """Test trend direction detection"""
    try:
        from technical_indicators import TechnicalIndicators

        # Perfect bullish alignment
        trend = TechnicalIndicators.get_trend_direction(100, 98, 95, 90)
        assert trend == "bullish", "Should detect bullish trend"

        # Perfect bearish alignment
        trend = TechnicalIndicators.get_trend_direction(90, 92, 95, 100)
        assert trend == "bearish", "Should detect bearish trend"

        print("✓ Trend direction detection correct")
        return True
    except Exception as e:
        print(f"✗ Trend direction test failed: {e}")
        traceback.print_exc()
        return False


def test_crossover():
    """Test crossover detection"""
    try:
        from technical_indicators import TechnicalIndicators
        import numpy as np

        # Bullish crossover
        fast = [10, 11, 12, 13, 14, 15]
        slow = [12, 12, 12, 12, 12, 12]

        crossovers = TechnicalIndicators.detect_crossover(fast, slow)
        bullish_crosses = np.where(crossovers == 1)[0]
        assert len(bullish_crosses) > 0, "Should detect bullish crossover"

        print("✓ Crossover detection correct")
        return True
    except Exception as e:
        print(f"✗ Crossover test failed: {e}")
        traceback.print_exc()
        return False


def test_calculate_all():
    """Test calculate_all_indicators"""
    try:
        from technical_indicators import TechnicalIndicators
        import numpy as np

        # Generate sample data
        np.random.seed(42)
        n = 250
        high = np.random.uniform(100, 110, n)
        low = np.random.uniform(90, 100, n)
        close = np.random.uniform(95, 105, n)

        indicators = TechnicalIndicators.calculate_all_indicators(high, low, close)

        # Check all expected keys
        expected_keys = ['ema', 'rsi', 'macd', 'bollinger_bands', 'atr',
                        'ichimoku', 'pivot_points', 'trend', 'alignment', 'crossovers']

        for key in expected_keys:
            assert key in indicators, f"Missing key: {key}"

        # Check trend is valid
        assert indicators['trend'] in ['bullish', 'bearish', 'neutral'], \
            "Invalid trend value"

        print("✓ calculate_all_indicators correct")
        return True
    except Exception as e:
        print(f"✗ calculate_all_indicators test failed: {e}")
        traceback.print_exc()
        return False


def test_input_validation():
    """Test input validation"""
    try:
        from technical_indicators import TechnicalIndicators

        # Empty list
        try:
            TechnicalIndicators.calculate_sma([], 5)
            assert False, "Should raise ValueError for empty list"
        except ValueError:
            pass

        # Insufficient data
        try:
            TechnicalIndicators.calculate_sma([1, 2, 3], 10)
            assert False, "Should raise ValueError for insufficient data"
        except ValueError:
            pass

        # Invalid period
        try:
            TechnicalIndicators.calculate_sma([1, 2, 3, 4, 5], 0)
            assert False, "Should raise ValueError for invalid period"
        except ValueError:
            pass

        print("✓ Input validation correct")
        return True
    except Exception as e:
        print(f"✗ Input validation test failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("="*80)
    print("TECHNICAL INDICATORS - BASIC TESTS")
    print("="*80)
    print()

    tests = [
        ("Module Imports", test_imports),
        ("SMA Calculation", test_sma),
        ("EMA Calculation", test_ema),
        ("RSI Calculation", test_rsi),
        ("MACD Calculation", test_macd),
        ("Bollinger Bands", test_bollinger_bands),
        ("ATR Calculation", test_atr),
        ("Pivot Points", test_pivot_points),
        ("Trend Direction", test_trend_direction),
        ("Crossover Detection", test_crossover),
        ("Calculate All Indicators", test_calculate_all),
        ("Input Validation", test_input_validation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\nTesting: {name}")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            traceback.print_exc()
            failed += 1

    print()
    print("="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)

    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
