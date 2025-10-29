"""
TradeMatrix.ai - Validation Engine
===================================

Validates trade signals using multi-metric confidence scoring system.

This module implements the core validation logic for all trade setups,
calculating confidence scores based on weighted metrics and applying
priority override logic for high-probability reversal patterns.

Metrics Weighting:
- EMA Alignment: 0.25
- Pivot Confluence: 0.20
- Volume Confirmation: 0.20
- Candle Structure: 0.20
- Context Flow: 0.15

Confidence threshold: > 0.8 = High-Probability Trade
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class StrategyType(Enum):
    """Trading strategy types (MR-Series)"""
    MR_01 = "MR-01"  # EMA-Cross Reversal
    MR_02 = "MR-02"  # Pivot Rebound
    MR_03 = "MR-03"  # Gap-Open Play
    MR_04 = "MR-04"  # Vortagstief-Reversal (Priority Override)
    MR_05 = "MR-05"  # End-of-Month Rotation
    MR_06 = "MR-06"  # Yesterday Range Reversion (Priority Override)


@dataclass
class ValidationResult:
    """Result of signal validation"""
    confidence: float
    is_valid: bool
    breakdown: Dict[str, float]
    priority_override: bool
    notes: Optional[str] = None


class ValidationEngine:
    """
    Core validation engine for trade signal analysis.

    Implements weighted multi-metric scoring system to determine
    trade signal validity and confidence levels.

    Attributes:
        WEIGHTS (Dict[str, float]): Metric weights for confidence calculation
        HIGH_CONFIDENCE_THRESHOLD (float): Minimum confidence for valid signal (0.8)
        PRIORITY_STRATEGIES (set): Strategies that override pullback setups

    Example:
        >>> engine = ValidationEngine()
        >>> signal_data = {
        ...     'price': 18500.0,
        ...     'emas': {'20': 18450.0, '50': 18400.0, '200': 18300.0},
        ...     'levels': {'pivot': 18480.0, 'r1': 18550.0, 's1': 18410.0},
        ...     'volume': 15000,
        ...     'avg_volume': 10000,
        ...     'candle': {'open': 18490.0, 'high': 18510.0, 'low': 18485.0, 'close': 18505.0},
        ...     'context': {'trend': 'bullish', 'volatility': 0.15},
        ...     'strategy': 'MR-02'
        ... }
        >>> result = engine.validate_signal(signal_data)
        >>> print(f"Confidence: {result.confidence:.2f}, Valid: {result.is_valid}")
    """

    # Metric weights (sum = 1.0)
    WEIGHTS = {
        'ema_alignment': 0.25,
        'pivot_confluence': 0.20,
        'volume_confirmation': 0.20,
        'candle_structure': 0.20,
        'context_flow': 0.15
    }

    # Confidence threshold
    HIGH_CONFIDENCE_THRESHOLD = 0.8

    # Priority strategies that override MR-02 (Pivot Pullback)
    PRIORITY_STRATEGIES = {StrategyType.MR_04.value, StrategyType.MR_06.value}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the validation engine.

        Args:
            config: Optional configuration dictionary for custom thresholds
                   and weights. If not provided, uses default values.

        Example:
            >>> engine = ValidationEngine()
            >>> # With custom config:
            >>> engine = ValidationEngine({'threshold': 0.75})
        """
        self.config = config or {}
        self.threshold = self.config.get('threshold', self.HIGH_CONFIDENCE_THRESHOLD)

        # Allow custom weights if provided
        self.weights = self.config.get('weights', self.WEIGHTS.copy())

        # Validate weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    def calculate_confidence(self, signal_data: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score from weighted metrics.

        Args:
            signal_data: Dictionary containing all signal information

        Returns:
            Float confidence score between 0.0 and 1.0

        Example:
            >>> confidence = engine.calculate_confidence(signal_data)
            >>> print(f"Confidence: {confidence:.2%}")
        """
        # Extract EMA data
        emas = signal_data.get('emas', {})
        prices = {
            'current': signal_data.get('price', 0.0),
            '20': emas.get('20', 0.0),
            '50': emas.get('50', 0.0),
            '200': emas.get('200', 0.0)
        }

        # Extract level data
        levels = signal_data.get('levels', {})

        # Extract volume data
        current_volume = signal_data.get('volume', 0.0)
        avg_volume = signal_data.get('avg_volume', 1.0)  # Avoid division by zero

        # Extract candle data
        candle = signal_data.get('candle', {})

        # Extract context data
        context = signal_data.get('context', {})

        # Calculate individual metric scores
        ema_score = self.check_ema_alignment(
            prices['current'],
            prices['20'],
            prices['50'],
            prices['200']
        )

        pivot_score = self.check_pivot_confluence(
            prices['current'],
            levels
        )

        volume_score = self.check_volume_confirmation(
            current_volume,
            avg_volume
        )

        candle_score = self.check_candle_structure(candle)

        context_score = self.check_context_flow(context)

        # Calculate weighted confidence
        confidence = (
            ema_score * self.weights['ema_alignment'] +
            pivot_score * self.weights['pivot_confluence'] +
            volume_score * self.weights['volume_confirmation'] +
            candle_score * self.weights['candle_structure'] +
            context_score * self.weights['context_flow']
        )

        return min(max(confidence, 0.0), 1.0)  # Clamp between 0.0 and 1.0

    def validate_signal(self, signal_data: Dict[str, Any]) -> ValidationResult:
        """
        Perform full validation of a trade signal.

        Calculates confidence score, applies priority override logic,
        and returns comprehensive validation result.

        Args:
            signal_data: Complete signal data including:
                - price (float): Current price
                - emas (dict): EMA values {'20': float, '50': float, '200': float}
                - levels (dict): Pivot levels {'pivot': float, 'r1': float, 's1': float}
                - volume (float): Current volume
                - avg_volume (float): Average volume
                - candle (dict): OHLC data {'open', 'high', 'low', 'close'}
                - context (dict): Market context {'trend': str, 'volatility': float}
                - strategy (str): Strategy type (MR-01 to MR-06)

        Returns:
            ValidationResult containing:
                - confidence: Overall confidence score (0.0-1.0)
                - is_valid: Whether signal passes threshold
                - breakdown: Individual metric scores
                - priority_override: Whether strategy has priority override
                - notes: Additional validation notes

        Example:
            >>> result = engine.validate_signal(signal_data)
            >>> if result.is_valid:
            ...     print(f"Valid signal with {result.confidence:.2%} confidence")
            >>> print(f"EMA Alignment: {result.breakdown['ema_alignment']:.2f}")
        """
        # Get strategy type
        strategy = signal_data.get('strategy', '')
        priority_override = strategy in self.PRIORITY_STRATEGIES

        # Extract data for individual metric calculations
        emas = signal_data.get('emas', {})
        prices = {
            'current': signal_data.get('price', 0.0),
            '20': emas.get('20', 0.0),
            '50': emas.get('50', 0.0),
            '200': emas.get('200', 0.0)
        }
        levels = signal_data.get('levels', {})
        current_volume = signal_data.get('volume', 0.0)
        avg_volume = signal_data.get('avg_volume', 1.0)
        candle = signal_data.get('candle', {})
        context = signal_data.get('context', {})

        # Calculate individual scores
        ema_score = self.check_ema_alignment(
            prices['current'],
            prices['20'],
            prices['50'],
            prices['200']
        )

        pivot_score = self.check_pivot_confluence(
            prices['current'],
            levels
        )

        volume_score = self.check_volume_confirmation(
            current_volume,
            avg_volume
        )

        candle_score = self.check_candle_structure(candle)

        context_score = self.check_context_flow(context)

        # Create breakdown
        breakdown = {
            'ema_alignment': ema_score,
            'pivot_confluence': pivot_score,
            'volume_confirmation': volume_score,
            'candle_structure': candle_score,
            'context_flow': context_score
        }

        # Calculate overall confidence
        confidence = self.calculate_confidence(signal_data)

        # Determine validity
        is_valid = confidence >= self.threshold

        # Generate notes
        notes = []
        if priority_override:
            notes.append(f"Priority override active: {strategy}")
        if is_valid:
            notes.append(f"High-confidence signal: {confidence:.2%}")
        else:
            notes.append(f"Below threshold: {confidence:.2%} < {self.threshold:.2%}")

        # Check which metrics are weak
        weak_metrics = [
            metric for metric, score in breakdown.items()
            if score < 0.6
        ]
        if weak_metrics:
            notes.append(f"Weak metrics: {', '.join(weak_metrics)}")

        return ValidationResult(
            confidence=confidence,
            is_valid=is_valid,
            breakdown=breakdown,
            priority_override=priority_override,
            notes=" | ".join(notes) if notes else None
        )

    def check_ema_alignment(
        self,
        current_price: float,
        ema_20: float,
        ema_50: float,
        ema_200: float
    ) -> float:
        """
        Check EMA alignment for trend confirmation.

        Perfect alignment (bullish): Price > EMA20 > EMA50 > EMA200
        Perfect alignment (bearish): Price < EMA20 < EMA50 < EMA200

        Weight: 0.25 (highest priority metric)

        Args:
            current_price: Current market price
            ema_20: 20-period EMA value
            ema_50: 50-period EMA value
            ema_200: 200-period EMA value

        Returns:
            Float score between 0.0 (no alignment) and 1.0 (perfect alignment)

        Example:
            >>> score = engine.check_ema_alignment(18500, 18450, 18400, 18300)
            >>> print(f"EMA Alignment: {score:.2f}")
        """
        if not all([current_price, ema_20, ema_50, ema_200]):
            return 0.0

        score = 0.0

        # Check bullish alignment
        bullish_alignment = (
            current_price > ema_20 and
            ema_20 > ema_50 and
            ema_50 > ema_200
        )

        # Check bearish alignment
        bearish_alignment = (
            current_price < ema_20 and
            ema_20 < ema_50 and
            ema_50 < ema_200
        )

        if bullish_alignment or bearish_alignment:
            score = 1.0
        else:
            # Partial alignment scoring
            alignment_count = 0

            # For bullish direction
            if current_price > ema_20:
                alignment_count += 1
            if ema_20 > ema_50:
                alignment_count += 1
            if ema_50 > ema_200:
                alignment_count += 1

            # Check if bearish direction has more alignments
            bearish_count = 0
            if current_price < ema_20:
                bearish_count += 1
            if ema_20 < ema_50:
                bearish_count += 1
            if ema_50 < ema_200:
                bearish_count += 1

            alignment_count = max(alignment_count, bearish_count)
            score = alignment_count / 3.0

        return score

    def check_pivot_confluence(
        self,
        current_price: float,
        levels: Dict[str, float]
    ) -> float:
        """
        Check proximity to key pivot levels for confluence.

        Evaluates how close the current price is to pivot points,
        support, and resistance levels. Closer proximity indicates
        higher confluence and better risk/reward setups.

        Weight: 0.20

        Args:
            current_price: Current market price
            levels: Dictionary of pivot levels {'pivot': float, 'r1': float, 's1': float, ...}

        Returns:
            Float score between 0.0 (no confluence) and 1.0 (perfect confluence)

        Example:
            >>> levels = {'pivot': 18480, 'r1': 18550, 's1': 18410}
            >>> score = engine.check_pivot_confluence(18485, levels)
            >>> print(f"Pivot Confluence: {score:.2f}")
        """
        if not current_price or not levels:
            return 0.0

        pivot = levels.get('pivot', 0.0)
        r1 = levels.get('r1', 0.0)
        s1 = levels.get('s1', 0.0)

        if not pivot:
            return 0.0

        # Calculate distances to key levels
        distances = []

        # Distance to pivot (most important)
        if pivot:
            pivot_distance = abs(current_price - pivot) / pivot
            distances.append(('pivot', pivot_distance, 1.5))  # Higher weight

        # Distance to R1
        if r1:
            r1_distance = abs(current_price - r1) / r1
            distances.append(('r1', r1_distance, 1.0))

        # Distance to S1
        if s1:
            s1_distance = abs(current_price - s1) / s1
            distances.append(('s1', s1_distance, 1.0))

        if not distances:
            return 0.0

        # Find closest level with its weight
        closest = min(distances, key=lambda x: x[1])
        closest_distance = closest[1]
        closest_weight = closest[2]

        # Score based on proximity (closer = higher score)
        # Within 0.1% = perfect score
        # Within 0.5% = good score
        # Beyond 1.0% = low score
        if closest_distance < 0.001:  # Within 0.1%
            base_score = 1.0
        elif closest_distance < 0.005:  # Within 0.5%
            base_score = 0.8
        elif closest_distance < 0.01:  # Within 1.0%
            base_score = 0.6
        elif closest_distance < 0.02:  # Within 2.0%
            base_score = 0.4
        else:
            base_score = 0.2

        # Apply weight multiplier
        score = min(base_score * (closest_weight / 1.5), 1.0)

        return score

    def check_volume_confirmation(
        self,
        current_volume: float,
        avg_volume: float
    ) -> float:
        """
        Check volume confirmation for trade setup.

        Higher volume confirms stronger price moves and market conviction.
        Compares current volume to average volume.

        Weight: 0.20

        Args:
            current_volume: Current period volume
            avg_volume: Average volume (typically 20-period)

        Returns:
            Float score between 0.0 (no confirmation) and 1.0 (strong confirmation)

        Example:
            >>> score = engine.check_volume_confirmation(15000, 10000)
            >>> print(f"Volume Confirmation: {score:.2f}")
        """
        if not current_volume or not avg_volume or avg_volume == 0:
            return 0.0

        volume_ratio = current_volume / avg_volume

        # Scoring based on volume ratio
        if volume_ratio >= 2.0:  # 2x or more = exceptional
            score = 1.0
        elif volume_ratio >= 1.5:  # 1.5x = strong
            score = 0.9
        elif volume_ratio >= 1.2:  # 1.2x = good
            score = 0.75
        elif volume_ratio >= 1.0:  # Average or slightly above
            score = 0.6
        elif volume_ratio >= 0.8:  # Slightly below average
            score = 0.4
        else:  # Below 0.8x = weak
            score = 0.2

        return score

    def check_candle_structure(self, candle: Dict[str, float]) -> float:
        """
        Check candle structure for pattern confirmation.

        Evaluates candle patterns such as:
        - Bullish engulfing
        - Hammer/Inverted hammer
        - Doji patterns
        - Body-to-wick ratios

        Weight: 0.20

        Args:
            candle: Dictionary with OHLC data {'open': float, 'high': float, 'low': float, 'close': float}

        Returns:
            Float score between 0.0 (no pattern) and 1.0 (strong pattern)

        Example:
            >>> candle = {'open': 18490, 'high': 18510, 'low': 18485, 'close': 18505}
            >>> score = engine.check_candle_structure(candle)
            >>> print(f"Candle Structure: {score:.2f}")
        """
        if not candle or not all(k in candle for k in ['open', 'high', 'low', 'close']):
            return 0.0

        open_price = candle['open']
        high = candle['high']
        low = candle['low']
        close = candle['close']

        # Prevent division by zero
        if high == low:
            return 0.5  # Doji-like, neutral

        # Calculate candle metrics
        body = abs(close - open_price)
        total_range = high - low
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low

        # Body ratio
        body_ratio = body / total_range if total_range > 0 else 0

        # Wick ratios
        upper_wick_ratio = upper_wick / total_range if total_range > 0 else 0
        lower_wick_ratio = lower_wick / total_range if total_range > 0 else 0

        score = 0.5  # Base score

        # Check for special patterns first (highest priority)
        # Hammer: Long lower wick (>50% of range), small body, minimal upper wick
        is_hammer = (lower_wick_ratio > 0.5 and
                     body_ratio < 0.3 and
                     upper_wick_ratio < 0.2)

        # Inverted Hammer: Long upper wick (>50% of range), small body, minimal lower wick
        is_inverted_hammer = (upper_wick_ratio > 0.5 and
                              body_ratio < 0.3 and
                              lower_wick_ratio < 0.2)

        # Doji: Very small body
        is_doji = body_ratio < 0.1

        # Apply pattern-specific scoring
        if is_hammer:
            score = 0.95  # Strong reversal signal
        elif is_inverted_hammer:
            score = 0.95  # Strong reversal signal
        elif is_doji:
            score = 0.7  # Indecision, moderate score

        # Check for bullish patterns (if no special pattern)
        elif close > open_price:
            # Strong bullish candle (large body, small wicks)
            if body_ratio > 0.7:
                score = 0.9
            # Moderate bullish candle
            elif body_ratio > 0.5:
                score = 0.75
            else:
                score = 0.6

        # Check for bearish patterns (if no special pattern)
        elif close < open_price:
            # Strong bearish candle (large body, small wicks)
            if body_ratio > 0.7:
                score = 0.9
            # Moderate bearish candle
            elif body_ratio > 0.5:
                score = 0.75
            else:
                score = 0.6

        return score

    def check_context_flow(self, context: Dict[str, Any]) -> float:
        """
        Check market context and flow for trend alignment.

        Evaluates:
        - Overall trend direction (bullish/bearish/neutral)
        - Market volatility
        - Session context (US open, European close, etc.)

        Weight: 0.15 (lowest priority, but important for timing)

        Args:
            context: Dictionary with market context {'trend': str, 'volatility': float, ...}

        Returns:
            Float score between 0.0 (poor context) and 1.0 (perfect context)

        Example:
            >>> context = {'trend': 'bullish', 'volatility': 0.15}
            >>> score = engine.check_context_flow(context)
            >>> print(f"Context Flow: {score:.2f}")
        """
        if not context:
            return 0.5  # Neutral if no context provided

        trend = context.get('trend', 'neutral').lower()
        volatility = context.get('volatility', 0.0)

        score = 0.5  # Base score

        # Trend scoring
        if trend in ['bullish', 'bearish']:
            # Strong trend is good for trend-following strategies
            score += 0.3
        elif trend == 'neutral':
            # Neutral can be good for mean reversion
            score += 0.1

        # Volatility scoring
        # Ideal volatility: 0.1 - 0.25 (moderate volatility)
        if 0.1 <= volatility <= 0.25:
            score += 0.2
        elif 0.05 <= volatility < 0.1 or 0.25 < volatility <= 0.35:
            score += 0.1
        # Extreme volatility (< 0.05 or > 0.35) doesn't add to score

        # Cap at 1.0
        score = min(score, 1.0)

        return score


def validate_trade_signal(signal_data: Dict[str, Any]) -> ValidationResult:
    """
    Convenience function to validate a trade signal.

    Creates a ValidationEngine instance and validates the provided signal.

    Args:
        signal_data: Complete signal data dictionary

    Returns:
        ValidationResult with confidence score and validation details

    Example:
        >>> from core.validation_engine import validate_trade_signal
        >>> result = validate_trade_signal(signal_data)
        >>> if result.is_valid:
        ...     print("Signal is valid!")
    """
    engine = ValidationEngine()
    return engine.validate_signal(signal_data)


# Export main classes and functions
__all__ = [
    'ValidationEngine',
    'ValidationResult',
    'StrategyType',
    'validate_trade_signal'
]
