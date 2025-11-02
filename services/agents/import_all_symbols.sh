#!/bin/bash
# Import all historical data for 5 symbols

set -e  # Exit on error

echo "=================================="
echo "TradeMatrix - Import All Symbols"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found"
    echo "Please create .env with:"
    echo "  SUPABASE_URL=https://your-project.supabase.co"
    echo "  SUPABASE_SERVICE_KEY=your-service-role-key"
    exit 1
fi

# Array of CSV files and their symbols
declare -A SYMBOLS=(
    ["../../data/historical/dax_historical.csv"]="^GDAXI"
    ["../../data/historical/ndq_historical.csv"]="^NDX"
    ["../../data/historical/dji_historical.csv"]="^DJI"
    ["../../data/historical/eurusd_historical.csv"]="EURUSD"
    ["../../data/historical/eurgbp_historical.csv"]="EURGBP"
)

# Import each symbol
for csv in "${!SYMBOLS[@]}"; do
    symbol="${SYMBOLS[$csv]}"
    echo ""
    echo "==== Importing: $symbol ===="
    python import_historical_data.py "$csv" "$symbol"

    if [ $? -eq 0 ]; then
        echo "✅ $symbol imported successfully"
    else
        echo "❌ $symbol import failed"
    fi
done

echo ""
echo "=================================="
echo "✅ All imports complete!"
echo "=================================="
