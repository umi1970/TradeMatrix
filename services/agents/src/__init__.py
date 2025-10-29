"""
TradeMatrix.ai - AI Agents
Intelligent agents for market analysis and trading decisions
"""

__version__ = "0.1.0"

# Agents will be exported here as they are created
# Example:
# from .chart_watcher import ChartWatcher
# from .signal_bot import SignalBot
# from .risk_manager import RiskManager

from .morning_planner import MorningPlanner
from .us_open_planner import USOpenPlanner
from .signal_bot import SignalBot
from .chart_watcher import ChartWatcher

__all__ = ["MorningPlanner", "USOpenPlanner", "SignalBot", "ChartWatcher"]
