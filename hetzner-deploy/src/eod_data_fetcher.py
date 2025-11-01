"""
TradeMatrix.ai - EOD Data Fetcher
Fetches End-of-Day market data from multiple sources (Stooq, Yahoo Finance)

Execution: Daily at 07:30 CET (via Celery scheduler)
Output: Stores data in Supabase (eod_data table)
"""

import logging
import csv
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from io import StringIO
import asyncio
import aiohttp
from uuid import UUID

import yaml
from supabase import Client

# Setup logger
logger = logging.getLogger(__name__)


class EODDataFetcher:
    """
    End-of-Day Data Fetcher
    
    Responsibilities:
    - Fetch EOD data from configured sources (Stooq, Yahoo Finance, EODHD)
    - Cross-validate data from multiple sources
    - Store validated data in Supabase
    - Calculate derived levels (yesterday high/low/close)
    - Log all fetch operations
    """
    
    def __init__(self, supabase_client: Client, config_path: str = "config/eod_data_config.yaml"):
        """
        Initialize EOD Data Fetcher
        
        Args:
            supabase_client: Supabase client instance (service role)
            config_path: Path to EOD configuration YAML file
        """
        self.supabase = supabase_client
        self.config = self._load_config(config_path)
        logger.info("EODDataFetcher initialized")
    
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    
    async def fetch_from_stooq(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch EOD data from Stooq.com (CSV format)
        
        Args:
            symbol: Stooq symbol (e.g., '^dax', 'eurusd')
            
        Returns:
            Dict with OHLCV data or None if fetch failed
            Format: {
                'date': datetime,
                'open': Decimal,
                'high': Decimal,
                'low': Decimal,
                'close': Decimal,
                'volume': int,
                'source': 'stooq'
            }
        """
        url = f"{self.config['data_sources']['primary']['base_url']}?s={symbol}&i=d"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"Stooq fetch failed for {symbol}: HTTP {response.status}")
                        return None
                    
                    content = await response.text()
                    
                    # Parse CSV
                    csv_reader = csv.DictReader(StringIO(content))
                    rows = list(csv_reader)
                    
                    if not rows:
                        logger.warning(f"No data returned from Stooq for {symbol}")
                        return None
                    
                    # Get the most recent row (last entry)
                    latest = rows[-1]
                    
                    return {
                        'date': datetime.strptime(latest['Date'], '%Y-%m-%d').date(),
                        'open': Decimal(latest['Open']),
                        'high': Decimal(latest['High']),
                        'low': Decimal(latest['Low']),
                        'close': Decimal(latest['Close']),
                        'volume': int(float(latest['Volume'])) if latest.get('Volume') else None,
                        'source': 'stooq'
                    }
                    
        except Exception as e:
            logger.error(f"Stooq fetch error for {symbol}: {e}")
            return None
    
    
    async def fetch_from_yahoo(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch EOD data from Yahoo Finance (JSON format)
        
        Args:
            symbol: Yahoo symbol (e.g., '^GDAXI', 'EURUSD=X')
            
        Returns:
            Dict with OHLCV data or None if fetch failed
        """
        base_url = self.config['data_sources']['backup']['base_url']
        params = self.config['data_sources']['backup']['parameters']
        url = f"{base_url}{symbol}?interval={params['interval']}&range={params['range']}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"Yahoo fetch failed for {symbol}: HTTP {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    result = data['chart']['result'][0]
                    timestamps = result['timestamp']
                    quote = result['indicators']['quote'][0]
                    
                    if not timestamps:
                        logger.warning(f"No data returned from Yahoo for {symbol}")
                        return None
                    
                    # Get the most recent data point
                    idx = -1
                    
                    return {
                        'date': datetime.fromtimestamp(timestamps[idx]).date(),
                        'open': Decimal(str(quote['open'][idx])),
                        'high': Decimal(str(quote['high'][idx])),
                        'low': Decimal(str(quote['low'][idx])),
                        'close': Decimal(str(quote['close'][idx])),
                        'volume': int(quote['volume'][idx]) if quote.get('volume') and quote['volume'][idx] else None,
                        'source': 'yahoo'
                    }
                    
        except Exception as e:
            logger.error(f"Yahoo fetch error for {symbol}: {e}")
            return None
    
    
    def cross_validate(
        self,
        data_primary: Dict[str, Any],
        data_backup: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Cross-validate data from two sources
        
        Args:
            data_primary: Data from primary source
            data_backup: Data from backup source
            
        Returns:
            Tuple of (is_valid, warning_message)
        """
        max_deviation = self.config['quality_control']['cross_validation']['max_deviation_percent']
        
        # Check if dates match
        if data_primary['date'] != data_backup['date']:
            return False, f"Date mismatch: {data_primary['date']} vs {data_backup['date']}"
        
        # Check close price deviation
        close_1 = float(data_primary['close'])
        close_2 = float(data_backup['close'])
        deviation_percent = abs((close_1 - close_2) / close_1) * 100
        
        if deviation_percent > max_deviation:
            warning = f"Close price deviation {deviation_percent:.2f}% exceeds threshold {max_deviation}%"
            logger.warning(warning)
            return False, warning
        
        return True, None
    
    
    async def fetch_and_store_symbol(self, symbol_config: Dict[str, Any]) -> bool:
        """
        Fetch EOD data for a single symbol and store in database
        
        Args:
            symbol_config: Symbol configuration from YAML
            
        Returns:
            True if successful, False otherwise
        """
        symbol_name = symbol_config['symbol']
        stooq_symbol = symbol_config['stooq_symbol']
        yahoo_symbol = symbol_config['yahoo_symbol']
        
        logger.info(f"Fetching EOD data for {symbol_name}")
        
        fetch_started_at = datetime.utcnow()
        
        # Fetch from both sources
        data_stooq = await self.fetch_from_stooq(stooq_symbol)
        data_yahoo = await self.fetch_from_yahoo(yahoo_symbol)
        
        # Determine which data to use
        if not data_stooq and not data_yahoo:
            logger.error(f"Failed to fetch data for {symbol_name} from any source")
            self._log_fetch_attempt(symbol_name, fetch_started_at, 'failed', 'All sources failed')
            return False
        
        # Prefer primary source (Stooq)
        data_to_use = data_stooq or data_yahoo
        quality_score = Decimal('0.50')  # Default score
        is_validated = False
        quality_warnings = []
        
        # Cross-validate if both sources available
        if data_stooq and data_yahoo:
            is_valid, warning = self.cross_validate(data_stooq, data_yahoo)
            if is_valid:
                quality_score = Decimal('0.95')
                is_validated = True
            else:
                quality_warnings.append(warning)
                quality_score = Decimal('0.70')
        
        # Get symbol_id from database
        symbol_result = self.supabase.table('symbols')\
            .select('id')\
            .eq('symbol', symbol_name)\
            .execute()
        
        if not symbol_result.data:
            logger.error(f"Symbol {symbol_name} not found in database")
            return False
        
        symbol_id = symbol_result.data[0]['id']
        
        # Store in database
        try:
            # Insert or update eod_data
            eod_record = {
                'symbol_id': symbol_id,
                'trade_date': data_to_use['date'].isoformat(),
                'open': float(data_to_use['open']),
                'high': float(data_to_use['high']),
                'low': float(data_to_use['low']),
                'close': float(data_to_use['close']),
                'volume': data_to_use['volume'],
                'data_source': data_to_use['source'],
                'quality_score': float(quality_score),
                'is_validated': is_validated
            }
            
            # Upsert (insert or update if exists)
            self.supabase.table('eod_data').upsert(
                eod_record,
                on_conflict='symbol_id,trade_date'
            ).execute()
            
            logger.info(f"Stored EOD data for {symbol_name} on {data_to_use['date']}")
            
            # Calculate and store derived levels
            await self._calculate_and_store_levels(symbol_id, data_to_use['date'])
            
            # Log successful fetch
            self._log_fetch_attempt(
                symbol_name,
                fetch_started_at,
                'success',
                None,
                quality_warnings
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store EOD data for {symbol_name}: {e}")
            self._log_fetch_attempt(symbol_name, fetch_started_at, 'failed', str(e))
            return False
    
    
    async def _calculate_and_store_levels(self, symbol_id: str, trade_date) -> None:
        """
        Calculate derived levels (yesterday high/low/close, ATR, etc.) and store
        
        Args:
            symbol_id: UUID of the symbol
            trade_date: Current trade date
        """
        try:
            # Fetch last 20 days of EOD data for calculations
            eod_result = self.supabase.table('eod_data')\
                .select('*')\
                .eq('symbol_id', symbol_id)\
                .order('trade_date', desc=True)\
                .limit(20)\
                .execute()
            
            if not eod_result.data or len(eod_result.data) < 2:
                logger.warning(f"Not enough historical data for symbol {symbol_id}")
                return
            
            data = eod_result.data
            
            # Yesterday's data (index 1, since index 0 is today)
            yesterday = data[1] if len(data) > 1 else data[0]
            
            # Calculate ATR (5 days)
            atr_5d = None
            if len(data) >= 5:
                ranges = [Decimal(str(d['high'])) - Decimal(str(d['low'])) for d in data[:5]]
                atr_5d = sum(ranges) / len(ranges)
            
            # Calculate ATR (20 days)
            atr_20d = None
            if len(data) >= 20:
                ranges = [Decimal(str(d['high'])) - Decimal(str(d['low'])) for d in data[:20]]
                atr_20d = sum(ranges) / len(ranges)
            
            # Daily change
            today = data[0]
            daily_change_points = Decimal(str(today['close'])) - Decimal(str(yesterday['close']))
            daily_change_percent = (daily_change_points / Decimal(str(yesterday['close']))) * 100
            
            # Yesterday range
            yesterday_range = Decimal(str(yesterday['high'])) - Decimal(str(yesterday['low']))
            
            # Create levels record
            levels_record = {
                'symbol_id': symbol_id,
                'trade_date': trade_date.isoformat(),
                'yesterday_high': float(yesterday['high']),
                'yesterday_low': float(yesterday['low']),
                'yesterday_close': float(yesterday['close']),
                'yesterday_open': float(yesterday['open']),
                'yesterday_range': float(yesterday_range),
                'atr_5d': float(atr_5d) if atr_5d else None,
                'atr_20d': float(atr_20d) if atr_20d else None,
                'daily_change_points': float(daily_change_points),
                'daily_change_percent': float(daily_change_percent)
            }
            
            # Upsert levels
            self.supabase.table('eod_levels').upsert(
                levels_record,
                on_conflict='symbol_id,trade_date'
            ).execute()
            
            logger.info(f"Calculated and stored levels for symbol {symbol_id}")
            
        except Exception as e:
            logger.error(f"Failed to calculate levels for symbol {symbol_id}: {e}")
    
    
    def _log_fetch_attempt(
        self,
        symbol_name: str,
        started_at: datetime,
        status: str,
        error_message: Optional[str] = None,
        quality_warnings: Optional[List[str]] = None
    ) -> None:
        """Log fetch attempt to database"""
        try:
            # Get symbol_id
            symbol_result = self.supabase.table('symbols')\
                .select('id')\
                .eq('symbol', symbol_name)\
                .execute()
            
            symbol_id = symbol_result.data[0]['id'] if symbol_result.data else None
            
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            log_record = {
                'symbol_id': symbol_id,
                'fetch_date': started_at.date().isoformat(),
                'data_source': 'stooq',  # Primary source
                'status': status,
                'fetch_started_at': started_at.isoformat(),
                'fetch_completed_at': completed_at.isoformat(),
                'duration_ms': duration_ms,
                'error_message': error_message,
                'quality_warnings': quality_warnings
            }
            
            self.supabase.table('eod_fetch_log').insert(log_record).execute()
            
        except Exception as e:
            logger.error(f"Failed to log fetch attempt: {e}")
    
    
    async def fetch_all_symbols(self) -> Dict[str, bool]:
        """
        Fetch EOD data for all enabled symbols
        
        Returns:
            Dict mapping symbol names to success status
        """
        results = {}
        
        # Get all enabled symbols from config
        all_symbols = []
        for category in ['indices', 'forex']:
            if category in self.config['symbols']:
                all_symbols.extend([
                    s for s in self.config['symbols'][category]
                    if s.get('fetch_enabled', True)
                ])
        
        logger.info(f"Fetching EOD data for {len(all_symbols)} symbols")
        
        # Fetch data for each symbol
        for symbol_config in all_symbols:
            symbol_name = symbol_config['symbol']
            success = await self.fetch_and_store_symbol(symbol_config)
            results[symbol_name] = success
        
        # Log summary
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"EOD fetch complete: {success_count}/{len(all_symbols)} successful")
        
        return results


# ============================================================
# Celery Task Integration
# ============================================================

async def fetch_eod_data_task(supabase_client: Client) -> Dict[str, bool]:
    """
    Celery task wrapper for EOD data fetching
    
    Args:
        supabase_client: Supabase service role client
        
    Returns:
        Dict of fetch results
    """
    fetcher = EODDataFetcher(supabase_client)
    results = await fetcher.fetch_all_symbols()
    return results


# For testing
if __name__ == "__main__":
    import os
    from supabase import create_client
    
    # Load from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Run fetch
    results = asyncio.run(fetch_eod_data_task(supabase))
    
    print("\n=== EOD Fetch Results ===")
    for symbol, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {symbol}")
