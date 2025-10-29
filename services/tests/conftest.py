"""
PyTest Configuration and Fixtures for E2E Tests
================================================
Provides shared fixtures for database setup, sample data, and test utilities
"""

import pytest
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4, UUID
from typing import Dict, List, Any
import pytz

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api/src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../agents/src')))

from supabase import Client, create_client
from config.supabase import settings


# ================================================
# Test Configuration
# ================================================

@pytest.fixture(scope="session")
def test_settings():
    """
    Test configuration settings
    Override with test-specific values if needed
    """
    return {
        'use_mock_db': os.getenv('USE_MOCK_DB', 'false').lower() == 'true',
        'test_db_url': os.getenv('TEST_SUPABASE_URL', settings.SUPABASE_URL),
        'test_db_key': os.getenv('TEST_SUPABASE_KEY', settings.SUPABASE_SERVICE_ROLE_KEY),
        'berlin_tz': pytz.timezone('Europe/Berlin'),
        'utc_tz': pytz.UTC,
    }


@pytest.fixture(scope="session")
def supabase_client(test_settings) -> Client:
    """
    Create Supabase client for tests
    Uses test database if configured, otherwise uses development database

    IMPORTANT: Ensure you're using a test database to avoid polluting production data
    """
    client = create_client(
        test_settings['test_db_url'],
        test_settings['test_db_key']
    )

    yield client

    # Cleanup would go here if needed
    # For now, we'll leave test data in place for inspection


# ================================================
# Symbol Fixtures
# ================================================

@pytest.fixture
def dax_symbol_id(supabase_client) -> UUID:
    """Get or create DAX symbol and return its UUID"""
    result = supabase_client.table('market_symbols')\
        .select('id')\
        .eq('symbol', 'DAX')\
        .limit(1)\
        .execute()

    if result.data and len(result.data) > 0:
        return UUID(result.data[0]['id'])

    # Create if not exists
    insert_result = supabase_client.table('market_symbols')\
        .insert({
            'vendor': 'twelve_data',
            'symbol': 'DAX',
            'alias': 'DAX 40',
            'tick_size': 0.5,
            'timezone': 'Europe/Berlin',
            'active': True
        })\
        .execute()

    return UUID(insert_result.data[0]['id'])


@pytest.fixture
def ndx_symbol_id(supabase_client) -> UUID:
    """Get or create NASDAQ symbol and return its UUID"""
    result = supabase_client.table('market_symbols')\
        .select('id')\
        .eq('symbol', 'NDX')\
        .limit(1)\
        .execute()

    if result.data and len(result.data) > 0:
        return UUID(result.data[0]['id'])

    # Create if not exists
    insert_result = supabase_client.table('market_symbols')\
        .insert({
            'vendor': 'twelve_data',
            'symbol': 'NDX',
            'alias': 'NASDAQ 100',
            'tick_size': 0.25,
            'timezone': 'America/New_York',
            'active': True
        })\
        .execute()

    return UUID(insert_result.data[0]['id'])


@pytest.fixture
def dji_symbol_id(supabase_client) -> UUID:
    """Get or create DOW JONES symbol and return its UUID"""
    result = supabase_client.table('market_symbols')\
        .select('id')\
        .eq('symbol', 'DJI')\
        .limit(1)\
        .execute()

    if result.data and len(result.data) > 0:
        return UUID(result.data[0]['id'])

    # Create if not exists
    insert_result = supabase_client.table('market_symbols')\
        .insert({
            'vendor': 'twelve_data',
            'symbol': 'DJI',
            'alias': 'Dow Jones 30',
            'tick_size': 1.0,
            'timezone': 'America/New_York',
            'active': True
        })\
        .execute()

    return UUID(insert_result.data[0]['id'])


@pytest.fixture
def all_symbol_ids(dax_symbol_id, ndx_symbol_id, dji_symbol_id) -> Dict[str, UUID]:
    """Return dictionary of all symbol IDs"""
    return {
        'DAX': dax_symbol_id,
        'NDX': ndx_symbol_id,
        'DJI': dji_symbol_id
    }


# ================================================
# Sample Data Fixtures
# ================================================

