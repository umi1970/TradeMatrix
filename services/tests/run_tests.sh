#!/bin/bash
# ================================================
# TradeMatrix.ai - E2E Test Runner
# ================================================
# Runs end-to-end tests with various options
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh fast         # Skip slow tests
#   ./run_tests.sh morning      # Run morning flow test only
#   ./run_tests.sh usopen       # Run US open flow test only
#   ./run_tests.sh coverage     # Run with coverage report
#   ./run_tests.sh benchmark    # Run performance benchmarks

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}TradeMatrix.ai - E2E Test Runner${NC}"
echo -e "${BLUE}================================================${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo -e "   Creating from .env.example..."
    cp .env.example .env
    echo -e "${RED}   ❌ Please configure .env with your test database credentials${NC}"
    exit 1
fi

# Load environment
export $(grep -v '^#' .env | xargs)

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python version: ${python_version}"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found${NC}"
    echo -e "   Install with: pip install -r ../api/requirements.txt"
    exit 1
fi

echo -e "${GREEN}✓${NC} pytest installed"

# Parse command
test_mode=${1:-all}

case $test_mode in
    all)
        echo -e "\n${BLUE}Running all E2E tests...${NC}\n"
        pytest test_e2e_trading_flow.py -v -s
        ;;

    fast)
        echo -e "\n${BLUE}Running fast tests (excluding slow tests)...${NC}\n"
        pytest test_e2e_trading_flow.py -v -s -m "not slow"
        ;;

    morning)
        echo -e "\n${BLUE}Running Morning Flow test...${NC}\n"
        pytest test_e2e_trading_flow.py::test_complete_morning_flow -v -s
        ;;

    usopen)
        echo -e "\n${BLUE}Running US Open Flow test...${NC}\n"
        pytest test_e2e_trading_flow.py::test_complete_usopen_flow -v -s
        ;;

    alert)
        echo -e "\n${BLUE}Running Alert Flow test...${NC}\n"
        pytest test_e2e_trading_flow.py::test_realtime_alert_flow -v -s
        ;;

    risk)
        echo -e "\n${BLUE}Running Risk Management test...${NC}\n"
        pytest test_e2e_trading_flow.py::test_risk_management_flow -v -s
        ;;

    multi)
        echo -e "\n${BLUE}Running Multi-Symbol test...${NC}\n"
        pytest test_e2e_trading_flow.py::test_multi_symbol_flow -v -s
        ;;

    error)
        echo -e "\n${BLUE}Running Error Recovery test...${NC}\n"
        pytest test_e2e_trading_flow.py::test_error_recovery_flow -v -s
        ;;

    benchmark)
        echo -e "\n${BLUE}Running Performance Benchmarks...${NC}\n"
        pytest test_e2e_trading_flow.py::test_performance_benchmark -v -s
        ;;

    coverage)
        echo -e "\n${BLUE}Running tests with coverage report...${NC}\n"
        pytest test_e2e_trading_flow.py -v --cov=. --cov-report=html --cov-report=term
        echo -e "\n${GREEN}✓${NC} Coverage report generated in htmlcov/index.html"
        ;;

    integrity)
        echo -e "\n${BLUE}Running Database Integrity test...${NC}\n"
        pytest test_e2e_trading_flow.py::test_database_integrity -v -s
        ;;

    smoke)
        echo -e "\n${BLUE}Running smoke tests (quick validation)...${NC}\n"
        pytest test_e2e_trading_flow.py -v -s -m "smoke or (e2e and not slow)"
        ;;

    help|--help|-h)
        echo -e "\n${YELLOW}Available commands:${NC}"
        echo -e "  ${GREEN}all${NC}         - Run all tests (default)"
        echo -e "  ${GREEN}fast${NC}        - Run fast tests only (exclude slow)"
        echo -e "  ${GREEN}morning${NC}     - Run Morning Flow test"
        echo -e "  ${GREEN}usopen${NC}      - Run US Open Flow test"
        echo -e "  ${GREEN}alert${NC}       - Run Alert Flow test"
        echo -e "  ${GREEN}risk${NC}        - Run Risk Management test"
        echo -e "  ${GREEN}multi${NC}       - Run Multi-Symbol test"
        echo -e "  ${GREEN}error${NC}       - Run Error Recovery test"
        echo -e "  ${GREEN}benchmark${NC}   - Run Performance Benchmarks"
        echo -e "  ${GREEN}coverage${NC}    - Run with coverage report"
        echo -e "  ${GREEN}integrity${NC}   - Run Database Integrity test"
        echo -e "  ${GREEN}smoke${NC}       - Run quick smoke tests"
        echo -e "  ${GREEN}help${NC}        - Show this help message"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo -e "  ./run_tests.sh"
        echo -e "  ./run_tests.sh fast"
        echo -e "  ./run_tests.sh morning"
        echo -e "  ./run_tests.sh coverage"
        exit 0
        ;;

    *)
        echo -e "${RED}❌ Unknown command: ${test_mode}${NC}"
        echo -e "   Use './run_tests.sh help' to see available commands"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}================================================${NC}"
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "${GREEN}================================================${NC}"
else
    echo -e "\n${RED}================================================${NC}"
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${RED}================================================${NC}"
    exit 1
fi
