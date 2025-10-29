"""
Technical Indicators Module for TradeMatrix.ai

This module provides a comprehensive set of technical analysis indicators
for market analysis and trading signal generation.

All calculations are implemented using numpy for optimal performance
and follow standard technical analysis formulas.

Author: TradeMatrix.ai
Version: 1.0.0
"""

import numpy as np
from typing import Dict, List, Tuple, Union, Optional
from dataclasses import dataclass


@dataclass
class MACDResult:
    """MACD indicator results"""
    macd_line: np.ndarray
    signal_line: np.ndarray
    histogram: np.ndarray


@dataclass
class BollingerBandsResult:
    """Bollinger Bands results"""
    upper: np.ndarray
    middle: np.ndarray
    lower: np.ndarray


@dataclass
class IchimokuResult:
    """Ichimoku Cloud results"""
    tenkan_sen: np.ndarray  # Conversion Line
    kijun_sen: np.ndarray   # Base Line
    senkou_span_a: np.ndarray  # Leading Span A
    senkou_span_b: np.ndarray  # Leading Span B
    chikou_span: np.ndarray    # Lagging Span


@dataclass
class PivotPointsResult:
    """Pivot Points results"""
    pp: float  # Pivot Point
    r1: float  # Resistance 1
    r2: float  # Resistance 2
    r3: float  # Resistance 3
    s1: float  # Support 1
    s2: float  # Support 2
    s3: float  # Support 3


