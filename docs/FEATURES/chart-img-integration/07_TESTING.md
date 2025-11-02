# Testing Checklist

## Overview

Comprehensive testing strategy für die chart-img.com Integration.

---

## Unit Tests

### ChartService Tests

**File**: `services/agents/tests/test_chart_service.py`

```python
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.chart_service import ChartService

@pytest.fixture
def chart_service():
    """Create ChartService instance for testing."""
    return ChartService()

@pytest.fixture
def mock_supabase_response():
    """Mock Supabase response."""
    return {
        "data": {
            "chart_config": {
                "tv_symbol": "XETR:DAX",
                "timeframes": ["15", "60", "D"],
                "indicators": ["RSI@tv-basicstudies"],
                "chart_type": "candles",
                "theme": "dark",
                "width": 1200,
                "height": 800,
                "show_volume": True
            }
        }
    }

class TestChartService:
    """Test suite for ChartService."""

    @pytest.mark.asyncio
    async def test_map_symbol(self, chart_service):
        """Test symbol mapping."""
        assert chart_service.map_symbol("^GDAXI") == "XETR:DAX"
        assert chart_service.map_symbol("^NDX") == "NASDAQ:NDX"
        assert chart_service.map_symbol("UNKNOWN") == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_get_chart_config_success(self, chart_service, mock_supabase_response):
        """Test successful chart config retrieval."""
        with patch.object(chart_service.supabase.table("market_symbols"), "select") as mock_select:
            mock_select.return_value.eq.return_value.single.return_value.execute.return_value = mock_supabase_response

            config = await chart_service.get_chart_config("^GDAXI")

            assert config is not None
            assert config["tv_symbol"] == "XETR:DAX"
            assert "15" in config["timeframes"]

    @pytest.mark.asyncio
    async def test_get_chart_config_not_found(self, chart_service):
        """Test chart config retrieval when symbol not found."""
        with patch.object(chart_service.supabase.table("market_symbols"), "select") as mock_select:
            mock_select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("Not found")

            config = await chart_service.get_chart_config("INVALID_SYMBOL")

            assert config is None

    def test_build_chart_url(self, chart_service):
        """Test chart URL building."""
        url = chart_service.build_chart_url(
            tv_symbol="XETR:DAX",
            timeframe="15",
            indicators=["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
            theme="dark",
            width=1200,
            height=800
        )

        assert "symbol=XETR:DAX" in url
        assert "interval=15" in url
        assert "studies=RSI@tv-basicstudies,MACD@tv-basicstudies" in url
        assert "theme=dark" in url

    def test_get_cache_key(self, chart_service):
        """Test cache key generation."""
        key1 = chart_service.get_cache_key("^GDAXI", "M15", ["RSI@tv-basicstudies"])
        key2 = chart_service.get_cache_key("^GDAXI", "M15", ["RSI@tv-basicstudies"])
        key3 = chart_service.get_cache_key("^GDAXI", "H1", ["RSI@tv-basicstudies"])

        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different timeframe = different key

    @pytest.mark.asyncio
    async def test_check_rate_limits_success(self, chart_service):
        """Test rate limit check when within limits."""
        with patch.object(chart_service, "get_daily_request_count", return_value=500):
            with patch.object(chart_service.redis_client, "incr", return_value=10):
                with patch.object(chart_service.redis_client, "expire"):
                    allowed = await chart_service.check_rate_limits()
                    assert allowed is True

    @pytest.mark.asyncio
    async def test_check_rate_limits_daily_exceeded(self, chart_service):
        """Test rate limit check when daily limit exceeded."""
        with patch.object(chart_service, "get_daily_request_count", return_value=1001):
            allowed = await chart_service.check_rate_limits()
            assert allowed is False

    @pytest.mark.asyncio
    async def test_check_rate_limits_per_second_exceeded(self, chart_service):
        """Test rate limit check when per-second limit exceeded."""
        with patch.object(chart_service, "get_daily_request_count", return_value=500):
            with patch.object(chart_service.redis_client, "incr", return_value=16):  # Over 15/sec
                with patch.object(chart_service.redis_client, "expire"):
                    allowed = await chart_service.check_rate_limits()
                    assert allowed is False

    @pytest.mark.asyncio
    async def test_generate_chart_url_success(self, chart_service, mock_supabase_response):
        """Test successful chart URL generation."""
        with patch.object(chart_service, "get_chart_config", return_value=mock_supabase_response["data"]["chart_config"]):
            with patch.object(chart_service, "check_rate_limits", return_value=True):
                with patch.object(chart_service, "increment_request_count"):
                    with patch.object(chart_service, "get_remaining_requests", return_value=950):
                        with patch.object(chart_service, "save_snapshot", return_value="snapshot-uuid"):
                            result = await chart_service.generate_chart_url(
                                symbol="^GDAXI",
                                timeframe="15",
                                save_snapshot=True,
                                agent_name="TestAgent"
                            )

                            assert result["success"] is True
                            assert "chart_url" in result
                            assert result["snapshot_id"] == "snapshot-uuid"
                            assert result["cached"] is False

    @pytest.mark.asyncio
    async def test_generate_chart_url_cached(self, chart_service):
        """Test chart URL generation with cache hit."""
        cached_url = "https://api.chart-img.com/tradingview/advanced-chart?cached=true"

        with patch.object(chart_service.redis_client, "get", return_value=cached_url):
            with patch.object(chart_service, "get_remaining_requests", return_value=950):
                result = await chart_service.generate_chart_url(
                    symbol="^GDAXI",
                    timeframe="15",
                    agent_name="TestAgent"
                )

                assert result["chart_url"] == cached_url
                assert result["cached"] is True

    @pytest.mark.asyncio
    async def test_generate_chart_url_rate_limit_exceeded(self, chart_service, mock_supabase_response):
        """Test chart URL generation when rate limit exceeded."""
        with patch.object(chart_service, "get_chart_config", return_value=mock_supabase_response["data"]["chart_config"]):
            with patch.object(chart_service, "check_rate_limits", return_value=False):
                with pytest.raises(Exception, match="Rate limit exceeded"):
                    await chart_service.generate_chart_url(
                        symbol="^GDAXI",
                        timeframe="15",
                        agent_name="TestAgent"
                    )

# Run tests
# pytest services/agents/tests/test_chart_service.py -v
```

