"""
TradeMatrix.ai - ChartWatcher Test Suite
Tests chart image analysis and pattern detection with OpenAI Vision API
"""

import logging
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4
import base64

import sys
import os

# Add agents src to path
agents_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.insert(0, agents_src_path)

# Add API src to path for config
api_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api/src'))
sys.path.insert(0, api_src_path)

from chart_watcher import ChartWatcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def chart_watcher(mock_supabase_client):
    """Create ChartWatcher instance with mocked dependencies"""
    with patch('chart_watcher.OpenAI') as mock_openai:
        watcher = ChartWatcher(
            supabase_client=mock_supabase_client,
            openai_api_key="test-api-key"
        )
        watcher.openai_client = Mock()
        return watcher


def test_chart_watcher_initialization(chart_watcher):
    """Test ChartWatcher initialization"""
    print("\n" + "="*80)
    print("TEST 1: ChartWatcher Initialization")
    print("="*80)

    assert chart_watcher is not None
    assert chart_watcher.supabase is not None
    assert chart_watcher.openai_client is not None
    print("✅ ChartWatcher initialized successfully")


def test_download_chart_success(chart_watcher):
    """Test successful chart download"""
    print("\n" + "="*80)
    print("TEST 2: Chart Download (Success)")
    print("="*80)

    test_url = "https://example.com/chart.png"
    fake_image_data = b"fake-png-data"

    with patch('httpx.Client') as mock_httpx_client:
        # Setup mock response
        mock_response = Mock()
        mock_response.content = fake_image_data
        mock_response.raise_for_status = Mock()

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=False)

        mock_httpx_client.return_value = mock_client_instance

        # Test download
        result = chart_watcher.download_chart(test_url)

        assert result == fake_image_data
        assert len(result) == len(fake_image_data)
        print(f"✅ Downloaded {len(result)} bytes from {test_url}")


def test_download_chart_failure(chart_watcher):
    """Test chart download failure"""
    print("\n" + "="*80)
    print("TEST 3: Chart Download (Failure)")
    print("="*80)

    test_url = "https://example.com/nonexistent.png"

    with patch('httpx.Client') as mock_httpx_client:
        # Setup mock to raise error
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = Exception("404 Not Found")
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=False)

        mock_httpx_client.return_value = mock_client_instance

        # Test download failure
        result = chart_watcher.download_chart(test_url)

        assert result is None
        print("✅ Correctly handled download failure")


def test_extract_price_values(chart_watcher):
    """Test price value extraction from chart image"""
    print("\n" + "="*80)
    print("TEST 4: Extract Price Values from Chart")
    print("="*80)

    fake_image_data = b"fake-chart-image"
    symbol_name = "DAX"

    # Mock OpenAI response
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()
    mock_message.content = '''
    {
        "current_price": 18500.50,
        "high_24h": 18650.00,
        "low_24h": 18420.00,
        "visible_levels": [18300.0, 18200.0, 18700.0],
        "confidence": 0.85
    }
    '''
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    chart_watcher.openai_client.chat.completions.create = Mock(return_value=mock_response)

    # Test extraction
    result = chart_watcher.extract_price_values(fake_image_data, symbol_name)

    assert result is not None
    assert result['current_price'] == 18500.50
    assert result['high_24h'] == 18650.00
    assert result['low_24h'] == 18420.00
    assert len(result['visible_levels']) == 3
    assert result['confidence'] == 0.85

    print(f"\n✅ Extracted price values:")
    print(f"   Current Price: {result['current_price']}")
    print(f"   High 24h: {result['high_24h']}")
    print(f"   Low 24h: {result['low_24h']}")
    print(f"   Visible Levels: {result['visible_levels']}")
    print(f"   Confidence: {result['confidence']}")


