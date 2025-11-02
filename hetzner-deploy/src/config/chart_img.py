#!/usr/bin/env python3
"""
Chart-img.com API Configuration
Manages API keys, symbol mappings, and chart generation settings
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


class ChartImgConfig:
    """Configuration for chart-img.com API"""

    # API Configuration
    API_KEY = os.getenv('CHART_IMG_API_KEY', '3pJTrvapkk9LQ7FwaUOmf6I354fSOeWa8VJifI2l')
    BASE_URL = os.getenv('CHART_IMG_BASE_URL', 'https://api.chart-img.com')
    API_ENDPOINT = f"{BASE_URL}/v2/tradingview/advanced-chart"

    # Rate Limiting Configuration
    RATE_LIMIT_DAILY = 1000  # Max requests per day
    RATE_LIMIT_PER_SECOND = 15  # Max requests per second
    RATE_LIMIT_WARNING_THRESHOLD = 0.80  # Alert at 80% (800 requests)
    RATE_LIMIT_HARD_STOP_THRESHOLD = 0.95  # Hard stop at 95% (950 requests)

    # Redis Configuration
    REDIS_KEY_PREFIX = "chart_img"
    REDIS_DAILY_COUNTER_KEY_FORMAT = "{prefix}:requests:daily:{date}"
    REDIS_CACHE_KEY_FORMAT = "chart:{symbol_id}:{timeframe}:{timestamp_5min}"
    REDIS_CACHE_TTL = 300  # 5 minutes in seconds

    # Chart Generation Settings
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1200
    DEFAULT_THEME = "dark"

    # Supported Timeframes
    SUPPORTED_TIMEFRAMES = [
        "1m", "5m", "15m", "30m",
        "1h", "2h", "4h", "6h", "12h",
        "1d", "3d", "1w", "1M"
    ]

    # Timeframe Display Names
    TIMEFRAME_DISPLAY = {
        "1m": "1 Minute",
        "5m": "5 Minutes",
        "15m": "15 Minutes",
        "30m": "30 Minutes",
        "1h": "1 Hour",
        "2h": "2 Hours",
        "4h": "4 Hours",
        "6h": "6 Hours",
        "12h": "12 Hours",
        "1d": "Daily",
        "3d": "3 Days",
        "1w": "Weekly",
        "1M": "Monthly",
    }

    # Indicator Presets (Mapping our naming to chart-img.com API)
    INDICATOR_MAPPING = {
        "EMA_20": {"name": "EMA", "inputs": [20]},
        "EMA_50": {"name": "EMA", "inputs": [50]},
        "EMA_200": {"name": "EMA", "inputs": [200]},
        "RSI": {"name": "RSI", "inputs": [14]},
        "Volume": {"name": "Volume", "inputs": []},
        "MACD": {"name": "MACD", "inputs": [12, 26, 9]},
        "BB": {"name": "BB", "inputs": [20, 2]},  # Bollinger Bands
        "ATR": {"name": "ATR", "inputs": [14]},
    }

    # Default Indicators per Asset Type
    DEFAULT_INDICATORS_INDICES = ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"]
    DEFAULT_INDICATORS_FOREX = ["EMA_20", "EMA_50", "RSI", "Volume"]

    # Trigger Types
    TRIGGER_TYPES = [
        "manual",      # User-initiated chart generation
        "report",      # Automated report generation
        "setup",       # Trading setup detected
        "analysis",    # Technical analysis request
        "monitoring",  # Regular monitoring
        "alert",       # Alert triggered
    ]

    # Chart Snapshot Retention
    CHART_RETENTION_DAYS = 60  # chart-img.com retention period

    @classmethod
    def get_indicator_config(cls, indicator_name: str) -> Dict:
        """
        Get chart-img.com API config for an indicator

        Args:
            indicator_name: Our internal indicator name (e.g., "EMA_20")

        Returns:
            Dict with "name" and "inputs" for API request

        Example:
            >>> ChartImgConfig.get_indicator_config("EMA_20")
            {"name": "EMA", "inputs": [20]}
        """
        return cls.INDICATOR_MAPPING.get(indicator_name, {})

    @classmethod
    def get_indicators_for_api(cls, indicator_names: List[str]) -> List[Dict]:
        """
        Convert list of indicator names to API format

        Args:
            indicator_names: List of our internal indicator names

        Returns:
            List of dicts for chart-img.com API "studies" parameter

        Example:
            >>> ChartImgConfig.get_indicators_for_api(["EMA_20", "RSI"])
            [{"name": "EMA", "inputs": [20]}, {"name": "RSI", "inputs": [14]}]
        """
        indicators = []
        for name in indicator_names:
            config = cls.get_indicator_config(name)
            if config:
                indicators.append(config)
        return indicators

    @classmethod
    def is_valid_timeframe(cls, timeframe: str) -> bool:
        """Check if timeframe is supported"""
        return timeframe in cls.SUPPORTED_TIMEFRAMES

    @classmethod
    def get_daily_limit_remaining_percentage(cls, current_count: int) -> float:
        """Calculate percentage of daily limit remaining"""
        return 1.0 - (current_count / cls.RATE_LIMIT_DAILY)

    @classmethod
    def should_warn_rate_limit(cls, current_count: int) -> bool:
        """Check if we should warn about approaching rate limit"""
        return current_count >= (cls.RATE_LIMIT_DAILY * cls.RATE_LIMIT_WARNING_THRESHOLD)

    @classmethod
    def should_block_rate_limit(cls, current_count: int) -> bool:
        """Check if we should hard-stop due to rate limit"""
        return current_count >= (cls.RATE_LIMIT_DAILY * cls.RATE_LIMIT_HARD_STOP_THRESHOLD)


# Export singleton instance
config = ChartImgConfig()
