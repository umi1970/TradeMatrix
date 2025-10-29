# TradeAnalyzer - Phase 2 Integration Module

**Complete trade analysis workflow combining all Phase 2 components**

## Overview

The `TradeAnalyzer` is the main integration module that orchestrates the entire trade analysis workflow from market data fetching to risk management. It combines four core Phase 2 modules:

1. **MarketDataFetcher** - Fetches OHLCV data from Twelve Data API
2. **TechnicalIndicators** - Calculates EMAs, RSI, MACD, Bollinger Bands, ATR, Ichimoku
3. **ValidationEngine** - Validates trade signals with confidence scoring
4. **RiskCalculator** - Calculates position sizing and risk parameters

## Quick Start

```python
from core.trade_analyzer import create_analyzer

# Create analyzer with 10,000 EUR account, 1% risk
analyzer = create_analyzer(
    account_balance=10000.0,
    risk_per_trade=0.01
)

# Complete analysis with risk calculation
analysis = analyzer.get_complete_analysis(
    symbol="DAX",
    strategy_id="MR-02",
    entry_price=19500.0,
    stop_loss=19450.0,
    position_type='long',
    risk_reward_ratio=2.0
)

# Check if signal is valid
if analysis['signal']['is_valid']:
    print(f"Valid signal with {analysis['signal']['confidence']:.1%} confidence")
    print(f"Position size: {analysis['trade_plan']['position_size']:.2f} units")
    print(f"Risk: {analysis['trade_plan']['risk_amount']:.2f} EUR")
```

## Key Features

### 1. Complete Analysis Workflow

Single method call performs entire workflow:
- Fetch market data
- Calculate all indicators
- Validate trade signal
- Calculate risk parameters

### 2. Flexible Usage

Use individual methods for custom workflows:

```python
# Step 1: Fetch data and calculate indicators
data = analyzer.fetch_and_calculate_indicators("DAX", "1h", 300)

# Step 2: Validate trade setup
validation = analyzer.validate_trade_setup(
    symbol="DAX",
    strategy_id="MR-02",
    indicators=data['indicators'],
    current_price=data['current_price']
)

# Step 3: Calculate trade parameters
trade_plan = analyzer.calculate_trade_params(
    entry_price=19500.0,
    stop_loss=19450.0,
    position_type='long'
)
```

### 3. Multiple Product Types

Supports different trading products:
- **CFD** - Contract for Difference (default)
- **KO** - Knock-Out Certificates (with KO threshold calculation)
- **Futures** - Futures contracts

### 4. Comprehensive Output

Returns complete analysis with:
- Market data (current price, candles, interval)
- Technical indicators (EMAs, RSI, MACD, BB, ATR, Ichimoku, Pivots)
- Signal validation (confidence score, breakdown, notes)
- Trade plan (entry, SL, TP, position size, risk, leverage)
- Summary (quick reference with recommendation)

## API Reference

### Main Class: `TradeAnalyzer`

#### Initialization

```python
TradeAnalyzer(
    supabase_client=None,        # Supabase client (defaults to admin)
    twelve_data_api_key=None,    # Twelve Data API key (defaults to env var)
    account_balance=10000.0,     # Account balance in EUR
    risk_per_trade=0.01          # Risk per trade (1%)
)
```

#### Methods

##### `get_complete_analysis()`

Perform complete analysis from data fetching to risk calculation.

```python
analysis = analyzer.get_complete_analysis(
    symbol="DAX",                # Trading symbol
    strategy_id="MR-02",         # Strategy type (MR-01 to MR-06)
    interval="1h",               # Time interval (default: "1h")
    outputsize=300,              # Number of candles (default: 300)
    entry_price=None,            # Optional: Entry price for risk calc
    stop_loss=None,              # Optional: Stop loss for risk calc
    position_type=None,          # Optional: 'long' or 'short'
    risk_reward_ratio=2.0,       # Risk-reward ratio (default: 2.0)
    product_type='CFD'           # Product type (default: 'CFD')
)
```

