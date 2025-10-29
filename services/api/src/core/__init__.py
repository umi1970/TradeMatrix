"""
Core utilities for TradeMatrix.ai
"""

from .market_data_fetcher import MarketDataFetcher
from .validation_engine import (
    ValidationEngine,
    ValidationResult,
    StrategyType,
    validate_trade_signal
)
from .technical_indicators import (
    TechnicalIndicators,
    MACDResult,
    BollingerBandsResult,
    IchimokuResult,
    PivotPointsResult
)

# RiskCalculator will be imported when it exists
try:
    from .risk_calculator import RiskCalculator
    has_risk_calculator = True
except ImportError:
    has_risk_calculator = False

__all__ = [
    "MarketDataFetcher",
    "ValidationEngine",
    "ValidationResult",
    "StrategyType",
    "validate_trade_signal",
    "TechnicalIndicators",
    "MACDResult",
    "BollingerBandsResult",
    "IchimokuResult",
    "PivotPointsResult",
]

if has_risk_calculator:
    __all__.append("RiskCalculator")