### Run Unit Tests

```bash
# Navigate to agents directory
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/services/agents

# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run all tests
pytest tests/test_chart_service.py -v

# Run with coverage
pytest tests/test_chart_service.py --cov=src.chart_service --cov-report=html
```

**Expected Output**:
```
tests/test_chart_service.py::TestChartService::test_map_symbol PASSED
tests/test_chart_service.py::TestChartService::test_get_chart_config_success PASSED
tests/test_chart_service.py::TestChartService::test_build_chart_url PASSED
tests/test_chart_service.py::TestChartService::test_check_rate_limits_success PASSED
tests/test_chart_service.py::TestChartService::test_generate_chart_url_success PASSED

========================= 10 passed in 2.34s =========================
```

---

## Integration Tests

### Agent Integration Tests

**File**: `services/agents/tests/test_agent_integration.py`

```python
import pytest
import asyncio
from src.chart_watcher import ChartWatcher
from src.morning_planner import MorningPlanner
from src.journal_bot import JournalBot

@pytest.mark.integration
@pytest.mark.asyncio
async def test_chart_watcher_integration():
    """Test ChartWatcher with real ChartService."""
    chart_watcher = ChartWatcher()

    result = await chart_watcher.analyze_symbol("^GDAXI", timeframes=["M15"])

    assert len(result) == 1
    assert result[0]["timeframe"] == "M15"
    assert "chart_url" in result[0]
    assert "snapshot_id" in result[0]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_morning_planner_integration():
    """Test MorningPlanner with real ChartService."""
    planner = MorningPlanner()

    result = await planner.generate_symbol_setup("^GDAXI")

    assert result["symbol"] == "^GDAXI"
    assert "H1" in result["charts"]
    assert "M15" in result["charts"]
    assert "D1" in result["charts"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_journal_bot_integration():
    """Test JournalBot with real ChartService."""
    journal_bot = JournalBot()

    trade_data = {
        "trade_id": "test-trade-123",
        "symbol": "^GDAXI",
        "timeframe": "M15",
        "entry_price": 18500.50,
        "exit_price": 18550.75,
        "pnl": 50.25
    }

    entry_id = await journal_bot.create_journal_entry(trade_data)

    assert entry_id is not None

# Run integration tests (requires database connection)
# pytest tests/test_agent_integration.py -v -m integration
```

---

## End-to-End Tests

### E2E Test Scenarios

**File**: `services/agents/tests/test_e2e.py`

