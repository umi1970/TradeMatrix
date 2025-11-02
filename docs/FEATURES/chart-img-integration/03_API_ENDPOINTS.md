# API Endpoints

## Overview

FastAPI Endpoints für die chart-img.com Integration. Diese Endpoints ermöglichen die Generierung, Verwaltung und Abfrage von Chart-URLs.

## Base URL

**Local Development**: `http://localhost:8000`
**Production (Hetzner)**: `http://135.181.195.241:8000`

## Authentication

Alle Endpoints außer `/health` erfordern Authentifizierung via Supabase JWT.

```bash
# Include in request header
Authorization: Bearer <supabase_jwt_token>
```

---

## Endpoints

### 1. Generate Chart URL

Generiert eine chart-img.com URL basierend auf Symbol-Konfiguration.

**Endpoint**: `POST /api/v1/charts/generate`

**Request Body**:
```json
{
  "symbol": "^GDAXI",
  "timeframe": "M15",
  "custom_indicators": ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
  "save_snapshot": true,
  "agent_name": "ChartWatcher"
}
```

**Request Schema**:
```python
from pydantic import BaseModel
from typing import List, Optional

class ChartGenerateRequest(BaseModel):
    symbol: str                          # Yahoo symbol (e.g., ^GDAXI)
    timeframe: str                       # M5, M15, H1, H4, D1, W1, M1
    custom_indicators: Optional[List[str]] = None  # Override config indicators
    save_snapshot: bool = True           # Save to chart_snapshots table
    agent_name: Optional[str] = None     # Agent requesting chart
```

**Response**:
```json
{
  "success": true,
  "chart_url": "https://api.chart-img.com/tradingview/advanced-chart?symbol=XETR:DAX&interval=15&studies=RSI@tv-basicstudies,MACD@tv-basicstudies&theme=dark&width=1200&height=800",
  "snapshot_id": "uuid-of-snapshot",
  "cached": false,
  "remaining_requests": 987
}
```

**Response Schema**:
```python
class ChartGenerateResponse(BaseModel):
    success: bool
    chart_url: str
    snapshot_id: Optional[str] = None
    cached: bool
    remaining_requests: int
    error: Optional[str] = None
```

**Status Codes**:
- `200`: Chart URL generated successfully
- `400`: Invalid request (missing symbol, invalid timeframe)
- `401`: Unauthorized (invalid/missing JWT)
- `404`: Symbol not found in database
- `429`: Rate limit exceeded (daily or per-second)
- `500`: Internal server error

**Example Request (curl)**:
```bash
curl -X POST http://localhost:8000/api/v1/charts/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "^GDAXI",
    "timeframe": "M15",
    "save_snapshot": true,
    "agent_name": "ChartWatcher"
  }'
```

**Example Request (Python)**:
```python
import httpx

async def generate_chart():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/charts/generate",
            headers={"Authorization": f"Bearer {jwt_token}"},
            json={
                "symbol": "^GDAXI",
                "timeframe": "M15",
                "save_snapshot": True,
                "agent_name": "ChartWatcher"
            }
        )
        data = response.json()
        return data["chart_url"]
```

---

### 2. Get Chart Snapshots

Ruft gespeicherte Chart-Snapshots ab (mit Filterung).

**Endpoint**: `GET /api/v1/charts/snapshots`

**Query Parameters**:
- `symbol` (optional): Filter by Yahoo symbol (e.g., `^GDAXI`)
- `timeframe` (optional): Filter by timeframe (e.g., `M15`)
- `agent` (optional): Filter by agent name (e.g., `ChartWatcher`)
- `limit` (optional): Max results (default: 50, max: 200)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "success": true,
  "snapshots": [
    {
      "id": "snapshot-uuid-1",
      "symbol": "^GDAXI",
      "symbol_name": "DAX",
      "chart_url": "https://api.chart-img.com/...",
      "timeframe": "M15",
      "created_by_agent": "ChartWatcher",
      "metadata": {
        "indicators": ["RSI@tv-basicstudies"],
        "chart_type": "candles",
        "theme": "dark"
      },
      "created_at": "2025-11-02T10:30:00Z",
      "expires_at": "2026-01-01T10:30:00Z"
    }
  ],
  "total": 127,
  "limit": 50,
  "offset": 0
}
```

**Response Schema**:
```python
class ChartSnapshot(BaseModel):
    id: str
    symbol: str
    symbol_name: str
    chart_url: str
    timeframe: str
    created_by_agent: str
    metadata: dict
    created_at: str
    expires_at: str

