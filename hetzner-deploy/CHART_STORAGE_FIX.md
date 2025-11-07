# Chart Image Storage Fix

**Problem:** ChartWatcher gets 403 Forbidden errors when downloading chart URLs from chart-img.com API.

**Root Cause:** chart-img.com URLs expire after generation or require special authentication headers.

**Solution:** Store chart images in Supabase Storage for persistent, public access.

---

## Changes Made

### 1. Modified `src/chart_service.py`

**New Flow:**
```
chart-img.com API → Download PNG bytes → Upload to Supabase Storage → Return Storage URL
```

**Key Changes:**

1. **`generate_chart_url()` Method (Lines 371-475)**
   - After calling chart-img.com API, downloads PNG image bytes
   - Calls new `_upload_to_storage()` helper method
   - Returns Supabase Storage URL instead of chart-img.com URL
   - Caches Supabase Storage URL in Redis

2. **New `_upload_to_storage()` Method (Lines 477-521)**
   - Uploads PNG bytes to Supabase Storage bucket `chart-snapshots`
   - Generates organized path: `{agent_name}/{YYYY}/{MM}/{DD}/{symbol}_{timeframe}_{timestamp}.png`
   - Returns public URL: `https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/chart-snapshots/...`

---

## Storage Structure

### Bucket: `chart-snapshots`

**Path Format:**
```
chart-snapshots/
├── ChartWatcher/
│   ├── 2025/
│   │   ├── 11/
│   │   │   ├── 06/
│   │   │   │   ├── DAX_1h_20251106_143000.png
│   │   │   │   ├── DAX_5m_20251106_143100.png
│   │   │   │   └── EUR-USD_15m_20251106_143200.png
│   │   │   └── 07/
│   │   └── 12/
├── MorningPlanner/
├── JournalBot/
└── TestAgent/
```

**Advantages:**
- Organized by agent and date
- Easy to find charts by timeframe
- Automatic cleanup possible (delete old months)
- Unique filenames prevent collisions

---

## Testing

### Prerequisites

1. **Supabase Storage Bucket:** `chart-snapshots` must exist
2. **Bucket Permissions:** Public read access enabled
3. **Environment Variables:** All set in `.env`

### Test Command

```bash
cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/hetzner-deploy
python3 test_chart_storage.py
```

### Expected Output

```
================================================================================
Chart Storage Upload Test
================================================================================

1️⃣ Initializing ChartService...
✅ ChartService initialized

2️⃣ Generating chart for DAX (1h timeframe)...
✅ Chart generated successfully!
📊 Chart URL: https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/chart-snapshots/TestAgent/2025/11/06/DAX_1h_20251106_143000.png

3️⃣ Verifying Supabase Storage URL format...
✅ URL format correct!
   Bucket: chart-snapshots
   Path: TestAgent/2025/11/06/DAX_1h_20251106_143000.png

4️⃣ Testing download from Supabase Storage URL...
✅ Successfully downloaded 234567 bytes from Storage
✅ Image format verified (PNG)

================================================================================
✅ ALL TESTS PASSED!
================================================================================

Verifications:
  ✅ ChartService initialized
  ✅ Chart generated via chart-img.com API
  ✅ Image uploaded to Supabase Storage
  ✅ Public URL has correct format
  ✅ Image can be downloaded from Storage URL
  ✅ No 403 errors (Storage URL is public)
```

---

## Verification Checklist

### Local Testing

- [ ] Run `python3 test_chart_storage.py`
- [ ] Verify Storage URL format starts with `https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/chart-snapshots/`
- [ ] Verify image downloads successfully (no 403 error)
- [ ] Verify PNG format (bytes start with `\x89PNG`)

### Supabase Dashboard

- [ ] Go to **Storage** → **chart-snapshots** bucket
- [ ] Verify new image files appear in correct path
- [ ] Verify images are viewable in browser
- [ ] Verify bucket has public read access

### Database Table

- [ ] Check `chart_snapshots` table has new records
- [ ] Verify `chart_url` column contains Supabase Storage URLs
- [ ] Verify no chart-img.com URLs in database

```sql
-- Check recent chart snapshots
SELECT
  id,
  timeframe,
  chart_url,
  generated_at
FROM chart_snapshots
ORDER BY generated_at DESC
LIMIT 5;

-- Verify all URLs are Supabase Storage URLs
SELECT COUNT(*) AS total_snapshots,
       COUNT(*) FILTER (WHERE chart_url LIKE '%supabase.co/storage%') AS storage_urls,
       COUNT(*) FILTER (WHERE chart_url LIKE '%chart-img.com%') AS chart_img_urls
FROM chart_snapshots;
```

