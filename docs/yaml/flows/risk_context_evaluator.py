import json, logging

class RiskContextEvaluator:
    def __init__(self, max_daily_loss_pct=3.0, max_open_trades=5):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_open_trades = max_open_trades
        self.logger = logging.getLogger("RiskContextEvaluator")

    def evaluate(self, account_state: dict):
        balance = account_state.get("balance", 10000)
        equity = account_state.get("equity", balance)
        open_trades = account_state.get("open_trades", 0)
        daily_pnl_pct = account_state.get("daily_pnl_pct", 0)

        exposure_ok = open_trades < self.max_open_trades
        drawdown_ok = daily_pnl_pct > -self.max_daily_loss_pct

        mode = "NORMAL"
        if not drawdown_ok:
            mode = "STOP_TRADING"
        elif not exposure_ok:
            mode = "LIMITED_MODE"

        return {
            "balance": balance,
            "equity": equity,
            "open_trades": open_trades,
            "daily_pnl_pct": daily_pnl_pct,
            "mode": mode,
            "allowed": drawdown_ok and exposure_ok
        }

if __name__ == "__main__":
    test = {"balance": 10000, "equity": 9700, "open_trades": 2, "daily_pnl_pct": -2.1}
    print(json.dumps(RiskContextEvaluator().evaluate(test), indent=2))
