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

# RiskCalculator import
try:
    from .risk_calculator import RiskCalculator
    has_risk_calculator = True
except ImportError:
    has_risk_calculator = False

# TradeAnalyzer import (Integration Module)
try:
    from .trade_analyzer import (
        TradeAnalyzer,
        TradeAnalyzerError,
        InsufficientDataError,
        create_analyzer
    )
    has_trade_analyzer = True
except ImportError:
    has_trade_analyzer = False

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

if has_trade_analyzer:
    __all__.extend([
        "TradeAnalyzer",
        "TradeAnalyzerError",
        "InsufficientDataError",
        "create_analyzer"
    ])
