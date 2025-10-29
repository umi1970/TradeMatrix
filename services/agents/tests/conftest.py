"""
Pytest Configuration and Shared Fixtures
=========================================

Provides common fixtures for all tests including:
- Mock Supabase client
- Sample OHLC data
- Test database setup
- Environment configuration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from decimal import Decimal
import pytz


@pytest.fixture
def mock_supabase():
    """
    Mock Supabase client for testing without database connection.

    Returns:
        Mock Supabase client with standard methods mocked
    """
    mock_client = Mock()

    # Mock table() method
    mock_table = Mock()
    mock_client.table = Mock(return_value=mock_table)

    # Mock query builder methods
    mock_table.select = Mock(return_value=mock_table)
    mock_table.insert = Mock(return_value=mock_table)
    mock_table.update = Mock(return_value=mock_table)
    mock_table.delete = Mock(return_value=mock_table)
    mock_table.eq = Mock(return_value=mock_table)
    mock_table.gte = Mock(return_value=mock_table)
    mock_table.lte = Mock(return_value=mock_table)
    mock_table.gt = Mock(return_value=mock_table)
    mock_table.lt = Mock(return_value=mock_table)
    mock_table.order = Mock(return_value=mock_table)
    mock_table.limit = Mock(return_value=mock_table)
    mock_table.in_ = Mock(return_value=mock_table)
    mock_table.upsert = Mock(return_value=mock_table)

    # Mock execute() to return sample data
    mock_result = Mock()
    mock_result.data = []
    mock_table.execute = Mock(return_value=mock_result)

    return mock_client


@pytest.fixture
def test_symbol_id():
    """Fixed UUID for testing symbol references."""
    return UUID('12345678-1234-1234-1234-123456789012')


@pytest.fixture
def test_trade_date():
    """Fixed date for testing (2025-10-29)."""
    berlin_tz = pytz.timezone('Europe/Berlin')
    return berlin_tz.localize(datetime(2025, 10, 29, 8, 25, 0))


@pytest.fixture
def sample_ohlc_candles():
    """
    Generate sample OHLC candles for testing.

    Returns:
        List of OHLC candle dictionaries (100 candles)
    """
    berlin_tz = pytz.timezone('Europe/Berlin')
    start_time = berlin_tz.localize(datetime(2025, 10, 29, 2, 0, 0))

    candles = []
    base_price = 19500.0

    for i in range(100):
        ts = start_time + timedelta(minutes=5 * i)

        # Simulate price movement
        open_price = base_price + (i * 2) - 100
        high = open_price + 10
        low = open_price - 10
        close = open_price + 5
        volume = 10000 + (i * 100)

        candles.append({
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return candles


@pytest.fixture
def sample_asia_session_candles(test_symbol_id):
    """
    Generate Asia session candles with sweep below y_low.

    Returns:
        List of candles from 02:00-05:00 MEZ with sweep pattern
    """
    berlin_tz = pytz.timezone('Europe/Berlin')
    start_time = berlin_tz.localize(datetime(2025, 10, 29, 2, 0, 0))

    candles = []
    y_low = 19400.0

    for i in range(36):  # 3 hours = 36 x 5min candles
        ts = start_time + timedelta(minutes=5 * i)

        # Create sweep pattern: move down to sweep y_low, then recover
        if i < 10:
            # Move down
            open_price = 19450.0 - (i * 5)
            low = open_price - 5
        elif i < 20:
            # Sweep below y_low
            open_price = y_low - 10
            low = y_low - 15  # Sweep below y_low
        else:
            # Recovery
            open_price = y_low + ((i - 20) * 3)
            low = open_price - 5

        high = open_price + 10
        close = open_price + 2
        volume = 8000 + (i * 50)

        candles.append({
            'id': str(uuid4()),
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'symbol_id': str(test_symbol_id),
            'timeframe': '5m',
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return candles


@pytest.fixture
def sample_eu_open_candles(test_symbol_id):
    """
    Generate EU open candles (08:00-08:25 MEZ).

    Returns:
        List of candles showing reversal above y_low
    """
    berlin_tz = pytz.timezone('Europe/Berlin')
    start_time = berlin_tz.localize(datetime(2025, 10, 29, 8, 0, 0))

    y_low = 19400.0
    candles = []

    for i in range(5):  # 25 minutes = 5 x 5min candles
        ts = start_time + timedelta(minutes=5 * i)

        # Price above y_low (reversal confirmed)
        open_price = y_low + 20 + (i * 5)
        high = open_price + 15
        low = y_low + 10  # Stay above y_low
        close = open_price + 10
        volume = 12000 + (i * 200)

        candles.append({
            'id': str(uuid4()),
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'symbol_id': str(test_symbol_id),
            'timeframe': '5m',
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return candles


@pytest.fixture
def sample_levels_daily(test_symbol_id, test_trade_date):
    """
    Sample daily levels (pivot points, y_high, y_low).

    Returns:
        Dict with daily level data
    """
    return {
        'id': str(uuid4()),
        'symbol_id': str(test_symbol_id),
        'trade_date': test_trade_date.strftime('%Y-%m-%d'),
        'y_high': 19600.0,
        'y_low': 19400.0,
        'pivot': 19500.0,
        'r1': 19550.0,
        'r2': 19600.0,
        'r3': 19650.0,
        's1': 19450.0,
        's2': 19400.0,
        's3': 19350.0,
        'created_at': datetime.now(pytz.UTC).isoformat()
    }


@pytest.fixture
def sample_market_symbols(test_symbol_id):
    """
    Sample market symbols data.

    Returns:
        List of market symbol records
    """
    return [
        {
            'id': str(test_symbol_id),
            'symbol': 'DAX',
            'name': 'DAX 40',
            'vendor': 'twelve_data',
            'active': True,
            'created_at': datetime.now(pytz.UTC).isoformat()
        },
        {
            'id': str(uuid4()),
            'symbol': 'NDX',
            'name': 'NASDAQ 100',
            'vendor': 'twelve_data',
            'active': True,
            'created_at': datetime.now(pytz.UTC).isoformat()
        }
    ]


@pytest.fixture
def sample_setup_record(test_symbol_id):
    """
    Sample setup record for testing.

    Returns:
        Dict with setup data
    """
    return {
        'id': str(uuid4()),
        'user_id': None,
        'module': 'morning',
        'symbol_id': str(test_symbol_id),
        'strategy': 'asia_sweep',
        'side': 'long',
        'entry_price': 19420.0,
        'stop_loss': 19385.0,
        'take_profit': 19500.0,
        'confidence': 0.85,
        'status': 'pending',
        'payload': {
            'asia_low': 19385.0,
            'y_low': 19400.0,
            'pivot': 19500.0,
            'detection_time': datetime.now(pytz.UTC).isoformat()
        },
        'created_at': datetime.now(pytz.UTC).isoformat()
    }


@pytest.fixture
def sample_orb_range():
    """
    Sample ORB (Opening Range Breakout) data.

    Returns:
        Dict with ORB range data
    """
    berlin_tz = pytz.timezone('Europe/Berlin')
    start_dt = berlin_tz.localize(datetime(2025, 10, 29, 15, 30, 0))
    end_dt = berlin_tz.localize(datetime(2025, 10, 29, 15, 45, 0))

    return {
        'high': Decimal('18550.0'),
        'low': Decimal('18520.0'),
        'range_size': Decimal('30.0'),
        'start_time': start_dt,
        'end_time': end_dt,
        'candle_count': 15,
        'opening_candle': {
            'open': Decimal('18530.0'),
            'high': Decimal('18540.0'),
            'low': Decimal('18525.0'),
            'close': Decimal('18535.0'),
            'volume': 15000,
            'ts': start_dt.isoformat()
        }
    }


@pytest.fixture
def sample_breakout_data():
    """
    Sample breakout detection data.

    Returns:
        Dict with breakout data
    """
    return {
        'direction': 'long',
        'breakout_price': Decimal('18560.0'),
        'breakout_time': datetime.now(pytz.UTC).isoformat(),
        'candle_close': Decimal('18560.0'),
        'volume': 20000,
        'retest_available': True,
        'retest_price': Decimal('18550.0'),
        'breakout_strength': 0.33
    }


@pytest.fixture
def mock_twelve_data_api():
    """
    Mock Twelve Data API responses.

    Returns:
        Mock HTTP client with sample API responses
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={
        'values': [
            {
                'datetime': '2025-10-29 14:00:00',
                'open': '19500.0',
                'high': '19520.0',
                'low': '19490.0',
                'close': '19515.0',
                'volume': '10000'
            }
        ],
        'meta': {
            'symbol': 'DAX',
            'interval': '1h',
            'currency': 'EUR'
        }
    })

    return mock_response


