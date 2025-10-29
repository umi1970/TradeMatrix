"""
Test Utility Functions
======================

Helper functions for creating mocks, assertions, and test data manipulation.
"""

from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
import pytz


def create_mock_supabase_client(table_data: Optional[Dict[str, List[Dict]]] = None) -> Mock:
    """
    Create a mock Supabase client with configurable table data.

    Args:
        table_data: Dict mapping table names to list of records
                   Example: {'ohlc': [...], 'levels_daily': [...]}

    Returns:
        Mock Supabase client with pre-configured responses

    Example:
        >>> mock_client = create_mock_supabase_client({
        ...     'market_symbols': [{'id': '123', 'symbol': 'DAX'}]
        ... })
        >>> result = mock_client.table('market_symbols').select('*').execute()
        >>> result.data
        [{'id': '123', 'symbol': 'DAX'}]
    """
    if table_data is None:
        table_data = {}

    mock_client = Mock()

    def table_mock(table_name: str):
        """Mock table() method."""
        mock_table = Mock()

        # Store query state
        query_state = {
            'table_name': table_name,
            'filters': {},
            'limit_val': None,
            'order_by': None
        }

        def select(*args):
            return mock_table

        def insert(data):
            # Simulate insert
            if isinstance(data, dict):
                data['id'] = 'new_id_123'
            elif isinstance(data, list):
                for item in data:
                    if 'id' not in item:
                        item['id'] = 'new_id_123'
            return mock_table

        def update(data):
            return mock_table

        def eq(field, value):
            query_state['filters'][field] = value
            return mock_table

        def gte(field, value):
            query_state['filters'][f'{field}__gte'] = value
            return mock_table

        def lte(field, value):
            query_state['filters'][f'{field}__lte'] = value
            return mock_table

        def order(field, **kwargs):
            query_state['order_by'] = (field, kwargs.get('desc', False))
            return mock_table

        def limit(count):
            query_state['limit_val'] = count
            return mock_table

        def in_(field, values):
            query_state['filters'][f'{field}__in'] = values
            return mock_table

        def upsert(data, **kwargs):
            return mock_table

        def execute():
            """Execute query and return filtered data."""
            mock_result = Mock()

            # Get data for table
            data = table_data.get(table_name, [])

            # Apply filters
            filtered_data = data.copy()

            for filter_key, filter_value in query_state['filters'].items():
                if '__gte' in filter_key:
                    field = filter_key.replace('__gte', '')
                    filtered_data = [
                        item for item in filtered_data
                        if item.get(field, '') >= filter_value
                    ]
                elif '__lte' in filter_key:
                    field = filter_key.replace('__lte', '')
                    filtered_data = [
                        item for item in filtered_data
                        if item.get(field, '') <= filter_value
                    ]
                elif '__in' in filter_key:
                    field = filter_key.replace('__in', '')
                    filtered_data = [
                        item for item in filtered_data
                        if item.get(field) in filter_value
                    ]
                else:
                    # Equality filter
                    filtered_data = [
                        item for item in filtered_data
                        if str(item.get(filter_key)) == str(filter_value)
                    ]

            # Apply order
            if query_state['order_by']:
                field, desc = query_state['order_by']
                filtered_data.sort(
                    key=lambda x: x.get(field, ''),
                    reverse=desc
                )

            # Apply limit
            if query_state['limit_val']:
                filtered_data = filtered_data[:query_state['limit_val']]

            mock_result.data = filtered_data
            return mock_result

        # Assign mock methods
        mock_table.select = select
        mock_table.insert = insert
        mock_table.update = update
        mock_table.eq = eq
        mock_table.gte = gte
        mock_table.lte = lte
        mock_table.order = order
        mock_table.limit = limit
        mock_table.in_ = in_
        mock_table.upsert = upsert
        mock_table.execute = execute

        return mock_table

    mock_client.table = table_mock

    return mock_client


