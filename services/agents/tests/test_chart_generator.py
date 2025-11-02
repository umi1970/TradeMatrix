#!/usr/bin/env python3
"""
Unit Tests for ChartGenerator Service

Test Coverage:
- Chart generation (happy path)
- Rate limiting
- Caching
- Error handling (invalid symbol, timeframe, API errors)
- Database operations
- Redis operations
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

# Add src directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chart_generator import ChartGenerator
from exceptions.chart_errors import (
    RateLimitError,
    ChartGenerationError,
    SymbolNotFoundError,
    InvalidTimeframeError,
    ChartAPIError,
)


# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    return mock


@pytest.fixture
def chart_generator(mock_supabase, mock_redis):
    """ChartGenerator instance with mocked dependencies"""
    with patch('chart_generator.create_client', return_value=mock_supabase):
        with patch('chart_generator.redis.from_url', return_value=mock_redis):
            generator = ChartGenerator()
            generator.supabase = mock_supabase
            generator.redis_client = mock_redis
            return generator


@pytest.fixture
def sample_symbol_config():
    """Sample symbol configuration"""
    return {
        'id': str(uuid4()),
        'symbol': '^GDAXI',
        'chart_img_symbol': 'XETR:DAX',
        'chart_enabled': True,
        'chart_config': {
            'timeframes': ['1h', '4h', '1d'],
            'indicators': ['EMA_20', 'EMA_50', 'RSI', 'Volume'],
            'default_timeframe': '4h',
            'theme': 'dark'
        }
    }


# =====================================================================
# TESTS: CHART GENERATION (HAPPY PATH)
# =====================================================================

def test_generate_chart_success(chart_generator, sample_symbol_config, mock_supabase, mock_redis):
    """Test successful chart generation"""
    symbol_id = sample_symbol_config['id']
    timeframe = '4h'
    chart_url = 'https://chart-img.com/i/abc123.png'

    # Mock database: symbol lookup
    mock_response = MagicMock()
    mock_response.data = [sample_symbol_config]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response

    # Mock Redis: no cache
    mock_redis.get.return_value = None

    # Mock API call
    with patch('chart_generator.httpx.Client') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'url': chart_url}
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        # Mock database: save snapshot
        mock_snapshot_response = MagicMock()
        mock_snapshot_response.data = [{
            'id': str(uuid4()),
            'symbol_id': symbol_id,
            'timeframe': timeframe,
            'chart_url': chart_url,
            'trigger_type': 'manual',
            'generated_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=60)).isoformat(),
            'metadata': {}
        }]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_snapshot_response

        # Execute
        result = chart_generator.generate_chart(
            symbol_id=symbol_id,
            timeframe=timeframe,
            trigger_type='manual'
        )

        # Assertions
        assert result['chart_url'] == chart_url
        assert result['cached'] is False
        assert 'snapshot_id' in result
        assert 'generated_at' in result


def test_generate_chart_from_cache(chart_generator, sample_symbol_config, mock_redis):
    """Test chart generation returns cached URL"""
    symbol_id = sample_symbol_config['id']
    timeframe = '4h'
    cached_url = 'https://chart-img.com/i/cached123.png'

    # Mock Redis: cache hit
    mock_redis.get.return_value = cached_url

    # Execute
    result = chart_generator.generate_chart(
        symbol_id=symbol_id,
        timeframe=timeframe
    )

    # Assertions
    assert result['chart_url'] == cached_url
    assert result['cached'] is True


# =====================================================================
# TESTS: RATE LIMITING
# =====================================================================

def test_rate_limit_warning(chart_generator, mock_redis, caplog):
    """Test rate limit warning at 80%"""
    # Mock Redis: 800 requests (80%)
    mock_redis.get.return_value = '800'

    # Execute
    current_count = chart_generator._check_rate_limit()

    # Assertions
    assert current_count == 800
    assert "Rate limit warning" in caplog.text


def test_rate_limit_exceeded(chart_generator, mock_redis):
    """Test rate limit hard stop at 95%"""
    # Mock Redis: 950 requests (95%)
    mock_redis.get.return_value = '950'

    # Execute & Assert
    with pytest.raises(RateLimitError) as exc_info:
        chart_generator._check_rate_limit()

    assert exc_info.value.current_count == 950
    assert exc_info.value.limit == 1000


def test_increment_request_counter(chart_generator, mock_redis):
    """Test request counter increment"""
    # Mock Redis: increment returns 1 (first request)
    mock_redis.incr.return_value = 1

    # Execute
    chart_generator._increment_request_counter()

    # Assertions
    assert mock_redis.incr.called
    assert mock_redis.expire.called  # Should set expiry for first request


# =====================================================================
# TESTS: CACHING
# =====================================================================

def test_cache_hit(chart_generator, mock_redis):
    """Test cache retrieval"""
    symbol_id = str(uuid4())
    timeframe = '4h'
    cached_url = 'https://chart-img.com/i/test.png'

    # Mock Redis: cache hit
    mock_redis.get.return_value = cached_url

    # Execute
    result = chart_generator._get_cached_chart(symbol_id, timeframe)

    # Assertions
    assert result == cached_url
    assert mock_redis.get.called


def test_cache_miss(chart_generator, mock_redis):
    """Test cache miss"""
    symbol_id = str(uuid4())
    timeframe = '4h'

    # Mock Redis: cache miss
    mock_redis.get.return_value = None

    # Execute
    result = chart_generator._get_cached_chart(symbol_id, timeframe)

    # Assertions
    assert result is None


def test_set_cache(chart_generator, mock_redis):
    """Test setting cache"""
    symbol_id = str(uuid4())
    timeframe = '4h'
    chart_url = 'https://chart-img.com/i/test.png'

    # Execute
    chart_generator._set_cached_chart(symbol_id, timeframe, chart_url)

    # Assertions
    assert mock_redis.setex.called
    call_args = mock_redis.setex.call_args
    assert call_args[0][1] == 300  # TTL = 5 minutes
    assert call_args[0][2] == chart_url


# =====================================================================
# TESTS: ERROR HANDLING
# =====================================================================

def test_invalid_symbol(chart_generator, mock_supabase):
    """Test symbol not found error"""
    symbol_id = str(uuid4())

    # Mock database: no symbol found
    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response

    # Execute & Assert
    with pytest.raises(SymbolNotFoundError) as exc_info:
        chart_generator._get_symbol_config(symbol_id)

    assert exc_info.value.symbol_id == symbol_id


def test_invalid_timeframe(chart_generator):
    """Test invalid timeframe error"""
    symbol_id = str(uuid4())
    invalid_timeframe = '999h'

    # Execute & Assert
    with pytest.raises(InvalidTimeframeError) as exc_info:
        chart_generator.generate_chart(
            symbol_id=symbol_id,
            timeframe=invalid_timeframe
        )

    assert exc_info.value.timeframe == invalid_timeframe


def test_api_error_500(chart_generator, sample_symbol_config, mock_supabase, mock_redis):
    """Test chart-img.com API error (500)"""
    symbol_id = sample_symbol_config['id']
    timeframe = '4h'

    # Mock database: symbol lookup
    mock_response = MagicMock()
    mock_response.data = [sample_symbol_config]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response

    # Mock Redis: no cache
    mock_redis.get.return_value = None

    # Mock API call: 500 error
    with patch('chart_generator.httpx.Client') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_response.json.side_effect = Exception('Not JSON')
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response

        # Execute & Assert
        with pytest.raises(ChartAPIError) as exc_info:
            chart_generator.generate_chart(
                symbol_id=symbol_id,
                timeframe=timeframe
            )

        assert exc_info.value.status_code == 500


def test_api_timeout(chart_generator, sample_symbol_config, mock_supabase, mock_redis):
    """Test chart-img.com API timeout"""
    symbol_id = sample_symbol_config['id']
    timeframe = '4h'

    # Mock database: symbol lookup
    mock_response = MagicMock()
    mock_response.data = [sample_symbol_config]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response

    # Mock Redis: no cache
    mock_redis.get.return_value = None

    # Mock API call: timeout
    with patch('chart_generator.httpx.Client') as mock_client:
        import httpx
        mock_client.return_value.__enter__.return_value.post.side_effect = httpx.TimeoutException('Timeout')

        # Execute & Assert
        with pytest.raises(ChartAPIError) as exc_info:
            chart_generator.generate_chart(
                symbol_id=symbol_id,
                timeframe=timeframe
            )

        assert exc_info.value.status_code == 408
        assert 'timed out' in exc_info.value.api_error_message


# =====================================================================
# TESTS: DATABASE OPERATIONS
# =====================================================================

def test_get_latest_chart_url(chart_generator, mock_supabase):
    """Test fetching latest chart URL from database"""
    symbol_id = str(uuid4())
    timeframe = '4h'
    chart_url = 'https://chart-img.com/i/latest.png'

    # Mock database: snapshot found
    mock_response = MagicMock()
    mock_response.data = [{
        'chart_url': chart_url,
        'generated_at': datetime.utcnow().isoformat()
    }]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_response

    # Execute
    result = chart_generator.get_latest_chart_url(symbol_id, timeframe)

    # Assertions
    assert result == chart_url


def test_cleanup_expired_snapshots(chart_generator, mock_supabase):
    """Test cleanup of expired snapshots"""
    # Mock database: cleanup procedure
    mock_response = MagicMock()
    mock_response.data = 5  # 5 snapshots deleted
    mock_supabase.rpc.return_value.execute.return_value = mock_response

    # Execute
    deleted_count = chart_generator.cleanup_expired_snapshots()

    # Assertions
    assert deleted_count == 5
    assert mock_supabase.rpc.called


# =====================================================================
# TESTS: USAGE STATS
# =====================================================================

def test_get_usage_stats(chart_generator, mock_redis):
    """Test getting usage statistics"""
    # Mock Redis: 245 requests today
    mock_redis.get.return_value = '245'

    # Execute
    stats = chart_generator.get_usage_stats()

    # Assertions
    assert stats['requests_today'] == 245
    assert stats['limit_daily'] == 1000
    assert stats['remaining'] == 755
    assert stats['percentage_used'] == 24.5
    assert 'date' in stats


# =====================================================================
# INTEGRATION TESTS (Optional - requires real Redis/Supabase)
# =====================================================================

@pytest.mark.integration
def test_integration_full_workflow():
    """
    Integration test for full workflow (requires real services)

    Skip this test in CI/CD unless Redis and Supabase are available.

    Run with: pytest -m integration
    """
    pytest.skip("Integration test requires real Redis and Supabase")


# =====================================================================
# RUN TESTS
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, '-v', '--tb=short'])
