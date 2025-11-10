# Aktuelle Commands (Copy/Paste)

Commands für **JETZT** - copy/paste direkt ins Terminal:

---

## 1. Signup für API Keys (PARALLEL!)

### Alpha Vantage
```
https://www.alphavantage.co/support/#api-key
```
- Free: 25 requests/day (zu wenig!)
- Premium: $49.99/mo (5000 requests/day)

### Finnhub
```
https://finnhub.io/register
```
- **FREE Tier:** 60 calls/minute (könnte reichen!)
- Premium: $59.99/mo (300 calls/minute)

---

## 2. API Keys in .env eintragen

Auf dem Server:
```bash
nano ~/TradeMatrix/hetzner-deploy/.env
```

Füge hinzu:
```
ALPHA_VANTAGE_API_KEY=dein_key_hier
FINNHUB_API_KEY=dein_key_hier
```

Save: CTRL+O, Enter, CTRL+X

---

## 3. Test ausführen

```bash
cd ~/TradeMatrix/hetzner-deploy/
git pull origin main
docker-compose restart fastapi
docker exec -it tradematrix_fastapi python3 src/test_alphavantage_finnhub.py
```

**Das zeigt:**
- ✅ Welcher Provider funktioniert
- 💰 Echte Preise (DAX ~24000, NDX ~21000, DOW ~43000)
- ⏰ Timestamps + Age

---

## 4. Nach dem Test

Wenn **Finnhub FREE funktioniert** → PERFEKT, kostet nichts!
Wenn nur Alpha Vantage funktioniert → $49.99/mo

---
