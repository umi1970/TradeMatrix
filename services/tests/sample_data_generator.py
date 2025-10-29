"""
Sample Data Generator for E2E Tests
====================================
Generates realistic market data for testing trading flows

Usage:
    from sample_data_generator import generate_sample_data
    data = generate_sample_data('DAX', days=14)
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple
import pytz
import random


class SampleDataGenerator:
    """
    Generates realistic sample OHLC data for testing
    """

    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducibility"""
        random.seed(seed)
        self.berlin_tz = pytz.timezone('Europe/Berlin')
        self.utc_tz = pytz.UTC

    def generate_ohlc_candles(
        self,
        symbol: str,
        base_price: Decimal,
        start_time: datetime,
        duration_minutes: int,
        timeframe: str = '5m',
        volatility: float = 0.002,
        trend: str = 'neutral'
    ) -> List[Dict]:
        """
        Generate OHLC candles with realistic price action

        Args:
            symbol: Symbol name (e.g., 'DAX')
            base_price: Starting price
            start_time: Start timestamp (timezone-aware)
            duration_minutes: Total duration in minutes
            timeframe: Candle timeframe ('1m', '5m', '15m', '1h', '1d')
            volatility: Price volatility (0.0-1.0, default 0.002 = 0.2%)
            trend: Price trend ('up', 'down', 'neutral')

        Returns:
            List of OHLC candle dicts
        """
        # Parse timeframe
        timeframe_minutes = self._parse_timeframe(timeframe)
        num_candles = duration_minutes // timeframe_minutes

        candles = []
        current_price = base_price
        current_time = start_time

        # Trend bias
        trend_bias = 0.0
        if trend == 'up':
            trend_bias = volatility * 0.3
        elif trend == 'down':
            trend_bias = -volatility * 0.3

        for i in range(num_candles):
            # Calculate OHLC with random walk
            open_price = current_price

            # Random price movements
            change_pct = Decimal(str(random.uniform(-volatility, volatility))) + Decimal(str(trend_bias))
            close_price = open_price * (Decimal('1.0') + change_pct)

            # High and low based on intra-candle volatility
            high_offset = abs(change_pct) * Decimal(str(random.uniform(1.2, 2.0)))
            low_offset = abs(change_pct) * Decimal(str(random.uniform(1.2, 2.0)))

            high_price = max(open_price, close_price) + (open_price * high_offset)
            low_price = min(open_price, close_price) - (open_price * low_offset)

            # Ensure high >= open, close and low <= open, close
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            # Volume (random with trend)
            base_volume = 50000
            volume = int(base_volume * random.uniform(0.8, 1.5))

            candles.append({
                'ts': current_time.astimezone(self.utc_tz).isoformat(),
                'timeframe': timeframe,
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'close': float(close_price),
                'volume': volume
            })

            # Update for next candle
            current_price = close_price
            current_time += timedelta(minutes=timeframe_minutes)

        return candles

    def generate_asia_sweep_scenario(
        self,
        base_price: Decimal,
        y_low: Decimal,
        trade_date: datetime
    ) -> List[Dict]:
        """
        Generate Asia session candles with sweep below y_low

        Args:
            base_price: Starting price
            y_low: Yesterday's low level
            trade_date: Trade date (Berlin timezone)

        Returns:
            List of 5m candles for Asia session (02:00-05:00)
        """
        candles = []
        asia_start = trade_date.replace(hour=2, minute=0, second=0, microsecond=0)

        # Phase 1: Early Asia (02:00-03:00) - neutral
        phase1_candles = self.generate_ohlc_candles(
            symbol='DAX',
            base_price=base_price,
            start_time=asia_start,
            duration_minutes=60,
            timeframe='5m',
            volatility=0.001,
            trend='neutral'
        )
        candles.extend(phase1_candles)

        # Phase 2: Mid Asia (03:00-04:00) - sweep below y_low
        phase2_start = asia_start + timedelta(hours=1)
        sweep_price = y_low - (y_low * Decimal('0.005'))  # Sweep 0.5% below y_low

        phase2_candles = self.generate_ohlc_candles(
            symbol='DAX',
            base_price=phase1_candles[-1]['close'],
            start_time=phase2_start,
            duration_minutes=60,
            timeframe='5m',
            volatility=0.003,
            trend='down'
        )

        # Force minimum to be below y_low
        for candle in phase2_candles[3:8]:  # Middle 5 candles sweep
            candle['low'] = float(min(Decimal(str(candle['low'])), sweep_price))

        candles.extend(phase2_candles)

        # Phase 3: Late Asia (04:00-05:00) - recovery
        phase3_start = asia_start + timedelta(hours=2)

        phase3_candles = self.generate_ohlc_candles(
            symbol='DAX',
            base_price=phase2_candles[-1]['close'],
            start_time=phase3_start,
            duration_minutes=60,
            timeframe='5m',
            volatility=0.002,
            trend='up'
        )
        candles.extend(phase3_candles)

        return candles

    def generate_eu_open_reversal(
        self,
        base_price: Decimal,
        y_low: Decimal,
        trade_date: datetime
    ) -> List[Dict]:
        """
        Generate EU session candles with reversal above y_low

        Args:
            base_price: Starting price (should be near y_low)
            y_low: Yesterday's low level
            trade_date: Trade date (Berlin timezone)

        Returns:
            List of 5m candles for EU open (08:00-08:30)
        """
        eu_start = trade_date.replace(hour=8, minute=0, second=0, microsecond=0)

        # EU open with bullish reversal above y_low
        recovery_price = y_low * Decimal('1.003')  # 0.3% above y_low

        candles = self.generate_ohlc_candles(
            symbol='DAX',
            base_price=recovery_price,
            start_time=eu_start,
            duration_minutes=30,
            timeframe='5m',
            volatility=0.002,
            trend='up'
        )

        # Ensure all closes are above y_low
        for candle in candles:
            if Decimal(str(candle['close'])) <= y_low:
                candle['close'] = float(y_low * Decimal('1.001'))
            if Decimal(str(candle['high'])) <= y_low:
                candle['high'] = float(y_low * Decimal('1.002'))

        return candles

    def generate_orb_scenario(
        self,
        base_price: Decimal,
        trade_date: datetime,
        breakout_direction: str = 'long'
    ) -> Tuple[List[Dict], Dict]:
        """
        Generate US market ORB scenario (15:30-15:45 range + breakout)

        Args:
            base_price: Starting price
            trade_date: Trade date (Berlin timezone)
            breakout_direction: 'long' or 'short'

        Returns:
            Tuple of (candles list, orb_data dict)
        """
        orb_start = trade_date.replace(hour=15, minute=30, second=0, microsecond=0)

        # Phase 1: ORB range formation (15:30-15:45, 15 x 1m candles)
        orb_candles = self.generate_ohlc_candles(
            symbol='NDX',
            base_price=base_price,
            start_time=orb_start,
            duration_minutes=15,
            timeframe='1m',
            volatility=0.0015,
            trend='neutral'
        )

        # Calculate ORB high/low
        orb_high = max(Decimal(str(c['high'])) for c in orb_candles)
        orb_low = min(Decimal(str(c['low'])) for c in orb_candles)
        orb_range = orb_high - orb_low

        # Phase 2: Breakout (15:45-16:00, 3 x 5m candles)
        breakout_start = trade_date.replace(hour=15, minute=45, second=0, microsecond=0)

        if breakout_direction == 'long':
            breakout_base = orb_high * Decimal('1.002')  # Start above high
            trend = 'up'
        else:
            breakout_base = orb_low * Decimal('0.998')  # Start below low
            trend = 'down'

        breakout_candles = self.generate_ohlc_candles(
            symbol='NDX',
            base_price=breakout_base,
            start_time=breakout_start,
            duration_minutes=15,
            timeframe='5m',
            volatility=0.003,
            trend=trend
        )

        # Add retest in first breakout candle
        if breakout_direction == 'long':
            breakout_candles[0]['low'] = float(orb_high * Decimal('0.9995'))
        else:
            breakout_candles[0]['high'] = float(orb_low * Decimal('1.0005'))

        all_candles = orb_candles + breakout_candles

        orb_data = {
            'high': float(orb_high),
            'low': float(orb_low),
            'range_size': float(orb_range),
            'breakout_direction': breakout_direction
        }

        return all_candles, orb_data

    def calculate_pivot_levels(
        self,
        y_high: Decimal,
        y_low: Decimal,
        y_close: Decimal
    ) -> Dict[str, float]:
        """
        Calculate pivot points using standard formula

        Args:
            y_high: Yesterday's high
            y_low: Yesterday's low
            y_close: Yesterday's close

        Returns:
            Dict with pivot, r1, r2, s1, s2
        """
        pivot = (y_high + y_low + y_close) / Decimal('3.0')
        r1 = (pivot * Decimal('2.0')) - y_low
        r2 = pivot + (y_high - y_low)
        s1 = (pivot * Decimal('2.0')) - y_high
        s2 = pivot - (y_high - y_low)

        return {
            'pivot': float(pivot),
            'r1': float(r1),
            'r2': float(r2),
            's1': float(s1),
            's2': float(s2),
            'y_high': float(y_high),
            'y_low': float(y_low),
            'y_close': float(y_close)
        }

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to minutes"""
        if timeframe == '1m':
            return 1
        elif timeframe == '5m':
            return 5
        elif timeframe == '15m':
            return 15
        elif timeframe == '1h':
            return 60
        elif timeframe == '1d':
            return 1440
        else:
            raise ValueError(f"Unknown timeframe: {timeframe}")


# ================================================
# Convenience Functions
# ================================================

def generate_sample_data(
    symbol: str = 'DAX',
    days: int = 14,
    include_scenarios: bool = True
) -> Dict:
    """
    Generate complete sample dataset for testing

    Args:
        symbol: Symbol name
        days: Number of days of historical data
        include_scenarios: Include specific test scenarios

    Returns:
        Dict with 'ohlc', 'levels', 'scenarios'
    """
    generator = SampleDataGenerator()
    berlin_tz = pytz.timezone('Europe/Berlin')

    # Base prices for different symbols
    base_prices = {
        'DAX': Decimal('18500.0'),
        'NDX': Decimal('16500.0'),
        'DJI': Decimal('38000.0')
    }

    base_price = base_prices.get(symbol, Decimal('10000.0'))

    # Generate daily data
    end_date = datetime.now(berlin_tz)
    start_date = end_date - timedelta(days=days)

    ohlc_data = []
    levels_data = []

    current_date = start_date
    current_price = base_price

    for day in range(days):
        # Generate daily candle
        daily_candles = generator.generate_ohlc_candles(
            symbol=symbol,
            base_price=current_price,
            start_time=current_date.replace(hour=8, minute=0),
            duration_minutes=480,  # 8 hours
            timeframe='1h',
            volatility=0.01,
            trend='neutral'
        )

        ohlc_data.extend(daily_candles)

        # Calculate levels
        if daily_candles:
            y_high = max(Decimal(str(c['high'])) for c in daily_candles)
            y_low = min(Decimal(str(c['low'])) for c in daily_candles)
            y_close = Decimal(str(daily_candles[-1]['close']))

            levels = generator.calculate_pivot_levels(y_high, y_low, y_close)
            levels['trade_date'] = (current_date + timedelta(days=1)).date().isoformat()

            levels_data.append(levels)

            current_price = y_close

        current_date += timedelta(days=1)

    result = {
        'ohlc': ohlc_data,
        'levels': levels_data,
        'scenarios': {}
    }

    # Add specific test scenarios
    if include_scenarios:
        trade_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        if symbol == 'DAX':
            # Asia sweep scenario
            y_low = Decimal(str(levels_data[-1]['y_low']))
            asia_candles = generator.generate_asia_sweep_scenario(
                base_price=current_price,
                y_low=y_low,
                trade_date=trade_date
            )

            eu_candles = generator.generate_eu_open_reversal(
                base_price=Decimal(str(asia_candles[-1]['close'])),
                y_low=y_low,
                trade_date=trade_date
            )

            result['scenarios']['asia_sweep'] = {
                'asia_candles': asia_candles,
                'eu_candles': eu_candles
            }

        elif symbol in ['NDX', 'DJI']:
            # ORB scenario
            orb_candles, orb_data = generator.generate_orb_scenario(
                base_price=current_price,
                trade_date=trade_date,
                breakout_direction='long'
            )

            result['scenarios']['orb'] = {
                'candles': orb_candles,
                'orb_data': orb_data
            }

    return result


if __name__ == "__main__":
    # Example usage
    data = generate_sample_data('DAX', days=7, include_scenarios=True)

    print(f"Generated {len(data['ohlc'])} OHLC candles")
    print(f"Generated {len(data['levels'])} daily levels")
    print(f"Scenarios: {list(data['scenarios'].keys())}")
