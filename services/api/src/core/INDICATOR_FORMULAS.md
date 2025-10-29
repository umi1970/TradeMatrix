# Technical Indicator Formulas Reference

**TradeMatrix.ai - Complete Formula Documentation**

---

## Moving Averages

### Simple Moving Average (SMA)

**Formula:**
```
SMA = (P₁ + P₂ + P₃ + ... + Pₙ) / n

where:
- P = Price at each period
- n = Number of periods
```

**Example (3-period SMA):**
```
Prices: [10, 11, 12, 13, 14]

SMA₃ = (10 + 11 + 12) / 3 = 11.00
SMA₄ = (11 + 12 + 13) / 3 = 12.00
SMA₅ = (12 + 13 + 14) / 3 = 13.00
```

**Characteristics:**
- Equal weight to all periods
- Smooth price action
- Lagging indicator
- Good for trend identification

---

### Exponential Moving Average (EMA)

**Formula:**
```
EMAₜ = Priceₜ × k + EMAₜ₋₁ × (1 - k)

where:
k = 2 / (period + 1)  (smoothing constant)

First EMA value = SMA of first n periods
```

**Example (5-period EMA):**
```
k = 2 / (5 + 1) = 0.3333

Period 1-5: EMA₅ = SMA₅ = 12.00
Period 6: EMA₆ = 13 × 0.3333 + 12.00 × 0.6667 = 12.33
Period 7: EMA₇ = 14 × 0.3333 + 12.33 × 0.6667 = 12.89
```

**Characteristics:**
- More weight to recent prices
- More responsive than SMA
- Still lagging but less than SMA
- Popular periods: 20, 50, 200

---

## Momentum Indicators

### Relative Strength Index (RSI)

**Formula:**
```
RS = Average Gain / Average Loss

RSI = 100 - (100 / (1 + RS))

where:
Average Gain = EMA of upward price changes
Average Loss = EMA of downward price changes
```

**Step-by-Step Calculation:**

1. **Calculate price changes:**
   ```
   Change = Priceₜ - Priceₜ₋₁
   ```

2. **Separate gains and losses:**
   ```
   Gain = Change if Change > 0, else 0
   Loss = -Change if Change < 0, else 0
   ```

3. **Calculate first averages (SMA):**
   ```
   First Avg Gain = sum(Gains[1:14]) / 14
   First Avg Loss = sum(Losses[1:14]) / 14
   ```

4. **Calculate subsequent averages (EMA style):**
   ```
   Avg Gain = (Previous Avg Gain × 13 + Current Gain) / 14
   Avg Loss = (Previous Avg Loss × 13 + Current Loss) / 14
   ```

5. **Calculate RSI:**
   ```
   RS = Avg Gain / Avg Loss
   RSI = 100 - (100 / (1 + RS))
   ```

**Example:**
```
Price changes: +2, +3, -1, +2, -3, +4, ...

Gains: 2, 3, 0, 2, 0, 4, ...
Losses: 0, 0, 1, 0, 3, 0, ...

After 14 periods:
Avg Gain = 1.5
Avg Loss = 0.8
RS = 1.5 / 0.8 = 1.875
RSI = 100 - (100 / (1 + 1.875)) = 65.22
```

**Interpretation:**
- RSI > 70: Overbought (potential reversal down)
- RSI < 30: Oversold (potential reversal up)
- RSI = 50: Neutral

---

### Moving Average Convergence Divergence (MACD)

**Formula:**
```
MACD Line = EMA₁₂ - EMA₂₆
Signal Line = EMA₉(MACD Line)
Histogram = MACD Line - Signal Line
```

**Step-by-Step:**

1. **Calculate fast EMA:**
   ```
   Fast EMA = EMA(close, 12)
   ```

2. **Calculate slow EMA:**
   ```
   Slow EMA = EMA(close, 26)
   ```

3. **Calculate MACD line:**
   ```
   MACD = Fast EMA - Slow EMA
   ```

