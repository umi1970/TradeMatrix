#!/usr/bin/env python3
"""
OHLC Data Fetcher for Morning Planner
Fetches 5-minute candlestick data for intraday analysis

Data Sources:
- Indices (DAX, NASDAQ, DOW): yfinance (free)
- Forex (EUR/USD, EUR/GBP): Twelvedata Grow Plan ($29/mo)

Schedule: Every 5 minutes (Celery task)
Storage: ohlc table in Supabase
"""

import os
import requests
import yfinance as yf
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
import pytz
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class OHLCFetcher:
    """Hybrid OHLC fetcher using yfinance (indices) and Twelvedata (forex)"""

    def __init__(self):
        self.twelvedata_api_key = os.getenv('TWELVEDATA_API_KEY')
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )

    def determine_provider(self, symbol: str, vendor: str = None) -> str:
        """
        Automatically determine provider based on symbol format or vendor

        Args:
            symbol: Symbol name (DAX, EUR/USD, US30, etc.)
            vendor: Vendor from DB (capitalcom, tradingview, etc.)

        Returns:
            'twelvedata' or 'yfinance'
        """
        # Forex symbols contain '/' → Twelvedata
        if '/' in symbol:
            return 'twelvedata'

        # Everything else → yfinance (indices, stocks, commodities, etc.)
        return 'yfinance'

    def get_api_symbol(self, symbol: str, vendor: str = None) -> str:
        """
        Convert DB symbol to API symbol

        Args:
            symbol: DB symbol (DAX, NDX, EUR/USD, US30, etc.)
            vendor: Vendor from DB

        Returns:
            API-compatible symbol
        """
        # Known mappings
        mappings = {
            'DAX': '^GDAXI',
            'NDX': '^NDX',
            'DJI': '^DJI',
            'US30': '^DJI',  # US30 = Dow Jones
            'US100': '^NDX',  # US100 = NASDAQ
            'GER40': '^GDAXI',  # GER40 = DAX
            'EUR/USD': 'EUR/USD',
            'EUR/GBP': 'EUR/GBP',
            'GBP/USD': 'GBP/USD',
        }

        return mappings.get(symbol, symbol)

    def fetch_yfinance_ohlc(self, symbol: str, api_symbol: str) -> Optional[Dict]:
        """
        Fetch latest 5m candle from yfinance

        Args:
            symbol: DB symbol (DAX, NDX, DJI)
            api_symbol: API symbol (^GDAXI, ^NDX, ^DJI)

        Returns:
            Dict with OHLC data or None
        """
        try:
            ticker = yf.Ticker(api_symbol)

            # Get last 2 periods (5m interval) to ensure we have latest complete candle
            hist = ticker.history(period='1d', interval='5m')

            if hist.empty:
                print(f"⚠️  {symbol}: No data from yfinance")
                return None

            # Get second-to-last candle (last one might be incomplete)
            latest = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]

            # Convert timestamp to UTC
            ts = latest.name
            if ts.tzinfo is None:
                # Assume US market timezone (EST/EDT)
                us_eastern = pytz.timezone('America/New_York')
                ts = us_eastern.localize(ts).astimezone(pytz.UTC)
            else:
                ts = ts.astimezone(pytz.UTC)

            return {
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'volume': int(latest['Volume']) if 'Volume' in latest else 0,
                'timestamp': ts
            }

        except Exception as e:
            print(f"❌ {symbol}: yfinance error: {str(e)}")
            return None

    def fetch_twelvedata_ohlc(self, symbol: str, api_symbol: str) -> Optional[Dict]:
        """
        Fetch latest 5m candle from Twelvedata

        Args:
            symbol: DB symbol (EUR/USD, EUR/GBP)
            api_symbol: API symbol (EUR/USD, EUR/GBP)

        Returns:
            Dict with OHLC data or None
        """
        try:
            # Twelvedata time_series endpoint
            # outputsize=2 to get last 2 candles (latest might be incomplete)
            url = 'https://api.twelvedata.com/time_series'
            params = {
                'symbol': api_symbol,
                'interval': '5min',
                'outputsize': 2,
                'apikey': self.twelvedata_api_key,
                'format': 'JSON'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'values' not in data or len(data['values']) == 0:
                print(f"⚠️  {symbol}: No data from Twelvedata")
                return None

            # Get second-to-last candle (index 1)
            candle = data['values'][1] if len(data['values']) > 1 else data['values'][0]

            # Parse timestamp
            ts_str = candle['datetime']  # Format: "2025-01-12 08:20:00"
            ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            ts = pytz.UTC.localize(ts)  # Twelvedata returns UTC

            return {
                'open': float(candle['open']),
                'high': float(candle['high']),
                'low': float(candle['low']),
                'close': float(candle['close']),
                'volume': int(candle.get('volume', 0)),
                'timestamp': ts
            }

        except Exception as e:
            print(f"❌ {symbol}: Twelvedata error: {str(e)}")
            return None

    def fetch_symbol_ohlc(self, symbol: str, vendor: str = None) -> Optional[Dict]:
        """
        Fetch OHLC for a symbol using appropriate provider

        Args:
            symbol: DB symbol (DAX, EUR/USD, US30, etc.)
            vendor: Vendor from DB (capitalcom, tradingview, etc.)

        Returns:
            Dict with OHLC data or None
        """
        # Determine provider automatically
        provider = self.determine_provider(symbol, vendor)

        # Get API symbol
        api_symbol = self.get_api_symbol(symbol, vendor)

        if provider == 'yfinance':
            return self.fetch_yfinance_ohlc(symbol, api_symbol)
        elif provider == 'twelvedata':
            return self.fetch_twelvedata_ohlc(symbol, api_symbol)
        else:
            print(f"❌ Unknown provider: {provider}")
            return None

    def store_ohlc(self, symbol_id: str, symbol_name: str, ohlc_data: Dict, timeframe: str = '5m'):
        """
        Store OHLC data in ohlc table

        Args:
            symbol_id: UUID of market symbol
            symbol_name: Symbol name (for logging)
            ohlc_data: OHLC dict with keys: open, high, low, close, volume, timestamp
            timeframe: Timeframe (default: 5m)
        """
        try:
            record = {
                'symbol_id': symbol_id,
                'timeframe': timeframe,
                'ts': ohlc_data['timestamp'].isoformat(),
                'open': ohlc_data['open'],
                'high': ohlc_data['high'],
                'low': ohlc_data['low'],
                'close': ohlc_data['close'],
                'volume': ohlc_data['volume'],
            }

            # Upsert (avoid duplicates by ts + symbol_id + timeframe)
            result = self.supabase.table('ohlc').upsert(
                record,
                on_conflict='symbol_id,timeframe,ts'
            ).execute()

            if result.data:
                print(f"  ✅ {symbol_name}: Stored OHLC at {ohlc_data['timestamp'].strftime('%H:%M:%S')}")
                return True
            else:
                print(f"  ⚠️  {symbol_name}: Upsert returned no data")
                return False

        except Exception as e:
            print(f"  ❌ {symbol_name}: Storage error: {str(e)}")
            return False

    def fetch_all_ohlc(self) -> Dict[str, any]:
        """
        Fetch OHLC for all active symbols (DYNAMIC - reads from market_symbols table)

        Returns:
            Dict with summary:
            {
                'success': int,
                'failed': int,
                'symbols_processed': List[str]
            }
        """
        print("=" * 70)
        print("📊 OHLC Fetcher - Starting (DYNAMIC)...")
        print("=" * 70)

        # Get ALL active symbols from database (dynamic)
        try:
            symbols_result = self.supabase.table('market_symbols')\
                .select('id, symbol, vendor')\
                .eq('active', True)\
                .execute()

            db_symbols = symbols_result.data if symbols_result.data else []

            if not db_symbols:
                print("⚠️  No active symbols in database!")
                return {
                    'success': 0,
                    'failed': 0,
                    'symbols_processed': []
                }

            print(f"Found {len(db_symbols)} active symbols to fetch")

        except Exception as e:
            print(f"❌ Database query failed: {str(e)}")
            return {
                'success': 0,
                'failed': 0,
                'symbols_processed': [],
                'error': str(e)
            }

        success_count = 0
        failed_count = 0
        processed = []

        for db_symbol in db_symbols:
            symbol_name = db_symbol['symbol']
            symbol_id = db_symbol['id']
            vendor = db_symbol.get('vendor')

            # Determine provider automatically
            provider = self.determine_provider(symbol_name, vendor)

            print(f"\n📈 Fetching {symbol_name} ({provider})...")

            # Fetch OHLC
            ohlc_data = self.fetch_symbol_ohlc(symbol_name, vendor)

            if ohlc_data and symbol_id:
                # Store in database
                stored = self.store_ohlc(symbol_id, symbol_name, ohlc_data)
                if stored:
                    success_count += 1
                    processed.append(symbol_name)
                else:
                    failed_count += 1
            else:
                failed_count += 1
                if not symbol_id:
                    print(f"  ⚠️  {symbol_name}: Missing symbol_id")

        print("\n" + "=" * 70)
        print(f"✅ OHLC Fetch Complete: {success_count} success, {failed_count} failed")
        print("=" * 70)

        return {
            'success': success_count,
            'failed': failed_count,
            'symbols_processed': processed
        }


# Manual test
if __name__ == "__main__":
    fetcher = OHLCFetcher()
    result = fetcher.fetch_all_ohlc()
    print(f"\nResult: {result}")
