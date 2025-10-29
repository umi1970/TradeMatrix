"""
Test Suite for Market Data Integration
=======================================

Tests for:
- MarketDataFetcher functionality
- Database operations
- Celery tasks
- API endpoints (manual testing)

Run with:
    pytest test_market_data_integration.py -v

Author: TradeMatrix.ai Development Team
Date: 2025-10-29
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../api/src'))

from core.market_data_fetcher import (
    MarketDataFetcher,
    MarketDataFetcherError,
    RateLimitError,
    SymbolNotFoundError,
    APIError
)

# ================================================
# Fixtures
# ================================================

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock_client = Mock()
    mock_client.table = Mock(return_value=mock_client)
    mock_client.select = Mock(return_value=mock_client)
    mock_client.eq = Mock(return_value=mock_client)
    mock_client.single = Mock(return_value=mock_client)
    mock_client.upsert = Mock(return_value=mock_client)
    mock_client.execute = Mock(return_value=Mock(data=[{'id': 'test-uuid'}]))
    return mock_client


@pytest.fixture
def fetcher(mock_supabase):
    """Create MarketDataFetcher with mocked Supabase"""
    return MarketDataFetcher(
        api_key='test_api_key',
        supabase_client=mock_supabase
    )


@pytest.fixture
def sample_quote_response():
    """Sample quote response from Twelve Data API"""
    return {
        'symbol': 'DAX',
        'open': '18500.0',
        'high': '18650.0',
        'low': '18450.0',
        'close': '18600.0',
        'volume': '1234567',
        'datetime': '2025-10-29 12:00:00',
        'previous_close': '18550.0',
        'percent_change': '0.27',
        'change': '50.0',
        'exchange': 'XETRA',
        'currency': 'EUR',
        'is_market_open': True
    }


@pytest.fixture
def sample_time_series_response():
    """Sample time series response from Twelve Data API"""
    return {
        'meta': {
            'symbol': 'DAX',
            'interval': '1h',
            'currency': 'EUR',
            'exchange_timezone': 'Europe/Berlin'
        },
        'values': [
            {
                'datetime': '2025-10-29 12:00:00',
                'open': '18500.0',
                'high': '18550.0',
                'low': '18480.0',
                'close': '18520.0',
                'volume': '123456'
            },
            {
                'datetime': '2025-10-29 11:00:00',
                'open': '18480.0',
                'high': '18510.0',
                'low': '18460.0',
                'close': '18500.0',
                'volume': '134567'
            }
        ],
        'status': 'ok'
    }


# ================================================
# Test: MarketDataFetcher Initialization
# ================================================

def test_fetcher_initialization():
    """Test fetcher initializes correctly"""
    fetcher = MarketDataFetcher(api_key='test_key')
    assert fetcher.api_key == 'test_key'
    assert fetcher.supabase is not None
    assert fetcher.request_count == 0


def test_fetcher_initialization_without_api_key(mock_supabase):
    """Test fetcher initializes without API key (should warn but not fail)"""
    with patch.dict(os.environ, {}, clear=True):
        fetcher = MarketDataFetcher(supabase_client=mock_supabase)
        assert fetcher.api_key is None


# ================================================
# Test: API Request Handling
# ================================================

@patch('httpx.Client')
def test_make_request_success(mock_httpx, fetcher, sample_quote_response):
    """Test successful API request"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_quote_response

    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.get = Mock(return_value=mock_response)
    mock_httpx.return_value = mock_client

    result = fetcher._make_request('quote', {'symbol': 'DAX'})

    assert result == sample_quote_response
    assert fetcher.request_count == 1


@patch('httpx.Client')
def test_make_request_rate_limit(mock_httpx, fetcher):
    """Test rate limit handling"""
    mock_response = Mock()
    mock_response.status_code = 429

    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.get = Mock(return_value=mock_response)
    mock_httpx.return_value = mock_client

    with pytest.raises(RateLimitError):
        fetcher._make_request('quote', {'symbol': 'DAX'})