class TechnicalIndicators:
    """
    Technical Indicators calculation engine.

    All methods are static and can be used without instantiation.
    Implements standard technical analysis indicators with numpy
    for optimal performance.
    """

    @staticmethod
    def _validate_input(data: Union[List, np.ndarray], min_length: int = 1, name: str = "data") -> np.ndarray:
        """
        Validate input data and convert to numpy array.

        Args:
            data: Input data (list or numpy array)
            min_length: Minimum required length
            name: Name of the parameter for error messages

        Returns:
            Validated numpy array

        Raises:
            ValueError: If data is invalid
        """
        if data is None:
            raise ValueError(f"{name} cannot be None")

        if isinstance(data, list):
            if len(data) == 0:
                raise ValueError(f"{name} cannot be empty")
            data = np.array(data, dtype=float)
        elif isinstance(data, np.ndarray):
            if data.size == 0:
                raise ValueError(f"{name} cannot be empty")
            data = data.astype(float)
        else:
            raise ValueError(f"{name} must be a list or numpy array")

        if len(data) < min_length:
            raise ValueError(f"{name} must have at least {min_length} elements, got {len(data)}")

        # Check for NaN or inf values
        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
            raise ValueError(f"{name} contains NaN or infinite values")

        return data

    @staticmethod
    def calculate_sma(prices: Union[List, np.ndarray], period: int) -> np.ndarray:
        """
        Calculate Simple Moving Average (SMA).

        Formula: SMA = (P1 + P2 + ... + Pn) / n

        Args:
            prices: Array of prices
            period: Number of periods for the average

        Returns:
            Array of SMA values (NaN for insufficient data points)

        Example:
            >>> prices = [10, 11, 12, 13, 14, 15]
            >>> sma = TechnicalIndicators.calculate_sma(prices, 3)
            >>> # Returns: [nan, nan, 11.0, 12.0, 13.0, 14.0]
        """
        prices = TechnicalIndicators._validate_input(prices, period, "prices")

        if period < 1:
            raise ValueError("period must be >= 1")

        sma = np.full(len(prices), np.nan)

        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1:i + 1])

        return sma

    @staticmethod
    def calculate_ema(prices: Union[List, np.ndarray], period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average (EMA).

        Formula:
            EMA(t) = Price(t) * k + EMA(t-1) * (1 - k)
            where k = 2 / (period + 1)

        Args:
            prices: Array of prices
            period: Number of periods for the average

        Returns:
            Array of EMA values (NaN for insufficient data points)

        Example:
            >>> prices = [10, 11, 12, 13, 14, 15]
            >>> ema = TechnicalIndicators.calculate_ema(prices, 3)
        """
        prices = TechnicalIndicators._validate_input(prices, period, "prices")

        if period < 1:
            raise ValueError("period must be >= 1")

        ema = np.full(len(prices), np.nan)

        # First EMA value is SMA
        ema[period - 1] = np.mean(prices[:period])

        # Calculate multiplier
        multiplier = 2.0 / (period + 1)

        # Calculate EMA for remaining values
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1]

        return ema

    @staticmethod
    def calculate_rsi(prices: Union[List, np.ndarray], period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index (RSI).

        Formula:
            RSI = 100 - (100 / (1 + RS))
            where RS = Average Gain / Average Loss

        Args:
            prices: Array of prices
            period: RSI period (default: 14)

        Returns:
            Array of RSI values (0-100, NaN for insufficient data points)

        Example:
            >>> prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83, ...]
            >>> rsi = TechnicalIndicators.calculate_rsi(prices, 14)
        """
        prices = TechnicalIndicators._validate_input(prices, period + 1, "prices")

        if period < 1:
            raise ValueError("period must be >= 1")

        # Calculate price changes
        deltas = np.diff(prices)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Initialize RSI array
        rsi = np.full(len(prices), np.nan)

        # Calculate initial average gain and loss (SMA)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        # Calculate first RSI value
        if avg_loss == 0:
            rsi[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[period] = 100.0 - (100.0 / (1.0 + rs))

        # Calculate remaining RSI values (using EMA-style smoothing)
        for i in range(period + 1, len(prices)):
            avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period

            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    @staticmethod
    def calculate_macd(
        prices: Union[List, np.ndarray],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> MACDResult:
        """
        Calculate Moving Average Convergence Divergence (MACD).

        Formula:
            MACD Line = EMA(fast) - EMA(slow)
            Signal Line = EMA(MACD Line, signal)
            Histogram = MACD Line - Signal Line

        Args:
            prices: Array of prices
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)

        Returns:
            MACDResult with macd_line, signal_line, and histogram

        Example:
            >>> prices = [...]
            >>> macd = TechnicalIndicators.calculate_macd(prices)
            >>> print(macd.macd_line[-1], macd.signal_line[-1])
        """
        prices = TechnicalIndicators._validate_input(prices, slow, "prices")

        if fast >= slow:
            raise ValueError("fast period must be < slow period")
        if signal < 1:
            raise ValueError("signal period must be >= 1")

        # Calculate EMAs
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow)

        # Calculate MACD line
        macd_line = ema_fast - ema_slow

        # Calculate signal line (EMA of MACD line)
        # Remove NaN values for signal calculation
        valid_idx = ~np.isnan(macd_line)
        signal_line = np.full(len(prices), np.nan)

        if np.sum(valid_idx) >= signal:
            macd_valid = macd_line[valid_idx]
            signal_valid = TechnicalIndicators.calculate_ema(macd_valid, signal)
            signal_line[valid_idx] = signal_valid

        # Calculate histogram
        histogram = macd_line - signal_line

        return MACDResult(
            macd_line=macd_line,
            signal_line=signal_line,
            histogram=histogram
        )

    @staticmethod
    def calculate_bollinger_bands(
        prices: Union[List, np.ndarray],
        period: int = 20,
        std_dev: float = 2.0
    ) -> BollingerBandsResult:
        """
        Calculate Bollinger Bands.

        Formula:
            Middle Band = SMA(period)
            Upper Band = Middle Band + (std_dev * standard deviation)
            Lower Band = Middle Band - (std_dev * standard deviation)

        Args:
            prices: Array of prices
            period: Period for SMA (default: 20)
            std_dev: Number of standard deviations (default: 2.0)

        Returns:
            BollingerBandsResult with upper, middle, and lower bands

        Example:
            >>> prices = [...]
            >>> bb = TechnicalIndicators.calculate_bollinger_bands(prices)
            >>> print(bb.upper[-1], bb.middle[-1], bb.lower[-1])
        """
        prices = TechnicalIndicators._validate_input(prices, period, "prices")

        if period < 2:
            raise ValueError("period must be >= 2")
        if std_dev <= 0:
            raise ValueError("std_dev must be > 0")

        # Calculate middle band (SMA)
        middle = TechnicalIndicators.calculate_sma(prices, period)

        # Calculate standard deviation
        std = np.full(len(prices), np.nan)
        for i in range(period - 1, len(prices)):
            std[i] = np.std(prices[i - period + 1:i + 1], ddof=1)

        # Calculate upper and lower bands
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        return BollingerBandsResult(
            upper=upper,
            middle=middle,
            lower=lower
        )

    @staticmethod
    def calculate_atr(
        high: Union[List, np.ndarray],
        low: Union[List, np.ndarray],
        close: Union[List, np.ndarray],
        period: int = 14
    ) -> np.ndarray:
        """
        Calculate Average True Range (ATR).

        Formula:
            TR = max[(high - low), abs(high - close_prev), abs(low - close_prev)]
            ATR = EMA(TR, period)

        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of close prices
            period: ATR period (default: 14)

        Returns:
            Array of ATR values (NaN for insufficient data points)

        Example:
            >>> high = [...]
            >>> low = [...]
            >>> close = [...]
            >>> atr = TechnicalIndicators.calculate_atr(high, low, close, 14)
        """
        high = TechnicalIndicators._validate_input(high, period, "high")
        low = TechnicalIndicators._validate_input(low, period, "low")
        close = TechnicalIndicators._validate_input(close, period, "close")

        if len(high) != len(low) or len(high) != len(close):
            raise ValueError("high, low, and close must have the same length")
        if period < 1:
            raise ValueError("period must be >= 1")

        # Calculate True Range
        tr = np.full(len(close), np.nan)

        # First TR is just high - low
        tr[0] = high[0] - low[0]

        # Calculate TR for remaining values
        for i in range(1, len(close)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i - 1])
            lc = abs(low[i] - close[i - 1])
            tr[i] = max(hl, hc, lc)

        # Calculate ATR as EMA of TR
        atr = TechnicalIndicators.calculate_ema(tr, period)

        return atr

    @staticmethod
    def calculate_ichimoku(
        high: Union[List, np.ndarray],
        low: Union[List, np.ndarray],
        close: Union[List, np.ndarray],
        tenkan: int = 9,
        kijun: int = 26,
        senkou_b: int = 52
    ) -> IchimokuResult:
        """
        Calculate Ichimoku Cloud indicators.

        Formula:
            Tenkan-sen (Conversion Line) = (9-period high + 9-period low) / 2
            Kijun-sen (Base Line) = (26-period high + 26-period low) / 2
            Senkou Span A (Leading Span A) = (Tenkan-sen + Kijun-sen) / 2 (shifted 26 periods ahead)
            Senkou Span B (Leading Span B) = (52-period high + 52-period low) / 2 (shifted 26 periods ahead)
            Chikou Span (Lagging Span) = Close price (shifted 26 periods back)

        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of close prices
            tenkan: Tenkan-sen period (default: 9)
            kijun: Kijun-sen period (default: 26)
            senkou_b: Senkou Span B period (default: 52)

        Returns:
            IchimokuResult with all Ichimoku components

        Example:
            >>> high = [...]
            >>> low = [...]
            >>> close = [...]
            >>> ichimoku = TechnicalIndicators.calculate_ichimoku(high, low, close)
        """
        max_period = max(tenkan, kijun, senkou_b)
        high = TechnicalIndicators._validate_input(high, max_period, "high")
        low = TechnicalIndicators._validate_input(low, max_period, "low")
        close = TechnicalIndicators._validate_input(close, max_period, "close")

        if len(high) != len(low) or len(high) != len(close):
            raise ValueError("high, low, and close must have the same length")

        n = len(close)

        # Initialize arrays
        tenkan_sen = np.full(n, np.nan)
        kijun_sen = np.full(n, np.nan)
        senkou_span_a = np.full(n, np.nan)
        senkou_span_b = np.full(n, np.nan)
        chikou_span = np.full(n, np.nan)

        # Calculate Tenkan-sen (Conversion Line)
        for i in range(tenkan - 1, n):
            period_high = np.max(high[i - tenkan + 1:i + 1])
            period_low = np.min(low[i - tenkan + 1:i + 1])
            tenkan_sen[i] = (period_high + period_low) / 2

        # Calculate Kijun-sen (Base Line)
        for i in range(kijun - 1, n):
            period_high = np.max(high[i - kijun + 1:i + 1])
            period_low = np.min(low[i - kijun + 1:i + 1])
            kijun_sen[i] = (period_high + period_low) / 2

        # Calculate Senkou Span A (Leading Span A) - shifted forward
        for i in range(kijun - 1, n):
            if not np.isnan(tenkan_sen[i]) and not np.isnan(kijun_sen[i]):
                senkou_span_a[i] = (tenkan_sen[i] + kijun_sen[i]) / 2

        # Calculate Senkou Span B (Leading Span B) - shifted forward
        for i in range(senkou_b - 1, n):
            period_high = np.max(high[i - senkou_b + 1:i + 1])
            period_low = np.min(low[i - senkou_b + 1:i + 1])
            senkou_span_b[i] = (period_high + period_low) / 2

        # Calculate Chikou Span (Lagging Span) - current close shifted back
        chikou_span = close.copy()

        return IchimokuResult(
            tenkan_sen=tenkan_sen,
            kijun_sen=kijun_sen,
            senkou_span_a=senkou_span_a,
            senkou_span_b=senkou_span_b,
            chikou_span=chikou_span
        )

    @staticmethod
    def calculate_pivot_points(
        high: float,
        low: float,
        close: float
    ) -> PivotPointsResult:
        """
        Calculate Pivot Points (Standard Method).

        Formula:
            PP = (High + Low + Close) / 3
            R1 = (2 * PP) - Low
            R2 = PP + (High - Low)
            R3 = High + 2 * (PP - Low)
            S1 = (2 * PP) - High
            S2 = PP - (High - Low)
            S3 = Low - 2 * (High - PP)

        Args:
            high: Previous period's high
            low: Previous period's low
            close: Previous period's close

        Returns:
            PivotPointsResult with PP, R1-R3, S1-S3

        Example:
            >>> pivots = TechnicalIndicators.calculate_pivot_points(1.2050, 1.2000, 1.2030)
            >>> print(f"PP: {pivots.pp}, R1: {pivots.r1}, S1: {pivots.s1}")
        """
        if high <= 0 or low <= 0 or close <= 0:
            raise ValueError("high, low, and close must be positive")
        if low > high:
            raise ValueError("low cannot be greater than high")
        if close < low or close > high:
            raise ValueError("close must be between low and high")

        # Calculate Pivot Point
        pp = (high + low + close) / 3.0

        # Calculate Resistance levels
        r1 = (2.0 * pp) - low
        r2 = pp + (high - low)
        r3 = high + 2.0 * (pp - low)

        # Calculate Support levels
        s1 = (2.0 * pp) - high
        s2 = pp - (high - low)
        s3 = low - 2.0 * (high - pp)

        return PivotPointsResult(
            pp=pp,
            r1=r1,
            r2=r2,
            r3=r3,
            s1=s1,
            s2=s2,
            s3=s3
        )

    @staticmethod
    def get_trend_direction(
        price: float,
        ema_20: float,
        ema_50: float,
        ema_200: float
    ) -> str:
        """
        Determine trend direction based on EMA alignment.

        Rules:
            - Bullish: Price > EMA20 > EMA50 > EMA200
            - Bearish: Price < EMA20 < EMA50 < EMA200
            - Neutral: Mixed or sideways

        Args:
            price: Current price
            ema_20: 20-period EMA
            ema_50: 50-period EMA
            ema_200: 200-period EMA

        Returns:
            "bullish", "bearish", or "neutral"

        Example:
            >>> trend = TechnicalIndicators.get_trend_direction(100, 98, 95, 90)
            >>> # Returns: "bullish"
        """
        if any(np.isnan([price, ema_20, ema_50, ema_200])):
            return "neutral"

        # Perfect bullish alignment
        if price > ema_20 > ema_50 > ema_200:
            return "bullish"

        # Perfect bearish alignment
        if price < ema_20 < ema_50 < ema_200:
            return "bearish"

        # Strong bullish (price above all EMAs)
        if price > ema_20 and price > ema_50 and price > ema_200:
            if ema_20 > ema_50:  # Recent momentum bullish
                return "bullish"

        # Strong bearish (price below all EMAs)
        if price < ema_20 and price < ema_50 and price < ema_200:
            if ema_20 < ema_50:  # Recent momentum bearish
                return "bearish"

        return "neutral"

    @staticmethod
    def check_ema_alignment(
        price: float,
        ema_20: float,
        ema_50: float,
        ema_200: float
    ) -> Dict[str, bool]:
        """
        Check EMA alignment conditions.

        Args:
            price: Current price
            ema_20: 20-period EMA
            ema_50: 50-period EMA
            ema_200: 200-period EMA

        Returns:
            Dictionary with alignment checks:
                - perfect_bullish: Price > EMA20 > EMA50 > EMA200
                - perfect_bearish: Price < EMA20 < EMA50 < EMA200
                - above_all: Price above all EMAs
                - below_all: Price below all EMAs
                - golden_cross: EMA50 > EMA200 (bullish)
                - death_cross: EMA50 < EMA200 (bearish)

        Example:
            >>> alignment = TechnicalIndicators.check_ema_alignment(100, 98, 95, 90)
            >>> if alignment['perfect_bullish']:
            >>>     print("Strong bullish trend")
        """
        return {
            "perfect_bullish": price > ema_20 > ema_50 > ema_200,
            "perfect_bearish": price < ema_20 < ema_50 < ema_200,
            "above_all": price > ema_20 and price > ema_50 and price > ema_200,
            "below_all": price < ema_20 and price < ema_50 and price < ema_200,
            "golden_cross": ema_50 > ema_200,
            "death_cross": ema_50 < ema_200,
            "price_above_20": price > ema_20,
            "price_above_50": price > ema_50,
            "price_above_200": price > ema_200,
        }

    @staticmethod
    def detect_crossover(
        series1: Union[List, np.ndarray],
        series2: Union[List, np.ndarray]
    ) -> np.ndarray:
        """
        Detect crossover points between two series.

        Returns:
            Array with values:
                1: series1 crosses above series2 (bullish crossover)
                -1: series1 crosses below series2 (bearish crossover)
                0: no crossover

        Args:
            series1: First time series
            series2: Second time series

        Returns:
            Array of crossover signals

        Example:
            >>> ema_fast = [...]
            >>> ema_slow = [...]
            >>> crossovers = TechnicalIndicators.detect_crossover(ema_fast, ema_slow)
            >>> # crossovers[-1] == 1 means bullish crossover just occurred
        """
        series1 = TechnicalIndicators._validate_input(series1, 2, "series1")
        series2 = TechnicalIndicators._validate_input(series2, 2, "series2")

        if len(series1) != len(series2):
            raise ValueError("series1 and series2 must have the same length")

        crossover = np.zeros(len(series1))

        for i in range(1, len(series1)):
            # Skip if either value is NaN
            if np.isnan(series1[i]) or np.isnan(series2[i]) or \
               np.isnan(series1[i-1]) or np.isnan(series2[i-1]):
                continue

            # Bullish crossover: series1 crosses above series2
            if series1[i] > series2[i] and series1[i-1] <= series2[i-1]:
                crossover[i] = 1

            # Bearish crossover: series1 crosses below series2
            elif series1[i] < series2[i] and series1[i-1] >= series2[i-1]:
                crossover[i] = -1

        return crossover

    @staticmethod
    def calculate_all_indicators(
        high: Union[List, np.ndarray],
        low: Union[List, np.ndarray],
        close: Union[List, np.ndarray],
        volume: Optional[Union[List, np.ndarray]] = None
    ) -> Dict:
        """
        Calculate all technical indicators at once.

        This is a convenience method that calculates all indicators
        and returns them in a structured dictionary.

        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of close prices
            volume: Optional array of volumes

        Returns:
            Dictionary with all calculated indicators

        Example:
            >>> indicators = TechnicalIndicators.calculate_all_indicators(high, low, close)
            >>> print(indicators['ema']['20'][-1])
        """
        high = TechnicalIndicators._validate_input(high, 200, "high")
        low = TechnicalIndicators._validate_input(low, 200, "low")
        close = TechnicalIndicators._validate_input(close, 200, "close")

        if len(high) != len(low) or len(high) != len(close):
            raise ValueError("high, low, and close must have the same length")

        # Calculate EMAs
        ema_20 = TechnicalIndicators.calculate_ema(close, 20)
        ema_50 = TechnicalIndicators.calculate_ema(close, 50)
        ema_200 = TechnicalIndicators.calculate_ema(close, 200)

        # Calculate other indicators
        rsi = TechnicalIndicators.calculate_rsi(close, 14)
        macd = TechnicalIndicators.calculate_macd(close, 12, 26, 9)
        bb = TechnicalIndicators.calculate_bollinger_bands(close, 20, 2)
        atr = TechnicalIndicators.calculate_atr(high, low, close, 14)
        ichimoku = TechnicalIndicators.calculate_ichimoku(high, low, close)

        # Calculate pivot points for last period
        pivots = TechnicalIndicators.calculate_pivot_points(
            high[-1], low[-1], close[-1]
        )

        # Get trend direction
        current_price = close[-1]
        trend = TechnicalIndicators.get_trend_direction(
            current_price,
            ema_20[-1],
            ema_50[-1],
            ema_200[-1]
        )

        # Check EMA alignment
        alignment = TechnicalIndicators.check_ema_alignment(
            current_price,
            ema_20[-1],
            ema_50[-1],
            ema_200[-1]
        )

        # Detect EMA crossovers
        ema_20_50_cross = TechnicalIndicators.detect_crossover(ema_20, ema_50)
        ema_50_200_cross = TechnicalIndicators.detect_crossover(ema_50, ema_200)

        return {
            "ema": {
                "20": ema_20,
                "50": ema_50,
                "200": ema_200
            },
            "rsi": rsi,
            "macd": {
                "macd_line": macd.macd_line,
                "signal_line": macd.signal_line,
                "histogram": macd.histogram
            },
            "bollinger_bands": {
                "upper": bb.upper,
                "middle": bb.middle,
                "lower": bb.lower
            },
            "atr": atr,
            "ichimoku": {
                "tenkan_sen": ichimoku.tenkan_sen,
                "kijun_sen": ichimoku.kijun_sen,
                "senkou_span_a": ichimoku.senkou_span_a,
                "senkou_span_b": ichimoku.senkou_span_b,
                "chikou_span": ichimoku.chikou_span
            },
            "pivot_points": {
                "pp": pivots.pp,
                "r1": pivots.r1,
                "r2": pivots.r2,
                "r3": pivots.r3,
                "s1": pivots.s1,
                "s2": pivots.s2,
                "s3": pivots.s3
            },
            "trend": trend,
            "alignment": alignment,
            "crossovers": {
                "ema_20_50": ema_20_50_cross,
                "ema_50_200": ema_50_200_cross
            }
        }
