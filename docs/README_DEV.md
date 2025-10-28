# Developer Guide – TradeMatrix.ai

This project is modular. Each module handles a distinct process:
MarketData → AIAnalyzer → Validation → Decision → Journal → Report.

## Run Examples

### 1. Fetch and analyze market data
```bash
python src/utils/marketdata_fetcher.py --symbol DAX --interval 5min


Validate a trade setup:
python src/utils/trade_validation_engine.py --signal signal.json

Generate weekly briefing
python src/utils/report_publisher.py --input data/trades_log.json


Developer Notes

Follow PEP8 coding style.

Log every output.

Always commit YAML rule updates before running the system.

All flows use UTC timestamps; convert to CET for reporting.