@patch('httpx.Client')
def test_make_request_api_error(mock_httpx, fetcher):
    """Test API error handling"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'status': 'error',
        'message': 'Invalid API key'
    }

    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.get = Mock(return_value=mock_response)
    mock_httpx.return_value = mock_client

    with pytest.raises(APIError, match='Invalid API key'):
        fetcher._make_request('quote', {'symbol': 'DAX'})


# ================================================
# Test: Quote Fetching
# ================================================

@patch.object(MarketDataFetcher, '_make_request')
def test_fetch_quote_success(mock_make_request, fetcher, sample_quote_response):
    """Test successful quote fetching"""
    mock_make_request.return_value = sample_quote_response

    result = fetcher.fetch_quote('DAX')

    assert result['symbol'] == 'DAX'
    assert result['close'] == '18600.0'
    mock_make_request.assert_called_once()


@patch.object(MarketDataFetcher, '_make_request')
def test_fetch_quote_empty_response(mock_make_request, fetcher):
    """Test empty quote response"""
    mock_make_request.return_value = {}

    with pytest.raises(APIError, match='Empty response'):
        fetcher.fetch_quote('DAX')


# ================================================
# Test: Time Series Fetching
# ================================================

@patch.object(MarketDataFetcher, '_make_request')
def test_fetch_time_series_success(mock_make_request, fetcher, sample_time_series_response):
    """Test successful time series fetching"""
    mock_make_request.return_value = sample_time_series_response

    result = fetcher.fetch_time_series('DAX', '1h', 100)

    assert len(result) == 2
    assert result[0]['datetime'] == '2025-10-29 12:00:00'
    assert result[0]['open'] == '18500.0'


@patch.object(MarketDataFetcher, '_make_request')
def test_fetch_time_series_no_data(mock_make_request, fetcher):
    """Test time series with no data"""
    mock_make_request.return_value = {'values': []}

    result = fetcher.fetch_time_series('DAX', '1h', 100)

    assert result == []


# ================================================
# Test: Database Operations
# ================================================

def test_get_symbol_id_success(fetcher, mock_supabase):
    """Test successful symbol ID retrieval"""
    mock_supabase.execute.return_value = Mock(data=[{'id': 'test-symbol-id'}])

    symbol_id = fetcher._get_symbol_id('DAX')

    assert symbol_id == 'test-symbol-id'


def test_get_symbol_id_not_found(fetcher, mock_supabase):
    """Test symbol not found error"""
    mock_supabase.execute.return_value = Mock(data=[])

    with pytest.raises(SymbolNotFoundError, match='DAX'):
        fetcher._get_symbol_id('DAX')


def test_save_to_database_success(fetcher, mock_supabase):
    """Test successful database save"""
    mock_supabase.execute.return_value = Mock(data=[{'id': 'test-uuid'}] * 2)

    candles = [
        {
            'datetime': '2025-10-29 12:00:00',
            'open': '18500.0',
            'high': '18550.0',
            'low': '18480.0',
            'close': '18520.0',
            'volume': '123456'
        },
        {
            'datetime': '2025-10-29 11:00:00',
            'open': '18480.0',
            'high': '18510.0',
            'low': '18460.0',
            'close': '18500.0',
            'volume': '134567'
        }
    ]

    count = fetcher.save_to_database('DAX', '1h', candles)

    assert count == 2


def test_save_to_database_empty_candles(fetcher):
    """Test saving empty candles list"""
    count = fetcher.save_to_database('DAX', '1h', [])
    assert count == 0


# ================================================
# Test: Current Price Saving
# ================================================

def test_save_current_price_success(fetcher, mock_supabase, sample_quote_response):
    """Test successful current price saving"""
    mock_supabase.execute.return_value = Mock(data=[{'id': 'test-price-id'}])

    success = fetcher.save_current_price('DAX', sample_quote_response)

    assert success is True


def test_save_current_price_invalid_price(fetcher, mock_supabase):
    """Test saving invalid price (price = 0)"""
    invalid_quote = {
        'close': '0',
        'open': '18500.0'
    }

    success = fetcher.save_current_price('DAX', invalid_quote)

    assert success is False


# ================================================
# Test: Batch Operations
# ================================================

@patch.object(MarketDataFetcher, 'fetch_time_series')
def test_batch_fetch_symbols(mock_fetch, fetcher):
    """Test batch fetching multiple symbols"""
    mock_fetch.return_value = [{'datetime': '2025-10-29 12:00:00', 'close': '18500.0'}]

    symbols = ['DAX', 'NDX', 'DJI']
    results = fetcher.batch_fetch_symbols(symbols, '1h', 50)

    assert len(results) == 3
    assert all(symbol in results for symbol in symbols)
    assert mock_fetch.call_count == 3


# ================================================
# Test: Caching
# ================================================

@patch.object(MarketDataFetcher, 'fetch_quote')
def test_fetch_and_save_current_price_uses_cache(mock_fetch_quote, fetcher, sample_quote_response):
    """Test that fetch_and_save_current_price uses cache"""
    mock_fetch_quote.return_value = sample_quote_response

    # First call - should fetch
    result1 = fetcher.fetch_and_save_current_price('DAX', use_cache=True)
    assert result1 == sample_quote_response
    assert mock_fetch_quote.call_count == 1

    # Second call - should use cache
    result2 = fetcher.fetch_and_save_current_price('DAX', use_cache=True)
    assert result2 == sample_quote_response
    assert mock_fetch_quote.call_count == 1  # Still 1, didn't call again


# ================================================
# Test: Error Recovery
# ================================================

@patch.object(MarketDataFetcher, 'fetch_time_series')
def test_batch_fetch_continues_on_error(mock_fetch, fetcher):
    """Test batch fetch continues even if one symbol fails"""
    def side_effect(symbol, *args, **kwargs):
        if symbol == 'INVALID':
            raise APIError('Symbol not found')
        return [{'datetime': '2025-10-29 12:00:00', 'close': '18500.0'}]

    mock_fetch.side_effect = side_effect

    symbols = ['DAX', 'INVALID', 'NDX']
    results = fetcher.batch_fetch_symbols(symbols, '1h', 50)

    assert len(results) == 3
    assert len(results['DAX']) > 0
    assert len(results['INVALID']) == 0
    assert len(results['NDX']) > 0


# ================================================
# Test: Celery Tasks (Unit Tests)
# ================================================

def test_celery_app_configuration():
    """Test Celery app is configured correctly"""
    from src.market_data_tasks import celery_app

    assert celery_app.conf.task_serializer == 'json'
    assert celery_app.conf.timezone == 'UTC'
    assert celery_app.conf.enable_utc is True


def test_tracked_symbols_defined():
    """Test tracked symbols list is defined"""
    from src.market_data_tasks import TRACKED_SYMBOLS, SYMBOL_NAMES

    assert len(TRACKED_SYMBOLS) > 0
    assert 'DAX' in SYMBOL_NAMES
    assert 'NDX' in SYMBOL_NAMES


# ================================================
# Test: Integration Helpers
# ================================================

def test_convenience_function():
    """Test fetch_and_save convenience function"""
    from core.market_data_fetcher import fetch_and_save

    with patch.object(MarketDataFetcher, 'fetch_time_series') as mock_fetch, \
         patch.object(MarketDataFetcher, 'save_to_database') as mock_save:

        mock_fetch.return_value = [{'datetime': '2025-10-29 12:00:00', 'close': '18500.0'}]
        mock_save.return_value = 1

        count = fetch_and_save('DAX', '1h', 100, api_key='test_key')

        assert count == 1
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()


# ================================================
# Manual Integration Tests (Run with real API)
# ================================================

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('TWELVE_DATA_API_KEY'), reason='API key not set')
def test_real_api_quote_fetch():
    """Test real API quote fetching (requires API key)"""
    api_key = os.getenv('TWELVE_DATA_API_KEY')
    fetcher = MarketDataFetcher(api_key=api_key)

    quote = fetcher.fetch_quote('DAX')

    assert 'symbol' in quote
    assert 'close' in quote
    assert float(quote['close']) > 0


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('TWELVE_DATA_API_KEY'), reason='API key not set')
def test_real_api_time_series_fetch():
    """Test real API time series fetching (requires API key)"""
    api_key = os.getenv('TWELVE_DATA_API_KEY')
    fetcher = MarketDataFetcher(api_key=api_key)

    candles = fetcher.fetch_time_series('DAX', '1h', 10)

    assert len(candles) > 0
    assert 'datetime' in candles[0]
    assert 'open' in candles[0]
    assert 'close' in candles[0]


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('TWELVE_DATA_API_KEY'), reason='API key not set')
def test_api_usage_check():
    """Test API usage endpoint (requires API key)"""
    api_key = os.getenv('TWELVE_DATA_API_KEY')
    fetcher = MarketDataFetcher(api_key=api_key)

    usage = fetcher.get_api_usage()

    assert 'current_usage' in usage or 'plan_limit' in usage


# ================================================
# Run Tests
# ================================================

if __name__ == '__main__':
    # Run with: python test_market_data_integration.py
    pytest.main([__file__, '-v', '--tb=short'])
