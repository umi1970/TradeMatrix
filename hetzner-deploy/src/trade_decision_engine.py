"""
TradeMatrix.ai - TradeDecisionEngine
Combines validation, risk context, and event data to make final trade decisions.

Execution: Called by ValidationAndRisk flow after all checks complete
Decision Types:
  - EXECUTE: All checks passed, trade can proceed
  - REJECT: Validation failed, do not trade
  - WAIT: High-impact news ahead, postpone trade
  - HALT: Daily loss limit reached, stop trading
  - REDUCE: Risk limits reached, reduce position size

Data sources:
  - TradeValidationEngine (validation_result)
  - RiskContextEvaluator (risk_context)
  - EventWatcher (high_risk flag)
  - trade_decisions table (decision history)

Output: Final decision to trade_decisions table
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal

from supabase import Client

# Setup logger
logger = logging.getLogger(__name__)


class TradeDecisionEngine:
    """
    TradeDecisionEngine - Combines validation + risk context + events to decide

    Responsibilities:
    - Evaluate validation result (APPROVED/REJECTED)
    - Check risk context mode (NORMAL/STOP_TRADING/LIMITED_MODE)
    - Check high-risk event flag (news events)
    - Make final decision (EXECUTE/REJECT/WAIT/HALT/REDUCE)
    - Save decision to database with reasoning
    - Query decision history for analysis
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize TradeDecisionEngine

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
        """
        self.supabase = supabase_client
        logger.info("TradeDecisionEngine initialized")


    def decide(
        self,
        validation_result: Dict[str, Any],
        risk_context: Dict[str, Any],
        high_risk: bool,
        trade_proposal: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make final trading decision based on all inputs

        Decision Logic:
        1. If validation REJECTED → REJECT
        2. If high_risk event → WAIT
        3. If risk_mode == STOP_TRADING → HALT
        4. If risk_mode == LIMITED_MODE → REDUCE
        5. Otherwise → EXECUTE

        Args:
            validation_result: Dict from TradeValidationEngine
                {
                    'status': 'APPROVED' | 'REJECTED',
                    'bias_score': float,
                    'rr': float,
                    'timestamp': str,
                    'warnings': List[str]
                }
            risk_context: Dict from RiskContextEvaluator
                {
                    'mode': 'NORMAL' | 'STOP_TRADING' | 'LIMITED_MODE',
                    'balance': float,
                    'equity': float,
                    'open_trades': int,
                    'daily_pnl_pct': float,
                    'allowed': bool
                }
            high_risk: Boolean from EventWatcher (True if high-impact news ahead)
            trade_proposal: Optional dict with trade details (for logging)

        Returns:
            Dict with final decision:
            {
                'decision': 'EXECUTE' | 'REJECT' | 'WAIT' | 'HALT' | 'REDUCE',
                'reason': str,
                'bias_score': float,
                'rr': float,
                'risk_context': dict,
                'timestamp': str,
                'trade_proposal': dict
            }
        """
        logger.info("Making trade decision...")

        approved = validation_result.get("status") == "APPROVED"
        risk_mode = risk_context.get("mode", "NORMAL")

        final_decision = "REJECT"
        reason = ""

        # Decision tree
        if not approved:
            final_decision = "REJECT"
            reason = f"Validation failed: {', '.join(validation_result.get('warnings', []))}"
            logger.warning(f"Decision: REJECT - {reason}")

        elif high_risk:
            final_decision = "WAIT"
            reason = "High-impact news event detected - postponing trade"
            logger.warning(f"Decision: WAIT - {reason}")

        elif risk_mode == "STOP_TRADING":
            final_decision = "HALT"
            reason = "Daily loss limit reached or excessive drawdown - stop trading"
            logger.warning(f"Decision: HALT - {reason}")

        elif risk_mode == "LIMITED_MODE":
            final_decision = "REDUCE"
            reason = "Maximum open trades reached - reduce position size or wait"
            logger.warning(f"Decision: REDUCE - {reason}")

        else:
            final_decision = "EXECUTE"
            reason = "All validation and risk checks passed"
            logger.info(f"Decision: EXECUTE - {reason}")

        # Build decision payload
        decision = {
            "decision": final_decision,
            "reason": reason,
            "bias_score": validation_result.get("bias_score"),
            "rr": validation_result.get("rr"),
            "risk_context": risk_context,
            "validation_warnings": validation_result.get("warnings", []),
            "high_risk_event": high_risk,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trade_proposal": trade_proposal or {}
        }

        logger.info(
            f"Final decision: {final_decision} | "
            f"Bias: {decision['bias_score']} | "
            f"RR: {decision['rr']} | "
            f"Risk Mode: {risk_mode}"
        )

        return decision


    def save_decision(
        self,
        decision: Dict[str, Any],
        trade_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        symbol_id: Optional[UUID] = None
    ) -> Optional[UUID]:
        """
        Save decision to trade_decisions table for audit trail

        Args:
            decision: Decision dict from decide()
            trade_id: Optional UUID of related trade
            user_id: Optional UUID of user
            symbol_id: Optional UUID of symbol

        Returns:
            UUID of created decision record or None on error
        """
        logger.info(f"Saving decision: {decision['decision']}")

        try:
            # Prepare record
            record = {
                'trade_id': str(trade_id) if trade_id else None,
                'user_id': str(user_id) if user_id else None,
                'symbol_id': str(symbol_id) if symbol_id else None,
                'decision': decision['decision'],
                'reason': decision['reason'],
                'bias_score': float(decision.get('bias_score', 0)) if decision.get('bias_score') else None,
                'rr_ratio': float(decision.get('rr', 0)) if decision.get('rr') else None,
                'context': {
                    'risk_context': decision.get('risk_context', {}),
                    'validation_warnings': decision.get('validation_warnings', []),
                    'high_risk_event': decision.get('high_risk_event', False),
                    'trade_proposal': decision.get('trade_proposal', {})
                },
                'created_at': decision['timestamp']
            }

            # Insert into database
            result = self.supabase.table('trade_decisions').insert(record).execute()

            if result.data and len(result.data) > 0:
                decision_id = result.data[0]['id']
                logger.info(f"Decision saved: {decision_id}")
                return UUID(decision_id)
            else:
                logger.error("Failed to save decision")
                return None

        except Exception as e:
            logger.error(f"Error saving decision: {e}", exc_info=True)
            return None


    def get_decision_history(
        self,
        user_id: Optional[UUID] = None,
        symbol_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query past decisions for analysis

        Args:
            user_id: Optional filter by user
            symbol_id: Optional filter by symbol
            limit: Max number of decisions to return (default: 10)

        Returns:
            List of decision records with metadata
        """
        logger.info(f"Fetching decision history (limit: {limit})")

        try:
            # Build query
            query = self.supabase.table('trade_decisions')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(limit)

            # Apply filters
            if user_id:
                query = query.eq('user_id', str(user_id))
            if symbol_id:
                query = query.eq('symbol_id', str(symbol_id))

            result = query.execute()

            decisions = result.data if result.data else []
            logger.info(f"Fetched {len(decisions)} decisions")

            return decisions

        except Exception as e:
            logger.error(f"Error fetching decision history: {e}", exc_info=True)
            return []


    def get_decision_stats(
        self,
        user_id: Optional[UUID] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate decision statistics for analysis

        Args:
            user_id: Optional filter by user
            days: Number of days to analyze (default: 7)

        Returns:
            Dict with decision statistics:
            {
                'total_decisions': int,
                'execute_count': int,
                'reject_count': int,
                'wait_count': int,
                'halt_count': int,
                'reduce_count': int,
                'execute_rate': float,
                'avg_bias_score': float,
                'avg_rr_ratio': float
            }
        """
        logger.info(f"Calculating decision stats (last {days} days)")

        try:
            # Calculate cutoff date
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            # Build query
            query = self.supabase.table('trade_decisions')\
                .select('decision, bias_score, rr_ratio')\
                .gte('created_at', cutoff.isoformat())

            if user_id:
                query = query.eq('user_id', str(user_id))

            result = query.execute()
            decisions = result.data if result.data else []

            if not decisions:
                return {
                    'total_decisions': 0,
                    'execute_count': 0,
                    'reject_count': 0,
                    'wait_count': 0,
                    'halt_count': 0,
                    'reduce_count': 0,
                    'execute_rate': 0.0,
                    'avg_bias_score': 0.0,
                    'avg_rr_ratio': 0.0
                }

            # Count decisions by type
            execute_count = sum(1 for d in decisions if d['decision'] == 'EXECUTE')
            reject_count = sum(1 for d in decisions if d['decision'] == 'REJECT')
            wait_count = sum(1 for d in decisions if d['decision'] == 'WAIT')
            halt_count = sum(1 for d in decisions if d['decision'] == 'HALT')
            reduce_count = sum(1 for d in decisions if d['decision'] == 'REDUCE')

            # Calculate averages
            bias_scores = [float(d['bias_score']) for d in decisions if d.get('bias_score')]
            rr_ratios = [float(d['rr_ratio']) for d in decisions if d.get('rr_ratio')]

            avg_bias = sum(bias_scores) / len(bias_scores) if bias_scores else 0.0
            avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0.0

            stats = {
                'total_decisions': len(decisions),
                'execute_count': execute_count,
                'reject_count': reject_count,
                'wait_count': wait_count,
                'halt_count': halt_count,
                'reduce_count': reduce_count,
                'execute_rate': (execute_count / len(decisions) * 100) if decisions else 0.0,
                'avg_bias_score': round(avg_bias, 2),
                'avg_rr_ratio': round(avg_rr, 2),
                'days_analyzed': days
            }

            logger.info(
                f"Decision stats: {stats['execute_rate']:.1f}% execute rate, "
                f"{stats['total_decisions']} total decisions"
            )

            return stats

        except Exception as e:
            logger.error(f"Error calculating decision stats: {e}", exc_info=True)
            return {
                'error': str(e),
                'total_decisions': 0
            }


# Example usage (for testing)
if __name__ == "__main__":
    import json

    # Test data
    validation_result = {
        "status": "APPROVED",
        "bias_score": 0.83,
        "rr": 2.1,
        "timestamp": "2025-11-05T10:00:00",
        "warnings": []
    }

    risk_context = {
        "mode": "NORMAL",
        "balance": 10000.0,
        "equity": 10200.0,
        "open_trades": 2,
        "daily_pnl_pct": 1.5,
        "allowed": True
    }

    high_risk = False

    # Test decision
    engine = TradeDecisionEngine(supabase_client=None)  # Mock for testing
    decision = engine.decide(validation_result, risk_context, high_risk)

    print("Trade Decision:")
    print(json.dumps(decision, indent=2))
