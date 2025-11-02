#!/usr/bin/env python3
"""
Generate VAPID keys for Web Push in the correct format for pywebpush.
Run this on the Hetzner server to generate new keys.

Installation: pip install py-vapid
"""

import subprocess
import sys

print("=" * 80)
print("🔑 VAPID KEY GENERATOR")
print("=" * 80)
print()

# Run vapid --gen command
try:
    result = subprocess.run(
        ['vapid', '--gen'],
        capture_output=True,
        text=True,
        check=True
    )

    output = result.stdout

    # Parse output
    lines = output.strip().split('\n')

    print("✅ NEW VAPID KEYS GENERATED!")
    print()
    print("=" * 80)
    print("📝 ADD THESE TO YOUR .env FILE:")
    print("=" * 80)
    print()

    # Print formatted for .env
    for line in lines:
        if 'Public Key' in line:
            key = line.split(':', 1)[1].strip()
            print(f'VAPID_PUBLIC_KEY="{key}"')
        elif 'Private Key' in line:
            key = line.split(':', 1)[1].strip()
            print(f'VAPID_PRIVATE_KEY="{key}"')

    print('VAPID_SUBJECT="mailto:info@tradematrix.ai"')
    print()
    print("=" * 80)
    print("⚠️  IMPORTANT STEPS:")
    print("=" * 80)
    print()
    print("1. Copy the keys above to /root/TradeMatrix/hetzner-deploy/.env")
    print("2. Update VAPID_PUBLIC_KEY in frontend:")
    print("   File: apps/web/src/hooks/usePushNotifications.ts")
    print("3. Restart Celery workers: docker-compose restart celery_worker")
    print("4. Users need to RESUBSCRIBE to push notifications (new keys!)")
    print()

except FileNotFoundError:
    print("❌ Error: 'vapid' command not found!")
    print()
    print("Install py-vapid first:")
    print("  pip install py-vapid")
    print()
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"❌ Error generating keys: {e}")
    sys.exit(1)
