# System Architecture

## Module Overview
1. **MarketDataFetcher** – holt Kursdaten (Twelve Data, Stock3)
2. **AIAnalyzer** – berechnet Indikatoren (EMA, RSI, MACD, BB, ATR, Ichimoku)
3. **TradeValidationEngine** – bewertet Signale nach Struktur und Volumen
4. **TradeDecisionEngine** – trifft finale Entry/Exit-Entscheidung
5. **RiskManager** – berechnet SL/TP, 1 %-Regel, Break-Even
6. **JournalWriter** – schreibt JSON-/DOCX-Reports
7. **ReportPublisher** – publiziert auf Google Drive / Make.com
8. **EventWatcher** – verarbeitet CPI, FOMC, NFP, Shutdown-News
9. **USOpenPlanner** – plant 15:30 – 16:30 Setups

## Data Flow
Alle Module speichern Daten in Supabase (JSON) und Google Drive (DOCX).  
Automation via Make.com-Flows.