@pytest.fixture
def sample_ohlc_dax(supabase_client, dax_symbol_id, test_settings) -> List[Dict]:
    """
    Generate realistic sample OHLC data for DAX
    Creates 2 weeks of historical data (1m, 5m, 1h, 1d)
    """
    berlin_tz = test_settings['berlin_tz']
    trade_date = datetime.now(berlin_tz).replace(hour=8, minute=0, second=0, microsecond=0)

    candles = []
    base_price = Decimal('18500.0')  # DAX base price

    # Generate 5m candles for Asia session (02:00-05:00)
    asia_start = trade_date.replace(hour=2)
    for i in range(36):  # 36 x 5m = 3 hours
        ts = asia_start + timedelta(minutes=i*5)

        # Simulate sweep below y_low (18450)
        if i >= 12 and i <= 24:  # Between 03:00-04:00
            price_offset = Decimal('-50') - Decimal(str(i - 12)) * Decimal('2')
        else:
            price_offset = Decimal('0')

        open_price = base_price + price_offset
        high_price = open_price + Decimal('10')
        low_price = open_price - Decimal('15')
        close_price = open_price + Decimal('5')

        candles.append({
            'symbol_id': str(dax_symbol_id),
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'timeframe': '5m',
            'open': float(open_price),
            'high': float(high_price),
            'low': float(low_price),
            'close': float(close_price),
            'volume': 50000 + (i * 1000)
        })

    # Generate 5m candles for EU session (08:00-08:30)
    eu_start = trade_date.replace(hour=8)
    for i in range(6):  # 6 x 5m = 30 minutes
        ts = eu_start + timedelta(minutes=i*5)

        # Price recovers above y_low
        open_price = base_price + Decimal('10') + Decimal(str(i)) * Decimal('5')
        high_price = open_price + Decimal('15')
        low_price = open_price - Decimal('5')
        close_price = open_price + Decimal('10')

        candles.append({
            'symbol_id': str(dax_symbol_id),
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'timeframe': '5m',
            'open': float(open_price),
            'high': float(high_price),
            'low': float(low_price),
            'close': float(close_price),
            'volume': 75000 + (i * 2000)
        })

    # Insert candles (using upsert to avoid duplicates)
    if candles:
        supabase_client.table('ohlc').upsert(candles).execute()

    return candles


@pytest.fixture
def sample_ohlc_us_markets(supabase_client, ndx_symbol_id, dji_symbol_id, test_settings) -> Dict[str, List[Dict]]:
    """
    Generate realistic sample OHLC data for US markets (NDX, DJI)
    Creates ORB range (15:30-15:45 MEZ) and breakout candles
    """
    berlin_tz = test_settings['berlin_tz']
    trade_date = datetime.now(berlin_tz)

    result = {}

    # Generate data for both NDX and DJI
    symbols_data = [
        (ndx_symbol_id, 'NDX', Decimal('16500.0')),
        (dji_symbol_id, 'DJI', Decimal('38000.0'))
    ]

    for symbol_id, symbol_name, base_price in symbols_data:
        candles = []

        # ORB range candles (15:30-15:45 - 15 x 1m candles)
        orb_start = trade_date.replace(hour=15, minute=30, second=0, microsecond=0)
        orb_high = base_price + Decimal('50')
        orb_low = base_price - Decimal('30')

        for i in range(15):  # 15 minutes
            ts = orb_start + timedelta(minutes=i)

            # Create range-bound candles
            open_price = base_price + Decimal(str(i % 5)) * Decimal('5')
            high_price = min(open_price + Decimal('15'), orb_high)
            low_price = max(open_price - Decimal('10'), orb_low)
            close_price = open_price + Decimal('3')

            candles.append({
                'symbol_id': str(symbol_id),
                'ts': ts.astimezone(pytz.UTC).isoformat(),
                'timeframe': '1m',
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'close': float(close_price),
                'volume': 100000 + (i * 5000)
            })

        # Breakout candles (15:45-16:00 - 3 x 5m candles)
        breakout_start = trade_date.replace(hour=15, minute=45, second=0, microsecond=0)

        for i in range(3):  # 3 x 5m candles
            ts = breakout_start + timedelta(minutes=i*5)

            # Bullish breakout above range
            open_price = orb_high + Decimal(str(i)) * Decimal('10')
            high_price = open_price + Decimal('25')
            low_price = orb_high - Decimal('5') if i == 0 else open_price - Decimal('10')  # First candle shows retest
            close_price = high_price - Decimal('5')

            candles.append({
                'symbol_id': str(symbol_id),
                'ts': ts.astimezone(pytz.UTC).isoformat(),
                'timeframe': '5m',
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'close': float(close_price),
                'volume': 150000 + (i * 10000)
            })

        # Insert candles
        if candles:
            supabase_client.table('ohlc').upsert(candles).execute()

        result[symbol_name] = candles

    return result


