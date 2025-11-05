import json, logging

class TradeDecisionEngine:
    def __init__(self):
        self.logger = logging.getLogger("TradeDecisionEngine")

    def decide(self, validation_result, risk_context, high_risk):
        approved = validation_result.get("status") == "APPROVED"
        risk_mode = risk_context.get("mode", "NORMAL")
        final = "REJECT"

        if not approved:
            reason = "Validation failed"
        elif high_risk:
            final = "WAIT"
            reason = "High-impact news ahead"
        elif risk_mode == "STOP_TRADING":
            final = "HALT"
            reason = "Daily loss limit hit"
        elif risk_mode == "LIMITED_MODE":
            final = "REDUCE"
            reason = "Max trades reached"
        else:
            final = "EXECUTE"
            reason = "All checks passed"

        return {
            "decision": final,
            "reason": reason,
            "bias_score": validation_result.get("bias_score"),
            "rr": validation_result.get("rr"),
            "timestamp": validation_result.get("timestamp")
        }

if __name__ == "__main__":
    val = {"status": "APPROVED", "bias_score": 0.83, "rr": 2.1, "timestamp": "2025-11-05T10:00:00"}
    ctx = {"mode": "NORMAL"}
    print(json.dumps(TradeDecisionEngine().decide(val, ctx, False), indent=2))