4. **Calculate signal line:**
   ```
   Signal = EMA(MACD, 9)
   ```

5. **Calculate histogram:**
   ```
   Histogram = MACD - Signal
   ```

**Example:**
```
Price = 100
EMA₁₂ = 101.5
EMA₂₆ = 100.8

MACD = 101.5 - 100.8 = 0.7
Signal = EMA₉(MACD) = 0.5
Histogram = 0.7 - 0.5 = 0.2
```

**Interpretation:**
- MACD > Signal: Bullish momentum
- MACD < Signal: Bearish momentum
- Crossovers indicate trend changes
- Histogram shows momentum strength

---

## Volatility Indicators

### Bollinger Bands

**Formula:**
```
Middle Band = SMA(close, 20)
Upper Band = Middle Band + (2 × σ)
Lower Band = Middle Band - (2 × σ)

where:
σ = Standard Deviation of last 20 closes
```

**Standard Deviation Calculation:**
```
σ = √(Σ(Priceᵢ - SMA)² / n)
```

**Step-by-Step:**

1. **Calculate SMA:**
   ```
   SMA₂₀ = (P₁ + P₂ + ... + P₂₀) / 20
   ```

2. **Calculate variance:**
   ```
   Variance = Σ(Pᵢ - SMA)² / 20
   ```

3. **Calculate standard deviation:**
   ```
   σ = √Variance
   ```

4. **Calculate bands:**
   ```
   Upper = SMA + (2 × σ)
   Middle = SMA
   Lower = SMA - (2 × σ)
   ```

**Example:**
```
Prices (last 20): [100, 101, 102, ..., 105]
SMA₂₀ = 102.5
σ = 2.3

Upper = 102.5 + (2 × 2.3) = 107.1
Middle = 102.5
Lower = 102.5 - (2 × 2.3) = 97.9
```

**Interpretation:**
- Price near upper band: Overbought
- Price near lower band: Oversold
- Band width indicates volatility
- Squeeze (narrow bands) precedes breakout

---

### Average True Range (ATR)

**Formula:**
```
True Range (TR) = max of:
  1. High - Low (current period range)
  2. |High - Close₋₁| (high vs previous close)
  3. |Low - Close₋₁| (low vs previous close)

ATR = EMA(TR, 14)
```

**Step-by-Step:**

1. **Calculate True Range for each period:**
   ```
   TR₁ = High₁ - Low₁  (first period)

   For subsequent periods:
   HL = High - Low
   HC = |High - Close₋₁|
   LC = |Low - Close₋₁|
   TR = max(HL, HC, LC)
   ```

2. **Calculate ATR (EMA of TR):**
   ```
   First ATR = average of first 14 TRs
   Subsequent ATR = (Previous ATR × 13 + Current TR) / 14
   ```

**Example:**
```
Period 1: H=110, L=105, C=108
  TR = 110 - 105 = 5

Period 2: H=112, L=107, C_prev=108
  HL = 112 - 107 = 5
  HC = |112 - 108| = 4
  LC = |107 - 108| = 1
  TR = max(5, 4, 1) = 5

After 14 periods:
ATR = average(5, 5, 6, 4, ...) = 5.2
```

**Uses:**
- Volatility measurement
- Stop loss placement (e.g., 2× ATR)
- Position sizing
- Breakout confirmation

---

## Trend Indicators

### Ichimoku Cloud

**Complete Formula Set:**

```
1. Tenkan-sen (Conversion Line)
   = (Highest High₉ + Lowest Low₉) / 2

2. Kijun-sen (Base Line)
   = (Highest High₂₆ + Lowest Low₂₆) / 2

3. Senkou Span A (Leading Span A)
   = (Tenkan-sen + Kijun-sen) / 2
   [Plotted 26 periods ahead]

4. Senkou Span B (Leading Span B)
   = (Highest High₅₂ + Lowest Low₅₂) / 2
   [Plotted 26 periods ahead]

5. Chikou Span (Lagging Span)
   = Close price
   [Plotted 26 periods back]
```

