"""
US Open Planner Agent
=====================
Monitors US market open (15:30-15:45 MEZ) for Opening Range Breakout (ORB) setups

Strategy: ORB (Opening Range Breakout)
- Monitor first 15 minutes of US market open (15:30-15:45 MEZ)
- Identify High/Low range
- Detect breakout: 5m close > High → Long Bias, 5m close < Low → Short Bias
- Entry: Retest preferred
- SL: Opposite range edge
- TP: 2R or Daily H/L

Markets: DOW (DJI), NASDAQ (NDX)
Execution: Celery task scheduled at 15:25 MEZ daily
"""

from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import Dict, Optional, Tuple, List
from uuid import UUID

from supabase import Client
from config.supabase import get_supabase_admin, settings


class USOpenPlanner:
    """
    US Open Planner Agent

    Responsibilities:
    1. Monitor US market opening range (15:30-15:45 MEZ)
    2. Detect range breakouts (5m close > high or < low)
    3. Generate setup entries with confidence scores
    4. Calculate SL/TP levels
    5. Store setups in database
    """

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize US Open Planner

        Args:
            supabase_client: Optional Supabase client (defaults to admin client)
        """
        self.supabase = supabase_client or get_supabase_admin()
        self.symbols = ['DJI', 'NDX']  # Dow Jones, NASDAQ
        self.orb_start = time(15, 30)  # 15:30 MEZ
        self.orb_end = time(15, 45)    # 15:45 MEZ
        self.orb_duration_minutes = 15

    async def run(self, trade_date: Optional[datetime] = None) -> Dict:
        """
        Main execution method - called by Celery scheduler

        Workflow:
        1. Detect ORB range (15:30-15:45)
        2. Analyze breakout conditions
        3. Generate setups for valid breakouts
        4. Store in database
        5. Log execution

        Args:
            trade_date: Optional date to analyze (defaults to today)

        Returns:
            Dict with execution summary:
            {
                'status': 'success' | 'failed',
                'setups_created': int,
                'details': {...}
            }
        """
        if trade_date is None:
            trade_date = datetime.now()

        try:
            # TODO: Log execution start to agent_logs table
            agent_log_id = await self._log_execution_start()

            setups_created = []

            for symbol in self.symbols:
                # Step 1: Detect ORB range
                orb_range = await self.detect_orb_range(symbol, trade_date)

                if orb_range is None:
                    # TODO: Log warning - insufficient data
                    continue

                # Step 2: Analyze breakout
                breakout = await self.analyze_breakout(symbol, trade_date, orb_range)

                if breakout is None:
                    # TODO: Log info - no breakout detected
                    continue

                # Step 3: Generate setup
                setup = await self.generate_setup(
                    symbol=symbol,
                    orb_range=orb_range,
                    breakout=breakout,
                    trade_date=trade_date
                )

                if setup:
                    setups_created.append(setup)

            # TODO: Log execution completion
            await self._log_execution_complete(
                agent_log_id,
                setups_count=len(setups_created)
            )

            return {
                'status': 'success',
                'setups_created': len(setups_created),
                'details': {
                    'trade_date': trade_date.isoformat(),
                    'symbols_analyzed': self.symbols,
                    'setups': setups_created
                }
            }

        except Exception as e:
            # TODO: Log execution failure
            await self._log_execution_failed(agent_log_id, str(e))

            return {
                'status': 'failed',
                'error': str(e),
                'setups_created': 0
            }

    async def detect_orb_range(
        self,
        symbol: str,
        trade_date: datetime
    ) -> Optional[Dict]:
        """
        Detect Opening Range (first 15 minutes: 15:30-15:45 MEZ)

        Algorithm:
        1. Fetch 1m candles from 15:30-15:45
        2. Calculate range High/Low
        3. Validate sufficient data (minimum 12 candles)
        4. Return range data

        Args:
            symbol: Market symbol (e.g., 'DJI', 'NDX')
            trade_date: Date to analyze

        Returns:
            Dict with range data:
            {
                'high': Decimal,
                'low': Decimal,
                'range_size': Decimal,
                'start_time': datetime,
                'end_time': datetime,
                'candle_count': int,
                'opening_candle': Dict
            }
            or None if insufficient data
        """
        try:
            # 1. Get symbol_id from market_symbols table
            symbol_id = await self._get_symbol_id(symbol)

            # 2. Build time range for ORB period (15:30-15:45 MEZ)
            start_dt = datetime.combine(trade_date.date(), self.orb_start)
            end_dt = datetime.combine(trade_date.date(), self.orb_end)

            # 3. Query ohlc table for 1m candles
            response = self.supabase.table('ohlc')\
                .select('open, high, low, close, volume, ts')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '1m')\
                .gte('ts', start_dt.isoformat())\
                .lte('ts', end_dt.isoformat())\
                .order('ts', desc=False)\
                .execute()

            candles = response.data

            # 4. Validate minimum 12 candles exist (80% of expected 15)
            if not candles or len(candles) < 12:
                return None

            # 5. Calculate range from all candles
            orb_high = max(Decimal(str(c['high'])) for c in candles)
            orb_low = min(Decimal(str(c['low'])) for c in candles)
            orb_range_size = orb_high - orb_low

            # 6. Store opening candle (first 1m candle at 15:30)
            opening_candle = {
                'open': Decimal(str(candles[0]['open'])),
                'high': Decimal(str(candles[0]['high'])),
                'low': Decimal(str(candles[0]['low'])),
                'close': Decimal(str(candles[0]['close'])),
                'volume': candles[0]['volume'],
                'ts': candles[0]['ts']
            }

            return {
                'high': orb_high,
                'low': orb_low,
                'range_size': orb_range_size,
                'start_time': start_dt,
                'end_time': end_dt,
                'candle_count': len(candles),
                'opening_candle': opening_candle
            }

        except Exception as e:
            # Log error but don't crash - return None to signal failure
            print(f"Error detecting ORB range for {symbol}: {str(e)}")
            return None

    async def analyze_breakout(
        self,
        symbol: str,
        trade_date: datetime,
        orb_range: Dict
    ) -> Optional[Dict]:
        """
        Check for range breakout using 5m candles

        Breakout conditions:
        - LONG: 5m close > ORB High
        - SHORT: 5m close < ORB Low

        Args:
            symbol: Market symbol
            trade_date: Date to analyze
            orb_range: ORB range data from detect_orb_range()

        Returns:
            Dict with breakout data:
            {
                'direction': 'long' | 'short',
                'breakout_price': Decimal,
                'breakout_time': datetime,
                'candle_close': Decimal,
                'volume': int,
                'retest_available': bool,
                'retest_price': Optional[Decimal]
            }
            or None if no breakout
        """
        try:
            # 1. Get symbol_id
            symbol_id = await self._get_symbol_id(symbol)

            # 2. Define breakout detection window (15:45-16:00)
            breakout_start = orb_range['end_time']
            breakout_end = breakout_start + timedelta(minutes=15)

            # 3. Fetch 5m candles after ORB close
            response = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '5m')\
                .gte('ts', breakout_start.isoformat())\
                .lte('ts', breakout_end.isoformat())\
                .order('ts', desc=False)\
                .execute()

            candles = response.data

            if not candles:
                return None

            # 4. Check each candle for breakout
            orb_high = orb_range['high']
            orb_low = orb_range['low']

            for candle in candles:
                close = Decimal(str(candle['close']))
                high = Decimal(str(candle['high']))
                low = Decimal(str(candle['low']))
                volume = candle['volume']

                # Check for bullish breakout
                if close > orb_high:
                    # Check for retest: Did price come back to orb_high?
                    retest_available = low <= orb_high
                    retest_price = orb_high if retest_available else None

                    return {
                        'direction': 'long',
                        'breakout_price': close,
                        'breakout_time': candle['ts'],
                        'candle_close': close,
                        'volume': volume,
                        'retest_available': retest_available,
                        'retest_price': retest_price,
                        'breakout_strength': float((close - orb_high) / orb_range['range_size'])
                    }

                # Check for bearish breakout
                elif close < orb_low:
                    # Check for retest: Did price come back to orb_low?
                    retest_available = high >= orb_low
                    retest_price = orb_low if retest_available else None

                    return {
                        'direction': 'short',
                        'breakout_price': close,
                        'breakout_time': candle['ts'],
                        'candle_close': close,
                        'volume': volume,
                        'retest_available': retest_available,
                        'retest_price': retest_price,
                        'breakout_strength': float((orb_low - close) / orb_range['range_size'])
                    }

            # No breakout detected
            return None

        except Exception as e:
            print(f"Error analyzing breakout for {symbol}: {str(e)}")
            return None

    async def generate_setup(
        self,
        symbol: str,
        orb_range: Dict,
        breakout: Dict,
        trade_date: datetime
    ) -> Optional[Dict]:
        """
        Generate trading setup and store in database

        Setup calculation:
        - LONG: Entry = retest of ORB high, SL = ORB low, TP = 2R or Daily High
        - SHORT: Entry = retest of ORB low, SL = ORB high, TP = 2R or Daily Low

        Args:
            symbol: Market symbol
            orb_range: ORB range data
            breakout: Breakout data
            trade_date: Trade date

        Returns:
            Dict with created setup data or None if creation failed
        """
        try:
            # 1. Get symbol_id
            symbol_id = await self._get_symbol_id(symbol)

            # 2. Get daily levels (yesterday_high, yesterday_low) from eod_levels
            daily_levels = await self._get_daily_levels(symbol_id, trade_date)

            # 3. Calculate entry, SL, TP based on direction
            if breakout['direction'] == 'long':
                # LONG SETUP
                # Entry: Use retest price if available, else ORB high
                entry = breakout.get('retest_price', orb_range['high'])
                stop_loss = orb_range['low']
                risk = entry - stop_loss

                # TP: 2R or Yesterday High (whichever is closer)
                tp_2r = entry + (risk * Decimal('2.0'))
                if daily_levels and daily_levels.get('yesterday_high'):
                    tp_daily = Decimal(str(daily_levels['yesterday_high']))
                    take_profit = min(tp_2r, tp_daily)
                else:
                    take_profit = tp_2r

            else:  # short
                # SHORT SETUP
                # Entry: Use retest price if available, else ORB low
                entry = breakout.get('retest_price', orb_range['low'])
                stop_loss = orb_range['high']
                risk = stop_loss - entry

                # TP: 2R or Yesterday Low (whichever is closer)
                tp_2r = entry - (risk * Decimal('2.0'))
                if daily_levels and daily_levels.get('yesterday_low'):
                    tp_daily = Decimal(str(daily_levels['yesterday_low']))
                    take_profit = max(tp_2r, tp_daily)
                else:
                    take_profit = tp_2r

            # 4. Calculate confidence score
            confidence = await self._calculate_confidence(orb_range, breakout, daily_levels)

            # 5. Build setup payload
            setup_data = {
                'module': 'usopen',
                'symbol_id': str(symbol_id),
                'strategy': 'orb',
                'side': breakout['direction'],
                'entry_price': float(entry),
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'confidence': confidence,
                'status': 'pending',
                'payload': {
                    'symbol': symbol,
                    'trade_date': trade_date.date().isoformat(),
                    'orb_range': {
                        'high': float(orb_range['high']),
                        'low': float(orb_range['low']),
                        'range_size': float(orb_range['range_size']),
                        'candle_count': orb_range['candle_count']
                    },
                    'breakout': {
                        'price': float(breakout['breakout_price']),
                        'time': breakout['breakout_time'],
                        'strength': breakout.get('breakout_strength', 0.0),
                        'volume': breakout.get('volume', 0),
                        'retest_available': breakout.get('retest_available', False)
                    },
                    'risk_reward': 2.0,
                    'risk_amount': float(risk),
                    'daily_levels': daily_levels if daily_levels else None
                }
            }

            # 6. Insert setup into database
            response = self.supabase.table('setups')\
                .insert(setup_data)\
                .execute()

            if response.data:
                return response.data[0]
            else:
                return None

        except Exception as e:
            print(f"Error generating setup for {symbol}: {str(e)}")
            return None

    async def _get_symbol_id(self, symbol: str) -> UUID:
        """
        Get symbol UUID from market_symbols table

        Args:
            symbol: Symbol string (e.g., 'DJI', 'NDX')

        Returns:
            UUID of symbol

        Raises:
            ValueError: If symbol not found
        """
        response = self.supabase.table('market_symbols')\
            .select('id')\
            .eq('symbol', symbol)\
            .eq('active', True)\
            .limit(1)\
            .execute()

        if not response.data:
            raise ValueError(f"Symbol {symbol} not found in database or is inactive")

        return UUID(response.data[0]['id'])

    async def _get_daily_levels(
        self,
        symbol_id: UUID,
        trade_date: datetime
    ) -> Optional[Dict]:
        """
        Get daily levels (yesterday high/low, ATR) from eod_levels table

        Args:
            symbol_id: Symbol UUID
            trade_date: Date to get levels for

        Returns:
            Dict with daily levels or None if not found
        """
        response = self.supabase.table('eod_levels')\
            .select('*')\
            .eq('symbol_id', str(symbol_id))\
            .eq('trade_date', trade_date.date().isoformat())\
            .limit(1)\
            .execute()

        return response.data[0] if response.data else None

    async def _calculate_confidence(
        self,
        orb_range: Dict,
        breakout: Dict,
        daily_levels: Optional[Dict]
    ) -> float:
        """
        Calculate confidence score (0.0-1.0) for the setup

        Factors:
        - Range size (larger = higher confidence)
        - Breakout strength (distance from range)
        - Alignment with daily levels
        - Volume confirmation (if available)
        - Retest availability

        Args:
            orb_range: ORB range data
            breakout: Breakout data
            daily_levels: Daily levels data

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Start with base confidence
        confidence = 0.3

        # Factor 1: Range size (0-20 points)
        # Larger ranges indicate more significant moves
        # Normalize to 0-0.2 (assuming range size 0-500 points)
        range_size = float(orb_range['range_size'])
        range_factor = min(range_size / 500.0 * 0.2, 0.2)
        confidence += range_factor

        # Factor 2: Breakout strength (0-30 points)
        # Stronger breakouts = higher confidence
        breakout_strength = breakout.get('breakout_strength', 0.0)
        if breakout_strength > 0.5:  # Strong breakout (>50% of range)
            confidence += 0.3
        elif breakout_strength > 0.3:  # Moderate breakout (>30%)
            confidence += 0.2
        elif breakout_strength > 0.1:  # Weak breakout (>10%)
            confidence += 0.1

        # Factor 3: Retest availability (0-15 points)
        # Retests provide better entries
        if breakout.get('retest_available', False):
            confidence += 0.15

        # Factor 4: Volume confirmation (0-10 points)
        # Higher volume = more conviction
        volume = breakout.get('volume', 0)
        if volume > 0:
            # Placeholder: would need average volume for proper comparison
            confidence += 0.05

        # Factor 5: Daily level alignment (0-15 points)
        # Check if breakout aligns with yesterday's context
        if daily_levels:
            y_close = daily_levels.get('yesterday_close')
            if y_close:
                y_close_decimal = Decimal(str(y_close))
                breakout_price = breakout['breakout_price']

                # Check alignment: Long above yesterday close = bullish, Short below = bearish
                if breakout['direction'] == 'long' and breakout_price > y_close_decimal:
                    # Long above yesterday close = bullish alignment
                    confidence += 0.15
                elif breakout['direction'] == 'short' and breakout_price < y_close_decimal:
                    # Short below yesterday close = bearish alignment
                    confidence += 0.15

        # Ensure between 0.0 and 1.0
        return max(0.0, min(1.0, confidence))

    async def _log_execution_start(self) -> UUID:
        """
        Log agent execution start to agent_logs table

        Returns:
            UUID of created log entry
        """
        log_data = {
            'agent_type': 'us_open_planner',
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'input_data': {
                'symbols': self.symbols,
                'orb_start': self.orb_start.isoformat(),
                'orb_end': self.orb_end.isoformat(),
                'orb_duration_minutes': self.orb_duration_minutes
            }
        }

        response = self.supabase.table('agent_logs')\
            .insert(log_data)\
            .execute()

        return UUID(response.data[0]['id'])

    async def _log_execution_complete(
        self,
        log_id: UUID,
        setups_count: int
    ) -> None:
        """
        Log successful execution completion

        Args:
            log_id: Agent log entry UUID
            setups_count: Number of setups created
        """
        completed_at = datetime.now()
        started_at_response = self.supabase.table('agent_logs')\
            .select('started_at')\
            .eq('id', str(log_id))\
            .execute()

        # Calculate duration
        duration_ms = None
        if started_at_response.data:
            started_at = datetime.fromisoformat(started_at_response.data[0]['started_at'].replace('Z', '+00:00'))
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        self.supabase.table('agent_logs')\
            .update({
                'status': 'completed',
                'completed_at': completed_at.isoformat(),
                'duration_ms': duration_ms,
                'output_data': {
                    'setups_created': setups_count,
                    'symbols_analyzed': self.symbols
                }
            })\
            .eq('id', str(log_id))\
            .execute()

    async def _log_execution_failed(
        self,
        log_id: UUID,
        error_message: str
    ) -> None:
        """
        Log failed execution

        Args:
            log_id: Agent log entry UUID
            error_message: Error description
        """
        completed_at = datetime.now()
        started_at_response = self.supabase.table('agent_logs')\
            .select('started_at')\
            .eq('id', str(log_id))\
            .execute()

        # Calculate duration
        duration_ms = None
        if started_at_response.data:
            started_at = datetime.fromisoformat(started_at_response.data[0]['started_at'].replace('Z', '+00:00'))
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        self.supabase.table('agent_logs')\
            .update({
                'status': 'failed',
                'completed_at': completed_at.isoformat(),
                'duration_ms': duration_ms,
                'error_message': error_message
            })\
            .eq('id', str(log_id))\
            .execute()


# Example Celery task integration (to be implemented in tasks.py)
"""
from celery import Celery
from us_open_planner import USOpenPlanner

app = Celery('tradematrix')

@app.task
def run_us_open_planner():
    '''
    Celery task to run US Open Planner
    Scheduled daily at 15:25 MEZ
    '''
    planner = USOpenPlanner()
    result = await planner.run()
    return result

# Celery Beat schedule configuration:
app.conf.beat_schedule = {
    'us-open-planner': {
        'task': 'tasks.run_us_open_planner',
        'schedule': crontab(hour=15, minute=25),  # 15:25 MEZ daily
    }
}
"""
