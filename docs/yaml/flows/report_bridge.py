import json, logging
from datetime import datetime

class ReportBridge:
    def __init__(self):
        self.logger = logging.getLogger("ReportBridge")

    def process(self, final_decision):
        entry = {
            "time": datetime.utcnow().isoformat(),
            "decision": final_decision.get("decision"),
            "reason": final_decision.get("reason"),
            "rr": final_decision.get("rr"),
            "bias_score": final_decision.get("bias_score")
        }
        packet = {
            "title": f"Trade Decision {entry['decision']}",
            "content": json.dumps(entry, indent=2),
            "tags": ["validation", "risk", "journal"]
        }
        return {"journal_entry": entry, "publish_packet": packet}

if __name__ == "__main__":
    fd = {"decision": "EXECUTE", "reason": "All checks passed", "rr": 2.1, "bias_score": 0.85}
    print(json.dumps(ReportBridge().process(fd), indent=2))