**Returns:**
```python
{
    'symbol': 'DAX',
    'strategy': 'MR-02',
    'timestamp': '2025-10-29T10:30:00',
    'market_data': {
        'current_price': 19500.0,
        'interval': '1h',
        'candle_count': 300,
        'latest_candle': {...}
    },
    'indicators': {
        'ema': {'20': 19450.0, '50': 19400.0, '200': 19300.0},
        'rsi': 65.5,
        'macd': {...},
        'bollinger_bands': {...},
        'atr': 45.2,
        'pivot_points': {...},
        'trend': 'bullish',
        'alignment': {...}
    },
    'signal': {
        'confidence': 0.85,
        'is_valid': True,
        'breakdown': {...},
        'priority_override': False,
        'notes': '...'
    },
    'trade_plan': {
        'entry': 19500.0,
        'stop_loss': 19450.0,
        'take_profit': 19600.0,
        'position_size': 2.0,
        'risk_amount': 100.0,
        'risk_percentage': 1.0,
        'leverage': 3.9,
        'is_valid': True,
        'warnings': []
    },
    'summary': {
        'recommendation': 'TRADE',
        'confidence': '85.0%',
        'risk_amount': '100.00 EUR',
        ...
    }
}
```

##### `analyze_symbol()`

Quick analysis without risk calculation.

```python
analysis = analyzer.analyze_symbol(
    symbol="DAX",
    strategy_id="MR-02"
)
# Returns same structure but trade_plan is None
```

##### `fetch_and_calculate_indicators()`

Fetch market data and calculate all technical indicators.

```python
data = analyzer.fetch_and_calculate_indicators(
    symbol="DAX",
    interval="1h",
    outputsize=300
)
```

**Returns:**
```python
{
    'symbol': 'DAX',
    'interval': '1h',
    'candles': [...],          # Raw OHLCV data
    'indicators': {...},       # All technical indicators
    'current_price': 19500.0,
    'timestamp': '...',
    'candle_count': 300
}
```

##### `validate_trade_setup()`

Validate a trade setup using the ValidationEngine.

```python
result = analyzer.validate_trade_setup(
    symbol="DAX",
    strategy_id="MR-02",
    indicators=indicators,     # From fetch_and_calculate_indicators()
    current_price=19500.0,
    current_candle=None        # Optional OHLC dict
)
```

**Returns:** `ValidationResult` object with confidence score and breakdown.

##### `calculate_trade_params()`

Calculate complete trade parameters using RiskCalculator.

```python
params = analyzer.calculate_trade_params(
    entry_price=19500.0,
    stop_loss=19450.0,
    position_type='long',
    risk_reward_ratio=2.0,
    product_type='CFD',
    commission_percentage=0.0
)
```

**Returns:** Complete trade plan dictionary.

### Convenience Function: `create_analyzer()`

Quick factory function to create analyzer with defaults.

```python
from core.trade_analyzer import create_analyzer

analyzer = create_analyzer(
    account_balance=10000.0,
    risk_per_trade=0.01,
    twelve_data_api_key=None
)
```

## Usage Examples

### Example 1: Basic Analysis

```python
# Just check if there's a valid signal
analyzer = create_analyzer()
analysis = analyzer.analyze_symbol("DAX", "MR-02")

if analysis['signal']['is_valid']:
    print(f"✓ Valid signal: {analysis['signal']['confidence']:.1%} confidence")
    print(f"  Trend: {analysis['indicators']['trend']}")
    print(f"  Recommendation: {analysis['summary']['recommendation']}")
```

### Example 2: Complete Analysis with Trade Plan

```python
# Full analysis with risk calculation
analyzer = create_analyzer(account_balance=10000.0)

analysis = analyzer.get_complete_analysis(
    symbol="DAX",
    strategy_id="MR-02",
    entry_price=19500.0,
    stop_loss=19450.0,
    position_type='long',
    risk_reward_ratio=2.0
)

if analysis['signal']['is_valid'] and analysis['trade_plan']['is_valid']:
    plan = analysis['trade_plan']
    print(f"✓ Valid trade setup!")
    print(f"  Entry: {plan['entry']:.2f}")
    print(f"  SL: {plan['stop_loss']:.2f}")
    print(f"  TP: {plan['take_profit']:.2f}")
    print(f"  Position: {plan['position_size']:.2f} units")
    print(f"  Risk: {plan['risk_amount']:.2f} EUR ({plan['risk_percentage']:.2f}%)")
```

### Example 3: Short Position

```python
# Analyze short position
analysis = analyzer.get_complete_analysis(
    symbol="NASDAQ",
    strategy_id="MR-01",
    entry_price=18000.0,
    stop_loss=18100.0,   # Above entry for short
    position_type='short'
)
```

### Example 4: KO Product

