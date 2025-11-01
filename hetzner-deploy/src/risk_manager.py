"""
TradeMatrix.ai - RiskManager Agent
Monitors portfolio risk, validates position sizing, and enforces risk management rules.

Execution: Every 60 seconds (via Celery scheduler)
Responsibilities:
  1. Validate position sizes against 1% risk rule
  2. Calculate aggregate portfolio risk exposure
  3. Enforce daily loss limit (3-loss rule)
  4. Adjust stop losses to break-even when applicable
  5. Pre-trade risk validation for new trades
  6. Generate risk alerts for violations

Data sources:
  - trades table (active trades and positions)
  - market_symbols table (current prices via ohlc)
  - user_settings table (account balance, risk preferences)

Output: Risk alerts in 'alerts' table, trade updates in 'trades' table
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from uuid import UUID

from supabase import Client

# Setup logger
logger = logging.getLogger(__name__)


class RiskManager:
    """
    RiskManager Agent - Monitors and enforces risk management rules

    Responsibilities:
    - Validate position sizes don't exceed 1% risk rule
    - Monitor total portfolio risk exposure
    - Enforce 3-loss daily limit
    - Move stop losses to break-even when +0.5R profit reached
    - Pre-validate new trades before execution
    - Generate risk alerts for violations
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize RiskManager agent

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
        """
        self.supabase = supabase_client
        logger.info("RiskManager initialized")


    def check_position_sizes(
        self,
        symbol_id: UUID,
        symbol_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate position sizing rules for active trades

        Checks:
        1. Position size doesn't exceed 1% risk per trade
        2. Risk-per-unit calculation is correct
        3. Leverage is within safe limits

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (for logging)

        Returns:
            Dict with validation results and any violations:
            {
                'symbol_id': UUID,
                'symbol_name': str,
                'trades_checked': int,
                'violations': List[Dict],
                'total_risk': float
            }
        """
        logger.info(f"Checking position sizes for {symbol_name}")

        try:
            # Import risk calculator
            import sys
            import os
            api_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api/src'))
            sys.path.insert(0, api_src_path)
            from core.risk_calculator import RiskCalculator

            # Step 1 - Fetch active trades for this symbol
            result = self.supabase.table('trades')\
                .select('*')\
                .eq('symbol_id', str(symbol_id))\
                .eq('status', 'active')\
                .execute()

            active_trades = result.data if result.data else []

            if not active_trades:
                logger.debug(f"No active trades for {symbol_name}")
                return None

            logger.info(f"Checking {len(active_trades)} active trades for {symbol_name}")

            violations = []
            total_risk = Decimal('0.0')

            # Step 2 - Get user's account balance (assume first trade has user_id)
            user_id = active_trades[0].get('user_id')

            # Fetch user settings for account balance
            user_result = self.supabase.table('profiles')\
                .select('metadata')\
                .eq('id', user_id)\
                .single()\
                .execute()

            account_balance = 10000.0  # Default fallback
            if user_result.data and user_result.data.get('metadata'):
                account_balance = float(user_result.data['metadata'].get('account_balance', 10000.0))

            # Initialize risk calculator
            risk_calc = RiskCalculator(account_balance=account_balance, risk_per_trade=0.01)

            # Step 3 - Validate each trade
            for trade in active_trades:
                trade_id = trade['id']
                entry_price = float(trade['entry_price'])
                stop_loss = float(trade['stop_loss'])
                position_size = float(trade['position_size'])

                # Validate trade risk
                validation = risk_calc.validate_trade_risk(
                    entry=entry_price,
                    stop_loss=stop_loss,
                    position_size=position_size,
                    account_balance=account_balance
                )

                risk_amount = Decimal(str(validation['risk_amount']))
                total_risk += risk_amount

                # Check for violations
                if not validation['is_valid']:
                    violations.append({
                        'trade_id': trade_id,
                        'symbol': symbol_name,
                        'risk_amount': float(risk_amount),
                        'risk_percentage': validation['risk_percentage'],
                        'warnings': validation['warnings']
                    })
                    logger.warning(
                        f"Position size violation for trade {trade_id}: "
                        f"{validation['warnings']}"
                    )

            return {
                'symbol_id': str(symbol_id),
                'symbol_name': symbol_name,
                'trades_checked': len(active_trades),
                'violations': violations,
                'total_risk': float(total_risk),
                'account_balance': account_balance
            }

        except Exception as e:
            logger.error(f"Error checking position sizes for {symbol_name}: {e}", exc_info=True)
            return None


    def check_portfolio_risk(self) -> Dict[str, Any]:
        """
        Calculate aggregate portfolio risk exposure

        Aggregates:
        1. Total risk across all active trades
        2. Total position value (leverage exposure)
        3. Concentration by symbol (max 2-3 trades per symbol)
        4. Correlation risk (multiple correlated positions)

        Returns:
            Dict with portfolio risk metrics:
            {
                'total_risk_amount': float,
                'total_risk_percentage': float,
                'total_position_value': float,
                'total_leverage': float,
                'active_trades_count': int,
                'symbols_exposed': int,
                'warnings': List[str]
            }
        """
        logger.info("Calculating portfolio risk")

        try:
            # Import risk calculator
            import sys
            import os
            api_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api/src'))
            sys.path.insert(0, api_src_path)
            from core.risk_calculator import RiskCalculator

            # Step 1 - Fetch all active trades across all symbols
            result = self.supabase.table('trades')\
                .select('*')\
                .eq('status', 'active')\
                .execute()

            active_trades = result.data if result.data else []

            if not active_trades:
                logger.info("No active trades in portfolio")
                return {
                    'total_risk_amount': 0.0,
                    'total_risk_percentage': 0.0,
                    'total_position_value': 0.0,
                    'total_leverage': 0.0,
                    'active_trades_count': 0,
                    'symbols_exposed': 0,
                    'warnings': []
                }

            logger.info(f"Analyzing portfolio risk across {len(active_trades)} active trades")

            # Get account balance from first trade's user
            user_id = active_trades[0].get('user_id')
            user_result = self.supabase.table('profiles')\
                .select('metadata')\
                .eq('id', user_id)\
                .single()\
                .execute()

            account_balance = 10000.0  # Default
            if user_result.data and user_result.data.get('metadata'):
                account_balance = float(user_result.data['metadata'].get('account_balance', 10000.0))

            # Initialize risk calculator
            risk_calc = RiskCalculator(account_balance=account_balance, risk_per_trade=0.01)

            # Step 2 - Aggregate risk metrics
            total_risk_amount = Decimal('0.0')
            total_position_value = Decimal('0.0')
            symbols_count = {}
            warnings = []

            for trade in active_trades:
                entry_price = float(trade['entry_price'])
                stop_loss = float(trade['stop_loss'])
                position_size = float(trade['position_size'])
                symbol_id = trade['symbol_id']

                # Calculate risk for this trade
                risk_per_unit = abs(entry_price - stop_loss)
                trade_risk = Decimal(str(position_size * risk_per_unit))
                total_risk_amount += trade_risk

                # Calculate position value
                position_value = Decimal(str(position_size * entry_price))
                total_position_value += position_value

                # Track symbols
                if symbol_id not in symbols_count:
                    symbols_count[symbol_id] = 0
                symbols_count[symbol_id] += 1

            # Step 3 - Calculate percentages and leverage
            total_risk_percentage = float((total_risk_amount / Decimal(str(account_balance))) * 100)
            total_leverage = float(total_position_value / Decimal(str(account_balance)))

            # Step 4 - Check for warnings
            # Warning 1: Total risk > 5% (across all trades)
            if total_risk_percentage > 5.0:
                warnings.append(
                    f"Total portfolio risk ({total_risk_percentage:.2f}%) exceeds 5% limit"
                )

            # Warning 2: Too many trades per symbol (max 2-3)
            for symbol_id, count in symbols_count.items():
                if count > 3:
                    warnings.append(
                        f"Symbol {symbol_id} has {count} active trades (max recommended: 3)"
                    )

            # Warning 3: High leverage
            if total_leverage > 10.0:
                warnings.append(
                    f"Total portfolio leverage ({total_leverage:.2f}x) exceeds safe limit (10x)"
                )

            # Warning 4: Too many concurrent trades
            if len(active_trades) > 10:
                warnings.append(
                    f"Too many concurrent trades ({len(active_trades)}) - consider reducing exposure"
                )

            portfolio_risk = {
                'total_risk_amount': float(total_risk_amount),
                'total_risk_percentage': total_risk_percentage,
                'total_position_value': float(total_position_value),
                'total_leverage': total_leverage,
                'active_trades_count': len(active_trades),
                'symbols_exposed': len(symbols_count),
                'account_balance': account_balance,
                'warnings': warnings
            }

            if warnings:
                logger.warning(f"Portfolio risk warnings: {warnings}")

            logger.info(
                f"Portfolio risk: {total_risk_percentage:.2f}% "
                f"({len(active_trades)} trades, {len(symbols_count)} symbols)"
            )

            return portfolio_risk

        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}", exc_info=True)
            return {
                'error': str(e),
                'warnings': [f"Failed to calculate portfolio risk: {str(e)}"]
            }


    def check_daily_loss_limit(self) -> Dict[str, Any]:
        """
        Enforce daily loss limit (3-loss rule)

        Rules:
        1. Max 3 losing trades per day
        2. If 3 losses reached, stop trading for the day
        3. Track P&L for the current trading day

        Returns:
            Dict with daily loss status:
            {
                'trade_date': str,
                'losses_today': int,
                'wins_today': int,
                'daily_pnl': float,
                'limit_reached': bool,
                'warnings': List[str]
            }
        """
        logger.info("Checking daily loss limit")

        try:
            # Get today's date
            today = datetime.now(timezone.utc).date()

            # Step 1 - Fetch today's closed trades
            result = self.supabase.table('trades')\
                .select('*')\
                .eq('status', 'closed')\
                .gte('closed_at', today.isoformat())\
                .execute()

            today_trades = result.data if result.data else []

            if not today_trades:
                logger.info("No closed trades today")
                return {
                    'trade_date': str(today),
                    'losses_today': 0,
                    'wins_today': 0,
                    'daily_pnl': 0.0,
                    'limit_reached': False,
                    'warnings': []
                }

            logger.info(f"Analyzing {len(today_trades)} closed trades for today")

            # Step 2 - Count wins and losses
            losses = 0
            wins = 0
            daily_pnl = Decimal('0.0')

            for trade in today_trades:
                pnl = Decimal(str(trade.get('pnl', 0.0)))
                daily_pnl += pnl

                if pnl < 0:
                    losses += 1
                elif pnl > 0:
                    wins += 1

            # Step 3 - Check 3-loss rule
            limit_reached = losses >= 3
            warnings = []

            if limit_reached:
                warnings.append(
                    f"STOP TRADING: 3-loss limit reached today ({losses} losses)"
                )
                logger.warning(f"3-loss limit reached: {losses} losses today")
            elif losses == 2:
                warnings.append(
                    f"WARNING: 2 losses today - one more loss will trigger daily limit"
                )

            # Additional warning for negative daily P&L
            if float(daily_pnl) < -100.0:  # Example threshold
                warnings.append(
                    f"Daily P&L is negative: {float(daily_pnl):.2f} EUR"
                )

            result = {
                'trade_date': str(today),
                'losses_today': losses,
                'wins_today': wins,
                'daily_pnl': float(daily_pnl),
                'limit_reached': limit_reached,
                'warnings': warnings,
                'total_trades_today': len(today_trades)
            }

            logger.info(
                f"Daily loss check: {wins}W-{losses}L, PnL: {float(daily_pnl):.2f} EUR"
            )

            return result

        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}", exc_info=True)
            return {
                'error': str(e),
                'warnings': [f"Failed to check daily loss limit: {str(e)}"]
            }


    def adjust_stop_loss(self, trade_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Move stop loss to break-even when trade reaches +0.5R

        Process:
        1. Fetch trade details
        2. Get current market price
        3. Check if +0.5R profit reached using RiskCalculator
        4. If yes, update stop loss to entry price
        5. Log adjustment in trade history

        Args:
            trade_id: UUID of the trade to check

        Returns:
            Dict with adjustment result:
            {
                'trade_id': UUID,
                'adjusted': bool,
                'old_stop_loss': float,
                'new_stop_loss': float,
                'current_r': float,
                'reason': str
            }
        """
        logger.info(f"Checking stop loss adjustment for trade {trade_id}")

        try:
            # Import risk calculator
            import sys
            import os
            api_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api/src'))
            sys.path.insert(0, api_src_path)
            from core.risk_calculator import RiskCalculator

            # Step 1 - Fetch trade details
            result = self.supabase.table('trades')\
                .select('*')\
                .eq('id', str(trade_id))\
                .single()\
                .execute()

            trade = result.data
            if not trade:
                logger.warning(f"Trade {trade_id} not found")
                return None

            # Only adjust active trades
            if trade['status'] != 'active':
                logger.debug(f"Trade {trade_id} is not active (status: {trade['status']})")
                return None

            entry_price = float(trade['entry_price'])
            stop_loss = float(trade['stop_loss'])
            symbol_id = trade['symbol_id']

            # Step 2 - Get current market price
            price_result = self.supabase.table('ohlc')\
                .select('close')\
                .eq('symbol_id', symbol_id)\
                .eq('timeframe', '1m')\
                .order('ts', desc=True)\
                .limit(1)\
                .execute()

            if not price_result.data:
                logger.warning(f"No current price data for symbol {symbol_id}")
                return None

            current_price = float(price_result.data[0]['close'])

            # Step 3 - Check if break-even condition met
            risk_calc = RiskCalculator(account_balance=10000)  # Balance not needed for this calc
            be_check = risk_calc.should_move_to_break_even(
                entry=entry_price,
                current_price=current_price,
                stop_loss=stop_loss,
                threshold_r=0.5
            )

            if not be_check['should_move']:
                logger.debug(
                    f"Break-even not reached for trade {trade_id}: {be_check['reason']}"
                )
                return {
                    'trade_id': str(trade_id),
                    'adjusted': False,
                    'old_stop_loss': stop_loss,
                    'new_stop_loss': stop_loss,
                    'current_r': be_check['current_r'],
                    'reason': be_check['reason']
                }

            # Step 4 - Update stop loss to entry (break-even)
            new_stop_loss = entry_price

            update_result = self.supabase.table('trades')\
                .update({'stop_loss': new_stop_loss})\
                .eq('id', str(trade_id))\
                .execute()

            if not update_result.data:
                logger.error(f"Failed to update stop loss for trade {trade_id}")
                return None

            logger.info(
                f"Stop loss adjusted to break-even for trade {trade_id}: "
                f"{stop_loss:.4f} -> {new_stop_loss:.4f} (at +{be_check['current_r']:.2f}R)"
            )

            return {
                'trade_id': str(trade_id),
                'adjusted': True,
                'old_stop_loss': stop_loss,
                'new_stop_loss': new_stop_loss,
                'current_r': be_check['current_r'],
                'current_price': current_price,
                'reason': be_check['reason']
            }

        except Exception as e:
            logger.error(f"Error adjusting stop loss for trade {trade_id}: {e}", exc_info=True)
            return None


    def validate_new_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-trade risk check before executing new trade

        Validates:
        1. Position size meets 1% risk rule
        2. Portfolio risk won't exceed limits
        3. Daily loss limit not reached
        4. Leverage is acceptable
        5. Symbol concentration acceptable

        Args:
            trade_data: Dict with trade details:
                {
                    'user_id': UUID,
                    'symbol_id': UUID,
                    'side': 'long' | 'short',
                    'entry_price': float,
                    'stop_loss': float,
                    'position_size': float
                }

        Returns:
            Dict with validation result:
            {
                'is_valid': bool,
                'risk_amount': float,
                'risk_percentage': float,
                'warnings': List[str],
                'errors': List[str]
            }
        """
        logger.info("Validating new trade")

        try:
            # Import risk calculator
            import sys
            import os
            api_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api/src'))
            sys.path.insert(0, api_src_path)
            from core.risk_calculator import RiskCalculator

            errors = []
            warnings = []

            # Extract trade data
            user_id = trade_data.get('user_id')
            symbol_id = trade_data.get('symbol_id')
            entry_price = float(trade_data.get('entry_price', 0))
            stop_loss = float(trade_data.get('stop_loss', 0))
            position_size = float(trade_data.get('position_size', 0))

            # Step 1 - Get account balance
            user_result = self.supabase.table('profiles')\
                .select('metadata')\
                .eq('id', user_id)\
                .single()\
                .execute()

            account_balance = 10000.0  # Default
            if user_result.data and user_result.data.get('metadata'):
                account_balance = float(user_result.data['metadata'].get('account_balance', 10000.0))

            # Step 2 - Validate position size
            risk_calc = RiskCalculator(account_balance=account_balance, risk_per_trade=0.01)
            validation = risk_calc.validate_trade_risk(
                entry=entry_price,
                stop_loss=stop_loss,
                position_size=position_size,
                account_balance=account_balance
            )

            if not validation['is_valid']:
                errors.extend(validation['warnings'])
            else:
                warnings.extend(validation['warnings'])

            # Step 3 - Check daily loss limit
            daily_check = self.check_daily_loss_limit()
            if daily_check.get('limit_reached'):
                errors.append("Cannot trade: 3-loss daily limit reached")
            elif daily_check.get('losses_today', 0) >= 2:
                warnings.append("Warning: 2 losses today - approach with caution")

            # Step 4 - Check portfolio risk
            portfolio = self.check_portfolio_risk()

            # Simulate adding this trade's risk
            new_total_risk = portfolio['total_risk_percentage'] + validation['risk_percentage']
            if new_total_risk > 5.0:
                errors.append(
                    f"Trade would exceed portfolio risk limit: "
                    f"{new_total_risk:.2f}% > 5.0%"
                )

            # Step 5 - Check symbol concentration
            result = self.supabase.table('trades')\
                .select('id')\
                .eq('symbol_id', str(symbol_id))\
                .eq('status', 'active')\
                .execute()

            active_trades_for_symbol = len(result.data) if result.data else 0
            if active_trades_for_symbol >= 3:
                errors.append(
                    f"Symbol already has {active_trades_for_symbol} active trades (max: 3)"
                )
            elif active_trades_for_symbol >= 2:
                warnings.append(
                    f"Symbol already has {active_trades_for_symbol} active trades"
                )

            is_valid = len(errors) == 0

            result = {
                'is_valid': is_valid,
                'risk_amount': validation['risk_amount'],
                'risk_percentage': validation['risk_percentage'],
                'portfolio_risk_after': new_total_risk,
                'warnings': warnings,
                'errors': errors
            }

            if is_valid:
                logger.info(f"Trade validation passed: {validation['risk_percentage']:.2f}% risk")
            else:
                logger.warning(f"Trade validation failed: {errors}")

            return result

        except Exception as e:
            logger.error(f"Error validating new trade: {e}", exc_info=True)
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }


    def run(self) -> Dict[str, Any]:
        """
        Main execution method - Called by Celery scheduler every 60 seconds

        Process:
        1. Check portfolio-wide risk metrics
        2. Check daily loss limit
        3. Validate position sizes for all active trades
        4. Adjust stop losses to break-even where applicable
        5. Generate risk alerts for any violations
        6. Return summary of risk checks

        Returns:
            Dict with execution summary:
            {
                'execution_time': datetime,
                'portfolio_risk': Dict,
                'daily_loss_check': Dict,
                'position_violations': List[Dict],
                'stop_loss_adjustments': List[Dict],
                'risk_alerts_generated': int
            }
        """
        execution_start = datetime.now(timezone.utc)
        logger.info(f"RiskManager execution started at {execution_start}")

        # Step 1 - Check portfolio risk
        portfolio_risk = self.check_portfolio_risk()

        # Step 2 - Check daily loss limit
        daily_loss_check = self.check_daily_loss_limit()

        # Step 3 - Check position sizes for all symbols with active trades
        try:
            result = self.supabase.table('market_symbols')\
                .select('id, symbol')\
                .eq('active', True)\
                .execute()

            active_symbols = result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching active symbols: {e}")
            active_symbols = []

        position_violations = []
        for symbol in active_symbols:
            symbol_id = UUID(symbol['id'])
            symbol_name = symbol['symbol']

            position_check = self.check_position_sizes(
                symbol_id=symbol_id,
                symbol_name=symbol_name
            )

            if position_check and position_check.get('violations'):
                position_violations.extend(position_check['violations'])

        # Step 4 - Adjust stop losses for active trades
        try:
            result = self.supabase.table('trades')\
                .select('id')\
                .eq('status', 'active')\
                .execute()

            active_trades = result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching active trades: {e}")
            active_trades = []

        stop_loss_adjustments = []
        for trade in active_trades:
            trade_id = UUID(trade['id'])

            adjustment = self.adjust_stop_loss(trade_id)
            if adjustment and adjustment.get('adjusted'):
                stop_loss_adjustments.append(adjustment)

        # Step 5 - Generate risk alerts for violations
        risk_alerts_generated = 0

        # Alert for portfolio risk warnings
        if portfolio_risk.get('warnings'):
            for warning in portfolio_risk['warnings']:
                try:
                    self.supabase.table('alerts').insert({
                        'user_id': None,  # Global alert
                        'symbol_id': None,
                        'kind': 'risk_warning',
                        'context': {
                            'type': 'portfolio_risk',
                            'message': warning,
                            'portfolio_metrics': portfolio_risk
                        },
                        'sent': False
                    }).execute()
                    risk_alerts_generated += 1
                except Exception as e:
                    logger.error(f"Error creating portfolio risk alert: {e}")

        # Alert for daily loss limit
        if daily_loss_check.get('limit_reached'):
            try:
                self.supabase.table('alerts').insert({
                    'user_id': None,
                    'symbol_id': None,
                    'kind': 'risk_warning',
                    'context': {
                        'type': 'daily_loss_limit',
                        'message': 'STOP TRADING: 3-loss daily limit reached',
                        'daily_metrics': daily_loss_check
                    },
                    'sent': False
                }).execute()
                risk_alerts_generated += 1
            except Exception as e:
                logger.error(f"Error creating daily loss alert: {e}")

        # Alert for position violations
        for violation in position_violations:
            try:
                self.supabase.table('alerts').insert({
                    'user_id': None,
                    'symbol_id': None,
                    'kind': 'risk_warning',
                    'context': {
                        'type': 'position_size_violation',
                        'trade_id': violation['trade_id'],
                        'symbol': violation['symbol'],
                        'warnings': violation['warnings']
                    },
                    'sent': False
                }).execute()
                risk_alerts_generated += 1
            except Exception as e:
                logger.error(f"Error creating position violation alert: {e}")

        # Step 6 - Build execution summary
        execution_end = datetime.now(timezone.utc)
        duration_ms = int((execution_end - execution_start).total_seconds() * 1000)

        summary = {
            'execution_time': execution_start.isoformat(),
            'execution_duration_ms': duration_ms,
            'portfolio_risk': portfolio_risk,
            'daily_loss_check': daily_loss_check,
            'position_violations_count': len(position_violations),
            'position_violations': position_violations,
            'stop_loss_adjustments_count': len(stop_loss_adjustments),
            'stop_loss_adjustments': stop_loss_adjustments,
            'risk_alerts_generated': risk_alerts_generated
        }

        logger.info(
            f"RiskManager execution completed: "
            f"{risk_alerts_generated} alerts, "
            f"{len(stop_loss_adjustments)} SL adjustments, "
            f"{len(position_violations)} violations"
        )

        return summary


# Example usage (for testing)
if __name__ == "__main__":
    # This would be called from Celery task
    import sys
    sys.path.insert(0, '/mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/api/src')

    from config.supabase import get_supabase_admin

    # Initialize agent with admin client (bypasses RLS)
    risk_manager = RiskManager(supabase_client=get_supabase_admin())

    # Run analysis
    result = risk_manager.run()

    print("RiskManager Results:")
    print(result)