**Step-by-Step:**

1. **Tenkan-sen (9-period):**
   ```
   Find highest high in last 9 periods: HH₉ = 115
   Find lowest low in last 9 periods: LL₉ = 105
   Tenkan = (115 + 105) / 2 = 110
   ```

2. **Kijun-sen (26-period):**
   ```
   Find HH₂₆ = 120
   Find LL₂₆ = 100
   Kijun = (120 + 100) / 2 = 110
   ```

3. **Senkou Span A:**
   ```
   Span A = (Tenkan + Kijun) / 2
   Span A = (110 + 110) / 2 = 110
   Plot 26 periods ahead
   ```

4. **Senkou Span B (52-period):**
   ```
   Find HH₅₂ = 125
   Find LL₅₂ = 95
   Span B = (125 + 95) / 2 = 110
   Plot 26 periods ahead
   ```

5. **Chikou Span:**
   ```
   Chikou = Current Close
   Plot 26 periods back
   ```

**Interpretation:**
- Price above cloud: Bullish trend
- Price below cloud: Bearish trend
- Price in cloud: Consolidation/Neutral
- Tenkan/Kijun cross: Trading signal
- Cloud color (A vs B): Trend strength
- Cloud thickness: Support/Resistance strength

---

## Support/Resistance

### Pivot Points (Standard Method)

**Formula:**
```
Pivot Point (PP) = (High + Low + Close) / 3

Resistance Levels:
R1 = (2 × PP) - Low
R2 = PP + (High - Low)
R3 = High + 2 × (PP - Low)

Support Levels:
S1 = (2 × PP) - High
S2 = PP - (High - Low)
S3 = Low - 2 × (High - PP)
```

**Step-by-Step Calculation:**

Using previous day/period data:
```
High = 1.2050
Low = 1.2000
Close = 1.2030
```

1. **Calculate Pivot Point:**
   ```
   PP = (1.2050 + 1.2000 + 1.2030) / 3
   PP = 3.6080 / 3
   PP = 1.2027
   ```

2. **Calculate Resistance Levels:**
   ```
   R1 = (2 × 1.2027) - 1.2000
   R1 = 2.4054 - 1.2000
   R1 = 1.2054

   R2 = 1.2027 + (1.2050 - 1.2000)
   R2 = 1.2027 + 0.0050
   R2 = 1.2077

   R3 = 1.2050 + 2 × (1.2027 - 1.2000)
   R3 = 1.2050 + 2 × 0.0027
   R3 = 1.2050 + 0.0054
   R3 = 1.2104
   ```

3. **Calculate Support Levels:**
   ```
   S1 = (2 × 1.2027) - 1.2050
   S1 = 2.4054 - 1.2050
   S1 = 1.2004

   S2 = 1.2027 - (1.2050 - 1.2000)
   S2 = 1.2027 - 0.0050
   S2 = 1.1977

   S3 = 1.2000 - 2 × (1.2050 - 1.2027)
   S3 = 1.2000 - 2 × 0.0023
   S3 = 1.2000 - 0.0046
   S3 = 1.1954
   ```

**Result:**
```
R3: 1.2104
R2: 1.2077
R1: 1.2054
PP: 1.2027  ← Pivot Point
S1: 1.2004
S2: 1.1977
S3: 1.1954
```

**Trading Logic:**
```
If price > PP:
  - Target R1, then R2, then R3
  - Support at PP

If price < PP:
  - Target S1, then S2, then S3
  - Resistance at PP

Strong moves:
  - Break above R1 → target R2
  - Break below S1 → target S2
```

---

## Trend Detection

### EMA Alignment Method

**Perfect Bullish Alignment:**
```
Price > EMA₂₀ > EMA₅₀ > EMA₂₀₀
```

**Perfect Bearish Alignment:**
```
Price < EMA₂₀ < EMA₅₀ < EMA₂₀₀
```

