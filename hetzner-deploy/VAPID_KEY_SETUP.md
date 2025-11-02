# VAPID Keys Setup for Web Push Notifications

## Problem

VAPID keys need to be in the correct format for pywebpush library.

**Current Error:**
```
❌ Could not deserialize key data... header too long
```

## Solution: Generate New VAPID Keys

### On Hetzner Server:

```bash
# 1. Navigate to deployment directory
cd /root/TradeMatrix/hetzner-deploy

# 2. Install py-vapid (if not installed)
pip install py-vapid

# 3. Run key generator
python3 generate_vapid_keys.py
```

This will output NEW keys in the correct format:

```
VAPID_PUBLIC_KEY="BH5..."
VAPID_PRIVATE_KEY="oN8..."
VAPID_SUBJECT="mailto:info@tradematrix.ai"
```

### Steps:

1. **Copy generated keys to .env file:**
   ```bash
   nano /root/TradeMatrix/hetzner-deploy/.env
   ```

   Replace old VAPID keys with new ones.

2. **Update Frontend (IMPORTANT!):**
   ```bash
   # On your development machine
   nano apps/web/src/hooks/usePushNotifications.ts
   ```

   Update the public key:
   ```typescript
   const publicKey = 'NEW_PUBLIC_KEY_HERE'
   ```

3. **Restart Celery workers:**
   ```bash
   docker-compose restart celery_worker celery_beat
   ```

4. **Users must RESUBSCRIBE:**
   - Old subscriptions won't work with new keys
   - Users need to click "Enable Notifications" again in the app

## Verification

Check logs after restart:
```bash
docker-compose logs -f celery_worker
```

You should see:
```
🎯 1 alert(s) triggered!
✅ Notification sent: EURUSD (yesterday_low)
```

## Alternative: Manual Generation

```bash
# Install py-vapid
pip install py-vapid

# Generate keys
vapid --gen

# Output:
# Public Key: BH5...
# Private Key: oN8...
```

Add to .env:
```env
VAPID_PUBLIC_KEY="BH5..."
VAPID_PRIVATE_KEY="oN8..."
VAPID_SUBJECT="mailto:info@tradematrix.ai"
```

## Why This Is Needed

pywebpush expects VAPID keys in one of these formats:
1. **URL-safe base64 string** (recommended) ← from `vapid --gen`
2. **PEM-encoded private key** (-----BEGIN PRIVATE KEY-----)

The old keys were base64-encoded PEM files, which caused decoding issues.

New keys from `vapid --gen` are in the correct URL-safe base64 format.
