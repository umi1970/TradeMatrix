"""
TradeMatrix.ai – TradeValidationEngine
--------------------------------------
Validates all trade setups before execution.
Applies rule-based and score-based logic.
"""

class TradeValidationEngine:
    def __init__(self, ruleset):
        self.ruleset = ruleset

    def validate(self, signal):
        """
        Evaluate trade setup according to the MR-rules confidence weights.
        """
        score = (
            0.25 * signal["ema_alignment"]
            + 0.20 * signal["pivot_confluence"]
            + 0.20 * signal["volume"]
            + 0.20 * signal["candle_structure"]
            + 0.15 * signal["context_flow"]
        )

        if signal.get("mr_rule") in ["MR-04", "MR-06"]:
            score += 0.05  # bonus for strong reversal zones

        print(f"Validation Score: {score:.2f}")
        return score >= 0.75
