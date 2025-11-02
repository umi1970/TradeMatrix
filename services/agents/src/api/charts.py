#!/usr/bin/env python3
"""
FastAPI Router for Chart Generation
Provides REST API endpoints for chart-img.com integration

Endpoints:
- POST /api/charts/generate - Generate new chart
- GET /api/charts/snapshots/{symbol_id} - Get chart snapshots
- GET /api/charts/usage - Get API usage stats
- DELETE /api/charts/snapshots/{snapshot_id} - Delete snapshot
- GET /api/charts/config/{symbol_id} - Get symbol chart config
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from chart_generator import ChartGenerator
from exceptions.chart_errors import (
    RateLimitError,
    ChartGenerationError,
    SymbolNotFoundError,
    InvalidTimeframeError,
    ChartAPIError,
)


# =====================================================================
# PYDANTIC MODELS
# =====================================================================

class ChartGenerateRequest(BaseModel):
    """Request body for chart generation"""
    symbol_id: str = Field(..., description="UUID of the symbol")
    timeframe: str = Field(..., description="Chart timeframe (1h, 4h, 1d, etc.)")
    trigger_type: str = Field(
        default="manual",
        description="What triggered generation (manual, report, alert, etc.)"
    )
    user_id: Optional[str] = Field(None, description="User UUID (optional)")
    force_refresh: bool = Field(
        default=False,
        description="Skip cache and force new generation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "symbol_id": "123e4567-e89b-12d3-a456-426614174000",
                "timeframe": "4h",
                "trigger_type": "manual",
                "user_id": "987fcdeb-51a2-43d1-9012-345678901234",
                "force_refresh": False
            }
        }


class ChartGenerateResponse(BaseModel):
    """Response for successful chart generation"""
    chart_url: str = Field(..., description="URL to the generated chart image")
    snapshot_id: Optional[str] = Field(None, description="UUID of the snapshot record")
    cached: bool = Field(..., description="Whether this was served from cache")
    generated_at: str = Field(..., description="ISO timestamp when chart was generated")
    expires_at: Optional[str] = Field(None, description="ISO timestamp when chart expires")
    metadata: Optional[dict] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "chart_url": "https://chart-img.com/i/abc123.png",
                "snapshot_id": "456e7890-a12b-34c5-d678-901234567890",
                "cached": False,
                "generated_at": "2025-11-02T14:30:00Z",
                "expires_at": "2025-12-31T23:59:59Z",
                "metadata": {
                    "symbol": "^GDAXI",
                    "tradingview_symbol": "XETR:DAX",
                    "indicators": ["EMA_20", "EMA_50", "RSI"]
                }
            }
        }


class ChartSnapshotResponse(BaseModel):
    """Response for chart snapshot query"""
    id: str
    symbol_id: str
    timeframe: str
    chart_url: str
    trigger_type: str
    generated_by: Optional[str]
    generated_at: str
    expires_at: Optional[str]
    metadata: Optional[dict]


class UsageStatsResponse(BaseModel):
    """Response for API usage statistics"""
    requests_today: int
    limit_daily: int
    remaining: int
    percentage_used: float
    warning_threshold: int
    hard_stop_threshold: int
    date: str

    class Config:
        json_schema_extra = {
            "example": {
                "requests_today": 245,
                "limit_daily": 1000,
                "remaining": 755,
                "percentage_used": 24.5,
                "warning_threshold": 800,
                "hard_stop_threshold": 950,
                "date": "2025-11-02"
            }
        }


class SymbolConfigResponse(BaseModel):
    """Response for symbol chart configuration"""
    id: str
    symbol: str
    chart_img_symbol: str
    chart_enabled: bool
    chart_config: dict

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "symbol": "^GDAXI",
                "chart_img_symbol": "XETR:DAX",
                "chart_enabled": True,
                "chart_config": {
                    "timeframes": ["1h", "4h", "1d"],
                    "indicators": ["EMA_20", "EMA_50", "EMA_200", "RSI", "Volume"],
                    "default_timeframe": "4h",
                    "theme": "dark"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    details: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Rate limit exceeded: 950/1000 requests used",
                "details": {
                    "current_count": 950,
                    "limit": 1000,
                    "reset_time": "2025-11-03T00:00:00Z",
                    "percentage_used": 95.0
                }
            }
        }


# =====================================================================
# ROUTER SETUP
# =====================================================================

router = APIRouter(
    prefix="/api/charts",
    tags=["charts"],
    responses={
        HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    }
)


# =====================================================================
# DEPENDENCY: CHART GENERATOR INSTANCE
# =====================================================================

def get_chart_generator() -> ChartGenerator:
    """Dependency to get ChartGenerator instance"""
    return ChartGenerator()


# =====================================================================
# ENDPOINTS
# =====================================================================

@router.post(
    "/generate",
    response_model=ChartGenerateResponse,
    status_code=HTTP_201_CREATED,
    summary="Generate Chart",
    description="Generate a new trading chart via chart-img.com API",
    responses={
        HTTP_201_CREATED: {
            "description": "Chart generated successfully",
            "model": ChartGenerateResponse
        },
        HTTP_400_BAD_REQUEST: {
            "description": "Invalid request (bad timeframe, symbol not found, etc.)",
            "model": ErrorResponse
        },
        HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded",
            "model": ErrorResponse
        }
    }
)
async def generate_chart(
    request: ChartGenerateRequest,
    generator: ChartGenerator = Depends(get_chart_generator)
):
    """
    Generate a new trading chart

    **Rate Limits:**
    - 1,000 requests per day
    - 15 requests per second
    - Warning at 80% (800 requests)
    - Hard stop at 95% (950 requests)

    **Caching:**
    - Charts are cached for 5 minutes
    - Use `force_refresh=true` to bypass cache

    **Example:**
    ```json
    {
      "symbol_id": "123e4567-e89b-12d3-a456-426614174000",
      "timeframe": "4h",
      "trigger_type": "manual",
      "user_id": "987fcdeb-51a2-43d1-9012-345678901234"
    }
    ```
    """
    try:
        result = generator.generate_chart(
            symbol_id=request.symbol_id,
            timeframe=request.timeframe,
            trigger_type=request.trigger_type,
            user_id=request.user_id,
            force_refresh=request.force_refresh
        )

        return ChartGenerateResponse(**result)

    except RateLimitError as e:
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": e.message,
                "details": e.details
            }
        )

    except SymbolNotFoundError as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail={
                "error": e.message,
                "details": e.details
            }
        )

    except InvalidTimeframeError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail={
                "error": e.message,
                "details": e.details
            }
        )

    except ChartAPIError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": f"chart-img.com API error: {e.message}",
                "details": e.details
            }
        )

    except ChartGenerationError as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": e.message,
                "details": e.details
            }
        )


@router.get(
    "/snapshots/{symbol_id}",
    response_model=List[ChartSnapshotResponse],
    status_code=HTTP_200_OK,
    summary="Get Chart Snapshots",
    description="Retrieve all chart snapshots for a symbol",
)
async def get_chart_snapshots(
    symbol_id: str,
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    limit: int = Query(10, ge=1, le=100, description="Max number of snapshots to return"),
    generator: ChartGenerator = Depends(get_chart_generator)
):
    """
    Get all chart snapshots for a symbol

    **Query Parameters:**
    - `timeframe` (optional): Filter by specific timeframe (e.g., "4h")
    - `limit`: Max number of snapshots (default: 10, max: 100)

    **Returns:** List of chart snapshots ordered by generation time (newest first)
    """
    try:
        query = generator.supabase.table('chart_snapshots')\
            .select('*')\
            .eq('symbol_id', symbol_id)\
            .order('generated_at', desc=True)\
            .limit(limit)

        if timeframe:
            query = query.eq('timeframe', timeframe)

        response = query.execute()

        if not response.data:
            return []

        return [ChartSnapshotResponse(**snapshot) for snapshot in response.data]

    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": f"Error fetching snapshots: {str(e)}"
            }
        )


@router.get(
    "/usage",
    response_model=UsageStatsResponse,
    status_code=HTTP_200_OK,
    summary="Get API Usage Stats",
    description="Get current API usage statistics and rate limits",
)
async def get_usage_stats(
    generator: ChartGenerator = Depends(get_chart_generator)
):
    """
    Get API usage statistics

    **Returns:**
    - Number of requests made today
    - Daily limit
    - Remaining requests
    - Percentage used
    - Warning and hard-stop thresholds
    """
    try:
        stats = generator.get_usage_stats()

        if 'error' in stats:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": stats['error']}
            )

        return UsageStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error fetching usage stats: {str(e)}"}
        )


@router.delete(
    "/snapshots/{snapshot_id}",
    status_code=HTTP_200_OK,
    summary="Delete Chart Snapshot",
    description="Delete a chart snapshot by ID",
)
async def delete_chart_snapshot(
    snapshot_id: str,
    generator: ChartGenerator = Depends(get_chart_generator)
):
    """
    Delete a chart snapshot

    **Note:** This only deletes the database record, not the image on chart-img.com
    (chart-img.com will auto-delete after 60 days)
    """
    try:
        response = generator.supabase.table('chart_snapshots')\
            .delete()\
            .eq('id', snapshot_id)\
            .execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail={"error": f"Snapshot not found: {snapshot_id}"}
            )

        return {
            "success": True,
            "message": f"Snapshot deleted: {snapshot_id}",
            "deleted_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error deleting snapshot: {str(e)}"}
        )


@router.get(
    "/config/{symbol_id}",
    response_model=SymbolConfigResponse,
    status_code=HTTP_200_OK,
    summary="Get Symbol Chart Config",
    description="Get chart configuration for a symbol",
)
async def get_symbol_config(
    symbol_id: str,
    generator: ChartGenerator = Depends(get_chart_generator)
):
    """
    Get chart configuration for a symbol

    **Returns:**
    - Symbol details
    - TradingView symbol mapping
    - Chart settings (timeframes, indicators, theme)
    """
    try:
        response = generator.supabase.table('symbols')\
            .select('id, symbol, chart_img_symbol, chart_enabled, chart_config')\
            .eq('id', symbol_id)\
            .limit(1)\
            .execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail={"error": f"Symbol not found: {symbol_id}"}
            )

        symbol_data = response.data[0]

        if not symbol_data.get('chart_enabled'):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Chart generation not enabled for this symbol",
                    "symbol": symbol_data.get('symbol')
                }
            )

        return SymbolConfigResponse(**symbol_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error fetching symbol config: {str(e)}"}
        )


@router.post(
    "/cleanup-expired",
    status_code=HTTP_200_OK,
    summary="Cleanup Expired Snapshots",
    description="Delete all expired chart snapshots (admin endpoint)",
)
async def cleanup_expired_snapshots(
    generator: ChartGenerator = Depends(get_chart_generator)
):
    """
    Cleanup expired chart snapshots

    **Note:** This should be run periodically via cron/scheduler
    """
    try:
        deleted_count = generator.cleanup_expired_snapshots()

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} expired snapshots",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Error cleaning up snapshots: {str(e)}"}
        )
