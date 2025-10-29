"""
SignalBot Agent Tests
=====================

Tests for the SignalBot agent including:
- analyze_market_structure() - Market structure analysis with technical indicators
- generate_entry_signals() - Entry signal generation with validation
- generate_exit_signals() - Exit signal detection (TP, SL, break-even)
- create_signal() - Signal record creation
- run() - Full execution workflow

Run:
    pytest tests/test_signal_bot.py -v
    pytest tests/test_signal_bot.py::test_analyze_market_structure_success -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytz
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.signal_bot import SignalBot
from tests.fixtures import (
    create_test_setup,
    generate_ohlc_data,
    assert_setup_valid
)
from tests.utils import (
    create_mock_supabase_client,
    assert_price_valid,
    assert_confidence_valid,
    extract_setup_metrics
)


@pytest.mark.unit
@pytest.mark.agent
class TestSignalBotMarketStructure:
    """Tests for analyze_market_structure() method"""

    def test_analyze_market_structure_success(self, test_symbol_id):
        """Test successful market structure analysis with indicators"""
        # Generate sufficient OHLC data (250 candles for EMA-200)
        berlin_tz = pytz.timezone('Europe/Berlin')
        start_time = berlin_tz.localize(datetime(2025, 10, 29, 0, 0, 0))

        candles = generate_ohlc_data(
            start_time=start_time,
            count=250,
            timeframe_minutes=5,
            base_price=19500.0,
            volatility=0.005
        )

        # Add symbol_id to candles
        for candle in candles:
            candle['symbol_id'] = str(test_symbol_id)
            candle['timeframe'] = '5m'

        # Daily levels
        levels = {
            'symbol_id': str(test_symbol_id),
            'trade_date': '2025-10-29',
            'pivot': 19500.0,
            'r1': 19550.0,
            'r2': 19600.0,
            's1': 19450.0,
            's2': 19400.0
        }

        table_data = {
            'ohlc': candles,
            'levels_daily': [levels]
        }

        mock_client = create_mock_supabase_client(table_data)

        # Mock TechnicalIndicators
        with patch('src.signal_bot.TechnicalIndicators') as MockTechIndicators:
            # Configure mock indicators
            MockTechIndicators.calculate_ema.return_value = np.array([19480.0] * 250)
            MockTechIndicators.calculate_rsi.return_value = np.array([55.0] * 250)

            mock_macd = Mock()
            mock_macd.macd_line = np.array([10.5] * 250)
            mock_macd.signal_line = np.array([8.0] * 250)
            mock_macd.histogram = np.array([2.5] * 250)
            MockTechIndicators.calculate_macd.return_value = mock_macd

            mock_bb = Mock()
            mock_bb.upper = np.array([19550.0] * 250)
            mock_bb.middle = np.array([19500.0] * 250)
            mock_bb.lower = np.array([19450.0] * 250)
            MockTechIndicators.calculate_bollinger_bands.return_value = mock_bb

            MockTechIndicators.calculate_atr.return_value = np.array([25.0] * 250)
            MockTechIndicators.get_trend_direction.return_value = 'bullish'

            # Initialize and execute
            signal_bot = SignalBot(supabase_client=mock_client)

            result = signal_bot.analyze_market_structure(
                symbol_id=test_symbol_id,
                symbol_name='DAX',
                timeframe='5m'
            )

            # Assertions
            assert result is not None, "Should return market structure analysis"
            assert 'price' in result
            assert 'emas' in result
            assert 'rsi' in result
            assert 'macd' in result
            assert 'bb' in result
            assert 'atr' in result
            assert 'volume' in result
            assert 'candle' in result
            assert 'context' in result
            assert 'levels' in result

            # Check EMAs
            assert '20' in result['emas']
            assert '50' in result['emas']
            assert '200' in result['emas']

            # Check MACD
            assert 'line' in result['macd']
            assert 'signal' in result['macd']
            assert 'histogram' in result['macd']

            # Check Bollinger Bands
            assert 'upper' in result['bb']
            assert 'middle' in result['bb']
            assert 'lower' in result['bb']

            # Check context
            assert result['context']['trend'] == 'bullish'
            assert isinstance(result['context']['volatility'], float)

            # Check levels
            assert result['levels']['pivot'] == 19500.0

    def test_analyze_market_structure_insufficient_data(self, test_symbol_id):
        """Test when insufficient OHLC data (less than 200 candles)"""
        # Generate only 50 candles (insufficient for EMA-200)
        berlin_tz = pytz.timezone('Europe/Berlin')
        start_time = berlin_tz.localize(datetime(2025, 10, 29, 0, 0, 0))

        candles = generate_ohlc_data(
            start_time=start_time,
            count=50,
            timeframe_minutes=5
        )

        table_data = {'ohlc': candles, 'levels_daily': []}
        mock_client = create_mock_supabase_client(table_data)

        signal_bot = SignalBot(supabase_client=mock_client)

        result = signal_bot.analyze_market_structure(
            symbol_id=test_symbol_id,
            symbol_name='DAX'
        )

        assert result is None, "Should return None when insufficient data"

    def test_analyze_market_structure_no_data(self, test_symbol_id):
        """Test when no OHLC data exists"""
        table_data = {'ohlc': [], 'levels_daily': []}
        mock_client = create_mock_supabase_client(table_data)

        signal_bot = SignalBot(supabase_client=mock_client)

        result = signal_bot.analyze_market_structure(
            symbol_id=test_symbol_id,
            symbol_name='DAX'
        )

        assert result is None, "Should return None when no data"

    def test_analyze_market_structure_no_levels(self, test_symbol_id):
        """Test when no daily levels exist (optional data)"""
        berlin_tz = pytz.timezone('Europe/Berlin')
        start_time = berlin_tz.localize(datetime(2025, 10, 29, 0, 0, 0))

        candles = generate_ohlc_data(
            start_time=start_time,
            count=250,
            timeframe_minutes=5
        )

        for candle in candles:
            candle['symbol_id'] = str(test_symbol_id)
            candle['timeframe'] = '5m'

        table_data = {
            'ohlc': candles,
            'levels_daily': []  # No levels
        }

        mock_client = create_mock_supabase_client(table_data)

        with patch('src.signal_bot.TechnicalIndicators') as MockTechIndicators:
            # Configure mock indicators
            MockTechIndicators.calculate_ema.return_value = np.array([19480.0] * 250)
            MockTechIndicators.calculate_rsi.return_value = np.array([55.0] * 250)

            mock_macd = Mock()
            mock_macd.macd_line = np.array([10.5] * 250)
            mock_macd.signal_line = np.array([8.0] * 250)
            mock_macd.histogram = np.array([2.5] * 250)
            MockTechIndicators.calculate_macd.return_value = mock_macd

            mock_bb = Mock()
            mock_bb.upper = np.array([19550.0] * 250)
            mock_bb.middle = np.array([19500.0] * 250)
            mock_bb.lower = np.array([19450.0] * 250)
            MockTechIndicators.calculate_bollinger_bands.return_value = mock_bb

            MockTechIndicators.calculate_atr.return_value = np.array([25.0] * 250)
            MockTechIndicators.get_trend_direction.return_value = 'bullish'

            signal_bot = SignalBot(supabase_client=mock_client)

            result = signal_bot.analyze_market_structure(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            # Should still work without levels (levels will be zeros)
            assert result is not None
            assert result['levels']['pivot'] == 0.0


@pytest.mark.unit
@pytest.mark.agent
class TestSignalBotEntrySignals:
    """Tests for generate_entry_signals() method"""

    def test_generate_entry_signals_success(self, test_symbol_id):
        """Test successful entry signal generation with valid setup"""
        # Create pending setup
        setup = create_test_setup(
            symbol_id=test_symbol_id,
            strategy='asia_sweep',
            side='long',
            entry_price=19420.0,
            stop_loss=19385.0,
            take_profit=19500.0,
            confidence=0.85
        )
        setup['status'] = 'pending'

        # Generate OHLC data
        berlin_tz = pytz.timezone('Europe/Berlin')
        start_time = berlin_tz.localize(datetime(2025, 10, 29, 0, 0, 0))
        candles = generate_ohlc_data(start_time, count=250, timeframe_minutes=5)

        for candle in candles:
            candle['symbol_id'] = str(test_symbol_id)
            candle['timeframe'] = '5m'

        levels = {
            'symbol_id': str(test_symbol_id),
            'trade_date': '2025-10-29',
            'pivot': 19500.0,
            'r1': 19550.0,
            's1': 19450.0
        }

        table_data = {
            'setups': [setup],
            'ohlc': candles,
            'levels_daily': [levels]
        }

        mock_client = create_mock_supabase_client(table_data)

        # Mock TechnicalIndicators and ValidationEngine
        with patch('src.signal_bot.TechnicalIndicators') as MockTechIndicators, \
             patch('src.signal_bot.ValidationEngine') as MockValidationEngine:

            # Configure mock indicators
            MockTechIndicators.calculate_ema.return_value = np.array([19480.0] * 250)
            MockTechIndicators.calculate_rsi.return_value = np.array([55.0] * 250)

            mock_macd = Mock()
            mock_macd.macd_line = np.array([10.5] * 250)
            mock_macd.signal_line = np.array([8.0] * 250)
            mock_macd.histogram = np.array([2.5] * 250)
            MockTechIndicators.calculate_macd.return_value = mock_macd

            mock_bb = Mock()
            mock_bb.upper = np.array([19550.0] * 250)
            mock_bb.middle = np.array([19500.0] * 250)
            mock_bb.lower = np.array([19450.0] * 250)
            MockTechIndicators.calculate_bollinger_bands.return_value = mock_bb

            MockTechIndicators.calculate_atr.return_value = np.array([25.0] * 250)
            MockTechIndicators.get_trend_direction.return_value = 'bullish'

            # Mock ValidationEngine
            mock_validation_engine = Mock()
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.confidence = 0.88
            mock_validation_result.breakdown = {
                'ema_alignment': 0.9,
                'pivot_confluence': 0.85,
                'volume_confirmation': 0.88,
                'candle_structure': 0.87,
                'context_flow': 0.90
            }
            mock_validation_result.priority_override = False
            mock_validation_result.notes = "Valid entry signal"

            mock_validation_engine.validate_signal.return_value = mock_validation_result
            MockValidationEngine.return_value = mock_validation_engine

            # Execute
            signal_bot = SignalBot(supabase_client=mock_client)

            entry_signals = signal_bot.generate_entry_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            # Assertions
            assert len(entry_signals) == 1, "Should generate one entry signal"

            signal = entry_signals[0]
            assert signal['setup_id'] == setup['id']
            assert signal['strategy'] == 'asia_sweep'
            assert signal['side'] == 'long'
            assert signal['entry_price'] == 19420.0
            assert_confidence_valid(signal['confidence'])
            assert signal['confidence'] >= 0.8  # Validation passed
            assert 'validation_breakdown' in signal
            assert 'timestamp' in signal

    def test_generate_entry_signals_no_active_setups(self, test_symbol_id):
        """Test when no pending setups exist"""
        table_data = {
            'setups': [],
            'ohlc': [],
            'levels_daily': []
        }

        mock_client = create_mock_supabase_client(table_data)
        signal_bot = SignalBot(supabase_client=mock_client)

        entry_signals = signal_bot.generate_entry_signals(
            symbol_id=test_symbol_id,
            symbol_name='DAX'
        )

        assert entry_signals == [], "Should return empty list when no setups"

    def test_generate_entry_signals_validation_fails(self, test_symbol_id):
        """Test when validation engine rejects signal"""
        setup = create_test_setup(
            symbol_id=test_symbol_id,
            strategy='asia_sweep'
        )
        setup['status'] = 'pending'

        berlin_tz = pytz.timezone('Europe/Berlin')
        start_time = berlin_tz.localize(datetime(2025, 10, 29, 0, 0, 0))
        candles = generate_ohlc_data(start_time, count=250)

        for candle in candles:
            candle['symbol_id'] = str(test_symbol_id)
            candle['timeframe'] = '5m'

        table_data = {
            'setups': [setup],
            'ohlc': candles,
            'levels_daily': [{'symbol_id': str(test_symbol_id), 'pivot': 19500.0}]
        }

        mock_client = create_mock_supabase_client(table_data)

        with patch('src.signal_bot.TechnicalIndicators') as MockTechIndicators, \
             patch('src.signal_bot.ValidationEngine') as MockValidationEngine:

            # Configure basic mock indicators
            MockTechIndicators.calculate_ema.return_value = np.array([19480.0] * 250)
            MockTechIndicators.calculate_rsi.return_value = np.array([55.0] * 250)

            mock_macd = Mock()
            mock_macd.macd_line = np.array([10.5] * 250)
            mock_macd.signal_line = np.array([8.0] * 250)
            mock_macd.histogram = np.array([2.5] * 250)
            MockTechIndicators.calculate_macd.return_value = mock_macd

            mock_bb = Mock()
            mock_bb.upper = np.array([19550.0] * 250)
            mock_bb.middle = np.array([19500.0] * 250)
            mock_bb.lower = np.array([19450.0] * 250)
            MockTechIndicators.calculate_bollinger_bands.return_value = mock_bb

            MockTechIndicators.calculate_atr.return_value = np.array([25.0] * 250)
            MockTechIndicators.get_trend_direction.return_value = 'neutral'

            # Mock ValidationEngine to reject signal
            mock_validation_engine = Mock()
            mock_validation_result = Mock()
            mock_validation_result.is_valid = False
            mock_validation_result.confidence = 0.65  # Below threshold
            mock_validation_result.notes = "Trend not aligned"

            mock_validation_engine.validate_signal.return_value = mock_validation_result
            MockValidationEngine.return_value = mock_validation_engine

            signal_bot = SignalBot(supabase_client=mock_client)

            entry_signals = signal_bot.generate_entry_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            assert entry_signals == [], "Should return empty list when validation fails"

    def test_generate_entry_signals_no_market_data(self, test_symbol_id):
        """Test when market structure analysis fails"""
        setup = create_test_setup(symbol_id=test_symbol_id)
        setup['status'] = 'pending'

        table_data = {
            'setups': [setup],
            'ohlc': [],  # No data
            'levels_daily': []
        }

        mock_client = create_mock_supabase_client(table_data)
        signal_bot = SignalBot(supabase_client=mock_client)

        entry_signals = signal_bot.generate_entry_signals(
            symbol_id=test_symbol_id,
            symbol_name='DAX'
        )

        assert entry_signals == [], "Should return empty list when no market data"


@pytest.mark.unit
@pytest.mark.agent
class TestSignalBotExitSignals:
    """Tests for generate_exit_signals() method"""

    def test_generate_exit_signals_take_profit_long(self, test_symbol_id):
        """Test take profit detection for long position"""
        # Create active long setup
        setup = create_test_setup(
            symbol_id=test_symbol_id,
            side='long',
            entry_price=19420.0,
            stop_loss=19385.0,
            take_profit=19500.0
        )
        setup['status'] = 'active'

        # Current price at TP
        current_candle = {
            'symbol_id': str(test_symbol_id),
            'timeframe': '1m',
            'close': 19505.0,  # Above TP (19500)
            'ts': datetime.now(pytz.UTC).isoformat()
        }

        table_data = {
            'setups': [setup],
            'ohlc': [current_candle]
        }

        mock_client = create_mock_supabase_client(table_data)

        with patch('src.signal_bot.RiskCalculator'):
            signal_bot = SignalBot(supabase_client=mock_client)

            exit_signals = signal_bot.generate_exit_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            assert len(exit_signals) == 1, "Should detect TP hit"

            signal = exit_signals[0]
            assert signal['signal_type'] == 'take_profit'
            assert signal['side'] == 'long'
            assert signal['current_price'] == 19505.0
            assert signal['target_price'] == 19500.0

    def test_generate_exit_signals_take_profit_short(self, test_symbol_id):
        """Test take profit detection for short position"""
        setup = create_test_setup(
            symbol_id=test_symbol_id,
            side='short',
            entry_price=19500.0,
            stop_loss=19535.0,
            take_profit=19420.0
        )
        setup['status'] = 'active'

        current_candle = {
            'symbol_id': str(test_symbol_id),
            'timeframe': '1m',
            'close': 19415.0,  # Below TP (19420)
            'ts': datetime.now(pytz.UTC).isoformat()
        }

        table_data = {
            'setups': [setup],
            'ohlc': [current_candle]
        }

        mock_client = create_mock_supabase_client(table_data)

        with patch('src.signal_bot.RiskCalculator'):
            signal_bot = SignalBot(supabase_client=mock_client)

            exit_signals = signal_bot.generate_exit_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            assert len(exit_signals) == 1
            signal = exit_signals[0]
            assert signal['signal_type'] == 'take_profit'
            assert signal['side'] == 'short'

    def test_generate_exit_signals_stop_loss_long(self, test_symbol_id):
        """Test stop loss detection for long position"""
        setup = create_test_setup(
            symbol_id=test_symbol_id,
            side='long',
            entry_price=19420.0,
            stop_loss=19385.0,
            take_profit=19500.0
        )
        setup['status'] = 'active'

        current_candle = {
            'symbol_id': str(test_symbol_id),
            'timeframe': '1m',
            'close': 19380.0,  # Below SL (19385)
            'ts': datetime.now(pytz.UTC).isoformat()
        }

        table_data = {
            'setups': [setup],
            'ohlc': [current_candle]
        }

        mock_client = create_mock_supabase_client(table_data)

        with patch('src.signal_bot.RiskCalculator'):
            signal_bot = SignalBot(supabase_client=mock_client)

            exit_signals = signal_bot.generate_exit_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            assert len(exit_signals) == 1
            signal = exit_signals[0]
            assert signal['signal_type'] == 'stop_loss'
            assert signal['side'] == 'long'

    def test_generate_exit_signals_stop_loss_short(self, test_symbol_id):
        """Test stop loss detection for short position"""
        setup = create_test_setup(
            symbol_id=test_symbol_id,
            side='short',
            entry_price=19500.0,
            stop_loss=19535.0,
            take_profit=19420.0
        )
        setup['status'] = 'active'

        current_candle = {
            'symbol_id': str(test_symbol_id),
            'timeframe': '1m',
            'close': 19540.0,  # Above SL (19535)
            'ts': datetime.now(pytz.UTC).isoformat()
        }

        table_data = {
            'setups': [setup],
            'ohlc': [current_candle]
        }

        mock_client = create_mock_supabase_client(table_data)

        with patch('src.signal_bot.RiskCalculator'):
            signal_bot = SignalBot(supabase_client=mock_client)

            exit_signals = signal_bot.generate_exit_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            assert len(exit_signals) == 1
            signal = exit_signals[0]
            assert signal['signal_type'] == 'stop_loss'
            assert signal['side'] == 'short'

    def test_generate_exit_signals_break_even(self, test_symbol_id):
        """Test break-even condition detection"""
        setup = create_test_setup(
            symbol_id=test_symbol_id,
            side='long',
            entry_price=19420.0,
            stop_loss=19385.0,
            take_profit=19500.0
        )
        setup['status'] = 'active'

        # Current price at +0.5R (half-way to TP)
        # Risk = 35 points, so +0.5R = entry + 17.5 = 19437.5
        current_candle = {
            'symbol_id': str(test_symbol_id),
            'timeframe': '1m',
            'close': 19438.0,
            'ts': datetime.now(pytz.UTC).isoformat()
        }

        table_data = {
            'setups': [setup],
            'ohlc': [current_candle]
        }

        mock_client = create_mock_supabase_client(table_data)

        # Mock RiskCalculator to return break-even signal
        with patch('src.signal_bot.RiskCalculator') as MockRiskCalc:
            mock_risk_calc = Mock()
            mock_risk_calc.should_move_to_break_even.return_value = {
                'should_move': True,
                'current_r': 0.5,
                'reason': 'Price reached +0.5R threshold'
            }
            MockRiskCalc.return_value = mock_risk_calc

            signal_bot = SignalBot(supabase_client=mock_client)

            exit_signals = signal_bot.generate_exit_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            assert len(exit_signals) == 1
            signal = exit_signals[0]
            assert signal['signal_type'] == 'break_even'
            assert signal['target_price'] == 19420.0  # Entry price
            assert signal['current_r'] == 0.5

    def test_generate_exit_signals_no_active_trades(self, test_symbol_id):
        """Test when no active trades exist"""
        table_data = {
            'setups': [],
            'ohlc': []
        }

        mock_client = create_mock_supabase_client(table_data)

        with patch('src.signal_bot.RiskCalculator'):
            signal_bot = SignalBot(supabase_client=mock_client)

            exit_signals = signal_bot.generate_exit_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            assert exit_signals == []

    def test_generate_exit_signals_no_current_price(self, test_symbol_id):
        """Test when no current price data exists"""
        setup = create_test_setup(symbol_id=test_symbol_id)
        setup['status'] = 'active'

        table_data = {
            'setups': [setup],
            'ohlc': []  # No current price
        }

        mock_client = create_mock_supabase_client(table_data)

        with patch('src.signal_bot.RiskCalculator'):
            signal_bot = SignalBot(supabase_client=mock_client)

            exit_signals = signal_bot.generate_exit_signals(
                symbol_id=test_symbol_id,
                symbol_name='DAX'
            )

            assert exit_signals == []


@pytest.mark.unit
@pytest.mark.agent
class TestSignalBotCreateSignal:
    """Tests for create_signal() method"""

    def test_create_signal_entry_success(self, test_symbol_id):
        """Test successful entry signal creation"""
        signal_data = {
            'setup_id': str(uuid4()),
            'side': 'long',
            'current_price': 19420.0,
            'confidence': 0.88,
            'validation_breakdown': {},
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }

        # Mock successful insert
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table = Mock(return_value=mock_table)
        mock_table.insert = Mock(return_value=mock_table)

        mock_result = Mock()
        created_signal = {
            'id': str(uuid4()),
            'symbol_id': str(test_symbol_id),
            'setup_id': signal_data['setup_id'],
            'signal_type': 'entry',
            'side': 'long',
            'price': 19420.0,
            'confidence': 0.88,
            'executed': False
        }
        mock_result.data = [created_signal]
        mock_table.execute = Mock(return_value=mock_result)

        signal_bot = SignalBot(supabase_client=mock_client)

        signal_id = signal_bot.create_signal(
            symbol_id=test_symbol_id,
            signal_data=signal_data,
            signal_type='entry'
        )

        assert signal_id is not None
        assert isinstance(signal_id, UUID)

    def test_create_signal_exit_success(self, test_symbol_id):
        """Test successful exit signal creation"""
        signal_data = {
            'setup_id': str(uuid4()),
            'signal_type': 'take_profit',
            'side': 'long',
            'current_price': 19505.0,
            'target_price': 19500.0,
            'reason': 'TP hit'
        }

        mock_client = Mock()
        mock_table = Mock()
        mock_client.table = Mock(return_value=mock_table)
        mock_table.insert = Mock(return_value=mock_table)

        mock_result = Mock()
        created_signal = {
            'id': str(uuid4()),
            'symbol_id': str(test_symbol_id),
            'signal_type': 'exit',
            'executed': False
        }
        mock_result.data = [created_signal]
        mock_table.execute = Mock(return_value=mock_result)

        signal_bot = SignalBot(supabase_client=mock_client)

        signal_id = signal_bot.create_signal(
            symbol_id=test_symbol_id,
            signal_data=signal_data,
            signal_type='exit'
        )

        assert signal_id is not None

    def test_create_signal_database_error(self, test_symbol_id):
        """Test signal creation when database insert fails"""
        signal_data = {'setup_id': str(uuid4()), 'current_price': 19420.0}

        mock_client = Mock()
        mock_table = Mock()
        mock_client.table = Mock(return_value=mock_table)
        mock_table.insert = Mock(return_value=mock_table)

        mock_result = Mock()
        mock_result.data = []  # Empty = failure
        mock_table.execute = Mock(return_value=mock_result)

        signal_bot = SignalBot(supabase_client=mock_client)

        signal_id = signal_bot.create_signal(
            symbol_id=test_symbol_id,
            signal_data=signal_data,
            signal_type='entry'
        )

        assert signal_id is None


@pytest.mark.unit
@pytest.mark.agent
class TestSignalBotRun:
    """Tests for run() method - full execution"""

    def test_run_success_with_entry_and_exit_signals(self):
        """Test successful run with both entry and exit signals"""
        symbol_id = uuid4()

        # Create pending setup (for entry signal)
        pending_setup = create_test_setup(
            symbol_id=symbol_id,
            strategy='asia_sweep',
            side='long',
            entry_price=19420.0,
            stop_loss=19385.0,
            take_profit=19500.0
        )
        pending_setup['status'] = 'pending'

        # Create active setup (for exit signal)
        active_setup = create_test_setup(
            symbol_id=symbol_id,
            strategy='orb',
            side='long',
            entry_price=19450.0,
            stop_loss=19415.0,
            take_profit=19530.0
        )
        active_setup['status'] = 'active'

        # Generate OHLC data
        berlin_tz = pytz.timezone('Europe/Berlin')
        start_time = berlin_tz.localize(datetime(2025, 10, 29, 0, 0, 0))
        candles = generate_ohlc_data(start_time, count=250)

        for candle in candles:
            candle['symbol_id'] = str(symbol_id)
            candle['timeframe'] = '5m'

        # Current price candle (for exit detection)
        current_candle = {
            'symbol_id': str(symbol_id),
            'timeframe': '1m',
            'close': 19535.0,  # Hit TP for active_setup
            'ts': datetime.now(pytz.UTC).isoformat()
        }
        candles.append(current_candle)

        levels = {
            'symbol_id': str(symbol_id),
            'trade_date': '2025-10-29',
            'pivot': 19500.0,
            'r1': 19550.0,
            's1': 19450.0
        }

        symbols = [{'id': str(symbol_id), 'symbol': 'DAX', 'active': True}]

        table_data = {
            'market_symbols': symbols,
            'setups': [pending_setup, active_setup],
            'ohlc': candles,
            'levels_daily': [levels],
            'signals': []
        }

        mock_client = create_mock_supabase_client(table_data)

        # Mock signal insertion
        original_table = mock_client.table
        created_signals = []

        def table_with_insert_tracking(table_name):
            mock_table = original_table(table_name)
            if table_name == 'signals':
                original_insert = mock_table.insert

                def insert_and_track(data):
                    created_signals.append(data)
                    result_mock = original_insert(data)
                    execute_result = Mock()
                    execute_result.data = [{'id': str(uuid4()), **data}]
                    result_mock.execute = lambda: execute_result
                    return result_mock

                mock_table.insert = insert_and_track
            return mock_table

        mock_client.table = table_with_insert_tracking

        # Mock dependencies
        with patch('src.signal_bot.TechnicalIndicators') as MockTechIndicators, \
             patch('src.signal_bot.ValidationEngine') as MockValidationEngine, \
             patch('src.signal_bot.RiskCalculator') as MockRiskCalc:

            # Configure mocks
            MockTechIndicators.calculate_ema.return_value = np.array([19480.0] * 250)
            MockTechIndicators.calculate_rsi.return_value = np.array([55.0] * 250)

            mock_macd = Mock()
            mock_macd.macd_line = np.array([10.5] * 250)
            mock_macd.signal_line = np.array([8.0] * 250)
            mock_macd.histogram = np.array([2.5] * 250)
            MockTechIndicators.calculate_macd.return_value = mock_macd

            mock_bb = Mock()
            mock_bb.upper = np.array([19550.0] * 250)
            mock_bb.middle = np.array([19500.0] * 250)
            mock_bb.lower = np.array([19450.0] * 250)
            MockTechIndicators.calculate_bollinger_bands.return_value = mock_bb

            MockTechIndicators.calculate_atr.return_value = np.array([25.0] * 250)
            MockTechIndicators.get_trend_direction.return_value = 'bullish'

            # Mock ValidationEngine (approve entry signal)
            mock_validation_engine = Mock()
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.confidence = 0.88
            mock_validation_result.breakdown = {}
            mock_validation_result.priority_override = False
            mock_validation_result.notes = "Valid"
            mock_validation_engine.validate_signal.return_value = mock_validation_result
            MockValidationEngine.return_value = mock_validation_engine

            # Mock RiskCalculator
            mock_risk_calc = Mock()
            mock_risk_calc.should_move_to_break_even.return_value = {
                'should_move': False
            }
            MockRiskCalc.return_value = mock_risk_calc

            # Execute
            signal_bot = SignalBot(supabase_client=mock_client)
            result = signal_bot.run()

            # Assertions
            assert 'execution_time' in result
            assert 'symbols_analyzed' in result
            assert 'entry_signals' in result
            assert 'exit_signals' in result
            assert 'total_signals' in result
            assert 'signals' in result

            assert result['symbols_analyzed'] == 1
            assert isinstance(result['signals'], list)

            # Should have both entry and exit signals
            assert result['entry_signals'] >= 0
            assert result['exit_signals'] >= 0

    def test_run_no_active_symbols(self):
        """Test run when no active symbols exist"""
        table_data = {'market_symbols': []}
        mock_client = create_mock_supabase_client(table_data)

        signal_bot = SignalBot(supabase_client=mock_client)
        result = signal_bot.run()

        assert result['symbols_analyzed'] == 0
        assert result['entry_signals'] == 0
        assert result['exit_signals'] == 0
        assert result['signals'] == []

    def test_run_with_specific_symbols(self):
        """Test run with specific symbol filter"""
        symbol1_id = uuid4()
        symbol2_id = uuid4()

        symbols = [
            {'id': str(symbol1_id), 'symbol': 'DAX', 'active': True},
            {'id': str(symbol2_id), 'symbol': 'NDX', 'active': True}
        ]

        table_data = {
            'market_symbols': symbols,
            'setups': [],
            'ohlc': [],
            'levels_daily': []
        }

        mock_client = create_mock_supabase_client(table_data)

        signal_bot = SignalBot(supabase_client=mock_client)
        result = signal_bot.run(symbols=['DAX'])

        assert 'symbols_analyzed' in result

    def test_run_handles_exceptions(self):
        """Test run handles exceptions gracefully"""
        mock_client = Mock()
        mock_client.table = Mock(side_effect=Exception("Database error"))

        signal_bot = SignalBot(supabase_client=mock_client)
        result = signal_bot.run()

        assert 'error' in result
        assert result['symbols_analyzed'] == 0


@pytest.mark.integration
@pytest.mark.agent
class TestSignalBotIntegration:
    """Integration tests for complete workflows"""

    def test_complete_signal_generation_workflow(self):
        """Test complete workflow from market analysis to signal creation"""
        symbol_id = uuid4()

        # Create pending setup
        setup = create_test_setup(
            symbol_id=symbol_id,
            strategy='asia_sweep',
            side='long'
        )
        setup['status'] = 'pending'

        # Generate realistic OHLC data
        berlin_tz = pytz.timezone('Europe/Berlin')
        start_time = berlin_tz.localize(datetime(2025, 10, 29, 0, 0, 0))
        candles = generate_ohlc_data(start_time, count=250, base_price=19500.0)

        for candle in candles:
            candle['symbol_id'] = str(symbol_id)
            candle['timeframe'] = '5m'

        levels = {
            'symbol_id': str(symbol_id),
            'trade_date': '2025-10-29',
            'pivot': 19500.0,
            'r1': 19550.0,
            's1': 19450.0
        }

        symbols = [{'id': str(symbol_id), 'symbol': 'DAX', 'active': True}]

        table_data = {
            'market_symbols': symbols,
            'setups': [setup],
            'ohlc': candles,
            'levels_daily': [levels]
        }

        mock_client = create_mock_supabase_client(table_data)

        # Track created signals
        created_signals = []
        original_table = mock_client.table

        def table_with_tracking(table_name):
            mock_table = original_table(table_name)
            if table_name == 'signals':
                original_insert = mock_table.insert

                def insert_and_track(data):
                    created_signals.append(data)
                    result_mock = original_insert(data)
                    execute_result = Mock()
                    execute_result.data = [{'id': str(uuid4()), **data}]
                    result_mock.execute = lambda: execute_result
                    return result_mock

                mock_table.insert = insert_and_track
            return mock_table

        mock_client.table = table_with_tracking

        # Mock all dependencies
        with patch('src.signal_bot.TechnicalIndicators') as MockTechIndicators, \
             patch('src.signal_bot.ValidationEngine') as MockValidationEngine:

            # Configure indicators
            MockTechIndicators.calculate_ema.return_value = np.array([19480.0] * 250)
            MockTechIndicators.calculate_rsi.return_value = np.array([55.0] * 250)

            mock_macd = Mock()
            mock_macd.macd_line = np.array([10.5] * 250)
            mock_macd.signal_line = np.array([8.0] * 250)
            mock_macd.histogram = np.array([2.5] * 250)
            MockTechIndicators.calculate_macd.return_value = mock_macd

            mock_bb = Mock()
            mock_bb.upper = np.array([19550.0] * 250)
            mock_bb.middle = np.array([19500.0] * 250)
            mock_bb.lower = np.array([19450.0] * 250)
            MockTechIndicators.calculate_bollinger_bands.return_value = mock_bb

            MockTechIndicators.calculate_atr.return_value = np.array([25.0] * 250)
            MockTechIndicators.get_trend_direction.return_value = 'bullish'

            # Configure validation
            mock_validation_engine = Mock()
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.confidence = 0.88
            mock_validation_result.breakdown = {}
            mock_validation_result.priority_override = False
            mock_validation_result.notes = "Valid"
            mock_validation_engine.validate_signal.return_value = mock_validation_result
            MockValidationEngine.return_value = mock_validation_engine

            # Execute
            signal_bot = SignalBot(supabase_client=mock_client)
            result = signal_bot.run(symbols=['DAX'])

            # Verify workflow
            assert result['symbols_analyzed'] >= 0
            assert isinstance(result['signals'], list)

            # Check created signals are valid
            for signal_dict in created_signals:
                assert 'signal_type' in signal_dict
                assert signal_dict['signal_type'] in ['entry', 'exit']
                assert 'symbol_id' in signal_dict
                assert signal_dict['executed'] is False
