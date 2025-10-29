"""
Market Data Fetcher for Twelve Data API Integration

This module provides a class to fetch OHLCV data from Twelve Data API
and store it in the Supabase database.

Features:
- Fetch time series (OHLCV) data
- Fetch current quotes
- Handle rate limiting (800 req/day on free tier)
- Automatic retry with exponential backoff
- Save data to Supabase with duplicate handling
- Type-safe with proper error handling

Author: TradeMatrix.ai Development Team
Date: 2025-10-29
"""

import os
import time
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from supabase import Client

from config.supabase import get_supabase_admin, get_settings
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Cache for API responses (TTL: 60 seconds)
_price_cache = TTLCache(maxsize=100, ttl=60)


class MarketDataFetcherError(Exception):
    """Base exception for MarketDataFetcher errors"""
    pass


class RateLimitError(MarketDataFetcherError):
    """Raised when API rate limit is exceeded"""
    pass


class SymbolNotFoundError(MarketDataFetcherError):
    """Raised when symbol is not found in database"""
    pass


class APIError(MarketDataFetcherError):
    """Raised when API returns an error"""
    pass


class MarketDataFetcher:
    """
    Fetches market data from Twelve Data API and stores it in Supabase.

    Usage:
        fetcher = MarketDataFetcher()
        candles = fetcher.fetch_time_series("DAX", "1h", outputsize=100)
        fetcher.save_to_database("DAX", "1h", candles)
    """

    # Twelve Data API configuration
    BASE_URL = "https://api.twelvedata.com"
    DEFAULT_TIMEZONE = "Europe/Berlin"

    # Rate limiting configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    RATE_LIMIT_DELAY = 60  # seconds to wait after rate limit

    def __init__(
        self,
        api_key: Optional[str] = None,
        supabase_client: Optional[Client] = None
    ):
        """
        Initialize MarketDataFetcher.

        Args:
            api_key: Twelve Data API key (defaults to TWELVE_DATA_API_KEY env var)
            supabase_client: Supabase client (defaults to admin client)
        """
        settings = get_settings()

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key:
            logger.warning("TWELVE_DATA_API_KEY not set in environment")

        # Get Supabase client (use admin to bypass RLS)
        self.supabase = supabase_client or get_supabase_admin()

        # Request counter for rate limiting
        self.request_count = 0
        self.last_request_time = None

    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Twelve Data API with retry logic.

        Args:
            endpoint: API endpoint (e.g., "time_series")
            params: Query parameters
            retry_count: Current retry attempt number

        Returns:
            JSON response as dictionary

        Raises:
            RateLimitError: When rate limit is exceeded
            APIError: When API returns an error
            MarketDataFetcherError: For other errors
        """
        url = f"{self.BASE_URL}/{endpoint}"
        params["apikey"] = self.api_key

        try:
            # Rate limiting: add small delay between requests
            if self.last_request_time:
                elapsed = time.time() - self.last_request_time
                if elapsed < 1.0:  # Minimum 1 second between requests
                    time.sleep(1.0 - elapsed)

            # Make request
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                self.last_request_time = time.time()
                self.request_count += 1

                # Check for rate limiting (429)
                if response.status_code == 429:
                    if retry_count < self.MAX_RETRIES:
                        logger.warning(f"Rate limit exceeded. Waiting {self.RATE_LIMIT_DELAY}s...")
                        time.sleep(self.RATE_LIMIT_DELAY)
                        return self._make_request(endpoint, params, retry_count + 1)
                    else:
                        raise RateLimitError(
                            f"Rate limit exceeded after {self.MAX_RETRIES} retries. "
                            f"Free tier limit: 800 requests/day."
                        )

                # Check for other HTTP errors
                if response.status_code == 404:
                    raise APIError(f"Symbol not found: {params.get('symbol')}")

                if response.status_code >= 500:
                    if retry_count < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY * (2 ** retry_count)  # Exponential backoff
                        logger.warning(f"Server error ({response.status_code}). Retrying in {delay}s...")
                        time.sleep(delay)
                        return self._make_request(endpoint, params, retry_count + 1)
                    else:
                        raise APIError(
                            f"Server error {response.status_code} after {self.MAX_RETRIES} retries"
                        )

                response.raise_for_status()

                # Parse JSON response
                data = response.json()

                # Check for API error in response
                if "status" in data and data["status"] == "error":
                    error_msg = data.get("message", "Unknown API error")
                    if "rate limit" in error_msg.lower():
                        raise RateLimitError(error_msg)
                    else:
                        raise APIError(f"API error: {error_msg}")

                return data

        except httpx.HTTPError as e:
            raise MarketDataFetcherError(f"HTTP error: {str(e)}")
        except Exception as e:
            if isinstance(e, (RateLimitError, APIError)):
                raise
            raise MarketDataFetcherError(f"Unexpected error: {str(e)}")

    def fetch_time_series(
        self,
        symbol: str,
        interval: str = "1h",
        outputsize: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timezone: str = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV time series data from Twelve Data API.

        Args:
            symbol: Trading symbol (e.g., "DAX", "EUR/USD")
            interval: Time interval (e.g., "1min", "5min", "1h", "1day")
            outputsize: Number of data points (default: 100, max: 5000)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            timezone: Timezone for timestamps (default: Europe/Berlin)

        Returns:
            List of candle dictionaries with keys:
            - datetime: ISO timestamp
            - open: Opening price
            - high: High price
            - low: Low price
            - close: Closing price
            - volume: Trading volume

        Example:
            >>> fetcher = MarketDataFetcher()
            >>> candles = fetcher.fetch_time_series("DAX", "1h", 100)
            >>> print(candles[0])
            {
                'datetime': '2025-10-29 14:00:00',
                'open': '19250.5',
                'high': '19280.3',
                'low': '19240.1',
                'close': '19270.8',
                'volume': '12450'
            }
        """
        if timezone is None:
            timezone = self.DEFAULT_TIMEZONE

        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "format": "JSON",
            "timezone": timezone
        }

        # Add optional date range
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        logger.info(f"Fetching {symbol} {interval} data (outputsize={outputsize})...")

        response = self._make_request("time_series", params)

        # Extract values from response
        values = response.get("values", [])
        if not values:
            logger.warning(f"No data returned for {symbol} {interval}")
            return []

        logger.info(f"Fetched {len(values)} candles for {symbol}")
        return values

    def fetch_current_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current price for a symbol

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with current price and metadata
        """
        params = {
            "symbol": symbol,
            "apikey": self.api_key
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.BASE_URL}/price", params=params)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Fetched current price for {symbol}: {data.get('price')}")
                return data

        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {str(e)}")
            raise

    def fetch_quote(self, symbol: str, timezone: str = None) -> Dict[str, Any]:
        """
        Get current quote for a symbol.

        Args:
            symbol: Trading symbol (e.g., "DAX", "EUR/USD")
            timezone: Timezone for timestamps (default: Europe/Berlin)

        Returns:
            Dictionary with quote data:
            - symbol: Symbol name
            - open: Opening price
            - high: High price
            - low: Low price
            - close: Current/closing price
            - volume: Trading volume
            - datetime: Timestamp
            - percent_change: Percentage change
            - change: Absolute change

        Example:
            >>> fetcher = MarketDataFetcher()
            >>> quote = fetcher.fetch_quote("DAX")
            >>> print(f"DAX current price: {quote['close']}")
        """
        if timezone is None:
            timezone = self.DEFAULT_TIMEZONE

        params = {
            "symbol": symbol,
            "timezone": timezone
        }

        logger.info(f"Fetching quote for {symbol}...")

        response = self._make_request("quote", params)

        # Validate response
        if not response:
            raise APIError(f"Empty response for quote: {symbol}")

        return response

    def _get_symbol_id(self, symbol: str, vendor: str = "twelve_data") -> str:
        """
        Get symbol_id from market_symbols table.

        Args:
            symbol: Symbol name (e.g., "DAX")
            vendor: Data vendor (default: "twelve_data")

        Returns:
            UUID of the symbol

        Raises:
            SymbolNotFoundError: If symbol is not found in database
        """
        try:
            result = self.supabase.table("market_symbols") \
                .select("id") \
                .eq("symbol", symbol) \
                .eq("vendor", vendor) \
                .execute()

            if not result.data or len(result.data) == 0:
                raise SymbolNotFoundError(
                    f"Symbol '{symbol}' not found in market_symbols table. "
                    f"Please add it first using the seed data migration."
                )

            return result.data[0]["id"]

        except Exception as e:
            if isinstance(e, SymbolNotFoundError):
                raise
            raise MarketDataFetcherError(f"Database error: {str(e)}")

    def save_to_database(
        self,
        symbol: str,
        interval: str,
        candles: List[Dict[str, Any]],
        vendor: str = "twelve_data"
    ) -> int:
        """
        Save OHLCV candles to Supabase database.

        Args:
            symbol: Symbol name (e.g., "DAX")
            interval: Timeframe (e.g., "1h", "1d")
            candles: List of candle dictionaries from fetch_time_series()
            vendor: Data vendor (default: "twelve_data")

        Returns:
            Number of candles successfully saved

        Raises:
            SymbolNotFoundError: If symbol is not in database
            MarketDataFetcherError: For other errors

        Example:
            >>> fetcher = MarketDataFetcher()
            >>> candles = fetcher.fetch_time_series("DAX", "1h", 100)
            >>> count = fetcher.save_to_database("DAX", "1h", candles)
            >>> print(f"Saved {count} candles")
        """
        if not candles:
            logger.info("No candles to save")
            return 0

        # Get symbol_id
        symbol_id = self._get_symbol_id(symbol, vendor)

        logger.info(f"Saving {len(candles)} candles for {symbol} ({interval})...")

        # Prepare records for insertion
        records = []
        for candle in candles:
            try:
                # Parse timestamp (Twelve Data format: "YYYY-MM-DD HH:MM:SS")
                ts = candle["datetime"]
                if not ts.endswith("Z") and "+" not in ts:
                    # Add timezone if not present (assume UTC from API)
                    ts = f"{ts}+00:00"

                record = {
                    "ts": ts,
                    "symbol_id": symbol_id,
                    "timeframe": interval,
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                    "volume": int(candle.get("volume", 0))
                }
                records.append(record)

            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid candle: {e}")
                continue

        if not records:
            logger.warning("No valid records to save")
            return 0

        # Insert records with upsert (ignore duplicates)
        try:
            # Use upsert to handle duplicates gracefully
            result = self.supabase.table("ohlc") \
                .upsert(
                    records,
                    on_conflict="symbol_id,timeframe,ts",
                    ignore_duplicates=True
                ) \
                .execute()

            saved_count = len(result.data) if result.data else 0
            logger.info(f"Successfully saved {saved_count} candles to database")

            return saved_count

        except Exception as e:
            raise MarketDataFetcherError(f"Database insert error: {str(e)}")

    def get_api_usage(self) -> Dict[str, Any]:
        """
        Get API usage information from Twelve Data.

        Returns:
            Dictionary with usage info:
            - current_usage: Number of requests made today
            - plan_limit: Daily request limit
            - plan_name: Plan type

        Example:
            >>> fetcher = MarketDataFetcher()
            >>> usage = fetcher.get_api_usage()
            >>> print(f"Used {usage['current_usage']}/{usage['plan_limit']} requests")
        """
        params = {}

        logger.info("Fetching API usage...")

        response = self._make_request("api_usage", params)

        return response

    def fetch_historical_range(
        self,
        symbol: str,
        interval: str,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical data for the last N days

        Args:
            symbol: Trading symbol
            interval: Time interval
            days_back: Number of days to fetch

        Returns:
            List of OHLCV candles
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        data = self.fetch_time_series(
            symbol=symbol,
            interval=interval,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            outputsize=5000  # Max for date range queries
        )

        return data.get("values", [])


    def normalize_candle(self, candle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a candle from Twelve Data format to our internal format

        Args:
            candle: Raw candle from API

        Returns:
            Normalized candle dictionary
        """
        return {
            "timestamp": candle.get("datetime"),
            "open": float(candle.get("open", 0)),
            "high": float(candle.get("high", 0)),
            "low": float(candle.get("low", 0)),
            "close": float(candle.get("close", 0)),
            "volume": int(candle.get("volume", 0))
        }

    def batch_fetch_symbols(
        self,
        symbols: List[str],
        interval: str = "1h",
        outputsize: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch data for multiple symbols.

        Args:
            symbols: List of trading symbols
            interval: Time interval
            outputsize: Number of data points per symbol

        Returns:
            Dictionary mapping symbol to list of candles
        """
        results = {}

        for symbol in symbols:
            try:
                data = self.fetch_time_series(
                    symbol=symbol,
                    interval=interval,
                    outputsize=outputsize
                )
                results[symbol] = data

            except Exception as e:
                logger.error(f"Error fetching {symbol}: {str(e)}")
                results[symbol] = []

        return results

    def save_current_price(
        self,
        symbol: str,
        quote_data: Dict[str, Any],
        vendor: str = "twelve_data"
    ) -> bool:
        """
        Save or update current price in the current_prices table.

        Args:
            symbol: Symbol name (e.g., "DAX")
            quote_data: Quote data from fetch_quote()
            vendor: Data vendor (default: "twelve_data")

        Returns:
            True if successful, False otherwise

        Example:
            >>> fetcher = MarketDataFetcher()
            >>> quote = fetcher.fetch_quote("DAX")
            >>> success = fetcher.save_current_price("DAX", quote)
        """
        try:
            # Get symbol_id
            symbol_id = self._get_symbol_id(symbol, vendor)

            # Parse quote data
            price = float(quote_data.get("close", 0))
            if price <= 0:
                logger.error(f"Invalid price for {symbol}: {price}")
                return False

            # Calculate change metrics
            previous_close = float(quote_data.get("previous_close", 0))
            change = None
            change_percent = None

            if previous_close and previous_close > 0:
                change = price - previous_close
                change_percent = (change / previous_close) * 100

            # Prepare record
            record = {
                "symbol_id": symbol_id,
                "price": price,
                "open": float(quote_data.get("open", 0)) or None,
                "high": float(quote_data.get("high", 0)) or None,
                "low": float(quote_data.get("low", 0)) or None,
                "previous_close": previous_close if previous_close > 0 else None,
                "change": change,
                "change_percent": change_percent,
                "volume": int(quote_data.get("volume", 0)) if quote_data.get("volume") else None,
                "exchange": quote_data.get("exchange"),
                "currency": quote_data.get("currency", "USD"),
                "is_market_open": quote_data.get("is_market_open", False),
                "price_timestamp": quote_data.get("datetime"),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Upsert record (insert or update)
            result = self.supabase.table("current_prices") \
                .upsert(
                    record,
                    on_conflict="symbol_id"
                ) \
                .execute()

            if result.data:
                logger.info(f"Saved current price for {symbol}: {price}")
                return True
            else:
                logger.warning(f"No data returned when saving price for {symbol}")
                return False

        except Exception as e:
            logger.error(f"Error saving current price for {symbol}: {str(e)}")
            return False

    def fetch_and_save_current_price(
        self,
        symbol: str,
        vendor: str = "twelve_data",
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch current quote and save to database (with caching).

        Args:
            symbol: Trading symbol
            vendor: Data vendor
            use_cache: Use cached response if available (default: True)

        Returns:
            Quote data dictionary or None on error

        Example:
            >>> fetcher = MarketDataFetcher()
            >>> quote = fetcher.fetch_and_save_current_price("DAX")
            >>> print(f"Current DAX price: {quote['close']}")
        """
        cache_key = f"{vendor}:{symbol}:quote"

        # Check cache
        if use_cache and cache_key in _price_cache:
            logger.debug(f"Using cached quote for {symbol}")
            return _price_cache[cache_key]

        try:
            # Fetch fresh quote
            quote = self.fetch_quote(symbol)

            if not quote:
                logger.error(f"Empty quote response for {symbol}")
                return None

            # Save to database
            self.save_current_price(symbol, quote, vendor)

            # Cache response
            _price_cache[cache_key] = quote

            return quote

        except Exception as e:
            logger.error(f"Error fetching and saving current price for {symbol}: {str(e)}")
            return None

    def batch_fetch_and_save_current_prices(
        self,
        symbols: List[str],
        vendor: str = "twelve_data",
        delay_between: float = 1.5
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch and save current prices for multiple symbols.

        Args:
            symbols: List of trading symbols
            vendor: Data vendor
            delay_between: Delay between requests in seconds (for rate limiting)

        Returns:
            Dictionary mapping symbol to quote data (or None on error)

        Example:
            >>> fetcher = MarketDataFetcher()
            >>> symbols = ["DAX", "NDX", "DJI"]
            >>> results = fetcher.batch_fetch_and_save_current_prices(symbols)
            >>> for symbol, quote in results.items():
            >>>     if quote:
            >>>         print(f"{symbol}: {quote['close']}")
        """
        results = {}

        for i, symbol in enumerate(symbols):
            try:
                # Add delay between requests (except for first request)
                if i > 0 and delay_between > 0:
                    time.sleep(delay_between)

                quote = self.fetch_and_save_current_price(symbol, vendor, use_cache=False)
                results[symbol] = quote

                logger.info(f"Processed {i+1}/{len(symbols)}: {symbol}")

            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                results[symbol] = None

        return results


# Convenience function for quick data fetching
def fetch_and_save(
    symbol: str,
    interval: str = "1h",
    outputsize: int = 100,
    api_key: Optional[str] = None
) -> int:
    """
    Convenience function to fetch and save market data in one call.

    Args:
        symbol: Trading symbol
        interval: Time interval
        outputsize: Number of candles to fetch
        api_key: Twelve Data API key (optional)

    Returns:
        Number of candles saved

    Example:
        >>> from core.market_data_fetcher import fetch_and_save
        >>> count = fetch_and_save("DAX", "1h", 100)
        >>> print(f"Saved {count} candles")
    """
    fetcher = MarketDataFetcher(api_key=api_key)
    candles = fetcher.fetch_time_series(symbol, interval, outputsize)
    return fetcher.save_to_database(symbol, interval, candles)
