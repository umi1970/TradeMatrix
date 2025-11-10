# Aktuelle Commands (Copy/Paste)

Commands für **JETZT** - copy/paste direkt ins Terminal:

---

## 1. Frontend Deployment (Netlify)

```bash
cd apps/web
npm run build
```

Wenn Build erfolgreich:
```bash
git push origin main
```

Netlify deployed automatisch → https://tradematrix.netlify.app

---

## 2. Screenshot Upload Feature nutzen

1. **Gehe zu:** https://tradematrix.netlify.app/dashboard/screenshots
2. **Mache Screenshots** von TradingView Charts (DAX, NDX, DJI, EUR/USD, EUR/GBP, XAG/USD)
3. **Upload** die Screenshots in die jeweiligen Bereiche
4. **Klick "Analyze Screenshots"** → OpenAI Vision extrahiert Preise
5. **Ergebnis:** Preise werden in `current_prices` geschrieben

---

## 3. Trading Setup generieren

Nach dem Upload:
1. **Gehe zu:** https://tradematrix.netlify.app/agents
2. **Klick "Generate Trading Setup"** bei einem Symbol
3. **SetupGenerator nutzt die frischen Preise** aus Screenshots!

---

## 4. Was die Screenshots zeigen sollten

Für beste Ergebnisse:
- ✅ **Symbol Name** sichtbar (z.B. "DAX", "NASDAQ 100")
- ✅ **Current Price** groß und klar sichtbar
- ✅ **Timestamp** (Datum/Uhrzeit) sichtbar
- ✅ **Gute Auflösung** (nicht verpixelt)

**Beispiel TradingView:**
- Öffne Chart für DAX
- Zeige Current Price oben links
- Screenshot machen (Windows: Win+Shift+S, Mac: Cmd+Shift+4)

---

## 5. Kosten

**OpenAI Vision API:**
- GPT-4 Vision: ~$0.01 pro Bild
- 6 Symbole = ~$0.06 pro Upload
- 10x täglich = ~$0.60/Tag = ~$18/Monat

**Vergleich:**
- Alpha Vantage: $49.99/mo
- Finnhub Premium: $59.99/mo
- Screenshot-Lösung: ~$18/mo + 30 Sekunden manuelle Arbeit

---
