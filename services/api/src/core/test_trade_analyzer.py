"""
Unit Tests for TradeAnalyzer

Tests the integration of all Phase 2 modules:
- MarketDataFetcher
- TechnicalIndicators
- ValidationEngine
- RiskCalculator

Author: TradeMatrix.ai
Date: 2025-10-29
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from trade_analyzer import (
    TradeAnalyzer,
    TradeAnalyzerError,
    InsufficientDataError,
    create_analyzer
)


class TestTradeAnalyzerInitialization:
    """Test TradeAnalyzer initialization"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        analyzer = TradeAnalyzer()

        assert analyzer.account_balance == 10000.0
        assert analyzer.risk_per_trade == 0.01
        assert analyzer.data_fetcher is not None
        assert analyzer.validator is not None
        assert analyzer.risk_calculator is not None

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        analyzer = TradeAnalyzer(
            account_balance=5000.0,
            risk_per_trade=0.02
        )

        assert analyzer.risk_calculator.account_balance == 5000.0
        assert analyzer.risk_calculator.risk_per_trade == 0.02

    def test_init_invalid_account_balance(self):
        """Test initialization with invalid account balance"""
        with pytest.raises(ValueError):
            TradeAnalyzer(account_balance=-100.0)

        with pytest.raises(ValueError):
            TradeAnalyzer(account_balance=0.0)

    def test_init_invalid_risk_per_trade(self):
        """Test initialization with invalid risk percentage"""
        with pytest.raises(ValueError):
            TradeAnalyzer(risk_per_trade=0.0)

        with pytest.raises(ValueError):
            TradeAnalyzer(risk_per_trade=0.15)  # > 10%


class TestFetchAndCalculateIndicators:
    """Test fetch_and_calculate_indicators method"""

    @patch('trade_analyzer.MarketDataFetcher.fetch_time_series')
    def test_fetch_and_calculate_success(self, mock_fetch):
        """Test successful data fetching and indicator calculation"""
        # Mock candle data (300 candles)
        mock_candles = []
        for i in range(300):
            mock_candles.append({
                'datetime': f'2025-10-{(i % 28) + 1:02d} {i % 24:02d}:00:00',
                'open': '19000.0',
                'high': '19100.0',
                'low': '18900.0',
                'close': '19050.0',
                'volume': '10000'
            })

        mock_fetch.return_value = mock_candles

        analyzer = TradeAnalyzer()
        result = analyzer.fetch_and_calculate_indicators("DAX", "1h", 300)

        # Verify structure
        assert result['symbol'] == "DAX"
        assert result['interval'] == "1h"
        assert result['candle_count'] == 300
        assert 'indicators' in result
        assert 'current_price' in result
        assert result['current_price'] > 0

        # Verify indicators
        indicators = result['indicators']
        assert 'ema' in indicators
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'bollinger_bands' in indicators
        assert 'atr' in indicators

    @patch('trade_analyzer.MarketDataFetcher.fetch_time_series')
    def test_fetch_insufficient_data(self, mock_fetch):
        """Test error handling for insufficient data"""
        # Only 50 candles (need 200+)
        mock_candles = [
            {
                'datetime': '2025-10-29 10:00:00',
                'open': '19000.0',
                'high': '19100.0',
                'low': '18900.0',
                'close': '19050.0',
                'volume': '10000'
            }
        ] * 50

        mock_fetch.return_value = mock_candles

        analyzer = TradeAnalyzer()

        with pytest.raises(InsufficientDataError):
            analyzer.fetch_and_calculate_indicators("DAX", "1h", 50)

    @patch('trade_analyzer.MarketDataFetcher.fetch_time_series')
    def test_fetch_empty_data(self, mock_fetch):
        """Test error handling for empty data"""
        mock_fetch.return_value = []

        analyzer = TradeAnalyzer()

        with pytest.raises(InsufficientDataError):
            analyzer.fetch_and_calculate_indicators("DAX", "1h", 300)


