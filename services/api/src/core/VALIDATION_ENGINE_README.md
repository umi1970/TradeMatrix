# Validation Engine

**Trade Signal Validation System for TradeMatrix.ai**

## Overview

The ValidationEngine is the core component responsible for validating trade signals using a sophisticated multi-metric confidence scoring system. It evaluates signals across 5 key dimensions and calculates an overall confidence score to determine if a trade setup meets the quality threshold.

## Features

- **Multi-Metric Analysis**: Evaluates signals across 5 weighted metrics
- **Confidence Scoring**: Calculates overall confidence score (0.0-1.0)
- **Priority Override Logic**: Implements MR-04 and MR-06 priority strategies
- **Type-Safe**: Full type hints and validation
- **Flexible Configuration**: Customizable thresholds and weights
- **Comprehensive Testing**: Full test suite included

## Metrics & Weighting

| Metric | Weight | Description |
|--------|--------|-------------|
| **EMA Alignment** | 0.25 | Checks trend alignment across EMA 20, 50, and 200 |
| **Pivot Confluence** | 0.20 | Evaluates proximity to key pivot levels |
| **Volume Confirmation** | 0.20 | Compares current volume to average |
| **Candle Structure** | 0.20 | Analyzes candle patterns (hammer, engulfing, doji) |
| **Context Flow** | 0.15 | Evaluates market context and volatility |

**Confidence Threshold**: `> 0.8` = High-Probability Trade

## Installation

The ValidationEngine is part of the core module:

```python
from core.validation_engine import ValidationEngine, validate_trade_signal
```

Or import from the core module:

```python
from core import ValidationEngine, ValidationResult
```

## Usage

### Basic Usage

```python
from core.validation_engine import ValidationEngine

# Initialize engine
engine = ValidationEngine()

# Prepare signal data
signal_data = {
    'price': 18500.0,
    'emas': {
        '20': 18450.0,
        '50': 18400.0,
        '200': 18300.0
    },
    'levels': {
        'pivot': 18480.0,
        'r1': 18550.0,
        's1': 18410.0
    },
    'volume': 15000,
    'avg_volume': 10000,
    'candle': {
        'open': 18490.0,
        'high': 18510.0,
        'low': 18485.0,
        'close': 18505.0
    },
    'context': {
        'trend': 'bullish',
        'volatility': 0.15
    },
    'strategy': 'MR-02'
}

# Validate signal
result = engine.validate_signal(signal_data)

# Check result
if result.is_valid:
    print(f"✓ Valid signal with {result.confidence:.2%} confidence")
    print(f"Breakdown: {result.breakdown}")
else:
    print(f"✗ Invalid signal: {result.notes}")
```

### Convenience Function

```python
from core.validation_engine import validate_trade_signal

# Quick validation
result = validate_trade_signal(signal_data)
print(f"Confidence: {result.confidence:.2%}")
```

### Custom Configuration

```python
# Create engine with custom threshold
config = {
    'threshold': 0.75,  # Lower threshold (default: 0.8)
}

engine = ValidationEngine(config=config)
result = engine.validate_signal(signal_data)
```

### Individual Metric Checks

```python
engine = ValidationEngine()

# Check EMA alignment
ema_score = engine.check_ema_alignment(
    current_price=18500,
    ema_20=18450,
    ema_50=18400,
    ema_200=18300
)

# Check pivot confluence
pivot_score = engine.check_pivot_confluence(
    current_price=18485,
    levels={'pivot': 18480, 'r1': 18550, 's1': 18410}
)

# Check volume
volume_score = engine.check_volume_confirmation(
    current_volume=15000,
    avg_volume=10000
)

# Check candle structure
candle_score = engine.check_candle_structure({
    'open': 18490,
    'high': 18510,
    'low': 18485,
    'close': 18505
})

# Check context
context_score = engine.check_context_flow({
    'trend': 'bullish',
    'volatility': 0.15
})
```

## Signal Data Schema

### Required Fields

```python
signal_data = {
    # Current price
    'price': float,

    # EMA values
    'emas': {
        '20': float,
        '50': float,
        '200': float
    },

    # Pivot levels
    'levels': {
        'pivot': float,
        'r1': float,      # Resistance 1
        's1': float,      # Support 1
        'r2': float,      # Optional
        's2': float       # Optional
    },

    # Volume data
    'volume': float,
    'avg_volume': float,

    # OHLC candle data
    'candle': {
        'open': float,
        'high': float,
        'low': float,
        'close': float
    },

    # Market context
    'context': {
        'trend': str,           # 'bullish', 'bearish', or 'neutral'
        'volatility': float     # 0.0-1.0
    },

    # Strategy type (MR-Series)
    'strategy': str  # 'MR-01' to 'MR-06'
}
```