@pytest.fixture
def sample_daily_levels(supabase_client, all_symbol_ids, test_settings) -> Dict[str, Dict]:
    """
    Generate sample daily levels (pivot points, y_high, y_low) for all symbols
    """
    berlin_tz = test_settings['berlin_tz']
    trade_date = datetime.now(berlin_tz).date()

    levels_data = {
        'DAX': {
            'y_high': 18600.0,
            'y_low': 18450.0,
            'y_close': 18520.0,
            'pivot': 18523.33,
            'r1': 18596.66,
            'r2': 18673.32,
            's1': 18446.67,
            's2': 18373.34
        },
        'NDX': {
            'y_high': 16600.0,
            'y_low': 16450.0,
            'y_close': 16520.0,
            'pivot': 16523.33,
            'r1': 16596.66,
            'r2': 16673.32,
            's1': 16446.67,
            's2': 16373.34
        },
        'DJI': {
            'y_high': 38200.0,
            'y_low': 38000.0,
            'y_close': 38100.0,
            'pivot': 38100.0,
            'r1': 38200.0,
            'r2': 38300.0,
            's1': 38000.0,
            's2': 37900.0
        }
    }

    inserted_levels = {}

    for symbol_name, levels in levels_data.items():
        symbol_id = all_symbol_ids[symbol_name]

        level_record = {
            'symbol_id': str(symbol_id),
            'trade_date': trade_date.isoformat(),
            **levels
        }

        # Upsert to avoid duplicates
        result = supabase_client.table('levels_daily')\
            .upsert(level_record)\
            .execute()

        inserted_levels[symbol_name] = result.data[0] if result.data else level_record

    return inserted_levels


# ================================================
# Utility Fixtures
# ================================================

@pytest.fixture
def cleanup_test_data(supabase_client):
    """
    Fixture to cleanup test data after each test
    Yields control to test, then cleans up
    """
    # Store IDs created during test for cleanup
    created_ids = {
        'setups': [],
        'alerts': [],
    }

    yield created_ids

    # Cleanup after test
    # Note: OHLC and levels_daily are kept for inspection
    # Only cleanup setups and alerts created during this test

    if created_ids['setups']:
        for setup_id in created_ids['setups']:
            supabase_client.table('setups')\
                .delete()\
                .eq('id', str(setup_id))\
                .execute()

    if created_ids['alerts']:
        for alert_id in created_ids['alerts']:
            supabase_client.table('alerts')\
                .delete()\
                .eq('id', str(alert_id))\
                .execute()


@pytest.fixture
def performance_timer():
    """
    Fixture to measure test execution time
    Returns a context manager for timing code blocks
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def timer(label: str):
        start = time.time()
        yield
        end = time.time()
        duration_ms = int((end - start) * 1000)
        print(f"\n⏱️  {label}: {duration_ms}ms")

    return timer


# ================================================
# Assertion Helpers
# ================================================

@pytest.fixture
def assert_setup_valid():
    """
    Helper fixture to assert setup data is valid
    """
    def _assert_valid(setup: Dict[str, Any]):
        """Validate setup record structure and values"""
        assert setup is not None, "Setup should not be None"
        assert 'id' in setup, "Setup should have an ID"
        assert 'module' in setup, "Setup should have a module"
        assert setup['module'] in ['morning', 'usopen'], f"Invalid module: {setup['module']}"
        assert 'strategy' in setup, "Setup should have a strategy"
        assert 'side' in setup, "Setup should have a side"
        assert setup['side'] in ['long', 'short'], f"Invalid side: {setup['side']}"
        assert 'entry_price' in setup, "Setup should have entry_price"
        assert setup['entry_price'] > 0, "Entry price must be positive"
        assert 'stop_loss' in setup, "Setup should have stop_loss"
        assert setup['stop_loss'] > 0, "Stop loss must be positive"
        assert 'take_profit' in setup, "Setup should have take_profit"
        assert setup['take_profit'] > 0, "Take profit must be positive"
        assert 'confidence' in setup, "Setup should have confidence"
        assert 0.0 <= setup['confidence'] <= 1.0, f"Confidence must be between 0-1, got {setup['confidence']}"

        # Validate risk/reward makes sense for long trades
        if setup['side'] == 'long':
            assert setup['entry_price'] > setup['stop_loss'], "Long: Entry must be above stop loss"
            assert setup['take_profit'] > setup['entry_price'], "Long: Take profit must be above entry"
        else:  # short
            assert setup['entry_price'] < setup['stop_loss'], "Short: Entry must be below stop loss"
            assert setup['take_profit'] < setup['entry_price'], "Short: Take profit must be below entry"

        return True

    return _assert_valid


@pytest.fixture
def assert_alert_valid():
    """
    Helper fixture to assert alert data is valid
    """
    def _assert_valid(alert: Dict[str, Any]):
        """Validate alert record structure and values"""
        assert alert is not None, "Alert should not be None"
        assert 'id' in alert, "Alert should have an ID"
        assert 'kind' in alert, "Alert should have a kind"
        assert alert['kind'] in [
            'range_break', 'retest_touch', 'asia_sweep_confirmed',
            'pivot_touch', 'r1_touch', 's1_touch'
        ], f"Invalid alert kind: {alert['kind']}"
        assert 'context' in alert, "Alert should have context"
        assert isinstance(alert['context'], dict), "Context should be a dict"
        assert 'sent' in alert, "Alert should have sent status"

        return True

    return _assert_valid
