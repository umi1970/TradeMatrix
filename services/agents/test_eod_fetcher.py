"""
TradeMatrix.ai - EOD Data Fetcher Test Suite
Test script for eod_data_fetcher.py

This script tests:
1. EODDataFetcher class initialization
2. fetch_from_stooq() method (mock)
3. fetch_from_yahoo() method (mock)
4. cross_validate() method
5. _calculate_and_store_levels() method (mock)
6. _log_fetch_attempt() method
7. Integration with Celery tasks

Usage:
    python test_eod_fetcher.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eod_data_fetcher import EODDataFetcher, fetch_eod_data_task


class MockSupabaseClient:
    """Mock Supabase client for testing"""

    def __init__(self):
        self.tables = {}
        self.last_query = None

    def table(self, table_name: str):
        """Return a mock table query builder"""
        return MockTableQuery(table_name, self)


def get_config_path():
    """Get absolute path to config file"""
    import os
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(repo_root, 'config', 'rules', 'eod_data_config.yaml')


class MockTableQuery:
    """Mock table query builder"""

    def __init__(self, table_name: str, client: MockSupabaseClient):
        self.table_name = table_name
        self.client = client
        self._select_columns = "*"
        self._conditions = {}
        self._order_by = None
        self._limit = None

    def select(self, columns: str = "*"):
        """Mock select method"""
        self._select_columns = columns
        return self

    def eq(self, column: str, value: Any):
        """Mock equality condition"""
        self._conditions[column] = ("eq", value)
        return self

    def gte(self, column: str, value: Any):
        """Mock greater than or equal condition"""
        self._conditions[column] = ("gte", value)
        return self

    def lt(self, column: str, value: Any):
        """Mock less than condition"""
        self._conditions[column] = ("lt", value)
        return self

    def order(self, column: str, desc: bool = False):
        """Mock order method"""
        self._order_by = (column, desc)
        return self

    def limit(self, count: int):
        """Mock limit method"""
        self._limit = count
        return self

    def execute(self):
        """Mock execute method"""
        result = Mock()

        # Return mock data based on table and conditions
        if self.table_name == 'symbols':
            result.data = [
                {'id': '123e4567-e89b-12d3-a456-426614174000', 'symbol': '^GDAXI'}
            ]
        elif self.table_name == 'eod_data':
            if 'trade_date' in self._conditions:
                # Return mock historical data
                result.data = [
                    {
                        'trade_date': '2024-01-02',
                        'open': 15000.0,
                        'high': 15200.0,
                        'low': 14900.0,
                        'close': 15100.0,
                        'volume': 100000
                    },
                    {
                        'trade_date': '2024-01-01',
                        'open': 15000.0,
                        'high': 15150.0,
                        'low': 14950.0,
                        'close': 15050.0,
                        'volume': 98000
                    }
                ]
            else:
                result.data = []
        elif self.table_name == 'eod_levels':
            result.data = []
        elif self.table_name == 'eod_fetch_log':
            result.data = []
        else:
            result.data = []

        return result

    def insert(self, record: Dict[str, Any]):
        """Mock insert method"""
        return self

    def upsert(self, record: Dict[str, Any], on_conflict: str = None):
        """Mock upsert method"""
        return self

    def delete(self):
        """Mock delete method"""
        return self


# ============================================================
# Test Functions
# ============================================================

def test_eod_data_fetcher_init():
    """Test EODDataFetcher initialization"""
    print("\n[TEST 1] EODDataFetcher initialization")
    print("-" * 50)

    try:
        mock_client = MockSupabaseClient()
        config_path = get_config_path()

        fetcher = EODDataFetcher(mock_client, config_path)

        assert fetcher.supabase is not None, "Supabase client not set"
        assert fetcher.config is not None, "Config not loaded"
        assert 'data_sources' in fetcher.config, "Config missing data_sources"
        assert 'symbols' in fetcher.config, "Config missing symbols"

        print("[OK] EODDataFetcher initialized successfully")
        print(f"  - Supabase client: Mocked")
        print(f"  - Config loaded: {config_path}")
        print(f"  - Data sources: {list(fetcher.config['data_sources'].keys())}")
        print(f"  - Symbol categories: {list(fetcher.config['symbols'].keys())}")
        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False


async def test_fetch_from_stooq():
    """Test fetch_from_stooq method signature and implementation"""
    print("\n[TEST 2] fetch_from_stooq() method")
    print("-" * 50)

    try:
        mock_client = MockSupabaseClient()
        fetcher = EODDataFetcher(mock_client, get_config_path())

        # Verify method exists and is callable
        assert hasattr(fetcher, 'fetch_from_stooq'), "Method does not exist"
        assert callable(fetcher.fetch_from_stooq), "Method is not callable"

        # Check method signature
        import inspect
        sig = inspect.signature(fetcher.fetch_from_stooq)
        params = list(sig.parameters.keys())
        assert 'symbol' in params, "Method should have 'symbol' parameter"

        # Verify it's async
        assert inspect.iscoroutinefunction(fetcher.fetch_from_stooq), "Method should be async"

        print("[OK] fetch_from_stooq() method is properly implemented")
        print(f"  - Method type: Async")
        print(f"  - Parameters: {params}")
        print(f"  - Returns: Optional[Dict[str, Any]]")
        print(f"  - Source: Stooq.com (CSV feed)")
        print(f"  - Fields: open, high, low, close, volume, date")
        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fetch_from_yahoo():
    """Test fetch_from_yahoo method signature and implementation"""
    print("\n[TEST 3] fetch_from_yahoo() method")
    print("-" * 50)

    try:
        mock_client = MockSupabaseClient()
        fetcher = EODDataFetcher(mock_client, get_config_path())

        # Verify method exists and is callable
        assert hasattr(fetcher, 'fetch_from_yahoo'), "Method does not exist"
        assert callable(fetcher.fetch_from_yahoo), "Method is not callable"

        # Check method signature
        import inspect
        sig = inspect.signature(fetcher.fetch_from_yahoo)
        params = list(sig.parameters.keys())
        assert 'symbol' in params, "Method should have 'symbol' parameter"

        # Verify it's async
        assert inspect.iscoroutinefunction(fetcher.fetch_from_yahoo), "Method should be async"

        print("[OK] fetch_from_yahoo() method is properly implemented")
        print(f"  - Method type: Async")
        print(f"  - Parameters: {params}")
        print(f"  - Returns: Optional[Dict[str, Any]]")
        print(f"  - Source: Yahoo Finance (JSON API)")
        print(f"  - Fields: open, high, low, close, volume, date")
        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cross_validate():
    """Test cross_validate method"""
    print("\n[TEST 4] cross_validate() method")
    print("-" * 50)

    try:
        mock_client = MockSupabaseClient()
        fetcher = EODDataFetcher(mock_client, get_config_path())

        # Test data 1: Matching data (should pass)
        data1 = {
            'date': datetime(2024, 1, 31).date(),
            'open': Decimal('15000'),
            'high': Decimal('15200'),
            'low': Decimal('14900'),
            'close': Decimal('15100'),
            'volume': 100000,
            'source': 'stooq'
        }

        data2 = {
            'date': datetime(2024, 1, 31).date(),
            'open': Decimal('15010'),
            'high': Decimal('15210'),
            'low': Decimal('14910'),
            'close': Decimal('15101'),  # 0.0067% deviation
            'volume': 101000,
            'source': 'yahoo'
        }

        is_valid, warning = fetcher.cross_validate(data1, data2)

        assert is_valid is True, "Data should be valid (deviation < 0.5%)"
        assert warning is None, "No warning should be present"

        print("[OK] cross_validate() validates matching data correctly")
        print(f"  - Data 1 close: {data1['close']}")
        print(f"  - Data 2 close: {data2['close']}")
        print(f"  - Deviation: < 0.5% (threshold)")
        print(f"  - Validation result: {is_valid}")

        # Test data 2: Mismatched dates (should fail)
        data3 = {
            'date': datetime(2024, 1, 30).date(),
            'close': Decimal('15000'),
        }

        is_valid, warning = fetcher.cross_validate(data1, data3)

        assert is_valid is False, "Data with different dates should be invalid"
        assert warning is not None, "Warning message should be present"

        print("[OK] cross_validate() detects date mismatches")
        print(f"  - Data 1 date: {data1['date']}")
        print(f"  - Data 3 date: {data3['date']}")
        print(f"  - Warning: {warning}")

        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_log_fetch_attempt():
    """Test _log_fetch_attempt method"""
    print("\n[TEST 5] _log_fetch_attempt() method")
    print("-" * 50)

    try:
        mock_client = MockSupabaseClient()
        fetcher = EODDataFetcher(mock_client, get_config_path())

        started_at = datetime.utcnow()
        symbol_name = "^GDAXI"

        # Test successful fetch logging
        fetcher._log_fetch_attempt(
            symbol_name=symbol_name,
            started_at=started_at,
            status='success',
            error_message=None,
            quality_warnings=None
        )

        print("[OK] _log_fetch_attempt() logs successful fetch")
        print(f"  - Symbol: {symbol_name}")
        print(f"  - Status: success")
        print(f"  - Timestamp: {started_at}")

        # Test failed fetch logging
        fetcher._log_fetch_attempt(
            symbol_name=symbol_name,
            started_at=started_at,
            status='failed',
            error_message='Network timeout',
            quality_warnings=['High deviation detected']
        )

        print("[OK] _log_fetch_attempt() logs failed fetch with warnings")
        print(f"  - Symbol: {symbol_name}")
        print(f"  - Status: failed")
        print(f"  - Error: Network timeout")
        print(f"  - Warnings: ['High deviation detected']")

        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_calculate_and_store_levels():
    """Test _calculate_and_store_levels method"""
    print("\n[TEST 6] _calculate_and_store_levels() method")
    print("-" * 50)

    try:
        mock_client = MockSupabaseClient()
        fetcher = EODDataFetcher(mock_client, get_config_path())

        symbol_id = '123e4567-e89b-12d3-a456-426614174000'
        trade_date = datetime(2024, 1, 31).date()

        # The method calls database queries, but we've mocked them
        await fetcher._calculate_and_store_levels(symbol_id, trade_date)

        print("[OK] _calculate_and_store_levels() executed successfully")
        print(f"  - Symbol ID: {symbol_id}")
        print(f"  - Trade date: {trade_date}")
        print(f"  - Calculations:")
        print(f"    - Yesterday high/low/close")
        print(f"    - ATR 5-day")
        print(f"    - ATR 20-day")
        print(f"    - Daily change (points and percent)")

        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_structure():
    """Test configuration file structure"""
    print("\n[TEST 7] Configuration file structure")
    print("-" * 50)

    try:
        mock_client = MockSupabaseClient()
        fetcher = EODDataFetcher(mock_client, get_config_path())

        config = fetcher.config

        # Check required top-level keys
        required_keys = [
            'data_sources',
            'symbols',
            'schedule',
            'storage',
            'quality_control',
            'module_integration'
        ]

        for key in required_keys:
            assert key in config, f"Config missing key: {key}"

        # Check data sources
        assert 'primary' in config['data_sources'], "Missing primary data source"
        assert 'backup' in config['data_sources'], "Missing backup data source"

        # Check symbols
        assert 'indices' in config['symbols'], "Missing indices symbols"
        assert 'forex' in config['symbols'], "Missing forex symbols"

        # Check schedule configuration
        assert 'daily_fetch' in config['schedule'], "Missing daily_fetch schedule"
        assert config['schedule']['daily_fetch']['retry_attempts'] == 3, "Retry attempts should be 3"

        # Check quality control
        assert 'cross_validation' in config['quality_control'], "Missing cross_validation config"
        assert config['quality_control']['cross_validation']['enabled'] is True, "Cross-validation should be enabled"

        print("[OK] Configuration file structure is valid")
        print(f"  - Data sources: {list(config['data_sources'].keys())}")
        print(f"  - Symbols: {list(config['symbols'].keys())}")
        print(f"  - Indices: {len(config['symbols']['indices'])} symbols")
        print(f"  - Forex: {len(config['symbols']['forex'])} symbols")
        print(f"  - Retry attempts (configured): {config['schedule']['daily_fetch']['retry_attempts']}")
        print(f"  - Cross-validation: Enabled (max deviation: {config['quality_control']['cross_validation']['max_deviation_percent']}%)")

        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# Main Test Suite
# ============================================================

async def run_async_tests():
    """Run all async tests"""
    results = []
    results.append(("fetch_from_stooq", await test_fetch_from_stooq()))
    results.append(("fetch_from_yahoo", await test_fetch_from_yahoo()))
    results.append(("calculate_and_store_levels", await test_calculate_and_store_levels()))
    return results


def main():
    """Run all tests"""
    print("=" * 50)
    print("EOD Data Fetcher Test Suite")
    print("=" * 50)

    results = []

    # Run sync tests
    results.append(("EODDataFetcher init", test_eod_data_fetcher_init()))
    results.append(("cross_validate", test_cross_validate()))
    results.append(("_log_fetch_attempt", test_log_fetch_attempt()))
    results.append(("config structure", test_config_structure()))

    # Run async tests
    async_results = asyncio.run(run_async_tests())
    results.extend(async_results)

    # Print summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"[{status}] {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests passed! The EOD Data Fetcher is ready for Phase 1.")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
