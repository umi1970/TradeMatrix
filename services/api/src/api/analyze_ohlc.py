"""
OHLC Analysis API Endpoint

Analyzes OHLC bar data from TradingView alerts and generates trading setups.

Flow:
1. Receive OHLC bars (up to 100 bars)
2. Calculate technical indicators (EMA, RSI, ATR)
3. Detect trend (Higher Highs/Lows)
4. Find support/resistance levels
5. Calculate Entry/SL/TP prices
6. Generate confidence score
7. Use AI (GPT-4o-mini) for reasoning
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import os
from openai import OpenAI

router = APIRouter()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# =====================================================================
# REQUEST/RESPONSE MODELS
# =====================================================================

class OHLCBar(BaseModel):
    """Single OHLC candlestick bar"""
    time: str  # Unix timestamp (ms)
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


class AnalyzeOHLCRequest(BaseModel):
    """Request payload for OHLC analysis"""
    ticker: str = Field(..., description="Symbol ticker (e.g., DAX, EURUSD)")
    interval: str = Field(..., description="Timeframe (e.g., 60 for 1h, D for daily)")
    bars: List[OHLCBar] = Field(..., min_items=20, max_items=200, description="OHLC bars (20-200)")


class AnalyzeOHLCResponse(BaseModel):
    """AI Analysis response"""
    side: str = Field(..., description="Trade direction: long or short")
    entry_price: float = Field(..., description="Recommended entry price")
    stop_loss: float = Field(..., description="Stop loss price")
    take_profit: float = Field(..., description="Take profit price")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    reasoning: str = Field(..., description="AI reasoning for the setup")
    patterns_detected: Optional[List[str]] = Field(default=[], description="Detected chart patterns")
    support_levels: Optional[List[float]] = Field(default=[], description="Key support levels")
    resistance_levels: Optional[List[float]] = Field(default=[], description="Key resistance levels")
    trend: Optional[str] = Field(default=None, description="Current trend: bullish, bearish, sideways")
    risk_reward: Optional[float] = Field(default=None, description="Risk/Reward ratio")


# =====================================================================
# TECHNICAL ANALYSIS FUNCTIONS
# =====================================================================

def bars_to_dataframe(bars: List[OHLCBar]) -> pd.DataFrame:
    """Convert OHLC bars to pandas DataFrame"""
    data = []
    for bar in bars:
        data.append({
            'time': pd.to_datetime(int(bar.time), unit='ms'),
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume or 0,
        })

    df = pd.DataFrame(data)
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    return df


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators using pandas_ta-like logic
    (simplified version without pandas_ta dependency)
    """
    # EMA (Exponential Moving Average)
    df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean() if len(df) >= 50 else np.nan

    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # ATR (Average True Range)
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()

    return df


def detect_trend(df: pd.DataFrame) -> Tuple[str, float]:
    """
    Detect trend based on Higher Highs/Lows (bullish) or Lower Highs/Lows (bearish)

    Returns:
        (trend, strength): trend is 'bullish', 'bearish', or 'sideways'
                          strength is 0.0-1.0
    """
    # Get last 20 bars for trend analysis
    recent = df.tail(20)

    # Find swing highs and lows
    swing_highs = recent['high'].rolling(window=3, center=True).max()
    swing_lows = recent['low'].rolling(window=3, center=True).min()

    highs = recent[recent['high'] == swing_highs]['high'].dropna()
    lows = recent[recent['low'] == swing_lows]['low'].dropna()

    if len(highs) < 2 or len(lows) < 2:
        return 'sideways', 0.3

    # Check if highs are increasing (bullish)
    highs_increasing = all(highs.iloc[i] < highs.iloc[i+1] for i in range(len(highs)-1))

    # Check if lows are increasing (bullish)
    lows_increasing = all(lows.iloc[i] < lows.iloc[i+1] for i in range(len(lows)-1))

    # Check if highs are decreasing (bearish)
    highs_decreasing = all(highs.iloc[i] > highs.iloc[i+1] for i in range(len(highs)-1))

    # Check if lows are decreasing (bearish)
    lows_decreasing = all(lows.iloc[i] > lows.iloc[i+1] for i in range(len(lows)-1))

    # EMA trend confirmation
    last_close = df['close'].iloc[-1]
    ema_20 = df['ema_20'].iloc[-1]
    ema_50 = df['ema_50'].iloc[-1] if not pd.isna(df['ema_50'].iloc[-1]) else ema_20

    above_ema = last_close > ema_20 and ema_20 > ema_50
    below_ema = last_close < ema_20 and ema_20 < ema_50

    # Determine trend
    if highs_increasing and lows_increasing and above_ema:
        strength = 0.8 if (ema_20 - ema_50) / ema_50 > 0.01 else 0.6
        return 'bullish', strength
    elif highs_decreasing and lows_decreasing and below_ema:
        strength = 0.8 if (ema_50 - ema_20) / ema_50 > 0.01 else 0.6
        return 'bearish', strength
    else:
        return 'sideways', 0.4


