#!/usr/bin/env python3
"""
Dependency Verification Script
Tests that all required packages are installed and importable
"""

import sys

def test_imports():
    """Test all external dependencies"""

    results = {
        'success': [],
        'failed': []
    }

    dependencies = [
        # Core
        ('celery', 'Task Queue'),
        ('redis', 'Message Broker'),
        ('supabase', 'Database Client'),
        ('dotenv', 'Environment Variables'),

        # Data Fetching
        ('finnhub', 'Stock Prices API'),
        ('requests', 'HTTP Library'),
        ('aiohttp', 'Async HTTP'),
        ('httpx', 'Modern HTTP Client'),

        # Data Processing
        ('yaml', 'YAML Parser'),
        ('numpy', 'Numerical Computing'),

        # Push Notifications
        ('pywebpush', 'Web Push Protocol'),
        ('cryptography', 'Encryption'),

        # AI & Reports
        ('openai', 'OpenAI API'),
        ('langchain', 'AI Framework'),
        ('langchain_openai', 'LangChain OpenAI'),
        ('docx', 'DOCX Generation'),
        ('reportlab', 'PDF Generation'),
        ('PIL', 'Image Processing (Pillow)'),

        # Utilities
        ('pydantic', 'Data Validation'),
        ('pytz', 'Timezone Handling'),
    ]

    print("=" * 70)
    print("DEPENDENCY VERIFICATION TEST")
    print("=" * 70)
    print()

    for module_name, description in dependencies:
        try:
            __import__(module_name)
            results['success'].append((module_name, description))
            print(f"✅ {module_name:25} - {description}")
        except ImportError as e:
            results['failed'].append((module_name, description, str(e)))
            print(f"❌ {module_name:25} - {description}")
            print(f"   Error: {e}")

    print()
    print("=" * 70)
    print(f"SUMMARY: {len(results['success'])} passed, {len(results['failed'])} failed")
    print("=" * 70)

    if results['failed']:
        print()
        print("FAILED IMPORTS:")
        for module_name, description, error in results['failed']:
            print(f"  - {module_name}: {description}")
            print(f"    Install: pip install {module_name}")
        print()
        return False
    else:
        print()
        print("✅ ALL DEPENDENCIES VERIFIED SUCCESSFULLY!")
        print()
        return True


def test_specific_imports():
    """Test specific imports used in the codebase"""

    print("=" * 70)
    print("SPECIFIC IMPORT TESTS")
    print("=" * 70)
    print()

    tests = [
        # JournalBot imports
        ("from docx import Document", "DOCX Document class"),
        ("from docx.shared import Inches, Pt, RGBColor", "DOCX formatting"),
        ("from docx.enum.text import WD_ALIGN_PARAGRAPH", "DOCX alignment"),
        ("from langchain.chat_models import ChatOpenAI", "LangChain ChatOpenAI"),
        ("from langchain.prompts import ChatPromptTemplate", "LangChain prompts"),
        ("from langchain.chains import LLMChain", "LangChain chains"),

        # ReportLab imports
        ("from reportlab.lib import colors", "ReportLab colors"),
        ("from reportlab.lib.pagesizes import letter, A4", "ReportLab page sizes"),
        ("from reportlab.platypus import SimpleDocTemplate, Table", "ReportLab platypus"),

        # Other critical imports
        ("from pywebpush import webpush, WebPushException", "PyWebPush"),
        ("import numpy as np", "NumPy"),
        ("import aiohttp", "AIOHttp"),
        ("import yaml", "PyYAML"),
    ]

    success_count = 0
    failed_count = 0

    for import_statement, description in tests:
        try:
            exec(import_statement)
            print(f"✅ {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {description}")
            print(f"   Statement: {import_statement}")
            print(f"   Error: {e}")
            failed_count += 1

    print()
    print("=" * 70)
    print(f"SPECIFIC IMPORTS: {success_count} passed, {failed_count} failed")
    print("=" * 70)
    print()

    return failed_count == 0


if __name__ == "__main__":
    print()
    basic_test = test_imports()
    print()
    specific_test = test_specific_imports()

    if basic_test and specific_test:
        print("🎉 ALL TESTS PASSED - Ready for deployment!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Install missing dependencies")
        sys.exit(1)
