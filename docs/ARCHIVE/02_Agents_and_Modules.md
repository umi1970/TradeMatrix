# Agents and Modules

| Agent | Aufgabe | Flow |
|-------|----------|------|
| ChartWatcher | Beobachtet Charts, EMAs, Pivot-Levels | MorningPlanner |
| SignalBot | Erzeugt Long/Short-Signale | MorningPlanner |
| RiskManager | SL/TP, 1 %-Regel, BE @ +0,5 % | RiskManagement |
| JournalBot | Protokolliert Trades | TradeJournalWriter |
| Publisher | Erstellt DOCX-/JSON-Reports | ReportPublisher |
| EventWatcher | Makro-Events (CPI, FOMC ...) | NewsEventReaction |
| SpikeDetector | erkennt Volumen-Spitzen | MorningPlanner |
| USOpenPlanner | bewertet US-Open 15:30 – 16:30 | USOpenPlanner |
