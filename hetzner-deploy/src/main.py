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
from typing import Literal
from src.config.supabase import get_supabase_admin
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

@app.post("/api/agents/trigger")
async def trigger_agent(request: TriggerAgentRequest):
    """
    Manually trigger an AI agent task

    Available agents:
    - chart_watcher: ChartWatcher (analyzes charts with OpenAI Vision)
    - morning_planner: MorningPlanner (generates morning setups)
    - journal_bot: JournalBot (generates daily reports)
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
        result = task.apply_async()

        return {
            "success": True,
            "agent": request.agent_name,
            "task_id": result.id,
            "message": f"{request.agent_name} started successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger agent: {str(e)}")


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
