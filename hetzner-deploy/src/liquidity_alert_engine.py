#!/usr/bin/env python3
"""
Liquidity Level Alert Engine
Checks if current prices crossed key liquidity levels
"""

import os
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class LiquidityAlertEngine:
    """Check liquidity levels and trigger alerts"""

    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_KEY')
        )

    def get_latest_eod_levels(self, symbol_id: str) -> Optional[Dict]:
        """Get latest EOD levels for a symbol"""
        try:
            response = self.supabase.table('eod_levels')\
                .select('*')\
                .eq('symbol_id', symbol_id)\
                .order('trade_date', desc=True)\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            print(f"❌ Error fetching EOD levels: {e}")
            return None

    def get_current_price(self, symbol_id: str) -> Optional[Decimal]:
        """Get current price from cache"""
        try:
            response = self.supabase.table('price_cache')\
                .select('current_price')\
                .eq('symbol_id', symbol_id)\
                .limit(1)\
                .execute()

            if response.data and len(response.data) > 0:
                return Decimal(str(response.data[0]['current_price']))
            return None

        except Exception as e:
            print(f"❌ Error fetching current price: {e}")
            return None

    def get_active_subscriptions(self) -> List[Dict]:
        """Get all active alert subscriptions"""
        try:
            response = self.supabase.table('alert_subscriptions')\
                .select('*, symbols(symbol, name)')\
                .execute()

            return response.data or []

        except Exception as e:
            print(f"❌ Error fetching subscriptions: {e}")
            return []

    def check_level_crossed(
        self,
        current_price: Decimal,
        level_price: Decimal,
        level_type: str,
        tolerance: Decimal = Decimal('0.0005')  # 0.05% tolerance
    ) -> bool:
        """
        Check if price crossed/touched a level within tolerance
        """
        price_diff = abs(current_price - level_price)
        tolerance_amount = level_price * tolerance

        # Price is within tolerance of level
        return price_diff <= tolerance_amount

    def create_alert_record(
        self,
        user_id: str,
        symbol_id: str,
        level_type: str,
        target_price: Decimal,
        current_price: Decimal
    ) -> bool:
        """Create alert record in database"""
        try:
            alert_record = {
                'user_id': user_id,
                'symbol_id': symbol_id,
                'level_type': level_type,
                'target_price': float(target_price),
                'direction': 'touch',
                'status': 'triggered',
                'triggered_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            }

            self.supabase.table('alerts')\
                .insert(alert_record)\
                .execute()

            return True

        except Exception as e:
            print(f"❌ Error creating alert: {e}")
            return False

    def get_setup_context(self, level_type: str) -> Dict[str, str]:
        """Get trading setup context for alert message"""
        contexts = {
            'yesterday_high': {
                'emoji': '🔴',
                'title': 'SHORT SETUP',
                'description': 'Consider: MR-01 (Reversal from Yesterday High)',
                'action': 'Watch for bearish reversal patterns',
            },
            'yesterday_low': {
                'emoji': '🟢',
                'title': 'LONG SETUP',
                'description': 'Consider: MR-04 (Reversal from Yesterday Low)',
                'action': 'Watch for bullish reversal patterns',
            },
            'pivot_point': {
                'emoji': '🟡',
                'title': 'PIVOT ALERT',
                'description': 'Action: Evaluate position management',
                'action': 'Consider trend direction and momentum',
            },
        }
        return contexts.get(level_type, {})

    def check_alerts_for_symbol(self, subscription: Dict) -> List[Dict]:
        """
        Check all enabled alert types for a symbol
        Returns list of triggered alerts
        """
        triggered_alerts = []

        symbol_id = subscription['symbol_id']
        user_id = subscription['user_id']

        # Get current price
        current_price = self.get_current_price(symbol_id)
        if not current_price:
            return triggered_alerts

        # Get EOD levels
        eod_levels = self.get_latest_eod_levels(symbol_id)
        if not eod_levels:
            return triggered_alerts

        symbol_name = subscription['symbols']['symbol']

        # Check Yesterday High
        if subscription.get('yesterday_high_enabled'):
            yesterday_high = Decimal(str(eod_levels['yesterday_high']))
            if self.check_level_crossed(current_price, yesterday_high, 'yesterday_high'):
                context = self.get_setup_context('yesterday_high')

                # Create alert record
                self.create_alert_record(
                    user_id, symbol_id, 'yesterday_high',
                    yesterday_high, current_price
                )

                triggered_alerts.append({
                    'symbol': symbol_name,
                    'level_type': 'yesterday_high',
                    'level_price': yesterday_high,
                    'current_price': current_price,
                    'context': context,
                    'user_id': user_id,
                })

                print(f"  🔴 {symbol_name}: Yesterday High touched ({yesterday_high})")

        # Check Yesterday Low
        if subscription.get('yesterday_low_enabled'):
            yesterday_low = Decimal(str(eod_levels['yesterday_low']))
            if self.check_level_crossed(current_price, yesterday_low, 'yesterday_low'):
                context = self.get_setup_context('yesterday_low')

                self.create_alert_record(
                    user_id, symbol_id, 'yesterday_low',
                    yesterday_low, current_price
                )

                triggered_alerts.append({
                    'symbol': symbol_name,
                    'level_type': 'yesterday_low',
                    'level_price': yesterday_low,
                    'current_price': current_price,
                    'context': context,
                    'user_id': user_id,
                })

                print(f"  🟢 {symbol_name}: Yesterday Low touched ({yesterday_low})")

        # Check Pivot Point
        if subscription.get('pivot_point_enabled') and eod_levels.get('pivot_point'):
            pivot_point = Decimal(str(eod_levels['pivot_point']))
            if self.check_level_crossed(current_price, pivot_point, 'pivot_point'):
                context = self.get_setup_context('pivot_point')

                self.create_alert_record(
                    user_id, symbol_id, 'pivot_point',
                    pivot_point, current_price
                )

                triggered_alerts.append({
                    'symbol': symbol_name,
                    'level_type': 'pivot_point',
                    'level_price': pivot_point,
                    'current_price': current_price,
                    'context': context,
                    'user_id': user_id,
                })

                print(f"  🟡 {symbol_name}: Pivot Point touched ({pivot_point})")

        return triggered_alerts

    def check_all_alerts(self) -> List[Dict]:
        """
        Check all active subscriptions for triggered alerts
        Returns list of all triggered alerts
        """
        print("\n🔍 Checking Liquidity Levels...")

        subscriptions = self.get_active_subscriptions()
        all_triggered = []

        for subscription in subscriptions:
            triggered = self.check_alerts_for_symbol(subscription)
            all_triggered.extend(triggered)

        if all_triggered:
            print(f"\n🚨 {len(all_triggered)} alerts triggered!")
        else:
            print("✅ No levels crossed")

        return all_triggered


# Usage
if __name__ == "__main__":
    engine = LiquidityAlertEngine()
    alerts = engine.check_all_alerts()

    for alert in alerts:
        print(f"\n{alert['context']['emoji']} {alert['symbol']}")
        print(f"  Level: {alert['level_type']}")
        print(f"  Target: {alert['level_price']}")
        print(f"  Current: {alert['current_price']}")
