#!/usr/bin/env python3
"""
Test script for MarketDataFetcher

Usage:
    python test_fetcher.py

Make sure to set TWELVE_DATA_API_KEY, SUPABASE_URL, and SUPABASE_SERVICE_KEY
in your .env file before running.
"""

import logging
from market_data_fetcher import (
    MarketDataFetcher,
    fetch_and_save,
    RateLimitError,
    SymbolNotFoundError,
    APIError
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_fetch_time_series():
    """Test fetching time series data"""
    logger.info("=" * 60)
    logger.info("TEST: Fetching time series data")
    logger.info("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        # Fetch DAX 1h data
        candles = fetcher.fetch_time_series("DAX", "1h", outputsize=10)

        logger.info(f"✓ Successfully fetched {len(candles)} candles")
        if candles:
            logger.info(f"  First candle: {candles[0]}")
            logger.info(f"  Last candle: {candles[-1]}")

        return True

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return False


def test_fetch_quote():
    """Test fetching current quote"""
    logger.info("=" * 60)
    logger.info("TEST: Fetching current quote")
    logger.info("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        # Fetch DAX quote
        quote = fetcher.fetch_quote("DAX")

        logger.info(f"✓ Successfully fetched quote")
        logger.info(f"  Symbol: {quote.get('symbol')}")
        logger.info(f"  Close: {quote.get('close')}")
        logger.info(f"  Change: {quote.get('percent_change')}%")

        return True

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return False


def test_save_to_database():
    """Test saving data to database"""
    logger.info("=" * 60)
    logger.info("TEST: Saving data to database")
    logger.info("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        # Fetch data
        candles = fetcher.fetch_time_series("DAX", "1h", outputsize=10)

        if not candles:
            logger.warning("No candles to save")
            return False

        # Save to database
        count = fetcher.save_to_database("DAX", "1h", candles)

        logger.info(f"✓ Successfully saved {count} candles to database")

        return True

    except SymbolNotFoundError as e:
        logger.error(f"✗ Symbol not found: {str(e)}")
        logger.info("  Make sure to run migration 003_market_data_schema.sql first!")
        return False

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return False


def test_convenience_function():
    """Test convenience function fetch_and_save()"""
    logger.info("=" * 60)
    logger.info("TEST: Convenience function fetch_and_save()")
    logger.info("=" * 60)

    try:
        # Fetch and save in one call
        count = fetch_and_save("NDX", "1h", 10)

        logger.info(f"✓ Successfully fetched and saved {count} candles")

        return True

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return False


def test_api_usage():
    """Test checking API usage"""
    logger.info("=" * 60)
    logger.info("TEST: Checking API usage")
    logger.info("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        usage = fetcher.get_api_usage()

        logger.info(f"✓ API Usage:")
        logger.info(f"  Current usage: {usage.get('current_usage')}")
        logger.info(f"  Plan limit: {usage.get('plan_limit')}")
        logger.info(f"  Plan: {usage.get('plan_name')}")

        return True

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")
        return False


def test_error_handling():
    """Test error handling"""
    logger.info("=" * 60)
    logger.info("TEST: Error handling")
    logger.info("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        # Try to fetch non-existent symbol
        try:
            candles = fetcher.fetch_time_series("INVALID_SYMBOL_XYZ", "1h", 10)
            logger.error("✗ Should have raised an error for invalid symbol")
            return False
        except APIError as e:
            logger.info(f"✓ Correctly caught APIError: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"✗ Unexpected error: {str(e)}")
        return False


def main():
    """Run all tests"""
    logger.info("")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 10 + "MarketDataFetcher Test Suite" + " " * 20 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("")

    tests = [
        ("Fetch Time Series", test_fetch_time_series),
        ("Fetch Quote", test_fetch_quote),
        ("Save to Database", test_save_to_database),
        ("Convenience Function", test_convenience_function),
        ("API Usage", test_api_usage),
        ("Error Handling", test_error_handling),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {str(e)}")
            results.append((name, False))

        logger.info("")

    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status} - {name}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
