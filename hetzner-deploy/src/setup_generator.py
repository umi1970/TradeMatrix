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

            # Step 2: Build context for OpenAI
            context = self._build_context(analysis)

            # Step 3: Ask OpenAI for Entry/SL/TP
            setup_data = self._generate_levels_with_ai(symbol, context)

            if not setup_data:
                logger.error("AI failed to generate setup levels")
                return None

            # Step 4: Save setup to database
            setup_id = await self._save_setup(
                symbol_id=symbol_id,
                symbol=symbol,
                analysis=analysis,
                setup_data=setup_data,
                timeframe=timeframe or analysis['timeframe']
            )

            logger.info(f"Setup generated: {setup_id}")
            return setup_id

        except Exception as e:
            logger.error(f"Error generating setup: {e}", exc_info=True)
            return None

    def _build_context(self, analysis: Dict[str, Any]) -> str:
        """Build context string from analysis for AI prompt"""
        patterns = analysis.get('patterns_detected', [])
        trend = analysis.get('trend', 'unknown')
        support = analysis.get('support_levels', [])
        resistance = analysis.get('resistance_levels', [])
        confidence = analysis.get('confidence_score', 0)

        context = f"""
Chart Analysis Summary:
- Trend: {trend}
- Confidence: {float(confidence) * 100:.0f}%
- Detected Patterns: {len(patterns)}

"""

        if patterns:
            context += "Patterns:\n"
            for p in patterns[:5]:  # Limit to top 5
                context += f"  - {p.get('name', 'unknown')}: {p.get('type', '')} ({p.get('confidence', 0) * 100:.0f}% confidence)\n"

        if support:
            context += f"\nSupport Levels: {', '.join([str(round(float(s), 2)) for s in support[:3]])}\n"

        if resistance:
            context += f"Resistance Levels: {', '.join([str(round(float(r), 2)) for r in resistance[:3]])}\n"

        return context

    def _generate_levels_with_ai(self, symbol: str, context: str) -> Optional[Dict[str, Any]]:
        """Use OpenAI to generate Entry/SL/TP levels"""
        try:
            prompt = f"""You are an expert technical analyst creating a detailed trading setup for {symbol}.

{context}

Analyze this data and create a comprehensive trading setup. Your analysis must include:

1. **Market Context**: Current trend and momentum
2. **Pattern Analysis**: Which patterns are most significant and why
3. **Key Levels**: Relevant support/resistance levels
4. **Setup Rationale**: WHY this setup makes sense NOW
5. **Entry Logic**: WHY this specific entry price
6. **Stop Loss Logic**: WHERE and WHY this stop placement
7. **Take Profit Logic**: Target zone and reasoning
8. **Risk Assessment**: What could invalidate this setup

Return ONLY valid JSON in this exact format:
{{
    "side": "long" or "short",
    "entry": number,
    "stop_loss": number,
    "take_profit": number,
    "confidence": 0.0-1.0,
    "reasoning": "DETAILED multi-paragraph analysis covering all points above. Use specific levels, pattern names, and technical reasoning. Minimum 150 words."
}}

Requirements:
- Entry near support (long) or resistance (short)
- Stop loss beyond invalidation level
- Risk/Reward ratio minimum 1:2
- Reasoning MUST be detailed (150+ words) with specific technical details
- Reference actual support/resistance levels from the data
- Explain market structure and why NOW is a good time"""

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
            required = ['side', 'entry', 'stop_loss', 'take_profit', 'confidence']
            if not all(k in setup_data for k in required):
                logger.error(f"Missing required fields in AI response: {setup_data}")
                return None

            logger.info(f"AI generated setup: {setup_data}")
            return setup_data

        except Exception as e:
            logger.error(f"Error generating levels with AI: {e}", exc_info=True)
            return None

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
            setup_record = {
                "symbol_id": symbol_id,
                "module": "ai_generated",
                "strategy": "pattern_based",
                "side": setup_data['side'],
                "entry_price": float(setup_data['entry']),
                "stop_loss": float(setup_data['stop_loss']),
                "take_profit": float(setup_data['take_profit']),
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