Expected: `storage_urls = total_snapshots`, `chart_img_urls = 0`

---

## ChartWatcher Integration

**No Changes Required!**

ChartWatcher already uses `ChartService.generate_chart_url()`, which now returns Supabase Storage URLs automatically.

**Workflow:**
1. ChartWatcher calls `generate_chart_url()`
2. ChartService generates chart → uploads to Storage → returns Storage URL
3. ChartWatcher saves Storage URL to `chart_snapshots` table
4. ChartWatcher downloads from Storage URL (no 403 error!)
5. OpenAI Vision API analyzes image

---

## Deployment

### Step 1: Create Supabase Storage Bucket

**Supabase Dashboard:**
1. Go to **Storage** → **Create new bucket**
2. **Name:** `chart-snapshots`
3. **Public:** ✅ Enable (allow public read access)
4. **File size limit:** 10 MB
5. **Allowed MIME types:** `image/png`, `image/jpeg`

### Step 2: Deploy Updated Code

```bash
# SSH into Hetzner server
ssh root@135.181.195.241

# Navigate to deployment directory
cd /opt/tradematrix

# Pull latest changes
git pull origin main

# Restart Celery Worker
docker-compose restart celery-worker

# Check logs
docker-compose logs -f celery-worker
```

### Step 3: Verify Deployment

```bash
# SSH into server
ssh root@135.181.195.241

# Check Supabase Storage upload works
docker-compose exec celery-worker python3 /app/test_chart_storage.py

# Monitor ChartWatcher logs
docker-compose logs -f celery-worker | grep ChartWatcher
```

Expected:
```
✅ Chart generated and uploaded: DAX 1h
📊 Storage URL: https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/chart-snapshots/...
✅ Chart uploaded to storage: ChartWatcher/2025/11/06/DAX_1h_20251106_143000.png
```

---

## Troubleshooting

### Error: "bucket chart-snapshots not found"

**Solution:**
1. Go to Supabase Dashboard → Storage
2. Create bucket `chart-snapshots` with public read access

### Error: "403 Forbidden" on Storage URL

**Solution:**
1. Supabase Dashboard → Storage → `chart-snapshots` → Settings
2. Enable **Public access**
3. Verify RLS policies allow public SELECT

### Error: "Image upload failed"

**Solution:**
1. Check `SUPABASE_SERVICE_KEY` is set (not anon key)
2. Verify bucket exists and is writable
3. Check file size < 10 MB
4. Check MIME type is `image/png`

### Error: "Permission denied"

**Solution:**
1. Use admin client (`get_supabase_admin()`)
2. Verify service role key has storage admin permissions

---

## API Usage Impact

**Before:** 1 request per chart generation

**After:** Still 1 request per chart generation (no change!)

**Storage Upload:**
- Uses Supabase Storage API (unlimited uploads)
- No additional chart-img.com API calls
- Redis cache still reduces API usage

**Cost:**
- Supabase Storage: Free tier (1 GB, enough for ~4000 charts @ 250 KB each)
- No additional chart-img.com costs

---

## Rollback Plan

If issues occur, revert to old behavior:

```python
# In generate_chart_url(), replace:
storage_url = self._upload_to_storage(...)
return storage_url

# With:
chart_url = f"{self.base_url}/v2/tradingview/advanced-chart"
return chart_url
```

**Note:** Old behavior will bring back 403 errors!

---

## Summary

**Changes:**
- ✅ Modified `generate_chart_url()` to upload to Supabase Storage
- ✅ Added `_upload_to_storage()` helper method
- ✅ Created test script `test_chart_storage.py`
- ✅ Organized storage path structure

**Benefits:**
- ✅ No more 403 Forbidden errors
- ✅ Persistent chart storage (60+ days)
- ✅ Public URLs work everywhere
- ✅ Easy to manage and cleanup

**Next Steps:**
1. Run test script locally
2. Verify Supabase Storage bucket exists
3. Deploy to Hetzner server
4. Monitor ChartWatcher logs
5. Verify chart analyses succeed

---

**Date:** 2025-11-06
**Author:** Claude (Sonnet 4.5)
**Status:** Ready for Testing
