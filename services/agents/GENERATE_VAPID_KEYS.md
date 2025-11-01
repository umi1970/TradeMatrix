# How to Generate VAPID Keys for Push Notifications

## What are VAPID Keys?

VAPID (Voluntary Application Server Identification) keys are used to authenticate your server when sending Web Push notifications. They ensure that only your authorized server can send notifications to your users.

## Quick Setup (2 minutes)

### Step 1: Install py-vapid

```bash
pip install py-vapid
```

### Step 2: Generate Keys

```bash
vapid --gen
```

**Output Example:**
```
Generating VAPID keys...

Public Key (Application Server Key):
BNWo7JkF8xQ3ZmVz9FpQG5xY2tLfKjH3mN4oP5qR6sT7uV8wX9yZ0aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3

Private Key (Server Key - Keep Secret!):
aGx1M2N4V5bZ6cA7dB8eC9fD0gE1hF2iG3jH4kI5lJ6mK7nL8oM9pN0qO1rP2sQ3tR4uS5vT6wU7xV8yW9zA0bB1cC2d

VAPID Claims:
  "sub": "mailto:admin@example.com"
```

### Step 3: Add to .env File

Copy the keys to `/services/agents/.env`:

```bash
# Web Push Notifications (VAPID)
VAPID_PUBLIC_KEY=BNWo7JkF8xQ3ZmVz9FpQG5xY2tLfKjH3mN4oP5qR6sT7uV8wX9yZ0aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3
VAPID_PRIVATE_KEY=aGx1M2N4V5bZ6cA7dB8eC9fD0gE1hF2iG3jH4kI5lJ6mK7nL8oM9pN0qO1rP2sQ3tR4uS5vT6wU7xV8yW9zA0bB1cC2d
VAPID_SUBJECT=mailto:info@tradematrix.ai
```

### Step 4: Add Public Key to Frontend

The `VAPID_PUBLIC_KEY` must also be added to your frontend configuration:

```typescript
// apps/web/src/lib/push-notifications.ts
export const VAPID_PUBLIC_KEY = 'BNWo7JkF8xQ3ZmVz9FpQG5xY2tLfKjH3mN4oP5qR6sT7uV8wX9yZ0aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3';
```

## Alternative Method: Using OpenSSL

If you prefer using OpenSSL instead of py-vapid:

```bash
# Generate private key
openssl ecparam -genkey -name prime256v1 -out vapid_private.pem

# Extract public key
openssl ec -in vapid_private.pem -pubout -out vapid_public.pem

# Convert to base64 (for VAPID_PRIVATE_KEY)
openssl ec -in vapid_private.pem -outform DER | tail -c +8 | base64 | tr -d '=' | tr '/+' '_-'

# Convert public key to base64 (for VAPID_PUBLIC_KEY)
openssl ec -in vapid_private.pem -pubout -outform DER | tail -c 65 | base64 | tr -d '=' | tr '/+' '_-'
```

## Security Best Practices

### ✅ DO:
- Keep `VAPID_PRIVATE_KEY` secret (never commit to git)
- Add `.env` to `.gitignore`
- Store keys in environment variables
- Use different keys for development and production
- Rotate keys every 6-12 months

### ❌ DON'T:
- Don't share `VAPID_PRIVATE_KEY` publicly
- Don't commit keys to version control
- Don't reuse keys across different projects
- Don't hardcode keys in source code

## Testing Your Keys

After generating and configuring your keys, test them:

```bash
cd /services/agents

# Test with a user ID (replace with real UUID)
python test_push_service.py --user-id "your-user-uuid-here"
```

Expected output:
```
2️⃣ Checking environment variables...
   ✅ VAPID keys configured
```

## Troubleshooting

### Issue: "VAPID_PRIVATE_KEY not set in .env"

**Solution:**
1. Check that `.env` file exists in `/services/agents/`
2. Verify the key name is exactly `VAPID_PRIVATE_KEY` (case-sensitive)
3. Ensure no extra spaces around the `=` sign
4. Restart your Celery worker after updating `.env`

### Issue: "Invalid VAPID key format"

**Solution:**
- Keys must be base64-encoded (URL-safe)
- No newlines or spaces in the key
- Use the exact output from `vapid --gen`

### Issue: "Public key mismatch between frontend and backend"

**Solution:**
- Ensure the same `VAPID_PUBLIC_KEY` is used in both:
  - Backend: `/services/agents/.env`
  - Frontend: Service Worker configuration
- Keys are case-sensitive

## Key Rotation

When rotating keys (recommended every 6-12 months):

1. **Generate new keys:**
   ```bash
   vapid --gen
   ```

2. **Update backend `.env`:**
   - Replace old keys with new keys
   - Restart Celery workers

3. **Update frontend:**
   - Update `VAPID_PUBLIC_KEY` in frontend code
   - Deploy frontend changes

4. **Users must re-subscribe:**
   - Old subscriptions will become invalid
   - Users need to re-enable notifications
   - Consider sending an email notification about the change

## Production Deployment

### Environment Variables (Recommended)

For production, use environment variables instead of `.env` files:

**Docker:**
```yaml
# docker-compose.yml
services:
  celery-worker:
    environment:
      - VAPID_PUBLIC_KEY=${VAPID_PUBLIC_KEY}
      - VAPID_PRIVATE_KEY=${VAPID_PRIVATE_KEY}
      - VAPID_SUBJECT=mailto:info@tradematrix.ai
```

**Kubernetes:**
```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: vapid-keys
type: Opaque
data:
  public-key: <base64-encoded-public-key>
  private-key: <base64-encoded-private-key>
```

**Cloud Platforms:**
- **Heroku:** `heroku config:set VAPID_PRIVATE_KEY=...`
- **AWS:** Use AWS Secrets Manager
- **Google Cloud:** Use Secret Manager
- **Netlify:** Use environment variables in dashboard

## Resources

- [Web Push Protocol](https://developers.google.com/web/fundamentals/push-notifications)
- [VAPID Specification (RFC 8292)](https://tools.ietf.org/html/rfc8292)
- [py-vapid GitHub](https://github.com/web-push-libs/vapid)
- [Web Push Libraries](https://github.com/web-push-libs)

---

**Last Updated:** 2025-11-01