class ChartSnapshotsResponse(BaseModel):
    success: bool
    snapshots: List[ChartSnapshot]
    total: int
    limit: int
    offset: int
```

**Example Request (curl)**:
```bash
# Get all snapshots for DAX
curl -X GET "http://localhost:8000/api/v1/charts/snapshots?symbol=^GDAXI&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get ChartWatcher snapshots only
curl -X GET "http://localhost:8000/api/v1/charts/snapshots?agent=ChartWatcher" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 3. Get Latest Chart

Ruft den neuesten Chart-Snapshot für ein Symbol ab.

**Endpoint**: `GET /api/v1/charts/latest/{symbol}`

**Path Parameters**:
- `symbol`: Yahoo symbol (e.g., `^GDAXI`)

**Query Parameters**:
- `timeframe` (optional): Filter by timeframe (e.g., `M15`)

**Response**:
```json
{
  "success": true,
  "snapshot": {
    "id": "snapshot-uuid",
    "symbol": "^GDAXI",
    "symbol_name": "DAX",
    "chart_url": "https://api.chart-img.com/...",
    "timeframe": "M15",
    "created_by_agent": "MorningPlanner",
    "metadata": {
      "indicators": ["MACD@tv-basicstudies"],
      "report_id": "morning-report-2025-11-02"
    },
    "created_at": "2025-11-02T08:00:00Z",
    "expires_at": "2026-01-01T08:00:00Z"
  }
}
```

**Status Codes**:
- `200`: Snapshot found
- `404`: No snapshot found for symbol/timeframe
- `401`: Unauthorized

**Example Request (curl)**:
```bash
# Get latest M15 chart for DAX
curl -X GET "http://localhost:8000/api/v1/charts/latest/^GDAXI?timeframe=M15" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 4. Delete Chart Snapshot

Löscht einen Chart-Snapshot (nur eigene Snapshots).

**Endpoint**: `DELETE /api/v1/charts/snapshots/{snapshot_id}`

**Path Parameters**:
- `snapshot_id`: UUID of snapshot

**Response**:
```json
{
  "success": true,
  "message": "Chart snapshot deleted successfully"
}
```

**Status Codes**:
- `200`: Snapshot deleted
- `403`: Forbidden (not your snapshot)
- `404`: Snapshot not found

**Example Request (curl)**:
```bash
curl -X DELETE http://localhost:8000/api/v1/charts/snapshots/snapshot-uuid \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 5. Get Symbol Chart Config

Ruft die Chart-Konfiguration eines Symbols ab.

**Endpoint**: `GET /api/v1/charts/config/{symbol}`

**Path Parameters**:
- `symbol`: Yahoo symbol (e.g., `^GDAXI`)

**Response**:
```json
{
  "success": true,
  "symbol": "^GDAXI",
  "chart_config": {
    "tv_symbol": "XETR:DAX",
    "timeframes": ["15", "60", "D"],
    "indicators": ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
    "chart_type": "candles",
    "theme": "dark",
    "width": 1200,
    "height": 800,
    "show_volume": true
  }
}
```

**Status Codes**:
- `200`: Config found
- `404`: Symbol not found

**Example Request (curl)**:
```bash
curl -X GET http://localhost:8000/api/v1/charts/config/^GDAXI \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 6. Update Symbol Chart Config

Aktualisiert die Chart-Konfiguration eines Symbols.

**Endpoint**: `PUT /api/v1/charts/config/{symbol}`

**Path Parameters**:
- `symbol`: Yahoo symbol (e.g., `^GDAXI`)

**Request Body**:
```json
{
  "tv_symbol": "XETR:DAX",
  "timeframes": ["15", "60", "240", "D"],
  "indicators": ["RSI@tv-basicstudies", "BB@tv-basicstudies"],
  "chart_type": "candles",
  "theme": "light",
  "width": 1400,
  "height": 900,
  "show_volume": true
}
```

**Request Schema**:
```python
class ChartConfig(BaseModel):
    tv_symbol: str
    timeframes: List[str]
    indicators: List[str] = []
    chart_type: str = "candles"
    theme: str = "dark"
    width: int = 1200
    height: int = 800
    show_volume: bool = True
    show_legend: bool = True
    timezone: str = "Europe/Berlin"
