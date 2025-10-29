"""
Tests for Technical Indicators Module

Comprehensive test suite for all technical analysis indicators.
Tests include:
- Calculation accuracy
- Edge cases
- Input validation
- Performance benchmarks

Author: TradeMatrix.ai
Version: 1.0.0
"""

import numpy as np
import pytest
from typing import List

from technical_indicators import (
    TechnicalIndicators,
    MACDResult,
    BollingerBandsResult,
    IchimokuResult,
    PivotPointsResult
)


class TestInputValidation:
    """Test input validation for all methods"""

    def test_validate_empty_list(self):
        """Test that empty lists raise ValueError"""
        with pytest.raises(ValueError, match="cannot be empty"):
            TechnicalIndicators.calculate_sma([], 5)

    def test_validate_none_input(self):
        """Test that None input raises ValueError"""
        with pytest.raises(ValueError, match="cannot be None"):
            TechnicalIndicators.calculate_sma(None, 5)

    def test_validate_insufficient_data(self):
        """Test that insufficient data raises ValueError"""
        with pytest.raises(ValueError, match="must have at least"):
            TechnicalIndicators.calculate_sma([1, 2, 3], 10)

    def test_validate_nan_values(self):
        """Test that NaN values raise ValueError"""
        with pytest.raises(ValueError, match="contains NaN"):
            TechnicalIndicators.calculate_sma([1, 2, np.nan, 4], 3)

    def test_validate_inf_values(self):
        """Test that infinite values raise ValueError"""
        with pytest.raises(ValueError, match="infinite values"):
            TechnicalIndicators.calculate_sma([1, 2, np.inf, 4], 3)

    def test_validate_invalid_period(self):
        """Test that invalid periods raise ValueError"""
        with pytest.raises(ValueError, match="must be >= 1"):
            TechnicalIndicators.calculate_sma([1, 2, 3, 4, 5], 0)


class TestSMA:
    """Test Simple Moving Average calculations"""

    def test_sma_basic_calculation(self):
        """Test basic SMA calculation"""
        prices = [10, 11, 12, 13, 14, 15]
        sma = TechnicalIndicators.calculate_sma(prices, 3)

        # First two values should be NaN
        assert np.isnan(sma[0])
        assert np.isnan(sma[1])

        # Check calculated values
        assert sma[2] == pytest.approx(11.0)  # (10+11+12)/3
        assert sma[3] == pytest.approx(12.0)  # (11+12+13)/3
        assert sma[4] == pytest.approx(13.0)  # (12+13+14)/3
        assert sma[5] == pytest.approx(14.0)  # (13+14+15)/3

    def test_sma_period_one(self):
        """Test SMA with period 1 (should equal input)"""
        prices = [10, 11, 12, 13, 14]
        sma = TechnicalIndicators.calculate_sma(prices, 1)

        assert np.array_equal(sma, prices)

    def test_sma_numpy_input(self):
        """Test SMA with numpy array input"""
        prices = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        sma = TechnicalIndicators.calculate_sma(prices, 3)

        assert sma[2] == pytest.approx(11.0)


class TestEMA:
    """Test Exponential Moving Average calculations"""

    def test_ema_basic_calculation(self):
        """Test basic EMA calculation"""
        prices = [22.27, 22.19, 22.08, 22.17, 22.18, 22.13, 22.23, 22.43, 22.24, 22.29,
                  22.15, 22.39, 22.38, 22.61, 23.36, 24.05, 23.75, 23.83, 23.95, 23.63]
        ema = TechnicalIndicators.calculate_ema(prices, 10)

        # First 9 values should be NaN
        assert all(np.isnan(ema[:9]))

        # 10th value should be SMA
        assert ema[9] == pytest.approx(np.mean(prices[:10]), rel=1e-2)

        # Later values should be calculated (not exact due to floating point)
        assert not np.isnan(ema[-1])

    def test_ema_vs_sma_convergence(self):
        """Test that EMA converges to SMA over time for constant prices"""
        prices = [100.0] * 50
        ema = TechnicalIndicators.calculate_ema(prices, 10)
        sma = TechnicalIndicators.calculate_sma(prices, 10)

        # For constant prices, EMA should quickly converge to SMA
        assert ema[-1] == pytest.approx(100.0)
        assert sma[-1] == pytest.approx(100.0)


