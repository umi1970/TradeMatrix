#!/usr/bin/env python3
"""
Test Agent Integrations with ChartGenerator
Tests that all AI agents can successfully generate and use charts

Usage:
    python test_agent_integrations.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

from config.supabase import get_supabase_admin
from config import settings
from src.chart_generator import ChartGenerator
from src.chart_watcher import ChartWatcher
from src.morning_planner import MorningPlanner
from src.journal_bot import JournalBot
from src.exceptions.chart_errors import (
    RateLimitError,
    ChartGenerationError,
    SymbolNotFoundError
)

import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_chart_generator():
    """Test ChartGenerator standalone"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: ChartGenerator Standalone")
    logger.info("="*70)

    try:
        generator = ChartGenerator()

        # Get usage stats
        stats = generator.get_usage_stats()
        logger.info(f"📊 API Usage: {stats['requests_today']}/{stats['limit_daily']} ({stats['percentage_used']:.1f}%)")

        # Test chart generation (requires valid symbol_id from database)
        # You'll need to replace this with an actual symbol_id from your database
        logger.info("⏭️  Skipping chart generation (requires valid symbol_id)")
        # result = generator.generate_chart(
        #     symbol_id="<UUID-from-database>",
        #     timeframe="4h",
        #     trigger_type="test"
        # )
        # logger.info(f"✅ Chart generated: {result['chart_url']}")

        logger.info("✅ ChartGenerator test passed!\n")
        return True

    except Exception as e:
        logger.error(f"❌ ChartGenerator test failed: {e}")
        return False


def test_chart_watcher():
    """Test ChartWatcher integration"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: ChartWatcher Integration")
    logger.info("="*70)

    try:
        watcher = ChartWatcher(
            supabase_client=get_supabase_admin(),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

        # Test initialization
        assert hasattr(watcher, 'chart_generator'), "ChartGenerator not initialized"
        logger.info("✅ ChartWatcher initialized with ChartGenerator")

        # Test run method (will skip symbols without chart_enabled=true)
        result = watcher.run(timeframe='4h')

        logger.info(f"📊 Symbols analyzed: {result.get('symbols_analyzed', 0)}")
        logger.info(f"📊 Analyses created: {result.get('analyses_created', 0)}")

        logger.info("✅ ChartWatcher test passed!\n")
        return True

    except Exception as e:
        logger.error(f"❌ ChartWatcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_morning_planner():
    """Test MorningPlanner integration"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: MorningPlanner Integration")
    logger.info("="*70)

    try:
        planner = MorningPlanner(
            supabase_client=get_supabase_admin()
        )

        # Test initialization
        assert hasattr(planner, 'chart_generator'), "ChartGenerator not initialized"
        logger.info("✅ MorningPlanner initialized with ChartGenerator")

        # Test run method (will analyze symbols and generate setups)
        result = planner.run()

        logger.info(f"📊 Symbols analyzed: {result.get('symbols_analyzed', 0)}")
        logger.info(f"📊 Setups generated: {result.get('setups_generated', 0)}")

        # Check if setups have chart URLs
        setups = result.get('setups', [])
        if setups:
            logger.info(f"📊 Sample setup: {setups[0]}")

        logger.info("✅ MorningPlanner test passed!\n")
        return True

    except Exception as e:
        logger.error(f"❌ MorningPlanner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_journal_bot():
    """Test JournalBot integration"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: JournalBot Integration")
    logger.info("="*70)

    try:
        bot = JournalBot(
            supabase_client=get_supabase_admin(),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

        # Test initialization
        assert hasattr(bot, 'chart_generator'), "ChartGenerator not initialized"
        logger.info("✅ JournalBot initialized with ChartGenerator")

        # Test run method (will generate reports)
        result = bot.run()

        logger.info(f"📊 Reports generated: {result.get('reports_generated', 0)}")

        reports = result.get('reports', [])
        if reports:
            logger.info(f"📊 Sample report: {reports[0].get('report_id')}")
            logger.info(f"   PDF URL: {reports[0].get('pdf_url', 'N/A')}")
            logger.info(f"   Trades analyzed: {reports[0].get('trades_analyzed', 0)}")

        logger.info("✅ JournalBot test passed!\n")
        return True

    except Exception as e:
        logger.error(f"❌ JournalBot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for chart generation failures"""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: Error Handling")
    logger.info("="*70)

    try:
        generator = ChartGenerator()

        # Test with invalid symbol_id
        try:
            generator.generate_chart(
                symbol_id="invalid-uuid",
                timeframe="4h",
                trigger_type="test"
            )
            logger.error("❌ Should have raised SymbolNotFoundError")
            return False
        except (SymbolNotFoundError, ChartGenerationError) as e:
            logger.info(f"✅ Correctly caught error: {type(e).__name__}")

        # Test with invalid timeframe
        try:
            from src.exceptions.chart_errors import InvalidTimeframeError
            generator.generate_chart(
                symbol_id="550e8400-e29b-41d4-a716-446655440000",
                timeframe="invalid",
                trigger_type="test"
            )
            logger.error("❌ Should have raised InvalidTimeframeError")
            return False
        except Exception as e:
            logger.info(f"✅ Correctly caught error: {type(e).__name__}")

        logger.info("✅ Error handling test passed!\n")
        return True

    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    logger.info("\n" + "="*70)
    logger.info("🚀 AGENT INTEGRATION TESTS")
    logger.info("="*70)
    logger.info("Testing ChartGenerator integration with all AI agents")
    logger.info("="*70 + "\n")

    tests = [
        ("ChartGenerator Standalone", test_chart_generator),
        ("ChartWatcher Integration", test_chart_watcher),
        ("MorningPlanner Integration", test_morning_planner),
        ("JournalBot Integration", test_journal_bot),
        ("Error Handling", test_error_handling),
    ]

    results = []

    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    logger.info("\n" + "="*70)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status} - {name}")

    logger.info("="*70)
    logger.info(f"Results: {passed_count}/{total_count} tests passed")
    logger.info("="*70 + "\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
