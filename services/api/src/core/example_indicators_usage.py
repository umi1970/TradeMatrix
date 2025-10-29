"""
Example Usage of Technical Indicators Module

This script demonstrates how to use the TechnicalIndicators class
to calculate various technical analysis indicators.

Author: TradeMatrix.ai
Version: 1.0.0
"""

import numpy as np
from technical_indicators import TechnicalIndicators


def example_basic_indicators():
    """Example: Calculate basic indicators (EMA, SMA, RSI)"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Indicators (EMA, SMA, RSI)")
    print("="*80)

    # Sample price data (e.g., closing prices)
    prices = [
        44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84,
        46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03,
        46.41, 46.22, 45.64, 46.21, 46.25, 46.50, 46.75, 47.00,
        47.25, 47.50, 47.25, 47.00, 46.75, 46.50
    ]

    # Calculate Simple Moving Average (SMA)
    sma_10 = TechnicalIndicators.calculate_sma(prices, 10)
    print(f"\n📊 SMA(10) - Last 5 values:")
    print(f"   {sma_10[-5:]}")

    # Calculate Exponential Moving Average (EMA)
    ema_10 = TechnicalIndicators.calculate_ema(prices, 10)
    print(f"\n📈 EMA(10) - Last 5 values:")
    print(f"   {ema_10[-5:]}")

    # Calculate RSI
    rsi = TechnicalIndicators.calculate_rsi(prices, 14)
    print(f"\n💪 RSI(14) - Current value: {rsi[-1]:.2f}")
    if rsi[-1] > 70:
        print("   ⚠️  Overbought condition!")
    elif rsi[-1] < 30:
        print("   ⚠️  Oversold condition!")
    else:
        print("   ✓ Normal range")


def example_macd():
    """Example: Calculate MACD"""
    print("\n" + "="*80)
    print("EXAMPLE 2: MACD (Moving Average Convergence Divergence)")
    print("="*80)

    # Generate sample data with trend
    prices = list(range(100, 150)) + list(range(150, 130, -1))

    # Calculate MACD
    macd = TechnicalIndicators.calculate_macd(prices, fast=12, slow=26, signal=9)

    print(f"\n📊 MACD Analysis:")
    print(f"   MACD Line:   {macd.macd_line[-1]:.4f}")
    print(f"   Signal Line: {macd.signal_line[-1]:.4f}")
    print(f"   Histogram:   {macd.histogram[-1]:.4f}")

    if macd.macd_line[-1] > macd.signal_line[-1]:
        print("   ✓ Bullish: MACD above signal line")
    else:
        print("   ✗ Bearish: MACD below signal line")

    # Detect crossovers
    crossovers = TechnicalIndicators.detect_crossover(
        macd.macd_line, macd.signal_line
    )
    recent_cross = crossovers[-5:]
    if 1 in recent_cross:
        print("   🚀 Bullish crossover detected recently!")
    elif -1 in recent_cross:
        print("   📉 Bearish crossover detected recently!")


def example_bollinger_bands():
    """Example: Calculate Bollinger Bands"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Bollinger Bands")
    print("="*80)

    # Generate sample data with volatility
    np.random.seed(42)
    base_price = 100
    prices = [base_price + np.sin(i/5) * 5 + np.random.randn() * 2
              for i in range(50)]

    # Calculate Bollinger Bands
    bb = TechnicalIndicators.calculate_bollinger_bands(prices, period=20, std_dev=2)

    current_price = prices[-1]
    print(f"\n📊 Bollinger Bands Analysis:")
    print(f"   Upper Band:  {bb.upper[-1]:.2f}")
    print(f"   Middle Band: {bb.middle[-1]:.2f}")
    print(f"   Lower Band:  {bb.lower[-1]:.2f}")
    print(f"   Current:     {current_price:.2f}")

    # Check position relative to bands
    band_width = bb.upper[-1] - bb.lower[-1]
    position = (current_price - bb.lower[-1]) / band_width * 100

    print(f"\n   Position: {position:.1f}% of band width")
    if position > 100:
        print("   ⚠️  Price above upper band (potential overbought)")
    elif position < 0:
        print("   ⚠️  Price below lower band (potential oversold)")
    elif position > 80:
        print("   📈 Near upper band")
    elif position < 20:
        print("   📉 Near lower band")
    else:
        print("   ✓ Within normal range")