def test_detect_patterns_head_and_shoulders(chart_watcher):
    """Test Head & Shoulders pattern detection"""
    print("\n" + "="*80)
    print("TEST 5: Detect Head & Shoulders Pattern")
    print("="*80)

    fake_image_data = b"fake-chart-with-pattern"
    symbol_name = "NDX"
    context = {'current_price': 16500.0, 'timeframe': '1h'}

    # Mock OpenAI response with detected pattern
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()
    mock_message.content = '''
    {
        "patterns": [
            {
                "name": "head_and_shoulders",
                "type": "bearish",
                "confidence": 0.82,
                "description": "Clear head and shoulders formation with neckline at 16450",
                "key_levels": {
                    "neckline": 16450.0,
                    "target": 16200.0,
                    "left_shoulder": 16480.0,
                    "head": 16550.0,
                    "right_shoulder": 16490.0
                }
            }
        ],
        "trend": "bearish",
        "support_levels": [16400.0, 16300.0, 16200.0],
        "resistance_levels": [16550.0, 16600.0],
        "analysis_summary": "Bearish head and shoulders pattern suggests potential downside to 16200 level"
    }
    '''
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    chart_watcher.openai_client.chat.completions.create = Mock(return_value=mock_response)

    # Test pattern detection
    result = chart_watcher.detect_patterns(fake_image_data, symbol_name, context)

    assert result is not None
    assert len(result['patterns']) == 1
    assert result['patterns'][0]['name'] == 'head_and_shoulders'
    assert result['patterns'][0]['type'] == 'bearish'
    assert result['patterns'][0]['confidence'] == 0.82
    assert result['trend'] == 'bearish'
    assert len(result['support_levels']) == 3
    assert len(result['resistance_levels']) == 2

    print(f"\n✅ Detected Pattern:")
    print(f"   Name: {result['patterns'][0]['name']}")
    print(f"   Type: {result['patterns'][0]['type']}")
    print(f"   Confidence: {result['patterns'][0]['confidence']}")
    print(f"   Description: {result['patterns'][0]['description']}")
    print(f"\n   Key Levels:")
    for level_name, level_value in result['patterns'][0]['key_levels'].items():
        print(f"     {level_name}: {level_value}")
    print(f"\n   Trend: {result['trend']}")
    print(f"   Support Levels: {result['support_levels']}")
    print(f"   Resistance Levels: {result['resistance_levels']}")


def test_detect_patterns_multiple(chart_watcher):
    """Test multiple pattern detection"""
    print("\n" + "="*80)
    print("TEST 6: Detect Multiple Patterns")
    print("="*80)

    fake_image_data = b"fake-chart-with-multiple-patterns"
    symbol_name = "EUR/USD"
    context = {'current_price': 1.0850, 'timeframe': '4h'}

    # Mock OpenAI response with multiple patterns
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()
    mock_message.content = '''
    {
        "patterns": [
            {
                "name": "ascending_triangle",
                "type": "bullish",
                "confidence": 0.78,
                "description": "Ascending triangle forming with flat resistance at 1.0880",
                "key_levels": {
                    "resistance": 1.0880,
                    "breakout_target": 1.0920
                }
            },
            {
                "name": "bull_flag",
                "type": "bullish",
                "confidence": 0.65,
                "description": "Bull flag consolidation after strong upward move",
                "key_levels": {
                    "flag_high": 1.0870,
                    "flag_low": 1.0830,
                    "target": 1.0910
                }
            }
        ],
        "trend": "bullish",
        "support_levels": [1.0830, 1.0800, 1.0770],
        "resistance_levels": [1.0880, 1.0920],
        "analysis_summary": "Multiple bullish continuation patterns suggest upside potential to 1.0920"
    }
    '''
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    chart_watcher.openai_client.chat.completions.create = Mock(return_value=mock_response)

    # Test pattern detection
    result = chart_watcher.detect_patterns(fake_image_data, symbol_name, context)

    assert result is not None
    assert len(result['patterns']) == 2
    assert result['patterns'][0]['name'] == 'ascending_triangle'
    assert result['patterns'][1]['name'] == 'bull_flag'
    assert result['trend'] == 'bullish'

    print(f"\n✅ Detected {len(result['patterns'])} Patterns:")
    for i, pattern in enumerate(result['patterns'], 1):
        print(f"\n   Pattern {i}:")
        print(f"     Name: {pattern['name']}")
        print(f"     Type: {pattern['type']}")
        print(f"     Confidence: {pattern['confidence']}")
        print(f"     Description: {pattern['description']}")


