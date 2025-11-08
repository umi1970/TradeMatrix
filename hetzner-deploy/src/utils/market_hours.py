"""
Market Hours & Trading Calendar Utility

Checks if markets are open for different asset types and exchanges.
Handles:
- Stock indices (DAX, NASDAQ, DOW) - regular trading hours + holidays
- Forex pairs - 24/5 (closed weekends)
- Crypto - 24/7 (always open)
"""

import logging
from datetime import datetime
from typing import Dict, Optional
import pytz

logger = logging.getLogger(__name__)

# Exchange trading hours (local time)
EXCHANGE_HOURS = {
    'XETRA': {  # DAX (Frankfurt)
        'timezone': 'Europe/Berlin',
        'open': '09:00',
        'close': '17:30',
        'weekdays': [0, 1, 2, 3, 4],  # Mon-Fri
    },
    'NASDAQ': {  # NDX
        'timezone': 'America/New_York',
        'open': '09:30',
        'close': '16:00',
        'weekdays': [0, 1, 2, 3, 4],
    },
    'NYSE': {  # DJI
        'timezone': 'America/New_York',
        'open': '09:30',
        'close': '16:00',
        'weekdays': [0, 1, 2, 3, 4],
    },
    'FOREX': {  # EUR/USD, etc.
        'timezone': 'UTC',
        'open': '22:00',  # Sunday 22:00 UTC
        'close': '22:00',  # Friday 22:00 UTC
        'weekdays': [0, 1, 2, 3, 4, 6],  # Mon-Fri + Sun evening
    },
}

# Symbol to exchange mapping
SYMBOL_EXCHANGES = {
    'DAX': 'XETRA',
    'NDX': 'NASDAQ',
    'DJI': 'NYSE',
    'EUR/USD': 'FOREX',
    'EUR/GBP': 'FOREX',
    'GBP/USD': 'FOREX',
    # Crypto always returns True (24/7)
    'BTC/USD': 'CRYPTO',
    'ETH/USD': 'CRYPTO',
}

# Simple holiday list (you can expand this)
# Format: (month, day)
HOLIDAYS_2025 = {
    'XETRA': [
        (1, 1),   # New Year
        (4, 18),  # Good Friday
        (4, 21),  # Easter Monday
        (5, 1),   # Labour Day
        (12, 25), # Christmas
        (12, 26), # Boxing Day
    ],
    'NYSE': [
        (1, 1),   # New Year
        (1, 20),  # MLK Day
        (2, 17),  # Presidents Day
        (4, 18),  # Good Friday
        (5, 26),  # Memorial Day
        (7, 4),   # Independence Day
        (9, 1),   # Labor Day
        (11, 27), # Thanksgiving
        (12, 25), # Christmas
    ],
}


def is_market_open(symbol: str, check_time: Optional[datetime] = None) -> bool:
    """
    Check if market is open for given symbol.

    Args:
        symbol: Trading symbol (e.g., 'DAX', 'BTC/USD')
        check_time: Time to check (defaults to now UTC)

    Returns:
        True if market is open, False otherwise
    """
    if check_time is None:
        check_time = datetime.now(pytz.UTC)

    # Get exchange for symbol
    exchange = SYMBOL_EXCHANGES.get(symbol)

    if not exchange:
        logger.warning(f"Unknown symbol {symbol}, assuming market closed")
        return False

    # Crypto is always open
    if exchange == 'CRYPTO':
        return True

    # Get exchange config
    config = EXCHANGE_HOURS.get(exchange)
    if not config:
        logger.warning(f"Unknown exchange {exchange}, assuming market closed")
        return False

    # Convert to exchange timezone
    tz = pytz.timezone(config['timezone'])
    local_time = check_time.astimezone(tz)

    # Check if it's a weekday
    if local_time.weekday() not in config['weekdays']:
        return False

    # Check if it's a holiday
    holidays = HOLIDAYS_2025.get(exchange, [])
    if (local_time.month, local_time.day) in holidays:
        logger.info(f"{exchange} closed for holiday: {local_time.strftime('%Y-%m-%d')}")
        return False

    # Special handling for FOREX (24/5)
    if exchange == 'FOREX':
        # Closed from Friday 22:00 UTC to Sunday 22:00 UTC
        weekday = check_time.weekday()
        hour = check_time.hour

        # Friday after 22:00 UTC
        if weekday == 4 and hour >= 22:
            return False
        # Saturday (all day)
        if weekday == 5:
            return False
        # Sunday before 22:00 UTC
        if weekday == 6 and hour < 22:
            return False

        return True

    # Check trading hours for stocks
    open_time = datetime.strptime(config['open'], '%H:%M').time()
    close_time = datetime.strptime(config['close'], '%H:%M').time()
    current_time = local_time.time()

    is_open = open_time <= current_time <= close_time

    if not is_open:
        logger.debug(f"{exchange} closed - outside trading hours")

    return is_open


def should_run_analysis() -> bool:
    """
    Check if ANY market is open (for general market analysis tasks).

    Returns True if at least one tracked market is open.
    """
    symbols_to_check = ['DAX', 'NDX', 'DJI', 'EUR/USD']

    for symbol in symbols_to_check:
        if is_market_open(symbol):
            logger.info(f"Market open for {symbol} - analysis should run")
            return True

    logger.info("All markets closed - skipping analysis")
    return False


def get_open_symbols() -> list[str]:
    """
    Get list of symbols with open markets.

    Returns:
        List of symbols (e.g., ['DAX', 'BTC/USD'])
    """
    open_symbols = []

    for symbol in SYMBOL_EXCHANGES.keys():
        if is_market_open(symbol):
            open_symbols.append(symbol)

    return open_symbols
