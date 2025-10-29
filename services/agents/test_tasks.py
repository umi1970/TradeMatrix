#!/usr/bin/env python3
"""
Test Script for Celery Tasks
Run individual tasks manually for testing
"""

import sys
import os
from datetime import datetime

# Add API src to path
api_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../api/src'))
sys.path.insert(0, api_src_path)

# Must be after path setup
from src.tasks import (
    test_connection,
    historical_seed_task,
    realtime_pull_task,
    daily_close_task,
    calculate_pivots_task
)


def test_basic_connection():
    """Test 1: Basic Celery connection"""
    print("\n" + "="*60)
    print("TEST 1: Basic Celery Connection")
    print("="*60)

    try:
        result = test_connection.delay()
        output = result.get(timeout=10)
        print("✅ SUCCESS:", output)
        return True
    except Exception as e:
        print("❌ FAILED:", str(e))
        return False


def test_historical_seed():
    """Test 2: Historical data seeding"""
    print("\n" + "="*60)
    print("TEST 2: Historical Data Seed (DAX, 1h, 7 days)")
    print("="*60)

    try:
        result = historical_seed_task.delay("DAX", "1h", 7)
        output = result.get(timeout=60)
        print(f"✅ SUCCESS: Inserted {output} candles")
        return True
    except Exception as e:
        print("❌ FAILED:", str(e))
        return False


def test_realtime_pull():
    """Test 3: Real-time data pull"""
    print("\n" + "="*60)
    print("TEST 3: Real-time Data Pull (All Active Symbols)")
    print("="*60)

    try:
        result = realtime_pull_task.delay()
        output = result.get(timeout=120)

        print("\nResults:")
        for key, value in output.items():
            status = "✅" if value.get('success') else "❌"
            print(f"{status} {key}: {value}")

        return True
    except Exception as e:
        print("❌ FAILED:", str(e))
        return False


def test_daily_close():
    """Test 4: Daily close calculation"""
    print("\n" + "="*60)
    print("TEST 4: Daily Close Calculation")
    print("="*60)

    try:
        result = daily_close_task.delay()
        output = result.get(timeout=60)

        print("\nResults:")
        for symbol, data in output.items():
            if data.get('success'):
                print(f"✅ {symbol}:")
                print(f"   Y-High:  {data.get('y_high')}")
                print(f"   Y-Low:   {data.get('y_low')}")
                print(f"   Y-Close: {data.get('y_close')}")
            else:
                print(f"❌ {symbol}: {data.get('error')}")

        return True
    except Exception as e:
        print("❌ FAILED:", str(e))
        return False


def test_calculate_pivots():
    """Test 5: Pivot points calculation"""
    print("\n" + "="*60)
    print("TEST 5: Pivot Points Calculation")
    print("="*60)

    try:
        result = calculate_pivots_task.delay()
        output = result.get(timeout=60)

        print("\nResults:")
        for symbol, data in output.items():
            if data.get('success'):
                print(f"✅ {symbol}:")
                print(f"   Pivot: {data.get('pivot')}")
                print(f"   R2:    {data.get('r2')}")
                print(f"   R1:    {data.get('r1')}")
                print(f"   S1:    {data.get('s1')}")
                print(f"   S2:    {data.get('s2')}")
            else:
                print(f"❌ {symbol}: {data.get('error')}")

        return True
    except Exception as e:
        print("❌ FAILED:", str(e))
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print(" TradeMatrix.ai - Celery Tasks Test Suite")
    print("="*60)
    print(f" Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    tests = [
        ("Basic Connection", test_basic_connection),
        ("Historical Seed", test_historical_seed),
        ("Real-time Pull", test_realtime_pull),
        ("Daily Close", test_daily_close),
        ("Calculate Pivots", test_calculate_pivots),
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {str(e)}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {name}")

    print("\n" + "-"*60)
    print(f" Total: {passed}/{total} tests passed")
    print("="*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Celery tasks")
    parser.add_argument(
        "test",
        nargs="?",
        choices=["all", "connection", "seed", "realtime", "daily", "pivots"],
        default="all",
        help="Which test to run (default: all)"
    )

    args = parser.parse_args()

    if args.test == "all":
        run_all_tests()
    elif args.test == "connection":
        test_basic_connection()
    elif args.test == "seed":
        test_historical_seed()
    elif args.test == "realtime":
        test_realtime_pull()
    elif args.test == "daily":
        test_daily_close()
    elif args.test == "pivots":
        test_calculate_pivots()
