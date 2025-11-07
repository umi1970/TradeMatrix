#!/usr/bin/env python3
"""
Test Script: Verify Chart Storage Upload
Tests that chart-img.com API → Supabase Storage upload works correctly

Usage:
    cd /mnt/c/Users/uzobu/Documents/SaaS/TradeMatrix/hetzner-deploy
    python3 test_chart_storage.py
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.chart_service import ChartService
from src.config.supabase import get_supabase_admin

# Load environment variables
load_dotenv()

async def test_chart_storage():
    """
    Test chart generation and storage upload

    Expected Flow:
    1. Generate chart via chart-img.com API
    2. Download PNG image bytes
    3. Upload to Supabase Storage (bucket: chart-snapshots)
    4. Verify URL format: https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/chart-snapshots/...
    """
    print("=" * 80)
    print("Chart Storage Upload Test")
    print("=" * 80)

    # Initialize service
    print("\n1️⃣ Initializing ChartService...")
    try:
        service = ChartService()
        print("✅ ChartService initialized")
    except Exception as e:
        print(f"❌ Failed to initialize ChartService: {e}")
        return False

    # Test chart generation with storage upload
    print("\n2️⃣ Generating chart for DAX (1h timeframe)...")
    test_symbol = "DAX"
    test_timeframe = "1h"

    try:
        chart_url = await service.generate_chart_url(
            symbol=test_symbol,
            timeframe=test_timeframe,
            agent_name="TestAgent",
            force_refresh=True  # Skip cache to test full flow
        )

        if not chart_url:
            print("❌ Chart generation failed (returned None)")
            return False

        print(f"✅ Chart generated successfully!")
        print(f"📊 Chart URL: {chart_url}")

    except Exception as e:
        print(f"❌ Chart generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Verify URL format
    print("\n3️⃣ Verifying Supabase Storage URL format...")

    expected_prefix = "https://htnlhazqzpwfyhnngfsn.supabase.co/storage/v1/object/public/chart-snapshots/"

    if chart_url.startswith(expected_prefix):
        print(f"✅ URL format correct!")
        print(f"   Bucket: chart-snapshots")
        print(f"   Path: {chart_url.replace(expected_prefix, '')}")
    else:
        print(f"❌ URL format incorrect!")
        print(f"   Expected prefix: {expected_prefix}")
        print(f"   Got: {chart_url}")
        return False

    # Test download from Supabase Storage
    print("\n4️⃣ Testing download from Supabase Storage URL...")

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(chart_url)
            response.raise_for_status()

            image_bytes = response.content
            print(f"✅ Successfully downloaded {len(image_bytes)} bytes from Storage")

            # Verify PNG format
            if image_bytes[:4] == b'\x89PNG':
                print(f"✅ Image format verified (PNG)")
            else:
                print(f"⚠️ Warning: Image may not be PNG format")

    except httpx.HTTPError as e:
        print(f"❌ Download failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Success summary
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nVerifications:")
    print("  ✅ ChartService initialized")
    print("  ✅ Chart generated via chart-img.com API")
    print("  ✅ Image uploaded to Supabase Storage")
    print("  ✅ Public URL has correct format")
    print("  ✅ Image can be downloaded from Storage URL")
    print("  ✅ No 403 errors (Storage URL is public)")
    print("\nNext Steps:")
    print("  1. Check Supabase Dashboard → Storage → chart-snapshots bucket")
    print("  2. Verify image file exists in: TestAgent/YYYY/MM/DD/")
    print("  3. Deploy to Hetzner server")

    return True


if __name__ == "__main__":
    # Check required env vars
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY',
        'CHART_IMG_API_KEY',
        'REDIS_URL'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please set them in .env file")
        sys.exit(1)

    # Run test
    success = asyncio.run(test_chart_storage())
    sys.exit(0 if success else 1)
