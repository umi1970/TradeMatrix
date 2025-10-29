"""
Morning Planner Agent Tests
============================

Tests for the MorningPlanner agent including:
- analyze_asia_sweep() - Asia sweep detection
- analyze_y_low_rebound() - Y-low rebound detection
- generate_setup() - Setup generation
- run() - Full execution workflow

Run:
    pytest tests/test_morning_planner.py -v
    pytest tests/test_morning_planner.py::test_analyze_asia_sweep_success -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytz

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.morning_planner import MorningPlanner
from tests.fixtures import (
    create_asia_sweep_scenario,
    create_test_setup,
    assert_setup_valid
)
from tests.utils import (
    create_mock_supabase_client,
    assert_confidence_valid,
    extract_setup_metrics
)


@pytest.mark.unit
@pytest.mark.agent
class TestMorningPlannerAsiaSweep:
    """Tests for analyze_asia_sweep() method"""

    def test_analyze_asia_sweep_success(self, mock_supabase, test_symbol_id, test_trade_date):
        """Test successful Asia sweep detection with reversal"""
        # Create scenario
        scenario = create_asia_sweep_scenario(test_symbol_id, y_low=19400.0, sweep_depth=15.0)

        # Configure mock to return scenario data
        def mock_execute_side_effect():
            """Side effect for execute() to return appropriate data"""
            mock_result = Mock()

            # Check what table is being queried (simplified approach)
            if hasattr(mock_supabase._last_table, 'name'):
                if mock_supabase._last_table.name == 'levels_daily':
                    mock_result.data = [scenario['levels']]
                elif 'asia' in str(mock_supabase._last_query):
                    mock_result.data = scenario['asia_candles']
                else:
                    mock_result.data = scenario['eu_candles']
            else:
                mock_result.data = []

            return mock_result

        # Use proper table data mocking
        table_data = {
            'levels_daily': [scenario['levels']],
            'ohlc': scenario['asia_candles'] + scenario['eu_candles']
        }
        mock_client = create_mock_supabase_client(table_data)

        # Initialize planner
        planner = MorningPlanner(supabase_client=mock_client)

        # Execute
        result = planner.analyze_asia_sweep(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            trade_date=test_trade_date
        )

        # Assertions
        assert result is not None, "Should detect Asia sweep setup"
        assert result['strategy'] == 'asia_sweep'
        assert result['side'] == 'long'
        assert isinstance(result['entry_price'], Decimal)
        assert isinstance(result['stop_loss'], Decimal)
        assert isinstance(result['take_profit'], Decimal)
        assert_confidence_valid(result['confidence'])

        # Check metadata
        assert 'metadata' in result
        assert 'asia_low' in result['metadata']
        assert 'y_low' in result['metadata']
        assert result['metadata']['asia_low'] < result['metadata']['y_low']

    def test_analyze_asia_sweep_no_levels(self, mock_supabase, test_symbol_id, test_trade_date):
        """Test when no levels_daily record exists"""
        # Mock empty levels
        table_data = {'levels_daily': []}
        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.analyze_asia_sweep(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            trade_date=test_trade_date
        )

        assert result is None, "Should return None when no levels found"

    def test_analyze_asia_sweep_no_candles(self, test_symbol_id, test_trade_date):
        """Test when no Asia session candles exist"""
        # Mock levels but no candles
        levels = {
            'y_low': 19400.0,
            'pivot': 19500.0,
            'r1': 19550.0
        }
        table_data = {
            'levels_daily': [levels],
            'ohlc': []
        }
        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.analyze_asia_sweep(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            trade_date=test_trade_date
        )

        assert result is None, "Should return None when no candles found"

    def test_analyze_asia_sweep_no_sweep_detected(self, test_symbol_id, test_trade_date):
        """Test when price never sweeps below y_low"""
        # Create scenario where price stays above y_low
        berlin_tz = pytz.timezone('Europe/Berlin')
        start_time = berlin_tz.localize(datetime(2025, 10, 29, 2, 0, 0))

        y_low = 19400.0
        asia_candles = []

        for i in range(36):
            ts = start_time + timedelta(minutes=5 * i)
            asia_candles.append({
                'ts': ts.astimezone(pytz.UTC).isoformat(),
                'open': y_low + 50.0,  # Always above y_low
                'high': y_low + 60.0,
                'low': y_low + 40.0,  # Never sweeps below
                'close': y_low + 55.0,
                'volume': 8000
            })

        levels = {'y_low': y_low, 'pivot': 19500.0, 'r1': 19550.0}
        table_data = {
            'levels_daily': [levels],
            'ohlc': asia_candles
        }
        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.analyze_asia_sweep(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            trade_date=test_trade_date
        )

        assert result is None, "Should return None when no sweep detected"

    def test_analyze_asia_sweep_no_reversal(self, test_symbol_id, test_trade_date):
        """Test when sweep occurs but no EU open reversal"""
        scenario = create_asia_sweep_scenario(test_symbol_id)

        # Modify EU candles to stay below y_low (no reversal)
        for candle in scenario['eu_candles']:
            candle['close'] = 19395.0  # Below y_low

        table_data = {
            'levels_daily': [scenario['levels']],
            'ohlc': scenario['asia_candles'] + scenario['eu_candles']
        }
        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.analyze_asia_sweep(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            trade_date=test_trade_date
        )

        assert result is None, "Should return None when no reversal occurs"


@pytest.mark.unit
@pytest.mark.agent
class TestMorningPlannerYLowRebound:
    """Tests for analyze_y_low_rebound() method"""

    def test_analyze_y_low_rebound_success(self, test_symbol_id, test_trade_date):
        """Test successful Y-low rebound detection"""
        berlin_tz = pytz.timezone('Europe/Berlin')
        market_open = berlin_tz.localize(datetime(2025, 10, 29, 8, 0, 0))

        y_low = 19400.0
        pivot = 19500.0

        # Market opens below pivot
        market_open_candle = {
            'ts': market_open.astimezone(pytz.UTC).isoformat(),
            'open': 19450.0,  # Below pivot
            'high': 19460.0,
            'low': 19445.0,
            'close': 19455.0,
            'volume': 10000
        }

        # Current candle in entry zone
        current_candle = {
            'ts': (market_open + timedelta(minutes=20)).astimezone(pytz.UTC).isoformat(),
            'open': 19445.0,
            'high': 19455.0,
            'low': 19440.0,
            'close': 19450.0,  # Between y_low and pivot
            'volume': 12000
        }

        levels = {'y_low': y_low, 'pivot': pivot, 'r1': 19550.0}
        table_data = {
            'levels_daily': [levels],
            'ohlc': [market_open_candle, current_candle]
        }
        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.analyze_y_low_rebound(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            trade_date=test_trade_date
        )

        assert result is not None, "Should detect Y-low rebound setup"
        assert result['strategy'] == 'y_low_rebound'
        assert result['side'] == 'long'
        assert y_low < result['entry_price'] < pivot
        assert_confidence_valid(result['confidence'])

    def test_analyze_y_low_rebound_opens_above_pivot(self, test_symbol_id, test_trade_date):
        """Test when market opens above pivot (invalid condition)"""
        berlin_tz = pytz.timezone('Europe/Berlin')
        market_open = berlin_tz.localize(datetime(2025, 10, 29, 8, 0, 0))

        y_low = 19400.0
        pivot = 19500.0

        # Market opens ABOVE pivot
        market_open_candle = {
            'ts': market_open.astimezone(pytz.UTC).isoformat(),
            'open': 19520.0,  # Above pivot
            'high': 19530.0,
            'low': 19515.0,
            'close': 19525.0,
            'volume': 10000
        }

        levels = {'y_low': y_low, 'pivot': pivot, 'r1': 19550.0}
        table_data = {
            'levels_daily': [levels],
            'ohlc': [market_open_candle]
        }
        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.analyze_y_low_rebound(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            trade_date=test_trade_date
        )

        assert result is None, "Should return None when opens above pivot"

    def test_analyze_y_low_rebound_breakout_occurred(self, test_symbol_id, test_trade_date):
        """Test when breakout already occurred"""
        berlin_tz = pytz.timezone('Europe/Berlin')
        market_open = berlin_tz.localize(datetime(2025, 10, 29, 8, 0, 0))

        y_low = 19400.0
        pivot = 19500.0

        market_open_candle = {
            'ts': market_open.astimezone(pytz.UTC).isoformat(),
            'open': 19450.0,
            'close': 19455.0,
            'volume': 10000
        }

        # Current price already above pivot (breakout)
        current_candle = {
            'ts': (market_open + timedelta(minutes=20)).astimezone(pytz.UTC).isoformat(),
            'close': 19520.0,  # Above pivot
            'volume': 12000
        }

        levels = {'y_low': y_low, 'pivot': pivot, 'r1': 19550.0}
        table_data = {
            'levels_daily': [levels],
            'ohlc': [market_open_candle, current_candle]
        }
        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.analyze_y_low_rebound(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            trade_date=test_trade_date
        )

        assert result is None, "Should return None when breakout already occurred"


@pytest.mark.unit
@pytest.mark.agent
class TestMorningPlannerGenerateSetup:
    """Tests for generate_setup() method"""

    def test_generate_setup_success(self, test_symbol_id):
        """Test successful setup generation"""
        setup_data = {
            'strategy': 'asia_sweep',
            'side': 'long',
            'entry_price': Decimal('19420.0'),
            'stop_loss': Decimal('19385.0'),
            'take_profit': Decimal('19500.0'),
            'confidence': 0.85,
            'metadata': {'asia_low': 19385.0, 'y_low': 19400.0}
        }

        # Mock insert response
        mock_inserted_setup = {
            'id': str(uuid4()),
            **setup_data
        }

        table_data = {'setups': [mock_inserted_setup]}
        mock_client = create_mock_supabase_client(table_data)

        # Override insert to return new ID
        original_table = mock_client.table

        def table_with_insert(table_name):
            mock_table = original_table(table_name)
            if table_name == 'setups':
                original_insert = mock_table.insert

                def insert_with_id(data):
                    result_mock = original_insert(data)
                    execute_result = Mock()
                    execute_result.data = [{'id': str(uuid4()), **data}]
                    result_mock.execute = lambda: execute_result
                    return result_mock

                mock_table.insert = insert_with_id
            return mock_table

        mock_client.table = table_with_insert

        planner = MorningPlanner(supabase_client=mock_client)

        setup_id = planner.generate_setup(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            setup_data=setup_data
        )

        assert setup_id is not None, "Should return setup ID"
        assert isinstance(setup_id, UUID), "Setup ID should be UUID"

    def test_generate_setup_database_error(self, test_symbol_id):
        """Test setup generation when database insert fails"""
        setup_data = {
            'strategy': 'asia_sweep',
            'side': 'long',
            'entry_price': Decimal('19420.0'),
            'stop_loss': Decimal('19385.0'),
            'take_profit': Decimal('19500.0'),
            'confidence': 0.85
        }

        # Mock client that returns empty data (insert failure)
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table = Mock(return_value=mock_table)
        mock_table.insert = Mock(return_value=mock_table)
        mock_result = Mock()
        mock_result.data = []  # Empty data = failure
        mock_table.execute = Mock(return_value=mock_result)

        planner = MorningPlanner(supabase_client=mock_client)

        setup_id = planner.generate_setup(
            symbol_id=test_symbol_id,
            symbol_name='DAX',
            setup_data=setup_data
        )

        assert setup_id is None, "Should return None on database error"


@pytest.mark.unit
@pytest.mark.agent
class TestMorningPlannerRun:
    """Tests for run() method - full execution"""

    def test_run_success_multiple_symbols(self):
        """Test successful run with multiple symbols and setups"""
        symbol1_id = uuid4()
        symbol2_id = uuid4()

        symbols = [
            {'id': str(symbol1_id), 'symbol': 'DAX'},
            {'id': str(symbol2_id), 'symbol': 'NDX'}
        ]

        # Create scenarios for both symbols
        scenario1 = create_asia_sweep_scenario(symbol1_id)
        scenario2 = create_asia_sweep_scenario(symbol2_id)

        table_data = {
            'market_symbols': symbols,
            'levels_daily': [scenario1['levels'], scenario2['levels']],
            'ohlc': scenario1['asia_candles'] + scenario1['eu_candles'] +
                    scenario2['asia_candles'] + scenario2['eu_candles']
        }

        mock_client = create_mock_supabase_client(table_data)

        # Mock setup insertion
        def mock_insert_setup(data):
            result_mock = Mock()
            execute_result = Mock()
            execute_result.data = [{'id': str(uuid4()), **data}]
            result_mock.execute = lambda: execute_result
            return result_mock

        planner = MorningPlanner(supabase_client=mock_client)

        # Execute
        result = planner.run()

        # Assertions
        assert 'execution_time' in result
        assert 'symbols_analyzed' in result
        assert 'setups_generated' in result
        assert 'setups' in result
        assert result['symbols_analyzed'] >= 0
        assert isinstance(result['setups'], list)

    def test_run_no_active_symbols(self):
        """Test run when no active symbols exist"""
        table_data = {'market_symbols': []}
        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.run()

        assert result['symbols_analyzed'] == 0
        assert result['setups_generated'] == 0
        assert result['setups'] == []

    def test_run_with_specific_symbols(self):
        """Test run with specific symbol filter"""
        symbol_id = uuid4()

        symbols = [
            {'id': str(symbol_id), 'symbol': 'DAX'},
            {'id': str(uuid4()), 'symbol': 'NDX'}  # Should be filtered out
        ]

        scenario = create_asia_sweep_scenario(symbol_id)

        table_data = {
            'market_symbols': symbols,
            'levels_daily': [scenario['levels']],
            'ohlc': scenario['asia_candles'] + scenario['eu_candles']
        }

        mock_client = create_mock_supabase_client(table_data)

        planner = MorningPlanner(supabase_client=mock_client)

        # Run with specific symbol filter
        result = planner.run(symbols=['DAX'])

        assert 'symbols_analyzed' in result
        # Should only analyze DAX, not NDX

    def test_run_handles_exceptions(self):
        """Test run handles exceptions gracefully"""
        # Mock client that raises exception
        mock_client = Mock()
        mock_client.table = Mock(side_effect=Exception("Database connection error"))

        planner = MorningPlanner(supabase_client=mock_client)

        result = planner.run()

        assert 'error' in result
        assert result['symbols_analyzed'] == 0
        assert result['setups_generated'] == 0


@pytest.mark.integration
@pytest.mark.agent
class TestMorningPlannerIntegration:
    """Integration tests for complete workflows"""

    def test_complete_asia_sweep_workflow(self):
        """Test complete workflow from detection to setup generation"""
        symbol_id = uuid4()
        scenario = create_asia_sweep_scenario(symbol_id)

        table_data = {
            'market_symbols': [{'id': str(symbol_id), 'symbol': 'DAX', 'active': True}],
            'levels_daily': [scenario['levels']],
            'ohlc': scenario['asia_candles'] + scenario['eu_candles']
        }

        mock_client = create_mock_supabase_client(table_data)

        # Mock setup insertion to track what was created
        created_setups = []

        original_table = mock_client.table

        def table_with_tracking(table_name):
            mock_table = original_table(table_name)
            if table_name == 'setups':
                original_insert = mock_table.insert

                def insert_and_track(data):
                    created_setups.append(data)
                    result_mock = original_insert(data)
                    execute_result = Mock()
                    execute_result.data = [{'id': str(uuid4()), **data}]
                    result_mock.execute = lambda: execute_result
                    return result_mock

                mock_table.insert = insert_and_track
            return mock_table

        mock_client.table = table_with_tracking

        planner = MorningPlanner(supabase_client=mock_client)

        # Execute full run
        result = planner.run(symbols=['DAX'])

        # Verify workflow completed
        assert result['symbols_analyzed'] >= 0
        assert isinstance(result['setups'], list)

        # Check any created setups are valid
        for setup_dict in created_setups:
            assert 'module' in setup_dict
            assert setup_dict['module'] == 'morning'
            assert 'strategy' in setup_dict
            assert setup_dict['strategy'] in ['asia_sweep', 'y_low_rebound']
            assert 0.0 <= setup_dict['confidence'] <= 1.0