class TestValidateTradeSetup:
    """Test validate_trade_setup method"""

    def test_validate_trade_setup_success(self):
        """Test successful trade setup validation"""
        analyzer = TradeAnalyzer()

        # Mock indicators
        indicators = {
            'ema': {
                '20': np.array([19050.0]),
                '50': np.array([19000.0]),
                '200': np.array([18900.0])
            },
            'pivot_points': {
                'pp': 19000.0,
                'r1': 19100.0,
                's1': 18900.0
            },
            'trend': 'bullish',
            'volume': [10000] * 20
        }

        result = analyzer.validate_trade_setup(
            symbol="DAX",
            strategy_id="MR-02",
            indicators=indicators,
            current_price=19050.0,
            current_candle={
                'open': 19000.0,
                'high': 19100.0,
                'low': 18950.0,
                'close': 19050.0
            }
        )

        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.breakdown is not None
        assert 'ema_alignment' in result.breakdown

    def test_validate_with_high_confidence(self):
        """Test validation with perfect conditions (high confidence)"""
        analyzer = TradeAnalyzer()

        # Perfect bullish alignment
        indicators = {
            'ema': {
                '20': np.array([19050.0]),
                '50': np.array([19000.0]),
                '200': np.array([18900.0])
            },
            'pivot_points': {
                'pp': 19050.0,  # At current price
                'r1': 19150.0,
                's1': 18950.0
            },
            'trend': 'bullish',
            'volume': [20000] * 20  # High volume
        }

        result = analyzer.validate_trade_setup(
            symbol="DAX",
            strategy_id="MR-02",
            indicators=indicators,
            current_price=19050.0,
            current_candle={
                'open': 19000.0,
                'high': 19100.0,
                'low': 18995.0,
                'close': 19095.0  # Strong bullish candle
            }
        )

        assert result.confidence > 0.7  # Should have good confidence


class TestCalculateTradeParams:
    """Test calculate_trade_params method"""

    def test_calculate_trade_params_long(self):
        """Test trade parameter calculation for long position"""
        analyzer = TradeAnalyzer(account_balance=10000.0, risk_per_trade=0.01)

        result = analyzer.calculate_trade_params(
            entry_price=19500.0,
            stop_loss=19450.0,
            position_type='long',
            risk_reward_ratio=2.0,
            product_type='CFD'
        )

        # Verify structure
        assert result['entry'] == 19500.0
        assert result['stop_loss'] == 19450.0
        assert result['direction'] == 'long'
        assert result['risk_reward_ratio'] == 2.0
        assert result['is_valid'] is not None

        # Verify calculations
        assert result['position_size'] > 0
        assert result['risk_amount'] <= 100.0  # 1% of 10000
        assert result['take_profit'] > result['entry']

    def test_calculate_trade_params_short(self):
        """Test trade parameter calculation for short position"""
        analyzer = TradeAnalyzer(account_balance=10000.0, risk_per_trade=0.01)

        result = analyzer.calculate_trade_params(
            entry_price=19500.0,
            stop_loss=19550.0,
            position_type='short',
            risk_reward_ratio=2.0,
            product_type='CFD'
        )

        # Verify structure
        assert result['entry'] == 19500.0
        assert result['stop_loss'] == 19550.0
        assert result['direction'] == 'short'

        # Verify calculations
        assert result['take_profit'] < result['entry']  # TP below entry for short

    def test_calculate_trade_params_ko_product(self):
        """Test trade parameter calculation for KO product"""
        analyzer = TradeAnalyzer(account_balance=10000.0)

        result = analyzer.calculate_trade_params(
            entry_price=19500.0,
            stop_loss=19450.0,
            position_type='long',
            product_type='KO'
        )

        # Verify KO-specific data
        assert result['product_type'] == 'KO'
        assert result['ko_data'] is not None
        assert 'ko_threshold' in result['ko_data']
        assert 'leverage' in result['ko_data']