class TestRSI:
    """Test Relative Strength Index calculations"""

    def test_rsi_basic_calculation(self):
        """Test basic RSI calculation"""
        # Sample data from standard RSI example
        prices = [44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84,
                  46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03,
                  46.41, 46.22, 45.64, 46.21]

        rsi = TechnicalIndicators.calculate_rsi(prices, 14)

        # First 14 values should be NaN
        assert all(np.isnan(rsi[:14]))

        # RSI should be between 0 and 100
        valid_rsi = rsi[~np.isnan(rsi)]
        assert all(0 <= r <= 100 for r in valid_rsi)

    def test_rsi_overbought_oversold(self):
        """Test RSI overbought/oversold conditions"""
        # Strong uptrend should give high RSI
        uptrend = list(range(100, 150))
        rsi_up = TechnicalIndicators.calculate_rsi(uptrend, 14)
        assert rsi_up[-1] > 70  # Overbought

        # Strong downtrend should give low RSI
        downtrend = list(range(150, 100, -1))
        rsi_down = TechnicalIndicators.calculate_rsi(downtrend, 14)
        assert rsi_down[-1] < 30  # Oversold

    def test_rsi_range(self):
        """Test that RSI stays within 0-100 range"""
        np.random.seed(42)
        prices = np.random.uniform(90, 110, 100)

        rsi = TechnicalIndicators.calculate_rsi(prices, 14)

        valid_rsi = rsi[~np.isnan(rsi)]
        assert all(0 <= r <= 100 for r in valid_rsi)


class TestMACD:
    """Test MACD calculations"""

    def test_macd_basic_calculation(self):
        """Test basic MACD calculation"""
        # Generate sample data
        prices = list(range(100, 150)) + list(range(150, 120, -1))
        macd_result = TechnicalIndicators.calculate_macd(prices, 12, 26, 9)

        assert isinstance(macd_result, MACDResult)
        assert len(macd_result.macd_line) == len(prices)
        assert len(macd_result.signal_line) == len(prices)
        assert len(macd_result.histogram) == len(prices)

    def test_macd_uptrend(self):
        """Test MACD in uptrend"""
        prices = list(range(100, 200))
        macd_result = TechnicalIndicators.calculate_macd(prices, 12, 26, 9)

        # In strong uptrend, MACD should be positive
        valid_macd = macd_result.macd_line[~np.isnan(macd_result.macd_line)]
        assert valid_macd[-1] > 0

    def test_macd_downtrend(self):
        """Test MACD in downtrend"""
        prices = list(range(200, 100, -1))
        macd_result = TechnicalIndicators.calculate_macd(prices, 12, 26, 9)

        # In strong downtrend, MACD should be negative
        valid_macd = macd_result.macd_line[~np.isnan(macd_result.macd_line)]
        assert valid_macd[-1] < 0

    def test_macd_histogram(self):
        """Test MACD histogram calculation"""
        prices = list(range(100, 150))
        macd_result = TechnicalIndicators.calculate_macd(prices, 12, 26, 9)

        # Histogram should equal MACD line - signal line
        valid_idx = ~np.isnan(macd_result.histogram)
        histogram_check = (macd_result.macd_line[valid_idx] -
                          macd_result.signal_line[valid_idx])

        np.testing.assert_array_almost_equal(
            macd_result.histogram[valid_idx],
            histogram_check,
            decimal=10
        )


class TestBollingerBands:
    """Test Bollinger Bands calculations"""

    def test_bb_basic_calculation(self):
        """Test basic Bollinger Bands calculation"""
        prices = [100 + i + np.sin(i/5) * 10 for i in range(50)]
        bb = TechnicalIndicators.calculate_bollinger_bands(prices, 20, 2)

        assert isinstance(bb, BollingerBandsResult)
        assert len(bb.upper) == len(prices)
        assert len(bb.middle) == len(prices)
        assert len(bb.lower) == len(prices)

    def test_bb_bands_order(self):
        """Test that upper > middle > lower"""
        prices = [100 + i for i in range(50)]
        bb = TechnicalIndicators.calculate_bollinger_bands(prices, 20, 2)

        # Check valid values only
        valid_idx = ~np.isnan(bb.middle)
        assert all(bb.upper[valid_idx] > bb.middle[valid_idx])
        assert all(bb.middle[valid_idx] > bb.lower[valid_idx])

    def test_bb_middle_equals_sma(self):
        """Test that middle band equals SMA"""
        prices = [100 + i for i in range(50)]
        bb = TechnicalIndicators.calculate_bollinger_bands(prices, 20, 2)
        sma = TechnicalIndicators.calculate_sma(prices, 20)

        np.testing.assert_array_almost_equal(bb.middle, sma, decimal=10)

    def test_bb_low_volatility(self):
        """Test Bollinger Bands with low volatility"""
        # Constant prices = low volatility = narrow bands
        prices = [100.0] * 50
        bb = TechnicalIndicators.calculate_bollinger_bands(prices, 20, 2)

        # Bands should be very close together
        valid_idx = ~np.isnan(bb.middle)
        band_width = bb.upper[valid_idx] - bb.lower[valid_idx]
        assert all(band_width < 1.0)  # Very narrow


