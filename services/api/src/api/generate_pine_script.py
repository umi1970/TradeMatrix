"""
Pine Script Generator API

Generates TradingView Pine Script code for setup monitoring.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()


class GeneratePineScriptRequest(BaseModel):
    """Request payload for Pine Script generation"""
    setup_id: str = Field(..., description="Setup UUID")
    ticker: str = Field(..., description="Symbol ticker")
    side: str = Field(..., description="Trade direction: long or short")
    entry_price: float = Field(..., description="Entry price")
    stop_loss: float = Field(..., description="Stop loss price")
    take_profit: float = Field(..., description="Take profit price")


class GeneratePineScriptResponse(BaseModel):
    """Pine Script generation response"""
    setup_id: str
    pine_script: str
    webhook_url: str


def generate_pine_script_code(
    setup_id: str,
    ticker: str,
    side: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    webhook_url: str
) -> str:
    """
    Generate Pine Script v5 code for setup monitoring

    Features:
    - Draws Entry/SL/TP lines on chart
    - Labels with prices
    - Alerts when price crosses levels
    - Sends webhook with JSON payload
    """

    setup_label = side.upper()
    entry_color = 'color.green' if side == 'long' else 'color.orange'
    zone_color = 'color.new(color.green, 95)' if side == 'long' else 'color.new(color.orange, 95)'

    # Alert conditions based on trade direction
    if side == 'long':
        sl_condition = 'close <= stopLoss'
        tp_condition = 'close >= takeProfit'
    else:  # short
        sl_condition = 'close >= stopLoss'
        tp_condition = 'close <= takeProfit'

    # Calculate Risk/Reward
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    rr_ratio = reward / risk if risk > 0 else 0.0

    pine_code = f"""//@version=5
indicator("TradeMatrix: {ticker} {setup_label}", overlay=true)

// ====================================
// TradeMatrix AI-Generated Setup
// ====================================
// Symbol: {ticker}
// Setup Type: {setup_label}
// Entry: {entry_price}
// Stop Loss: {stop_loss}
// Take Profit: {take_profit}
// Risk:Reward: {rr_ratio:.1f}:1
// Setup ID: {setup_id}
// ====================================

// Setup levels
var float entryPrice = {entry_price}
var float stopLoss = {stop_loss}
var float takeProfit = {take_profit}

// Calculate R:R dynamically
var float risk = math.abs(entryPrice - stopLoss)
var float reward = math.abs(takeProfit - entryPrice)
var float calculatedRR = reward / risk

// Draw horizontal lines (persistent across bars)
var line entryLine = na
var line slLine = na
var line tpLine = na

if (bar_index == last_bar_index - 50)
    // Entry line
    entryLine := line.new(bar_index, entryPrice, bar_index + 100, entryPrice,
                          color={entry_color},
                          width=2,
                          style=line.style_dashed)

    // Stop Loss line
    slLine := line.new(bar_index, stopLoss, bar_index + 100, stopLoss,
                       color=color.red,
                       width=2,
                       style=line.style_dashed)

    // Take Profit line
    tpLine := line.new(bar_index, takeProfit, bar_index + 100, takeProfit,
                       color=color.blue,
                       width=2,
                       style=line.style_dashed)

// Labels (show once)
if (bar_index == last_bar_index - 25)
    label.new(bar_index, entryPrice, "ENTRY: $" + str.tostring(entryPrice, "#.##"),
              style=label.style_label_left,
              color={entry_color},
              textcolor=color.white,
              size=size.normal)

    label.new(bar_index, stopLoss, "STOP: $" + str.tostring(stopLoss, "#.##"),
              style=label.style_label_left,
              color=color.red,
              textcolor=color.white,
              size=size.normal)

    label.new(bar_index, takeProfit, "TARGET: $" + str.tostring(takeProfit, "#.##") + " (R:R " + str.tostring(calculatedRR, "#.#") + ")",
              style=label.style_label_left,
              color=color.blue,
              textcolor=color.white,
              size=size.normal)

// Background shading for setup zone
var box setupZone = na
if (bar_index == last_bar_index - 50)
    setupZone := box.new(bar_index, stopLoss, bar_index + 100, takeProfit,
                         border_color=color.new(color.gray, 70),
                         bgcolor={zone_color})

// ====================================
// ALERTS (for webhook integration)
// ====================================

// Entry hit alert
entryHit = ta.cross(close, entryPrice)
if (entryHit)
    alert('{{"setup_id": "{setup_id}", "event": "entry_hit", "price": ' + str.tostring(close, "#.####") + ', "symbol": "{ticker}"}}',
          alert.freq_once_per_bar)

// Stop Loss hit alert
slHit = {sl_condition}
if (slHit)
    alert('{{"setup_id": "{setup_id}", "event": "sl_hit", "price": ' + str.tostring(close, "#.####") + ', "symbol": "{ticker}"}}',
          alert.freq_once_per_bar)

// Take Profit hit alert
tpHit = {tp_condition}
if (tpHit)
    alert('{{"setup_id": "{setup_id}", "event": "tp_hit", "price": ' + str.tostring(close, "#.####") + ', "symbol": "{ticker}"}}',
          alert.freq_once_per_bar)

// Plot invisible price for alertcondition (required by some TradingView versions)
plot(close, display=display.none)

// ====================================
// Setup Info Label
// ====================================

if (bar_index == last_bar_index)
    label.new(bar_index, high, "TradeMatrix {setup_label}\\nRR: " + str.tostring(calculatedRR, "#.#") + ":1",
              style=label.style_label_down,
              color=color.new(color.yellow, 20),
              textcolor=color.black,
              size=size.small)

// ====================================
// INSTRUCTIONS
// ====================================
// 1. Copy this entire code
// 2. In TradingView, open {ticker} chart
// 3. Click "Pine Editor" (bottom panel)
// 4. Paste code → "Add to Chart"
// 5. Create alerts for entryHit, slHit, tpHit
// 6. Set webhook URL: {webhook_url}
// 7. TradeMatrix will auto-update setup status!
// ===================================="""

    return pine_code


@router.post("/generate-pine-script", response_model=GeneratePineScriptResponse)
async def generate_pine_script(request: GeneratePineScriptRequest):
    """
    Generate Pine Script code for TradingView setup monitoring

    Returns:
        Pine Script code with embedded setup_id for webhook tracking
    """
    try:
        # Get webhook URL from environment or use default
        import os
        app_url = os.getenv('NEXT_PUBLIC_APP_URL', 'http://localhost:3000')
        webhook_url = f"{app_url}/api/webhooks/tradingview-monitor"

        # Generate Pine Script code
        pine_script = generate_pine_script_code(
            setup_id=request.setup_id,
            ticker=request.ticker,
            side=request.side,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            webhook_url=webhook_url
        )

        return GeneratePineScriptResponse(
            setup_id=request.setup_id,
            pine_script=pine_script,
            webhook_url=webhook_url
        )

    except Exception as e:
        print(f"❌ Pine Script generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Pine Script: {str(e)}"
        )