def assert_price_valid(
    price: float,
    min_val: float = 0.0,
    max_val: float = 100000.0
) -> None:
    """
    Assert that a price value is valid.

    Args:
        price: Price value to validate
        min_val: Minimum allowed price
        max_val: Maximum allowed price

    Raises:
        AssertionError: If price is invalid

    Example:
        >>> assert_price_valid(19500.0)
        >>> assert_price_valid(-100.0)  # Raises AssertionError
    """
    assert isinstance(price, (int, float)), "Price must be numeric"
    assert min_val <= price <= max_val, f"Price {price} out of range [{min_val}, {max_val}]"


def assert_confidence_valid(confidence: float) -> None:
    """
    Assert that a confidence score is valid.

    Args:
        confidence: Confidence score (0.0-1.0)

    Raises:
        AssertionError: If confidence is invalid

    Example:
        >>> assert_confidence_valid(0.85)
        >>> assert_confidence_valid(1.5)  # Raises AssertionError
    """
    assert isinstance(confidence, (int, float)), "Confidence must be numeric"
    assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} must be between 0.0 and 1.0"


def assert_timestamp_recent(
    timestamp: str,
    max_age_seconds: int = 300
) -> None:
    """
    Assert that a timestamp is recent (within max_age_seconds).

    Args:
        timestamp: ISO timestamp string
        max_age_seconds: Maximum age in seconds (default: 300 = 5 minutes)

    Raises:
        AssertionError: If timestamp is too old

    Example:
        >>> from datetime import datetime
        >>> import pytz
        >>> ts = datetime.now(pytz.UTC).isoformat()
        >>> assert_timestamp_recent(ts)
    """
    ts_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    now = datetime.now(pytz.UTC)
    age_seconds = (now - ts_dt).total_seconds()

    assert age_seconds >= 0, "Timestamp is in the future"
    assert age_seconds <= max_age_seconds, f"Timestamp is too old ({age_seconds}s > {max_age_seconds}s)"


def compare_floats(a: float, b: float, tolerance: float = 0.001) -> bool:
    """
    Compare two floats with tolerance for floating-point precision.

    Args:
        a: First float
        b: Second float
        tolerance: Tolerance for comparison (default: 0.001)

    Returns:
        True if floats are equal within tolerance

    Example:
        >>> compare_floats(19500.0, 19500.001)
        True
        >>> compare_floats(19500.0, 19501.0)
        False
    """
    return abs(a - b) <= tolerance


