#!/usr/bin/env python3
"""
Example Usage of ChartGenerator Service

This script demonstrates various use cases for the ChartGenerator.

Run:
    python example_chart_usage.py
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chart_generator import ChartGenerator
from exceptions.chart_errors import (
    RateLimitError,
    ChartGenerationError,
    SymbolNotFoundError,
    InvalidTimeframeError,
)


def example_1_generate_chart():
    """Example 1: Generate a chart (basic usage)"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Generate Chart (Basic)")
    print("="*60 + "\n")

    generator = ChartGenerator()

    # Get DAX symbol ID from database (replace with actual UUID)
    # For demo purposes, we'll use a placeholder
    symbol_id = "replace-with-actual-uuid-from-database"

    try:
        result = generator.generate_chart(
            symbol_id=symbol_id,
            timeframe="4h",
            trigger_type="manual"
        )

        print("✅ Chart generated successfully!")
        print(f"   Chart URL: {result['chart_url']}")
        print(f"   Snapshot ID: {result['snapshot_id']}")
        print(f"   From cache: {result['cached']}")
        print(f"   Generated at: {result['generated_at']}")

    except SymbolNotFoundError as e:
        print(f"❌ Symbol not found: {e}")
        print("   Note: Replace 'symbol_id' with actual UUID from database")

    except ChartGenerationError as e:
        print(f"❌ Error: {e}")


def example_2_check_usage():
    """Example 2: Check API usage statistics"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Check API Usage")
    print("="*60 + "\n")

    generator = ChartGenerator()
    stats = generator.get_usage_stats()

    print("📊 API Usage Statistics:")
    print(f"   Requests today: {stats['requests_today']}/{stats['limit_daily']}")
    print(f"   Remaining: {stats['remaining']}")
    print(f"   Percentage used: {stats['percentage_used']:.1f}%")
    print(f"   Warning threshold: {stats['warning_threshold']}")
    print(f"   Hard stop threshold: {stats['hard_stop_threshold']}")
    print(f"   Date: {stats['date']}")

    # Check if approaching limit
    if stats['percentage_used'] >= 80:
        print("\n   ⚠️  WARNING: Approaching rate limit!")
    elif stats['percentage_used'] >= 95:
        print("\n   🚨 CRITICAL: Rate limit nearly exhausted!")
    else:
        print("\n   ✅ Usage healthy")


def example_3_get_latest_chart():
    """Example 3: Get latest chart without generating new one"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Get Latest Chart (No API Call)")
    print("="*60 + "\n")

    generator = ChartGenerator()
    symbol_id = "replace-with-actual-uuid-from-database"
    timeframe = "4h"

    chart_url = generator.get_latest_chart_url(symbol_id, timeframe)

    if chart_url:
        print(f"✅ Found latest chart: {chart_url}")
    else:
        print("ℹ️  No chart found. Generate one first.")


def example_4_force_refresh():
    """Example 4: Force refresh (skip cache)"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Force Refresh (Skip Cache)")
    print("="*60 + "\n")

    generator = ChartGenerator()
    symbol_id = "replace-with-actual-uuid-from-database"

    try:
        result = generator.generate_chart(
            symbol_id=symbol_id,
            timeframe="4h",
            trigger_type="manual",
            force_refresh=True  # Skip cache, always generate new
        )

        print("✅ Fresh chart generated!")
        print(f"   Chart URL: {result['chart_url']}")
        print(f"   Note: Cache was bypassed")

    except ChartGenerationError as e:
        print(f"❌ Error: {e}")


def example_5_multiple_timeframes():
    """Example 5: Generate charts for multiple timeframes"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Multiple Timeframes")
    print("="*60 + "\n")

    generator = ChartGenerator()
    symbol_id = "replace-with-actual-uuid-from-database"
    timeframes = ["1h", "4h", "1d"]

    print("Generating charts for DAX at multiple timeframes...\n")

    for timeframe in timeframes:
        try:
            result = generator.generate_chart(
                symbol_id=symbol_id,
                timeframe=timeframe,
                trigger_type="analysis"
            )

            cached_status = "cached" if result['cached'] else "new"
            print(f"✅ {timeframe:4} - {cached_status:6} - {result['chart_url']}")

        except ChartGenerationError as e:
            print(f"❌ {timeframe:4} - Error: {e}")


