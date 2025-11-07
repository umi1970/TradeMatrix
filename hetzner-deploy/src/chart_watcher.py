"""
TradeMatrix.ai - ChartWatcher Agent
Uses OpenAI Vision API to detect patterns in chart images.

Execution: Every 5 minutes during market hours (via Celery scheduler)
Patterns detected:
  1. Head & Shoulders (bullish/bearish)
  2. Double Top/Bottom
  3. Triangles (ascending/descending/symmetrical)
  4. Flags & Pennants
  5. Wedges (rising/falling)
  6. Channels

Data sources:
  - Supabase Storage (chart images from TradingView/generated)
  - ohlc table (for context: recent price action)

Output: Chart analyses in 'chart_analyses' table
"""

import logging
import io
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal
from pathlib import Path
import tempfile
import httpx

from supabase import Client
from openai import OpenAI

from src.chart_service import ChartService
from src.exceptions.chart_errors import (
    RateLimitError,
    ChartGenerationError,
    SymbolNotFoundError
)
from src.utils.ai_budget import check_ai_budget, log_ai_usage, AIBudgetError

# Setup logger
logger = logging.getLogger(__name__)


class ChartWatcher:
    """
    ChartWatcher Agent - Analyzes chart images using OpenAI Vision API

    Responsibilities:
    - Download chart images from Supabase Storage
    - Extract price values using OCR techniques
    - Detect chart patterns using OpenAI Vision API
    - Identify support/resistance levels
    - Store analysis results in database
    """

    def __init__(self, supabase_client: Client, openai_api_key: str, user_id: Optional[str] = None, tier: str = "free"):
        """
        Initialize ChartWatcher agent

        Args:
            supabase_client: Supabase client instance (admin client for bypassing RLS)
            openai_api_key: OpenAI API key for Vision API access
            user_id: Optional user ID who triggered this analysis (None for system-triggered)
            tier: User's subscription tier (free, starter, pro, expert)
        """
        self.supabase = supabase_client
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.chart_service = ChartService(supabase_client=supabase_client)
        self.user_id = user_id
        self.tier = tier
        logger.info(f"ChartWatcher initialized (user_id={user_id}, tier={tier})")


    def download_chart(self, chart_url: str) -> Optional[bytes]:
        """
        Download chart image from Supabase Storage or external URL

        Args:
            chart_url: URL to chart image (Supabase Storage URL or external)

        Returns:
            Image bytes if successful, None otherwise
        """
        logger.info(f"Downloading chart from: {chart_url}")

        try:
            # Download image using httpx
            with httpx.Client(timeout=30.0) as client:
                response = client.get(chart_url)
                response.raise_for_status()

                image_bytes = response.content
                logger.info(f"Downloaded {len(image_bytes)} bytes")
                return image_bytes

        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading chart: {e}")
            return None
        except Exception as e:
            logger.error(f"Error downloading chart: {e}")
            return None


    def extract_price_values(self, image_bytes: bytes, symbol_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract price values from chart image using OpenAI Vision API

        This method uses GPT-4 Vision to read price values displayed on the chart,
        including current price, high, low, and visible support/resistance levels.

        Args:
            image_bytes: Raw image bytes
            symbol_name: Symbol name for context

        Returns:
            Dict with extracted values:
            {
                'current_price': float,
                'high_24h': float,
                'low_24h': float,
                'visible_levels': List[float],
                'confidence': float (0.0-1.0)
            }
            Returns None if extraction fails
        """
        logger.info(f"Extracting price values for {symbol_name}")

        try:
            # Check AI budget before making OpenAI call
            check_ai_budget(self.user_id, self.tier, self.supabase)

            # Convert image bytes to base64 for OpenAI API
            import base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            # Construct prompt for price extraction
            prompt = f"""
You are analyzing a trading chart for {symbol_name}.

Extract the following information from the chart image:
1. Current price (the latest price visible on the chart)
2. 24-hour high (if visible)
3. 24-hour low (if visible)
4. Any visible support/resistance levels (horizontal lines or price zones)

Return your analysis in this JSON format:
{{
    "current_price": <number or null>,
    "high_24h": <number or null>,
    "low_24h": <number or null>,
    "visible_levels": [<list of price levels as numbers>],
    "confidence": <0.0 to 1.0 indicating confidence in extraction>
}}

If you cannot clearly read a value, use null. Only include levels you are confident about.
"""

            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # GPT-4 Omni with vision capabilities
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent extraction
            )

            # Parse response
            result_text = response.choices[0].message.content
            logger.debug(f"OpenAI response: {result_text}")

            # Log AI usage
            log_ai_usage(
                supabase=self.supabase,
                agent_name='chart_watcher',
                model='gpt-4o',
                user_id=self.user_id,
                symbol=symbol_name,
                tokens=response.usage.total_tokens if hasattr(response, 'usage') else None
            )

            # Extract JSON from response
            import json
            import re

            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group(0))
                logger.info(f"Extracted price values: {result_json}")
                return result_json
            else:
                logger.warning("No JSON found in OpenAI response")
                return None

        except Exception as e:
            logger.error(f"Error extracting price values: {e}", exc_info=True)
            return None


    def detect_patterns(
        self,
        image_bytes: bytes,
        symbol_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect chart patterns using OpenAI Vision API

        Patterns to detect:
        - Head & Shoulders (bullish/bearish)
        - Double Top/Bottom
        - Triangles (ascending/descending/symmetrical)
        - Flags & Pennants
        - Wedges (rising/falling)
        - Channels (uptrend/downtrend/sideways)

        Args:
            image_bytes: Raw image bytes
            symbol_name: Symbol name for context
            context: Optional context dict with recent price data

        Returns:
            Dict with detected patterns:
            {
                'patterns': [
                    {
                        'name': 'head_and_shoulders',
                        'type': 'bearish',
                        'confidence': 0.85,
                        'description': '...',
                        'key_levels': {
                            'neckline': 18500.0,
                            'target': 18200.0
                        }
                    },
                    ...
                ],
                'trend': 'bullish' | 'bearish' | 'sideways',
                'support_levels': [18300.0, 18100.0],
                'resistance_levels': [18700.0, 18900.0],
                'analysis_summary': 'Overall analysis text'
            }
            Returns None if detection fails
        """
        logger.info(f"Detecting patterns for {symbol_name}")

        try:
            # Check AI budget before making OpenAI call
            check_ai_budget(self.user_id, self.tier, self.supabase)

            # Convert image bytes to base64
            import base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            # Build context string if provided
            context_str = ""
            if context:
                current_price = context.get('current_price', 'unknown')
                timeframe = context.get('timeframe', 'unknown')
                context_str = f"\nCurrent price: {current_price}, Timeframe: {timeframe}"

            # Construct prompt for pattern detection
            prompt = f"""
You are an expert technical analyst analyzing a trading chart for {symbol_name}.{context_str}

Identify and analyze the following chart patterns if present:

**Reversal Patterns:**
- Head & Shoulders (bearish reversal)
- Inverse Head & Shoulders (bullish reversal)
- Double Top (bearish)
- Double Bottom (bullish)

**Continuation Patterns:**
- Ascending Triangle (bullish continuation)
- Descending Triangle (bearish continuation)
- Symmetrical Triangle (neutral, awaits breakout)
- Bull Flag / Pennant (bullish continuation)
- Bear Flag / Pennant (bearish continuation)

**Wedge Patterns:**
- Rising Wedge (can be bearish if in uptrend)
- Falling Wedge (can be bullish if in downtrend)

**Channel Patterns:**
- Uptrend Channel
- Downtrend Channel
- Sideways/Horizontal Channel

For each pattern detected, provide:
1. Pattern name
2. Pattern type (bullish/bearish/neutral)
3. Confidence score (0.0-1.0)
4. Brief description
5. Key levels (neckline, breakout level, target price, etc.)

Also identify:
- Overall trend direction (bullish/bearish/sideways)
- Support levels (at least 2-3 if visible)
- Resistance levels (at least 2-3 if visible)
- Brief analysis summary

Return your analysis in this JSON format:
{{
    "patterns": [
        {{
            "name": "pattern_name",
            "type": "bullish|bearish|neutral",
            "confidence": 0.0-1.0,
            "description": "brief description",
            "key_levels": {{
                "level_name": price_value
            }}
        }}
    ],
    "trend": "bullish|bearish|sideways",
    "support_levels": [list of prices],
    "resistance_levels": [list of prices],
    "analysis_summary": "Overall technical analysis"
}}

If no clear patterns are visible, return an empty patterns array but still provide trend and levels.
"""

            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # GPT-4 Omni
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.2  # Slightly higher for more nuanced analysis
            )

            # Parse response
            result_text = response.choices[0].message.content
            logger.debug(f"OpenAI pattern detection response: {result_text}")

            # Log AI usage
            log_ai_usage(
                supabase=self.supabase,
                agent_name='chart_watcher',
                model='gpt-4o',
                user_id=self.user_id,
                symbol=symbol_name,
                tokens=response.usage.total_tokens if hasattr(response, 'usage') else None
            )

            # Extract JSON from response
            import json
            import re

            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group(0))

                # Log detected patterns
                num_patterns = len(result_json.get('patterns', []))
                logger.info(f"Detected {num_patterns} patterns for {symbol_name}")

                return result_json
            else:
                logger.warning("No JSON found in OpenAI pattern detection response")
                return None

        except Exception as e:
            logger.error(f"Error detecting patterns: {e}", exc_info=True)
            return None


    def analyze_chart(
        self,
        symbol_id: UUID,
        symbol_name: str,
        chart_url: str,
        timeframe: str = '1h'
    ) -> Optional[UUID]:
        """
        Complete chart analysis workflow

        Steps:
        1. Download chart image from URL
        2. Extract price values (OCR)
        3. Detect chart patterns (Vision AI)
        4. Store analysis in chart_analyses table

        Args:
            symbol_id: UUID of the market symbol
            symbol_name: Symbol name (e.g., "DAX", "NDX")
            chart_url: URL to chart image
            timeframe: Chart timeframe (1m, 5m, 15m, 1h, 4h, 1d)

        Returns:
            UUID of created analysis record, None if failed
        """
        logger.info(f"Starting chart analysis for {symbol_name} ({timeframe})")

        try:
            # Step 1 - Download chart image
            image_bytes = self.download_chart(chart_url)

            if not image_bytes:
                logger.error(f"Failed to download chart for {symbol_name}")
                return None

            # Step 2 - Get current price from current_prices table (filled by PriceFetcher every 60s)
            try:
                result = self.supabase.table('current_prices')\
                    .select('price')\
                    .eq('symbol_id', str(symbol_id))\
                    .order('updated_at', desc=True)\
                    .limit(1)\
                    .execute()

                current_price = None
                if result.data and len(result.data) > 0:
                    current_price = float(result.data[0]['price'])
                    logger.info(f"Fetched current_price from current_prices table: {current_price}")
            except Exception as e:
                logger.warning(f"Could not fetch current price from current_prices table: {e}")
                current_price = None

            context = {
                'current_price': current_price,
                'timeframe': timeframe
            }

            # Step 3 - Extract price values
            price_data = self.extract_price_values(image_bytes, symbol_name)

            # Step 4 - Detect patterns
            pattern_data = self.detect_patterns(image_bytes, symbol_name, context)

            if not pattern_data:
                logger.warning(f"Pattern detection failed for {symbol_name}")
                return None

            # Step 5 - Combine results
            analysis_payload = {
                'price_data': price_data,
                'pattern_data': pattern_data,
                'chart_url': chart_url,
                'timeframe': timeframe,
                'current_price': current_price,  # Store for SetupGenerator
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Step 6 - Store in chart_analyses table
            analysis_record = {
                'symbol_id': str(symbol_id),
                'timeframe': timeframe,
                'chart_url': chart_url,
                'patterns_detected': pattern_data.get('patterns', []),
                'trend': pattern_data.get('trend', 'unknown'),
                'support_levels': pattern_data.get('support_levels', []),
                'resistance_levels': pattern_data.get('resistance_levels', []),
                'analysis_summary': pattern_data.get('analysis_summary', ''),
                'confidence_score': self._calculate_overall_confidence(pattern_data),
                'payload': analysis_payload
            }

            result = self.supabase.table('chart_analyses')\
                .insert(analysis_record)\
                .execute()

            if not result.data or len(result.data) == 0:
                logger.error(f"Failed to insert chart analysis for {symbol_name}")
                return None

            analysis_id = result.data[0]['id']
            logger.info(f"Chart analysis saved with ID: {analysis_id}")

            return UUID(analysis_id)

        except Exception as e:
            logger.error(f"Error in chart analysis for {symbol_name}: {e}", exc_info=True)
            return None


    def _calculate_overall_confidence(self, pattern_data: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score from pattern detection results

        Args:
            pattern_data: Dict from detect_patterns()

        Returns:
            Confidence score (0.0-1.0)
        """
        patterns = pattern_data.get('patterns', [])

        if not patterns:
            return 0.0

        # Average confidence of all detected patterns
        confidences = [p.get('confidence', 0.0) for p in patterns]
        avg_confidence = sum(confidences) / len(confidences)

        return round(avg_confidence, 2)


    async def run(
        self,
        symbols: Optional[List[str]] = None,
        timeframe: str = '1h'
    ) -> Dict[str, Any]:
        """
        Main execution method - Called by Celery scheduler every 5 minutes

        Process:
        1. Fetch active symbols from market_symbols table
        2. For each symbol:
           a. Check if chart image URL exists in database or Storage
           b. If found, run analyze_chart()
        3. Return summary of analyzed charts

        Args:
            symbols: Optional list of symbol names to analyze (default: all active symbols)
            timeframe: Chart timeframe to analyze (default: 1h)

        Returns:
            Dict with execution summary:
            {
                'execution_time': datetime,
                'symbols_analyzed': int,
                'analyses_created': int,
                'analyses': List[Dict]
            }
        """
        execution_start = datetime.now(timezone.utc)
        logger.info(f"ChartWatcher execution started at {execution_start}")

        # Check AI budget BEFORE starting analysis
        try:
            check_ai_budget(self.user_id, self.tier, self.supabase)
        except AIBudgetError as e:
            logger.error(f"❌ AI budget exceeded - aborting ChartWatcher run: {e}")
            return {
                'execution_time': execution_start.isoformat(),
                'symbols_analyzed': 0,
                'analyses_created': 0,
                'analyses': [],
                'error': str(e),
                'status': 'budget_exceeded'
            }

        try:
            # Step 1 - Fetch active symbols
            query = self.supabase.table('market_symbols')\
                .select('id, symbol')\
                .eq('active', True)

            if symbols:
                query = query.in_('symbol', symbols)

            result = query.execute()
            active_symbols = result.data if result.data else []

            if not active_symbols:
                logger.warning("No active symbols found")
                return {
                    'execution_time': execution_start.isoformat(),
                    'symbols_analyzed': 0,
                    'analyses_created': 0,
                    'analyses': []
                }

            logger.info(f"Processing {len(active_symbols)} symbols for chart analysis")

            # Step 2 - Analyze each symbol
            analyses = []

            for symbol_record in active_symbols:
                symbol_id = UUID(symbol_record['id'])
                symbol_name = symbol_record['symbol']

                try:
                    # Generate chart via ChartService (5m for scalping, 15m for intraday)
                    logger.info(f"Generating charts for {symbol_name}...")

                    # Generate 5m chart (scalping profile)
                    chart_url_5m = await self.chart_service.generate_chart_url(
                        symbol=symbol_name,
                        timeframe='5m',
                        agent_name='ChartWatcher',
                        symbol_id=str(symbol_id)
                    )

                    # Generate 15m chart (intraday profile)
                    chart_url_15m = await self.chart_service.generate_chart_url(
                        symbol=symbol_name,
                        timeframe='15m',
                        agent_name='ChartWatcher',
                        symbol_id=str(symbol_id)
                    )

                    # Use primary timeframe for analysis (from parameter)
                    primary_chart_url = chart_url_15m if timeframe == '15m' else chart_url_5m

                    if not primary_chart_url:
                        logger.warning(f"Failed to generate chart for {symbol_name}")
                        continue

                    # Save snapshot for primary timeframe
                    snapshot_id = await self.chart_service.save_snapshot(
                        symbol_id=str(symbol_id),
                        chart_url=primary_chart_url,
                        timeframe=timeframe,
                        agent_name='ChartWatcher',
                        metadata={'analysis_type': 'pattern_detection'}
                    )

                    logger.info(f"Chart generated: {primary_chart_url}")

                    # Analyze chart with OpenAI Vision API
                    analysis_id = self.analyze_chart(
                        symbol_id=symbol_id,
                        symbol_name=symbol_name,
                        chart_url=primary_chart_url,
                        timeframe=timeframe
                    )

                    if analysis_id:
                        analyses.append({
                            'symbol': symbol_name,
                            'analysis_id': str(analysis_id),
                            'timeframe': timeframe,
                            'chart_snapshot_id': str(snapshot_id) if snapshot_id else None
                        })
                        logger.info(f"✅ Chart analyzed: {symbol_name} ({timeframe})")

                except RateLimitError as e:
                    logger.error(f"❌ Rate limit reached: {e.details if hasattr(e, 'details') else str(e)}")
                    # Stop processing more symbols to avoid hitting rate limit
                    break
                except Exception as e:
                    logger.error(f"Error analyzing chart for {symbol_name}: {e}", exc_info=True)
                    continue

            execution_end = datetime.now(timezone.utc)
            duration_ms = int((execution_end - execution_start).total_seconds() * 1000)

            summary = {
                'execution_time': execution_start.isoformat(),
                'execution_duration_ms': duration_ms,
                'symbols_analyzed': len(active_symbols),
                'analyses_created': len(analyses),
                'analyses': analyses
            }

            logger.info(f"ChartWatcher execution completed: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error in ChartWatcher execution: {e}", exc_info=True)
            execution_end = datetime.now(timezone.utc)
            duration_ms = int((execution_end - execution_start).total_seconds() * 1000)

            return {
                'execution_time': execution_start.isoformat(),
                'execution_duration_ms': duration_ms,
                'symbols_analyzed': 0,
                'analyses_created': 0,
                'analyses': [],
                'error': str(e)
            }


# Example usage (for testing)
if __name__ == "__main__":
    # This would be called from Celery task
    import sys
    import os

    # Add API src to path
    api_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api/src'))
    sys.path.insert(0, api_src_path)

    from config.supabase import get_supabase_admin
    from config import settings

    # Initialize agent with admin client
    watcher = ChartWatcher(
        supabase_client=get_supabase_admin(),
        openai_api_key=settings.OPENAI_API_KEY
    )

    # Run analysis
    result = watcher.run(timeframe='1h')

    print("ChartWatcher Results:")
    print(result)