```

**Response**:
```json
{
  "success": true,
  "message": "Chart config updated successfully",
  "chart_config": { /* updated config */ }
}
```

**Status Codes**:
- `200`: Config updated
- `400`: Invalid config
- `403`: Forbidden (not your symbol)
- `404`: Symbol not found

**Example Request (curl)**:
```bash
curl -X PUT http://localhost:8000/api/v1/charts/config/^GDAXI \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tv_symbol": "XETR:DAX",
    "timeframes": ["15", "60", "D"],
    "indicators": ["RSI@tv-basicstudies"],
    "theme": "dark"
  }'
```

---

### 7. Rate Limit Status

Ruft den aktuellen Rate-Limit-Status ab.

**Endpoint**: `GET /api/v1/charts/rate-limit`

**Response**:
```json
{
  "success": true,
  "daily_limit": 1000,
  "daily_used": 247,
  "daily_remaining": 753,
  "per_second_limit": 15,
  "reset_at": "2025-11-03T00:00:00Z"
}
```

**Example Request (curl)**:
```bash
curl -X GET http://localhost:8000/api/v1/charts/rate-limit \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 8. Cleanup Expired Snapshots

Manuelles Cleanup von abgelaufenen Snapshots (Admin only).

**Endpoint**: `POST /api/v1/charts/cleanup`

**Response**:
```json
{
  "success": true,
  "deleted_count": 34,
  "message": "Deleted 34 expired chart snapshots"
}
```

**Status Codes**:
- `200`: Cleanup successful
- `403`: Forbidden (admin only)

---

## Implementation (FastAPI)

### Router Setup

