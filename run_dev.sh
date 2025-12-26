#!/bin/bash
# run_dev.sh - Run Su6i Yar Bot in Development Mode with Auto-Restart

# Check if .env has TELEGRAM_BOT_TOKEN_DEV
if ! grep -q "TELEGRAM_BOT_TOKEN_DEV" .env; then
    echo "⚠️ Warning: TELEGRAM_BOT_TOKEN_DEV not found in .env"
    echo "Please add your development bot token to .env first."
fi

echo "🚀 Starting Su6i Yar in DEVELOPMENT MODE with Auto-Restart..."
echo "💡 Tip: The bot will automatically restart if the code changes or the process crashes."

# Infinite loop to handle crashes or manual stop signals from code
while true; do
    # Optimization: Use 'ls' and 'sum' as a simple change detector for Mac
    # or just run it and let the user restart manually? 
    # Actually, proper Dev mode should watch for file changes.
    
    # Check if 'nodemon' (Node.js) or 'watchmedo' (Python) is available
    if command -v nodemon &> /dev/null; then
        nodemon --watch su6i_yar.py --exec python3 su6i_yar.py -- --dev
        break
    elif command -v watchmedo &> /dev/null; then
        echo "🐕 Using watchmedo (watchdog) for auto-restart..."
        watchmedo auto-restart --pattern="*.py" --recursive -- python3 su6i_yar.py --dev
        break
    else
        # Fallback to simple restart loop
        python3 su6i_yar.py --dev
        echo "♻️ Bot process exited. Restarting in 2 seconds (Ctrl+C to stop)..."
        sleep 2
    fi
done