## Validation Result

The `validate_signal()` method returns a `ValidationResult` object:

```python
@dataclass
class ValidationResult:
    confidence: float              # Overall confidence (0.0-1.0)
    is_valid: bool                 # True if confidence > threshold
    breakdown: Dict[str, float]    # Individual metric scores
    priority_override: bool        # True for MR-04 or MR-06
    notes: Optional[str]           # Additional validation notes
```

### Example Result

```python
ValidationResult(
    confidence=0.89,
    is_valid=True,
    breakdown={
        'ema_alignment': 1.0,
        'pivot_confluence': 0.8,
        'volume_confirmation': 0.9,
        'candle_structure': 0.75,
        'context_flow': 1.0
    },
    priority_override=False,
    notes='High-confidence signal: 89.00%'
)
```

## Strategy Types

```python
from core.validation_engine import StrategyType

# Available strategies
StrategyType.MR_01  # EMA-Cross Reversal
StrategyType.MR_02  # Pivot Rebound
StrategyType.MR_03  # Gap-Open Play
StrategyType.MR_04  # Vortagstief-Reversal (Priority Override)
StrategyType.MR_05  # End-of-Month Rotation
StrategyType.MR_06  # Yesterday Range Reversion (Priority Override)
```

### Priority Override

**MR-04** (Vortagstief-Reversal) and **MR-06** (Yesterday Range Reversion) have priority override status, meaning they can override MR-02 (Pivot Pullback) signals when both are present.

```python
signal_data['strategy'] = 'MR-04'
result = engine.validate_signal(signal_data)

if result.priority_override:
    print("Priority strategy active - overrides pullback setups")
```

## Metric Details

### 1. EMA Alignment (Weight: 0.25)

Checks for trend confirmation across multiple EMAs.

**Perfect Score (1.0):**
- Bullish: Price > EMA20 > EMA50 > EMA200
- Bearish: Price < EMA20 < EMA50 < EMA200

**Partial Score (0.33-0.67):**
- Partial alignment of EMAs

```python
# Perfect bullish alignment
score = engine.check_ema_alignment(
    current_price=18500,
    ema_20=18450,
    ema_50=18400,
    ema_200=18300
)
# Returns: 1.0
```

### 2. Pivot Confluence (Weight: 0.20)

Evaluates proximity to key pivot levels (PP, R1, S1).

**Score Ranges:**
- Within 0.1%: 1.0 (perfect)
- Within 0.5%: 0.8 (good)
- Within 1.0%: 0.6 (moderate)
- Within 2.0%: 0.4 (weak)
- Beyond 2.0%: 0.2 (poor)

```python
# Price very close to pivot
score = engine.check_pivot_confluence(
    current_price=18485,
    levels={'pivot': 18480, 'r1': 18550, 's1': 18410}
)
# Returns: ~1.0 (within 0.1%)
```

### 3. Volume Confirmation (Weight: 0.20)

Compares current volume to average volume.

**Score Ranges:**
- ≥ 2.0x average: 1.0 (exceptional)
- ≥ 1.5x average: 0.9 (strong)
- ≥ 1.2x average: 0.75 (good)
- ≥ 1.0x average: 0.6 (moderate)
- ≥ 0.8x average: 0.4 (weak)
- < 0.8x average: 0.2 (poor)

```python
# 1.5x average volume
score = engine.check_volume_confirmation(
    current_volume=15000,
    avg_volume=10000
)
# Returns: 0.9
```

### 4. Candle Structure (Weight: 0.20)

Analyzes candle patterns for confirmation signals.

**Pattern Recognition:**
- **Hammer**: Long lower wick (>50%), small body (<30%), minimal upper wick (<20%) → 0.95
- **Inverted Hammer**: Long upper wick (>50%), small body (<30%), minimal lower wick (<20%) → 0.95
- **Doji**: Very small body (<10%) → 0.7
- **Strong Bullish/Bearish**: Large body (>70%) → 0.9
- **Moderate Candle**: Medium body (>50%) → 0.75

```python
# Hammer pattern
hammer = {
    'open': 18390,
    'high': 18400,
    'low': 18360,   # Long lower wick
    'close': 18395  # Small body at top
}
score = engine.check_candle_structure(hammer)
# Returns: 0.95
```

### 5. Context Flow (Weight: 0.15)

Evaluates market context and volatility.

**Scoring:**
- Strong trend (bullish/bearish): +0.3
- Neutral trend: +0.1
- Ideal volatility (0.1-0.25): +0.2
- Moderate volatility (0.05-0.1 or 0.25-0.35): +0.1

```python
# Ideal conditions
score = engine.check_context_flow({
    'trend': 'bullish',
    'volatility': 0.15
})
# Returns: 1.0 (0.5 base + 0.3 trend + 0.2 volatility)
```