class TestATR:
    """Test Average True Range calculations"""

    def test_atr_basic_calculation(self):
        """Test basic ATR calculation"""
        high = [110, 112, 111, 113, 115]
        low = [105, 107, 106, 108, 110]
        close = [108, 110, 109, 112, 113]

        atr = TechnicalIndicators.calculate_atr(high, low, close, 3)

        # Should have same length as input
        assert len(atr) == len(high)

        # ATR should be positive
        valid_atr = atr[~np.isnan(atr)]
        assert all(a > 0 for a in valid_atr)

    def test_atr_increasing_volatility(self):
        """Test ATR increases with volatility"""
        # Low volatility
        high_low = [101, 102, 101, 102, 101] * 10
        low_low = [99, 98, 99, 98, 99] * 10
        close_low = [100, 100, 100, 100, 100] * 10

        atr_low = TechnicalIndicators.calculate_atr(high_low, low_low, close_low, 14)

        # High volatility
        high_high = [110, 120, 110, 120, 110] * 10
        low_high = [90, 80, 90, 80, 90] * 10
        close_high = [100, 100, 100, 100, 100] * 10

        atr_high = TechnicalIndicators.calculate_atr(high_high, low_high, close_high, 14)

        # High volatility ATR should be greater
        assert atr_high[-1] > atr_low[-1]

    def test_atr_mismatched_lengths(self):
        """Test that mismatched array lengths raise error"""
        high = [110, 112, 111]
        low = [105, 107]
        close = [108, 110, 109]

        with pytest.raises(ValueError, match="same length"):
            TechnicalIndicators.calculate_atr(high, low, close, 2)


class TestIchimoku:
    """Test Ichimoku Cloud calculations"""

    def test_ichimoku_basic_calculation(self):
        """Test basic Ichimoku calculation"""
        high = list(range(110, 210))
        low = list(range(90, 190))
        close = list(range(100, 200))

        ichimoku = TechnicalIndicators.calculate_ichimoku(high, low, close)

        assert isinstance(ichimoku, IchimokuResult)
        assert len(ichimoku.tenkan_sen) == len(close)
        assert len(ichimoku.kijun_sen) == len(close)
        assert len(ichimoku.senkou_span_a) == len(close)
        assert len(ichimoku.senkou_span_b) == len(close)
        assert len(ichimoku.chikou_span) == len(close)

    def test_ichimoku_chikou_equals_close(self):
        """Test that Chikou span equals close"""
        high = list(range(110, 160))
        low = list(range(90, 140))
        close = list(range(100, 150))

        ichimoku = TechnicalIndicators.calculate_ichimoku(high, low, close)

        np.testing.assert_array_equal(ichimoku.chikou_span, close)


