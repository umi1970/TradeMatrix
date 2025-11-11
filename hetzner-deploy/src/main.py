"""
TradeMatrix.ai - FastAPI Backend
Simplified backend focused on AI Agents only

Architecture:
- Supabase handles: Database, Auth, Storage, CRUD APIs
- FastAPI handles: AI Agent orchestration, complex business logic
- Celery handles: Background AI tasks
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional
from src.config.supabase import get_supabase_admin
from src.api.analyze_ohlc import router as analyze_ohlc_router
from src.api.generate_pine_script import router as pine_script_router
import os

# Create FastAPI app
app = FastAPI(
    title="TradeMatrix.ai AI Agents API",
    description="AI Agent orchestration for trading analysis",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local dev
        "https://tradematrix.netlify.app",  # Netlify
        "https://tradematrix.ai",  # Production
        "https://*.tradematrix.ai",  # Subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze_ohlc_router, prefix="/api", tags=["TradingView Analysis"])
app.include_router(pine_script_router, prefix="/api", tags=["Pine Script"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "TradeMatrix.ai AI Agents API",
        "version": "0.1.0",
        "status": "healthy",
        "environment": os.getenv('ENVIRONMENT', 'production'),
    }


@app.get("/api/health")
async def health():
    """API health check with Supabase connection test"""
    try:
        # Test Supabase connection
        supabase = get_supabase_admin()
        result = supabase.table("profiles").select("count").execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "database": db_status,
        "environment": os.getenv('ENVIRONMENT', 'production'),
    }


# AI Agent Routes (to be implemented)
# Note: Most CRUD operations go through Supabase auto-generated APIs
# These endpoints are ONLY for AI agent orchestration

class TriggerAgentRequest(BaseModel):
    agent_name: Literal["chart_watcher", "morning_planner", "journal_bot"]
    symbol: Optional[str] = None  # Optional: Single symbol to analyze (e.g., "DAX", "NDX")
    user_id: Optional[str] = None  # Optional: User ID who triggered this (for rate limiting)
    tier: str = "free"  # User's subscription tier (free, starter, pro, expert)

@app.post("/api/agents/trigger")
async def trigger_agent(request: TriggerAgentRequest):
    """
    Manually trigger an AI agent task

    Available agents:
    - chart_watcher: ChartWatcher (analyzes charts with OpenAI Vision)
    - morning_planner: MorningPlanner (generates morning setups)
    - journal_bot: JournalBot (generates daily reports)

    Optional parameters:
    - symbol: Specific symbol to analyze (default: all active symbols)
    """
    try:
        # Import Celery tasks
        from src.tasks import run_chart_analysis_task, run_morning_planner_task, run_journal_bot_task

        # Map agent names to Celery tasks
        task_map = {
            "chart_watcher": run_chart_analysis_task,
            "morning_planner": run_morning_planner_task,
            "journal_bot": run_journal_bot_task,
        }

        task = task_map.get(request.agent_name)
        if not task:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {request.agent_name}")

        # Trigger Celery task asynchronously
        # For chart_watcher: pass symbol, user_id, tier
        # For other agents: only pass user_id, tier if they support it
        if request.agent_name == "chart_watcher":
            # ChartWatcher supports user_id + tier for rate limiting
            result = task.apply_async(kwargs={
                'symbol': request.symbol,
                'user_id': request.user_id,
                'tier': request.tier
            })
        elif request.symbol:
            result = task.apply_async(args=[request.symbol])
        else:
            result = task.apply_async()

        message = f"{request.agent_name} started"
        if request.symbol:
            message += f" for {request.symbol}"
        if request.user_id:
            message += f" (user: {request.user_id}, tier: {request.tier})"

        return {
            "success": True,
            "agent": request.agent_name,
            "symbol": request.symbol,
            "task_id": result.id,
            "message": message
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger agent: {str(e)}")


@app.post("/api/setups/generate-from-analysis")
async def generate_setup_from_analysis(request: dict):
    """
    Generate trading setup with Entry/SL/TP from chart analysis

    Request body:
    {
        "analysis_id": "uuid",
        "timeframe": "1h"  # optional, defaults to analysis timeframe
    }

    Returns:
    {
        "success": true,
        "setup_id": "uuid",
        "setup": { ... }
    }
    """
    try:
        analysis_id = request.get("analysis_id")
        if not analysis_id:
            raise HTTPException(status_code=400, detail="analysis_id is required")

        # Import setup generator v1.3 (ChatGPT-improved)
        from src.setup_generator_v13 import SetupGeneratorV13
        from src.config.supabase import get_supabase_admin
        import os

        # Initialize generator
        generator = SetupGeneratorV13(
            supabase_client=get_supabase_admin(),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

        # Generate setup from analysis
        setup_id = await generator.generate_from_analysis(
            analysis_id=analysis_id,
            timeframe=request.get("timeframe")
        )

        if not setup_id:
            raise HTTPException(status_code=500, detail="Failed to generate setup")

        return {
            "success": True,
            "setup_id": setup_id,
            "message": "Trading setup generated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup generation failed: {str(e)}")


@app.post("/api/agents/generate-signals")
async def generate_signals():
    """
    Trigger SignalBot to generate trading signals
    Runs as background Celery task
    """
    # TODO: Implement SignalBot trigger
    raise HTTPException(status_code=501, detail="SignalBot not implemented yet")


@app.post("/api/agents/risk-check")
async def risk_check():
    """
    Trigger RiskManager to validate trade setup
    Runs synchronously (fast response needed)
    """
    # TODO: Implement RiskManager
    raise HTTPException(status_code=501, detail="RiskManager not implemented yet")


@app.post("/api/agents/generate-report")
async def generate_report():
    """
    Trigger JournalBot to create automated report
    Runs as background Celery task
    """
    # TODO: Implement JournalBot trigger
    raise HTTPException(status_code=501, detail="JournalBot not implemented yet")


@app.get("/api/agents/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of background AI task
    Queries Celery result backend
    """
    # TODO: Implement Celery task status check
    raise HTTPException(status_code=501, detail="Task status check not implemented yet")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
