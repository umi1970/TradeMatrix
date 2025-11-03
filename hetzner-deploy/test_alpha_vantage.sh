#!/bin/bash
# Test Alpha Vantage for DAX, NASDAQ 100, DOW JONES

API_KEY="GPSA28ME4GMVYUUG"

echo "Testing Alpha Vantage API..."
echo ""

echo "=== DAX (^GDAXI) ==="
curl -s "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=^GDAXI&apikey=$API_KEY" | python3 -m json.tool
echo ""

echo "=== NASDAQ 100 (^NDX) ==="
curl -s "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=^NDX&apikey=$API_KEY" | python3 -m json.tool
echo ""

echo "=== DOW JONES (^DJI) ==="
curl -s "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=^DJI&apikey=$API_KEY" | python3 -m json.tool