def test_calculate_overall_confidence(chart_watcher):
    """Test overall confidence score calculation"""
    print("\n" + "="*80)
    print("TEST 7: Calculate Overall Confidence Score")
    print("="*80)

    # Test with multiple patterns
    pattern_data = {
        'patterns': [
            {'name': 'pattern1', 'confidence': 0.85},
            {'name': 'pattern2', 'confidence': 0.75},
            {'name': 'pattern3', 'confidence': 0.90}
        ]
    }

    confidence = chart_watcher._calculate_overall_confidence(pattern_data)

    expected_avg = (0.85 + 0.75 + 0.90) / 3
    assert confidence == round(expected_avg, 2)

    print(f"\n✅ Overall Confidence Calculation:")
    print(f"   Pattern Confidences: [0.85, 0.75, 0.90]")
    print(f"   Calculated Average: {confidence}")
    print(f"   Expected: {round(expected_avg, 2)}")

    # Test with no patterns
    pattern_data_empty = {'patterns': []}
    confidence_empty = chart_watcher._calculate_overall_confidence(pattern_data_empty)
    assert confidence_empty == 0.0
    print(f"\n✅ No patterns: Confidence = {confidence_empty}")


def test_analyze_chart_full_workflow(chart_watcher):
    """Test complete chart analysis workflow"""
    print("\n" + "="*80)
    print("TEST 8: Complete Chart Analysis Workflow")
    print("="*80)

    symbol_id = uuid4()
    symbol_name = "DAX"
    chart_url = "https://example.com/dax_chart.png"
    timeframe = "1h"

    fake_image_data = b"fake-chart-image"

    # Mock download
    with patch.object(chart_watcher, 'download_chart', return_value=fake_image_data):
        # Mock OHLC query for context
        mock_table = Mock()
        mock_result = Mock()
        mock_result.data = [{'close': 18500.0}]
        mock_table.execute.return_value = mock_result
        mock_table.limit.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.select.return_value = mock_table

        chart_watcher.supabase.table.return_value = mock_table

        # Mock extract_price_values
        price_data = {
            'current_price': 18500.0,
            'high_24h': 18600.0,
            'low_24h': 18400.0,
            'visible_levels': [18300.0, 18700.0],
            'confidence': 0.85
        }
        with patch.object(chart_watcher, 'extract_price_values', return_value=price_data):
            # Mock detect_patterns
            pattern_data = {
                'patterns': [
                    {
                        'name': 'double_top',
                        'type': 'bearish',
                        'confidence': 0.80,
                        'description': 'Double top at 18600',
                        'key_levels': {'neckline': 18450.0}
                    }
                ],
                'trend': 'bearish',
                'support_levels': [18400.0, 18300.0],
                'resistance_levels': [18600.0],
                'analysis_summary': 'Bearish double top pattern'
            }
            with patch.object(chart_watcher, 'detect_patterns', return_value=pattern_data):
                # Mock database insert
                mock_insert_result = Mock()
                mock_insert_result.data = [{'id': str(uuid4())}]
                mock_insert_table = Mock()
                mock_insert_table.execute.return_value = mock_insert_result
                mock_insert_table.insert.return_value = mock_insert_table

                # Setup table mock to return insert mock for chart_analyses
                def table_side_effect(table_name):
                    if table_name == 'chart_analyses':
                        return mock_insert_table
                    return mock_table

                chart_watcher.supabase.table.side_effect = table_side_effect

                # Test full workflow
                result = chart_watcher.analyze_chart(symbol_id, symbol_name, chart_url, timeframe)

                assert result is not None
                print(f"\n✅ Chart Analysis Complete:")
                print(f"   Symbol: {symbol_name}")
                print(f"   Timeframe: {timeframe}")
                print(f"   Analysis ID: {result}")
                print(f"   Patterns Detected: {len(pattern_data['patterns'])}")
                print(f"   Trend: {pattern_data['trend']}")


def run_all_tests():
    """Run all tests manually"""
    print("\n" + "="*80)
    print("ChartWatcher Agent - Test Suite")
    print("="*80)

    # Create fixtures
    mock_supabase = Mock()
    with patch('chart_watcher.OpenAI') as mock_openai:
        watcher = ChartWatcher(
            supabase_client=mock_supabase,
            openai_api_key="test-api-key"
        )
        watcher.openai_client = Mock()

        # Run tests
        test_chart_watcher_initialization(watcher)
        test_download_chart_success(watcher)
        test_download_chart_failure(watcher)
        test_extract_price_values(watcher)
        test_detect_patterns_head_and_shoulders(watcher)
        test_detect_patterns_multiple(watcher)
        test_calculate_overall_confidence(watcher)
        test_analyze_chart_full_workflow(watcher)

    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)


if __name__ == "__main__":
    # Run tests manually
    run_all_tests()