class TestGetCompleteAnalysis:
    """Test get_complete_analysis method (main integration)"""

    @patch('trade_analyzer.MarketDataFetcher.fetch_time_series')
    def test_complete_analysis_without_trade_plan(self, mock_fetch):
        """Test complete analysis without risk calculation"""
        # Mock candle data
        mock_candles = []
        for i in range(300):
            mock_candles.append({
                'datetime': f'2025-10-{(i % 28) + 1:02d} {i % 24:02d}:00:00',
                'open': '19000.0',
                'high': '19100.0',
                'low': '18900.0',
                'close': '19050.0',
                'volume': '10000'
            })

        mock_fetch.return_value = mock_candles

        analyzer = TradeAnalyzer()
        result = analyzer.get_complete_analysis(
            symbol="DAX",
            strategy_id="MR-02"
        )

        # Verify structure
        assert result['symbol'] == "DAX"
        assert result['strategy'] == "MR-02"
        assert 'market_data' in result
        assert 'indicators' in result
        assert 'signal' in result
        assert result['trade_plan'] is None  # No entry/SL provided
        assert 'summary' in result

        # Verify market data
        assert result['market_data']['current_price'] > 0
        assert result['market_data']['interval'] == "1h"

        # Verify signal
        assert 'confidence' in result['signal']
        assert 'is_valid' in result['signal']

    @patch('trade_analyzer.MarketDataFetcher.fetch_time_series')
    def test_complete_analysis_with_trade_plan(self, mock_fetch):
        """Test complete analysis with risk calculation"""
        # Mock candle data
        mock_candles = []
        for i in range(300):
            mock_candles.append({
                'datetime': f'2025-10-{(i % 28) + 1:02d} {i % 24:02d}:00:00',
                'open': '19000.0',
                'high': '19100.0',
                'low': '18900.0',
                'close': '19050.0',
                'volume': '10000'
            })

        mock_fetch.return_value = mock_candles

        analyzer = TradeAnalyzer(account_balance=10000.0)
        result = analyzer.get_complete_analysis(
            symbol="DAX",
            strategy_id="MR-02",
            entry_price=19500.0,
            stop_loss=19450.0,
            position_type='long',
            risk_reward_ratio=2.0
        )

        # Verify trade plan is included
        assert result['trade_plan'] is not None
        assert result['trade_plan']['entry'] == 19500.0
        assert result['trade_plan']['stop_loss'] == 19450.0
        assert result['trade_plan']['position_size'] > 0

        # Verify summary includes trade plan details
        assert 'entry' in result['summary']
        assert 'stop_loss' in result['summary']
        assert 'take_profit' in result['summary']

    @patch('trade_analyzer.MarketDataFetcher.fetch_time_series')
    def test_complete_analysis_summary(self, mock_fetch):
        """Test that summary is generated correctly"""
        # Mock candle data
        mock_candles = []
        for i in range(300):
            mock_candles.append({
                'datetime': f'2025-10-{(i % 28) + 1:02d} {i % 24:02d}:00:00',
                'open': '19000.0',
                'high': '19100.0',
                'low': '18900.0',
                'close': '19050.0',
                'volume': '10000'
            })

        mock_fetch.return_value = mock_candles

        analyzer = TradeAnalyzer()
        result = analyzer.get_complete_analysis(
            symbol="NASDAQ",
            strategy_id="MR-01"
        )

        summary = result['summary']

        # Verify summary fields
        assert summary['symbol'] == "NASDAQ"
        assert summary['strategy'] == "MR-01"
        assert 'current_price' in summary
        assert 'trend' in summary
        assert 'signal_valid' in summary
        assert 'confidence' in summary
        assert 'recommendation' in summary
        assert summary['recommendation'] in ['TRADE', 'WAIT']


class TestAnalyzeSymbol:
    """Test analyze_symbol convenience method"""

    @patch('trade_analyzer.MarketDataFetcher.fetch_time_series')
    def test_analyze_symbol(self, mock_fetch):
        """Test quick analysis method"""
        # Mock candle data
        mock_candles = []
        for i in range(300):
            mock_candles.append({
                'datetime': f'2025-10-{(i % 28) + 1:02d} {i % 24:02d}:00:00',
                'open': '19000.0',
                'high': '19100.0',
                'low': '18900.0',
                'close': '19050.0',
                'volume': '10000'
            })

        mock_fetch.return_value = mock_candles

        analyzer = TradeAnalyzer()
        result = analyzer.analyze_symbol("DAX", "MR-02")

        # Should return same as get_complete_analysis without trade plan
        assert result['symbol'] == "DAX"
        assert result['strategy'] == "MR-02"
        assert result['trade_plan'] is None


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_create_analyzer_defaults(self):
        """Test create_analyzer with default parameters"""
        analyzer = create_analyzer()

        assert isinstance(analyzer, TradeAnalyzer)
        assert analyzer.risk_calculator.account_balance == 10000.0
        assert analyzer.risk_calculator.risk_per_trade == 0.01

    def test_create_analyzer_custom(self):
        """Test create_analyzer with custom parameters"""
        analyzer = create_analyzer(
            account_balance=5000.0,
            risk_per_trade=0.02
        )

        assert analyzer.risk_calculator.account_balance == 5000.0
        assert analyzer.risk_calculator.risk_per_trade == 0.02


class TestErrorHandling:
    """Test error handling and edge cases"""

    @patch('trade_analyzer.MarketDataFetcher.fetch_time_series')
    def test_api_error_handling(self, mock_fetch):
        """Test handling of API errors"""
        mock_fetch.side_effect = Exception("API Error")

        analyzer = TradeAnalyzer()

        with pytest.raises(TradeAnalyzerError):
            analyzer.fetch_and_calculate_indicators("INVALID", "1h", 300)

    def test_invalid_trade_params(self):
        """Test error handling for invalid trade parameters"""
        analyzer = TradeAnalyzer()

        with pytest.raises(ValueError):
            analyzer.calculate_trade_params(
                entry_price=0.0,  # Invalid
                stop_loss=19450.0,
                position_type='long'
            )

        with pytest.raises(ValueError):
            analyzer.calculate_trade_params(
                entry_price=19500.0,
                stop_loss=19500.0,  # Same as entry
                position_type='long'
            )


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
