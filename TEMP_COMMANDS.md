# Aktuelle Commands (Copy/Paste)

Commands für **JETZT** - copy/paste direkt ins Terminal:

---

## 1. Frontend Build & Deploy

```bash
cd apps/web
npm run build
```

Wenn erfolgreich, Netlify deployed automatisch (git push wurde gemacht).

---

## 2. Screenshot Analysis testen

1. **Gehe zu:** https://tradematrix.netlify.app/dashboard/screenshots
2. **Upload dow5m.png** (oder andere Chart-Screenshots)
3. **Klick "Analyze Screenshots"**
4. **Warte 10-20 Sekunden** (Vision AI analysiert)
5. **Siehe Ergebnis:**
   - Symbol: Dow Jones
   - Timeframe: 5m
   - Current Price: 47,036
   - Trend: BEARISH (wegen dem Crash)
   - Confidence: ~70-90%
   - Setup Recommendation: SHORT Entry ~47,000, Stop ~47,300, Target ~46,850

---

## 3. Was Vision AI ALLES erkennt:

✅ **Basic Data:** Symbol, Timeframe, OHLC, Current Price
✅ **Indicators:** EMA50 (47,073), EMA200 (47,077), Pivot Points (alle 7 Levels!)
✅ **Levels:** Support (46,950, 46,851), Resistance (47,073, 47,300)
✅ **Trend:** Bearish nach dem 350-Punkte Drop
✅ **Patterns:** Crash, Sharp Rejection, Recovery
✅ **Price Action:** Price UNTER EMAs = Bearish Structure
✅ **Trading Setup:** Entry, Stop, Target mit Reasoning

---

## 4. Wenn Analyse gut ist → Generate Trading Setup

Klick auf "Generate Trading Setup" Button in der Analyse-Card.

Das nutzt die chart_analyses Daten und erstellt ein vollständiges Setup via SetupGenerator!

---

## 5. Workflow (komplett automatisiert!)

```
1. Mache Screenshots (30 Sek für 5-10 Charts)
2. Upload auf /screenshots
3. Vision analysiert ALLES (10-20 Sek pro Chart)
4. Schreibt in chart_analyses
5. Klick "Generate Setup" → SetupGenerator nutzt die Daten
6. FERTIG! Vollständiges Trading Setup basierend auf Chart-Analyse
```

---

## 6. Kosten

**OpenAI Vision (GPT-4o):**
- ~$0.015 pro Bild (mit 2000 tokens Output)
- 10 Charts/Tag = $0.15/Tag = $4.50/Monat
- 50 Charts/Tag = $0.75/Tag = $22.50/Monat

**VIEL günstiger als:**
- Alpha Vantage: $49.99/mo
- Finnhub Premium: $59.99/mo
- Polygon.io: $89/mo

---