```python
import pytest
import asyncio
from src.chart_service import ChartService

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_chart_generation_flow():
    """
    E2E Test: Full chart generation flow
    1. Generate chart URL
    2. Verify chart URL is accessible
    3. Verify snapshot saved to database
    4. Verify cache works on second request
    """
    chart_service = ChartService()

    # 1. Generate chart URL
    result1 = await chart_service.generate_chart_url(
        symbol="^GDAXI",
        timeframe="15",
        save_snapshot=True,
        agent_name="E2ETest"
    )

    assert result1["chart_url"].startswith("https://api.chart-img.com")
    assert result1["snapshot_id"] is not None
    assert result1["cached"] is False

    # 2. Verify chart URL is accessible (HTTP GET)
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(result1["chart_url"], timeout=10.0)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/png")

    # 3. Verify snapshot in database
    snapshot = chart_service.supabase.table("chart_snapshots").select("*").eq("id", result1["snapshot_id"]).single().execute()
    assert snapshot.data is not None
    assert snapshot.data["chart_url"] == result1["chart_url"]
    assert snapshot.data["created_by_agent"] == "E2ETest"

    # 4. Verify cache on second request
    result2 = await chart_service.generate_chart_url(
        symbol="^GDAXI",
        timeframe="15",
        save_snapshot=False,
        agent_name="E2ETest"
    )

    assert result2["cached"] is True
    assert result2["chart_url"] == result1["chart_url"]

# Run E2E tests (requires full environment)
# pytest tests/test_e2e.py -v -m e2e
```

---

## Manual Testing Scenarios

### Scenario 1: User Configures Chart Settings

**Steps**:
1. Login to TradeMatrix Dashboard
2. Navigate to Market Symbols
3. Click "Chart Config" for DAX
4. Select timeframes: M15, H1, D1
5. Select indicators: RSI, MACD
6. Switch to Preview tab
7. Verify chart preview loads
8. Click "Save Configuration"
9. Verify toast notification: "Chart configuration saved"

**Expected Result**:
- [ ] Modal opens without errors
- [ ] Preview shows correct chart
- [ ] Config saved to database
- [ ] Toast notification appears

**Verification**:
```sql
SELECT symbol, chart_config FROM market_symbols WHERE symbol = '^GDAXI';
```

---

### Scenario 2: ChartWatcher Generates Charts

**Steps**:
1. SSH into Hetzner server
2. Trigger ChartWatcher task manually:
   ```bash
   docker-compose exec celery-worker celery -A src.tasks call chart_watcher.analyze_all_symbols
   ```
3. Check logs for chart generation messages
4. Verify chart snapshots in database

**Expected Result**:
- [ ] Task completes successfully
- [ ] Logs show "ChartWatcher analyzed {symbol} {timeframe}"
- [ ] `chart_snapshots` table has new entries
- [ ] Chart URLs are accessible

**Verification**:
```sql
SELECT COUNT(*) FROM chart_snapshots WHERE created_by_agent = 'ChartWatcher';
```

---

### Scenario 3: MorningPlanner Daily Report

**Steps**:
1. SSH into Hetzner server
2. Trigger MorningPlanner task:
   ```bash
   docker-compose exec celery-worker celery -A src.tasks call morning_planner.generate_report
   ```
3. Verify 3 charts generated per symbol (H1, M15, D1)
4. Check chart URLs are accessible

**Expected Result**:
- [ ] Task completes successfully
- [ ] 15 chart snapshots created (5 symbols × 3 timeframes)
- [ ] Chart URLs load correctly

**Verification**:
```sql
SELECT symbol, timeframe, chart_url
FROM chart_snapshots cs
JOIN market_symbols ms ON cs.symbol_id = ms.id
WHERE created_by_agent = 'MorningPlanner'
ORDER BY created_at DESC;
```

---

### Scenario 4: Rate Limit Handling

**Steps**:
1. Make 1,000 chart generation requests rapidly
2. On 1,001st request, verify error handling
3. Check Redis counter
4. Verify fallback to cached charts

**Expected Result**:
- [ ] First 1,000 requests succeed
- [ ] 1,001st request returns error or cached chart
- [ ] No crashes or exceptions
- [ ] Redis counter = 1,000

**Verification**:
```bash
docker-compose exec redis redis-cli GET chart_api:daily:$(date +%Y-%m-%d)
# Should return: 1000
```

---

### Scenario 5: Chart Snapshot Gallery

**Steps**:
1. Navigate to Dashboard → Chart Snapshots
2. Verify gallery loads with snapshots
3. Filter by Agent (ChartWatcher)
4. Filter by Timeframe (M15)
5. Click external link icon on a snapshot
6. Verify chart opens in new tab
7. Click delete icon
8. Confirm deletion
9. Verify snapshot removed from gallery

**Expected Result**:
- [ ] Gallery loads without errors
- [ ] Filters work correctly
- [ ] External link opens chart in new tab
- [ ] Delete removes snapshot
- [ ] Gallery refreshes after delete

---

## Performance Testing

### Load Test: Chart Generation

**File**: `services/agents/tests/load_test_chart_service.py`