def example_atr():
    """Example: Calculate Average True Range (ATR)"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Average True Range (Volatility)")
    print("="*80)

    # Sample OHLC data
    high = [110.5, 112.3, 111.8, 113.2, 115.1, 114.8, 116.2, 115.5]
    low = [105.2, 107.1, 106.5, 108.3, 110.4, 109.8, 111.5, 110.2]
    close = [108.3, 110.2, 109.4, 112.1, 113.5, 112.8, 114.5, 113.2]

    # Calculate ATR
    atr = TechnicalIndicators.calculate_atr(high, low, close, period=5)

    print(f"\n📊 ATR Analysis:")
    print(f"   Current ATR: {atr[-1]:.2f}")
    print(f"   Avg ATR:     {np.nanmean(atr):.2f}")

    # Use ATR for stop loss calculation
    current_price = close[-1]
    atr_multiplier = 2.0
    stop_loss_long = current_price - (atr[-1] * atr_multiplier)
    stop_loss_short = current_price + (atr[-1] * atr_multiplier)

    print(f"\n💰 Stop Loss Suggestions (2x ATR):")
    print(f"   Long Position:  ${stop_loss_long:.2f}")
    print(f"   Short Position: ${stop_loss_short:.2f}")


def example_pivot_points():
    """Example: Calculate Pivot Points"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Pivot Points")
    print("="*80)

    # Previous day's data
    prev_high = 1.2050
    prev_low = 1.2000
    prev_close = 1.2030

    # Calculate pivot points
    pivots = TechnicalIndicators.calculate_pivot_points(
        prev_high, prev_low, prev_close
    )

    print(f"\n📊 Daily Pivot Points:")
    print(f"   R3:  {pivots.r3:.4f}")
    print(f"   R2:  {pivots.r2:.4f}")
    print(f"   R1:  {pivots.r1:.4f}")
    print(f"   PP:  {pivots.pp:.4f}  ← Pivot Point")
    print(f"   S1:  {pivots.s1:.4f}")
    print(f"   S2:  {pivots.s2:.4f}")
    print(f"   S3:  {pivots.s3:.4f}")

    # Current price analysis
    current_price = 1.2035
    print(f"\n   Current Price: {current_price:.4f}")

    if current_price > pivots.pp:
        if current_price < pivots.r1:
            print(f"   ✓ Above PP, target R1 ({pivots.r1:.4f})")
        elif current_price < pivots.r2:
            print(f"   ✓ Above R1, target R2 ({pivots.r2:.4f})")
        else:
            print(f"   🚀 Strong uptrend, target R3 ({pivots.r3:.4f})")
    else:
        if current_price > pivots.s1:
            print(f"   ✗ Below PP, watch S1 ({pivots.s1:.4f})")
        elif current_price > pivots.s2:
            print(f"   ✗ Below S1, watch S2 ({pivots.s2:.4f})")
        else:
            print(f"   📉 Strong downtrend, watch S3 ({pivots.s3:.4f})")