@pytest.fixture
def sample_validation_signal_data():
    """
    Sample signal data for validation engine testing.

    Returns:
        Dict with complete signal data
    """
    return {
        'price': 18500.0,
        'emas': {
            '20': 18450.0,
            '50': 18400.0,
            '200': 18300.0
        },
        'levels': {
            'pivot': 18480.0,
            'r1': 18550.0,
            's1': 18410.0
        },
        'volume': 15000,
        'avg_volume': 10000,
        'candle': {
            'open': 18490.0,
            'high': 18510.0,
            'low': 18485.0,
            'close': 18505.0
        },
        'context': {
            'trend': 'bullish',
            'volatility': 0.15
        },
        'strategy': 'MR-02'
    }


@pytest.fixture
def env_vars(monkeypatch):
    """
    Set environment variables for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setenv('SUPABASE_URL', 'https://test.supabase.co')
    monkeypatch.setenv('SUPABASE_KEY', 'test_key')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'test_service_key')
    monkeypatch.setenv('TWELVE_DATA_API_KEY', 'test_twelve_data_key')


# Pytest configuration hooks

def pytest_configure(config):
    """
    Pytest configuration hook.

    Registers custom markers.
    """
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "agent: Agent tests")
    config.addinivalue_line("markers", "core: Core module tests")


def pytest_collection_modifyitems(config, items):
    """
    Pytest collection hook.

    Automatically mark tests based on file location.
    """
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark agent tests
        if any(agent in item.nodeid for agent in ["morning_planner", "us_open_planner", "alert_engine"]):
            item.add_marker(pytest.mark.agent)

        # Mark core tests
        if any(module in item.nodeid for module in ["fetcher", "indicators", "validation", "risk"]):
            item.add_marker(pytest.mark.core)
