#!/usr/bin/env python3
"""
Test script for Push Notification Service

Prerequisites:
1. Generate VAPID keys: pip install py-vapid && vapid --gen
2. Add keys to .env file
3. Set up user_push_subscriptions table in Supabase
4. Subscribe to push notifications from frontend

Usage:
    python test_push_service.py --user-id <uuid>
"""

import sys
import os
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from push_notification_service import PushNotificationService


def test_push_notification(user_id: str):
    """
    Test sending a push notification to a user

    Args:
        user_id: UUID of the user to send notification to
    """
    print("\n" + "="*70)
    print("🧪 Testing Push Notification Service")
    print("="*70)

    # Initialize service
    print("\n1️⃣ Initializing PushNotificationService...")
    service = PushNotificationService()

    # Check environment variables
    print("\n2️⃣ Checking environment variables...")
    if not service.vapid_private_key:
        print("   ❌ VAPID_PRIVATE_KEY not set in .env")
        return False
    if not service.vapid_public_key:
        print("   ❌ VAPID_PUBLIC_KEY not set in .env")
        return False
    print("   ✅ VAPID keys configured")

    # Get user subscriptions
    print(f"\n3️⃣ Fetching subscriptions for user: {user_id}")
    subscriptions = service.get_user_subscriptions(user_id)

    if not subscriptions:
        print("   ❌ No push subscriptions found for this user")
        print("   💡 Make sure the user has subscribed from the frontend first")
        return False

    print(f"   ✅ Found {len(subscriptions)} subscription(s)")
    for i, sub in enumerate(subscriptions, 1):
        endpoint_preview = sub['endpoint'][:60] + "..."
        print(f"      {i}. {endpoint_preview}")

    # Send test notification
    print("\n4️⃣ Sending test push notification...")
    success = service.send_push_notification(
        user_id=user_id,
        title="🔴 TEST: DAX touched Yesterday High",
        body="Consider: MR-01 (Reversal from Yesterday High)\nLevel: 24,215.38 | Current: 24,214.89",
        data={
            'symbol': 'DAX',
            'level_type': 'yesterday_high',
            'level_price': '24215.38',
            'current_price': '24214.89',
        }
    )

    if success:
        print("\n✅ Push notification sent successfully!")
        print("   Check your browser for the notification")
    else:
        print("\n❌ Failed to send push notification")

    print("\n" + "="*70)
    return success


def main():
    parser = argparse.ArgumentParser(description='Test Push Notification Service')
    parser.add_argument('--user-id', required=True, help='User UUID to send notification to')

    args = parser.parse_args()

    success = test_push_notification(args.user_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
