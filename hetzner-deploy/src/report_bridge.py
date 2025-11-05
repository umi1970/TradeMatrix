"""
TradeMatrix.ai - ReportBridge
Forwards final trade decisions to JournalBot and Publisher for reporting.

Execution: Called at the end of ValidationAndRisk flow
Responsibilities:
  - Create journal entry in database for audit trail
  - Queue decision for daily report generation
  - Forward to Publisher for blog/subdomain (future)
  - Track decision statistics

Data sources:
  - Final decision from TradeDecisionEngine
  - Trade proposal data

Output:
  - journal_entries table (audit trail)
  - report_queue table (for JournalBot)
  - Publisher queue (future)
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from supabase import Client

# Setup logger
logger = logging.getLogger(__name__)


class ReportBridge:
    """
    ReportBridge - Forwards decisions to JournalBot and Publisher

    Responsibilities:
    - Create journal entries for all trade decisions
    - Queue decisions for report generation
    - Forward to Publisher (future: subdomain/blog)
    - Track decision statistics for analysis
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize ReportBridge

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
        """
        self.supabase = supabase_client
        logger.info("ReportBridge initialized")


    def forward_to_journal(
        self,
        final_decision: Dict[str, Any],
        trade_data: Optional[Dict[str, Any]] = None
    ) -> Optional[UUID]:
        """
        Create journal entry for the decision

        Journal entries provide an audit trail of all trading decisions,
        including rejected trades (for analysis of false signals).

        Args:
            final_decision: Dict from TradeDecisionEngine.decide()
            trade_data: Optional trade proposal data

        Returns:
            UUID of created journal entry or None on error
        """
        logger.info(f"Creating journal entry for decision: {final_decision['decision']}")

        try:
            entry = self.create_journal_entry(final_decision, trade_data)

            if entry:
                logger.info(f"Journal entry created: {entry}")
                return entry
            else:
                logger.error("Failed to create journal entry")
                return None

        except Exception as e:
            logger.error(f"Error forwarding to journal: {e}", exc_info=True)
            return None


    def forward_to_publisher(
        self,
        final_decision: Dict[str, Any],
        trade_data: Optional[Dict[str, Any]] = None
    ) -> Optional[UUID]:
        """
        Queue decision for report generation and publishing

        Adds decision to report_queue for processing by JournalBot.
        Future: Also forwards to Publisher for subdomain/blog.

        Args:
            final_decision: Dict from TradeDecisionEngine.decide()
            trade_data: Optional trade proposal data

        Returns:
            UUID of created queue entry or None on error
        """
        logger.info(f"Queuing decision for report: {final_decision['decision']}")

        try:
            queue_id = self.queue_for_report(final_decision, trade_data)

            if queue_id:
                logger.info(f"Decision queued for report: {queue_id}")
                return queue_id
            else:
                logger.warning("Failed to queue decision for report")
                return None

        except Exception as e:
            logger.error(f"Error forwarding to publisher: {e}", exc_info=True)
            return None


    def create_journal_entry(
        self,
        decision: Dict[str, Any],
        trade_data: Optional[Dict[str, Any]] = None
    ) -> Optional[UUID]:
        """
        Insert journal entry into database

        Journal entries track all decisions (EXECUTE, REJECT, WAIT, etc.)
        for later analysis and reporting.

        Args:
            decision: Final decision dict
            trade_data: Optional trade proposal

        Returns:
            UUID of journal entry or None on error
        """
        logger.info("Creating journal entry in database...")

        try:
            # Extract IDs from trade_data if available
            user_id = None
            symbol_id = None
            trade_id = None

            if trade_data:
                user_id = trade_data.get('user_id')
                symbol_id = trade_data.get('symbol_id')
                trade_id = trade_data.get('trade_id')

            # Build entry payload
            entry_record = {
                'user_id': str(user_id) if user_id else None,
                'symbol_id': str(symbol_id) if symbol_id else None,
                'trade_id': str(trade_id) if trade_id else None,
                'entry_type': 'decision',  # Type of journal entry
                'decision': decision['decision'],
                'content': decision['reason'],  # Main text content
                'context': {
                    'bias_score': decision.get('bias_score'),
                    'rr': decision.get('rr'),
                    'risk_context': decision.get('risk_context', {}),
                    'validation_warnings': decision.get('validation_warnings', []),
                    'high_risk_event': decision.get('high_risk_event', False),
                    'trade_proposal': decision.get('trade_proposal', {})
                },
                'metadata': {
                    'timestamp': decision['timestamp'],
                    'source': 'ValidationAndRisk Flow',
                    'version': '1.0'
                },
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            # Insert into journal_entries table
            result = self.supabase.table('journal_entries').insert(entry_record).execute()

            if result.data and len(result.data) > 0:
                entry_id = result.data[0]['id']
                logger.info(f"Journal entry saved: {entry_id}")
                return UUID(entry_id)
            else:
                logger.error("Failed to insert journal entry")
                return None

        except Exception as e:
            logger.error(f"Error creating journal entry: {e}", exc_info=True)
            return None


    def queue_for_report(
        self,
        decision: Dict[str, Any],
        trade_data: Optional[Dict[str, Any]] = None
    ) -> Optional[UUID]:
        """
        Add decision to report queue for JournalBot

        Report queue is processed by JournalBot during daily report generation.
        Decisions with status EXECUTE are prioritized.

        Args:
            decision: Final decision dict
            trade_data: Optional trade proposal

        Returns:
            UUID of queue entry or None on error
        """
        logger.info("Queuing decision for report generation...")

        try:
            # Extract metadata
            user_id = None
            symbol_id = None

            if trade_data:
                user_id = trade_data.get('user_id')
                symbol_id = trade_data.get('symbol_id')

            # Determine priority (EXECUTE decisions have higher priority)
            priority = 1 if decision['decision'] == 'EXECUTE' else 2

            # Build publish packet
            publish_packet = {
                'title': f"Trade Decision: {decision['decision']}",
                'content': {
                    'decision': decision['decision'],
                    'reason': decision['reason'],
                    'bias_score': decision.get('bias_score'),
                    'rr': decision.get('rr'),
                    'risk_mode': decision.get('risk_context', {}).get('mode'),
                    'timestamp': decision['timestamp']
                },
                'tags': [
                    'validation',
                    'risk',
                    'decision',
                    decision['decision'].lower()
                ],
                'metadata': {
                    'source': 'ReportBridge',
                    'flow': 'ValidationAndRisk',
                    'trade_data': trade_data or {}
                }
            }

            # Insert into report_queue table
            queue_record = {
                'user_id': str(user_id) if user_id else None,
                'symbol_id': str(symbol_id) if symbol_id else None,
                'queue_type': 'decision',
                'priority': priority,
                'payload': publish_packet,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat()
            }

            result = self.supabase.table('report_queue').insert(queue_record).execute()

            if result.data and len(result.data) > 0:
                queue_id = result.data[0]['id']
                logger.info(f"Decision queued: {queue_id} (priority: {priority})")
                return UUID(queue_id)
            else:
                logger.error("Failed to insert into report queue")
                return None

        except Exception as e:
            logger.error(f"Error queuing for report: {e}", exc_info=True)
            return None


    def process(
        self,
        final_decision: Dict[str, Any],
        trade_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main processing method - forwards decision to both journal and publisher

        This is the primary method called by ValidationAndRisk flow.

        Args:
            final_decision: Dict from TradeDecisionEngine.decide()
            trade_data: Optional trade proposal data

        Returns:
            Dict with results:
            {
                'journal_entry_id': UUID or None,
                'publish_queue_id': UUID or None,
                'success': bool,
                'timestamp': str
            }
        """
        logger.info("Processing decision through ReportBridge...")

        try:
            # Forward to journal
            journal_id = self.forward_to_journal(final_decision, trade_data)

            # Forward to publisher
            publish_id = self.forward_to_publisher(final_decision, trade_data)

            result = {
                'journal_entry_id': str(journal_id) if journal_id else None,
                'publish_queue_id': str(publish_id) if publish_id else None,
                'success': journal_id is not None or publish_id is not None,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'decision': final_decision['decision']
            }

            if result['success']:
                logger.info(
                    f"✅ Decision processed successfully: "
                    f"Journal={result['journal_entry_id']}, "
                    f"Queue={result['publish_queue_id']}"
                )
            else:
                logger.warning("⚠️ Decision processing failed or incomplete")

            return result

        except Exception as e:
            logger.error(f"Error processing decision: {e}", exc_info=True)
            return {
                'journal_entry_id': None,
                'publish_queue_id': None,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }


    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get report queue statistics for monitoring

        Returns:
            Dict with queue statistics:
            {
                'pending_count': int,
                'processing_count': int,
                'completed_count': int,
                'failed_count': int,
                'oldest_pending': datetime or None
            }
        """
        logger.info("Fetching report queue statistics...")

        try:
            # Count by status
            result = self.supabase.table('report_queue')\
                .select('status, created_at')\
                .execute()

            entries = result.data if result.data else []

            if not entries:
                return {
                    'pending_count': 0,
                    'processing_count': 0,
                    'completed_count': 0,
                    'failed_count': 0,
                    'oldest_pending': None
                }

            # Count statuses
            pending = [e for e in entries if e['status'] == 'pending']
            processing = [e for e in entries if e['status'] == 'processing']
            completed = [e for e in entries if e['status'] == 'completed']
            failed = [e for e in entries if e['status'] == 'failed']

            # Find oldest pending
            oldest_pending = None
            if pending:
                oldest = min(pending, key=lambda x: x['created_at'])
                oldest_pending = oldest['created_at']

            stats = {
                'pending_count': len(pending),
                'processing_count': len(processing),
                'completed_count': len(completed),
                'failed_count': len(failed),
                'total_count': len(entries),
                'oldest_pending': oldest_pending
            }

            logger.info(
                f"Queue stats: {stats['pending_count']} pending, "
                f"{stats['completed_count']} completed"
            )

            return stats

        except Exception as e:
            logger.error(f"Error fetching queue stats: {e}", exc_info=True)
            return {
                'error': str(e),
                'pending_count': 0
            }


# Example usage (for testing)
if __name__ == "__main__":
    import json

    # Test data
    final_decision = {
        "decision": "EXECUTE",
        "reason": "All checks passed",
        "rr": 2.1,
        "bias_score": 0.85,
        "risk_context": {
            "mode": "NORMAL",
            "balance": 10000.0,
            "open_trades": 2
        },
        "timestamp": "2025-11-05T10:30:00Z"
    }

    trade_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "symbol_id": "123e4567-e89b-12d3-a456-426614174001",
        "side": "long",
        "entry_price": 18500.0,
        "stop_loss": 18400.0
    }

    # Test bridge (mock client)
    bridge = ReportBridge(supabase_client=None)
    result = bridge.process(final_decision, trade_data)

    print("ReportBridge Result:")
    print(json.dumps(result, indent=2))