class TestPivotPoints:
    """Test Pivot Points calculations"""

    def test_pivot_basic_calculation(self):
        """Test basic pivot point calculation"""
        high = 1.2050
        low = 1.2000
        close = 1.2030

        pivots = TechnicalIndicators.calculate_pivot_points(high, low, close)

        assert isinstance(pivots, PivotPointsResult)

        # Check PP calculation
        expected_pp = (high + low + close) / 3
        assert pivots.pp == pytest.approx(expected_pp)

        # Check resistance levels are above PP
        assert pivots.r1 > pivots.pp
        assert pivots.r2 > pivots.r1
        assert pivots.r3 > pivots.r2

        # Check support levels are below PP
        assert pivots.s1 < pivots.pp
        assert pivots.s2 < pivots.s1
        assert pivots.s3 < pivots.s2

    def test_pivot_manual_calculation(self):
        """Test pivot calculation with known values"""
        high = 100.0
        low = 90.0
        close = 95.0

        pivots = TechnicalIndicators.calculate_pivot_points(high, low, close)

        # Manual calculations
        pp = (100 + 90 + 95) / 3  # 95
        r1 = (2 * pp) - low  # 100
        s1 = (2 * pp) - high  # 90

        assert pivots.pp == pytest.approx(pp)
        assert pivots.r1 == pytest.approx(r1)
        assert pivots.s1 == pytest.approx(s1)

    def test_pivot_invalid_inputs(self):
        """Test pivot points with invalid inputs"""
        # Low > High
        with pytest.raises(ValueError, match="low cannot be greater than high"):
            TechnicalIndicators.calculate_pivot_points(100, 110, 105)

        # Close outside range
        with pytest.raises(ValueError, match="must be between low and high"):
            TechnicalIndicators.calculate_pivot_points(100, 90, 110)


class TestTrendDirection:
    """Test trend direction detection"""

    def test_trend_perfect_bullish(self):
        """Test perfect bullish trend"""
        trend = TechnicalIndicators.get_trend_direction(
            price=100,
            ema_20=98,
            ema_50=95,
            ema_200=90
        )
        assert trend == "bullish"

    def test_trend_perfect_bearish(self):
        """Test perfect bearish trend"""
        trend = TechnicalIndicators.get_trend_direction(
            price=90,
            ema_20=92,
            ema_50=95,
            ema_200=100
        )
        assert trend == "bearish"

    def test_trend_neutral(self):
        """Test neutral trend"""
        trend = TechnicalIndicators.get_trend_direction(
            price=95,
            ema_20=98,
            ema_50=93,
            ema_200=96
        )
        assert trend == "neutral"

    def test_trend_with_nan(self):
        """Test trend with NaN values"""
        trend = TechnicalIndicators.get_trend_direction(
            price=100,
            ema_20=np.nan,
            ema_50=95,
            ema_200=90
        )
        assert trend == "neutral"


class TestEMAAlignment:
    """Test EMA alignment checks"""

    def test_alignment_perfect_bullish(self):
        """Test perfect bullish alignment"""
        alignment = TechnicalIndicators.check_ema_alignment(
            price=100,
            ema_20=98,
            ema_50=95,
            ema_200=90
        )

        assert alignment["perfect_bullish"] is True
        assert alignment["perfect_bearish"] is False
        assert alignment["above_all"] is True
        assert alignment["below_all"] is False
        assert alignment["golden_cross"] is True

    def test_alignment_perfect_bearish(self):
        """Test perfect bearish alignment"""
        alignment = TechnicalIndicators.check_ema_alignment(
            price=90,
            ema_20=92,
            ema_50=95,
            ema_200=100
        )

        assert alignment["perfect_bullish"] is False
        assert alignment["perfect_bearish"] is True
        assert alignment["above_all"] is False
        assert alignment["below_all"] is True
        assert alignment["death_cross"] is True

    def test_alignment_mixed(self):
        """Test mixed alignment"""
        alignment = TechnicalIndicators.check_ema_alignment(
            price=95,
            ema_20=98,
            ema_50=93,
            ema_200=96
        )

        assert alignment["perfect_bullish"] is False
        assert alignment["perfect_bearish"] is False


class TestCrossover:
    """Test crossover detection"""

    def test_crossover_bullish(self):
        """Test bullish crossover detection"""
        fast = [10, 11, 12, 13, 14, 15]
        slow = [12, 12, 12, 12, 12, 12]

        crossovers = TechnicalIndicators.detect_crossover(fast, slow)

        # Should detect bullish crossover when fast crosses above slow
        bullish_crosses = np.where(crossovers == 1)[0]
        assert len(bullish_crosses) > 0

    def test_crossover_bearish(self):
        """Test bearish crossover detection"""
        fast = [15, 14, 13, 12, 11, 10]
        slow = [12, 12, 12, 12, 12, 12]

        crossovers = TechnicalIndicators.detect_crossover(fast, slow)

        # Should detect bearish crossover when fast crosses below slow
        bearish_crosses = np.where(crossovers == -1)[0]
        assert len(bearish_crosses) > 0

    def test_crossover_no_cross(self):
        """Test no crossover"""
        fast = [15, 15, 15, 15, 15]
        slow = [10, 10, 10, 10, 10]

        crossovers = TechnicalIndicators.detect_crossover(fast, slow)

        # Should have no crossovers
        assert all(crossovers == 0)

    def test_crossover_mismatched_lengths(self):
        """Test crossover with mismatched lengths"""
        fast = [10, 11, 12]
        slow = [12, 12]

        with pytest.raises(ValueError, match="same length"):
            TechnicalIndicators.detect_crossover(fast, slow)


