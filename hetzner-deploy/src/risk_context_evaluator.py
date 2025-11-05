"""
TradeMatrix.ai - RiskContextEvaluator
Evaluates account state and determines risk mode for trading decisions.

Execution: Called by ValidationAndRisk flow before trade decision
Risk Modes:
  - NORMAL: All systems go, trade freely
  - STOP_TRADING: Daily loss limit hit, halt all trading
  - LIMITED_MODE: Max trades reached, reduce exposure

Risk Rules:
  - Max daily loss: 3% of account balance
  - Max open trades: 5 concurrent positions
  - Max drawdown check: Daily P&L percentage

Data sources:
  - profiles.metadata (account balance)
  - trades table (active trades, daily P&L)
  - user_settings table (risk preferences)

Output: Risk context dict for TradeDecisionEngine
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from supabase import Client

# Setup logger
logger = logging.getLogger(__name__)


class RiskContextEvaluator:
    """
    RiskContextEvaluator - Checks account exposure and enforces risk limits

    Responsibilities:
    - Fetch account state (balance, equity, open trades)
    - Calculate daily P&L percentage
    - Check against max daily loss limit (3%)
    - Check against max open trades limit (5)
    - Determine risk mode (NORMAL/STOP_TRADING/LIMITED_MODE)
    - Return context for decision engine
    """

    def __init__(
        self,
        supabase_client: Client,
        max_daily_loss_pct: float = 3.0,
        max_open_trades: int = 5
    ):
        """
        Initialize RiskContextEvaluator

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
            max_daily_loss_pct: Maximum daily loss as percentage of balance (default: 3.0%)
            max_open_trades: Maximum concurrent open trades (default: 5)
        """
        self.supabase = supabase_client
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_open_trades = max_open_trades
        logger.info(
            f"RiskContextEvaluator initialized "
            f"(max_daily_loss: {max_daily_loss_pct}%, max_trades: {max_open_trades})"
        )


    def fetch_account_state(self, user_id: UUID) -> Dict[str, Any]:
        """
        Fetch account state from database

        Args:
            user_id: User UUID

        Returns:
            Dict with account state:
            {
                'balance': float,
                'equity': float,
                'open_trades': int,
                'daily_pnl_pct': float
            }
        """
        logger.info(f"Fetching account state for user {user_id}")

        try:
            # Step 1 - Get account balance from profiles.metadata
            user_result = self.supabase.table('profiles')\
                .select('metadata')\
                .eq('id', str(user_id))\
                .single()\
                .execute()

            balance = 10000.0  # Default fallback
            if user_result.data and user_result.data.get('metadata'):
                balance = float(user_result.data['metadata'].get('account_balance', 10000.0))

            # Step 2 - Count open trades
            trades_result = self.supabase.table('trades')\
                .select('id, entry_price, position_size')\
                .eq('user_id', str(user_id))\
                .eq('status', 'active')\
                .execute()

            open_trades = trades_result.data if trades_result.data else []
            open_trades_count = len(open_trades)

            # Step 3 - Calculate equity (balance + unrealized P&L)
            # For now, we'll use balance as equity (simplified)
            # In production, you'd fetch current prices and calculate unrealized P&L
            equity = balance

            # Step 4 - Get daily P&L
            daily_pnl_pct = self.get_daily_pnl(user_id, balance)

            account_state = {
                'balance': balance,
                'equity': equity,
                'open_trades': open_trades_count,
                'daily_pnl_pct': daily_pnl_pct
            }

            logger.info(
                f"Account state: Balance={balance:.2f}, "
                f"Equity={equity:.2f}, "
                f"Open Trades={open_trades_count}, "
                f"Daily P&L={daily_pnl_pct:.2f}%"
            )

            return account_state

        except Exception as e:
            logger.error(f"Error fetching account state: {e}", exc_info=True)
            # Return safe defaults
            return {
                'balance': 10000.0,
                'equity': 10000.0,
                'open_trades': 0,
                'daily_pnl_pct': 0.0
            }


    def get_daily_pnl(self, user_id: UUID, balance: float) -> float:
        """
        Calculate daily P&L percentage

        Args:
            user_id: User UUID
            balance: Account balance

        Returns:
            Daily P&L as percentage of balance
        """
        logger.info(f"Calculating daily P&L for user {user_id}")

        try:
            # Get today's date range
            today = datetime.now(timezone.utc).date()
            start_of_day = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)

            # Fetch today's closed trades
            result = self.supabase.table('trades')\
                .select('pnl')\
                .eq('user_id', str(user_id))\
                .eq('status', 'closed')\
                .gte('closed_at', start_of_day.isoformat())\
                .execute()

            trades = result.data if result.data else []

            if not trades:
                logger.debug("No closed trades today")
                return 0.0

            # Sum P&L
            total_pnl = sum(Decimal(str(t.get('pnl', 0))) for t in trades)

            # Calculate percentage
            daily_pnl_pct = float((total_pnl / Decimal(str(balance))) * 100)

            logger.info(f"Daily P&L: {float(total_pnl):.2f} ({daily_pnl_pct:.2f}%)")

            return round(daily_pnl_pct, 2)

        except Exception as e:
            logger.error(f"Error calculating daily P&L: {e}", exc_info=True)
            return 0.0


    def evaluate(
        self,
        account_state: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Evaluate risk context and determine risk mode

        Args:
            account_state: Optional pre-fetched account state dict
                          If None, will fetch using user_id
            user_id: User UUID (required if account_state is None)

        Returns:
            Dict with risk context:
            {
                'balance': float,
                'equity': float,
                'open_trades': int,
                'daily_pnl_pct': float,
                'mode': 'NORMAL' | 'STOP_TRADING' | 'LIMITED_MODE',
                'allowed': bool,
                'warnings': List[str]
            }
        """
        logger.info("Evaluating risk context...")

        # Fetch account state if not provided
        if not account_state:
            if not user_id:
                logger.error("Either account_state or user_id must be provided")
                return {
                    'mode': 'STOP_TRADING',
                    'allowed': False,
                    'warnings': ['Missing account state or user_id']
                }

            account_state = self.fetch_account_state(user_id)

        # Extract values
        balance = account_state.get("balance", 10000.0)
        equity = account_state.get("equity", balance)
        open_trades = account_state.get("open_trades", 0)
        daily_pnl_pct = account_state.get("daily_pnl_pct", 0.0)

        # Check limits
        exposure_ok = open_trades < self.max_open_trades
        drawdown_ok = daily_pnl_pct > -self.max_daily_loss_pct

        # Determine risk mode
        mode = "NORMAL"
        warnings = []

        if not drawdown_ok:
            mode = "STOP_TRADING"
            warnings.append(
                f"Daily loss limit reached: {daily_pnl_pct:.2f}% "
                f"(max: -{self.max_daily_loss_pct}%)"
            )
            logger.warning(f"Risk Mode: STOP_TRADING - {warnings[-1]}")

        elif not exposure_ok:
            mode = "LIMITED_MODE"
            warnings.append(
                f"Max open trades reached: {open_trades}/{self.max_open_trades}"
            )
            logger.warning(f"Risk Mode: LIMITED_MODE - {warnings[-1]}")

        # Additional warnings (not blocking)
        if daily_pnl_pct < -2.0:  # Warning at 2% loss
            warnings.append(
                f"Approaching daily loss limit: {daily_pnl_pct:.2f}%"
            )

        if open_trades >= self.max_open_trades - 1:  # Warning at max-1
            warnings.append(
                f"Near max open trades: {open_trades}/{self.max_open_trades}"
            )

        # Build context
        context = {
            "balance": balance,
            "equity": equity,
            "open_trades": open_trades,
            "daily_pnl_pct": daily_pnl_pct,
            "mode": mode,
            "allowed": drawdown_ok and exposure_ok,
            "warnings": warnings,
            "limits": {
                "max_daily_loss_pct": self.max_daily_loss_pct,
                "max_open_trades": self.max_open_trades
            }
        }

        logger.info(
            f"Risk context evaluated: Mode={mode}, "
            f"Allowed={context['allowed']}, "
            f"Open Trades={open_trades}, "
            f"Daily P&L={daily_pnl_pct:.2f}%"
        )

        return context


    def get_risk_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive risk summary for dashboard

        Args:
            user_id: User UUID

        Returns:
            Dict with risk summary including history and trends
        """
        logger.info(f"Generating risk summary for user {user_id}")

        try:
            # Get current risk context
            current_context = self.evaluate(user_id=user_id)

            # Get last 7 days of P&L
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)

            result = self.supabase.table('trades')\
                .select('closed_at, pnl')\
                .eq('user_id', str(user_id))\
                .eq('status', 'closed')\
                .gte('closed_at', cutoff.isoformat())\
                .order('closed_at', desc=False)\
                .execute()

            trades = result.data if result.data else []

            # Calculate daily P&L trend
            daily_pnl = {}
            for trade in trades:
                closed_date = datetime.fromisoformat(
                    trade['closed_at'].replace('Z', '+00:00')
                ).date()
                date_str = closed_date.isoformat()

                if date_str not in daily_pnl:
                    daily_pnl[date_str] = 0.0

                daily_pnl[date_str] += float(trade.get('pnl', 0))

            # Calculate stats
            pnl_values = list(daily_pnl.values())
            avg_daily_pnl = sum(pnl_values) / len(pnl_values) if pnl_values else 0.0
            max_daily_loss = min(pnl_values) if pnl_values else 0.0

            balance = current_context['balance']
            max_daily_loss_pct = (max_daily_loss / balance * 100) if balance > 0 else 0.0

            risk_summary = {
                'current_context': current_context,
                'last_7_days': {
                    'avg_daily_pnl': round(avg_daily_pnl, 2),
                    'max_daily_loss': round(max_daily_loss, 2),
                    'max_daily_loss_pct': round(max_daily_loss_pct, 2),
                    'daily_pnl_trend': daily_pnl,
                    'total_trades': len(trades)
                },
                'risk_capacity': {
                    'remaining_open_slots': self.max_open_trades - current_context['open_trades'],
                    'remaining_daily_loss': round(
                        self.max_daily_loss_pct + current_context['daily_pnl_pct'], 2
                    )
                }
            }

            logger.info("Risk summary generated successfully")
            return risk_summary

        except Exception as e:
            logger.error(f"Error generating risk summary: {e}", exc_info=True)
            return {
                'error': str(e),
                'current_context': self.evaluate(user_id=user_id)
            }


# Example usage (for testing)
if __name__ == "__main__":
    import json

    # Test with mock account state
    test_account_state = {
        "balance": 10000.0,
        "equity": 9700.0,
        "open_trades": 2,
        "daily_pnl_pct": -2.1
    }

    evaluator = RiskContextEvaluator(
        supabase_client=None,  # Mock for testing
        max_daily_loss_pct=3.0,
        max_open_trades=5
    )

    context = evaluator.evaluate(account_state=test_account_state)

    print("Risk Context:")
    print(json.dumps(context, indent=2))
