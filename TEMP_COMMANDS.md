# Aktuelle Commands (Copy/Paste)

Commands für **JETZT** - copy/paste direkt ins Terminal:

---

## 1. FastAPI Logs mit ERROR Messages

```bash
cd ~/TradeMatrix/hetzner-deploy/
docker-compose logs fastapi --tail=100 | grep -A 5 -B 5 "ERROR\|Exception\|Traceback"
```

Wenn das nichts zeigt, dann alle logs:

```bash
docker-compose logs fastapi --tail=200
```

---

## 2. Test PriceFetcher direkt

```bash
docker exec -it tradematrix_fastapi python3 src/test_price_fetcher.py
```

---

## 3. Deployment (falls Fix nötig)

```bash
cd ~/TradeMatrix/hetzner-deploy/
git pull origin main
bash deploy.sh
```

---
