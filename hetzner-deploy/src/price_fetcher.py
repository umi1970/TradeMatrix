#!/usr/bin/env python3
"""
Hybrid Price Fetcher for Liquidity Alert System

Data Sources:
- Indices (DAX, NASDAQ, DOW): yfinance (free, no API key required)
- Forex (EUR/USD, EUR/GBP): Twelvedata Grow Plan ($29/mo)

Rationale:
- Twelvedata Grow Plan does NOT support major indices despite listing them
- yfinance provides accurate, real-time index data for free
- Twelvedata works perfectly for forex pairs
"""

import os
import requests
import yfinance as yf
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class PriceFetcher:
    """Hybrid price fetcher using yfinance (indices) and Twelvedata (forex)"""

    def __init__(self):
        self.twelvedata_api_key = os.getenv('TWELVEDATA_API_KEY')
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )

        # Default fallback symbols (used if DB query fails)
        self.default_symbols = {
            '^GDAXI': {'provider': 'yfinance'},     # DAX Performance Index
            '^NDX': {'provider': 'yfinance'},       # NASDAQ 100 Index
            '^DJI': {'provider': 'yfinance'},       # Dow Jones Industrial Average
            'EURUSD': {'provider': 'twelvedata', 'ticker': 'EUR/USD', 'exchange': None},
            'EURGBP': {'provider': 'twelvedata', 'ticker': 'EUR/GBP', 'exchange': None},
        }

        # Will be populated from database on first use
        self.symbol_config = None

    def get_all_watched_symbols(self) -> Dict[str, Dict]:
        """
        Get unique symbols from all user watchlists (dynamic)

        Queries user_watchlist table to get all symbols currently watched by users.
        Returns symbol configuration dict with provider info.

        Returns:
            Dict mapping symbol to provider config
            Example: {
                '^GDAXI': {'provider': 'yfinance'},
                'EURUSD': {'provider': 'twelvedata', 'ticker': 'EUR/USD', 'exchange': None}
            }

        Fallback: Returns default symbols if query fails or no symbols found
        """
        try:
            # Query user_watchlist + symbols table (JOIN)
            # Filter only active symbols
            result = self.supabase.table('user_watchlist')\
                .select('symbols!inner(symbol, is_active, type)')\
                .eq('symbols.is_active', True)\
                .execute()

            if not result.data:
                print("⚠️  No symbols in any watchlist, using defaults")
                return self.default_symbols

            # Extract unique symbols and build config
            symbol_config = {}

            for item in result.data:
                symbol_data = item.get('symbols')
                if not symbol_data:
                    continue

                symbol = symbol_data['symbol']
                symbol_type = symbol_data.get('type', '')

                # Skip duplicates
                if symbol in symbol_config:
                    continue

                # Determine provider based on symbol format
                # Indices start with ^ (use yfinance)
                # Forex are all caps without ^ (use twelvedata)
                if symbol.startswith('^'):
                    # Index symbol - use yfinance
                    symbol_config[symbol] = {'provider': 'yfinance'}
                elif symbol_type == 'forex' or self._is_forex_pair(symbol):
                    # Forex pair - use twelvedata
                    # Format: EURUSD → EUR/USD
                    ticker = self._format_forex_ticker(symbol)
                    symbol_config[symbol] = {
                        'provider': 'twelvedata',
                        'ticker': ticker,
                        'exchange': None
                    }
                else:
                    # Default to yfinance for unknown types
                    print(f"⚠️  Unknown type '{symbol_type}' for {symbol}, defaulting to yfinance")
                    symbol_config[symbol] = {'provider': 'yfinance'}

            if not symbol_config:
                print("⚠️  No valid symbols found, using defaults")
                return self.default_symbols

            print(f"✓ Loaded {len(symbol_config)} watched symbols from database")
            return symbol_config

        except Exception as e:
            print(f"❌ Error fetching watched symbols from DB: {e}")
            print("   Using fallback symbols")
            return self.default_symbols

    def _is_forex_pair(self, symbol: str) -> bool:
        """
        Check if symbol is a forex pair (e.g., EURUSD, GBPJPY)

        Args:
            symbol: Symbol to check

        Returns:
            True if likely a forex pair
        """
        # Forex pairs are typically 6 characters (EURUSD, GBPJPY)
        if len(symbol) == 6 and symbol.isupper() and symbol.isalpha():
            return True
        return False

    def _format_forex_ticker(self, symbol: str) -> str:
        """
        Format forex symbol for Twelvedata API

        Args:
            symbol: Internal symbol (e.g., 'EURUSD')

        Returns:
            Formatted ticker for API (e.g., 'EUR/USD')
        """
        if len(symbol) == 6:
            # Split into base/quote currency (e.g., EURUSD → EUR/USD)
            base = symbol[:3]
            quote = symbol[3:]
            return f"{base}/{quote}"
        return symbol  # Return as-is if not standard format

    def fetch_yfinance_quote(self, symbol: str) -> Optional[Dict]:
        """
        Fetch real-time quote from Yahoo Finance via yfinance

        Args:
            symbol: Yahoo symbol (e.g., '^GDAXI', '^NDX', '^DJI')

        Returns:
            Dict with price data or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            # Get today's data
            hist = ticker.history(period='1d')

            if hist.empty:
                print(f"❌ yfinance: No data returned for {symbol}")
                return None

            latest = hist.iloc[-1]

            return {
                'current_price': Decimal(str(latest['Close'])),
                'high_today': Decimal(str(latest['High'])),
                'low_today': Decimal(str(latest['Low'])),
                'open_today': Decimal(str(latest['Open'])),
                'volume_today': int(latest['Volume']) if latest['Volume'] > 0 else None,
                'data_source': 'yfinance',
                'change': Decimal('0'),  # yfinance doesn't provide change directly
                'change_percent': Decimal('0'),
                'previous_close': Decimal(str(latest['Close'])),  # Use close as fallback
            }

        except Exception as e:
            print(f"❌ yfinance error for {symbol}: {e}")
            return None

    def fetch_twelvedata_quote(self, symbol: str, exchange: Optional[str]) -> Optional[Dict]:
        """
        Fetch real-time quote from Twelvedata API

        Args:
            symbol: Ticker symbol (e.g., 'EUR/USD')
            exchange: Exchange name (optional for forex)

        Returns:
            Dict with price data or None if failed
        """
        if not self.twelvedata_api_key:
            print("❌ TWELVEDATA_API_KEY not set")
            return None

        url = "https://api.twelvedata.com/quote"
        params = {
            'symbol': symbol,
            'apikey': self.twelvedata_api_key,
        }

        if exchange:
            params['exchange'] = exchange

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if 'code' in data:
                print(f"❌ Twelvedata API error for {symbol}: {data.get('message', 'Unknown error')}")
                return None

            # Extract price data
            if 'close' in data:
                return {
                    'current_price': Decimal(str(data['close'])),
                    'high_today': Decimal(str(data.get('high', data['close']))),
                    'low_today': Decimal(str(data.get('low', data['close']))),
                    'open_today': Decimal(str(data.get('open', data['close']))),
                    'volume_today': int(data.get('volume', 0)) if data.get('volume') else None,
                    'data_source': 'twelvedata',
                    'change': Decimal(str(data.get('change', 0))),
                    'change_percent': Decimal(str(data.get('percent_change', 0))),
                    'previous_close': Decimal(str(data.get('previous_close', data['close']))),
                }

            print(f"⚠️  No price data returned for {symbol}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Twelvedata network error for {symbol}: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error fetching {symbol}: {e}")
            return None

    def fetch_price(self, symbol: str) -> Optional[Dict]:
        """
        Fetch realtime price for a symbol using appropriate provider

        Args:
            symbol: Internal symbol (e.g., '^GDAXI', 'EURUSD')

        Returns:
            Dict with price data or None if failed
        """
        # Load symbol config on first use (lazy loading)
        if self.symbol_config is None:
            self.symbol_config = self.get_all_watched_symbols()

        config = self.symbol_config.get(symbol)
        if not config:
            print(f"⚠️  Unknown symbol: {symbol}")
            return None

        provider = config['provider']

        if provider == 'yfinance':
            return self.fetch_yfinance_quote(symbol)
        elif provider == 'twelvedata':
            return self.fetch_twelvedata_quote(
                symbol=config['ticker'],
                exchange=config.get('exchange')
            )
        else:
            print(f"❌ Unknown provider: {provider}")
            return None

    def get_symbol_id(self, symbol: str) -> Optional[str]:
        """Get symbol UUID from database"""
        try:
            response = self.supabase.table('symbols')\
                .select('id')\
                .eq('symbol', symbol)\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['id']
            return None

        except Exception as e:
            print(f"❌ Database error getting symbol ID for {symbol}: {e}")
            return None

    def update_price_cache(self, symbol: str, price_data: Dict) -> bool:
        """Update price_cache table with latest price"""
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            return False

        try:
            cache_record = {
                'symbol_id': symbol_id,
                'current_price': float(price_data['current_price']),
                'high_today': float(price_data['high_today']),
                'low_today': float(price_data['low_today']),
                'open_today': float(price_data['open_today']),
                'volume_today': price_data.get('volume_today'),
                'data_source': price_data['data_source'],
                'fetched_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
            }

            # Upsert (insert or update)
            response = self.supabase.table('current_prices')\
                .upsert(cache_record, on_conflict='symbol_id')\
                .execute()

            return True

        except Exception as e:
            print(f"❌ Database error updating price cache for {symbol}: {e}")
            return False

    def fetch_all_prices(self) -> Dict[str, Optional[Dict]]:
        """
        Fetch prices for all watched symbols (dynamic)

        Loads symbols from database on each run to ensure we monitor
        all currently watched symbols.

        Returns:
            Dict mapping symbol to price data
        """
        # Refresh symbol config from database (ensures we get latest watchlist)
        self.symbol_config = self.get_all_watched_symbols()

        if not self.symbol_config:
            print("⚠️  No symbols to fetch")
            return {}

        print(f"📊 Checking alerts for {len(self.symbol_config)} symbols: {list(self.symbol_config.keys())}")

        results = {}

        for symbol in self.symbol_config.keys():
            print(f"📊 Fetching {symbol}...")
            price_data = self.fetch_price(symbol)

            if price_data:
                # Update cache in database
                if self.update_price_cache(symbol, price_data):
                    results[symbol] = price_data
                    print(f"  ✓ {symbol}: ${price_data['current_price']} ({price_data['data_source']})")
                else:
                    results[symbol] = None
                    print(f"  ❌ Failed to update cache")
            else:
                results[symbol] = None
                print(f"  ❌ Failed to fetch price")

        return results


# CLI for testing
if __name__ == '__main__':
    print("=" * 70)
    print("🔄 Testing Hybrid Price Fetcher (yfinance + Twelvedata)")
    print("=" * 70)

    fetcher = PriceFetcher()
    results = fetcher.fetch_all_prices()

    print("\n" + "=" * 70)
    success_count = len([r for r in results.values() if r])
    print(f"✅ Fetched {success_count} / {len(results)} symbols")

    # Show data sources
    yfinance_symbols = [s for s, r in results.items() if r and r.get('data_source') == 'yfinance']
    twelvedata_symbols = [s for s, r in results.items() if r and r.get('data_source') == 'twelvedata']

    print(f"\nData Sources:")
    print(f"  yfinance: {len(yfinance_symbols)} symbols")
    print(f"  Twelvedata: {len(twelvedata_symbols)} symbols")
    print("=" * 70)
