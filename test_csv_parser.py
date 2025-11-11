#!/usr/bin/env python3
"""
TradingView CSV Quality Test
Test if TradingView CSV export has required data for AI analysis
"""

import pandas as pd
from datetime import datetime
import sys

def test_tradingview_csv(file_path: str):
    """Test if TradingView CSV has required data."""

    print("=" * 70)
    print("TradingView CSV Quality Test")
    print("=" * 70)

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        return False

    print(f"\n📊 CSV Stats:")
    print(f"   File: {file_path}")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Size: {len(df) * len(df.columns)} cells")

    print(f"\n📋 Columns found:")
    for i, col in enumerate(df.columns):
        sample_value = df[col].iloc[0] if len(df) > 0 else "N/A"
        print(f"   {i+1}. {col} (example: {sample_value})")

    # Check required columns
    required = ['time', 'open', 'high', 'low', 'close']
    missing_required = [col for col in required if col not in df.columns]

    if missing_required:
        print(f"\n❌ MISSING REQUIRED COLUMNS: {missing_required}")
        print("   CSV is NOT usable!")
        return False
    else:
        print(f"\n✅ All required OHLC columns present")

    # Check optional indicators
    indicators = {
        'volume': 'Volume',
        'ema20': 'EMA(20)',
        'ema50': 'EMA(50)',
        'ema200': 'EMA(200)',
        'rsi': 'RSI(14)',
        'atr': 'ATR(14)',
        'macd': 'MACD'
    }

    found_indicators = []
    missing_indicators = []

    for key, name in indicators.items():
        if key in df.columns:
            found_indicators.append(name)
        else:
            missing_indicators.append(name)

    # Check for unnamed "Plot" columns
    plot_columns = [col for col in df.columns if col == 'Plot']

    if plot_columns:
        print(f"\n⚠️  Found {len(plot_columns)} unnamed 'Plot' columns")
        print(f"   These are likely indicators (EMAs?) but NOT labeled")
        print(f"   Values:")
        for i, col_idx in enumerate([j for j, c in enumerate(df.columns) if c == 'Plot']):
            col_name = df.columns[col_idx]
            sample = df.iloc[0, col_idx]
            print(f"   - Plot #{i+1}: {sample:.2f}")

    if found_indicators:
        print(f"\n✅ Labeled indicators found: {', '.join(found_indicators)}")
    else:
        print(f"\n❌ NO labeled indicators found")

    if missing_indicators:
        print(f"⚠️  Missing indicators: {', '.join(missing_indicators)}")

    # Check data quality
    print(f"\n🔍 Data Quality:")
    null_count = df.isnull().sum().sum()
    print(f"   Null values: {null_count}")
    if null_count > 0:
        print(f"   ⚠️  WARNING: CSV contains null values!")

    duplicate_count = df.duplicated().sum()
    print(f"   Duplicate rows: {duplicate_count}")
    if duplicate_count > 0:
        print(f"   ⚠️  WARNING: CSV contains duplicates!")

    # Check OHLC range and consistency
    print(f"\n💰 Price Data:")
    print(f"   Low: {df['low'].min():.2f}")
    print(f"   High: {df['high'].max():.2f}")
    print(f"   Latest Open: {df['open'].iloc[-1]:.2f}")
    print(f"   Latest Close: {df['close'].iloc[-1]:.2f}")

    # Validate OHLC logic (High >= Low, Close between High and Low)
    invalid_ohlc = 0
    for idx, row in df.iterrows():
        if row['high'] < row['low']:
            invalid_ohlc += 1
        if row['close'] > row['high'] or row['close'] < row['low']:
            invalid_ohlc += 1
        if row['open'] > row['high'] or row['open'] < row['low']:
            invalid_ohlc += 1

    if invalid_ohlc > 0:
        print(f"   ❌ Invalid OHLC logic in {invalid_ohlc} rows!")
    else:
        print(f"   ✅ OHLC data is logically consistent")

    # Check if data is recent
    if 'time' in df.columns:
        try:
            first_time = pd.to_datetime(df['time'].iloc[0])
            latest_time = pd.to_datetime(df['time'].iloc[-1])
            print(f"\n⏰ Time Range:")
            print(f"   First: {first_time}")
            print(f"   Latest: {latest_time}")
            print(f"   Duration: {(latest_time - first_time)}")

            # Check freshness (last bar should be recent)
            now = datetime.now(latest_time.tzinfo)
            age = now - latest_time
            age_hours = age.total_seconds() / 3600

            if age_hours < 1:
                print(f"   ✅ Data is FRESH ({age.total_seconds() / 60:.0f} minutes old)")
            elif age_hours < 24:
                print(f"   ⚠️  Data is {age_hours:.1f} hours old")
            else:
                print(f"   ❌ Data is {age_hours / 24:.1f} days old (STALE!)")
        except Exception as e:
            print(f"   ⚠️  Could not parse timestamps: {e}")

    # Show sample data
    print(f"\n📈 First 5 rows:")
    print(df.head().to_string())

    # Decision
    print("\n" + "=" * 70)
    print("DECISION:")
    print("=" * 70)

    usability_score = 0
    max_score = 5

    # Scoring
    if not missing_required and len(df) >= 50:
        usability_score += 2
        print("✅ +2: Has OHLC data with sufficient rows")

    if null_count == 0 and duplicate_count == 0 and invalid_ohlc == 0:
        usability_score += 1
        print("✅ +1: Data quality is excellent")

    if len(plot_columns) >= 3:
        usability_score += 1
        print("✅ +1: Has 3+ indicator plots (likely EMAs)")
    elif found_indicators:
        usability_score += 1
        print("✅ +1: Has labeled indicators")

    if 'volume' in df.columns:
        usability_score += 0.5
        print("✅ +0.5: Has volume data")

    if 'rsi' in df.columns or 'atr' in df.columns:
        usability_score += 0.5
        print("✅ +0.5: Has RSI or ATR")

    print(f"\n📊 Usability Score: {usability_score}/{max_score}")

    if usability_score >= 4:
        print("\n" + "🎯 " + "=" * 65)
        print("✅ CSV FORMAT IS EXCELLENT!")
        print("=" * 70)
        print("RECOMMENDATION:")
        print("✅ Proceed with TradingView CSV integration")
        if found_indicators:
            print("✅ All indicators included - use directly")
        elif len(plot_columns) >= 3:
            print("⚠️  Indicators unnamed - we'll treat Plot 1-3 as EMA 20/50/200")
            print("⚠️  Calculate RSI/ATR ourselves (pandas_ta)")
        return True

    elif usability_score >= 2.5:
        print("\n" + "⚠️  " + "=" * 65)
        print("⚠️  CSV FORMAT IS USABLE (with limitations)")
        print("=" * 70)
        print("RECOMMENDATION:")
        print("✅ CSV can be used BUT:")
        print("   - Calculate missing indicators ourselves (RSI, ATR)")
        if len(plot_columns) > 0:
            print("   - Assume Plot columns are EMAs (verify manually)")
        print("   - Consider Pine Script if this becomes unreliable")
        return True

    else:
        print("\n" + "❌ " + "=" * 65)
        print("❌ CSV FORMAT IS NOT USABLE")
        print("=" * 70)
        print("RECOMMENDATION:")
        print("❌ SKIP CSV approach entirely")
        print("✅ Use Pine Script integration instead (Phase 0.5)")
        print("✅ NO TradingView Plus subscription needed")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_csv_parser.py <csv_file_path>")
        print("\nExample:")
        print("  python test_csv_parser.py '/mnt/c/Users/uzobu/Pictures/Screenshots/FX_GER30, 5.csv'")
        sys.exit(1)

    csv_path = sys.argv[1]
    result = test_tradingview_csv(csv_path)

    sys.exit(0 if result else 1)
