#!/usr/bin/env python3
"""
Example usage of MarketDataFetcher

This script demonstrates real-world usage scenarios for the MarketDataFetcher class.

Prerequisites:
1. Set environment variables in .env:
   - TWELVE_DATA_API_KEY
   - SUPABASE_URL
   - SUPABASE_SERVICE_KEY

2. Run database migration 003_market_data_schema.sql

3. Install dependencies:
   pip install -r requirements.txt
"""

import logging
from datetime import datetime, timedelta
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_basic_fetch_and_save():
    """
    Example 1: Basic fetch and save
    Fetch 100 1-hour candles for DAX and save to database
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Fetch and Save")
    print("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        # Fetch data
        logger.info("Fetching DAX 1h data...")
        candles = fetcher.fetch_time_series("DAX", "1h", outputsize=100)

        logger.info(f"Fetched {len(candles)} candles")
        logger.info(f"Latest candle: {candles[0]}")

        # Save to database
        logger.info("Saving to database...")
        count = fetcher.save_to_database("DAX", "1h", candles)

        logger.info(f"✓ Successfully saved {count} candles")

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")


def example_2_convenience_function():
    """
    Example 2: Using convenience function
    Fetch and save in one call
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Convenience Function")
    print("=" * 60)

    try:
        # Fetch and save multiple symbols
        symbols = ["DAX", "NDX", "DJI"]

        for symbol in symbols:
            logger.info(f"Processing {symbol}...")
            count = fetch_and_save(symbol, "1h", 50)
            logger.info(f"✓ {symbol}: Saved {count} candles")

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")


def example_3_current_quotes():
    """
    Example 3: Fetch current quotes
    Get real-time prices for multiple symbols
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Current Quotes")
    print("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        symbols = ["DAX", "NDX", "DJI", "EUR/USD"]

        logger.info("Fetching current quotes...\n")

        for symbol in symbols:
            quote = fetcher.fetch_quote(symbol)

            print(f"{symbol:12} | Close: {quote.get('close', 'N/A'):>10} | "
                  f"Change: {quote.get('percent_change', 'N/A'):>6}%")

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")


def example_4_historical_date_range():
    """
    Example 4: Fetch historical data with date range
    Get EUR/USD daily data for last 30 days
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Historical Date Range")
    print("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        logger.info(f"Fetching EUR/USD data from {start_date.date()} to {end_date.date()}...")

        candles = fetcher.fetch_time_series(
            symbol="EUR/USD",
            interval="1day",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            outputsize=5000
        )

        logger.info(f"✓ Fetched {len(candles)} daily candles")

        if candles:
            # Save to database
            count = fetcher.save_to_database("EUR/USD", "1day", candles)
            logger.info(f"✓ Saved {count} candles to database")

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")


def example_5_error_handling():
    """
    Example 5: Proper error handling
    Demonstrate handling different error types
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Error Handling")
    print("=" * 60)

    fetcher = MarketDataFetcher()

    # Test 1: Invalid symbol (API will return error or 404)
    print("\n1. Testing invalid symbol...")
    try:
        candles = fetcher.fetch_time_series("INVALID_XYZ", "1h", 10)
    except APIError as e:
        logger.info(f"✓ Correctly caught APIError: {e}")
    except Exception as e:
        logger.warning(f"Caught different error: {type(e).__name__}: {e}")

    # Test 2: Symbol not in database
    print("\n2. Testing symbol not in database...")
    try:
        # This will work for API fetch but fail on save
        candles = fetcher.fetch_time_series("AAPL", "1h", 10)
        if candles:
            fetcher.save_to_database("AAPL", "1h", candles)
    except SymbolNotFoundError as e:
        logger.info(f"✓ Correctly caught SymbolNotFoundError: {e}")
    except Exception as e:
        logger.warning(f"Caught different error: {type(e).__name__}: {e}")


def example_6_batch_processing():
    """
    Example 6: Batch processing
    Fetch and process multiple symbols efficiently
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Batch Processing")
    print("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        # Define symbols and intervals to fetch
        jobs = [
            ("DAX", "5min", 50),
            ("DAX", "1h", 100),
            ("NDX", "1h", 100),
            ("DJI", "1h", 100),
            ("EUR/USD", "1h", 50),
        ]

        logger.info(f"Processing {len(jobs)} jobs...\n")

        results = []
        for symbol, interval, outputsize in jobs:
            try:
                logger.info(f"Fetching {symbol} {interval}...")

                candles = fetcher.fetch_time_series(symbol, interval, outputsize)
                count = fetcher.save_to_database(symbol, interval, candles)

                results.append((symbol, interval, count, "Success"))
                logger.info(f"✓ {symbol} {interval}: {count} candles saved")

            except Exception as e:
                results.append((symbol, interval, 0, str(e)))
                logger.error(f"✗ {symbol} {interval}: {str(e)}")

        # Summary
        print("\n" + "-" * 60)
        print("BATCH PROCESSING SUMMARY")
        print("-" * 60)
        print(f"{'Symbol':<10} {'Interval':<10} {'Saved':<10} {'Status':<20}")
        print("-" * 60)

        for symbol, interval, count, status in results:
            status_short = status if len(status) < 20 else status[:17] + "..."
            print(f"{symbol:<10} {interval:<10} {count:<10} {status_short:<20}")

        print("-" * 60)

    except Exception as e:
        logger.error(f"✗ Batch processing error: {str(e)}")


def example_7_api_usage_monitoring():
    """
    Example 7: Monitor API usage
    Check remaining API credits
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 7: API Usage Monitoring")
    print("=" * 60)

    try:
        fetcher = MarketDataFetcher()

        logger.info("Checking API usage...")
        usage = fetcher.get_api_usage()

        print(f"\nAPI Usage Information:")
        print(f"  Plan: {usage.get('plan_name', 'Unknown')}")
        print(f"  Current Usage: {usage.get('current_usage', 'Unknown')}")
        print(f"  Plan Limit: {usage.get('plan_limit', 'Unknown')}")

        # Calculate percentage
        try:
            current = int(usage.get('current_usage', 0))
            limit = int(usage.get('plan_limit', 800))
            percentage = (current / limit) * 100
            print(f"  Usage: {percentage:.1f}%")

            if percentage > 80:
                logger.warning("⚠️  API usage is above 80%! Consider upgrading your plan.")
            else:
                logger.info("✓ API usage is within limits")

        except (ValueError, ZeroDivisionError):
            logger.warning("Could not calculate usage percentage")

    except Exception as e:
        logger.error(f"✗ Error: {str(e)}")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MarketDataFetcher Usage Examples" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")

    examples = [
        example_1_basic_fetch_and_save,
        example_2_convenience_function,
        example_3_current_quotes,
        example_4_historical_date_range,
        example_5_error_handling,
        example_6_batch_processing,
        example_7_api_usage_monitoring,
    ]

    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except KeyboardInterrupt:
            print("\n\nExecution interrupted by user")
            break
        except Exception as e:
            logger.error(f"Example {i} crashed: {str(e)}")

        # Add separator between examples
        if i < len(examples):
            input("\n[Press Enter to continue to next example...]")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
