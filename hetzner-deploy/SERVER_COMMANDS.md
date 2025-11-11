# Server Commands (Copy/Paste Ready)

Commands ohne Indent-Probleme - direkt copy/pasten!

---

## Test PriceFetcher Mapping

```bash
cd ~/TradeMatrix/hetzner-deploy/
git pull origin main
docker exec -it tradematrix_fastapi python3 test_price_fetcher.py
```

---

## FastAPI Logs anschauen

```bash
cd ~/TradeMatrix/hetzner-deploy/
docker-compose logs -f fastapi
```

Nur letzte 50 Zeilen:
```bash
docker-compose logs fastapi --tail=50
```

---

## Deployment

```bash
cd ~/TradeMatrix/hetzner-deploy/
git pull origin main
bash deploy.sh
```

---

## Services neu starten

```bash
cd ~/TradeMatrix/hetzner-deploy/
docker-compose restart fastapi
```

---

## Test: yfinance DAX Preis

```bash
docker exec -it tradematrix_fastapi python3 -c "import yfinance as yf; ticker = yf.Ticker('^GDAXI'); print('fast_info:', ticker.fast_info.get('lastPrice')); print('info:', ticker.info.get('regularMarketPrice')); hist = ticker.history(period='1d'); print('history:', hist['Close'].iloc[-1] if not hist.empty else 'empty')"
```

---

## Redis Cache löschen

```bash
cd ~/TradeMatrix/hetzner-deploy/
docker exec tradematrix_redis redis-cli FLUSHDB
```

---

## Container Status

```bash
cd ~/TradeMatrix/hetzner-deploy/
docker-compose ps
```

---

## Health Check

```bash
cd ~/TradeMatrix/hetzner-deploy/
./health_check.sh
```
