"""
TradeMatrix.ai - EventWatcher Agent
Monitors macro economic events and high-impact news releases.

Execution: Part of ValidationAndRisk flow (on-demand)
Responsibilities:
  1. Fetch upcoming economic events from external API or database
  2. Identify high-risk events within specified time window
  3. Flag trades for rejection if high-risk event is imminent
  4. Cache event data in Supabase for performance

Data sources:
  - External economic calendar API (Trading Economics, Forex Factory, etc.)
  - Cached events in 'economic_events' table (Supabase)

Output: Risk events analysis for TradeDecisionEngine
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from uuid import UUID

from supabase import Client
import requests

# Setup logger
logger = logging.getLogger(__name__)


class EventWatcher:
    """
    EventWatcher Agent - Monitors macro economic events and high-impact news

    Responsibilities:
    - Fetch upcoming economic events from external API
    - Cache events in Supabase for performance
    - Identify high-risk events (CPI, NFP, FOMC, Fed speeches, etc.)
    - Determine if trading should be paused due to event risk
    - Return list of upcoming high-risk events
    """

    # High-impact event keywords (configurable)
    HIGH_IMPACT_KEYWORDS = [
        'CPI', 'NFP', 'FOMC', 'Fed', 'Interest Rate', 'Employment',
        'GDP', 'PCE', 'Retail Sales', 'Shutdown', 'Debt Ceiling',
        'Central Bank', 'ECB', 'Powell', 'Lagarde', 'Non-Farm'
    ]

    def __init__(self, supabase_client: Client, api_key: Optional[str] = None):
        """
        Initialize EventWatcher agent

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
            api_key: Optional API key for external economic calendar service
        """
        self.supabase = supabase_client
        self.api_key = api_key
        logger.info("EventWatcher initialized")


    def fetch_upcoming_events(
        self,
        country: str = "United States",
        importance: str = "high",
        hours_ahead: int = 48
    ) -> List[Dict[str, Any]]:
        """
        Fetch upcoming economic events from external API or cached data

        Process:
        1. Check Supabase cache for recent events (within 1 hour)
        2. If cache miss or stale, fetch from external API
        3. Store fetched events in cache
        4. Filter by country and importance
        5. Return upcoming events within hours_ahead window

        Args:
            country: Country name (e.g., "United States", "Germany")
            importance: Event importance ("high", "medium", "low")
            hours_ahead: Look ahead window in hours (default: 48)

        Returns:
            List of event dicts:
            [{
                'event_id': str,
                'title': str,
                'country': str,
                'impact': str ('high', 'medium', 'low'),
                'event_time': str (ISO timestamp),
                'description': str,
                'actual': Optional[str],
                'forecast': Optional[str],
                'previous': Optional[str]
            }]
        """
        logger.info(f"Fetching upcoming events for {country} (importance: {importance})")

        try:
            # Step 1 - Check cache first
            now = datetime.now(timezone.utc)
            cache_cutoff = now - timedelta(hours=1)  # Cache valid for 1 hour

            result = self.supabase.table('economic_events')\
                .select('*')\
                .eq('country', country)\
                .gte('event_time', now.isoformat())\
                .lte('event_time', (now + timedelta(hours=hours_ahead)).isoformat())\
                .gte('cached_at', cache_cutoff.isoformat())\
                .execute()

            cached_events = result.data if result.data else []

            if cached_events:
                logger.info(f"Using {len(cached_events)} cached events")
                # Filter by importance
                filtered = [e for e in cached_events if e.get('impact', '').lower() == importance.lower()]
                return filtered

            # Step 2 - Cache miss, fetch from external API
            logger.info("Cache miss, fetching from external API")
            external_events = self._fetch_from_external_api(country, hours_ahead)

            # Step 3 - Store in cache
            if external_events:
                self._cache_events(external_events)

            # Step 4 - Filter by importance
            filtered = [e for e in external_events if e.get('impact', '').lower() == importance.lower()]

            logger.info(f"Fetched {len(filtered)} {importance}-impact events")
            return filtered

        except Exception as e:
            logger.error(f"Error fetching upcoming events: {e}", exc_info=True)
            return []


    def _fetch_from_external_api(
        self,
        country: str,
        hours_ahead: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from external economic calendar API

        Note: This is a placeholder implementation. In production, integrate with:
        - Trading Economics API
        - Forex Factory API
        - Investing.com API
        - Or custom web scraper

        Args:
            country: Country name
            hours_ahead: Look ahead window in hours

        Returns:
            List of event dicts
        """
        logger.info("Fetching from external API (placeholder)")

        # TODO: Replace with actual API integration
        # For now, return mock data for high-impact events

        now = datetime.now(timezone.utc)

        # Mock upcoming events (for testing)
        mock_events = [
            {
                'event_id': 'mock_cpi_2025',
                'title': 'Consumer Price Index (CPI)',
                'country': 'United States',
                'impact': 'high',
                'event_time': (now + timedelta(hours=6)).isoformat(),
                'description': 'Monthly CPI inflation report',
                'actual': None,
                'forecast': '3.2%',
                'previous': '3.4%'
            },
            {
                'event_id': 'mock_fed_2025',
                'title': 'FOMC Meeting Statement',
                'country': 'United States',
                'impact': 'high',
                'event_time': (now + timedelta(hours=24)).isoformat(),
                'description': 'Federal Reserve interest rate decision',
                'actual': None,
                'forecast': '5.50%',
                'previous': '5.50%'
            }
        ]

        logger.warning("Using mock event data - integrate real API in production!")
        return mock_events


    def _cache_events(self, events: List[Dict[str, Any]]) -> None:
        """
        Store events in Supabase cache

        Args:
            events: List of event dicts to cache
        """
        try:
            now = datetime.now(timezone.utc)

            for event in events:
                cache_record = {
                    'event_id': event.get('event_id'),
                    'title': event.get('title'),
                    'country': event.get('country'),
                    'impact': event.get('impact'),
                    'event_time': event.get('event_time'),
                    'description': event.get('description', ''),
                    'actual': event.get('actual'),
                    'forecast': event.get('forecast'),
                    'previous': event.get('previous'),
                    'cached_at': now.isoformat()
                }

                # Upsert (insert or update)
                self.supabase.table('economic_events')\
                    .upsert(cache_record, on_conflict='event_id')\
                    .execute()

            logger.info(f"Cached {len(events)} events")

        except Exception as e:
            logger.error(f"Error caching events: {e}", exc_info=True)


    def check_high_risk(
        self,
        within_hours: float = 2.0,
        country: str = "United States"
    ) -> bool:
        """
        Check if a high-risk event is imminent

        Args:
            within_hours: Time window in hours (default: 2.0)
            country: Country to check (default: "United States")

        Returns:
            True if high-risk event within time window, False otherwise
        """
        logger.info(f"Checking for high-risk events within {within_hours} hours")

        try:
            # Fetch upcoming high-impact events
            events = self.fetch_upcoming_events(
                country=country,
                importance="high",
                hours_ahead=int(within_hours)
            )

            if not events:
                logger.info("No high-risk events found")
                return False

            # Check if any event is within the time window
            now = datetime.now(timezone.utc)
            cutoff_time = now + timedelta(hours=within_hours)

            for event in events:
                event_time_str = event.get('event_time')
                if not event_time_str:
                    continue

                event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))

                if now <= event_time <= cutoff_time:
                    logger.warning(
                        f"High-risk event imminent: {event.get('title')} at {event_time_str}"
                    )
                    return True

            logger.info("No imminent high-risk events")
            return False

        except Exception as e:
            logger.error(f"Error checking high-risk events: {e}", exc_info=True)
            # Fail-safe: return False on error (don't block trading)
            return False


    def get_risk_events(
        self,
        within_hours: float = 24.0,
        country: str = "United States"
    ) -> Dict[str, Any]:
        """
        Get detailed risk events analysis

        Args:
            within_hours: Time window in hours (default: 24.0)
            country: Country to check (default: "United States")

        Returns:
            Dict with risk analysis:
            {
                'high_risk': bool,
                'events_count': int,
                'events': [
                    {
                        'title': str,
                        'impact': str,
                        'time': str,
                        'hours_until': float,
                        'description': str
                    }
                ],
                'recommendation': str
            }
        """
        logger.info(f"Getting risk events within {within_hours} hours")

        try:
            # Fetch upcoming high-impact events
            events = self.fetch_upcoming_events(
                country=country,
                importance="high",
                hours_ahead=int(within_hours)
            )

            now = datetime.now(timezone.utc)

            # Build detailed event list
            risk_events = []
            high_risk = False

            for event in events:
                event_time_str = event.get('event_time')
                if not event_time_str:
                    continue

                event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))
                hours_until = (event_time - now).total_seconds() / 3600

                # Mark as high risk if within 2 hours
                if hours_until <= 2.0:
                    high_risk = True

                risk_events.append({
                    'title': event.get('title'),
                    'impact': event.get('impact'),
                    'time': event_time_str,
                    'hours_until': round(hours_until, 1),
                    'description': event.get('description', ''),
                    'forecast': event.get('forecast'),
                    'previous': event.get('previous')
                })

            # Sort by time (soonest first)
            risk_events.sort(key=lambda x: x['hours_until'])

            # Generate recommendation
            if high_risk:
                recommendation = "PAUSE TRADING - High-impact event within 2 hours"
            elif risk_events:
                recommendation = f"CAUTION - {len(risk_events)} high-impact event(s) upcoming"
            else:
                recommendation = "CLEAR - No high-impact events in timeframe"

            result = {
                'high_risk': high_risk,
                'events_count': len(risk_events),
                'events': risk_events,
                'recommendation': recommendation,
                'timestamp': now.isoformat()
            }

            logger.info(f"Risk analysis: {recommendation}")
            return result

        except Exception as e:
            logger.error(f"Error getting risk events: {e}", exc_info=True)
            return {
                'high_risk': False,
                'events_count': 0,
                'events': [],
                'recommendation': "ERROR - Could not fetch events (proceeding with caution)",
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }


# Example usage (for testing)
if __name__ == "__main__":
    import sys
    from config.supabase import get_supabase_admin

    # Initialize agent with admin client
    watcher = EventWatcher(supabase_client=get_supabase_admin())

    # Check for high-risk events
    high_risk = watcher.check_high_risk(within_hours=2.0)
    print(f"High risk: {high_risk}")

    # Get detailed risk analysis
    risk_analysis = watcher.get_risk_events(within_hours=24.0)
    print("\nRisk Analysis:")
    print(risk_analysis)
