#!/usr/bin/env python3
"""Test CSV Parser with real TradingView CSV"""

import sys
sys.path.insert(0, 'services/agents/src')

from services.tv_csv_parser import parse_tradingview_csv
import json

# Test with real CSV
csv_path = "/mnt/c/Users/uzobu/Pictures/Screenshots/CAPITALCOM_US30, 15.csv"

print("=" * 70)
print("Testing TradingView CSV Parser")
print("=" * 70)

try:
    result = parse_tradingview_csv(csv_path)

    print(f"\n✅ Parse successful!")
    print(f"\n📊 Symbol: {result['symbol']}")
    print(f"⏰ Timeframe: {result['timeframe']}")
    print(f"💰 Current Price: {result['current_price']}")
    print(f"📈 Trend: {result['trend']} ({result['trend_strength']})")
    print(f"🎯 Setup: {result['setup_type']}")

    if result['setup_type'] != 'no_trade':
        print(f"\n💹 Trade Setup:")
        print(f"   Entry: {result['entry_price']}")
        print(f"   Stop Loss: {result['stop_loss']}")
        print(f"   Take Profit: {result['take_profit']}")
        print(f"   Risk/Reward: {result['risk_reward']}")

    print(f"\n🔍 Indicators:")
    print(f"   EMA 20: {result['ema20']:.2f}")
    print(f"   EMA 50: {result['ema50']:.2f}")
    print(f"   EMA 200: {result['ema200']:.2f}")
    print(f"   RSI: {result['rsi']:.2f}")
    print(f"   ATR: {result['atr']:.2f}")
    print(f"   ADX: {result['adx']:.2f}")

    print(f"\n📝 Reasoning:")
    print(f"   {result['reasoning']}")

    print(f"\n⭐ Confidence: {result['confidence_score']}")

    print(f"\n🔗 Data Source: {result['data_source']}")
    print(f"📊 Total Bars: {result['total_bars']}")

    print("\n" + "=" * 70)
    print("✅ TEST PASSED")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