def extract_setup_metrics(setup: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract key metrics from a setup dict for easy comparison.

    Args:
        setup: Setup dictionary

    Returns:
        Dict with extracted metrics

    Example:
        >>> setup = {'entry_price': 19500, 'stop_loss': 19450, 'take_profit': 19600}
        >>> metrics = extract_setup_metrics(setup)
        >>> metrics['risk_reward_ratio']
        2.0
    """
    entry = float(setup['entry_price'])
    sl = float(setup['stop_loss'])
    tp = float(setup['take_profit'])

    # Determine direction
    direction = 'long' if entry > sl else 'short'

    # Calculate distances
    risk = abs(entry - sl)
    reward = abs(tp - entry)

    # Calculate R:R ratio
    rr_ratio = reward / risk if risk > 0 else 0

    return {
        'direction': direction,
        'entry': entry,
        'stop_loss': sl,
        'take_profit': tp,
        'risk_distance': risk,
        'reward_distance': reward,
        'risk_reward_ratio': round(rr_ratio, 2),
        'risk_percentage': round((risk / entry) * 100, 2) if entry > 0 else 0,
        'reward_percentage': round((reward / entry) * 100, 2) if entry > 0 else 0
    }


def mock_datetime_now(fixed_datetime: datetime):
    """
    Context manager to mock datetime.now() for testing.

    Args:
        fixed_datetime: Fixed datetime to return

    Example:
        >>> from datetime import datetime
        >>> import pytz
        >>> fixed_dt = pytz.UTC.localize(datetime(2025, 10, 29, 8, 25, 0))
        >>> with mock_datetime_now(fixed_dt):
        ...     # datetime.now() will return fixed_dt
        ...     pass
    """
    from unittest.mock import patch

    class MockDatetime:
        @classmethod
        def now(cls, tz=None):
            if tz:
                return fixed_datetime.astimezone(tz)
            return fixed_datetime

    return patch('datetime.datetime', MockDatetime)


def create_supabase_response(data: List[Dict], error: Optional[str] = None) -> Mock:
    """
    Create a mock Supabase response object.

    Args:
        data: List of data records
        error: Optional error message

    Returns:
        Mock response object

    Example:
        >>> response = create_supabase_response([{'id': '123', 'symbol': 'DAX'}])
        >>> response.data
        [{'id': '123', 'symbol': 'DAX'}]
    """
    mock_response = Mock()
    mock_response.data = data
    mock_response.error = error
    return mock_response


def verify_agent_execution_summary(summary: Dict[str, Any]) -> None:
    """
    Verify that an agent execution summary has all required fields.

    Args:
        summary: Execution summary dict

    Raises:
        AssertionError: If summary is invalid

    Example:
        >>> summary = {
        ...     'execution_time': '2025-10-29T08:25:00Z',
        ...     'symbols_analyzed': 2,
        ...     'setups_generated': 1,
        ...     'setups': [...]
        ... }
        >>> verify_agent_execution_summary(summary)
    """
    required_fields = [
        'execution_time',
        'symbols_analyzed',
        'setups_generated',
        'setups'
    ]

    for field in required_fields:
        assert field in summary, f"Missing required field in summary: {field}"

    # Validate types
    assert isinstance(summary['symbols_analyzed'], int), "symbols_analyzed must be int"
    assert isinstance(summary['setups_generated'], int), "setups_generated must be int"
    assert isinstance(summary['setups'], list), "setups must be list"

    # Validate counts match
    assert summary['setups_generated'] == len(summary['setups']), \
        "setups_generated count doesn't match setups list length"


def calculate_expected_confidence(
    ema_score: float,
    pivot_score: float,
    volume_score: float,
    candle_score: float,
    context_score: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate expected confidence score from metric scores.

    Args:
        ema_score: EMA alignment score
        pivot_score: Pivot confluence score
        volume_score: Volume confirmation score
        candle_score: Candle structure score
        context_score: Context flow score
        weights: Optional custom weights (default: ValidationEngine.WEIGHTS)

    Returns:
        Weighted confidence score

    Example:
        >>> confidence = calculate_expected_confidence(1.0, 0.8, 0.9, 0.85, 0.7)
        >>> 0.8 < confidence < 0.9
        True
    """
    if weights is None:
        weights = {
            'ema_alignment': 0.25,
            'pivot_confluence': 0.20,
            'volume_confirmation': 0.20,
            'candle_structure': 0.20,
            'context_flow': 0.15
        }

    confidence = (
        ema_score * weights['ema_alignment'] +
        pivot_score * weights['pivot_confluence'] +
        volume_score * weights['volume_confirmation'] +
        candle_score * weights['candle_structure'] +
        context_score * weights['context_flow']
    )

    return min(max(confidence, 0.0), 1.0)


def simulate_price_movement(
    current_price: float,
    target_price: float,
    steps: int = 10
) -> List[float]:
    """
    Simulate gradual price movement from current to target.

    Args:
        current_price: Starting price
        target_price: Target price
        steps: Number of steps (default: 10)

    Returns:
        List of prices showing gradual movement

    Example:
        >>> prices = simulate_price_movement(19500.0, 19550.0, steps=5)
        >>> len(prices)
        5
        >>> prices[0]
        19500.0
        >>> prices[-1]
        19550.0
    """
    if steps <= 0:
        return [target_price]

    step_size = (target_price - current_price) / steps
    prices = []

    for i in range(steps):
        price = current_price + (step_size * i)
        prices.append(round(price, 2))

    return prices


# Export commonly used functions
__all__ = [
    'create_mock_supabase_client',
    'assert_price_valid',
    'assert_confidence_valid',
    'assert_timestamp_recent',
    'compare_floats',
    'extract_setup_metrics',
    'mock_datetime_now',
    'create_supabase_response',
    'verify_agent_execution_summary',
    'calculate_expected_confidence',
    'simulate_price_movement'
]
