#!/bin/bash
# run_dev.sh - Run Su6i Yar Bot in Development Mode with Auto-Restart

# Ensure we are in root
cd "$(dirname "$0")/.."

# Export DEV Token if available
if grep -q "TELEGRAM_BOT_TOKEN_DEV" .env; then
    echo "🔑 Loading Dev Token..."
    export TELEGRAM_BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN_DEV" .env | cut -d '=' -f2 | xargs)
else
    echo "⚠️ Warning: TELEGRAM_BOT_TOKEN_DEV not found. Running with PRODUCTION token!"
fi

echo "🚀 Starting Su6i Yar in DEVELOPMENT MODE with Auto-Restart..."
echo "💡 Tip: The bot will automatically restart if the code changes or the process crashes."

# Infinite loop to handle crashes or manual stop signals from code
while true; do
    # Check if 'nodemon' or 'watchmedo' is available
    if command -v watchmedo &> /dev/null; then
        echo "🐕 Using watchmedo (watchdog) for auto-restart..."
        watchmedo auto-restart --directory=src --pattern="*.py" --recursive -- python3 -m src.main --dev
        break
    else
        # Fallback to simple restart loop
        python3 -m src.main --dev
        echo "♻️ Bot process exited. Restarting in 2 seconds (Ctrl+C to stop)..."
        sleep 2
    fi
done
