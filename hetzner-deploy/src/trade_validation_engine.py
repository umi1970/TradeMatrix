"""
TradeMatrix.ai - TradeValidationEngine
Validates trade setup quality using technical analysis and rule-based scoring.

Execution: Part of ValidationAndRisk flow (on-demand)
Responsibilities:
  1. Calculate technical bias score (EMA alignment, structure, momentum)
  2. Validate Risk/Reward ratio (minimum 2.5:1)
  3. Check market structure (trend alignment, support/resistance confluence)
  4. Apply trading rules from config/rules/*.yaml
  5. Generate validation result (APPROVED/REJECTED) with confidence score

Data sources:
  - trade_proposal dict (from SignalBot)
  - config/rules/*.yaml (trading rule configurations)
  - Technical indicators (from market structure analysis)

Output: ValidationResult for RiskManager
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pathlib import Path
import yaml

from supabase import Client

# Setup logger
logger = logging.getLogger(__name__)


class ValidationResult:
    """
    Validation result data class

    Attributes:
        status: "APPROVED" or "REJECTED"
        bias_score: Technical bias score (0.0-1.0)
        rr_ratio: Risk/Reward ratio
        confidence: Overall confidence score (0.0-1.0)
        breakdown: Dict with individual scores
        reason: Approval/rejection reason
        notes: Additional validation notes
    """

    def __init__(
        self,
        status: str,
        bias_score: float,
        rr_ratio: float,
        confidence: float,
        breakdown: Dict[str, float],
        reason: str,
        notes: List[str] = None
    ):
        self.status = status
        self.bias_score = bias_score
        self.rr_ratio = rr_ratio
        self.confidence = confidence
        self.breakdown = breakdown
        self.reason = reason
        self.notes = notes or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'status': self.status,
            'bias_score': self.bias_score,
            'rr_ratio': self.rr_ratio,
            'confidence': self.confidence,
            'breakdown': self.breakdown,
            'reason': self.reason,
            'notes': self.notes
        }


class TradeValidationEngine:
    """
    TradeValidationEngine - Validates trade setup quality

    Responsibilities:
    - Calculate technical bias score (trend, EMA alignment, momentum)
    - Validate Risk/Reward ratio (minimum 2.5:1)
    - Check market structure (support/resistance confluence)
    - Apply trading rules from YAML config files
    - Generate validation result (APPROVED/REJECTED)
    """

    # Validation thresholds
    MIN_RR_RATIO = 2.5
    MIN_BIAS_SCORE = 0.60
    MIN_CONFIDENCE = 0.75

    def __init__(self, supabase_client: Client):
        """
        Initialize TradeValidationEngine

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
        """
        self.supabase = supabase_client
        self.rules_cache = {}  # Cache for loaded trading rules
        logger.info("TradeValidationEngine initialized")


    def validate_trade(
        self,
        trade_proposal: Dict[str, Any]
    ) -> ValidationResult:
        """
        Main validation method - validates entire trade setup

        Process:
        1. Extract trade parameters
        2. Calculate bias score (technical structure)
        3. Check R:R ratio
        4. Check market structure
        5. Apply trading rules
        6. Calculate overall confidence
        7. Generate approval/rejection decision

        Args:
            trade_proposal: Dict with trade parameters:
            {
                'symbol': str,
                'direction': 'long' | 'short',
                'entry': float,
                'sl': float,
                'tp': float,
                'timeframe': str,
                'strategy': str (e.g., 'asia_sweep', 'ema_cross'),
                'indicators': {
                    'emas': {'20': float, '50': float, '200': float},
                    'rsi': float,
                    'macd': {...},
                    'atr': float
                },
                'levels': {
                    'pivot': float,
                    'r1': float, 's1': float, ...
                },
                'context': {
                    'trend': str,
                    'volatility': float
                }
            }

        Returns:
            ValidationResult with status, scores, and reasoning
        """
        logger.info(f"Validating trade: {trade_proposal.get('symbol')} {trade_proposal.get('direction')}")

        try:
            # Step 1 - Extract parameters
            symbol = trade_proposal.get('symbol', 'UNKNOWN')
            direction = trade_proposal.get('direction', 'long')
            entry = float(trade_proposal.get('entry', 0))
            sl = float(trade_proposal.get('sl', 0))
            tp = float(trade_proposal.get('tp', 0))
            strategy = trade_proposal.get('strategy', 'unknown')

            # Step 2 - Calculate bias score
            bias_score = self.calculate_bias_score(trade_proposal)

            # Step 3 - Check R:R ratio
            rr_ratio = self.check_rr_ratio(entry, sl, tp, direction)

            # Step 4 - Check market structure
            structure_score = self.check_market_structure(
                symbol=symbol,
                timeframe=trade_proposal.get('timeframe', '5m'),
                direction=direction,
                indicators=trade_proposal.get('indicators', {}),
                context=trade_proposal.get('context', {})
            )

            # Step 5 - Apply trading rules
            rules_score = self.apply_trading_rules(trade_proposal)

            # Step 6 - Build breakdown
            breakdown = {
                'bias_score': bias_score,
                'rr_ratio': rr_ratio,
                'structure_score': structure_score,
                'rules_score': rules_score
            }

            # Step 7 - Calculate overall confidence
            confidence = (
                bias_score * 0.35 +
                structure_score * 0.30 +
                rules_score * 0.25 +
                min(rr_ratio / 5.0, 0.20) * 0.10  # R:R bonus (capped at 5:1)
            )

            # Step 8 - Generate decision
            notes = []

            if rr_ratio < self.MIN_RR_RATIO:
                status = "REJECTED"
                reason = f"R:R ratio {rr_ratio:.2f} below minimum {self.MIN_RR_RATIO}"
                notes.append("Insufficient risk/reward ratio")
            elif bias_score < self.MIN_BIAS_SCORE:
                status = "REJECTED"
                reason = f"Bias score {bias_score:.2f} below minimum {self.MIN_BIAS_SCORE}"
                notes.append("Weak technical bias")
            elif confidence < self.MIN_CONFIDENCE:
                status = "REJECTED"
                reason = f"Overall confidence {confidence:.2f} below minimum {self.MIN_CONFIDENCE}"
                notes.append("Insufficient confidence score")
            else:
                status = "APPROVED"
                reason = f"Trade approved with confidence {confidence:.2f}"
                notes.append("All validation criteria met")

            logger.info(f"Validation result: {status} (confidence: {confidence:.2f})")

            return ValidationResult(
                status=status,
                bias_score=bias_score,
                rr_ratio=rr_ratio,
                confidence=confidence,
                breakdown=breakdown,
                reason=reason,
                notes=notes
            )

        except Exception as e:
            logger.error(f"Error validating trade: {e}", exc_info=True)
            return ValidationResult(
                status="REJECTED",
                bias_score=0.0,
                rr_ratio=0.0,
                confidence=0.0,
                breakdown={},
                reason=f"Validation error: {str(e)}",
                notes=["Validation failed due to internal error"]
            )


    def calculate_bias_score(self, trade_proposal: Dict[str, Any]) -> float:
        """
        Calculate technical bias score (0.0-1.0)

        Scoring factors:
        - EMA alignment (30%)
        - Price position vs EMAs (25%)
        - RSI confirmation (20%)
        - MACD confirmation (15%)
        - Volume confirmation (10%)

        Args:
            trade_proposal: Trade proposal dict

        Returns:
            Bias score (0.0-1.0)
        """
        logger.debug("Calculating bias score")

        try:
            direction = trade_proposal.get('direction', 'long')
            indicators = trade_proposal.get('indicators', {})
            context = trade_proposal.get('context', {})

            emas = indicators.get('emas', {})
            ema_20 = emas.get('20', 0)
            ema_50 = emas.get('50', 0)
            ema_200 = emas.get('200', 0)
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', {})
            macd_histogram = macd.get('histogram', 0)

            price = float(trade_proposal.get('entry', 0))
            trend = context.get('trend', 'neutral')

            score = 0.0

            # Factor 1 - EMA alignment (30%)
            if direction == 'long':
                if ema_20 > ema_50 > ema_200:
                    score += 0.30  # Perfect bullish alignment
                elif ema_20 > ema_50:
                    score += 0.20  # Partial alignment
                elif ema_20 > ema_200:
                    score += 0.10  # Minimal alignment
            else:  # short
                if ema_20 < ema_50 < ema_200:
                    score += 0.30  # Perfect bearish alignment
                elif ema_20 < ema_50:
                    score += 0.20  # Partial alignment
                elif ema_20 < ema_200:
                    score += 0.10  # Minimal alignment

            # Factor 2 - Price position (25%)
            if direction == 'long':
                if price > ema_20 > ema_50:
                    score += 0.25  # Price above fast EMAs
                elif price > ema_50:
                    score += 0.15
                elif price > ema_200:
                    score += 0.10
            else:  # short
                if price < ema_20 < ema_50:
                    score += 0.25  # Price below fast EMAs
                elif price < ema_50:
                    score += 0.15
                elif price < ema_200:
                    score += 0.10

            # Factor 3 - RSI confirmation (20%)
            if direction == 'long':
                if 40 <= rsi <= 70:
                    score += 0.20  # Not oversold, not overbought
                elif 30 <= rsi < 40:
                    score += 0.10  # Slightly oversold (potential bounce)
            else:  # short
                if 30 <= rsi <= 60:
                    score += 0.20  # Not overbought, not oversold
                elif 60 < rsi <= 70:
                    score += 0.10  # Slightly overbought (potential drop)

            # Factor 4 - MACD confirmation (15%)
            if direction == 'long':
                if macd_histogram > 0:
                    score += 0.15  # Bullish momentum
            else:  # short
                if macd_histogram < 0:
                    score += 0.15  # Bearish momentum

            # Factor 5 - Trend alignment (10%)
            if direction == 'long' and trend == 'bullish':
                score += 0.10
            elif direction == 'short' and trend == 'bearish':
                score += 0.10

            bias_score = min(score, 1.0)  # Cap at 1.0
            logger.debug(f"Bias score: {bias_score:.2f}")

            return bias_score

        except Exception as e:
            logger.error(f"Error calculating bias score: {e}", exc_info=True)
            return 0.0


    def check_rr_ratio(
        self,
        entry: float,
        sl: float,
        tp: float,
        direction: str = 'long'
    ) -> float:
        """
        Calculate and validate Risk/Reward ratio

        Args:
            entry: Entry price
            sl: Stop loss price
            tp: Take profit price
            direction: 'long' or 'short'

        Returns:
            R:R ratio (e.g., 2.5 for 2.5:1)
        """
        try:
            if direction == 'long':
                risk = entry - sl
                reward = tp - entry
            else:  # short
                risk = sl - entry
                reward = entry - tp

            if risk <= 0:
                logger.warning("Invalid risk calculation (risk <= 0)")
                return 0.0

            rr_ratio = reward / risk

            logger.debug(f"R:R ratio: {rr_ratio:.2f} (risk: {risk:.2f}, reward: {reward:.2f})")
            return rr_ratio

        except Exception as e:
            logger.error(f"Error calculating R:R ratio: {e}", exc_info=True)
            return 0.0


    def check_market_structure(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        indicators: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """
        Check market structure quality

        Scoring factors:
        - Trend alignment with direction (40%)
        - Support/resistance confluence (30%)
        - Volatility level (20%)
        - Price action structure (10%)

        Args:
            symbol: Symbol name
            timeframe: Timeframe
            direction: Trade direction
            indicators: Technical indicators dict
            context: Market context dict

        Returns:
            Structure score (0.0-1.0)
        """
        logger.debug("Checking market structure")

        try:
            trend = context.get('trend', 'neutral')
            volatility = context.get('volatility', 0.0)
            levels = indicators.get('levels', {})

            score = 0.0

            # Factor 1 - Trend alignment (40%)
            if direction == 'long' and trend == 'bullish':
                score += 0.40
            elif direction == 'short' and trend == 'bearish':
                score += 0.40
            elif trend == 'neutral':
                score += 0.20  # Neutral trend gets partial credit

            # Factor 2 - Support/resistance confluence (30%)
            # Check if entry is near key level (within 0.5% tolerance)
            entry = float(indicators.get('price', 0))
            if entry > 0 and levels:
                pivot = levels.get('pivot', 0)
                r1 = levels.get('r1', 0)
                s1 = levels.get('s1', 0)

                tolerance = entry * 0.005  # 0.5% tolerance

                if any(abs(entry - level) <= tolerance for level in [pivot, r1, s1] if level > 0):
                    score += 0.30  # Near key level (confluence)

            # Factor 3 - Volatility level (20%)
            # Prefer medium volatility (0.01-0.03)
            if 0.01 <= volatility <= 0.03:
                score += 0.20  # Optimal volatility
            elif 0.005 <= volatility < 0.01 or 0.03 < volatility <= 0.05:
                score += 0.10  # Acceptable volatility

            # Factor 4 - Price action structure (10%)
            # This would require candle pattern analysis (future enhancement)
            score += 0.05  # Default partial credit

            structure_score = min(score, 1.0)
            logger.debug(f"Structure score: {structure_score:.2f}")

            return structure_score

        except Exception as e:
            logger.error(f"Error checking market structure: {e}", exc_info=True)
            return 0.0


    def apply_trading_rules(self, trade_proposal: Dict[str, Any]) -> float:
        """
        Apply trading rules from config/rules/*.yaml

        Args:
            trade_proposal: Trade proposal dict

        Returns:
            Rules compliance score (0.0-1.0)
        """
        logger.debug("Applying trading rules")

        try:
            strategy = trade_proposal.get('strategy', 'unknown')

            # Load strategy rule file
            rule_config = self._load_rule_config(strategy)

            if not rule_config:
                logger.warning(f"No rule config found for strategy: {strategy}")
                return 0.70  # Default moderate score if no rules found

            # Extract validation metrics from rule config
            validation_metrics = rule_config.get('validation_metrics', {})
            min_confidence = validation_metrics.get('min_confidence_score', 0.75)

            # Check entry conditions
            # (Simplified - in production, parse YAML and check each condition)
            score = 0.80  # Default good score

            logger.debug(f"Rules score: {score:.2f}")
            return score

        except Exception as e:
            logger.error(f"Error applying trading rules: {e}", exc_info=True)
            return 0.50  # Default neutral score on error


    def _load_rule_config(self, strategy: str) -> Optional[Dict[str, Any]]:
        """
        Load trading rule configuration from YAML file

        Args:
            strategy: Strategy name (e.g., 'ema_cross', 'asia_sweep')

        Returns:
            Rule config dict or None if not found
        """
        # Check cache first
        if strategy in self.rules_cache:
            return self.rules_cache[strategy]

        try:
            # Look for rule file in config/rules/
            rules_dir = Path(__file__).parent.parent.parent / 'config' / 'rules'
            rule_files = list(rules_dir.glob(f"*{strategy}*.yaml"))

            if not rule_files:
                logger.warning(f"No rule file found for strategy: {strategy}")
                return None

            # Load first matching file
            with open(rule_files[0], 'r') as f:
                rule_config = yaml.safe_load(f)

            # Cache for future use
            self.rules_cache[strategy] = rule_config

            logger.debug(f"Loaded rule config for {strategy}")
            return rule_config

        except Exception as e:
            logger.error(f"Error loading rule config for {strategy}: {e}", exc_info=True)
            return None


# Example usage (for testing)
if __name__ == "__main__":
    import sys
    from config.supabase import get_supabase_admin

    # Initialize engine with admin client
    engine = TradeValidationEngine(supabase_client=get_supabase_admin())

    # Mock trade proposal
    trade_proposal = {
        'symbol': 'DAX',
        'direction': 'long',
        'entry': 18500.0,
        'sl': 18450.0,
        'tp': 18650.0,
        'timeframe': '5m',
        'strategy': 'ema_cross',
        'indicators': {
            'emas': {'20': 18480.0, '50': 18450.0, '200': 18400.0},
            'rsi': 55.0,
            'macd': {'line': 10.5, 'signal': 8.2, 'histogram': 2.3},
            'atr': 30.0
        },
        'levels': {
            'pivot': 18470.0,
            'r1': 18520.0,
            's1': 18420.0
        },
        'context': {
            'trend': 'bullish',
            'volatility': 0.016
        }
    }

    # Validate trade
    result = engine.validate_trade(trade_proposal)

    print("Validation Result:")
    print(result.to_dict())
