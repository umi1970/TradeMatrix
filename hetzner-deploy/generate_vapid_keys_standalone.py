#!/usr/bin/env python3
"""
Generate VAPID keys using only standard Python + cryptography library
No py-vapid needed! Works with the cryptography lib already in requirements.txt
"""

import base64
import os

# Use cryptography library (already in requirements.txt!)
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

print("=" * 80)
print("🔑 VAPID KEY GENERATOR (Standalone)")
print("=" * 80)
print()

# Generate EC private key (NIST P-256 curve)
private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

# Get public key
public_key = private_key.public_key()

# Serialize private key to PEM format
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Get public key in uncompressed format (for Web Push)
public_numbers = public_key.public_numbers()
x = public_numbers.x.to_bytes(32, 'big')
y = public_numbers.y.to_bytes(32, 'big')

# Uncompressed point format: 0x04 || X || Y
public_bytes_raw = b'\x04' + x + y

# URL-safe base64 encode (required by Web Push spec)
public_key_b64 = base64.urlsafe_b64encode(public_bytes_raw).decode('utf-8').rstrip('=')

print("✅ NEW VAPID KEYS GENERATED!")
print()
print("=" * 80)
print("📝 ADD THESE TO YOUR .env FILE:")
print("=" * 80)
print()

# Private key as PEM string
print(f'VAPID_PRIVATE_KEY="{private_pem.decode().strip()}"')
print()
print(f'VAPID_PUBLIC_KEY="{public_key_b64}"')
print()
print('VAPID_SUBJECT="mailto:info@tradematrix.ai"')
print()

print("=" * 80)
print("⚠️  IMPORTANT STEPS:")
print("=" * 80)
print()
print("1. Copy the keys above to /root/TradeMatrix/hetzner-deploy/.env")
print("2. Replace OLD keys (that start with LS0tLS1...) with NEW keys")
print("3. Restart Celery workers: docker-compose restart celery_worker")
print("4. Update frontend public key (apps/web/src/hooks/usePushNotifications.ts)")
print("5. Users need to RESUBSCRIBE to push notifications")
print()

print("=" * 80)
print("✅ KEYS GENERATED SUCCESSFULLY!")
print("=" * 80)
print()
print(f"Public Key Length: {len(public_key_b64)} chars")
print(f"Private Key Type: PEM format (PKCS8)")
print()
