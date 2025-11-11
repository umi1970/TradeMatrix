"""
FastAPI Endpoint: Parse TradingView CSV

Receives CSV file, parses it, returns structured analysis
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ParseCSVResponse(BaseModel):
    """Response from CSV parsing"""
    symbol: str
    timeframe: str
    current_price: float
    trend: str
    trend_strength: str
    setup_type: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_reward: Optional[float]
    confidence_score: float
    reasoning: str

    # Full data
    data: dict


@router.post("/parse-csv", response_model=ParseCSVResponse)
async def parse_csv(
    file: UploadFile = File(...),
    symbol: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None)
):
    """
    Parse TradingView CSV file with Pine Script indicators

    Args:
        file: CSV file upload
        symbol: Symbol name (optional, will extract from filename)
        timeframe: Timeframe (optional, will extract from filename)

    Returns:
        Structured analysis data
    """
    logger.info(f"📥 Received CSV upload: {file.filename}")

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # Save to temporary file
    try:
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        logger.info(f"💾 Saved to temp file: {tmp_path}")

        # Parse CSV
        from src.services.tv_csv_parser import parse_tradingview_csv

        result = parse_tradingview_csv(tmp_path, symbol=symbol, timeframe=timeframe)

        logger.info(f"✅ Parsed {result['symbol']} {result['timeframe']}: {result['trend']} trend")

        # Build response
        response = ParseCSVResponse(
            symbol=result['symbol'],
            timeframe=result['timeframe'],
            current_price=result['current_price'],
            trend=result['trend'],
            trend_strength=result['trend_strength'],
            setup_type=result['setup_type'],
            entry_price=result.get('entry_price'),
            stop_loss=result.get('stop_loss'),
            take_profit=result.get('take_profit'),
            risk_reward=result.get('risk_reward'),
            confidence_score=result['confidence_score'],
            reasoning=result['reasoning'],
            data=result  # Full data
        )

        return response

    except ValueError as e:
        logger.error(f"❌ CSV validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"❌ CSV parsing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse CSV: {str(e)}")

    finally:
        # Cleanup temp file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.info(f"🗑️  Cleaned up temp file")