def find_support_resistance(df: pd.DataFrame) -> Tuple[List[float], List[float]]:
    """
    Find key support and resistance levels using swing points

    Returns:
        (support_levels, resistance_levels)
    """
    # Get last 50 bars
    recent = df.tail(50)

    # Find swing highs (resistance)
    swing_highs = recent['high'].rolling(window=5, center=True).max()
    resistance_points = recent[recent['high'] == swing_highs]['high'].dropna()
    resistance_levels = sorted(resistance_points.unique().tolist(), reverse=True)[:3]

    # Find swing lows (support)
    swing_lows = recent['low'].rolling(window=5, center=True).min()
    support_points = recent[recent['low'] == swing_lows]['low'].dropna()
    support_levels = sorted(support_points.unique().tolist())[:3]

    return support_levels, resistance_levels


def calculate_entry_sl_tp(
    df: pd.DataFrame,
    trend: str,
    trend_strength: float,
    support_levels: List[float],
    resistance_levels: List[float]
) -> Tuple[str, float, float, float, float]:
    """
    Calculate Entry, Stop Loss, and Take Profit prices

    Returns:
        (side, entry, sl, tp, risk_reward)
    """
    last_close = df['close'].iloc[-1]
    atr = df['atr'].iloc[-1]

    # Default multipliers
    sl_multiplier = 1.5  # SL = 1.5x ATR
    tp_multiplier_min = 2.0  # Min RR = 2:1

    if trend == 'bullish' and trend_strength >= 0.6:
        side = 'long'

        # Entry: Current price or just above recent high
        entry = last_close * 1.001  # 0.1% above current price

        # SL: Below nearest support or 1.5 ATR below entry
        if support_levels:
            sl = min(support_levels) - (atr * 0.5)
        else:
            sl = entry - (atr * sl_multiplier)

        # TP: Above nearest resistance or 2x risk
        risk = entry - sl
        if resistance_levels:
            tp = max(resistance_levels) + (atr * 0.5)
            # Ensure min 2:1 RR
            if (tp - entry) < (risk * tp_multiplier_min):
                tp = entry + (risk * tp_multiplier_min)
        else:
            tp = entry + (risk * tp_multiplier_min)

    elif trend == 'bearish' and trend_strength >= 0.6:
        side = 'short'

        # Entry: Current price or just below recent low
        entry = last_close * 0.999  # 0.1% below current price

        # SL: Above nearest resistance or 1.5 ATR above entry
        if resistance_levels:
            sl = max(resistance_levels) + (atr * 0.5)
        else:
            sl = entry + (atr * sl_multiplier)

        # TP: Below nearest support or 2x risk
        risk = sl - entry
        if support_levels:
            tp = min(support_levels) - (atr * 0.5)
            # Ensure min 2:1 RR
            if (entry - tp) < (risk * tp_multiplier_min):
                tp = entry - (risk * tp_multiplier_min)
        else:
            tp = entry - (risk * tp_multiplier_min)

    else:
        # Sideways or weak trend - no trade
        return 'none', 0.0, 0.0, 0.0, 0.0

    # Calculate Risk/Reward
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    risk_reward = reward / risk if risk > 0 else 0.0

    return side, round(entry, 2), round(sl, 2), round(tp, 2), round(risk_reward, 2)


def calculate_confidence(
    trend: str,
    trend_strength: float,
    df: pd.DataFrame,
    risk_reward: float
) -> float:
    """
    Calculate confidence score (0.0-1.0) based on multiple factors
    """
    confidence = 0.0

    # Factor 1: Trend strength (40% weight)
    confidence += trend_strength * 0.4

    # Factor 2: RSI confirmation (20% weight)
    last_rsi = df['rsi'].iloc[-1]
    if not pd.isna(last_rsi):
        if trend == 'bullish' and 40 <= last_rsi <= 70:
            confidence += 0.2
        elif trend == 'bearish' and 30 <= last_rsi <= 60:
            confidence += 0.2
        elif 30 < last_rsi < 70:
            confidence += 0.1

    # Factor 3: Risk/Reward ratio (20% weight)
    if risk_reward >= 2.5:
        confidence += 0.2
    elif risk_reward >= 2.0:
        confidence += 0.15
    elif risk_reward >= 1.5:
        confidence += 0.1

    # Factor 4: Volume trend (20% weight)
    if 'volume' in df.columns and df['volume'].sum() > 0:
        volume_ma = df['volume'].rolling(window=10).mean()
        last_volume = df['volume'].iloc[-1]
        last_volume_ma = volume_ma.iloc[-1]

        if last_volume > last_volume_ma * 1.2:
            confidence += 0.2
        elif last_volume > last_volume_ma:
            confidence += 0.1

    return round(min(confidence, 1.0), 2)


