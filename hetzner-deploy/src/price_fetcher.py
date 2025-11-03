#!/usr/bin/env python3
"""
Realtime Price Fetcher for Liquidity Alert System
Fetches prices from Twelvedata API (Grow Plan)

Twelvedata Grow Plan:
- 55 API calls/minute
- No daily limits
- Real-time data for stocks, forex, indices
- 8 WebSocket connections available
"""

import os
import requests
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class PriceFetcher:
    """Fetch realtime prices from Twelvedata API"""

    def __init__(self):
        self.twelvedata_api_key = os.getenv('TWELVEDATA_API_KEY')
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )

        if not self.twelvedata_api_key:
            raise ValueError("TWELVEDATA_API_KEY not set in environment")

        # Symbol mapping for Twelvedata Grow Plan
        # NOTE: Twelvedata Grow Plan does not include major indices directly
        # Using industry-standard ETF proxies that track the indices:
        # - EXS1: iShares Core DAX ETF (tracks DAX index, EUR-denominated)
        # - QQQ: Invesco QQQ Trust (tracks NASDAQ 100 with 99.9% correlation)
        # - DIA: SPDR Dow Jones Industrial Average ETF (tracks Dow Jones)
        self.symbol_config = {
            '^GDAXI': {'ticker': 'EXS1', 'exchange': 'XETR'},    # DAX proxy (iShares Core DAX ETF)
            '^NDX': {'ticker': 'QQQ', 'exchange': 'NASDAQ'},     # NASDAQ 100 proxy (Invesco QQQ ETF)
            '^DJI': {'ticker': 'DIA', 'exchange': 'NYSE'},       # Dow Jones proxy (SPDR DIA ETF)
            'EURUSD': {'ticker': 'EUR/USD', 'exchange': None},   # Forex (no exchange needed)
            'EURGBP': {'ticker': 'EUR/GBP', 'exchange': None},   # Forex (no exchange needed)
        }

    def fetch_twelvedata_quote(self, symbol: str, exchange: str) -> Optional[Dict]:
        """
        Fetch real-time quote from Twelvedata API

        Args:
            symbol: Ticker symbol (e.g., 'DAX', 'EUR/USD')
            exchange: Exchange name (e.g., 'XETR', 'Forex')

        Returns:
            Dict with price data or None if failed
        """
        # Twelvedata Quote endpoint
        url = "https://api.twelvedata.com/quote"

        params = {
            'symbol': symbol,
            'apikey': self.twelvedata_api_key,
        }

        # Add exchange if specified (not needed for Forex)
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
        except (ValueError, KeyError) as e:
            print(f"❌ Twelvedata parsing error for {symbol}: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error fetching {symbol}: {e}")
            return None

    def fetch_price(self, symbol: str) -> Optional[Dict]:
        """
        Fetch realtime price for a symbol
        Maps internal symbol to Twelvedata ticker format

        Args:
            symbol: Internal symbol (e.g., '^GDAXI', 'EURUSD')

        Returns:
            Dict with price data or None if failed
        """
        config = self.symbol_config.get(symbol)
        if not config:
            print(f"⚠️  Unknown symbol: {symbol}")
            return None

        return self.fetch_twelvedata_quote(
            symbol=config['ticker'],
            exchange=config['exchange']
        )

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
            response = self.supabase.table('price_cache')\
                .upsert(cache_record, on_conflict='symbol_id')\
                .execute()

            return True

        except Exception as e:
            print(f"❌ Database error updating price cache for {symbol}: {e}")
            return False

    def fetch_all_prices(self) -> Dict[str, Optional[Dict]]:
        """
        Fetch prices for all configured symbols

        Returns:
            Dict mapping symbol to price data
        """
        results = {}

        for symbol in self.symbol_config.keys():
            print(f"📊 Fetching {symbol}...")
            price_data = self.fetch_price(symbol)

            if price_data:
                # Update cache in database
                if self.update_price_cache(symbol, price_data):
                    results[symbol] = price_data
                    print(f"  ✓ {symbol}: ${price_data['current_price']}")
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
    print("🔄 Testing Twelvedata Price Fetcher")
    print("=" * 70)

    fetcher = PriceFetcher()
    results = fetcher.fetch_all_prices()

    print("\n" + "=" * 70)
    print(f"✅ Fetched {len([r for r in results.values() if r])} / {len(results)} symbols")
    print("=" * 70)
