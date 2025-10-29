"""
Test Data Fixtures
==================

Provides helper functions to generate test data for agents and modules.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytz
from typing import List, Dict, Any


def generate_ohlc_data(
    start_time: datetime,
    count: int = 100,
    timeframe_minutes: int = 5,
    base_price: float = 19500.0,
    volatility: float = 0.01
) -> List[Dict[str, Any]]:
    """
    Generate synthetic OHLC candle data for testing.

    Args:
        start_time: Starting datetime (timezone-aware)
        count: Number of candles to generate
        timeframe_minutes: Timeframe in minutes (default: 5)
        base_price: Starting price (default: 19500.0)
        volatility: Price volatility factor (default: 0.01 = 1%)

    Returns:
        List of OHLC candle dictionaries

    Example:
        >>> from datetime import datetime
        >>> import pytz
        >>> berlin_tz = pytz.timezone('Europe/Berlin')
        >>> start = berlin_tz.localize(datetime(2025, 10, 29, 8, 0, 0))
        >>> candles = generate_ohlc_data(start, count=50)
        >>> len(candles)
        50
    """
    import random

    candles = []
    current_price = base_price

    for i in range(count):
        ts = start_time + timedelta(minutes=timeframe_minutes * i)

        # Simulate price movement with random walk
        price_change = random.uniform(-volatility, volatility) * current_price
        current_price += price_change

        # Generate OHLC
        open_price = current_price
        high = open_price * (1 + abs(random.uniform(0, volatility * 0.5)))
        low = open_price * (1 - abs(random.uniform(0, volatility * 0.5)))
        close = random.uniform(low, high)
        volume = random.randint(8000, 15000)

        candles.append({
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume
        })

        current_price = close

    return candles


def create_test_setup(
    symbol_id: UUID,
    strategy: str = 'asia_sweep',
    side: str = 'long',
    entry_price: float = 19420.0,
    stop_loss: float = 19385.0,
    take_profit: float = 19500.0,
    confidence: float = 0.85
) -> Dict[str, Any]:
    """
    Create a test setup record.

    Args:
        symbol_id: Symbol UUID
        strategy: Strategy name
        side: 'long' or 'short'
        entry_price: Entry price
        stop_loss: Stop loss price
        take_profit: Take profit price
        confidence: Confidence score (0.0-1.0)

    Returns:
        Setup dictionary

    Example:
        >>> from uuid import uuid4
        >>> setup = create_test_setup(uuid4(), strategy='orb', confidence=0.9)
        >>> setup['strategy']
        'orb'
    """
    return {
        'id': str(uuid4()),
        'user_id': None,
        'module': 'morning' if strategy in ['asia_sweep', 'y_low_rebound'] else 'usopen',
        'symbol_id': str(symbol_id),
        'strategy': strategy,
        'side': side,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'confidence': confidence,
        'status': 'pending',
        'payload': {
            'detection_time': datetime.now(pytz.UTC).isoformat(),
            'metadata': {}
        },
        'created_at': datetime.now(pytz.UTC).isoformat()
    }


def create_asia_sweep_scenario(
    symbol_id: UUID,
    y_low: float = 19400.0,
    sweep_depth: float = 15.0
) -> Dict[str, Any]:
    """
    Create a complete Asia sweep test scenario with candles and levels.

    Args:
        symbol_id: Symbol UUID
        y_low: Yesterday's low level
        sweep_depth: How far below y_low the sweep goes

    Returns:
        Dict with asia_candles, eu_candles, and levels

    Example:
        >>> from uuid import uuid4
        >>> scenario = create_asia_sweep_scenario(uuid4())
        >>> len(scenario['asia_candles'])
        36
    """
    berlin_tz = pytz.timezone('Europe/Berlin')
    trade_date = datetime(2025, 10, 29)

    # Asia session: 02:00-05:00 MEZ
    asia_start = berlin_tz.localize(datetime(2025, 10, 29, 2, 0, 0))
    asia_candles = []

    for i in range(36):  # 3 hours = 36 x 5min
        ts = asia_start + timedelta(minutes=5 * i)

        if i < 15:
            # Move down gradually
            open_price = 19450.0 - (i * 3)
            low = open_price - 5
        elif i < 25:
            # Sweep below y_low
            open_price = y_low - sweep_depth
            low = y_low - sweep_depth - 5
        else:
            # Start recovering
            open_price = y_low - sweep_depth + ((i - 25) * 2)
            low = open_price - 3

        high = open_price + 8
        close = open_price + 2
        volume = 8000 + (i * 100)

        asia_candles.append({
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'symbol_id': str(symbol_id),
            'timeframe': '5m',
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    # EU open: 08:00-08:25 MEZ
    eu_start = berlin_tz.localize(datetime(2025, 10, 29, 8, 0, 0))
    eu_candles = []

    for i in range(5):  # 25 minutes = 5 x 5min
        ts = eu_start + timedelta(minutes=5 * i)

        # Price reverses above y_low
        open_price = y_low + 15 + (i * 5)
        high = open_price + 15
        low = y_low + 5  # Stay above y_low
        close = open_price + 10
        volume = 12000 + (i * 300)

        eu_candles.append({
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'symbol_id': str(symbol_id),
            'timeframe': '5m',
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    # Daily levels
    levels = {
        'symbol_id': str(symbol_id),
        'trade_date': trade_date.strftime('%Y-%m-%d'),
        'y_high': 19600.0,
        'y_low': y_low,
        'pivot': 19500.0,
        'r1': 19550.0,
        'r2': 19600.0,
        's1': 19450.0,
        's2': 19400.0
    }

    return {
        'asia_candles': asia_candles,
        'eu_candles': eu_candles,
        'levels': levels
    }


def create_orb_scenario(
    symbol_id: UUID,
    orb_high: float = 18550.0,
    orb_low: float = 18520.0,
    breakout_direction: str = 'long'
) -> Dict[str, Any]:
    """
    Create a complete ORB (Opening Range Breakout) test scenario.

    Args:
        symbol_id: Symbol UUID
        orb_high: ORB high price
        orb_low: ORB low price
        breakout_direction: 'long' or 'short'

    Returns:
        Dict with orb_candles, breakout_candles, and daily_levels

    Example:
        >>> from uuid import uuid4
        >>> scenario = create_orb_scenario(uuid4(), breakout_direction='short')
        >>> scenario['breakout_candles'][0]['close'] < 18520.0
        True
    """
    berlin_tz = pytz.timezone('Europe/Berlin')

    # ORB period: 15:30-15:45 MEZ
    orb_start = berlin_tz.localize(datetime(2025, 10, 29, 15, 30, 0))
    orb_candles = []

    for i in range(15):  # 15 minutes = 15 x 1min
        ts = orb_start + timedelta(minutes=i)

        # Price oscillates within range
        open_price = orb_low + ((orb_high - orb_low) * (i / 15))
        high = min(orb_high, open_price + 5)
        low = max(orb_low, open_price - 5)
        close = open_price + 2
        volume = 15000 + (i * 100)

        orb_candles.append({
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'symbol_id': str(symbol_id),
            'timeframe': '1m',
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    # Breakout period: 15:45-16:00 MEZ
    breakout_start = berlin_tz.localize(datetime(2025, 10, 29, 15, 45, 0))
    breakout_candles = []

    for i in range(3):  # 15 minutes = 3 x 5min
        ts = breakout_start + timedelta(minutes=5 * i)

        if breakout_direction == 'long':
            # Breakout above range
            open_price = orb_high + 5 + (i * 10)
            high = open_price + 15
            low = orb_high - 2 if i == 0 else open_price - 5  # Retest on first candle
            close = open_price + 12
        else:
            # Breakout below range
            open_price = orb_low - 5 - (i * 10)
            high = orb_low + 2 if i == 0 else open_price + 5  # Retest on first candle
            low = open_price - 15
            close = open_price - 12

        volume = 20000 + (i * 500)

        breakout_candles.append({
            'ts': ts.astimezone(pytz.UTC).isoformat(),
            'symbol_id': str(symbol_id),
            'timeframe': '5m',
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    # Daily levels
    daily_levels = {
        'symbol_id': str(symbol_id),
        'trade_date': '2025-10-29',
        'y_high': 18650.0,
        'y_low': 18450.0,
        'pivot': 18535.0,
        'r1': 18600.0,
        's1': 18480.0
    }

    return {
        'orb_candles': orb_candles,
        'breakout_candles': breakout_candles,
        'daily_levels': daily_levels
    }


def create_alert_test_data(
    symbol_id: UUID,
    alert_kind: str = 'range_break'
) -> Dict[str, Any]:
    """
    Create test data for alert engine testing.

    Args:
        symbol_id: Symbol UUID
        alert_kind: Type of alert to create

    Returns:
        Dict with test data for specified alert kind

    Example:
        >>> from uuid import uuid4
        >>> data = create_alert_test_data(uuid4(), 'pivot_touch')
        >>> data['levels']['pivot']
        18500.0
    """
    if alert_kind == 'range_break':
        return {
            'setup': {
                'strategy': 'orb',
                'payload': {
                    'range_high': 18550.0,
                    'range_low': 18520.0
                }
            },
            'candle': {
                'close': 18560.0,  # Above range
                'high': 18565.0,
                'low': 18555.0,
                'ts': datetime.now(pytz.UTC).isoformat()
            }
        }

    elif alert_kind == 'pivot_touch':
        return {
            'levels': {
                'pivot': 18500.0,
                'r1': 18550.0,
                's1': 18450.0
            },
            'candle': {
                'close': 18502.0,  # Near pivot
                'high': 18505.0,
                'low': 18498.0,  # Touches pivot
                'ts': datetime.now(pytz.UTC).isoformat()
            }
        }

    elif alert_kind == 'asia_sweep_confirmed':
        return create_asia_sweep_scenario(symbol_id)

    else:
        raise ValueError(f"Unknown alert_kind: {alert_kind}")


def assert_setup_valid(setup: Dict[str, Any]) -> None:
    """
    Assert that a setup dict has all required fields.

    Args:
        setup: Setup dictionary to validate

    Raises:
        AssertionError: If setup is missing required fields

    Example:
        >>> setup = create_test_setup(uuid4())
        >>> assert_setup_valid(setup)
        >>> # Passes silently if valid
    """
    required_fields = [
        'module', 'symbol_id', 'strategy', 'side',
        'entry_price', 'stop_loss', 'take_profit',
        'confidence', 'status', 'payload'
    ]

    for field in required_fields:
        assert field in setup, f"Missing required field: {field}"

    # Validate types
    assert isinstance(setup['confidence'], (int, float)), "Confidence must be numeric"
    assert 0.0 <= setup['confidence'] <= 1.0, "Confidence must be between 0.0 and 1.0"
    assert setup['side'] in ['long', 'short'], "Side must be 'long' or 'short'"
    assert setup['status'] in ['pending', 'active', 'closed', 'cancelled'], "Invalid status"


def assert_candle_valid(candle: Dict[str, Any]) -> None:
    """
    Assert that a candle dict has valid OHLC data.

    Args:
        candle: Candle dictionary to validate

    Raises:
        AssertionError: If candle data is invalid

    Example:
        >>> candle = {'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        >>> assert_candle_valid(candle)
    """
    required_fields = ['open', 'high', 'low', 'close']

    for field in required_fields:
        assert field in candle, f"Missing required field: {field}"
        assert isinstance(candle[field], (int, float, Decimal)), f"{field} must be numeric"

    # Validate OHLC relationships
    high = float(candle['high'])
    low = float(candle['low'])
    open_price = float(candle['open'])
    close = float(candle['close'])

    assert high >= low, "High must be >= Low"
    assert high >= open_price, "High must be >= Open"
    assert high >= close, "High must be >= Close"
    assert low <= open_price, "Low must be <= Open"
    assert low <= close, "Low must be <= Close"
