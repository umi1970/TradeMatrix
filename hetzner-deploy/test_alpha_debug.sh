#!/bin/bash
API_KEY="GPSA28ME4GMVYUUG"

echo "Testing Alpha Vantage with different symbol formats..."
echo ""

# Test ohne ^
echo "=== DAX ohne ^ (GDAXI) ==="
curl -s "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=GDAXI&apikey=$API_KEY"
echo ""
echo ""

# Test bekanntes US Symbol (sollte immer funktionieren)
echo "=== Apple (AAPL) - Test ob API grundsätzlich funktioniert ==="
curl -s "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=$API_KEY"
echo ""
