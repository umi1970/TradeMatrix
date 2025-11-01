"""
TradeMatrix.ai - Alert Engine Agent
Monitors market data in real-time and generates alerts for trading events.

Execution: Every 60 seconds (via Celery scheduler)
Alert Types:
  1. range_break - ORB 5m Close above/below 15m Range
  2. retest_touch - Price returns to Range edge
  3. asia_sweep_confirmed - EU Open above y_low after Asia sweep
  4. pivot_touch - Price touches Pivot Point
  5. r1_touch - Price touches R1
  6. s1_touch - Price touches S1

Data sources:
  - ohlc table (latest 1m/5m candles)
  - levels_daily table (pivot, r1, s1)
  - setups table (active ORB setups)

Output: Alerts in 'alerts' table
Realtime: Frontend subscribes via Supabase Realtime
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from uuid import UUID

from supabase import Client

# Setup logger
logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Alert Engine Agent - Monitors market data and generates real-time alerts

    Responsibilities:
    - Detect ORB range breaks (5m close above/below 15m range)
    - Detect retest touches (price returns to range edge)
    - Detect Asia sweep confirmations (EU open above y_low)
    - Detect pivot point touches (PP, R1, S1)
    - Write alerts to database for frontend consumption
    - Support Supabase Realtime subscriptions
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize Alert Engine agent

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
        """
        self.supabase = supabase_client
        logger.info("AlertEngine initialized")


    def check_range_break(
        self,
        symbol_id: UUID,
        symbol_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect ORB 5m Close above/below 15m Range

        Detection Logic:
        - Fetch active ORB setups from 'setups' table
        - Get latest 5m candle
        - Check if candle.close > setup.range_high (bullish break)
        - OR candle.close < setup.range_low (bearish break)

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)

        Returns:
            Dict with alert details if break detected, None otherwise
            Format: {
                'kind': 'range_break',
                'direction': 'bullish' | 'bearish',
                'price': Decimal,
                'range_high': Decimal,
                'range_low': Decimal,
                'timestamp': datetime
            }
        """
        logger.info(f"Checking range break for {symbol_name}")

        # Step 1 - Fetch active ORB setups for this symbol
        try:
            result = self.supabase.table('setups')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('strategy', 'orb')\
                .eq('status', 'active')\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()

            active_setup = result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching ORB setup for {symbol_name}: {e}")
            return None

        if not active_setup:
            logger.debug(f"No active ORB setup for {symbol_name}")
            return None

        # Step 2 - Extract range high/low from setup payload
        try:
            payload = active_setup.get('payload', {})
            range_high = Decimal(str(payload.get('range_high', 0)))
            range_low = Decimal(str(payload.get('range_low', 0)))

            if range_high == 0 or range_low == 0:
                logger.warning(f"Invalid range values for {symbol_name}")
                return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error extracting range from payload for {symbol_name}: {e}")
            return None

        # Step 3 - Fetch latest 5m candle
        try:
            result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '5m')\
                .order('ts', desc=True)\
                .limit(1)\
                .execute()

            latest_candle = result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching latest candle for {symbol_name}: {e}")
            return None

        if not latest_candle:
            logger.warning(f"No latest candle for {symbol_name}")
            return None

        close_price = Decimal(str(latest_candle.get('close', 0)))

        # Step 4 - Check for break
        is_bullish_break = close_price > range_high
        is_bearish_break = close_price < range_low

        if not (is_bullish_break or is_bearish_break):
            logger.debug(f"No range break detected for {symbol_name}")
            return None

        # Step 5 - Determine direction
        direction = 'bullish' if is_bullish_break else 'bearish'

        # Step 6 - Return alert details
        alert_data = {
            'kind': 'range_break',
            'direction': direction,
            'price': float(close_price),
            'range_high': float(range_high),
            'range_low': float(range_low),
            'candle_timestamp': latest_candle.get('ts') if latest_candle else None,
            'detection_time': datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Range break detected for {symbol_name}: {direction} at {close_price}")
        return alert_data


    def check_retest_touch(
        self,
        symbol_id: UUID,
        symbol_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect price return to Range edge (retest)

        Detection Logic:
        - After range break, price returns to range boundary
        - Bullish retest: Price broke above, now returns to range_high
        - Bearish retest: Price broke below, now returns to range_low
        - Tolerance: Within 0.1% of range edge

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)

        Returns:
            Dict with alert details if retest detected, None otherwise
        """
        logger.info(f"Checking retest touch for {symbol_name}")

        # Step 1 - Fetch active ORB setup that has already broken
        try:
            result = self.supabase.table('setups')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('strategy', 'orb')\
                .eq('status', 'active')\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()

            active_setup = result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching setup for {symbol_name}: {e}")
            return None

        if not active_setup:
            logger.debug(f"No active setup with break for {symbol_name}")
            return None

        # Step 2 - Get range boundaries and break direction
        try:
            payload = active_setup.get('payload', {})

            # Check if break has occurred
            if not payload.get('break_detected'):
                logger.debug(f"No break detected yet for {symbol_name}")
                return None

            range_high = Decimal(str(payload.get('range_high', 0)))
            range_low = Decimal(str(payload.get('range_low', 0)))
            break_direction = payload.get('break_direction')  # 'bullish' or 'bearish'

            if not break_direction or range_high == 0 or range_low == 0:
                logger.warning(f"Invalid break data for {symbol_name}")
                return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error extracting break data for {symbol_name}: {e}")
            return None

        # Step 3 - Fetch latest candle
        try:
            result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '1m')\
                .order('ts', desc=True)\
                .limit(1)\
                .execute()

            latest_candle = result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching latest candle for {symbol_name}: {e}")
            return None

        if not latest_candle:
            return None

        current_price = Decimal(str(latest_candle.get('close', 0)))

        # Step 4 - Check for retest
        # Bullish retest: current_price is near range_high (within 0.1%)
        # Bearish retest: current_price is near range_low (within 0.1%)
        tolerance = Decimal("0.001")  # 0.1%

        if break_direction == 'bullish':
            # Check if price returned to range_high
            price_diff = abs(current_price - range_high)
            is_retest = (price_diff / range_high) <= tolerance
        elif break_direction == 'bearish':
            # Check if price returned to range_low
            price_diff = abs(current_price - range_low)
            is_retest = (price_diff / range_low) <= tolerance
        else:
            is_retest = False

        if not is_retest:
            logger.debug(f"No retest detected for {symbol_name}")
            return None

        # Step 5 - Return alert details
        alert_data = {
            'kind': 'retest_touch',
            'direction': break_direction,
            'price': float(current_price),
            'range_edge': float(range_high if break_direction == 'bullish' else range_low),
            'candle_timestamp': latest_candle.get('ts') if latest_candle else None,
            'detection_time': datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Retest touch detected for {symbol_name}: {break_direction} at {current_price}")
        return alert_data


    def check_asia_sweep_confirmed(
        self,
        symbol_id: UUID,
        symbol_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect EU-Open above y_low after Asia sweep

        Detection Logic:
        - Asia session (02:00-05:00 MEZ): Price swept below y_low
        - EU open (08:00+ MEZ): Price confirms reversal by staying above y_low
        - Confirmation: Current price > y_low for at least 3 consecutive 5m candles

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)

        Returns:
            Dict with alert details if Asia sweep confirmed, None otherwise
        """
        logger.info(f"Checking Asia sweep confirmation for {symbol_name}")

        # Step 1 - Get current time and check if we're in EU session (08:00-10:00 UTC)
        # Note: Using UTC for simplicity. Adjust timezone if needed (Berlin = UTC+1/UTC+2)
        now = datetime.now(timezone.utc)
        current_hour = now.hour

        # EU session is approximately 07:00-09:00 UTC (08:00-10:00 CET/CEST)
        is_eu_session = 7 <= current_hour <= 9

        if not is_eu_session:
            logger.debug(f"Not in EU session for {symbol_name} (current hour: {current_hour})")
            return None

        # Step 2 - Fetch today's levels (y_low)
        try:
            result = self.supabase.table('levels_daily')\
                .select('y_low')\
                .eq('symbol_id', str(symbol_id))\
                .eq('trade_date', now.date().isoformat())\
                .limit(1)\
                .execute()

            levels = result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching levels for {symbol_name}: {e}")
            return None

        if not levels:
            return None

        y_low = Decimal(str(levels.get('y_low', 0)))

        # Step 3 - Check if Asia sweep occurred (01:00-06:00 UTC = 02:00-07:00 CET)
        # Get today's Asia session range
        asia_start = now.replace(hour=1, minute=0, second=0, microsecond=0)
        asia_end = now.replace(hour=6, minute=0, second=0, microsecond=0)

        try:
            result = self.supabase.table('ohlc')\
                .select('low')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '5m')\
                .gte('ts', asia_start.isoformat())\
                .lte('ts', asia_end.isoformat())\
                .execute()

            if not result.data:
                logger.debug(f"No Asia session data for {symbol_name}")
                return None

            # Find minimum low during Asia session
            asia_low = min(Decimal(str(candle['low'])) for candle in result.data)
        except Exception as e:
            logger.error(f"Error fetching Asia session data for {symbol_name}: {e}")
            return None

        asia_sweep_occurred = asia_low < y_low

        if not asia_sweep_occurred:
            logger.debug(f"No Asia sweep detected for {symbol_name}")
            return None

        # Step 4 - Fetch last 3 candles to confirm reversal
        try:
            result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '5m')\
                .order('ts', desc=True)\
                .limit(3)\
                .execute()

            recent_candles = result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching recent candles for {symbol_name}: {e}")
            return None

        if len(recent_candles) < 3:
            return None

        # Step 5 - Check if all 3 candles have close > y_low
        all_above_y_low = all(
            Decimal(str(candle['close'])) > y_low
            for candle in recent_candles
        )

        if not all_above_y_low:
            logger.debug(f"Asia sweep not confirmed for {symbol_name}")
            return None

        # Step 6 - Return alert details
        current_price = Decimal(str(recent_candles[0].get('close', 0)))

        alert_data = {
            'kind': 'asia_sweep_confirmed',
            'price': float(current_price),
            'y_low': float(y_low),
            'asia_low': float(asia_low) if asia_low else None,
            'candle_timestamp': recent_candles[0].get('ts') if recent_candles else None,
            'detection_time': datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Asia sweep confirmed for {symbol_name} at {current_price}")
        return alert_data


    def check_pivot_touches(
        self,
        symbol_id: UUID,
        symbol_name: str
    ) -> List[Dict[str, Any]]:
        """
        Detect price touches Pivot Point, R1, or S1

        Detection Logic:
        - Fetch today's pivot levels (pivot, r1, s1)
        - Get latest candle
        - Check if price is within 0.05% of any level
        - Generate separate alerts for each level touched

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)

        Returns:
            List of alert dicts (can be empty, or contain 1-3 alerts)
            Format: [
                {'kind': 'pivot_touch', 'price': ..., 'level': ...},
                {'kind': 'r1_touch', 'price': ..., 'level': ...},
                ...
            ]
        """
        logger.info(f"Checking pivot touches for {symbol_name}")

        alerts = []

        # Step 1 - Fetch today's pivot levels
        now = datetime.now(timezone.utc)
        try:
            result = self.supabase.table('levels_daily')\
                .select('pivot, r1, s1')\
                .eq('symbol_id', str(symbol_id))\
                .eq('trade_date', now.date().isoformat())\
                .limit(1)\
                .execute()

            levels = result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching pivot levels for {symbol_name}: {e}")
            return alerts

        if not levels:
            logger.warning(f"No pivot levels for {symbol_name}")
            return alerts

        pivot = Decimal(str(levels.get('pivot', 0)))
        r1 = Decimal(str(levels.get('r1', 0)))
        s1 = Decimal(str(levels.get('s1', 0)))

        # Step 2 - Fetch latest candle
        try:
            result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '1m')\
                .order('ts', desc=True)\
                .limit(1)\
                .execute()

            latest_candle = result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching latest candle for {symbol_name}: {e}")
            return alerts

        if not latest_candle:
            return alerts

        current_price = Decimal(str(latest_candle.get('close', 0)))
        candle_high = Decimal(str(latest_candle.get('high', 0)))
        candle_low = Decimal(str(latest_candle.get('low', 0)))

        # Step 3 - Define touch tolerance (0.05% of level)
        tolerance_pct = Decimal("0.0005")  # 0.05%

        # Step 4 - Check each level for touch
        # A "touch" means: candle_low <= level <= candle_high (with tolerance)

        # Check Pivot Point
        if pivot > 0:
            pivot_tolerance = pivot * tolerance_pct
            is_pivot_touch = (candle_low - pivot_tolerance) <= pivot <= (candle_high + pivot_tolerance)

            if is_pivot_touch:
                alerts.append({
                    'kind': 'pivot_touch',
                    'price': float(current_price),
                    'level': float(pivot),
                    'level_name': 'Pivot',
                    'candle_high': float(candle_high),
                    'candle_low': float(candle_low),
                    'candle_timestamp': latest_candle.get('ts'),
                    'detection_time': datetime.now(timezone.utc).isoformat(),
                })
                logger.info(f"Pivot touch detected for {symbol_name} at {current_price}")

        # Check R1
        if r1 > 0:
            r1_tolerance = r1 * tolerance_pct
            is_r1_touch = (candle_low - r1_tolerance) <= r1 <= (candle_high + r1_tolerance)

            if is_r1_touch:
                alerts.append({
                    'kind': 'r1_touch',
                    'price': float(current_price),
                    'level': float(r1),
                    'level_name': 'R1',
                    'candle_high': float(candle_high),
                    'candle_low': float(candle_low),
                    'candle_timestamp': latest_candle.get('ts'),
                    'detection_time': datetime.now(timezone.utc).isoformat(),
                })
                logger.info(f"R1 touch detected for {symbol_name} at {current_price}")

        # Check S1
        if s1 > 0:
            s1_tolerance = s1 * tolerance_pct
            is_s1_touch = (candle_low - s1_tolerance) <= s1 <= (candle_high + s1_tolerance)

            if is_s1_touch:
                alerts.append({
                    'kind': 's1_touch',
                    'price': float(current_price),
                    'level': float(s1),
                    'level_name': 'S1',
                    'candle_high': float(candle_high),
                    'candle_low': float(candle_low),
                    'candle_timestamp': latest_candle.get('ts'),
                    'detection_time': datetime.now(timezone.utc).isoformat(),
                })
                logger.info(f"S1 touch detected for {symbol_name} at {current_price}")

        return alerts


    def create_alert(
        self,
        symbol_id: UUID,
        alert_data: Dict[str, Any],
        user_id: Optional[UUID] = None
    ) -> UUID:
        """
        Write alert to 'alerts' table

        Args:
            symbol_id: UUID of the market symbol
            alert_data: Alert details dict (from check_* methods)
            user_id: Optional user ID (for user-specific alerts, None for global)

        Returns:
            UUID of created alert record
        """
        logger.info(f"Creating alert: {alert_data['kind']} for symbol {symbol_id}")

        # Build alert record
        alert_record = {
            'user_id': str(user_id) if user_id else None,
            'symbol_id': str(symbol_id),
            'kind': alert_data['kind'],
            'context': alert_data,  # Store full alert data as JSON
            'sent': False  # Frontend will mark as True after display
        }

        # Insert into alerts table
        try:
            result = self.supabase.table('alerts')\
                .insert(alert_record)\
                .execute()

            if result.data and len(result.data) > 0:
                alert_id = result.data[0]['id']
                logger.info(f"Alert created with ID: {alert_id}")
                return alert_id
            else:
                logger.error(f"No data returned when creating alert for {symbol_id}")
                return None

        except Exception as e:
            logger.error(f"Error creating alert for symbol {symbol_id}: {e}")
            return None


    def run(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Main execution method - Called by Celery scheduler every 60 seconds

        Process:
        1. Fetch active symbols from market_symbols table
        2. For each symbol:
           a. Check range_break
           b. Check retest_touch
           c. Check asia_sweep_confirmed
           d. Check pivot_touches (returns list)
           e. Create alerts for detected events
        3. Return summary of generated alerts

        Args:
            symbols: Optional list of symbol names to analyze (default: all active symbols)

        Returns:
            Dict with execution summary:
            {
                'execution_time': datetime,
                'symbols_analyzed': int,
                'alerts_generated': int,
                'alerts': List[Dict]
            }
        """
        execution_start = datetime.now(timezone.utc)
        logger.info(f"Alert Engine execution started at {execution_start}")

        # Step 1 - Fetch active symbols
        try:
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
                'alerts_generated': 0,
                'alerts': [],
                'error': str(e)
            }

        if not active_symbols:
            logger.warning("No active symbols found")
            return {
                'execution_time': execution_start.isoformat(),
                'symbols_analyzed': 0,
                'alerts_generated': 0,
                'alerts': []
            }

        logger.info(f"Processing {len(active_symbols)} active symbols")

        # Step 2 - Analyze each symbol
        generated_alerts = []

        for symbol in active_symbols:
            symbol_id = symbol['id']
            symbol_name = symbol['symbol']

            logger.info(f"Processing alerts for symbol: {symbol_name}")

            try:
                # Check 1 - Range Break
                range_break_alert = self.check_range_break(
                    symbol_id=symbol_id,
                    symbol_name=symbol_name
                )

                if range_break_alert:
                    alert_id = self.create_alert(
                        symbol_id=symbol_id,
                        alert_data=range_break_alert
                    )
                    if alert_id:
                        generated_alerts.append({
                            'symbol': symbol_name,
                            'kind': 'range_break',
                            'alert_id': str(alert_id),
                            'details': range_break_alert
                        })

                # Check 2 - Retest Touch
                retest_alert = self.check_retest_touch(
                    symbol_id=symbol_id,
                    symbol_name=symbol_name
                )

                if retest_alert:
                    alert_id = self.create_alert(
                        symbol_id=symbol_id,
                        alert_data=retest_alert
                    )
                    if alert_id:
                        generated_alerts.append({
                            'symbol': symbol_name,
                            'kind': 'retest_touch',
                            'alert_id': str(alert_id),
                            'details': retest_alert
                        })

                # Check 3 - Asia Sweep Confirmed
                asia_sweep_alert = self.check_asia_sweep_confirmed(
                    symbol_id=symbol_id,
                    symbol_name=symbol_name
                )

                if asia_sweep_alert:
                    alert_id = self.create_alert(
                        symbol_id=symbol_id,
                        alert_data=asia_sweep_alert
                    )
                    if alert_id:
                        generated_alerts.append({
                            'symbol': symbol_name,
                            'kind': 'asia_sweep_confirmed',
                            'alert_id': str(alert_id),
                            'details': asia_sweep_alert
                        })

                # Check 4 - Pivot Touches (returns list)
                pivot_alerts = self.check_pivot_touches(
                    symbol_id=symbol_id,
                    symbol_name=symbol_name
                )

                for pivot_alert in pivot_alerts:
                    alert_id = self.create_alert(
                        symbol_id=symbol_id,
                        alert_data=pivot_alert
                    )
                    if alert_id:
                        generated_alerts.append({
                            'symbol': symbol_name,
                            'kind': pivot_alert['kind'],
                            'alert_id': str(alert_id),
                            'details': pivot_alert
                        })

            except Exception as e:
                logger.error(f"Error processing alerts for {symbol_name}: {e}")
                continue

        # Step 3 - Log execution to agent_logs table
        try:
            log_record = {
                'agent_type': 'alert_engine',
                'status': 'success',
                'input_data': {
                    'symbols_filter': symbols,
                    'symbols_count': len(active_symbols)
                },
                'output_data': {
                    'alerts_generated': len(generated_alerts),
                    'alerts': generated_alerts
                },
                'duration_ms': None  # Will be calculated below
            }

            # Will be filled after duration calculation
        except Exception as e:
            logger.warning(f"Error logging to agent_logs: {e}")
            # Continue even if logging fails

        execution_end = datetime.now(timezone.utc)
        duration_ms = int((execution_end - execution_start).total_seconds() * 1000)

        summary = {
            'execution_time': execution_start.isoformat(),
            'execution_duration_ms': duration_ms,
            'symbols_analyzed': len(active_symbols),
            'alerts_generated': len(generated_alerts),
            'alerts': generated_alerts
        }

        logger.info(f"Alert Engine execution completed: {summary}")
        return summary


# Example usage (for testing)
if __name__ == "__main__":
    # This would be called from Celery task
    from config.supabase import get_supabase_admin

    # Initialize agent with admin client (bypasses RLS)
    engine = AlertEngine(supabase_client=get_supabase_admin())

    # Run analysis
    result = engine.run()

    print("Alert Engine Results:")
    print(result)