## Testing

Run the comprehensive test suite:

```bash
cd services/api/src/core
python3 test_validation_engine.py
```

### Test Coverage

1. **Basic Validation** - Complete signal validation
2. **Priority Override** - MR-04 and MR-06 strategies
3. **Weak Signal** - Signal below threshold
4. **Individual Metrics** - Each metric in isolation
5. **Convenience Function** - Quick validation function
6. **Custom Configuration** - Custom threshold testing

## Integration Example

### With MarketDataFetcher

```python
from core import MarketDataFetcher, ValidationEngine

# Fetch market data
fetcher = MarketDataFetcher()
candles = fetcher.fetch_time_series("DAX", "1h", 100)

# Get latest candle
latest = candles[-1]

# Prepare signal data
signal_data = {
    'price': latest['close'],
    'emas': calculate_emas(candles),  # Your EMA calculation
    'levels': calculate_pivots(candles),  # Your pivot calculation
    'volume': latest['volume'],
    'avg_volume': calculate_avg_volume(candles),
    'candle': {
        'open': latest['open'],
        'high': latest['high'],
        'low': latest['low'],
        'close': latest['close']
    },
    'context': analyze_context(candles),
    'strategy': 'MR-02'
}

# Validate
engine = ValidationEngine()
result = engine.validate_signal(signal_data)

if result.is_valid:
    print(f"✓ High-probability trade setup detected!")
    print(f"Confidence: {result.confidence:.2%}")
```

### With AI Agents

```python
# In ChartWatcher agent
from core import ValidationEngine

class ChartWatcher:
    def __init__(self):
        self.validation_engine = ValidationEngine()

    def analyze_chart(self, market_data):
        # Extract signal data from chart
        signal_data = self.extract_signal_data(market_data)

        # Validate signal
        result = self.validation_engine.validate_signal(signal_data)

        # Only send high-confidence signals to SignalBot
        if result.is_valid:
            self.send_to_signal_bot(signal_data, result)
```

## Best Practices

1. **Always validate signals** before trading - Use the ValidationEngine for every signal
2. **Check breakdown** - Inspect individual metric scores to understand weaknesses
3. **Use priority override** - Respect MR-04 and MR-06 priority strategies
4. **Configure thresholds** - Adjust threshold based on your risk tolerance
5. **Log results** - Keep validation results for backtesting and analysis

## Troubleshooting

### Low Confidence Score

If signals consistently score low:

1. **Check EMA Alignment** - Ensure trend is clear
2. **Verify Pivot Levels** - Recalculate pivots if needed
3. **Confirm Volume** - Check if volume is sufficient
4. **Analyze Candles** - Look for clearer patterns
5. **Review Context** - Ensure volatility is moderate

### Priority Override Not Working

```python
# Make sure strategy is set correctly
signal_data['strategy'] = 'MR-04'  # or 'MR-06'

result = engine.validate_signal(signal_data)
assert result.priority_override == True
```

### Custom Weights Not Applied

```python
# Custom weights must sum to 1.0
custom_weights = {
    'ema_alignment': 0.30,
    'pivot_confluence': 0.25,
    'volume_confirmation': 0.20,
    'candle_structure': 0.15,
    'context_flow': 0.10
}

engine = ValidationEngine(config={'weights': custom_weights})
```

## API Reference

### ValidationEngine

```python
class ValidationEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None)
    def calculate_confidence(self, signal_data: Dict[str, Any]) -> float
    def validate_signal(self, signal_data: Dict[str, Any]) -> ValidationResult
    def check_ema_alignment(self, current_price, ema_20, ema_50, ema_200) -> float
    def check_pivot_confluence(self, current_price, levels) -> float
    def check_volume_confirmation(self, current_volume, avg_volume) -> float
    def check_candle_structure(self, candle) -> float
    def check_context_flow(self, context) -> float
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    confidence: float
    is_valid: bool
    breakdown: Dict[str, float]
    priority_override: bool
    notes: Optional[str] = None
```

### Helper Functions

```python
def validate_trade_signal(signal_data: Dict[str, Any]) -> ValidationResult
```

## Contributing

When modifying the ValidationEngine:

1. Update type hints
2. Add comprehensive docstrings
3. Update tests in `test_validation_engine.py`
4. Update this README
5. Test all scenarios thoroughly

## Related Documentation

- [Trading Rules](../../../../docs/04_Trading_Rules.md) - MR-Series strategies
- [Validation Metrics](../../../../docs/05_Validation_Engine.md) - Metric weighting
- [Project Overview](../../../../docs/PROJECT_OVERVIEW.md) - Overall architecture
- [MarketDataFetcher](./README.md) - Market data integration

## License

© 2025 TradeMatrix.ai - All rights reserved