def get_ai_reasoning(
    ticker: str,
    trend: str,
    side: str,
    entry: float,
    sl: float,
    tp: float,
    confidence: float,
    patterns: List[str],
    df: pd.DataFrame
) -> str:
    """
    Use GPT-4o-mini to generate human-readable reasoning for the setup
    """
    last_close = df['close'].iloc[-1]
    last_rsi = df['rsi'].iloc[-1] if not pd.isna(df['rsi'].iloc[-1]) else None

    prompt = f"""Analyze this trading setup and provide concise reasoning (2-3 sentences):

Symbol: {ticker}
Trend: {trend}
Trade: {side.upper()}
Entry: {entry}
Stop Loss: {sl}
Take Profit: {tp}
Current Price: {last_close}
RSI: {last_rsi:.1f if last_rsi else 'N/A'}
Confidence: {confidence:.2f}
Patterns: {', '.join(patterns) if patterns else 'None detected'}

Explain WHY this is a good setup based on trend, support/resistance, and risk/reward. Be specific and professional."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional trading analyst. Provide concise, actionable reasoning for trade setups."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ OpenAI API error: {e}")
        # Fallback reasoning
        return f"{trend.capitalize()} trend detected with {confidence:.0%} confidence. Entry at {entry} with stop loss at {sl} and target at {tp} provides good risk/reward ratio."


# =====================================================================
# API ENDPOINT
# =====================================================================

@router.post("/analyze-ohlc", response_model=AnalyzeOHLCResponse)
async def analyze_ohlc(request: AnalyzeOHLCRequest):
    """
    Analyze OHLC data and generate trading setup

    Process:
    1. Parse OHLC bars into DataFrame
    2. Calculate technical indicators
    3. Detect trend
    4. Find support/resistance
    5. Calculate Entry/SL/TP
    6. Calculate confidence score
    7. Generate AI reasoning
    """
    try:
        print(f"📊 Analyzing {request.ticker} {request.interval} ({len(request.bars)} bars)")

        # Step 1: Convert to DataFrame
        df = bars_to_dataframe(request.bars)

        # Step 2: Calculate indicators
        df = calculate_indicators(df)

        # Step 3: Detect trend
        trend, trend_strength = detect_trend(df)
        print(f"📈 Trend: {trend} (strength: {trend_strength:.2f})")

        # Step 4: Find support/resistance
        support_levels, resistance_levels = find_support_resistance(df)
        print(f"📍 Support: {support_levels}, Resistance: {resistance_levels}")

        # Step 5: Calculate Entry/SL/TP
        side, entry, sl, tp, risk_reward = calculate_entry_sl_tp(
            df, trend, trend_strength, support_levels, resistance_levels
        )

        if side == 'none':
            raise HTTPException(
                status_code=400,
                detail=f"No clear setup detected. Trend: {trend} with strength {trend_strength:.2f}"
            )

        print(f"✅ Setup: {side} @ {entry}, SL: {sl}, TP: {tp}, RR: {risk_reward:.2f}")

        # Step 6: Calculate confidence
        confidence = calculate_confidence(trend, trend_strength, df, risk_reward)
        print(f"💯 Confidence: {confidence:.2f}")

        # Step 7: Detect patterns (placeholder - can be enhanced)
        patterns_detected = []
        if trend == 'bullish' and trend_strength >= 0.7:
            patterns_detected.append('Higher Highs & Higher Lows')
        elif trend == 'bearish' and trend_strength >= 0.7:
            patterns_detected.append('Lower Highs & Lower Lows')

        # Step 8: Generate AI reasoning
        reasoning = get_ai_reasoning(
            request.ticker, trend, side, entry, sl, tp,
            confidence, patterns_detected, df
        )

        # Step 9: Return analysis
        return AnalyzeOHLCResponse(
            side=side,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            confidence=confidence,
            reasoning=reasoning,
            patterns_detected=patterns_detected,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            trend=trend,
            risk_reward=risk_reward
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
