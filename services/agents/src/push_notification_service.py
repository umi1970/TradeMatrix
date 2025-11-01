#!/usr/bin/env python3
"""
Web Push Notification Service
Sends browser push notifications to users

VAPID Key Generation:
To generate VAPID keys for Web Push notifications, run:
    pip install py-vapid
    vapid --gen

This will output:
    Public Key: <base64-encoded-public-key>
    Private Key: <base64-encoded-private-key>

Add these to your .env file:
    VAPID_PUBLIC_KEY=<public-key>
    VAPID_PRIVATE_KEY=<private-key>
    VAPID_SUBJECT=mailto:info@tradematrix.ai

The public key should also be added to your frontend service worker registration.
"""

import os
import json
from typing import Dict, List, Optional
from pywebpush import webpush, WebPushException
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class PushNotificationService:
    """Send Web Push notifications to subscribed users"""

    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )

        # VAPID keys for Web Push
        self.vapid_private_key = os.getenv('VAPID_PRIVATE_KEY')
        self.vapid_public_key = os.getenv('VAPID_PUBLIC_KEY')
        self.vapid_claims = {
            "sub": os.getenv('VAPID_SUBJECT', 'mailto:info@tradematrix.ai')
        }

    def get_user_subscriptions(self, user_id: str) -> List[Dict]:
        """Get all push subscriptions for a user"""
        try:
            response = self.supabase.table('user_push_subscriptions')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()

            return response.data or []

        except Exception as e:
            print(f"❌ Error fetching subscriptions: {e}")
            return []

    def send_push_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Send push notification to all user's devices
        """
        subscriptions = self.get_user_subscriptions(user_id)

        if not subscriptions:
            print(f"⚠️  No push subscriptions for user {user_id}")
            return False

        payload = json.dumps({
            'title': title,
            'body': body,
            'data': data or {},
        })

        success_count = 0
        for subscription in subscriptions:
            try:
                # Build subscription info for pywebpush
                subscription_info = {
                    "endpoint": subscription['endpoint'],
                    "keys": {
                        "p256dh": subscription['p256dh'],
                        "auth": subscription['auth']
                    }
                }

                # Send push notification
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims=self.vapid_claims
                )

                success_count += 1

                # Update last_used_at
                self.supabase.table('user_push_subscriptions')\
                    .update({'last_used_at': 'NOW()'})\
                    .eq('id', subscription['id'])\
                    .execute()

            except WebPushException as e:
                print(f"❌ WebPush error: {e}")

                # If subscription is invalid, delete it
                if e.response and e.response.status_code in [404, 410]:
                    print(f"   Removing invalid subscription: {subscription['endpoint'][:50]}...")
                    self.supabase.table('user_push_subscriptions')\
                        .delete()\
                        .eq('id', subscription['id'])\
                        .execute()

            except Exception as e:
                print(f"❌ Unexpected error sending push: {e}")

        if success_count > 0:
            print(f"✅ Sent push to {success_count}/{len(subscriptions)} devices")
            return True
        else:
            print(f"❌ Failed to send push to any device")
            return False


# Usage
if __name__ == "__main__":
    service = PushNotificationService()

    # Test notification
    test_user_id = "your-user-id-here"
    service.send_push_notification(
        user_id=test_user_id,
        title="🔴 TEST: DAX touched Yesterday High",
        body="Consider: MR-01 (Reversal from Yesterday High)\nLevel: 24,215.38 | Current: 24,214.89",
        data={
            'symbol': 'DAX',
            'level_type': 'yesterday_high',
        }
    )
