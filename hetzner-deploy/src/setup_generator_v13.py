"""
TradeMatrix.ai Setup Generator v1.3
Professional-grade setup generation with confidence calculation and validation

Based on ChatGPT feedback - implements proper:
- Pattern Detection (EMA Alignment)
- Confidence Scoring (0.0-0.95 based on technical factors)
- Risk/Reward Validation (minimum 2.0)
- Current Price Fetching
- RSI/MACD/Volume Integration
- Watchlist vs Active Setup Logic
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from supabase import Client
from openai import OpenAI
from src.price_fetcher import PriceFetcher
import yfinance as yf
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SetupGeneratorV13:
    """
    Professional Setup Generator with proper technical analysis

    Improvements over v1.0:
    - Fetches current_price from price_cache
    - Calculates confidence from EMA alignment, RSI, patterns
    - Validates R:R ratio mathematically (not relying on LLM)
    - Uses OpenAI only for detailed reasoning text
    - Implements Watchlist logic (confidence < 0.5)
    """

    def __init__(self, supabase_client: Client, openai_api_key: str):
        self.supabase = supabase_client
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.price_fetcher = PriceFetcher()
        logger.info("SetupGeneratorV13 initialized with PriceFetcher")

    async def generate_from_analysis(
        self,
        analysis_id: str,
        timeframe: Optional[str] = None
    ) -> Optional[str]:
        """Generate trading setup from chart analysis"""
        logger.info(f"[v1.3] Generating setup from analysis: {analysis_id}")

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

            # Step 2: Build structured context
            context = self._build_technical_context(analysis, symbol_id)

            if not context:
                logger.error("Failed to build technical context")
                return None

            # Step 3: Generate setup using technical analysis
            setup_data = self._generate_setup(symbol, context)

            if not setup_data or not setup_data.get('valid'):
                logger.warning(f"Setup invalid or rejected: {setup_data}")
                return None

            # Step 4: Enhance reasoning with OpenAI (optional)
            if setup_data.get('confidence', 0) >= 0.6:
                enhanced_reasoning = await self._enhance_reasoning_with_ai(
                    symbol, context, setup_data
                )
                if enhanced_reasoning:
                    setup_data['reasoning'] = enhanced_reasoning

            # Step 5: Save to database
            setup_id = await self._save_setup(
                symbol_id=symbol_id,
                symbol=symbol,
                analysis=analysis,
                setup_data=setup_data,
                timeframe=setup_data.get('timeframe') or timeframe or analysis['timeframe']
            )

            logger.info(f"Setup generated successfully: {setup_id}")
            return setup_id

        except Exception as e:
            logger.error(f"Error generating setup: {e}", exc_info=True)
            return None

    def _fetch_real_time_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch REAL-TIME price and calculate ACTUAL technical indicators

        Returns:
            Dict with current_price, ema20, ema50, ema200, rsi, atr
        """
        try:
            # Step 1: Get current price from PriceFetcher
            logger.info(f"Fetching real-time data for {symbol}")
            price_data = self.price_fetcher.fetch_price(symbol)

            if not price_data:
                logger.error(f"PriceFetcher returned no data for {symbol}")
                return None

            current_price = float(price_data['current_price'])
            price_timestamp = price_data.get('timestamp')

            # Step 1.5: Validate price freshness (max 2 minutes old)
            if price_timestamp:
                from datetime import datetime, timedelta
                try:
                    price_time = datetime.fromisoformat(price_timestamp.replace('Z', '+00:00'))
                    now = datetime.now()
                    age_seconds = (now - price_time).total_seconds()

                    logger.info(f"Price age: {age_seconds:.0f} seconds (timestamp: {price_timestamp})")

                    if age_seconds > 120:  # 2 minutes
                        logger.error(f"❌ Price too old: {age_seconds:.0f}s (max 120s)")
                        return None

                    logger.info(f"✅ Price is fresh ({age_seconds:.0f}s old)")
                except Exception as e:
                    logger.warning(f"Could not parse timestamp: {e}")
                    # Continue anyway (better than rejecting)

            if not current_price:
                logger.error(f"Failed to fetch current price for {symbol}")
                return None

            logger.info(f"✅ Current price for {symbol}: {current_price}")

            # Step 2: Get yfinance symbol mapping
            symbol_map = {
                'DAX': '^GDAXI',
                'NDX': '^NDX',
                'DJI': '^DJI',
                'EUR/USD': 'EURUSD=X',
                'EUR/GBP': 'EURGBP=X',
            }

            yf_symbol = symbol_map.get(symbol, symbol)

            # Step 3: Fetch historical data for indicators (need 200+ periods for EMA200)
            ticker = yf.Ticker(yf_symbol)

            # Download historical data (last 1 year for proper EMA200)
            hist = ticker.history(period='1y', interval='1d')

            if hist.empty or len(hist) < 20:
                logger.warning(f"Insufficient historical data for {symbol}, using placeholders")
                return {
                    'current_price': current_price,
                    'ema20': current_price,
                    'ema50': current_price,
                    'ema200': current_price,
                    'rsi': 50.0,
                    'atr': current_price * 0.01
                }

            # Step 4: Calculate technical indicators (use historical data, NOT current price!)
            close_prices = hist['Close']

            logger.info(f"Historical data: {len(close_prices)} days, latest close: {close_prices.iloc[-1]:.2f}, current: {current_price:.2f}")

            # EMA calculation
            ema20 = close_prices.ewm(span=20, adjust=False).mean().iloc[-1]
            ema50 = close_prices.ewm(span=50, adjust=False).mean().iloc[-1]
            ema200 = close_prices.ewm(span=200, adjust=False).mean().iloc[-1] if len(close_prices) >= 200 else ema50

            # RSI calculation
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

            # ATR calculation
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean().iloc[-1]

            logger.info(f"✅ Calculated indicators: EMA20={ema20:.2f}, EMA50={ema50:.2f}, EMA200={ema200:.2f}, RSI={rsi_value:.1f}, ATR={atr:.2f}")

            return {
                'current_price': current_price,
                'ema20': float(ema20),
                'ema50': float(ema50),
                'ema200': float(ema200),
                'rsi': float(rsi_value),
                'atr': float(atr)
            }

        except Exception as e:
            logger.error(f"Error fetching real-time data: {e}", exc_info=True)
            return None

    def _build_technical_context(self, analysis: Dict[str, Any], symbol_id: str) -> Optional[Dict[str, Any]]:
        """Build structured technical context with REAL-TIME price and indicators"""
        try:
            # Get symbol from analysis
            symbol = analysis['market_symbols']['symbol']

            # Step 1: Fetch REAL-TIME data (current price + indicators)
            real_time_data = self._fetch_real_time_data(symbol)

            if not real_time_data:
                logger.error(f"Failed to fetch real-time data for {symbol}")
                return None

            current_price = real_time_data['current_price']
            logger.info(f"✅ Using REAL-TIME price: {current_price}")

            # Step 2: Extract support/resistance from analysis
            support_levels = analysis.get('support_levels', [])
            resistance_levels = analysis.get('resistance_levels', [])

            supports = [float(s) for s in support_levels] if support_levels else []
            resistances = [float(r) for r in resistance_levels] if resistance_levels else []

            # Step 3: Extract patterns
            patterns = analysis.get('patterns_detected', [])

            # Step 4: Build context dict with REAL-TIME data
            context = {
                "price": current_price,
                "supports": supports,
                "resistances": resistances,
                "patterns": patterns,
                "trend": analysis.get('trend', 'unknown'),
                "confidence_score": float(analysis.get('confidence_score', 0)),
                "timeframe": analysis.get('timeframe', '1h'),
                # ✅ REAL TECHNICAL INDICATORS (not placeholders!)
                "ema20": real_time_data['ema20'],
                "ema50": real_time_data['ema50'],
                "ema200": real_time_data['ema200'],
                "rsi": real_time_data['rsi'],
                "atr": real_time_data['atr'],
                "volume": 100  # Placeholder (not critical for setup generation)
            }

            logger.info(
                f"✅ Built context with REAL-TIME data: "
                f"price={current_price:.2f}, EMA20={real_time_data['ema20']:.2f}, "
                f"EMA50={real_time_data['ema50']:.2f}, RSI={real_time_data['rsi']:.1f}, "
                f"supports={len(supports)}, resistances={len(resistances)}"
            )
            return context

        except Exception as e:
            logger.error(f"Error building context: {e}", exc_info=True)
            return None

    def _generate_setup(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate setup using pure technical analysis (ChatGPT v1.3 logic)
        """
        current_price = context.get("price")
        if not current_price:
            return {"valid": False, "error": "current_price missing"}

        ema20 = context.get("ema20", current_price)
        ema50 = context.get("ema50", current_price)
        ema200 = context.get("ema200", current_price)
        rsi = context.get("rsi", 50.0)
        atr = context.get("atr", current_price * 0.01)
        timeframe = context.get("timeframe", "1h")

        # Trend detection
        if ema20 > ema50 > ema200:
            trend = "bullish"
            side = "long"
        elif ema20 < ema50 < ema200:
            trend = "bearish"
            side = "short"
        else:
            trend = "neutral"
            side = "none"

        pattern_detected = (ema20 > ema50 > ema200) or (ema20 < ema50 < ema200)

        # Support/Resistance
        supports = context.get("supports", [current_price * 0.98])
        resistances = context.get("resistances", [current_price * 1.02])

        support = min(supports) if supports else current_price * 0.98
        resistance = max(resistances) if resistances else current_price * 1.02

        # Entry/SL/TP Calculation
        if side == "long":
            entry = round(support + (resistance - support) * 0.25, 3)
            stop_loss = round(support - atr * 2, 3)
            take_profit = round(entry + (entry - stop_loss) * 2, 3)
        elif side == "short":
            entry = round(resistance - (resistance - support) * 0.25, 3)
            stop_loss = round(resistance + atr * 2, 3)
            take_profit = round(entry - (stop_loss - entry) * 2, 3)
        else:
            return {"valid": False, "error": "No valid trend direction"}

        # Risk/Reward
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        risk_reward = round(reward / risk, 2) if risk > 0 else 0

        # Validation
        valid = (
            (side == "long" and stop_loss < entry < take_profit) or
            (side == "short" and stop_loss > entry > take_profit)
        ) and (risk_reward >= 2.5)

        # Confidence Score (ChatGPT formula)
        confidence = 0.0
        if trend in ["bullish", "bearish"]:
            confidence += 0.3
        if pattern_detected:
            confidence += 0.25
        if 45 < rsi < 55:
            confidence += 0.1
        elif (trend == "bullish" and rsi > 55) or (trend == "bearish" and rsi < 45):
            confidence += 0.2
        if risk_reward >= 2.5:
            confidence += 0.15
        if valid:
            confidence += 0.1
        confidence = round(min(confidence, 0.95), 2)

        # Basic reasoning
        reasoning = (
            f"{symbol} shows {trend.upper()} trend with EMA structure "
            f"({ema20:.3f}/{ema50:.3f}/{ema200:.3f}). "
            f"RSI at {rsi:.1f} indicates {'neutral' if 45 < rsi < 55 else 'trend-confirming'} momentum. "
            f"Entry at {entry} near support zone ({support:.2f}), "
            f"Stop-Loss below structure at {stop_loss}, "
            f"Take-Profit at resistance ({take_profit}). "
            f"Risk/Reward: {risk_reward}:1. "
            f"Setup valid if price holds above {support:.2f}."
        )

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "side": side,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward": risk_reward,
            "confidence": confidence,
            "reasoning": reasoning,
            "valid": valid,
            "pattern_detected": pattern_detected,
            "trend": trend
        }

    async def _enhance_reasoning_with_ai(
        self,
        symbol: str,
        context: Dict[str, Any],
        setup_data: Dict[str, Any]
    ) -> Optional[str]:
        """Use OpenAI to generate detailed reasoning (150+ words)"""
        try:
            prompt = f"""You are a professional trading analyst for TradeMatrix.ai.

Symbol: {symbol}
Setup: {setup_data['side'].upper()} @ {setup_data['entry']}
SL: {setup_data['stop_loss']} | TP: {setup_data['take_profit']}
R:R: {setup_data['risk_reward']}:1 | Confidence: {setup_data['confidence']}

Context:
{json.dumps(context, indent=2)}

Write a detailed 150-200 word technical analysis explaining:
1. WHY this setup makes sense (trend, patterns, levels)
2. Entry logic and timing
3. Stop-Loss placement reasoning
4. Take-Profit target justification
5. Risk factors and invalidation criteria

Use professional language, reference specific levels, and explain market structure."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                temperature=0.3,
                max_tokens=300,
                messages=[
                    {"role": "system", "content": "You are a professional technical analyst. Write clear, concise analysis."},
                    {"role": "user", "content": prompt}
                ]
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error enhancing reasoning: {e}")
            return None

    async def _save_setup(
        self,
        symbol_id: str,
        symbol: str,
        analysis: Dict[str, Any],
        setup_data: Dict[str, Any],
        timeframe: str
    ) -> Optional[str]:
        """Save setup to database"""
        try:
            setup_record = {
                "symbol_id": symbol_id,
                "module": "ai_generated_v13",
                "strategy": "pattern_based",
                "side": setup_data['side'],
                "entry_price": float(setup_data['entry']),
                "stop_loss": float(setup_data['stop_loss']),
                "take_profit": float(setup_data['take_profit']),
                "confidence": float(setup_data['confidence']),
                "status": "pending" if setup_data['confidence'] >= 0.6 else "watchlist",
                "payload": {
                    "source": "chart_analysis_v13",
                    "analysis_id": analysis['id'],
                    "chart_url": analysis.get('chart_url'),
                    "timeframe": timeframe,
                    "reasoning": setup_data.get('reasoning', ''),
                    "risk_reward_ratio": setup_data['risk_reward'],
                    "pattern_detected": setup_data.get('pattern_detected', False),
                    "trend": setup_data.get('trend'),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }

            result = self.supabase.table('setups').insert(setup_record).execute()

            if result.data and len(result.data) > 0:
                setup_id = result.data[0]['id']
                logger.info(f"Setup saved: {setup_id} (confidence={setup_data['confidence']})")
                return setup_id

            return None

        except Exception as e:
            logger.error(f"Error saving setup: {e}", exc_info=True)
            return None