```python
import asyncio
import time
from src.chart_service import ChartService

async def load_test_chart_generation(concurrent_requests=10, total_requests=100):
    """
    Load test: Generate charts concurrently.

    Args:
        concurrent_requests: Number of concurrent requests
        total_requests: Total number of requests to make
    """
    chart_service = ChartService()

    async def generate_chart(i):
        start = time.time()
        try:
            result = await chart_service.generate_chart_url(
                symbol="^GDAXI",
                timeframe="15",
                save_snapshot=False,
                agent_name="LoadTest"
            )
            elapsed = time.time() - start
            return {"success": True, "elapsed": elapsed, "cached": result["cached"]}
        except Exception as e:
            elapsed = time.time() - start
            return {"success": False, "elapsed": elapsed, "error": str(e)}

    # Run requests in batches
    results = []
    for batch_start in range(0, total_requests, concurrent_requests):
        batch_end = min(batch_start + concurrent_requests, total_requests)
        batch = [generate_chart(i) for i in range(batch_start, batch_end)]
        batch_results = await asyncio.gather(*batch)
        results.extend(batch_results)

    # Analyze results
    successes = sum(1 for r in results if r["success"])
    failures = sum(1 for r in results if not r["success"])
    cached = sum(1 for r in results if r.get("cached", False))
    avg_time = sum(r["elapsed"] for r in results) / len(results)
    max_time = max(r["elapsed"] for r in results)
    min_time = min(r["elapsed"] for r in results)

    print(f"\n=== Load Test Results ===")
    print(f"Total requests: {total_requests}")
    print(f"Concurrent: {concurrent_requests}")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Cached: {cached}")
    print(f"Avg time: {avg_time:.3f}s")
    print(f"Min time: {min_time:.3f}s")
    print(f"Max time: {max_time:.3f}s")

if __name__ == "__main__":
    asyncio.run(load_test_chart_generation(concurrent_requests=15, total_requests=100))
```

**Run Load Test**:
```bash
python services/agents/tests/load_test_chart_service.py
```

**Expected Results**:
- Avg response time: < 500ms (cached), < 2s (uncached)
- Success rate: > 95%
- No rate limit errors (with cache enabled)

---

## Security Testing

### Test RLS Policies

```sql
-- Test as authenticated user
SET ROLE authenticated;
SET request.jwt.claims.sub TO 'user-uuid-here';

-- Should only see own chart configs
SELECT * FROM market_symbols;

-- Should only see own chart snapshots
SELECT * FROM chart_snapshots;

-- Should NOT see other users' snapshots
SELECT * FROM chart_snapshots WHERE symbol_id IN (
    SELECT id FROM market_symbols WHERE user_id != 'user-uuid-here'
);
-- Expected: 0 rows

-- Reset role
RESET ROLE;
```

### Test API Key Protection

```bash
# Check that API key is NOT exposed in frontend
curl https://tradematrix.netlify.app | grep CHART_IMG_API_KEY
# Expected: No matches

# Check that API key is NOT in Git history
git log --all --full-history --source --all -- '*/.env' | grep CHART_IMG_API_KEY
# Expected: No matches
```

---

## Regression Testing

After each deployment, verify:

- [ ] Existing features still work (EOD Levels, Liquidity Alerts)
- [ ] No new console errors in browser
- [ ] Database queries still performant
- [ ] No memory leaks (check Redis/Docker stats)
- [ ] Background tasks still running (Celery Beat)

---

## Testing Checklist Summary

### Unit Tests
- [ ] ChartService.map_symbol()
- [ ] ChartService.get_chart_config()
- [ ] ChartService.build_chart_url()
- [ ] ChartService.check_rate_limits()
- [ ] ChartService.generate_chart_url()
- [ ] ChartService.save_snapshot()

### Integration Tests
- [ ] ChartWatcher integration
- [ ] MorningPlanner integration
- [ ] JournalBot integration
- [ ] Database operations
- [ ] Redis caching

### E2E Tests
- [ ] Full chart generation flow
- [ ] Chart URL accessibility
- [ ] Snapshot persistence
- [ ] Cache behavior

### Manual Tests
- [ ] User configures chart settings
- [ ] ChartWatcher generates charts
- [ ] MorningPlanner daily report
- [ ] Rate limit handling
- [ ] Chart snapshot gallery

### Performance Tests
- [ ] Load test (100 requests)
- [ ] Response time benchmarks
- [ ] Cache hit rate measurement

### Security Tests
- [ ] RLS policies enforcement
- [ ] API key protection
- [ ] HTTPS verification

### Regression Tests
- [ ] Existing features work
- [ ] No new errors
- [ ] Performance maintained

---

## Next Steps

1. Run all unit tests locally
2. Deploy to staging environment
3. Run integration & E2E tests
4. Perform manual testing scenarios
5. Run load tests
6. Deploy to production
7. Monitor for 24 hours

---

**Last Updated**: 2025-11-02
**Test Coverage Goal**: > 80%
