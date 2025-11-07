"""
SetupGenerator - Generates trading setups from chart analyses

Takes ChartWatcher pattern detection results and generates concrete trading setups
with Entry/SL/TP levels using OpenAI GPT-4.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from supabase import Client
from openai import OpenAI

logger = logging.getLogger(__name__)


class SetupGenerator:
    """
    Generates trading setups with Entry/SL/TP from chart analyses

    Workflow:
    1. Fetch chart_analysis by ID
    2. Extract patterns, trend, support/resistance levels
    3. Use OpenAI to determine optimal Entry/SL/TP
    4. Save setup to database
    """

    def __init__(self, supabase_client: Client, openai_api_key: str):
        """
        Initialize SetupGenerator

        Args:
            supabase_client: Supabase admin client
            openai_api_key: OpenAI API key for GPT-4
        """
        self.supabase = supabase_client
        self.openai_client = OpenAI(api_key=openai_api_key)
        logger.info("SetupGenerator initialized")

    async def generate_from_analysis(
        self,
        analysis_id: str,
        timeframe: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate trading setup from chart analysis

        Args:
            analysis_id: UUID of chart_analysis record
            timeframe: Optional timeframe override

        Returns:
            UUID of created setup record or None if failed
        """
        logger.info(f"Generating setup from analysis: {analysis_id}")

        try:
            # Step 1: Fetch chart analysis
            response = self.supabase.table('chart_analyses')\
                .select('*, market_symbols!inner(symbol, id)')\
                .eq('id', analysis_id)\
                .single()\
                .execute()

            if not response.data:
                logger.error(f"Analysis not found: {analysis_id}")
                return None

            analysis = response.data
            symbol = analysis['market_symbols']['symbol']
            symbol_id = analysis['market_symbols']['id']

            # Step 2: Build structured context for OpenAI
            context = self._build_context(analysis)

            # Step 3: Get current price (optional - for proximity check)
            # TODO: Fetch from MarketDataFetcher or use latest analysis data
            current_price = None  # Could fetch from price_cache table

            # Step 4: Ask OpenAI for Entry/SL/TP
            setup_data = self._generate_levels_with_ai(symbol, context, current_price)

            if not setup_data:
                logger.error("AI failed to generate setup levels")
                return None

            # Step 5: Save setup to database
            setup_id = await self._save_setup(
                symbol_id=symbol_id,
                symbol=symbol,
                analysis=analysis,
                setup_data=setup_data,
                timeframe=setup_data.get('timeframe') or timeframe or analysis['timeframe']
            )

            logger.info(f"Setup generated: {setup_id}")
            return setup_id

        except Exception as e:
            logger.error(f"Error generating setup: {e}", exc_info=True)
            return None

    def _build_context(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build structured context dict from analysis for AI prompt"""
        patterns = analysis.get('patterns_detected', [])
        support = analysis.get('support_levels', [])
        resistance = analysis.get('resistance_levels', [])

        return {
            "trend": analysis.get('trend', 'unknown'),
            "confidence": float(analysis.get('confidence_score', 0)),
            "patterns": [
                {
                    "name": p.get('name', 'unknown'),
                    "type": p.get('type', ''),
                    "confidence": float(p.get('confidence', 0))
                }
                for p in patterns[:5]
            ],
            "support_levels": [round(float(s), 2) for s in support[:3]] if support else [],
            "resistance_levels": [round(float(r), 2) for r in resistance[:3]] if resistance else [],
            "timeframe": analysis.get('timeframe', '1h')
        }

    def _generate_levels_with_ai(self, symbol: str, context: Dict[str, Any], current_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Use OpenAI to generate Entry/SL/TP levels with structured context"""
        try:
            import json

            # Format context as JSON string for prompt
            context_json = json.dumps(context, indent=2)

            prompt = f"""You are the TradeMatrix.ai Setup Generator, an expert system within a modular AI trading architecture.

Context Data:
{context_json}

Current Market Price: {current_price or 'unknown'}

Generate a structured trading setup for {symbol} using only technical analysis.
Include:
- Market trend & momentum (based on trend field)
- Active pattern detection (reference specific patterns from context)
- Key levels and validation against current price
- Entry, SL, TP logic consistent with TradeMatrix Risk Rules (min R:R 1:2)

Return ONLY valid JSON in this format:
{{
  "symbol": "{symbol}",
  "timeframe": "{context.get('timeframe', '1h')}",
  "side": "long" or "short",
  "entry": number,
  "stop_loss": number,
  "take_profit": number,
  "risk_reward": float,
  "confidence": 0.0-1.0,
  "reasoning": "Detailed technical justification (min 150 words, covering trend, structure, pattern, key levels, and timing)."
}}

Validation Rules:
- long → stop_loss < entry < take_profit
- short → stop_loss > entry > take_profit
- Entry should be within 2% of current price if current_price provided
- Use context data (support_levels, resistance_levels) for all numeric references
- Risk/Reward must be ≥ 1.5 (prefer 1:2 or better)
- Return ONLY pure JSON (no text outside braces, no markdown)"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                temperature=0.3,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical analyst. Return only valid JSON, no markdown, no explanations outside the JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            # Parse JSON
            import json
            setup_data = json.loads(content)

            # Validate required fields
            required = ['side', 'entry', 'stop_loss', 'take_profit', 'confidence', 'timeframe']
            if not all(k in setup_data for k in required):
                logger.error(f"Missing required fields in AI response: {setup_data}")
                return None

            # Validate setup logic
            if not self._validate_setup(setup_data):
                logger.error(f"Setup failed validation: {setup_data}")
                return None

            logger.info(f"AI generated valid setup: {setup_data}")
            return setup_data

        except Exception as e:
            logger.error(f"Error generating levels with AI: {e}", exc_info=True)
            return None

    def _validate_setup(self, setup_data: Dict[str, Any]) -> bool:
        """Validate setup meets TradeMatrix rules"""
        try:
            side = setup_data.get('side')
            entry = float(setup_data.get('entry', 0))
            sl = float(setup_data.get('stop_loss', 0))
            tp = float(setup_data.get('take_profit', 0))

            # Basic checks
            if not all([side, entry, sl, tp]):
                logger.error("Missing required fields for validation")
                return False

            # Validate order logic
            if side == 'long':
                if not (sl < entry < tp):
                    logger.error(f"Invalid LONG setup: SL={sl} Entry={entry} TP={tp} (must be SL < Entry < TP)")
                    return False
            elif side == 'short':
                if not (sl > entry > tp):
                    logger.error(f"Invalid SHORT setup: SL={sl} Entry={entry} TP={tp} (must be SL > Entry > TP)")
                    return False
            else:
                logger.error(f"Invalid side: {side}")
                return False

            # Validate Risk/Reward ratio
            risk = abs(entry - sl)
            reward = abs(tp - entry)

            if risk == 0:
                logger.error("Risk is zero - invalid setup")
                return False

            rr_ratio = reward / risk

            if rr_ratio < 1.5:
                logger.error(f"Risk/Reward ratio too low: {rr_ratio:.2f} (minimum 1.5)")
                return False

            logger.info(f"Setup passed validation: {side.upper()} R:R={rr_ratio:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False

    async def _save_setup(
        self,
        symbol_id: str,
        symbol: str,
        analysis: Dict[str, Any],
        setup_data: Dict[str, Any],
        timeframe: str
    ) -> Optional[str]:
        """Save generated setup to database"""
        try:
            # Calculate R:R if not provided by AI
            entry = float(setup_data['entry'])
            sl = float(setup_data['stop_loss'])
            tp = float(setup_data['take_profit'])
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr_ratio = round(reward / risk, 2) if risk > 0 else 0

            setup_record = {
                "symbol_id": symbol_id,
                "module": "ai_generated",
                "strategy": "pattern_based",
                "side": setup_data['side'],
                "entry_price": entry,
                "stop_loss": sl,
                "take_profit": tp,
                "confidence": float(setup_data['confidence']),
                "status": "pending",
                "payload": {
                    "source": "chart_analysis",
                    "analysis_id": analysis['id'],
                    "chart_url": analysis.get('chart_url'),
                    "timeframe": timeframe,
                    "reasoning": setup_data.get('reasoning', ''),
                    "patterns": analysis.get('patterns_detected', []),
                    "trend": analysis.get('trend'),
                    "risk_reward_ratio": setup_data.get('risk_reward', rr_ratio),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }

            result = self.supabase.table('setups').insert(setup_record).execute()

            if result.data and len(result.data) > 0:
                setup_id = result.data[0]['id']
                logger.info(f"Setup saved: {setup_id}")
                return setup_id

            return None

        except Exception as e:
            logger.error(f"Error saving setup: {e}", exc_info=True)
            return None