**Example:**
```
Bullish:
Price = 100
EMA₂₀ = 98
EMA₅₀ = 95
EMA₂₀₀ = 90
→ BULLISH TREND

Bearish:
Price = 90
EMA₂₀ = 92
EMA₅₀ = 95
EMA₂₀₀ = 100
→ BEARISH TREND
```

### Crossover Detection

**Golden Cross (Bullish):**
```
EMA₅₀ crosses above EMA₂₀₀
```

**Death Cross (Bearish):**
```
EMA₅₀ crosses below EMA₂₀₀
```

**Detection Logic:**
```
If EMA₅₀[t] > EMA₂₀₀[t] AND EMA₅₀[t-1] <= EMA₂₀₀[t-1]:
  → Golden Cross (Bullish signal)

If EMA₅₀[t] < EMA₂₀₀[t] AND EMA₅₀[t-1] >= EMA₂₀₀[t-1]:
  → Death Cross (Bearish signal)
```

---

## Combined Indicator Strategies

### Strategy 1: Trend Following

**Rules:**
```
LONG Entry:
1. EMA₂₀ > EMA₅₀ > EMA₂₀₀ (bullish alignment)
2. RSI < 70 (not overbought)
3. MACD > Signal (bullish momentum)
4. Price > BB Middle (uptrend confirmation)

SHORT Entry:
1. EMA₂₀ < EMA₅₀ < EMA₂₀₀ (bearish alignment)
2. RSI > 30 (not oversold)
3. MACD < Signal (bearish momentum)
4. Price < BB Middle (downtrend confirmation)
```

### Strategy 2: Mean Reversion

**Rules:**
```
BUY Signal:
1. Price < BB Lower (oversold)
2. RSI < 30 (oversold)
3. Price near support (S1 or S2)

SELL Signal:
1. Price > BB Upper (overbought)
2. RSI > 70 (overbought)
3. Price near resistance (R1 or R2)
```

### Strategy 3: Breakout

**Rules:**
```
Breakout LONG:
1. BB width < 20th percentile (low volatility)
2. ATR increasing (volatility expansion)
3. Price breaks above BB Upper
4. Volume confirmation (if available)

Breakout SHORT:
1. BB width < 20th percentile (low volatility)
2. ATR increasing (volatility expansion)
3. Price breaks below BB Lower
4. Volume confirmation (if available)
```

---

## Risk Management Formulas

### Position Sizing with ATR

**Formula:**
```
Position Size = (Account Risk) / (ATR × ATR Multiplier)

where:
Account Risk = Account Balance × Risk %
ATR Multiplier = typically 2.0
```

**Example:**
```
Account Balance = $10,000
Risk per trade = 1% = $100
Current ATR = $5
ATR Multiplier = 2

Stop Loss Distance = ATR × Multiplier = $5 × 2 = $10
Position Size = $100 / $10 = 10 shares
```

### Stop Loss Placement

**ATR-Based Stop Loss:**
```
Long Position:
Stop Loss = Entry Price - (ATR × 2)

Short Position:
Stop Loss = Entry Price + (ATR × 2)
```

**Pivot-Based Stop Loss:**
```
Long Position:
Stop Loss = S1 or S2 (below entry)

Short Position:
Stop Loss = R1 or R2 (above entry)
```

---

## References

1. **Wilder, J. W.** (1978). *New Concepts in Technical Trading Systems*
   - Original RSI and ATR formulas

2. **Bollinger, J.** (1992). *Bollinger on Bollinger Bands*
   - Bollinger Bands methodology

3. **Appel, G.** (2005). *Technical Analysis: Power Tools for Active Investors*
   - MACD development and applications

4. **Murphy, J. J.** (1999). *Technical Analysis of the Financial Markets*
   - Comprehensive TA reference

5. **Hosoda, G.** (1930s-1960s). *Ichimoku Kinko Hyo*
   - Ichimoku Cloud system

---

**Last Updated:** 2025-10-29
**Version:** 1.0.0
**Author:** TradeMatrix.ai
