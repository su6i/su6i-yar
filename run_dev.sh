#!/bin/bash
# Auto-restart bot on file changes (Development Mode)
# Usage: ./run_dev.sh

echo "🔄 Starting Su6i Yar in development mode (auto-restart on changes)..."

# Check if watchdog is installed
if ! python3 -c "import watchdog" 2>/dev/null; then
    echo "📦 Installing watchdog..."
    pip install watchdog
fi

# Run with auto-restart
watchmedo auto-restart \
    --patterns="*.py" \
    --ignore-patterns="*.pyc;__pycache__/*" \
    --recursive \
    -- python3 su6i_yar.py
