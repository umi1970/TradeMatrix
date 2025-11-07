"""
AI Budget Management & Rate Limiting
Centralized utility for tracking OpenAI API usage and enforcing limits
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Literal
from supabase import Client

logger = logging.getLogger(__name__)

# ================================================
# Rate Limit Configuration
# ================================================

# Per-user daily limits based on subscription tier
DAILY_LIMITS = {
    "free": 2,       # 2 AI calls/day
    "starter": 5,    # 5 AI calls/day ($9/mo)
    "pro": 20,       # 20 AI calls/day ($39/mo)
    "expert": 50,    # 50 AI calls/day ($79/mo)
}

# System-wide daily budget (safety net against runaway costs)
SYSTEM_DAILY_BUDGET = 100  # Max 100 AI calls/day across all users

# Estimated costs per model (USD)
MODEL_COSTS = {
    "gpt-4-vision-preview": 0.02,  # ~$0.02 per image analysis
    "gpt-4": 0.03,                 # ~$0.03 per completion (1k tokens)
    "gpt-3.5-turbo": 0.002,        # ~$0.002 per completion
}

# ================================================
# Budget Checking
# ================================================

class AIBudgetError(Exception):
    """Raised when AI budget/rate limit is exceeded"""
    pass


def check_ai_budget(
    user_id: Optional[str],
    tier: Literal["free", "starter", "pro", "expert"],
    supabase: Client
) -> bool:
    """
    Check if user/system has remaining AI budget for today

    Args:
        user_id: User ID (None for system-triggered calls)
        tier: User's subscription tier
        supabase: Supabase admin client

    Returns:
        True if budget available

    Raises:
        AIBudgetError: If daily limit exceeded
    """
    # Calculate 24h ago timestamp
    yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    try:
        # 1. Check user's daily usage (if user_id provided)
        if user_id:
            user_calls_result = supabase.table("ai_usage_log")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", yesterday)\
                .execute()

            user_calls = user_calls_result.count or 0
            user_limit = DAILY_LIMITS.get(tier, DAILY_LIMITS["free"])

            if user_calls >= user_limit:
                logger.warning(f"User {user_id} ({tier}) exceeded daily limit: {user_calls}/{user_limit}")
                raise AIBudgetError(
                    f"Daily AI limit reached ({user_limit} calls). "
                    f"Upgrade to {'Pro' if tier == 'starter' else 'Expert'} for more!"
                )

            logger.info(f"User {user_id} ({tier}): {user_calls}/{user_limit} calls today")

        # 2. Check system-wide budget (safety net)
        system_calls_result = supabase.table("ai_usage_log")\
            .select("id", count="exact")\
            .gte("created_at", yesterday)\
            .execute()

        system_calls = system_calls_result.count or 0

        if system_calls >= SYSTEM_DAILY_BUDGET:
            logger.error(f"System-wide AI budget exceeded: {system_calls}/{SYSTEM_DAILY_BUDGET}")
            raise AIBudgetError(
                "System capacity reached. Please try again tomorrow. "
                "Our AI usage limit helps control costs."
            )

        logger.info(f"System-wide: {system_calls}/{SYSTEM_DAILY_BUDGET} calls today")

        return True

    except AIBudgetError:
        raise
    except Exception as e:
        logger.error(f"Error checking AI budget: {e}")
        # Fail open (allow call) if budget check fails
        # This prevents budget check bugs from breaking the system
        return True


# ================================================
# Usage Logging
# ================================================

def log_ai_usage(
    supabase: Client,
    agent_name: str,
    model: str,
    user_id: Optional[str] = None,
    symbol: Optional[str] = None,
    tokens: Optional[int] = None
) -> None:
    """
    Log an AI API call to the usage table

    Args:
        supabase: Supabase admin client
        agent_name: Name of the agent (chart_watcher, journal_bot, etc.)
        model: OpenAI model used
        user_id: User who triggered the call (None for system calls)
        symbol: Symbol being analyzed (optional)
        tokens: Tokens used (optional, for cost estimation)
    """
    try:
        # Estimate cost based on model
        estimated_cost = MODEL_COSTS.get(model, 0.01)

        # Adjust cost based on tokens if provided
        if tokens and model in ["gpt-4", "gpt-3.5-turbo"]:
            estimated_cost = (tokens / 1000) * MODEL_COSTS[model]

        # Insert usage record
        supabase.table("ai_usage_log").insert({
            "user_id": user_id,
            "agent_name": agent_name,
            "symbol": symbol,
            "model": model,
            "cost": round(estimated_cost, 4)
        }).execute()

        logger.info(f"Logged AI usage: {agent_name} ({model}) - ${estimated_cost:.4f}")

    except Exception as e:
        logger.error(f"Error logging AI usage: {e}")
        # Don't raise - logging failure shouldn't break the agent


# ================================================
# Usage Statistics
# ================================================

def get_user_usage_today(user_id: str, supabase: Client) -> dict:
    """
    Get user's AI usage statistics for today

    Returns:
        {
            'calls_today': int,
            'cost_today': float,
            'limit': int,
            'remaining': int
        }
    """
    yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    try:
        result = supabase.table("ai_usage_log")\
            .select("cost")\
            .eq("user_id", user_id)\
            .gte("created_at", yesterday)\
            .execute()

        calls_today = len(result.data) if result.data else 0
        cost_today = sum(float(row.get("cost", 0)) for row in result.data) if result.data else 0

        # TODO: Get actual user tier from profiles table
        # For now, assume 'free' tier
        tier = "free"
        limit = DAILY_LIMITS[tier]

        return {
            "calls_today": calls_today,
            "cost_today": round(cost_today, 2),
            "limit": limit,
            "remaining": max(0, limit - calls_today)
        }

    except Exception as e:
        logger.error(f"Error getting user usage: {e}")
        return {
            "calls_today": 0,
            "cost_today": 0.0,
            "limit": DAILY_LIMITS["free"],
            "remaining": DAILY_LIMITS["free"]
        }
