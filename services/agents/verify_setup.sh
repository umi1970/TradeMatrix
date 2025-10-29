#!/bin/bash
# ================================================
# TradeMatrix.ai - Setup Verification Script
# ================================================
# Checks if all prerequisites are met before running Celery
# ================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  TradeMatrix.ai - Setup Verification${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Python version
echo -e "${BLUE}[1/7] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    echo -e "${GREEN}✅ Python $PYTHON_VERSION (OK)${NC}"
else
    echo -e "${RED}❌ Python 3.11+ required (found $PYTHON_VERSION)${NC}"
    ((ERRORS++))
fi
echo ""

# Check 2: Redis
echo -e "${BLUE}[2/7] Checking Redis connection...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
    echo -e "   Start with: docker run -d -p 6379:6379 --name redis redis:7-alpine"
    ((ERRORS++))
fi
echo ""

# Check 3: Environment file
echo -e "${BLUE}[3/7] Checking .env file...${NC}"
if [ -f ".env" ] || [ -f "../.env" ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
    
    # Check required variables
    if [ -f ".env" ]; then
        ENV_FILE=".env"
    else
        ENV_FILE="../.env"
    fi
    
    REQUIRED_VARS=("SUPABASE_URL" "SUPABASE_SERVICE_KEY" "TWELVEDATA_API_KEY" "REDIS_URL")
    
    for VAR in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${VAR}=" "$ENV_FILE" && ! grep -q "^${VAR}=$" "$ENV_FILE"; then
            echo -e "   ✅ $VAR is set"
        else
            echo -e "${YELLOW}   ⚠️  $VAR is not set${NC}"
            ((WARNINGS++))
        fi
    done
else
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "   Copy .env.example to .env and configure"
    ((ERRORS++))
fi
echo ""

# Check 4: Python dependencies
echo -e "${BLUE}[4/7] Checking Python dependencies...${NC}"
REQUIRED_PACKAGES=("celery" "redis" "supabase" "httpx" "pytz")
MISSING_PACKAGES=()

for PACKAGE in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $PACKAGE" 2>/dev/null; then
        echo -e "   ✅ $PACKAGE installed"
    else
        echo -e "${RED}   ❌ $PACKAGE not installed${NC}"
        MISSING_PACKAGES+=("$PACKAGE")
        ((ERRORS++))
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}   Install with: pip install -r ../api/requirements.txt${NC}"
fi
echo ""

# Check 5: File structure
echo -e "${BLUE}[5/7] Checking file structure...${NC}"
REQUIRED_FILES=("src/tasks.py" "src/__init__.py" ".env.example" "README.md")

for FILE in "${REQUIRED_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo -e "   ✅ $FILE exists"
    else
        echo -e "${RED}   ❌ $FILE missing${NC}"
        ((ERRORS++))
    fi
done
echo ""

# Check 6: Supabase connectivity
echo -e "${BLUE}[6/7] Checking Supabase connectivity...${NC}"
if [ -f ".env" ] || [ -f "../.env" ]; then
    # This would require Python - skip for now
    echo -e "${YELLOW}⚠️  Skipped (run 'python test_tasks.py connection' to verify)${NC}"
    ((WARNINGS++))
else
    echo -e "${YELLOW}⚠️  Skipped (no .env file)${NC}"
    ((WARNINGS++))
fi
echo ""

# Check 7: Database schema
echo -e "${BLUE}[7/7] Checking database schema...${NC}"
echo -e "${YELLOW}⚠️  Manual check required${NC}"
echo -e "   Verify these tables exist in Supabase:"
echo -e "   - market_symbols"
echo -e "   - ohlc"
echo -e "   - levels_daily"
echo -e "   - setups"
echo -e "   - alerts"
((WARNINGS++))
echo ""

# Summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}================================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to run Celery.${NC}"
    echo ""
    echo -e "Start with: ${BLUE}./start_worker.sh${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) - Review and proceed${NC}"
    echo ""
    echo -e "You can start with: ${BLUE}./start_worker.sh${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) found - Fix before proceeding${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS warning(s)${NC}"
    fi
    echo ""
    echo -e "See README.md for setup instructions"
    exit 1
fi
