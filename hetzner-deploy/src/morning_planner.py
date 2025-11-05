"""
TradeMatrix.ai - Morning Planner Agent
Analyzes overnight market movements and generates morning trading setups.

Execution: Daily at 08:25 MEZ (via Celery scheduler)
Strategies:
  1. Asia Sweep -> EU Open Reversal
  2. Y-Low -> Pivot Rebound

Data sources:
  - ohlc table (1m/5m candles from 02:00-08:25 MEZ)
  - levels_daily table (pivot points, r1/r2, s1/s2, y_high, y_low)

Output: Trading setups in 'setups' table
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from uuid import UUID
import pytz

from supabase import Client

from src.chart_service import ChartService

# Setup logger
logger = logging.getLogger(__name__)


class MorningPlanner:
    """
    Morning Planner Agent - Analyzes overnight price action and generates trading setups

    Responsibilities:
    - Detect Asia Sweep -> EU Open Reversal patterns
    - Identify Y-Low -> Pivot Rebound setups
    - Calculate entry zones, stop loss, take profit
    - Generate setup records in database
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize Morning Planner agent

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
        """
        self.supabase = supabase_client
        self.chart_service = ChartService(supabase_client=supabase_client)
        logger.info("MorningPlanner initialized with ChartService")


    def analyze_asia_sweep(
        self,
        symbol_id: UUID,
        symbol_name: str,
        trade_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Detect Asia Sweep -> EU Open Reversal setup

        Strategy Logic:
        - Asia Session (02:00-05:00 MEZ): Price sweeps below y_low
        - EU Open (08:00+ MEZ): Price reverses back above y_low
        - Signal: Potential long entry when EU open > y_low after Asia sweep

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)
            trade_date: Current trading date

        Returns:
            Dict with setup details if pattern detected, None otherwise
            Format: {
                'strategy': 'asia_sweep',
                'side': 'long' | 'short',
                'entry_price': Decimal,
                'stop_loss': Decimal,
                'take_profit': Decimal,
                'confidence': float (0.0-1.0),
                'metadata': {...}
            }
        """
        logger.info(f"Analyzing Asia Sweep for {symbol_name} on {trade_date}")

        try:
            # Step 1 - Fetch eod_levels for today (yesterday's data)
            trade_date_str = trade_date.strftime('%Y-%m-%d')
            levels_result = self.supabase.table('eod_levels')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('trade_date', trade_date_str)\
                .execute()

            if not levels_result.data or len(levels_result.data) == 0:
                logger.warning(f"No EOD levels found for {symbol_name} on {trade_date_str}")
                return None

            levels = levels_result.data[0]
            y_low = Decimal(str(levels['yesterday_low'])) if levels['yesterday_low'] else None
            y_high = Decimal(str(levels['yesterday_high'])) if levels['yesterday_high'] else None
            y_close = Decimal(str(levels['yesterday_close'])) if levels['yesterday_close'] else None

            if not y_low or not y_high:
                logger.warning(f"Missing yesterday_low or yesterday_high for {symbol_name}")
                return None

            # Use yesterday_close as pivot fallback, calculate simple R1
            pivot = y_close if y_close else (y_high + y_low) / Decimal('2')
            r1 = y_high  # Use yesterday_high as resistance level

            # Step 2 - Fetch OHLC data for Asia session (02:00-05:00 MEZ)
            berlin_tz = pytz.timezone('Europe/Berlin')
            trade_date_berlin = berlin_tz.localize(datetime(trade_date.year, trade_date.month, trade_date.day))

            asia_start = (trade_date_berlin + timedelta(hours=2)).astimezone(pytz.UTC)
            asia_end = (trade_date_berlin + timedelta(hours=5)).astimezone(pytz.UTC)

            asia_result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '5m')\
                .gte('ts', asia_start.isoformat())\
                .lte('ts', asia_end.isoformat())\
                .order('ts', desc=False)\
                .execute()

            asia_candles = asia_result.data if asia_result.data else []

            if not asia_candles:
                logger.warning(f"No Asia session candles for {symbol_name}")
                return None

            # Step 3 - Detect sweep below y_low during Asia session
            asia_sweep_detected = False
            asia_low = None
            total_volume = 0

            for candle in asia_candles:
                candle_low = Decimal(str(candle['low']))
                if candle_low < y_low:
                    asia_sweep_detected = True
                    asia_low = candle_low if asia_low is None else min(asia_low, candle_low)
                total_volume += candle.get('volume', 0)

            if not asia_sweep_detected:
                logger.info(f"No Asia sweep detected for {symbol_name}")
                return None

            avg_volume = total_volume / len(asia_candles) if asia_candles else 0

            # Step 4 - Fetch latest candle (EU Open ~08:00-08:25)
            eu_open_start = (trade_date_berlin + timedelta(hours=8)).astimezone(pytz.UTC)

            eu_result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '5m')\
                .gte('ts', eu_open_start.isoformat())\
                .order('ts', desc=True)\
                .limit(1)\
                .execute()

            if not eu_result.data or len(eu_result.data) == 0:
                logger.warning(f"No EU open candle for {symbol_name}")
                return None

            eu_open_candle = eu_result.data[0]
            eu_close = Decimal(str(eu_open_candle['close']))
            eu_volume = eu_open_candle.get('volume', 0)

            # Step 5 - Check reversal condition
            is_reversal = eu_close > y_low

            if not is_reversal:
                logger.info(f"No reversal detected for {symbol_name} (EU close: {eu_close}, y_low: {y_low})")
                return None

            # Step 6 - Calculate entry, stop loss, take profit
            entry_price = eu_close

            # Stop Loss: asia_low - 0.25% buffer
            sl_buffer = asia_low * Decimal('0.0025')
            stop_loss = asia_low - sl_buffer

            # Take Profit: Use pivot if closer, otherwise R1
            distance_to_pivot = abs(pivot - entry_price)
            distance_to_r1 = abs(r1 - entry_price) if r1 else distance_to_pivot

            take_profit = pivot if distance_to_pivot <= distance_to_r1 else (r1 if r1 else pivot)

            # Step 7 - Calculate confidence score (0.0-1.0)
            # Factors:
            # 1. Distance from y_low to entry (closer = higher confidence)
            entry_distance_pct = abs(float((entry_price - y_low) / y_low * 100))
            distance_score = max(0.0, min(1.0, 1.0 - (entry_distance_pct / 2.0)))  # 0-2% = high score

            # 2. Volume confirmation (>1.5x average)
            volume_score = min(1.0, eu_volume / (avg_volume * 1.5)) if avg_volume > 0 else 0.5

            # 3. Sweep depth (deeper sweep = higher confidence)
            sweep_depth_pct = abs(float((asia_low - y_low) / y_low * 100))
            sweep_score = min(1.0, sweep_depth_pct / 1.0)  # 0-1% sweep depth

            # Weighted average
            confidence = (distance_score * 0.4 + volume_score * 0.3 + sweep_score * 0.3)
            confidence = round(confidence, 2)

            # Step 8 - Return setup details
            setup = {
                "strategy": "asia_sweep",
                "side": "long",
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "metadata": {
                    "asia_low": float(asia_low),
                    "y_low": float(y_low),
                    "pivot": float(pivot),
                    "r1": float(r1) if r1 else None,
                    "eu_open_close": float(eu_close),
                    "sweep_depth_pct": round(sweep_depth_pct, 2),
                    "entry_distance_pct": round(entry_distance_pct, 2),
                    "volume_ratio": round(eu_volume / avg_volume, 2) if avg_volume > 0 else 0,
                    "detection_time": datetime.now(timezone.utc).isoformat(),
                }
            }

            logger.info(f"Asia Sweep setup detected for {symbol_name}: {setup}")
            return setup

        except Exception as e:
            logger.error(f"Error analyzing Asia Sweep for {symbol_name}: {str(e)}", exc_info=True)
            return None


    def analyze_y_low_rebound(
        self,
        symbol_id: UUID,
        symbol_name: str,
        trade_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Detect Y-Low -> Pivot Rebound setup

        Strategy Logic:
        - Open < Pivot (market opens below pivot point)
        - No immediate breakout detected
        - Entry zone: Between y_low and pivot
        - Target: Price rebounds from y_low area towards pivot/r1

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)
            trade_date: Current trading date

        Returns:
            Dict with setup details if pattern detected, None otherwise
        """
        logger.info(f"Analyzing Y-Low Rebound for {symbol_name} on {trade_date}")

        try:
            # Step 1 - Fetch eod_levels for today (yesterday's data)
            trade_date_str = trade_date.strftime('%Y-%m-%d')
            levels_result = self.supabase.table('eod_levels')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('trade_date', trade_date_str)\
                .execute()

            if not levels_result.data or len(levels_result.data) == 0:
                logger.warning(f"No EOD levels found for {symbol_name} on {trade_date_str}")
                return None

            levels = levels_result.data[0]
            y_low = Decimal(str(levels['yesterday_low'])) if levels['yesterday_low'] else None
            y_high = Decimal(str(levels['yesterday_high'])) if levels['yesterday_high'] else None
            y_close = Decimal(str(levels['yesterday_close'])) if levels['yesterday_close'] else None

            if not y_low or not y_high:
                logger.warning(f"Missing yesterday_low or yesterday_high for {symbol_name}")
                return None

            # Use yesterday_close as pivot fallback, calculate simple R1
            pivot = y_close if y_close else (y_high + y_low) / Decimal('2')
            r1 = y_high  # Use yesterday_high as resistance level

            # Step 2 - Fetch first candle of the day (market open at 08:00 MEZ)
            berlin_tz = pytz.timezone('Europe/Berlin')
            trade_date_berlin = berlin_tz.localize(datetime(trade_date.year, trade_date.month, trade_date.day))
            market_open_time = (trade_date_berlin + timedelta(hours=8)).astimezone(pytz.UTC)

            open_result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '5m')\
                .gte('ts', market_open_time.isoformat())\
                .order('ts', desc=False)\
                .limit(1)\
                .execute()

            if not open_result.data or len(open_result.data) == 0:
                logger.warning(f"No market open candle for {symbol_name}")
                return None

            market_open_candle = open_result.data[0]
            market_open_price = Decimal(str(market_open_candle['open']))

            # Step 3 - Check if open < pivot
            open_below_pivot = market_open_price < pivot

            if not open_below_pivot:
                logger.info(f"Market did not open below pivot for {symbol_name} (open: {market_open_price}, pivot: {pivot})")
                return None

            # Step 4 - Check for breakout (fetch latest candle to check current price)
            current_result = self.supabase.table('ohlc')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('timeframe', '5m')\
                .order('ts', desc=True)\
                .limit(1)\
                .execute()

            if not current_result.data:
                logger.warning(f"No current candle for {symbol_name}")
                return None

            current_candle = current_result.data[0]
            current_price = Decimal(str(current_candle['close']))

            # If price already broke above pivot, setup is invalid
            breakout_occurred = current_price > pivot

            if breakout_occurred:
                logger.info(f"Breakout already occurred for {symbol_name} (current: {current_price}, pivot: {pivot})")
                return None

            # Step 5 - Define entry zone (midpoint between y_low and pivot)
            # Using midpoint as entry provides better risk/reward
            entry_price = (y_low + pivot) / Decimal('2')

            # Alternatively, could use current price if it's in the zone
            if y_low <= current_price <= pivot:
                entry_price = current_price

            # Step 6 - Calculate stop loss and take profit
            # Stop Loss: y_low - 0.25% buffer
            sl_buffer = y_low * Decimal('0.0025')
            stop_loss = y_low - sl_buffer

            # Take Profit: Use pivot as first target, R1 as extended target
            take_profit = pivot
            extended_target = r1 if r1 else pivot

            # Step 7 - Calculate confidence score
            # Factors:
            # 1. Distance from y_low (closer to y_low = clearer level, but higher risk)
            distance_from_ylow = abs(float((current_price - y_low) / y_low * 100))
            # Sweet spot: 0.5-1.5% above y_low
            if 0.5 <= distance_from_ylow <= 1.5:
                distance_score = 1.0
            elif distance_from_ylow < 0.5:
                distance_score = 0.7  # Too close, risky
            else:
                distance_score = max(0.0, 1.0 - ((distance_from_ylow - 1.5) / 3.0))  # Further = lower score

            # 2. Time of day (earlier = more time for rebound)
            now_berlin = datetime.now(berlin_tz)
            hour = now_berlin.hour
            if 8 <= hour <= 9:
                time_score = 1.0  # Early morning, best time
            elif 9 < hour <= 11:
                time_score = 0.8  # Still good
            elif 11 < hour <= 13:
                time_score = 0.6  # Afternoon, less time
            else:
                time_score = 0.4  # Late day

            # 3. Market structure (no immediate resistance above entry)
            resistance_score = 0.8  # Default (could enhance with more analysis)

            # Weighted average
            confidence = (distance_score * 0.4 + time_score * 0.3 + resistance_score * 0.3)
            confidence = round(confidence, 2)

            # Step 8 - Return setup details
            setup = {
                "strategy": "y_low_rebound",
                "side": "long",
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": confidence,
                "metadata": {
                    "y_low": float(y_low),
                    "pivot": float(pivot),
                    "r1": float(r1) if r1 else None,
                    "market_open": float(market_open_price),
                    "current_price": float(current_price),
                    "extended_target": float(extended_target),
                    "distance_from_ylow_pct": round(distance_from_ylow, 2),
                    "time_of_analysis": now_berlin.strftime('%H:%M'),
                    "detection_time": datetime.now(timezone.utc).isoformat(),
                }
            }

            logger.info(f"Y-Low Rebound setup detected for {symbol_name}: {setup}")
            return setup

        except Exception as e:
            logger.error(f"Error analyzing Y-Low Rebound for {symbol_name}: {str(e)}", exc_info=True)
            return None


    async def generate_setup(
        self,
        symbol_id: UUID,
        symbol_name: str,
        setup_data: Dict[str, Any],
        user_id: Optional[UUID] = None
    ) -> UUID:
        """
        Generate and save setup entry in 'setups' table

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)
            setup_data: Dict returned from analyze_asia_sweep() or analyze_y_low_rebound()
            user_id: Optional user ID (for user-specific setups, None for global)

        Returns:
            UUID of the created setup record
        """
        logger.info(f"Generating setup for {symbol_name}: {setup_data['strategy']}")

        try:
            # Generate charts for setup (1h for structure, 15m for entry, 1D for context)
            chart_url_1h = None
            chart_url_15m = None
            chart_url_1d = None
            chart_snapshot_id = None

            try:
                logger.info(f"Generating charts for setup: {symbol_name}...")

                # 1h chart (intraday profile - structure)
                chart_url_1h = await self.chart_service.generate_chart_url(
                    symbol=symbol_name,
                    timeframe='1h',
                    agent_name='MorningPlanner',
                    symbol_id=str(symbol_id)
                )

                # 15m chart (intraday profile - entry)
                chart_url_15m = await self.chart_service.generate_chart_url(
                    symbol=symbol_name,
                    timeframe='15m',
                    agent_name='MorningPlanner',
                    symbol_id=str(symbol_id)
                )

                # 1D chart (swing profile - context with prev high/low)
                chart_url_1d = await self.chart_service.generate_chart_url(
                    symbol=symbol_name,
                    timeframe='1D',
                    agent_name='MorningPlanner',
                    symbol_id=str(symbol_id)
                )

                # Save snapshot for primary timeframe (1h)
                if chart_url_1h:
                    chart_snapshot_id = await self.chart_service.save_snapshot(
                        symbol_id=str(symbol_id),
                        chart_url=chart_url_1h,
                        timeframe='1h',
                        agent_name='MorningPlanner',
                        metadata={
                            'strategy': setup_data['strategy'],
                            'confidence': setup_data['confidence']
                        }
                    )
                    logger.info(f"📊 Setup charts generated: 1h, 15m, 1D")

            except Exception as e:
                logger.warning(f"Chart generation failed for setup: {e}")
                # Continue without chart - setup is still valid

            # Prepare setup record for database insertion
            setup_record = {
                "user_id": str(user_id) if user_id else None,
                "module": "morning",
                "symbol_id": str(symbol_id),
                "strategy": setup_data["strategy"],
                "side": setup_data["side"],
                "entry_price": float(setup_data["entry_price"]),
                "stop_loss": float(setup_data["stop_loss"]),
                "take_profit": float(setup_data["take_profit"]),
                "confidence": setup_data["confidence"],
                "status": "pending",
                "payload": {
                    **setup_data,  # Full JSON details including metadata
                    "chart_url_1h": chart_url_1h,
                    "chart_url_15m": chart_url_15m,
                    "chart_url_1d": chart_url_1d,
                    "chart_snapshot_id": str(chart_snapshot_id) if chart_snapshot_id else None
                }
            }

            # Insert into setups table
            result = self.supabase.table("setups").insert(setup_record).execute()

            if not result.data or len(result.data) == 0:
                logger.error(f"Failed to insert setup for {symbol_name}")
                return None

            setup_id = result.data[0]["id"]
            logger.info(f"Setup created with ID: {setup_id} for {symbol_name}")

            return UUID(setup_id)

        except Exception as e:
            logger.error(f"Error generating setup for {symbol_name}: {str(e)}", exc_info=True)
            return None


    async def run(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Main execution method - Called by Celery scheduler at 08:25 MEZ daily

        Process:
        1. Fetch active symbols from market_symbols table
        2. For each symbol:
           a. Run analyze_asia_sweep()
           b. Run analyze_y_low_rebound()
           c. Generate setup if pattern detected
        3. Return summary of generated setups

        Args:
            symbols: Optional list of symbol names to analyze (default: all active symbols)

        Returns:
            Dict with execution summary:
            {
                'execution_time': datetime,
                'symbols_analyzed': int,
                'setups_generated': int,
                'setups': List[Dict]
            }
        """
        execution_start = datetime.now(timezone.utc)
        logger.info(f"Morning Planner execution started at {execution_start}")

        try:
            # Step 1 - Fetch active symbols from database
            query = self.supabase.table('market_symbols')\
                .select('id, symbol')\
                .eq('active', True)

            # If specific symbols requested, filter by them
            if symbols:
                query = query.in_('symbol', symbols)

            symbols_result = query.execute()

            active_symbols = symbols_result.data if symbols_result.data else []

            if not active_symbols:
                logger.warning("No active symbols found")
                return {
                    "execution_time": execution_start.isoformat(),
                    "symbols_analyzed": 0,
                    "setups_generated": 0,
                    "setups": []
                }

            logger.info(f"Found {len(active_symbols)} active symbols to analyze")

            # Step 2 - Get current trade date (today in Berlin timezone)
            berlin_tz = pytz.timezone('Europe/Berlin')
            trade_date = datetime.now(berlin_tz)

            # Step 3 - Analyze each symbol
            generated_setups = []

            for symbol in active_symbols:
                symbol_id = UUID(symbol["id"])
                symbol_name = symbol["symbol"]

                logger.info(f"Processing symbol: {symbol_name}")

                # Run strategy 1 - Asia Sweep
                try:
                    asia_sweep_setup = self.analyze_asia_sweep(
                        symbol_id=symbol_id,
                        symbol_name=symbol_name,
                        trade_date=trade_date
                    )

                    if asia_sweep_setup:
                        setup_id = await self.generate_setup(
                            symbol_id=symbol_id,
                            symbol_name=symbol_name,
                            setup_data=asia_sweep_setup
                        )
                        if setup_id:
                            generated_setups.append({
                                "symbol": symbol_name,
                                "strategy": "asia_sweep",
                                "setup_id": str(setup_id),
                                "confidence": asia_sweep_setup["confidence"],
                                "entry_price": float(asia_sweep_setup["entry_price"])
                            })
                except Exception as e:
                    logger.error(f"Error analyzing Asia Sweep for {symbol_name}: {str(e)}", exc_info=True)

                # Run strategy 2 - Y-Low Rebound
                try:
                    y_low_setup = self.analyze_y_low_rebound(
                        symbol_id=symbol_id,
                        symbol_name=symbol_name,
                        trade_date=trade_date
                    )

                    if y_low_setup:
                        setup_id = await self.generate_setup(
                            symbol_id=symbol_id,
                            symbol_name=symbol_name,
                            setup_data=y_low_setup
                        )
                        if setup_id:
                            generated_setups.append({
                                "symbol": symbol_name,
                                "strategy": "y_low_rebound",
                                "setup_id": str(setup_id),
                                "confidence": y_low_setup["confidence"],
                                "entry_price": float(y_low_setup["entry_price"])
                            })
                except Exception as e:
                    logger.error(f"Error analyzing Y-Low Rebound for {symbol_name}: {str(e)}", exc_info=True)

            # Step 4 - Log execution to agent_logs table (if table exists)
            # For now, we'll skip this as agent_logs table structure is not defined in migrations

            execution_end = datetime.now(timezone.utc)
            duration_ms = int((execution_end - execution_start).total_seconds() * 1000)

            summary = {
                "execution_time": execution_start.isoformat(),
                "execution_duration_ms": duration_ms,
                "symbols_analyzed": len(active_symbols),
                "setups_generated": len(generated_setups),
                "setups": generated_setups
            }

            logger.info(f"Morning Planner execution completed: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Fatal error in Morning Planner execution: {str(e)}", exc_info=True)
            execution_end = datetime.now(timezone.utc)
            duration_ms = int((execution_end - execution_start).total_seconds() * 1000)

            return {
                "execution_time": execution_start.isoformat(),
                "execution_duration_ms": duration_ms,
                "symbols_analyzed": 0,
                "setups_generated": 0,
                "setups": [],
                "error": str(e)
            }


# Example usage (for testing)
if __name__ == "__main__":
    # This would be called from Celery task
    from config.supabase import get_supabase_admin

    # Initialize agent with admin client (bypasses RLS)
    planner = MorningPlanner(supabase_client=get_supabase_admin())

    # Run analysis
    result = planner.run()

    print("Morning Planner Results:")
    print(result)