class TestCalculateAllIndicators:
    """Test the convenience method that calculates all indicators"""

    def test_calculate_all_basic(self):
        """Test calculating all indicators at once"""
        np.random.seed(42)
        high = np.random.uniform(100, 110, 250)
        low = np.random.uniform(90, 100, 250)
        close = np.random.uniform(95, 105, 250)

        indicators = TechnicalIndicators.calculate_all_indicators(high, low, close)

        # Check all expected keys are present
        assert "ema" in indicators
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "bollinger_bands" in indicators
        assert "atr" in indicators
        assert "ichimoku" in indicators
        assert "pivot_points" in indicators
        assert "trend" in indicators
        assert "alignment" in indicators
        assert "crossovers" in indicators

        # Check EMA values
        assert "20" in indicators["ema"]
        assert "50" in indicators["ema"]
        assert "200" in indicators["ema"]

        # Check trend is valid
        assert indicators["trend"] in ["bullish", "bearish", "neutral"]

    def test_calculate_all_insufficient_data(self):
        """Test that insufficient data raises error"""
        high = [110, 112]
        low = [90, 92]
        close = [100, 102]

        with pytest.raises(ValueError, match="must have at least"):
            TechnicalIndicators.calculate_all_indicators(high, low, close)


class TestPerformance:
    """Test performance benchmarks"""

    def test_large_dataset_performance(self):
        """Test performance with large dataset"""
        import time

        # Generate large dataset (10 years of 5-minute bars)
        n = 100000
        np.random.seed(42)
        high = np.random.uniform(100, 110, n)
        low = np.random.uniform(90, 100, n)
        close = np.random.uniform(95, 105, n)

        start = time.time()
        indicators = TechnicalIndicators.calculate_all_indicators(high, low, close)
        elapsed = time.time() - start

        print(f"\nCalculated all indicators for {n} bars in {elapsed:.2f} seconds")

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0

        # Verify results are valid
        assert not np.all(np.isnan(indicators["ema"]["20"]))


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_single_value_change(self):
        """Test indicators with single value change"""
        prices = [100] * 50
        prices[25] = 105  # Single spike

        ema = TechnicalIndicators.calculate_ema(prices, 20)
        assert not np.all(np.isnan(ema))

    def test_extreme_volatility(self):
        """Test indicators with extreme volatility"""
        prices = []
        for i in range(100):
            prices.append(100 if i % 2 == 0 else 200)

        rsi = TechnicalIndicators.calculate_rsi(prices, 14)
        valid_rsi = rsi[~np.isnan(rsi)]
        assert all(0 <= r <= 100 for r in valid_rsi)

    def test_gradual_trend(self):
        """Test indicators with gradual trend"""
        prices = [100 + i * 0.1 for i in range(200)]

        indicators = TechnicalIndicators.calculate_all_indicators(
            prices, prices, prices
        )

        # Should detect bullish trend
        assert indicators["trend"] in ["bullish", "neutral"]


if __name__ == "__main__":
    """Run tests with pytest"""
    print("Running Technical Indicators Tests...")
    print("=" * 80)

    # Run with pytest if available
    try:
        import pytest
        pytest.main([__file__, "-v", "--tb=short"])
    except ImportError:
        print("pytest not installed. Install with: pip install pytest")
        print("\nRunning basic tests without pytest...")

        # Run basic tests manually
        test_classes = [
            TestSMA,
            TestEMA,
            TestRSI,
            TestMACD,
            TestBollingerBands,
            TestATR,
            TestPivotPoints,
            TestTrendDirection,
            TestCrossover
        ]

        for test_class in test_classes:
            print(f"\nRunning {test_class.__name__}...")
            instance = test_class()
            methods = [m for m in dir(instance) if m.startswith("test_")]
            for method_name in methods:
                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"  ✓ {method_name}")
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
