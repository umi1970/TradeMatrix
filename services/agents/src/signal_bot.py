"""
TradeMatrix.ai - SignalBot Agent
Evaluates market structure and generates entry/exit signals for trading setups.

Execution: Every 60 seconds (via Celery scheduler)
Responsibilities:
  1. Analyze market structure using technical indicators
  2. Generate entry signals validated through ValidationEngine
  3. Generate exit signals (TP/SL/breakeven conditions)
  4. Create signal records in database

Data sources:
  - ohlc table (historical price data for indicators)
  - setups table (active trading setups)
  - levels_daily table (pivot levels for confluence)

Output: Signals in 'signals' table
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from uuid import UUID
import numpy as np

from supabase import Client

# Setup logger
logger = logging.getLogger(__name__)


class SignalBot:
    """
    SignalBot Agent - Analyzes market structure and generates trading signals

    Responsibilities:
    - Calculate technical indicators (EMA, RSI, MACD, BB, ATR)
    - Determine trend direction and market structure
    - Generate entry signals with ValidationEngine
    - Generate exit signals (TP hit, SL hit, breakeven conditions)
    - Write signals to database for execution/alerts
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize SignalBot agent

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
        """
        self.supabase = supabase_client
        logger.info("SignalBot initialized")


    def analyze_market_structure(
        self,
        symbol_id: UUID,
        symbol_name: str,
        timeframe: str = '5m'
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate technical indicators and determine market structure

        Process:
        1. Fetch recent OHLC data (200+ candles for indicators)
        2. Calculate EMAs (20, 50, 200)
        3. Calculate RSI (14)
        4. Calculate MACD (12, 26, 9)
        5. Calculate Bollinger Bands (20, 2)
        6. Calculate ATR (14) for volatility
        7. Determine trend direction
        8. Fetch current pivot levels for confluence

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)
            timeframe: Timeframe for analysis (default: '5m')

        Returns:
            Dict with market structure analysis:
            {
                'price': float,
                'emas': {'20': float, '50': float, '200': float},
                'rsi': float,
                'macd': {'line': float, 'signal': float, 'histogram': float},
                'bb': {'upper': float, 'middle': float, 'lower': float},
                'atr': float,
                'volume': float,
                'avg_volume': float,
                'candle': {'open': float, 'high': float, 'low': float, 'close': float},
                'context': {'trend': str, 'volatility': float},
                'levels': {'pivot': float, 'r1': float, 's1': float, ...},
                'timestamp': str
            }
        """
        logger.info(f"Analyzing market structure for {symbol_name} on {timeframe}")

        try:
            # Import technical indicators here to avoid circular import
            from core.technical_indicators import TechnicalIndicators

            # Step 1 - Fetch recent OHLC data (need 200+ candles for EMA-200)
            result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', timeframe)\
                .order('ts', desc=True)\
                .limit(250)\
                .execute()

            candles = result.data if result.data else []

            if not candles or len(candles) < 200:
                logger.warning(f"Insufficient OHLC data for {symbol_name} (need 200+, got {len(candles)})")
                return None

            # Reverse to chronological order (oldest first)
            candles = list(reversed(candles))

            # Extract OHLC arrays
            highs = [float(c['high']) for c in candles]
            lows = [float(c['low']) for c in candles]
            closes = [float(c['close']) for c in candles]
            opens = [float(c['open']) for c in candles]
            volumes = [float(c.get('volume', 0)) for c in candles]

            # Step 2 - Calculate EMAs
            ema_20 = TechnicalIndicators.calculate_ema(closes, 20)
            ema_50 = TechnicalIndicators.calculate_ema(closes, 50)
            ema_200 = TechnicalIndicators.calculate_ema(closes, 200)

            # Step 3 - Calculate RSI
            rsi = TechnicalIndicators.calculate_rsi(closes, 14)

            # Step 4 - Calculate MACD
            macd = TechnicalIndicators.calculate_macd(closes, 12, 26, 9)

            # Step 5 - Calculate Bollinger Bands
            bb = TechnicalIndicators.calculate_bollinger_bands(closes, 20, 2.0)

            # Step 6 - Calculate ATR for volatility
            atr = TechnicalIndicators.calculate_atr(highs, lows, closes, 14)

            # Step 7 - Get current values (last candle)
            current_price = closes[-1]
            current_ema_20 = float(ema_20[-1]) if not np.isnan(ema_20[-1]) else 0.0
            current_ema_50 = float(ema_50[-1]) if not np.isnan(ema_50[-1]) else 0.0
            current_ema_200 = float(ema_200[-1]) if not np.isnan(ema_200[-1]) else 0.0
            current_rsi = float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0
            current_macd_line = float(macd.macd_line[-1]) if not np.isnan(macd.macd_line[-1]) else 0.0
            current_macd_signal = float(macd.signal_line[-1]) if not np.isnan(macd.signal_line[-1]) else 0.0
            current_macd_histogram = float(macd.histogram[-1]) if not np.isnan(macd.histogram[-1]) else 0.0
            current_bb_upper = float(bb.upper[-1]) if not np.isnan(bb.upper[-1]) else 0.0
            current_bb_middle = float(bb.middle[-1]) if not np.isnan(bb.middle[-1]) else 0.0
            current_bb_lower = float(bb.lower[-1]) if not np.isnan(bb.lower[-1]) else 0.0
            current_atr = float(atr[-1]) if not np.isnan(atr[-1]) else 0.0
            current_volume = volumes[-1]
            avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else current_volume

            # Step 8 - Determine trend direction
            trend = TechnicalIndicators.get_trend_direction(
                current_price,
                current_ema_20,
                current_ema_50,
                current_ema_200
            )

            # Step 9 - Calculate volatility (ATR / Price)
            volatility = (current_atr / current_price) if current_price > 0 else 0.0

            # Step 10 - Fetch pivot levels for confluence
            now = datetime.now(timezone.utc)
            trade_date_str = now.date().isoformat()

            levels_result = self.supabase.table('levels_daily')\
                .select('pivot, r1, r2, s1, s2')\
                .eq('symbol_id', str(symbol_id))\
                .eq('trade_date', trade_date_str)\
                .limit(1)\
                .execute()

            levels_data = levels_result.data[0] if levels_result.data else {}
            pivot_levels = {
                'pivot': float(levels_data.get('pivot', 0)),
                'r1': float(levels_data.get('r1', 0)),
                'r2': float(levels_data.get('r2', 0)),
                's1': float(levels_data.get('s1', 0)),
                's2': float(levels_data.get('s2', 0))
            }

            # Step 11 - Build market structure analysis
            latest_candle = candles[-1]

            market_structure = {
                'price': current_price,
                'emas': {
                    '20': current_ema_20,
                    '50': current_ema_50,
                    '200': current_ema_200
                },
                'rsi': current_rsi,
                'macd': {
                    'line': current_macd_line,
                    'signal': current_macd_signal,
                    'histogram': current_macd_histogram
                },
                'bb': {
                    'upper': current_bb_upper,
                    'middle': current_bb_middle,
                    'lower': current_bb_lower
                },
                'atr': current_atr,
                'volume': current_volume,
                'avg_volume': avg_volume,
                'candle': {
                    'open': opens[-1],
                    'high': highs[-1],
                    'low': lows[-1],
                    'close': closes[-1]
                },
                'context': {
                    'trend': trend,
                    'volatility': volatility
                },
                'levels': pivot_levels,
                'timestamp': latest_candle.get('ts'),
                'symbol_id': str(symbol_id),
                'symbol_name': symbol_name
            }

            logger.info(f"Market structure analyzed for {symbol_name}: trend={trend}, price={current_price:.2f}")
            return market_structure

        except ImportError as e:
            logger.error(f"Failed to import TechnicalIndicators: {e}")
            return None
        except Exception as e:
            logger.error(f"Error analyzing market structure for {symbol_name}: {e}", exc_info=True)
            return None


    def generate_entry_signals(
        self,
        symbol_id: UUID,
        symbol_name: str
    ) -> List[Dict[str, Any]]:
        """
        Generate entry signals for active setups

        Process:
        1. Fetch active setups (status='pending')
        2. Analyze market structure
        3. Build signal data for ValidationEngine
        4. Validate signal using ValidationEngine
        5. If valid (confidence >= 0.8), generate entry signal
        6. Return list of entry signals

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)

        Returns:
            List of entry signal dicts:
            [{
                'setup_id': UUID,
                'strategy': str,
                'side': 'long' | 'short',
                'entry_price': float,
                'confidence': float,
                'validation_result': ValidationResult
            }]
        """
        logger.info(f"Generating entry signals for {symbol_name}")

        entry_signals = []

        try:
            # Import validation engine
            from core.validation_engine import ValidationEngine

            # Step 1 - Fetch active setups for this symbol
            result = self.supabase.table('setups')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('status', 'pending')\
                .order('created_at', desc=True)\
                .execute()

            active_setups = result.data if result.data else []

            if not active_setups:
                logger.debug(f"No active setups for {symbol_name}")
                return entry_signals

            logger.info(f"Found {len(active_setups)} active setups for {symbol_name}")

            # Step 2 - Analyze market structure once (reuse for all setups)
            market_structure = self.analyze_market_structure(
                symbol_id=symbol_id,
                symbol_name=symbol_name,
                timeframe='5m'
            )

            if not market_structure:
                logger.warning(f"Could not analyze market structure for {symbol_name}")
                return entry_signals

            # Step 3 - Validate each setup
            validation_engine = ValidationEngine()

            for setup in active_setups:
                setup_id = setup['id']
                strategy = setup['strategy']
                side = setup['side']
                entry_price = float(setup['entry_price'])
                confidence_score = float(setup.get('confidence', 0.0))

                logger.info(f"Validating setup {setup_id} ({strategy}, {side})")

                # Build signal data for validation
                signal_data = {
                    'price': market_structure['price'],
                    'emas': market_structure['emas'],
                    'levels': market_structure['levels'],
                    'volume': market_structure['volume'],
                    'avg_volume': market_structure['avg_volume'],
                    'candle': market_structure['candle'],
                    'context': market_structure['context'],
                    'strategy': strategy  # e.g., 'asia_sweep', 'y_low_rebound', 'orb'
                }

                # Step 4 - Validate using ValidationEngine
                validation_result = validation_engine.validate_signal(signal_data)

                # Step 5 - Check if signal is valid
                if validation_result.is_valid:
                    logger.info(
                        f"Valid entry signal for {symbol_name}: "
                        f"setup={setup_id}, confidence={validation_result.confidence:.2f}"
                    )

                    entry_signals.append({
                        'setup_id': setup_id,
                        'strategy': strategy,
                        'side': side,
                        'entry_price': entry_price,
                        'current_price': market_structure['price'],
                        'confidence': validation_result.confidence,
                        'validation_breakdown': validation_result.breakdown,
                        'priority_override': validation_result.priority_override,
                        'notes': validation_result.notes,
                        'timestamp': market_structure['timestamp']
                    })
                else:
                    logger.debug(
                        f"Signal validation failed for setup {setup_id}: {validation_result.notes}"
                    )

            return entry_signals

        except ImportError as e:
            logger.error(f"Failed to import ValidationEngine: {e}")
            return entry_signals
        except Exception as e:
            logger.error(f"Error generating entry signals for {symbol_name}: {e}", exc_info=True)
            return entry_signals


    def generate_exit_signals(
        self,
        symbol_id: UUID,
        symbol_name: str
    ) -> List[Dict[str, Any]]:
        """
        Generate exit signals for active trades

        Checks:
        1. Take Profit hit (price >= TP for long, price <= TP for short)
        2. Stop Loss hit (price <= SL for long, price >= SL for short)
        3. Break-even condition (price +0.5R, move SL to entry)

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)

        Returns:
            List of exit signal dicts:
            [{
                'setup_id': UUID,
                'signal_type': 'take_profit' | 'stop_loss' | 'break_even',
                'current_price': float,
                'target_price': float,
                'reason': str
            }]
        """
        logger.info(f"Generating exit signals for {symbol_name}")

        exit_signals = []

        try:
            # Import risk calculator for break-even checks
            from core.risk_calculator import RiskCalculator

            # Step 1 - Fetch active trades (setups with status='active')
            result = self.supabase.table('setups')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('status', 'active')\
                .execute()

            active_trades = result.data if result.data else []

            if not active_trades:
                logger.debug(f"No active trades for {symbol_name}")
                return exit_signals

            logger.info(f"Found {len(active_trades)} active trades for {symbol_name}")

            # Step 2 - Fetch current price
            latest_candle_result = self.supabase.table('ohlc')\
                .select('close')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '1m')\
                .order('ts', desc=True)\
                .limit(1)\
                .execute()

            if not latest_candle_result.data:
                logger.warning(f"No current price data for {symbol_name}")
                return exit_signals

            current_price = float(latest_candle_result.data[0]['close'])

            # Step 3 - Check each active trade for exit conditions
            for trade in active_trades:
                setup_id = trade['id']
                side = trade['side']
                entry_price = float(trade['entry_price'])
                stop_loss = float(trade['stop_loss'])
                take_profit = float(trade['take_profit'])

                logger.debug(
                    f"Checking exit conditions for {setup_id}: "
                    f"current={current_price:.2f}, entry={entry_price:.2f}, "
                    f"sl={stop_loss:.2f}, tp={take_profit:.2f}"
                )

                # Check 1 - Take Profit hit
                if side == 'long' and current_price >= take_profit:
                    exit_signals.append({
                        'setup_id': setup_id,
                        'signal_type': 'take_profit',
                        'current_price': current_price,
                        'target_price': take_profit,
                        'side': side,
                        'reason': f'Price {current_price:.2f} reached TP {take_profit:.2f}'
                    })
                    logger.info(f"Take Profit hit for {symbol_name}: {setup_id}")

                elif side == 'short' and current_price <= take_profit:
                    exit_signals.append({
                        'setup_id': setup_id,
                        'signal_type': 'take_profit',
                        'current_price': current_price,
                        'target_price': take_profit,
                        'side': side,
                        'reason': f'Price {current_price:.2f} reached TP {take_profit:.2f}'
                    })
                    logger.info(f"Take Profit hit for {symbol_name}: {setup_id}")

                # Check 2 - Stop Loss hit
                elif side == 'long' and current_price <= stop_loss:
                    exit_signals.append({
                        'setup_id': setup_id,
                        'signal_type': 'stop_loss',
                        'current_price': current_price,
                        'target_price': stop_loss,
                        'side': side,
                        'reason': f'Price {current_price:.2f} hit SL {stop_loss:.2f}'
                    })
                    logger.info(f"Stop Loss hit for {symbol_name}: {setup_id}")

                elif side == 'short' and current_price >= stop_loss:
                    exit_signals.append({
                        'setup_id': setup_id,
                        'signal_type': 'stop_loss',
                        'current_price': current_price,
                        'target_price': stop_loss,
                        'side': side,
                        'reason': f'Price {current_price:.2f} hit SL {stop_loss:.2f}'
                    })
                    logger.info(f"Stop Loss hit for {symbol_name}: {setup_id}")

                # Check 3 - Break-even condition (price at +0.5R)
                else:
                    # Use RiskCalculator to check break-even
                    risk_calc = RiskCalculator(account_balance=10000)  # Dummy balance for calculation
                    be_check = risk_calc.should_move_to_break_even(
                        entry=entry_price,
                        current_price=current_price,
                        stop_loss=stop_loss,
                        threshold_r=0.5
                    )

                    if be_check['should_move']:
                        exit_signals.append({
                            'setup_id': setup_id,
                            'signal_type': 'break_even',
                            'current_price': current_price,
                            'target_price': entry_price,  # New SL = entry
                            'side': side,
                            'current_r': be_check['current_r'],
                            'reason': be_check['reason']
                        })
                        logger.info(f"Break-even condition met for {symbol_name}: {setup_id}")

            return exit_signals

        except ImportError as e:
            logger.error(f"Failed to import RiskCalculator: {e}")
            return exit_signals
        except Exception as e:
            logger.error(f"Error generating exit signals for {symbol_name}: {e}", exc_info=True)
            return exit_signals


    def create_signal(
        self,
        symbol_id: UUID,
        signal_data: Dict[str, Any],
        signal_type: str
    ) -> Optional[UUID]:
        """
        Write signal to 'signals' table

        Args:
            symbol_id: UUID of the market symbol
            signal_data: Signal details dict (from generate_entry_signals or generate_exit_signals)
            signal_type: 'entry' or 'exit'

        Returns:
            UUID of created signal record, or None if failed
        """
        logger.info(f"Creating {signal_type} signal for symbol {symbol_id}")

        try:
            # Build signal record
            signal_record = {
                'symbol_id': str(symbol_id),
                'setup_id': str(signal_data.get('setup_id')) if signal_data.get('setup_id') else None,
                'signal_type': signal_type,
                'side': signal_data.get('side'),
                'price': float(signal_data.get('current_price', 0)),
                'confidence': float(signal_data.get('confidence', 0)) if signal_type == 'entry' else None,
                'metadata': signal_data,  # Store full signal data as JSON
                'executed': False
            }

            # Insert into signals table
            result = self.supabase.table('signals')\
                .insert(signal_record)\
                .execute()

            if result.data and len(result.data) > 0:
                signal_id = result.data[0]['id']
                logger.info(f"Signal created with ID: {signal_id}")
                return UUID(signal_id)
            else:
                logger.error(f"No data returned when creating signal for {symbol_id}")
                return None

        except Exception as e:
            logger.error(f"Error creating signal for symbol {symbol_id}: {e}", exc_info=True)
            return None


    def run(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Main execution method - Called by Celery scheduler every 60 seconds

        Process:
        1. Fetch active symbols from market_symbols table
        2. For each symbol:
           a. Generate entry signals (validate pending setups)
           b. Generate exit signals (check active trades)
           c. Create signal records in database
        3. Return summary of generated signals

        Args:
            symbols: Optional list of symbol names to analyze (default: all active symbols)

        Returns:
            Dict with execution summary:
            {
                'execution_time': datetime,
                'symbols_analyzed': int,
                'entry_signals': int,
                'exit_signals': int,
                'signals': List[Dict]
            }
        """
        execution_start = datetime.now(timezone.utc)
        logger.info(f"SignalBot execution started at {execution_start}")

        try:
            # Step 1 - Fetch active symbols
            query = self.supabase.table('market_symbols')\
                .select('id, symbol')\
                .eq('active', True)

            # If specific symbols requested, filter by name
            if symbols and len(symbols) > 0:
                query = query.in_('symbol', symbols)

            result = query.execute()
            active_symbols = result.data if result.data else []

        except Exception as e:
            logger.error(f"Error fetching active symbols: {e}")
            return {
                'execution_time': execution_start.isoformat(),
                'symbols_analyzed': 0,
                'entry_signals': 0,
                'exit_signals': 0,
                'signals': [],
                'error': str(e)
            }

        if not active_symbols:
            logger.warning("No active symbols found")
            return {
                'execution_time': execution_start.isoformat(),
                'symbols_analyzed': 0,
                'entry_signals': 0,
                'exit_signals': 0,
                'signals': []
            }

        logger.info(f"Processing {len(active_symbols)} active symbols")

        # Step 2 - Analyze each symbol and generate signals
        generated_signals = []
        entry_count = 0
        exit_count = 0

        for symbol in active_symbols:
            symbol_id = UUID(symbol['id'])
            symbol_name = symbol['symbol']

            logger.info(f"Processing signals for symbol: {symbol_name}")

            try:
                # Generate entry signals
                entry_signals = self.generate_entry_signals(
                    symbol_id=symbol_id,
                    symbol_name=symbol_name
                )

                for entry_signal in entry_signals:
                    signal_id = self.create_signal(
                        symbol_id=symbol_id,
                        signal_data=entry_signal,
                        signal_type='entry'
                    )
                    if signal_id:
                        generated_signals.append({
                            'symbol': symbol_name,
                            'signal_type': 'entry',
                            'signal_id': str(signal_id),
                            'setup_id': str(entry_signal['setup_id']),
                            'confidence': entry_signal['confidence'],
                            'details': entry_signal
                        })
                        entry_count += 1

                # Generate exit signals
                exit_signals = self.generate_exit_signals(
                    symbol_id=symbol_id,
                    symbol_name=symbol_name
                )

                for exit_signal in exit_signals:
                    signal_id = self.create_signal(
                        symbol_id=symbol_id,
                        signal_data=exit_signal,
                        signal_type='exit'
                    )
                    if signal_id:
                        generated_signals.append({
                            'symbol': symbol_name,
                            'signal_type': 'exit',
                            'signal_id': str(signal_id),
                            'setup_id': str(exit_signal['setup_id']),
                            'exit_type': exit_signal['signal_type'],
                            'details': exit_signal
                        })
                        exit_count += 1

            except Exception as e:
                logger.error(f"Error processing signals for {symbol_name}: {e}", exc_info=True)
                continue

        # Step 3 - Calculate execution duration
        execution_end = datetime.now(timezone.utc)
        duration_ms = int((execution_end - execution_start).total_seconds() * 1000)

        summary = {
            'execution_time': execution_start.isoformat(),
            'execution_duration_ms': duration_ms,
            'symbols_analyzed': len(active_symbols),
            'entry_signals': entry_count,
            'exit_signals': exit_count,
            'total_signals': len(generated_signals),
            'signals': generated_signals
        }

        logger.info(f"SignalBot execution completed: {summary}")
        return summary


# Example usage (for testing)
if __name__ == "__main__":
    # This would be called from Celery task
    import sys
    import numpy as np  # Add numpy import for testing
    sys.path.insert(0, '/mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/api/src')

    from config.supabase import get_supabase_admin

    # Initialize agent with admin client (bypasses RLS)
    signal_bot = SignalBot(supabase_client=get_supabase_admin())

    # Run analysis
    result = signal_bot.run()

    print("SignalBot Results:")
    print(result)
