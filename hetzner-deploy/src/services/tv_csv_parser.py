"""
TradingView CSV Parser Service

Parses TradingView CSV exports with Pine Script indicators
and returns structured data compatible with Vision API format.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TVCSVParser:
    """Parse TradingView CSV exports"""

    # Expected columns (25 total: 5 OHLC + 20 indicators)
    REQUIRED_COLUMNS = ['time', 'open', 'high', 'low', 'close']
    INDICATOR_COLUMNS = [
        'EMA_20', 'EMA_50', 'EMA_200',
        'RSI_14', 'ATR_14',
        'MACD_Line', 'MACD_Signal', 'MACD_Histogram',
        'BB_Upper', 'BB_Middle', 'BB_Lower',
        'Pivot_Point', 'Resistance_1', 'Support_1', 'Resistance_2', 'Support_2',
        'ADX_14', 'DI_Plus', 'DI_Minus',
        'Volume'
    ]

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.symbol: Optional[str] = None
        self.timeframe: Optional[str] = None

    def parse_csv(self, file_path: str, symbol: str = None, timeframe: str = None) -> Dict[str, Any]:
        """
        Parse TradingView CSV file

        Args:
            file_path: Path to CSV file
            symbol: Symbol name (optional, extracted from filename if not provided)
            timeframe: Timeframe (optional, extracted from filename if not provided)

        Returns:
            Dict with structured analysis data (compatible with Vision API format)
        """
        logger.info(f"📂 Parsing CSV: {file_path}")

        # Read CSV
        try:
            self.df = pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"❌ Failed to read CSV: {e}")
            raise ValueError(f"Invalid CSV file: {e}")

        # Validate columns
        self._validate_columns()

        # Extract metadata
        self.symbol = symbol or self._extract_symbol_from_filename(file_path)
        self.timeframe = timeframe or self._extract_timeframe_from_filename(file_path)

        # Get latest bar
        latest = self.df.iloc[-1]

        # Analyze trend
        trend, trend_strength = self._analyze_trend(latest)

        # Analyze price vs EMAs
        price_vs_emas = self._analyze_price_vs_emas(latest)

        # Analyze momentum
        momentum_bias = self._analyze_momentum(latest)

        # Calculate setup
        setup_type, entry_price, stop_loss, take_profit, risk_reward = self._calculate_setup(latest, trend)

        # Generate reasoning
        reasoning = self._generate_reasoning(latest, trend, setup_type)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(latest, trend, trend_strength)

        # Convert full DataFrame to OHLCV array for charting
        ohlcv_data = []
        for _, row in self.df.iterrows():
            ohlcv_data.append({
                'time': str(row['time']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row.get('Volume', 0)) if 'Volume' in row else None,
            })

        # Build response (compatible with Vision API format)
        response = {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'current_price': float(latest['close']),
            'timestamp': str(latest['time']),

            # OHLC (latest bar)
            'open': float(latest['open']),
            'high': float(latest['high']),
            'low': float(latest['low']),
            'close': float(latest['close']),

            # Full OHLCV data for charting
            'ohlcv_data': ohlcv_data,
            'total_bars': len(self.df),

            # EMAs
            'ema20': float(latest['EMA_20']),
            'ema50': float(latest['EMA_50']),
            'ema200': float(latest['EMA_200']),

            # Momentum
            'rsi': float(latest['RSI_14']),

            # Volatility
            'atr': float(latest['ATR_14']),

            # MACD
            'macd_line': float(latest['MACD_Line']),
            'macd_signal': float(latest['MACD_Signal']),
            'macd_histogram': float(latest['MACD_Histogram']),

            # Bollinger Bands
            'bb_upper': float(latest['BB_Upper']),
            'bb_middle': float(latest['BB_Middle']),
            'bb_lower': float(latest['BB_Lower']),

            # Pivot Points (Support/Resistance)
            'pivot_point': float(latest['Pivot_Point']),
            'resistance_1': float(latest['Resistance_1']),
            'support_1': float(latest['Support_1']),
            'resistance_2': float(latest['Resistance_2']),
            'support_2': float(latest['Support_2']),

            # Trend Strength
            'adx': float(latest['ADX_14']),
            'di_plus': float(latest['DI_Plus']),
            'di_minus': float(latest['DI_Minus']),

            # Volume
            'volume': int(latest['Volume']) if pd.notna(latest['Volume']) else 0,

            # Analysis
            'trend': trend,
            'trend_strength': trend_strength,
            'price_vs_emas': price_vs_emas,
            'momentum_bias': momentum_bias,
            'confidence_score': confidence_score,
            'chart_quality': 'excellent',  # CSV data is always high quality

            # Setup
            'setup_type': setup_type,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward,
            'reasoning': reasoning,
            'timeframe_validity': self._determine_timeframe_validity(),

            # Metadata
            'data_source': 'tradingview_csv',
            'total_bars': len(self.df),
        }

        logger.info(f"✅ Parsed {self.symbol} {self.timeframe}: {trend} trend, confidence {confidence_score:.2f}")

        return response

    def _validate_columns(self):
        """Validate CSV has required columns"""
        missing_required = [col for col in self.REQUIRED_COLUMNS if col not in self.df.columns]

        if missing_required:
            raise ValueError(f"Missing required columns: {missing_required}")

        missing_indicators = [col for col in self.INDICATOR_COLUMNS if col not in self.df.columns]

        if missing_indicators:
            logger.warning(f"⚠️  Missing indicator columns: {missing_indicators}")

        logger.info(f"✅ CSV validation passed: {len(self.df)} rows, {len(self.df.columns)} columns")

    def _extract_symbol_from_filename(self, file_path: str) -> str:
        """Extract symbol from CSV filename (e.g., 'CAPITALCOM_US30, 15.csv' -> 'US30')"""
        import os
        filename = os.path.basename(file_path)

        # Remove .csv extension
        name = filename.replace('.csv', '')

        # Split by comma or underscore
        parts = name.replace('_', ',').split(',')

        # Last part before timeframe is usually symbol
        if len(parts) >= 2:
            return parts[-2].strip()

        return 'UNKNOWN'

    def _extract_timeframe_from_filename(self, file_path: str) -> str:
        """Extract timeframe from CSV filename (e.g., 'CAPITALCOM_US30, 15.csv' -> '15m')"""
        import os
        filename = os.path.basename(file_path)

        # Remove .csv extension
        name = filename.replace('.csv', '')

        # Split by comma
        parts = name.split(',')

        # Last part is usually timeframe
        if len(parts) >= 2:
            tf = parts[-1].strip()
            # Add 'm' suffix if not present
            if tf.isdigit():
                return f"{tf}m"
            return tf

        return '15m'  # Default

    def _analyze_trend(self, bar: pd.Series) -> tuple[str, str]:
        """
        Analyze trend based on EMA alignment and ADX

        Returns:
            (trend, trend_strength)
            trend: 'bullish' | 'bearish' | 'sideways'
            trend_strength: 'strong' | 'moderate' | 'weak'
        """
        ema20 = bar['EMA_20']
        ema50 = bar['EMA_50']
        ema200 = bar['EMA_200']
        close = bar['close']
        adx = bar['ADX_14']

        # EMA alignment
        if close > ema20 > ema50 > ema200:
            trend = 'bullish'
        elif close < ema20 < ema50 < ema200:
            trend = 'bearish'
        else:
            trend = 'sideways'

        # Trend strength based on ADX
        if adx > 40:
            trend_strength = 'strong'
        elif adx > 25:
            trend_strength = 'moderate'
        else:
            trend_strength = 'weak'

        return trend, trend_strength

    def _analyze_price_vs_emas(self, bar: pd.Series) -> str:
        """
        Analyze price position relative to EMAs

        Returns:
            'above_all' | 'below_all' | 'between_20_50' | 'between_50_200' | 'mixed'
        """
        close = bar['close']
        ema20 = bar['EMA_20']
        ema50 = bar['EMA_50']
        ema200 = bar['EMA_200']

        if close > ema20 and close > ema50 and close > ema200:
            return 'above_all'
        elif close < ema20 and close < ema50 and close < ema200:
            return 'below_all'
        elif close > ema20 and close < ema50:
            return 'between_20_50'
        elif close > ema50 and close < ema200:
            return 'between_50_200'
        else:
            return 'mixed'

    def _analyze_momentum(self, bar: pd.Series) -> str:
        """Analyze momentum bias based on RSI and MACD"""
        rsi = bar['RSI_14']
        macd_hist = bar['MACD_Histogram']

        if rsi > 70:
            return 'Overbought - potential reversal'
        elif rsi < 30:
            return 'Oversold - potential bounce'
        elif rsi > 50 and macd_hist > 0:
            return 'Bullish momentum building'
        elif rsi < 50 and macd_hist < 0:
            return 'Bearish momentum building'
        else:
            return 'Neutral momentum'

    def _calculate_setup(self, bar: pd.Series, trend: str) -> tuple[str, float, float, float, float]:
        """
        Calculate setup: entry, stop loss, take profit

        Returns:
            (setup_type, entry_price, stop_loss, take_profit, risk_reward)
        """
        close = bar['close']
        atr = bar['ATR_14']
        support1 = bar['Support_1']
        resistance1 = bar['Resistance_1']
        rsi = bar['RSI_14']

        # Determine setup type
        if trend == 'bullish' and rsi < 70:
            setup_type = 'long'
            entry_price = float(close)
            stop_loss = float(support1) if support1 < close else float(close - atr * 1.5)
            take_profit = float(resistance1) if resistance1 > close else float(close + atr * 3.0)
        elif trend == 'bearish' and rsi > 30:
            setup_type = 'short'
            entry_price = float(close)
            stop_loss = float(resistance1) if resistance1 > close else float(close + atr * 1.5)
            take_profit = float(support1) if support1 < close else float(close - atr * 3.0)
        else:
            setup_type = 'no_trade'
            entry_price = float(close)
            stop_loss = None
            take_profit = None

        # Calculate risk/reward
        if setup_type != 'no_trade' and stop_loss and take_profit:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            risk_reward = round(reward / risk, 2) if risk > 0 else 0.0
        else:
            risk_reward = 0.0

        return setup_type, entry_price, stop_loss, take_profit, risk_reward

    def _generate_reasoning(self, bar: pd.Series, trend: str, setup_type: str) -> str:
        """Generate human-readable reasoning for the setup"""
        ema_alignment = "EMAs aligned" if trend != 'sideways' else "No clear EMA alignment"
        adx_level = bar['ADX_14']
        adx_desc = "strong trend" if adx_level > 25 else "weak trend"
        rsi_level = bar['RSI_14']

        if setup_type == 'long':
            return f"{trend.capitalize()} trend with {adx_desc} (ADX {adx_level:.0f}). {ema_alignment}. RSI at {rsi_level:.0f} shows room for upside."
        elif setup_type == 'short':
            return f"{trend.capitalize()} trend with {adx_desc} (ADX {adx_level:.0f}). {ema_alignment}. RSI at {rsi_level:.0f} shows room for downside."
        else:
            return f"No clear setup. Market is {trend} with {adx_desc}. RSI at {rsi_level:.0f} suggests neutral momentum."

    def _calculate_confidence(self, bar: pd.Series, trend: str, trend_strength: str) -> float:
        """
        Calculate confidence score (0.0 - 1.0)

        Factors:
        - Trend alignment (30%)
        - Trend strength (20%)
        - RSI position (20%)
        - Risk/Reward (20%)
        - Volume (10%)
        """
        confidence = 0.0

        # Trend alignment (30%)
        if trend in ['bullish', 'bearish']:
            confidence += 0.3

        # Trend strength (20%)
        if trend_strength == 'strong':
            confidence += 0.2
        elif trend_strength == 'moderate':
            confidence += 0.1

        # RSI position (20%)
        rsi = bar['RSI_14']
        if 40 < rsi < 60:
            confidence += 0.2  # Neutral zone = good
        elif 30 < rsi < 70:
            confidence += 0.1  # Not extreme

        # MACD alignment (10%)
        macd_hist = bar['MACD_Histogram']
        if (trend == 'bullish' and macd_hist > 0) or (trend == 'bearish' and macd_hist < 0):
            confidence += 0.1

        # Volume check (10%)
        # (Note: Volume can be 0 for some symbols, so we don't penalize)
        if bar['Volume'] > 0:
            confidence += 0.1

        # ADX confirmation (10%)
        if bar['ADX_14'] > 25:
            confidence += 0.1

        return round(min(confidence, 1.0), 2)

    def _determine_timeframe_validity(self) -> str:
        """Determine setup validity timeframe"""
        if not self.timeframe:
            return 'intraday'

        tf = self.timeframe.lower()

        if any(x in tf for x in ['1m', '5m', '15m', '30m']):
            return 'intraday'
        elif any(x in tf for x in ['1h', '2h', '4h']):
            return 'swing'
        else:
            return 'midterm'


def parse_tradingview_csv(file_path: str, symbol: str = None, timeframe: str = None) -> Dict[str, Any]:
    """
    Convenience function to parse TradingView CSV

    Args:
        file_path: Path to CSV file
        symbol: Symbol name (optional)
        timeframe: Timeframe (optional)

    Returns:
        Structured analysis data
    """
    parser = TVCSVParser()
    return parser.parse_csv(file_path, symbol, timeframe)