def example_6_handle_rate_limit():
    """Example 6: Gracefully handle rate limit"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Handle Rate Limit")
    print("="*60 + "\n")

    generator = ChartGenerator()
    symbol_id = "replace-with-actual-uuid-from-database"

    try:
        result = generator.generate_chart(
            symbol_id=symbol_id,
            timeframe="4h",
            trigger_type="manual"
        )

        print("✅ Chart generated!")

    except RateLimitError as e:
        print(f"🚨 Rate limit exceeded!")
        print(f"   Current: {e.current_count}/{e.limit} requests")
        print(f"   Resets at: {e.reset_time}")
        print(f"\n   💡 Tip: Use cache or wait until midnight UTC")

        # Fallback: Get latest chart from database
        chart_url = generator.get_latest_chart_url(symbol_id, "4h")
        if chart_url:
            print(f"\n   ℹ️  Using latest chart from database:")
            print(f"      {chart_url}")

    except ChartGenerationError as e:
        print(f"❌ Error: {e}")


def example_7_cleanup_expired():
    """Example 7: Cleanup expired snapshots"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Cleanup Expired Snapshots")
    print("="*60 + "\n")

    generator = ChartGenerator()

    deleted_count = generator.cleanup_expired_snapshots()

    print(f"🧹 Cleanup complete!")
    print(f"   Deleted: {deleted_count} expired snapshots")


def example_8_error_handling():
    """Example 8: Comprehensive error handling"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Error Handling")
    print("="*60 + "\n")

    generator = ChartGenerator()

    # Test various error scenarios
    test_cases = [
        {
            'name': 'Invalid Symbol',
            'symbol_id': '00000000-0000-0000-0000-000000000000',
            'timeframe': '4h',
            'expected_error': SymbolNotFoundError
        },
        {
            'name': 'Invalid Timeframe',
            'symbol_id': 'replace-with-actual-uuid',
            'timeframe': '999h',
            'expected_error': InvalidTimeframeError
        },
    ]

    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        try:
            result = generator.generate_chart(
                symbol_id=test['symbol_id'],
                timeframe=test['timeframe']
            )
            print(f"   ❌ Expected error but got success: {result['chart_url']}")

        except test['expected_error'] as e:
            print(f"   ✅ Correctly caught {type(e).__name__}")
            print(f"      Message: {e.message}")

        except ChartGenerationError as e:
            print(f"   ⚠️  Got different error: {type(e).__name__}")
            print(f"      Message: {e.message}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print(" ChartGenerator Service - Usage Examples")
    print("="*60)

    examples = [
        ("Generate Chart (Basic)", example_1_generate_chart),
        ("Check API Usage", example_2_check_usage),
        ("Get Latest Chart", example_3_get_latest_chart),
        ("Force Refresh", example_4_force_refresh),
        ("Multiple Timeframes", example_5_multiple_timeframes),
        ("Handle Rate Limit", example_6_handle_rate_limit),
        ("Cleanup Expired", example_7_cleanup_expired),
        ("Error Handling", example_8_error_handling),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nNote: Update 'symbol_id' with actual UUID from database")
    print("      You can get symbol IDs by querying: SELECT id, symbol FROM symbols;")

    # Run example 2 (usage stats) as it doesn't require symbol_id
    print("\n" + "="*60)
    print("Running Example 2 (Safe to run without DB):")
    print("="*60)
    example_2_check_usage()

    print("\n" + "="*60)
    print("To run other examples, update symbol_id and run:")
    print("  python example_chart_usage.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
