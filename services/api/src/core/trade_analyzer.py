"""
TradeAnalyzer - Complete Trade Analysis Integration Module

This module combines all Phase 2 components into a unified workflow:
- MarketDataFetcher: Fetch OHLCV data from Twelve Data API
- TechnicalIndicators: Calculate all technical indicators
- ValidationEngine: Validate trade signals with confidence scoring
- RiskCalculator: Calculate position sizing and risk parameters

The TradeAnalyzer provides a high-level API for complete trade analysis,
from data fetching to signal validation to risk management.

Author: TradeMatrix.ai
Date: 2025-10-29
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional, Literal, Tuple
from datetime import datetime
from supabase import Client

from .market_data_fetcher import MarketDataFetcher
from .technical_indicators import TechnicalIndicators
from .validation_engine import ValidationEngine, ValidationResult
from .risk_calculator import RiskCalculator
from config.supabase import get_supabase_admin

logger = logging.getLogger(__name__)


class TradeAnalyzerError(Exception):
    """Base exception for TradeAnalyzer errors"""
    pass


class InsufficientDataError(TradeAnalyzerError):
    """Raised when insufficient market data is available"""
    pass


class TradeAnalyzer:
    """
    Complete trade analysis integration module.

    Combines all Phase 2 components into a unified workflow for analyzing
    trading opportunities, validating signals, and calculating risk parameters.

    Components:
        - MarketDataFetcher: Retrieves OHLCV data
        - TechnicalIndicators: Calculates EMAs, RSI, MACD, BB, ATR, Ichimoku
        - ValidationEngine: Validates signals with confidence scoring
        - RiskCalculator: Position sizing and risk management

    Example:
        >>> analyzer = TradeAnalyzer(
        ...     supabase_client=supabase,
        ...     twelve_data_api_key="your_api_key",
        ...     account_balance=10000.0
        ... )
        >>> analysis = analyzer.get_complete_analysis(
        ...     symbol="DAX",
        ...     strategy_id="MR-02"
        ... )
        >>> if analysis['signal']['is_valid']:
        ...     print(f"Valid signal with {analysis['signal']['confidence']:.2%} confidence")
    """

    def __init__(
        self,
        supabase_client: Optional[Client] = None,
        twelve_data_api_key: Optional[str] = None,
        account_balance: float = 10000.0,
        risk_per_trade: float = 0.01
    ):
        """
        Initialize TradeAnalyzer with all required components.

        Args:
            supabase_client: Supabase client instance (defaults to admin client)
            twelve_data_api_key: Twelve Data API key (defaults to env var)
            account_balance: Trading account balance in EUR (default: 10000.0)
            risk_per_trade: Risk per trade as decimal (default: 0.01 = 1%)

        Raises:
            ValueError: If account_balance <= 0 or risk_per_trade not in (0, 0.1]
        """
        # Initialize Supabase client
        self.supabase = supabase_client or get_supabase_admin()

        # Initialize Market Data Fetcher
        self.data_fetcher = MarketDataFetcher(
            api_key=twelve_data_api_key,
            supabase_client=self.supabase
        )

        # Initialize Validation Engine
        self.validator = ValidationEngine()

        # Initialize Risk Calculator
        self.risk_calculator = RiskCalculator(
            account_balance=account_balance,
            risk_per_trade=risk_per_trade
        )

        logger.info(
            f"TradeAnalyzer initialized with account balance: {account_balance:.2f} EUR, "
            f"risk per trade: {risk_per_trade * 100:.1f}%"
        )

    def fetch_and_calculate_indicators(
        self,
        symbol: str,
        interval: str = "1h",
        outputsize: int = 300
    ) -> Dict[str, Any]:
        """
        Fetch market data and calculate all technical indicators.

        This method combines data fetching and indicator calculation into
        a single operation, returning a comprehensive set of indicators.

        Args:
            symbol: Trading symbol (e.g., "DAX", "NASDAQ", "EUR/USD")
            interval: Time interval (default: "1h")
            outputsize: Number of candles to fetch (default: 300 for 200 EMA)

        Returns:
            Dictionary containing:
                - candles: Raw OHLCV data
                - indicators: All technical indicators
                - current_price: Latest close price
                - timestamp: Analysis timestamp

        Raises:
            InsufficientDataError: If not enough data is available
            TradeAnalyzerError: For other errors

        Example:
            >>> data = analyzer.fetch_and_calculate_indicators("DAX", "1h", 300)
            >>> print(f"Current price: {data['current_price']}")
            >>> print(f"EMA 20: {data['indicators']['ema']['20'][-1]}")
        """
        try:
            logger.info(f"Fetching {symbol} data ({interval}, {outputsize} candles)...")

            # Fetch time series data
            candles = self.data_fetcher.fetch_time_series(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )

            if not candles or len(candles) < 200:
                raise InsufficientDataError(
                    f"Insufficient data for {symbol}: got {len(candles)} candles, need >= 200"
                )

            # Convert to arrays (reverse order - oldest first)
            candles_reversed = list(reversed(candles))
            high = [float(c['high']) for c in candles_reversed]
            low = [float(c['low']) for c in candles_reversed]
            close = [float(c['close']) for c in candles_reversed]
            volume = [int(c.get('volume', 0)) for c in candles_reversed]

            logger.info(f"Calculating indicators for {symbol}...")

            # Calculate all indicators
            indicators = TechnicalIndicators.calculate_all_indicators(
                high=high,
                low=low,
                close=close,
                volume=volume
            )

            # Get current price (latest close)
            current_price = close[-1]

            return {
                'symbol': symbol,
                'interval': interval,
                'candles': candles,  # Original order (newest first)
                'indicators': indicators,
                'current_price': current_price,
                'timestamp': datetime.utcnow().isoformat(),
                'candle_count': len(candles)
            }

        except InsufficientDataError:
            raise
        except Exception as e:
            raise TradeAnalyzerError(f"Error fetching/calculating indicators: {str(e)}")

    def validate_trade_setup(
        self,
        symbol: str,
        strategy_id: str,
        indicators: Dict[str, Any],
        current_price: float,
        current_candle: Optional[Dict[str, float]] = None
    ) -> ValidationResult:
        """
        Validate a trade setup using the ValidationEngine.

        Args:
            symbol: Trading symbol
            strategy_id: Strategy type (e.g., "MR-02")
            indicators: Technical indicators from fetch_and_calculate_indicators()
            current_price: Current market price
            current_candle: Optional current candle OHLC data

        Returns:
            ValidationResult with confidence score and validation details

        Example:
            >>> result = analyzer.validate_trade_setup(
            ...     symbol="DAX",
            ...     strategy_id="MR-02",
            ...     indicators=data['indicators'],
            ...     current_price=data['current_price']
            ... )
            >>> print(f"Confidence: {result.confidence:.2%}")
        """
        try:
            logger.info(f"Validating {strategy_id} setup for {symbol}...")

            # Extract latest indicator values
            ema_20 = indicators['ema']['20'][-1]
            ema_50 = indicators['ema']['50'][-1]
            ema_200 = indicators['ema']['200'][-1]

            # Calculate average volume (last 20 periods)
            avg_volume = sum(indicators.get('volume', [0])[-20:]) / 20 if 'volume' in indicators else 0

            # Get current volume (latest)
            current_volume = indicators.get('volume', [0])[-1] if 'volume' in indicators else 0

            # Prepare signal data for validation
            signal_data = {
                'symbol': symbol,
                'price': current_price,
                'emas': {
                    '20': ema_20,
                    '50': ema_50,
                    '200': ema_200
                },
                'levels': indicators.get('pivot_points', {}),
                'volume': current_volume,
                'avg_volume': avg_volume,
                'candle': current_candle or {},
                'context': {
                    'trend': indicators.get('trend', 'neutral'),
                    'volatility': 0.15  # Placeholder - could calculate from ATR
                },
                'strategy': strategy_id
            }

            # Validate signal
            result = self.validator.validate_signal(signal_data)

            logger.info(
                f"Validation complete: confidence={result.confidence:.2%}, "
                f"valid={result.is_valid}"
            )

            return result

        except Exception as e:
            raise TradeAnalyzerError(f"Error validating trade setup: {str(e)}")

    def calculate_trade_params(
        self,
        entry_price: float,
        stop_loss: float,
        position_type: Literal['long', 'short'],
        risk_reward_ratio: float = 2.0,
        product_type: Literal['CFD', 'KO', 'Futures'] = 'CFD',
        commission_percentage: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculate complete trade parameters using RiskCalculator.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            position_type: Position type ('long' or 'short')
            risk_reward_ratio: Risk-reward ratio (default: 2.0)
            product_type: Product type (default: 'CFD')
            commission_percentage: Commission percentage (default: 0.0)

        Returns:
            Complete trade plan with position sizing, risk, leverage, etc.

        Example:
            >>> params = analyzer.calculate_trade_params(
            ...     entry_price=19500.0,
            ...     stop_loss=19450.0,
            ...     position_type='long',
            ...     risk_reward_ratio=2.0
            ... )
            >>> print(f"Position size: {params['position_size']}")
        """
        try:
            logger.info(
                f"Calculating trade params: entry={entry_price}, sl={stop_loss}, "
                f"type={position_type}, rr={risk_reward_ratio}"
            )

            # Calculate full trade plan
            trade_plan = self.risk_calculator.calculate_full_trade_plan(
                entry=entry_price,
                stop_loss=stop_loss,
                direction=position_type,
                risk_reward_ratio=risk_reward_ratio,
                product_type=product_type,
                commission_percentage=commission_percentage
            )

            logger.info(
                f"Trade params calculated: position_size={trade_plan['position_size']}, "
                f"risk={trade_plan['risk_amount']:.2f} EUR"
            )

            return trade_plan

        except Exception as e:
            raise TradeAnalyzerError(f"Error calculating trade params: {str(e)}")

    def get_complete_analysis(
        self,
        symbol: str,
        strategy_id: str,
        interval: str = "1h",
        outputsize: int = 300,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        position_type: Optional[Literal['long', 'short']] = None,
        risk_reward_ratio: float = 2.0,
        product_type: Literal['CFD', 'KO', 'Futures'] = 'CFD'
    ) -> Dict[str, Any]:
        """
        Perform complete trade analysis from data fetching to risk calculation.

        This is the main integration method that orchestrates the entire
        analysis workflow:
        1. Fetch market data
        2. Calculate technical indicators
        3. Validate trade signal
        4. Calculate risk parameters (if entry/SL provided)

        Args:
            symbol: Trading symbol (e.g., "DAX", "NASDAQ")
            strategy_id: Strategy type (e.g., "MR-02")
            interval: Time interval (default: "1h")
            outputsize: Number of candles to fetch (default: 300)
            entry_price: Optional entry price for risk calculation
            stop_loss: Optional stop loss for risk calculation
            position_type: Optional position type for risk calculation
            risk_reward_ratio: Risk-reward ratio (default: 2.0)
            product_type: Product type (default: 'CFD')

        Returns:
            Comprehensive analysis dictionary containing:
                - market_data: Raw candles and current price
                - indicators: All technical indicators
                - signal: Validation result with confidence score
                - trade_plan: Risk parameters (if entry/SL provided)
                - summary: Quick reference summary

        Raises:
            InsufficientDataError: If not enough market data
            TradeAnalyzerError: For other errors

        Example:
            >>> # Full analysis with risk calculation
            >>> analysis = analyzer.get_complete_analysis(
            ...     symbol="DAX",
            ...     strategy_id="MR-02",
            ...     entry_price=19500.0,
            ...     stop_loss=19450.0,
            ...     position_type='long'
            ... )
            >>>
            >>> # Analysis without risk calculation
            >>> analysis = analyzer.get_complete_analysis(
            ...     symbol="NASDAQ",
            ...     strategy_id="MR-01"
            ... )
        """
        logger.info(f"Starting complete analysis for {symbol} ({strategy_id})...")

        try:
            # Step 1: Fetch data and calculate indicators
            data = self.fetch_and_calculate_indicators(
                symbol=symbol,
                interval=interval,
                outputsize=outputsize
            )

            # Step 2: Get current candle for validation
            latest_candle = None
            if data['candles']:
                latest = data['candles'][0]  # Newest first
                latest_candle = {
                    'open': float(latest['open']),
                    'high': float(latest['high']),
                    'low': float(latest['low']),
                    'close': float(latest['close'])
                }

            # Step 3: Validate trade setup
            validation_result = self.validate_trade_setup(
                symbol=symbol,
                strategy_id=strategy_id,
                indicators=data['indicators'],
                current_price=data['current_price'],
                current_candle=latest_candle
            )

            # Step 4: Calculate trade parameters (if entry/SL provided)
            trade_plan = None
            if entry_price and stop_loss and position_type:
                trade_plan = self.calculate_trade_params(
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    position_type=position_type,
                    risk_reward_ratio=risk_reward_ratio,
                    product_type=product_type
                )

            # Build comprehensive analysis result
            analysis = {
                'symbol': symbol,
                'strategy': strategy_id,
                'timestamp': data['timestamp'],
                'market_data': {
                    'current_price': data['current_price'],
                    'interval': interval,
                    'candle_count': data['candle_count'],
                    'latest_candle': latest_candle
                },
                'indicators': {
                    'ema': {
                        '20': data['indicators']['ema']['20'][-1],
                        '50': data['indicators']['ema']['50'][-1],
                        '200': data['indicators']['ema']['200'][-1]
                    },
                    'rsi': data['indicators']['rsi'][-1],
                    'macd': {
                        'macd_line': data['indicators']['macd']['macd_line'][-1],
                        'signal_line': data['indicators']['macd']['signal_line'][-1],
                        'histogram': data['indicators']['macd']['histogram'][-1]
                    },
                    'bollinger_bands': {
                        'upper': data['indicators']['bollinger_bands']['upper'][-1],
                        'middle': data['indicators']['bollinger_bands']['middle'][-1],
                        'lower': data['indicators']['bollinger_bands']['lower'][-1]
                    },
                    'atr': data['indicators']['atr'][-1],
                    'pivot_points': data['indicators']['pivot_points'],
                    'trend': data['indicators']['trend'],
                    'alignment': data['indicators']['alignment']
                },
                'signal': {
                    'confidence': validation_result.confidence,
                    'is_valid': validation_result.is_valid,
                    'breakdown': validation_result.breakdown,
                    'priority_override': validation_result.priority_override,
                    'notes': validation_result.notes
                },
                'trade_plan': trade_plan,
                'summary': self._generate_summary(
                    symbol=symbol,
                    strategy_id=strategy_id,
                    current_price=data['current_price'],
                    validation_result=validation_result,
                    trade_plan=trade_plan,
                    trend=data['indicators']['trend']
                )
            }

            logger.info(
                f"Complete analysis finished: {symbol} {strategy_id} - "
                f"confidence={validation_result.confidence:.2%}, "
                f"valid={validation_result.is_valid}"
            )

            return analysis

        except InsufficientDataError:
            raise
        except Exception as e:
            raise TradeAnalyzerError(f"Error in complete analysis: {str(e)}")

    def _generate_summary(
        self,
        symbol: str,
        strategy_id: str,
        current_price: float,
        validation_result: ValidationResult,
        trade_plan: Optional[Dict],
        trend: str
    ) -> Dict[str, Any]:
        """
        Generate a quick reference summary of the analysis.

        Args:
            symbol: Trading symbol
            strategy_id: Strategy ID
            current_price: Current price
            validation_result: Validation result
            trade_plan: Trade plan (optional)
            trend: Trend direction

        Returns:
            Summary dictionary with key insights
        """
        summary = {
            'symbol': symbol,
            'strategy': strategy_id,
            'current_price': current_price,
            'trend': trend,
            'signal_valid': validation_result.is_valid,
            'confidence': f"{validation_result.confidence:.1%}",
            'recommendation': 'TRADE' if validation_result.is_valid else 'WAIT'
        }

        if trade_plan:
            summary.update({
                'entry': trade_plan['entry'],
                'stop_loss': trade_plan['stop_loss'],
                'take_profit': trade_plan['take_profit'],
                'position_size': trade_plan['position_size'],
                'risk_amount': f"{trade_plan['risk_amount']:.2f} EUR",
                'risk_percentage': f"{trade_plan['risk_percentage']:.2f}%",
                'risk_reward': f"1:{trade_plan['risk_reward_ratio']}"
            })

        # Add weakest metric
        if validation_result.breakdown:
            weakest = min(
                validation_result.breakdown.items(),
                key=lambda x: x[1]
            )
            summary['weakest_metric'] = f"{weakest[0]} ({weakest[1]:.2f})"

        return summary

    def analyze_symbol(
        self,
        symbol: str,
        strategy_id: str
    ) -> Dict[str, Any]:
        """
        Quick analysis method - just fetch data, indicators, and validation.

        This is a convenience method that performs analysis without risk
        calculation. Use get_complete_analysis() for full analysis.

        Args:
            symbol: Trading symbol
            strategy_id: Strategy type

        Returns:
            Analysis without trade plan (market data + indicators + signal)

        Example:
            >>> analysis = analyzer.analyze_symbol("DAX", "MR-02")
            >>> if analysis['signal']['is_valid']:
            ...     print("Valid signal detected!")
        """
        return self.get_complete_analysis(
            symbol=symbol,
            strategy_id=strategy_id
        )


# Convenience functions
def create_analyzer(
    account_balance: float = 10000.0,
    risk_per_trade: float = 0.01,
    twelve_data_api_key: Optional[str] = None
) -> TradeAnalyzer:
    """
    Create a TradeAnalyzer instance with default configuration.

    Args:
        account_balance: Account balance in EUR (default: 10000.0)
        risk_per_trade: Risk per trade (default: 0.01 = 1%)
        twelve_data_api_key: Twelve Data API key (optional)

    Returns:
        Configured TradeAnalyzer instance

    Example:
        >>> from core.trade_analyzer import create_analyzer
        >>> analyzer = create_analyzer(account_balance=5000.0)
    """
    return TradeAnalyzer(
        account_balance=account_balance,
        risk_per_trade=risk_per_trade,
        twelve_data_api_key=twelve_data_api_key
    )


# Export main classes
__all__ = [
    'TradeAnalyzer',
    'TradeAnalyzerError',
    'InsufficientDataError',
    'create_analyzer'
]
