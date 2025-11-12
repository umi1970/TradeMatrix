#!/usr/bin/env python3
"""
Test OHLC Fetcher
Quick test to verify OHLC fetching works
"""

import sys
sys.path.insert(0, 'src')

from src.ohlc_fetcher import OHLCFetcher

if __name__ == "__main__":
    print("Testing OHLC Fetcher...")
    print("=" * 70)

    fetcher = OHLCFetcher()
    result = fetcher.fetch_all_ohlc()

    print("\n" + "=" * 70)
    print("Test Result:")
    print(f"  Success: {result['success']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Symbols: {', '.join(result['symbols_processed'])}")
    print("=" * 70)

    if result['success'] > 0:
        print("\n✅ OHLC Fetcher working!")
        sys.exit(0)
    else:
        print("\n❌ OHLC Fetcher failed!")
        sys.exit(1)
