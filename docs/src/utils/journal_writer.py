"""
TradeMatrix.ai – JournalWriter
------------------------------
Stores all trades, decisions, and validation results into JSON logs.
"""

import json
from datetime import datetime

class JournalWriter:
    def __init__(self, path="data/trades_log.json"):
        self.path = path

    def log_trade(self, trade_info):
        trade_info["timestamp"] = datetime.now().isoformat()
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        data.append(trade_info)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Logged trade → {trade_info['asset']} @ {trade_info['entry']}")