def example_trend_analysis():
    """Example: Analyze trend using EMAs"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Trend Analysis with EMAs")
    print("="*80)

    # Generate uptrend data
    prices = [100 + i * 0.5 + np.random.randn() * 0.2 for i in range(250)]

    # Calculate EMAs
    ema_20 = TechnicalIndicators.calculate_ema(prices, 20)
    ema_50 = TechnicalIndicators.calculate_ema(prices, 50)
    ema_200 = TechnicalIndicators.calculate_ema(prices, 200)

    current_price = prices[-1]

    print(f"\n📊 Current Market Structure:")
    print(f"   Price:     {current_price:.2f}")
    print(f"   EMA(20):   {ema_20[-1]:.2f}")
    print(f"   EMA(50):   {ema_50[-1]:.2f}")
    print(f"   EMA(200):  {ema_200[-1]:.2f}")

    # Get trend direction
    trend = TechnicalIndicators.get_trend_direction(
        current_price, ema_20[-1], ema_50[-1], ema_200[-1]
    )

    print(f"\n🎯 Trend: {trend.upper()}")

    # Check alignment
    alignment = TechnicalIndicators.check_ema_alignment(
        current_price, ema_20[-1], ema_50[-1], ema_200[-1]
    )

    if alignment["perfect_bullish"]:
        print("   ✓ Perfect bullish alignment (Price > 20 > 50 > 200)")
    elif alignment["perfect_bearish"]:
        print("   ✗ Perfect bearish alignment (Price < 20 < 50 < 200)")

    if alignment["golden_cross"]:
        print("   🌟 Golden Cross: EMA50 > EMA200")
    elif alignment["death_cross"]:
        print("   ☠️  Death Cross: EMA50 < EMA200")

    # Detect recent crossovers
    crossovers = TechnicalIndicators.detect_crossover(ema_20, ema_50)
    if crossovers[-1] == 1:
        print("   🚀 EMA20 just crossed above EMA50 (Bullish!)")
    elif crossovers[-1] == -1:
        print("   📉 EMA20 just crossed below EMA50 (Bearish!)")


def example_complete_analysis():
    """Example: Complete technical analysis using all indicators"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Complete Technical Analysis")
    print("="*80)

    # Generate realistic market data
    np.random.seed(42)
    n = 300
    trend = np.linspace(100, 120, n)
    cycle = 5 * np.sin(np.linspace(0, 8*np.pi, n))
    noise = np.random.randn(n) * 1.5

    close = trend + cycle + noise
    high = close + np.abs(np.random.randn(n) * 2)
    low = close - np.abs(np.random.randn(n) * 2)

    # Calculate all indicators at once
    print("\n🔄 Calculating all indicators...")
    indicators = TechnicalIndicators.calculate_all_indicators(high, low, close)

    # Display comprehensive analysis
    print(f"\n📊 MARKET ANALYSIS REPORT")
    print("="*80)

    # Current price
    current_price = close[-1]
    print(f"\n💰 Current Price: ${current_price:.2f}")

    # Trend
    print(f"\n🎯 Trend: {indicators['trend'].upper()}")

    # EMAs
    print(f"\n📈 Moving Averages:")
    print(f"   EMA(20):  ${indicators['ema']['20'][-1]:.2f}")
    print(f"   EMA(50):  ${indicators['ema']['50'][-1]:.2f}")
    print(f"   EMA(200): ${indicators['ema']['200'][-1]:.2f}")

    # RSI
    rsi_current = indicators['rsi'][-1]
    print(f"\n💪 RSI(14): {rsi_current:.2f}")
    if rsi_current > 70:
        print("   ⚠️  Overbought (> 70)")
    elif rsi_current < 30:
        print("   ⚠️  Oversold (< 30)")
    else:
        print("   ✓ Normal range (30-70)")

    # MACD
    macd_value = indicators['macd']['macd_line'][-1]
    signal_value = indicators['macd']['signal_line'][-1]
    print(f"\n📊 MACD:")
    print(f"   MACD:   {macd_value:.4f}")
    print(f"   Signal: {signal_value:.4f}")
    print(f"   {'✓ Bullish' if macd_value > signal_value else '✗ Bearish'}")

    # Bollinger Bands
    bb_upper = indicators['bollinger_bands']['upper'][-1]
    bb_middle = indicators['bollinger_bands']['middle'][-1]
    bb_lower = indicators['bollinger_bands']['lower'][-1]

    print(f"\n🎚️  Bollinger Bands:")
    print(f"   Upper:  ${bb_upper:.2f}")
    print(f"   Middle: ${bb_middle:.2f}")
    print(f"   Lower:  ${bb_lower:.2f}")

    bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) * 100
    print(f"   Position: {bb_position:.1f}%")

    # ATR (Volatility)
    atr_current = indicators['atr'][-1]
    print(f"\n📉 ATR(14): ${atr_current:.2f} (Volatility measure)")

    # Pivot Points
    pivots = indicators['pivot_points']
    print(f"\n🎯 Pivot Points:")
    print(f"   R1: ${pivots['r1']:.2f}  |  PP: ${pivots['pp']:.2f}  |  S1: ${pivots['s1']:.2f}")

    # Alignment
    alignment = indicators['alignment']
    print(f"\n✅ EMA Alignment:")
    if alignment['perfect_bullish']:
        print("   ✓ Perfect Bullish Alignment")
    elif alignment['perfect_bearish']:
        print("   ✗ Perfect Bearish Alignment")
    else:
        print("   ~ Mixed/Neutral")

    # Crossovers
    if indicators['crossovers']['ema_20_50'][-1] == 1:
        print("\n🚀 SIGNAL: Bullish crossover (EMA20 > EMA50)")
    elif indicators['crossovers']['ema_20_50'][-1] == -1:
        print("\n📉 SIGNAL: Bearish crossover (EMA20 < EMA50)")

    # Trading suggestion
    print(f"\n💡 TRADING SUGGESTION:")
    if indicators['trend'] == 'bullish' and rsi_current < 70:
        print("   ✓ Consider LONG positions")
        print(f"   Stop Loss: ${current_price - (atr_current * 2):.2f} (2x ATR)")
        print(f"   Take Profit: ${pivots['r2']:.2f} (R2 pivot)")
    elif indicators['trend'] == 'bearish' and rsi_current > 30:
        print("   ✗ Consider SHORT positions")
        print(f"   Stop Loss: ${current_price + (atr_current * 2):.2f} (2x ATR)")
        print(f"   Take Profit: ${pivots['s2']:.2f} (S2 pivot)")
    else:
        print("   ⏸️  Wait for better entry (neutral/overbought/oversold)")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("TECHNICAL INDICATORS MODULE - USAGE EXAMPLES")
    print("TradeMatrix.ai")
    print("="*80)

    try:
        example_basic_indicators()
        example_macd()
        example_bollinger_bands()
        example_atr()
        example_pivot_points()
        example_trend_analysis()
        example_complete_analysis()

        print("\n" + "="*80)
        print("✅ All examples completed successfully!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