```python
# Analyze with KO certificate
analysis = analyzer.get_complete_analysis(
    symbol="DAX",
    strategy_id="MR-04",
    entry_price=19500.0,
    stop_loss=19450.0,
    position_type='long',
    product_type='KO'
)

if analysis['trade_plan'] and analysis['trade_plan']['ko_data']:
    ko = analysis['trade_plan']['ko_data']
    print(f"KO Threshold: {ko['ko_threshold']:.2f}")
    print(f"KO Leverage: {ko['leverage']:.2f}x")
```

### Example 5: Step-by-Step Custom Workflow

```python
# Build custom workflow
analyzer = create_analyzer()

# Step 1: Get data
data = analyzer.fetch_and_calculate_indicators("DAX", "1h", 300)

# Step 2: Check trend
if data['indicators']['trend'] == 'bullish':
    # Step 3: Validate signal
    validation = analyzer.validate_trade_setup(
        symbol="DAX",
        strategy_id="MR-02",
        indicators=data['indicators'],
        current_price=data['current_price']
    )

    if validation.is_valid:
        # Step 4: Calculate risk
        trade_plan = analyzer.calculate_trade_params(
            entry_price=19500.0,
            stop_loss=19450.0,
            position_type='long'
        )

        print(f"Position size: {trade_plan['position_size']:.2f}")
```

## Error Handling

The module defines custom exceptions:

```python
from core.trade_analyzer import (
    TradeAnalyzerError,
    InsufficientDataError
)

try:
    analysis = analyzer.get_complete_analysis("DAX", "MR-02")
except InsufficientDataError as e:
    print(f"Not enough data: {e}")
except TradeAnalyzerError as e:
    print(f"Analysis error: {e}")
```

## Testing

Run the test suite:

```bash
cd services/api/src/core
pytest test_trade_analyzer.py -v
```

Run specific test class:

```bash
pytest test_trade_analyzer.py::TestGetCompleteAnalysis -v
```

## Examples Script

Run the comprehensive examples:

```bash
cd services/api/src/core
python3 example_trade_analyzer.py
```

The script includes 6 detailed examples:
1. Basic Analysis (No Trade Plan)
2. Complete Analysis (With Trade Plan)
3. Short Position Analysis
4. KO Product Analysis
5. Step-by-Step Analysis
6. Multiple Strategy Comparison

## Integration with Other Modules

### Use with FastAPI

```python
from fastapi import APIRouter
from core.trade_analyzer import create_analyzer

router = APIRouter()
analyzer = create_analyzer()

@router.get("/analyze/{symbol}")
def analyze_symbol(symbol: str, strategy: str):
    analysis = analyzer.analyze_symbol(symbol, strategy)
    return analysis
```

### Use with Celery Tasks

```python
from celery import task
from core.trade_analyzer import create_analyzer

@task
def analyze_trade_setup(symbol, strategy_id, entry, stop_loss):
    analyzer = create_analyzer()
    analysis = analyzer.get_complete_analysis(
        symbol=symbol,
        strategy_id=strategy_id,
        entry_price=entry,
        stop_loss=stop_loss,
        position_type='long'
    )

    # Save to database or send notification
    if analysis['signal']['is_valid']:
        notify_valid_signal(analysis)
```

## File Structure

```
services/api/src/core/
├── trade_analyzer.py              # Main integration module
├── test_trade_analyzer.py         # Unit tests
├── example_trade_analyzer.py      # Usage examples
├── TRADE_ANALYZER_README.md       # This file
│
├── market_data_fetcher.py         # Component 1
├── technical_indicators.py        # Component 2
├── validation_engine.py           # Component 3
└── risk_calculator.py             # Component 4
```

## Next Steps

After implementing TradeAnalyzer:

1. **Phase 3: AI Agents**
   - Integrate TradeAnalyzer into AI agents
   - Create ChartWatcher using indicators
   - Build SignalBot using validation
   - Implement RiskManager using risk calculator

2. **Phase 4: Dashboard UX**
   - Display analysis results in Next.js frontend
   - Create real-time chart widgets
   - Build trade management UI

3. **Phase 5: SaaS Features**
   - Add subscription limits
   - Implement automated notifications
   - Create PDF reports

## Requirements

- Python 3.9+
- Twelve Data API key (set in `TWELVE_DATA_API_KEY` env var)
- Supabase connection configured
- Market symbols in database (see migrations)

## Dependencies

```python
# Already included in requirements.txt
numpy
supabase
httpx
python-dotenv
```

## Support

For issues or questions:
- Check `docs/PROJECT_OVERVIEW.md`
- Review `services/api/src/core/example_trade_analyzer.py`
- See individual module documentation

---

**TradeMatrix.ai - Phase 2 Complete** ✓