**File**: `services/api/src/routers/charts.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..services.chart_service import ChartService
from ..services.rate_limiter import RateLimiter
from ..dependencies import get_current_user, get_supabase_client
from ..schemas.charts import (
    ChartGenerateRequest,
    ChartGenerateResponse,
    ChartSnapshotsResponse,
    ChartConfig,
)

router = APIRouter(prefix="/api/v1/charts", tags=["charts"])

@router.post("/generate", response_model=ChartGenerateResponse)
async def generate_chart(
    request: ChartGenerateRequest,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """
    Generate a chart URL from chart-img.com API
    """
    chart_service = ChartService(supabase=supabase, user_id=user["id"])
    rate_limiter = RateLimiter()

    # Check rate limits
    if not await rate_limiter.check_daily_limit():
        raise HTTPException(status_code=429, detail="Daily rate limit exceeded")

    if not await rate_limiter.check_per_second_limit():
        raise HTTPException(status_code=429, detail="Per-second rate limit exceeded")

    # Generate chart
    result = await chart_service.generate_chart_url(
        symbol=request.symbol,
        timeframe=request.timeframe,
        custom_indicators=request.custom_indicators,
        save_snapshot=request.save_snapshot,
        agent_name=request.agent_name
    )

    return ChartGenerateResponse(**result)


@router.get("/snapshots", response_model=ChartSnapshotsResponse)
async def get_chart_snapshots(
    symbol: Optional[str] = Query(None),
    timeframe: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """
    Get chart snapshots with optional filtering
    """
    chart_service = ChartService(supabase=supabase, user_id=user["id"])

    result = await chart_service.get_snapshots(
        symbol=symbol,
        timeframe=timeframe,
        agent=agent,
        limit=limit,
        offset=offset
    )

    return ChartSnapshotsResponse(**result)


@router.get("/latest/{symbol}")
async def get_latest_chart(
    symbol: str,
    timeframe: Optional[str] = Query(None),
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """
    Get latest chart snapshot for a symbol
    """
    chart_service = ChartService(supabase=supabase, user_id=user["id"])

    snapshot = await chart_service.get_latest_snapshot(
        symbol=symbol,
        timeframe=timeframe
    )

    if not snapshot:
        raise HTTPException(status_code=404, detail="No chart snapshot found")

    return {"success": True, "snapshot": snapshot}


@router.get("/config/{symbol}")
async def get_chart_config(
    symbol: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """
    Get chart configuration for a symbol
    """
    chart_service = ChartService(supabase=supabase, user_id=user["id"])

    config = await chart_service.get_chart_config(symbol)

    if not config:
        raise HTTPException(status_code=404, detail="Symbol not found")

    return {"success": True, "symbol": symbol, "chart_config": config}


@router.put("/config/{symbol}")
async def update_chart_config(
    symbol: str,
    config: ChartConfig,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """
    Update chart configuration for a symbol
    """
    chart_service = ChartService(supabase=supabase, user_id=user["id"])

    updated_config = await chart_service.update_chart_config(symbol, config.dict())

    return {
        "success": True,
        "message": "Chart config updated successfully",
        "chart_config": updated_config
    }


@router.delete("/snapshots/{snapshot_id}")
async def delete_chart_snapshot(
    snapshot_id: str,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """
    Delete a chart snapshot
    """
    chart_service = ChartService(supabase=supabase, user_id=user["id"])

    success = await chart_service.delete_snapshot(snapshot_id)

    if not success:
        raise HTTPException(status_code=404, detail="Snapshot not found or forbidden")

    return {"success": True, "message": "Chart snapshot deleted successfully"}


@router.get("/rate-limit")
async def get_rate_limit_status(
    user=Depends(get_current_user)
):
    """
    Get current rate limit status
    """
    rate_limiter = RateLimiter()
    status = await rate_limiter.get_status()

    return {"success": True, **status}


@router.post("/cleanup")
async def cleanup_expired_snapshots(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """
    Cleanup expired chart snapshots (admin only)
    """
    # Check if user is admin
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    chart_service = ChartService(supabase=supabase, user_id=user["id"])
    deleted_count = await chart_service.cleanup_expired()

    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} expired chart snapshots"
    }
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": {
    "error": "rate_limit_exceeded",
    "message": "Daily chart API limit exceeded (1000/1000)",
    "retry_after": 43200,
    "timestamp": "2025-11-02T14:30:00Z"
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `rate_limit_exceeded` | Daily or per-second limit reached | 429 |
| `invalid_symbol` | Symbol not found in database | 404 |
| `invalid_timeframe` | Unsupported timeframe | 400 |
| `api_error` | chart-img.com API error | 502 |
| `unauthorized` | Missing/invalid JWT | 401 |
| `forbidden` | Access denied | 403 |
| `internal_error` | Server error | 500 |

---

## Rate Limiting

### Daily Limit (1,000 requests)

```python
# Redis key: chart_api:daily:2025-11-02
# TTL: 24 hours
# Increment on each request
# Return 429 if > 1000
```

### Per-Second Limit (15 requests)

```python
# Redis key: chart_api:second:1730548200
# TTL: 1 second
# Increment on each request
# Return 429 if > 15
```

### Response Headers

```
X-RateLimit-Limit-Daily: 1000
X-RateLimit-Remaining-Daily: 753
X-RateLimit-Reset-Daily: 2025-11-03T00:00:00Z
X-RateLimit-Limit-Second: 15
X-RateLimit-Remaining-Second: 12
```

---

## Testing

### Unit Tests

**File**: `services/api/tests/test_charts.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_generate_chart_success():
    response = client.post(
        "/api/v1/charts/generate",
        headers={"Authorization": f"Bearer {get_test_token()}"},
        json={
            "symbol": "^GDAXI",
            "timeframe": "M15",
            "save_snapshot": True,
            "agent_name": "TestAgent"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "chart_url" in data
    assert "snapshot_id" in data

def test_generate_chart_invalid_symbol():
    response = client.post(
        "/api/v1/charts/generate",
        headers={"Authorization": f"Bearer {get_test_token()}"},
        json={
            "symbol": "INVALID_SYMBOL",
            "timeframe": "M15"
        }
    )
    assert response.status_code == 404

def test_get_snapshots_with_filter():
    response = client.get(
        "/api/v1/charts/snapshots?symbol=^GDAXI&limit=10",
        headers={"Authorization": f"Bearer {get_test_token()}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "snapshots" in data
    assert len(data["snapshots"]) <= 10

def test_rate_limit_exceeded():
    # Make 1001 requests
    for _ in range(1001):
        response = client.post(
            "/api/v1/charts/generate",
            headers={"Authorization": f"Bearer {get_test_token()}"},
            json={"symbol": "^GDAXI", "timeframe": "M15"}
        )

    assert response.status_code == 429
```

---

## Next Steps

1. Review [Frontend Components](./04_FRONTEND_COMPONENTS.md)
2. Implement [Agent Integration](./05_AGENT_INTEGRATION.md)
3. Read [Deployment Guide](./06_DEPLOYMENT.md)

---

**Last Updated**: 2025-11-02
**API Version**: v1
