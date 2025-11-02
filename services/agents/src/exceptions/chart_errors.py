#!/usr/bin/env python3
"""
Custom Exception Classes for Chart Generation
Provides specific error types for different failure scenarios
"""


class ChartGenerationError(Exception):
    """Base exception for chart generation errors"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class RateLimitError(ChartGenerationError):
    """
    Raised when API rate limit is exceeded

    Attributes:
        current_count: Current number of requests today
        limit: Maximum allowed requests
        reset_time: When the limit resets
    """

    def __init__(self, current_count: int, limit: int, reset_time: str = None):
        details = {
            'current_count': current_count,
            'limit': limit,
            'reset_time': reset_time,
            'percentage_used': (current_count / limit) * 100 if limit > 0 else 0,
        }
        message = f"Rate limit exceeded: {current_count}/{limit} requests used"
        super().__init__(message, details)
        self.current_count = current_count
        self.limit = limit
        self.reset_time = reset_time


class SymbolNotFoundError(ChartGenerationError):
    """
    Raised when a symbol is not found in the database
    or chart generation is not enabled for the symbol

    Attributes:
        symbol_id: The UUID of the symbol that wasn't found
        symbol: The symbol ticker (if available)
    """

    def __init__(self, symbol_id: str, symbol: str = None):
        details = {
            'symbol_id': symbol_id,
            'symbol': symbol,
        }
        message = f"Symbol not found or chart not enabled: {symbol or symbol_id}"
        super().__init__(message, details)
        self.symbol_id = symbol_id
        self.symbol = symbol


class InvalidTimeframeError(ChartGenerationError):
    """
    Raised when an invalid or unsupported timeframe is provided

    Attributes:
        timeframe: The invalid timeframe provided
        supported_timeframes: List of valid timeframes
    """

    def __init__(self, timeframe: str, supported_timeframes: list = None):
        details = {
            'timeframe': timeframe,
            'supported_timeframes': supported_timeframes or [],
        }
        message = f"Invalid timeframe: {timeframe}"
        if supported_timeframes:
            message += f" | Supported: {', '.join(supported_timeframes)}"
        super().__init__(message, details)
        self.timeframe = timeframe
        self.supported_timeframes = supported_timeframes


class ChartAPIError(ChartGenerationError):
    """
    Raised when chart-img.com API returns an error

    Attributes:
        status_code: HTTP status code from API
        response_body: Raw response from API
        api_error_message: Error message from API
    """

    def __init__(self, status_code: int, response_body: str = None, api_error_message: str = None):
        details = {
            'status_code': status_code,
            'response_body': response_body,
            'api_error_message': api_error_message,
        }
        message = f"chart-img.com API error: HTTP {status_code}"
        if api_error_message:
            message += f" - {api_error_message}"
        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body
        self.api_error_message = api_error_message


class ChartCacheError(ChartGenerationError):
    """
    Raised when Redis cache operations fail

    Attributes:
        operation: The cache operation that failed (get, set, delete, etc.)
        cache_key: The Redis key involved
    """

    def __init__(self, operation: str, cache_key: str = None, original_error: Exception = None):
        details = {
            'operation': operation,
            'cache_key': cache_key,
            'original_error': str(original_error) if original_error else None,
        }
        message = f"Cache {operation} operation failed"
        if cache_key:
            message += f" for key: {cache_key}"
        super().__init__(message, details)
        self.operation = operation
        self.cache_key = cache_key
        self.original_error = original_error
