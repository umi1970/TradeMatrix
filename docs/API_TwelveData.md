# Twelve Data API – Vollständige Dokumentation
Version: 1.0  
Sprache: Deutsch  
Erstellt: 28.10.2025  
Projekt: TradeMatrix.ai  

---

## 1. Einführung

**Twelve Data** ist eine REST-API für Echtzeit- und historische Marktdaten (Aktien, Indizes, Forex, Krypto).  
Die API wird über HTTPS aufgerufen und liefert strukturierte JSON-Antworten.

### Basis-URL
https://api.twelvedata.com/

### Authentifizierung
Jede Anfrage erfordert einen API-Key:
?apikey=YOUR_API_KEY
Beispiel:
https://api.twelvedata.com/time_series?symbol=DAX&interval=1h&apikey=YOUR_API_KEY


### Rate Limits
- **Free Plan:** 800 Requests/Tag  
- **Pro Plan:** bis 50.000 Requests/Tag  
- Zu viele Anfragen → HTTP 429: “Rate limit exceeded”

---

## 2. REST-Endpunkte (vollständige Liste)

| Endpoint | Beschreibung |
|-----------|--------------|
| `/time_series` | Historische & aktuelle Kursdaten (Open, High, Low, Close, Volume) |
| `/price` | Aktueller Preis eines Symbols |
| `/quote` | Kompakte Zusammenfassung (Open, High, Low, Close, Volume, Prozentänderung) |
| `/exchange_rate` | Realtime Wechselkurs zwischen zwei Währungen |
| `/indices` | Liste aller verfügbaren Indizes |
| `/forex_pairs` | Liste aller verfügbaren Forex-Paare |
| `/cryptocurrencies` | Liste aller unterstützten Kryptowährungen |
| `/technical_indicators` | Technische Analyseindikatoren wie RSI, EMA, MACD usw. |
| `/api_usage` | Informationen über verbleibende API-Credits |
| `/complex_data` | Mehrfach-Symbole in einem einzigen Request abrufen |

---

## 3. Parameterbeschreibung

| Parameter | Datentyp | Beispiel | Beschreibung |
|------------|-----------|-----------|---------------|
| `symbol` | String | `DAX`, `NASDAQ:IXIC`, `EUR/USD` | Handelsinstrument |
| `interval` | String | `1min`, `5min`, `1h`, `1day` | Zeitintervall |
| `outputsize` | Integer | `100` | Anzahl der Datensätze |
| `format` | String | `JSON` | Ausgabeformat |
| `timezone` | String | `Europe/Berlin` | Zeitkonvertierung |
| `start_date` | String | `2025-10-01` | Startzeitpunkt |
| `end_date` | String | `2025-10-28` | Endzeitpunkt |
| `type` | String | `Stock`, `Index`, `Forex` | Asset-Typ |

---

## 4. Technische Indikatoren

### Unterstützte Indikatoren
RSI, EMA, SMA, MACD, BBANDS, ATR, ADX, OBV, STOCH, VWAP, MOM, ROC, CCI, WMA, DEMA, TRIMA, KAMA, TEMA, SAR, MFI, WILLR, TRIX, BOP, PVI, NVI, CMO, DPO, TSI.

### Beispiel-Request (RSI)
https://api.twelvedata.com/rsi?symbol=DAX&interval=1h&time_period=14&apikey=YOUR_API_KEY


### Beispiel-Response
```json
{
  "meta": {
    "symbol": "DAX",
    "indicator": "RSI",
    "interval": "1h",
    "time_period": 14
  },
  "values": [
    {"datetime": "2025-10-28 13:00:00", "rsi": "54.35"}
  ]
}
5. Integration in TradeMatrix.ai
Ziel

Twelve Data liefert Daten für das Modul
src/utils/marketdata_fetcher.py.

Diese Daten werden anschließend an den
AIAnalyzer → TradeValidationEngine weitergegeben.

Beispiel: MarketDataFetcher
import requests, json

API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.twelvedata.com/time_series"

def fetch_data(symbol="DAX", interval="5min", outputsize=100):
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": API_KEY,
        "timezone": "Europe/Berlin"
    }
    r = requests.get(BASE_URL, params=params)
    data = r.json()

    # Standardisierte Ausgabe für Analyzer
    parsed = {
        "symbol": symbol,
        "interval": interval,
        "ohlcv": data.get("values", []),
        "meta": data.get("meta", {})
    }

    with open(f"data/{symbol}_{interval}.json", "w") as f:
        json.dump(parsed, f, indent=2)

    return parsed

Beispielausgabe (DAX 5-Minuten-Daten)
{
  "symbol": "DAX",
  "interval": "5min",
  "ohlcv": [
    {"datetime": "2025-10-28 09:00", "open": 24250.5, "high": 24300.3, "low": 24197.4, "close": 24220.6, "volume": 1482},
    {"datetime": "2025-10-28 09:05", "open": 24220.6, "high": 24240.1, "low": 24185.9, "close": 24205.3, "volume": 1210}
  ]
}

Weiterleitung an Analyzer
from utils.ai_analyzer import AIAnalyzer

data = fetch_data("DAX", "5min")
analyzer = AIAnalyzer(data)
indicators = analyzer.compute_indicators()
print(indicators)

6. Fehlercodes & Lösungen
Code	Bedeutung	Lösung
400	Ungültige Anfrage	Parameter prüfen
401	Kein oder falscher API-Key	Key einfügen
404	Symbol nicht gefunden	Schreibweise prüfen
429	Rate Limit überschritten	Pause / Upgrade
500	Serverfehler	Retry mit Delay
503	Wartungsmodus	Später erneut versuchen
7. Best Practices

API-Antworten lokal zwischenspeichern (data/)

Zeitzone immer auf Europe/Berlin setzen

Intervalle ≤ 5 min nur bei Bedarf nutzen

Für große Backtests outputsize=5000 (Pro-Plan)

Nach jeder erfolgreichen Abfrage → Sleep(1–2 s)

8. Lizenz & Attribution

Datenquelle: Twelve Data API

© Twelve Data Inc. – Nutzung gemäß Lizenzbedingungen.