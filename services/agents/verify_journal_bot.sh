#!/bin/bash

# JournalBot Implementation Verification Script
# Checks that all required files and dependencies are in place

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  JournalBot Implementation Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $2 - File not found: $1"
        ((FAIL++))
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $2 - Directory not found: $1"
        ((FAIL++))
    fi
}

# Function to check string in file
check_in_file() {
    if grep -q "$2" "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $3"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $3 - Not found in $1"
        ((FAIL++))
    fi
}

# Function to warn about requirement
warn_requirement() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN++))
}

echo "1. Core Files"
echo "─────────────"
check_file "src/journal_bot.py" "JournalBot agent implementation"
check_file "tests/test_journal_bot.py" "JournalBot test suite"
check_file "JOURNAL_BOT_QUICKREF.md" "Quick reference documentation"
check_file "JOURNAL_BOT_IMPLEMENTATION.md" "Implementation summary"
check_file "../api/supabase/migrations/007_reports_table.sql" "Database migration 007"
echo ""

echo "2. Integration Files"
echo "────────────────────"
check_in_file "src/tasks.py" "from journal_bot import JournalBot" "JournalBot import in tasks.py"
check_in_file "src/tasks.py" "def journal_bot_task" "journal_bot_task function"
check_in_file "src/tasks.py" "journal-bot" "Celery Beat schedule entry"
echo ""

echo "3. Dependencies"
echo "───────────────"
check_in_file "requirements.txt" "python-docx" "python-docx dependency"
check_in_file "requirements.txt" "reportlab" "reportlab dependency"
check_in_file "requirements.txt" "openai" "openai dependency (existing)"
check_in_file "requirements.txt" "langchain" "langchain dependency (existing)"
echo ""

echo "4. Code Structure"
echo "─────────────────"
check_in_file "src/journal_bot.py" "class JournalBot" "JournalBot class definition"
check_in_file "src/journal_bot.py" "def fetch_trades" "fetch_trades method"
check_in_file "src/journal_bot.py" "def generate_ai_summary" "generate_ai_summary method"
check_in_file "src/journal_bot.py" "def create_docx_report" "create_docx_report method"
check_in_file "src/journal_bot.py" "def create_pdf_report" "create_pdf_report method"
check_in_file "src/journal_bot.py" "def upload_to_storage" "upload_to_storage method"
check_in_file "src/journal_bot.py" "def create_report_record" "create_report_record method"
check_in_file "src/journal_bot.py" "def generate_daily_report" "generate_daily_report method"
check_in_file "src/journal_bot.py" "def run" "run method"
echo ""

echo "5. Test Coverage"
echo "────────────────"
check_in_file "tests/test_journal_bot.py" "TestJournalBotFetchTrades" "FetchTrades tests"
check_in_file "tests/test_journal_bot.py" "TestJournalBotAISummary" "AISummary tests"
check_in_file "tests/test_journal_bot.py" "TestJournalBotReportCreation" "ReportCreation tests"
check_in_file "tests/test_journal_bot.py" "TestJournalBotStorage" "Storage tests"
check_in_file "tests/test_journal_bot.py" "TestJournalBotRun" "Run tests"
check_in_file "tests/test_journal_bot.py" "TestJournalBotIntegration" "Integration tests"
echo ""

echo "6. Database Migration"
echo "─────────────────────"
check_in_file "../api/supabase/migrations/007_reports_table.sql" "CREATE TABLE.*reports" "reports table creation"
check_in_file "../api/supabase/migrations/007_reports_table.sql" "report_type" "report_type column"
check_in_file "../api/supabase/migrations/007_reports_table.sql" "file_url_pdf" "file_url_pdf column"
check_in_file "../api/supabase/migrations/007_reports_table.sql" "file_url_docx" "file_url_docx column"
check_in_file "../api/supabase/migrations/007_reports_table.sql" "ENABLE ROW LEVEL SECURITY" "RLS enabled"
echo ""

echo "7. Documentation"
echo "────────────────"
check_in_file "JOURNAL_BOT_QUICKREF.md" "fetch_trades" "fetch_trades documentation"
check_in_file "JOURNAL_BOT_QUICKREF.md" "generate_ai_summary" "generate_ai_summary documentation"
check_in_file "JOURNAL_BOT_QUICKREF.md" "create_docx_report" "create_docx_report documentation"
check_in_file "JOURNAL_BOT_QUICKREF.md" "Celery Task Integration" "Celery integration docs"
check_in_file "JOURNAL_BOT_QUICKREF.md" "Example Output" "Example output section"
echo ""

echo "8. Manual Setup Requirements"
echo "────────────────────────────"
warn_requirement "Apply migration 007 in Supabase SQL Editor"
warn_requirement "Create 'reports' bucket in Supabase Storage (public)"
warn_requirement "Set OPENAI_API_KEY in .env file"
warn_requirement "Install dependencies: pip install python-docx reportlab"
warn_requirement "Restart Celery worker and beat scheduler"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Verification Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"
echo -e "${YELLOW}Warnings:${NC} $WARN (manual setup required)"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All automated checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Apply migration: services/api/supabase/migrations/007_reports_table.sql"
    echo "2. Create Supabase Storage bucket: 'reports' (public)"
    echo "3. Set OPENAI_API_KEY in .env"
    echo "4. Install: pip install python-docx reportlab"
    echo "5. Restart Celery: celery -A tasks worker --loglevel=info"
    echo ""
    echo -e "${GREEN}JournalBot is ready for deployment!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the errors above.${NC}"
    exit 1
fi
