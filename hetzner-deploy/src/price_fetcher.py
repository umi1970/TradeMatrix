#!/usr/bin/env python3
"""
Realtime Price Fetcher for Liquidity Alert System
Fetches prices from Finnhub (indices) and Alpha Vantage (forex)
"""

import os
import requests
from typing import Dict, Optional, Literal
from decimal import Decimal
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class PriceFetcher:
    """Fetch realtime prices from Finnhub and Alpha Vantage"""

    def __init__(self):
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )

        # Symbol mapping
        # Note: Finnhub uses ^ prefix for indices (^GDAXI, ^NDX, ^DJI)
        self.symbol_config = {
            '^GDAXI': {'type': 'index', 'api': 'finnhub', 'ticker': '^GDAXI'},
            '^NDX': {'type': 'index', 'api': 'finnhub', 'ticker': '^NDX'},
            '^DJI': {'type': 'index', 'api': 'finnhub', 'ticker': '^DJI'},
            'EURUSD': {'type': 'forex', 'api': 'alpha_vantage', 'pair': 'EUR/USD'},
            'EURGBP': {'type': 'forex', 'api': 'alpha_vantage', 'pair': 'EUR/GBP'},
        }

    def fetch_finnhub_quote(self, ticker: str) -> Optional[Dict]:
        """Fetch quote from Finnhub API"""
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={self.finnhub_api_key}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('c'):  # Current price exists
                return {
                    'current_price': Decimal(str(data['c'])),
                    'high_today': Decimal(str(data['h'])),
                    'low_today': Decimal(str(data['l'])),
                    'open_today': Decimal(str(data['o'])),
                    'volume_today': None,  # Finnhub doesn't provide volume in quote
                    'data_source': 'finnhub',
                }
            return None

        except Exception as e:
            print(f"❌ Finnhub error for {ticker}: {e}")
            return None

    def fetch_alpha_vantage_quote(self, pair: str) -> Optional[Dict]:
        """Fetch forex quote from Alpha Vantage API"""
        # Alpha Vantage expects format: EUR/USD → FROM=EUR, TO=USD
        from_currency, to_currency = pair.split('/')

        url = (
            f"https://www.alphavantage.co/query"
            f"?function=CURRENCY_EXCHANGE_RATE"
            f"&from_currency={from_currency}"
            f"&to_currency={to_currency}"
            f"&apikey={self.alpha_vantage_api_key}"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            rate_data = data.get('Realtime Currency Exchange Rate')
            if rate_data:
                return {
                    'current_price': Decimal(rate_data['5. Exchange Rate']),
                    'high_today': Decimal(rate_data.get('2. High', rate_data['5. Exchange Rate'])),
                    'low_today': Decimal(rate_data.get('3. Low', rate_data['5. Exchange Rate'])),
                    'open_today': Decimal(rate_data.get('1. Open', rate_data['5. Exchange Rate'])),
                    'volume_today': None,
                    'data_source': 'alpha_vantage',
                }
            return None

        except Exception as e:
            print(f"❌ Alpha Vantage error for {pair}: {e}")
            return None

    def fetch_price(self, symbol: str) -> Optional[Dict]:
        """
        Fetch realtime price for a symbol
        Routes to correct API based on symbol type
        """
        config = self.symbol_config.get(symbol)
        if not config:
            print(f"⚠️  Unknown symbol: {symbol}")
            return None

        if config['api'] == 'finnhub':
            return self.fetch_finnhub_quote(config['ticker'])
        elif config['api'] == 'alpha_vantage':
            return self.fetch_alpha_vantage_quote(config['pair'])

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
            self.supabase.table('price_cache')\
                .upsert(cache_record, on_conflict='symbol_id')\
                .execute()

            return True

        except Exception as e:
            print(f"❌ Error updating price cache for {symbol}: {e}")
            return False

    def fetch_all_prices(self) -> Dict[str, Dict]:
        """
        Fetch prices for all symbols and update cache
        Returns dict of symbol -> price_data
        """
        results = {}

        for symbol in self.symbol_config.keys():
            print(f"📊 Fetching {symbol}...", end=' ')

            price_data = self.fetch_price(symbol)
            if price_data:
                success = self.update_price_cache(symbol, price_data)
                if success:
                    results[symbol] = price_data
                    print(f"✅ {price_data['current_price']} ({price_data['data_source']})")
                else:
                    print(f"❌ Failed to update cache")
            else:
                print(f"❌ Failed to fetch price")

        return results


# Usage example
if __name__ == "__main__":
    fetcher = PriceFetcher()
    prices = fetcher.fetch_all_prices()

    print(f"\n📊 Fetched {len(prices)}/{len(fetcher.symbol_config)} prices")
    for symbol, data in prices.items():
        print(f"  {symbol}: {data['current_price']}")
