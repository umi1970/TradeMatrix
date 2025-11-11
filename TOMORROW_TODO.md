# TODO für Morgen - Trade Monitoring & Validation

**Datum:** 2025-01-12
**Session:** Trade Lifecycle Management

---

## 🐛 BUGFIX: Screenshot Preview funktioniert nicht

**Problem:**
- Thumbnail-Vorschauen für pending files werden nicht angezeigt
- `URL.createObjectURL(file)` funktioniert nicht wie erwartet

**Location:**
- `apps/web/src/app/(dashboard)/dashboard/screenshots/page.tsx` (Line 428)

**Fix:**
- Console-Check: Werden File-Objekte korrekt gespeichert?
- Alternativ: Base64-Preview statt Blob-URL

---

## 🎯 FEATURE: Setup Card Gültigkeitszeitraum & Trade Monitoring

### 1. Setup Card Status Lifecycle

**Status-Flow:**
```
pending → entry_hit → (monitoring) → tp_hit/sl_hit → completed/failed
```

**States:**
- **pending**: Setup erstellt, wartet auf Entry
- **entry_hit**: Entry-Price wurde erreicht, Trade läuft
- **monitoring**: Trade aktiv, wird überwacht
- **tp_hit**: Take Profit erreicht → ✅ SUCCESS
- **sl_hit**: Stop Loss erreicht → ❌ FAILED
- **expired**: Entry nicht erreicht nach X Stunden → ⏰ EXPIRED

**Gültigkeitszeitraum:**
- Intraday (1m, 5m, 15m): 4-6 Stunden
- Swing (1h, 4h): 1-2 Tage
- Midterm (1d): 3-5 Tage

**Schema Changes:**
```sql
-- Add to setups table:
ALTER TABLE setups ADD COLUMN valid_until TIMESTAMP;
ALTER TABLE setups ADD COLUMN entry_hit_at TIMESTAMP;
ALTER TABLE setups ADD COLUMN monitoring_started_at TIMESTAMP;
ALTER TABLE setups ADD COLUMN closed_at TIMESTAMP;
ALTER TABLE setups ADD COLUMN outcome TEXT; -- 'tp_hit', 'sl_hit', 'expired'
ALTER TABLE setups ADD COLUMN outcome_analysis TEXT; -- Why did it fail?
```

---

### 2. CSV Upload in Setup Card für Trade Monitoring

**Feature:**
- Jede Setup Card bekommt CSV-Upload-Button
- User uploaded 1m oder 5m CSV während Trade läuft
- System prüft automatisch: Entry/SL/TP erreicht?

**UI Changes:**
```tsx
// In trading-setup-card.tsx
{setup.status === 'entry_hit' && (
  <div className="border-t pt-3">
    <p className="text-sm font-medium mb-2">📊 Upload Current Chart Data</p>
    <input type="file" accept=".csv" />
    <Button size="sm">Monitor Trade</Button>
  </div>
)}
```

**Backend Logic:**
1. User uploaded CSV (1m/5m aktueller Timeframe)
2. Parse CSV → aktuelle Price
3. Check:
   - `current_price <= entry_price ± 0.00010` → Entry Hit!
   - `current_price <= stop_loss` → SL Hit! (Long) → FAILED
   - `current_price >= take_profit` → TP Hit! (Long) → SUCCESS
4. Update Setup Status + Timestamp

**API Endpoint:**
```
POST /api/setups/{setup_id}/monitor
Body: FormData with CSV file
Response: { status, hit_level, current_price, outcome }
```

---

### 3. Trade Outcome Analysis (Post-Mortem)

**Bei SL Hit:**
- Automatische Analyse: WARUM hat es nicht funktioniert?
- Fragen:
  1. War die Analyse falsch? (Confluence fehlte)
  2. War der Entry zu früh? (Price reversal)
  3. War der SL zu eng? (Volatility zu hoch)
  4. War der Timeframe falsch? (5m zu noisy, 1h besser?)

**OpenAI Prompt:**
```
Analyze why this trade failed:

ORIGINAL SETUP:
- Symbol: {symbol}
- Entry: {entry_price}
- SL: {stop_loss}
- TP: {take_profit}
- Reasoning: {original_reasoning}
- Confidence: {confidence_score}

ACTUAL OUTCOME:
- Entry Hit At: {entry_hit_at}
- SL Hit At: {sl_hit_at}
- Max Adverse Excursion: {max_drawdown}

CSV DATA (at SL hit):
{csv_data}

Provide:
1. Root Cause: What went wrong?
2. Indicator Analysis: Which indicators failed?
3. Lesson Learned: How to avoid this next time?
4. Improved Strategy: What should we change?
```

**Database:**
```sql
CREATE TABLE trade_lessons (
  id UUID PRIMARY KEY,
  setup_id UUID REFERENCES setups(id),
  outcome TEXT, -- 'sl_hit', 'tp_hit'
  root_cause TEXT,
  failed_indicators TEXT[],
  lesson_learned TEXT,
  improved_strategy TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 4. Minütliches Monitoring (Optional - Phase 2)

**Automatisches Monitoring:**
- Celery Task: Alle 1 Minute
- Fetch aktuelle Prices via yfinance/Twelvedata
- Check alle `entry_hit` Setups
- Update Status bei SL/TP Hit

**Alternative (User-Driven):**
- User uploaded CSV wenn er will
- Keine automatischen API-Kosten
- User-Controlled Monitoring

**Empfehlung:** Start mit User-Driven (CSV Upload), später automatisch

---

## 📊 UI/UX Improvements

### Setup Card Badges:
```tsx
// Validity Badge
{setup.valid_until && new Date() > new Date(setup.valid_until) && (
  <Badge variant="outline" className="text-amber-600">
    ⏰ EXPIRED
  </Badge>
)}

// Monitoring Badge
{setup.status === 'entry_hit' && (
  <Badge className="bg-blue-500">
    👁️ MONITORING
  </Badge>
)}
```

### Timeline Visualization:
```
Created    Entry Hit     Current      TP Target
   |----------|-------------|------------|
   2h ago    30min ago    NOW         +45min
```

---

## 🎯 Implementation Plan

### Priority 1 (Morgen):
1. ✅ Fix Screenshot Preview Bug
2. ✅ Add `valid_until`, `outcome`, `outcome_analysis` to setups table
3. ✅ CSV Upload in Setup Card (UI Component)
4. ✅ Backend: `/api/setups/{id}/monitor` endpoint

### Priority 2 (Übermorgen):
5. ✅ Trade Outcome Analysis (OpenAI Prompt)
6. ✅ `trade_lessons` table + UI
7. ✅ Auto-expire old setups (Cron Job)

### Priority 3 (Später):
8. ⏳ Automatisches Monitoring (Celery + Price Fetcher)
9. ⏳ Chart-img.com integration für Visual Monitoring

---

## 📝 Notizen

- **CSV Monitoring ist akkurater** als chart-img.com (exakte Werte statt Pixel)
- **1m oder 5m CSV** für Intraday Setups
- **User-Driven** monitoring = kein API-Cost, User-Kontrolle
- **Post-Mortem Analysis** = Continuous Learning Loop

---

**Nächste Session startet hier!** 🚀
