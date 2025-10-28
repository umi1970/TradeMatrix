# AI Analyzer

Der Analyzer berechnet Indikatoren für alle Assets und übergibt sie an die Validation Engine.

### Implemented Indicators
- EMA (20, 50, 200)
- RSI (14)
- MACD (12, 26, 9)
- ATR (14)
- Bollinger Bands (20, 2)
- Ichimoku Cloud (9, 26, 52, 26)
- Pivot Points (Daily & Weekly)

### Output Schema
```json
{
  "asset": "DAX",
  "timeframe": "5m",
  "ema": { "20": 24210, "50": 24260, "200": 24380 },
  "pivot": { "pp": 24300, "r1": 24380, "s1": 24197 },
  "rsi": 46.3,
  "volume": 1.24,
  "signal": "neutral"
}
