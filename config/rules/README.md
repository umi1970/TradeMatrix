# Trading Rules Configuration

This directory contains YAML configuration files for all TradeMatrix.ai trading strategies (MR-Series).

## Overview

Each YAML file defines a complete trading strategy with:
- Entry conditions
- Exit conditions
- Risk management parameters
- Validation metrics
- Market conditions
- Priority rules

## Strategy Files

| File | Strategy | Priority | Confidence | Category |
|------|----------|----------|------------|----------|
| `MR-01_ema_cross.yaml` | EMA Cross Reversal | 2 | 0.75+ | Trend Reversal |
| `MR-02_pivot_rebound.yaml` | Pivot Rebound | 2 | 0.78+ | Mean Reversion |
| `MR-03_gap_open.yaml` | Gap-Open Play | 2 | 0.72+ | Momentum |
| `MR-04_vortagstief.yaml` | Yesterday Low Reversal | **1** | 0.85+ | Liquidity Grab |
| `MR-05_end_of_month.yaml` | End-of-Month Rotation | **1** | 0.80+ | Institutional Flow |
| `MR-06_yesterday_range.yaml` | Yesterday Range Reversion | **1** | 0.83+ | Mean Reversion |

## Priority System

**Priority 1 (High):** MR-04, MR-05, MR-06
- These setups can override Priority 2 setups
- Higher confidence scores required
- Based on institutional/liquidity concepts

**Priority 2 (Standard):** MR-01, MR-02, MR-03
- Standard technical analysis setups
- Can be overridden by Priority 1 setups

## Validation Metrics

All strategies use a weighted validation system:

| Metric | Weight | Description |
|--------|--------|-------------|
| EMA Alignment | 25% | Trend direction and momentum |
| Pivot Confluence | 20% | Support/resistance levels |
| Volume Confirmation | 20% | Market participation |
| Candle Structure | 20% | Price action patterns |
| Context Flow | 15% | Market context and timing |

**Minimum Confidence Score:** 0.70-0.85 (varies by strategy)

## Risk Management

All strategies follow these global rules:
- **Max Risk:** 1% per trade
- **Breakeven:** Move to BE at 0.5:1 RRR
- **Position Type:** CFD
- **Stop Loss:** Always defined
- **Take Profit:** Always defined

## YAML Structure

```yaml
strategy:
  id: "MR-XX"
  name: "Strategy Name"
  priority: 1 or 2
  category: "category_type"

entry_conditions:
  - type: "condition_type"
    parameters: values

exit_conditions:
  - type: "exit_type"
    parameters: values

risk_management:
  max_risk_percent: 1.0
  breakeven_at_rrr: 0.5

validation_metrics:
  metric_name:
    weight: 0.XX
    required_score: 0.XX
```

## Usage

These YAML files are consumed by:
1. **Trade Validation Engine** - Evaluates setups
2. **Signal Bot Agent** - Generates trade signals
3. **Risk Manager Agent** - Calculates position sizes
4. **Morning Planner Agent** - Plans daily trades

## Implementation

```python
import yaml

# Load strategy
with open('config/rules/MR-04_vortagstief.yaml') as f:
    strategy = yaml.safe_load(f)

# Access parameters
entry_conditions = strategy['entry_conditions']
confidence_threshold = strategy['validation_metrics']['min_confidence_score']
```

## Strategy Details

### MR-01: EMA Cross Reversal
- **Concept:** Trend reversal via EMA crossover
- **Best:** Trending markets
- **Timeframe:** 5m
- **Target RRR:** 2.0

### MR-02: Pivot Rebound
- **Concept:** Mean reversion at S1/R1 levels
- **Best:** Range-bound markets
- **Timeframe:** 5m
- **Target:** Pivot PP

### MR-03: Gap-Open Play
- **Concept:** Capitalize on opening gaps
- **Best:** Market open (first hour)
- **Gap Size:** >0.3%, <2.0%
- **Volume:** >1.5x average

### MR-04: Yesterday Low Reversal (PRIORITY)
- **Concept:** Stop-grab reversal at previous day's low
- **Best:** EU/US open
- **Confidence:** 0.85+
- **Key:** Liquidity grab + reversal candle

### MR-05: End-of-Month Rotation (PRIORITY)
- **Concept:** Institutional month-end rebalancing
- **Best:** Last 3 trading days of month
- **Volume:** >1.5x monthly average
- **Key:** Smart money flow detection

### MR-06: Yesterday Range Reversion (PRIORITY)
- **Concept:** Mean revert from extremes to pivot
- **Best:** Range-bound markets
- **Distance:** ±10 points from yesterday high/low
- **Target:** Pivot PP

## Notes

- Priority 1 strategies override Priority 2 when both signal
- All strategies require minimum confidence scores
- Volume is critical for most setups
- Time windows are in CET timezone
- Examples included in each YAML file

## Updates

When adding new strategies:
1. Copy template structure
2. Assign unique ID (MR-XX)
3. Define all required sections
4. Set priority level
5. Add validation metrics
6. Include examples
7. Update this README

## Reference

- **Main Docs:** `/docs/04_Trading_Rules.md`
- **Validation Engine:** `/docs/05_Validation_Engine.md`
- **Risk Management:** `/docs/06_Risk_Management.md`

---

**Last Updated:** 2025-10-29
**Version:** 1.0
**Status:** Production Ready
