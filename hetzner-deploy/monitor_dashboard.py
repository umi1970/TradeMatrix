#!/usr/bin/env python3
"""
TradeMatrix Monitoring Dashboard
Real-time monitoring for Hetzner deployment
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
NC = '\033[0m'  # No Color


def print_header(text: str):
    """Print section header"""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}{BOLD}{text:^60}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{NC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{NC}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{NC}")


def print_info(text: str):
    """Print info message"""
    print(f"{CYAN}ℹ️  {text}{NC}")


class MonitoringDashboard:
    """TradeMatrix monitoring dashboard"""

    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

        if not self.supabase_url or not self.supabase_key:
            print_error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
            sys.exit(1)

        # Initialize connections
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            print_success("Connected to Redis and Supabase")
        except Exception as e:
            print_error(f"Connection failed: {e}")
            sys.exit(1)

    def check_redis_health(self) -> Dict:
        """Check Redis connection and stats"""
        try:
            # Ping Redis
            self.redis_client.ping()

            # Get memory info
            info = self.redis_client.info('memory')
            memory_used = info.get('used_memory_human', 'N/A')

            # Get key count
            key_count = self.redis_client.dbsize()

            return {
                'status': 'healthy',
                'memory_used': memory_used,
                'key_count': key_count
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_api_usage(self) -> Dict:
        """Get chart-img.com API usage"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            key = f"chart_img:requests:daily:{today}"

            usage = self.redis_client.get(key)
            usage_count = int(usage) if usage else 0

            # Get last 7 days
            history = []
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                key = f"chart_img:requests:daily:{date}"
                count = self.redis_client.get(key)
                history.append({
                    'date': date,
                    'count': int(count) if count else 0
                })

            return {
                'today': usage_count,
                'limit': 1000,
                'history': history
            }
        except Exception as e:
            return {
                'error': str(e)
            }

    def get_chart_snapshots(self, limit: int = 10) -> List[Dict]:
        """Get recent chart snapshots from Supabase"""
        try:
            result = self.supabase.table('chart_snapshots') \
                .select('*') \
                .order('generated_at', desc=True) \
                .limit(limit) \
                .execute()

            return result.data
        except Exception as e:
            print_error(f"Failed to fetch chart snapshots: {e}")
            return []

    def get_liquidity_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent liquidity alerts"""
        try:
            result = self.supabase.table('liquidity_alerts') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            return result.data
        except Exception as e:
            print_error(f"Failed to fetch liquidity alerts: {e}")
            return []

    def get_alert_subscriptions(self) -> int:
        """Get count of active alert subscriptions"""
        try:
            result = self.supabase.table('liquidity_alert_subscriptions') \
                .select('id', count='exact') \
                .eq('active', True) \
                .execute()

            return result.count
        except Exception as e:
            print_error(f"Failed to fetch subscriptions: {e}")
            return 0

    def display_dashboard(self):
        """Display the complete monitoring dashboard"""
        # Header
        print_header("TradeMatrix Monitoring Dashboard")
        print(f"{CYAN}📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{NC}")

        # Redis Health
        print_header("1. Redis Status")
        redis_health = self.check_redis_health()
        if redis_health['status'] == 'healthy':
            print_success("Redis is healthy")
            print(f"  Memory Used: {redis_health['memory_used']}")
            print(f"  Total Keys: {redis_health['key_count']}")
        else:
            print_error(f"Redis error: {redis_health.get('error', 'Unknown')}")

        # API Usage
        print_header("2. chart-img.com API Usage")
        api_usage = self.get_api_usage()
        if 'error' not in api_usage:
            usage = api_usage['today']
            limit = api_usage['limit']
            percent = (usage / limit) * 100

            print(f"  Today: {usage} / {limit} requests ({percent:.1f}%)")

            if usage < 800:
                print_success("Usage is within safe limits")
            elif usage < 1000:
                print_warning(f"Usage is high ({usage}/1000)")
            else:
                print_error("API limit exceeded! Using fallback charts.")

            # Weekly history
            print("\n  Last 7 Days:")
            for day in api_usage['history']:
                bar_length = int((day['count'] / limit) * 20)
                bar = '█' * bar_length + '░' * (20 - bar_length)
                print(f"    {day['date']}: {bar} {day['count']:4d}")
        else:
            print_error(f"Failed to get API usage: {api_usage['error']}")

        # Chart Snapshots
        print_header("3. Recent Chart Snapshots")
        snapshots = self.get_chart_snapshots(limit=10)
        if snapshots:
            print_success(f"Found {len(snapshots)} recent snapshots")
            print("\n  Latest Charts:")
            for i, snap in enumerate(snapshots[:5], 1):
                generated = snap['generated_at'][:19]  # Remove timezone for readability
                symbol = snap['symbol']
                timeframe = snap['timeframe']
                trigger = snap['trigger_type']
                print(f"    {i}. {generated} | {symbol:8s} {timeframe:4s} | {trigger}")
        else:
            print_warning("No chart snapshots found")

        # Liquidity Alerts
        print_header("4. Recent Liquidity Alerts")
        alerts = self.get_liquidity_alerts(limit=5)
        if alerts:
            print_success(f"Found {len(alerts)} recent alerts")
            print("\n  Latest Alerts:")
            for i, alert in enumerate(alerts, 1):
                created = alert['created_at'][:19]
                symbol = alert['symbol']
                level_type = alert['level_type']
                price = alert.get('price', 0)
                print(f"    {i}. {created} | {symbol:8s} {level_type:10s} @ {price:.2f}")
        else:
            print_info("No recent alerts triggered")

        # Alert Subscriptions
        print_header("5. Alert Subscriptions")
        sub_count = self.get_alert_subscriptions()
        print(f"  Active Subscriptions: {sub_count}")
        if sub_count > 0:
            print_success(f"{sub_count} users subscribed to alerts")
        else:
            print_warning("No active alert subscriptions")

        # System Info
        print_header("6. System Information")
        print(f"  Server: Hetzner CX11 (135.181.195.241)")
        print(f"  Services: Redis, Celery Worker, Celery Beat")
        print(f"  Repository: /root/TradeMatrix")

        # Footer
        print_header("Dashboard End")
        print(f"\n{CYAN}For detailed logs, run:{NC}")
        print(f"  docker-compose logs -f celery_worker")
        print(f"  docker-compose logs -f celery_beat")
        print()


def main():
    """Main entry point"""
    try:
        dashboard = MonitoringDashboard()
        dashboard.display_dashboard()
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Dashboard error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
